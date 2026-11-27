"""Caso de uso: recibir turno (audio o texto), evaluar y avanzar máquina de estados."""
from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.defense_dtos import (
    SubmitAudioTurnCommand,
    SubmitTextTurnCommand,
    TurnSubmissionResult,
)
from app.application.observers.event_bus import InMemoryEventBus
from app.domain.entities.defense_enums import DefenseStateStatus, InputMode
from app.domain.entities.defense_session import (
    CriterionScoreDetail,
    DefenseSession,
    DefenseTurn,
    FinalDefenseSummary,
    TurnRubricEvaluation,
)
from app.domain.entities.rubric import compute_weighted_score, resolve_uts_verdict
from app.domain.events.defense_events import (
    DefenseSessionCompletedEvent,
    DefenseTurnEvaluatedEvent,
)
from app.domain.exceptions.defense_exceptions import (
    DefenseSessionNotFoundError,
    TranscriptTooShortError,
)
from app.domain.exceptions.fdc_exceptions import FdcDocumentNotFoundError, FdcDomainError
from app.domain.factories.jury_strategy_factory import JuryStrategyFactory
from app.domain.ports.defense_ai_ports import (
    DefenseAiDialogPort,
    SpeechSttPort,
    TurnEvaluationInput,
)
from app.domain.ports.defense_repository_port import DefenseSessionRepositoryPort
from app.domain.ports.repositories import (
    FdcAnalysisRepositoryPort,
    FdcDocumentRepositoryPort,
    ProjectRepositoryPort,
    UnitOfWorkPort,
)
from app.domain.ports.rubric_provider_port import RubricProviderPort


class SubmitDefenseTurnUseCase:
    """Evalúa respuesta oral o escrita, aplica State + Strategy y consolida cierre."""

    def __init__(
        self,
        project_repo: ProjectRepositoryPort,
        document_repo: FdcDocumentRepositoryPort,
        analysis_repo: FdcAnalysisRepositoryPort,
        defense_repo: DefenseSessionRepositoryPort,
        rubric_provider: RubricProviderPort,
        dialog_port: DefenseAiDialogPort,
        stt_port: SpeechSttPort,
        uow: UnitOfWorkPort,
        event_bus: InMemoryEventBus,
        min_words: int = 4,
    ) -> None:
        self._project_repo = project_repo
        self._document_repo = document_repo
        self._analysis_repo = analysis_repo
        self._defense_repo = defense_repo
        self._rubric_provider = rubric_provider
        self._dialog_port = dialog_port
        self._stt_port = stt_port
        self._uow = uow
        self._event_bus = event_bus
        self._min_words = min_words

    def execute_audio(self, cmd: SubmitAudioTurnCommand) -> TurnSubmissionResult:
        """Transcribe audio del estudiante y evalúa el turno."""
        session = self._load_session_and_enter_evaluation(cmd.session_id)
        try:
            transcription = self._stt_port.transcribe(
                audio_bytes=cmd.audio_bytes,
                mime_type=cmd.mime_type,
                filename=cmd.filename,
                custom_vocabulary=session.custom_vocabulary,
            )
            return self._evaluate_and_advance(
                session=session,
                transcript=transcription.transcript,
                input_mode=InputMode.AUDIO,
                extra_latency_ms=transcription.latency_ms,
            )
        except FdcDomainError:
            self._uow.rollback()
            raise

    def execute_text(self, cmd: SubmitTextTurnCommand) -> TurnSubmissionResult:
        """Evalúa respuesta ingresada o corregida manualmente como texto."""
        session = self._load_session_and_enter_evaluation(cmd.session_id)
        try:
            return self._evaluate_and_advance(
                session=session,
                transcript=cmd.transcript_text,
                input_mode=InputMode.TEXT,
                extra_latency_ms=0,
            )
        except FdcDomainError:
            self._uow.rollback()
            raise

    def _load_session_and_enter_evaluation(self, session_id) -> DefenseSession:
        session = self._defense_repo.get_session(session_id)
        if session is None:
            raise DefenseSessionNotFoundError(
                message=f"No existe la sesión de sustentación '{session_id}'.",
                context={"session_id": str(session_id)},
            )
        if session.state == DefenseStateStatus.AURA_SPEAKING:
            session.mark_speech_delivered()
        session.begin_turn_evaluation()
        return session

    def _evaluate_and_advance(
        self,
        session: DefenseSession,
        transcript: str,
        input_mode: InputMode,
        extra_latency_ms: int,
    ) -> TurnSubmissionResult:
        clean_transcript = " ".join(transcript.split())
        if len(clean_transcript.split()) < self._min_words:
            raise TranscriptTooShortError(
                message=f"La respuesta necesita al menos {self._min_words} palabras analizables.",
                context={"min_words": self._min_words, "actual_words": len(clean_transcript.split())},
            )

        document = self._document_repo.get(session.fdc_document_id)
        if document is None:
            raise FdcDocumentNotFoundError("Documento FDC asociado no encontrado.", {"document_id": str(session.fdc_document_id)})
        project = self._project_repo.get(document.project_id)
        analysis = self._analysis_repo.get_by_document_id(document.id)
        if project is None or analysis is None:
            raise FdcDocumentNotFoundError("Análisis FDC asociado no encontrado.", {"document_id": str(document.id)})

        previous_turns = self._defense_repo.list_turns(session.id)
        rubric = self._rubric_provider.get_rubric()
        jury_strategy = JuryStrategyFactory.create(session.jury_profile)
        question = session.current_question()
        is_follow_up_turn = session.is_current_prompt_follow_up(previous_turns)
        asked_text = session.active_prompt_text(previous_turns)
        next_index = session.current_question_index + 1
        next_question = (
            session.planned_questions[next_index]
            if next_index < len(session.planned_questions)
            else None
        )

        eval_result = self._dialog_port.evaluate_turn(
            TurnEvaluationInput(
                project=project,
                fdc_type=document.fdc_type,
                analysis=analysis,
                rubric=rubric,
                jury_strategy=jury_strategy,
                question=question,
                asked_text=asked_text,
                student_transcript=clean_transcript,
                is_follow_up_turn=is_follow_up_turn,
                previous_turns=previous_turns,
                next_planned_question=next_question,
            )
        )

        raw_scores = {code: pair[0] for code, pair in eval_result.criterion_scores.items()}
        weighted_score = compute_weighted_score(raw_scores, rubric)
        criteria_details = [
            CriterionScoreDetail(
                code=crit.code,
                label=crit.label,
                weight=crit.weight,
                score=round(max(0.0, min(5.0, raw_scores.get(crit.code, 0.0))), 2),
                rationale=eval_result.criterion_scores.get(crit.code, (0.0, "Sin observación"))[1],
            )
            for crit in rubric.criteria
        ]

        already_followed = is_follow_up_turn or session.has_follow_up_for_current_question(previous_turns)
        needs_follow_up = jury_strategy.should_trigger_follow_up(
            already_followed_up=already_followed,
            weighted_score=weighted_score,
            ai_recommends_follow_up=eval_result.ai_recommends_follow_up,
            follow_up_text=eval_result.follow_up_question,
        )

        now = datetime.now(timezone.utc)
        total_latency_ms = extra_latency_ms + eval_result.latency_ms
        turn = DefenseTurn(
            id=uuid4(),
            session_id=session.id,
            turn_number=len(previous_turns) + 1,
            question_index=session.current_question_index,
            is_follow_up=is_follow_up_turn,
            thematic_axis=question.thematic_axis,
            aura_question_text=asked_text,
            student_transcript=clean_transcript,
            input_mode=input_mode,
            rubric_scores=TurnRubricEvaluation(weighted_score=weighted_score, criteria=criteria_details),
            turn_feedback=eval_result.turn_feedback,
            needs_follow_up=needs_follow_up,
            latency_ms=total_latency_ms,
            created_at=now,
        )
        all_turns = [*previous_turns, turn]

        if needs_follow_up and eval_result.follow_up_question:
            session.advance_with_follow_up(eval_result.follow_up_question)
        elif session.current_question_index + 1 < len(session.planned_questions):
            session.advance_to_next_question(eval_result.transition_message)
        else:
            student_name = (
                project.authors[0].full_name.strip().split()[0].capitalize()
                if project.authors and project.authors[0].full_name.strip()
                else "estudiante"
            )
            overall_score, summary = self._build_final_summary(
                all_turns, eval_result, rubric, student_name
            )
            session.complete(overall_score=overall_score, summary=summary, completed_at=now)

        self._defense_repo.add_turn(turn)
        self._defense_repo.update_session(session)
        self._uow.commit()

        self._publish_events(session, turn, now)
        is_completed = session.state == DefenseStateStatus.COMPLETED
        return TurnSubmissionResult(
            session=session,
            evaluated_turn=turn,
            turns=all_turns,
            next_question_text=None if is_completed else session.active_prompt_text(all_turns),
            is_follow_up_pending=False if is_completed else session.is_current_prompt_follow_up(all_turns),
            is_completed=is_completed,
        )

    @staticmethod
    def _build_final_summary(
        turns: list[DefenseTurn],
        last_eval,
        rubric,
        student_name: str = "estudiante",
    ) -> tuple[float, FinalDefenseSummary]:
        averages: dict[str, float] = {}
        for crit in rubric.criteria:
            vals = [
                detail.score
                for t in turns
                for detail in t.rubric_scores.criteria
                if detail.code == crit.code
            ]
            averages[crit.code] = round(sum(vals) / len(vals), 2) if vals else 0.0
        overall = compute_weighted_score(averages, rubric)
        verdict = resolve_uts_verdict(overall)
        closing = (
            f"Excelente cierre, {student_name}. Has concluido tu sustentación ante AURA. "
            f"Tu calificación consolidada preliminar es {overall:.2f} sobre 5.00, "
            f"correspondiente al concepto {verdict.value}."
        )
        summary = FinalDefenseSummary(
            verdict=verdict,
            criteria_averages=averages,
            strengths=last_eval.strengths,
            improvements=last_eval.improvements,
            closing_message=closing,
            human_in_the_loop_notice=(
                "Evaluación preliminar generada por AURA como apoyo analítico. "
                "El veredicto académico definitivo corresponde al jurado docente UTS."
            ),
        )
        return overall, summary

    def _publish_events(self, session: DefenseSession, turn: DefenseTurn, now: datetime) -> None:
        self._event_bus.publish(
            DefenseTurnEvaluatedEvent(
                session_id=session.id,
                turn_number=turn.turn_number,
                question_index=turn.question_index,
                is_follow_up=turn.is_follow_up,
                weighted_score=turn.rubric_scores.weighted_score,
                latency_ms=turn.latency_ms,
                occurred_at=now,
            )
        )
        if session.state == DefenseStateStatus.COMPLETED and session.final_summary:
            self._event_bus.publish(
                DefenseSessionCompletedEvent(
                    session_id=session.id,
                    overall_score=session.overall_score or 0.0,
                    verdict=session.final_summary.verdict.value,
                    occurred_at=now,
                )
            )
