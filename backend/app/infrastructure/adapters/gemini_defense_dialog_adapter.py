"""Adaptador Gemini para planificación de preguntas y evaluación de turnos."""
from collections.abc import Callable
import json
import time
from typing import Any

from pydantic import ValidationError

from app.domain.entities.defense_session import PlannedQuestion
from app.domain.entities.fdc_document import FdcType
from app.domain.exceptions.fdc_exceptions import (
    AiProviderUnavailableError,
    AiResponseValidationError,
    FdcDomainError,
)
from app.domain.ports.defense_ai_ports import (
    DefensePreparationInput,
    DefensePreparationResult,
    TurnEvaluationInput,
    TurnEvaluationResult,
)
from app.infrastructure.adapters.gemini_client_helper import (
    build_gemini_client,
    execute_with_failover,
    extract_status_code,
)
from app.infrastructure.adapters.gemini_defense_schemas import (
    DefenseSessionPlanSchema,
    TurnEvaluationSchema,
)


class GeminiDefenseDialogAdapter:
    """Implementa DefenseAiDialogPort sobre google-genai Interactions + Structured Outputs."""

    def __init__(
        self,
        api_key: str,
        model: str,
        fallback_models: list[str],
        timeout_seconds: int = 45,
        max_retries: int = 1,
        base_delay_seconds: float = 1.5,
        client_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._api_key = api_key
        self._models = [model.strip(), *[m.strip() for m in fallback_models if m.strip() and m.strip() != model.strip()]]
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._base_delay = base_delay_seconds
        self._client_factory = client_factory

    def _client(self) -> Any:
        if self._client_factory is not None:
            return self._client_factory()
        return build_gemini_client(self._api_key, self._timeout_seconds, self._models[0])

    def generate_session_plan(self, payload: DefensePreparationInput) -> DefensePreparationResult:
        """Genera 4 preguntas base personalizadas y hasta 50 términos para STT."""
        started = time.perf_counter()
        system_instruction = (
            "Eres AURA, evaluadora académica de las UTS. "
            f"{payload.jury_strategy.build_question_generation_guidance(payload.fdc_type)} "
            "Genera exactamente 4 preguntas base (índices 0 a 3) cubriendo: "
            "0=PROBLEMA, 1=FUNDAMENTACION, 2=METODOLOGIA_O_PLAN, 3=RESULTADOS_O_VALIDACION, "
            "priorizando los vacíos detectados en el análisis FDC y generando hasta 50 términos técnicos."
        )
        prompt = self._build_plan_prompt(payload)
        schema = DefenseSessionPlanSchema.model_json_schema()

        raw_text, used_model = execute_with_failover(
            self._models,
            self._max_retries,
            self._base_delay,
            lambda model: self._invoke_structured(model, system_instruction, prompt, schema),
        )
        parsed = self._validate_json(DefenseSessionPlanSchema, raw_text, used_model)
        questions = [
            PlannedQuestion(
                index=idx,
                thematic_axis=q.thematic_axis,
                question_text=q.question_text.strip(),
                evaluation_focus=q.evaluation_focus.strip(),
            )
            for idx, q in enumerate(sorted(parsed.questions, key=lambda item: item.index))
        ]
        vocab = [term.strip() for term in parsed.custom_vocabulary if term.strip()][:50]
        return DefensePreparationResult(
            questions=questions,
            custom_vocabulary=vocab,
            model_used=used_model,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def evaluate_turn(self, payload: TurnEvaluationInput) -> TurnEvaluationResult:
        """Evalúa una respuesta del sustentante contra la rúbrica UTS y el FDC."""
        started = time.perf_counter()
        system_instruction = (
            "Eres AURA, jurado evaluador de las UTS. "
            f"{payload.jury_strategy.build_turn_evaluation_guidance(payload.fdc_type)} "
            "Califica cada uno de los 4 criterios de la rúbrica (pertinencia, coherencia, fundamentacion, metodologia) "
            "en escala 0.0 a 5.0 con justificación breve basada exclusivamente en lo respondido y el FDC."
        )
        prompt = self._build_eval_prompt(payload)
        schema = TurnEvaluationSchema.model_json_schema()

        raw_text, used_model = execute_with_failover(
            self._models,
            self._max_retries,
            self._base_delay,
            lambda model: self._invoke_structured(model, system_instruction, prompt, schema),
        )
        parsed = self._validate_json(TurnEvaluationSchema, raw_text, used_model)
        scores = {item.code: (round(item.score, 2), item.rationale.strip()) for item in parsed.criterion_scores}
        follow_up = parsed.follow_up_question.strip() if parsed.follow_up_question else None
        return TurnEvaluationResult(
            criterion_scores=scores,
            turn_feedback=parsed.turn_feedback.strip(),
            strengths=[s.strip() for s in parsed.strengths],
            improvements=[i.strip() for i in parsed.improvements],
            ai_recommends_follow_up=parsed.needs_follow_up,
            follow_up_question=follow_up,
            transition_message=parsed.transition_message.strip(),
            model_used=used_model,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def _invoke_structured(self, model: str, system_instruction: str, prompt: str, schema: dict) -> str:
        client = self._client()
        try:
            interaction = client.interactions.create(
                model=model,
                system_instruction=system_instruction,
                input=prompt,
                response_format={"type": "text", "mime_type": "application/json", "schema": schema},
                timeout=float(self._timeout_seconds),
            )
            return interaction.output_text or ""
        except FdcDomainError:
            raise
        except Exception as exc:
            raise AiProviderUnavailableError(
                message="Error comunicándose con Google Gemini en diálogo de sustentación.",
                context={"reason": str(exc), "model": model, "status_code": extract_status_code(exc)},
            ) from exc

    @staticmethod
    def _validate_json(schema_cls: type[Any], raw_text: str, model: str) -> Any:
        try:
            return schema_cls.model_validate_json(raw_text)
        except ValidationError as exc:
            raise AiResponseValidationError(
                message="La respuesta estructurada de Gemini en sustentación fue inválida.",
                context={"errors": exc.errors(), "model": model},
            ) from exc

    @staticmethod
    def _build_plan_prompt(payload: DefensePreparationInput) -> str:
        syn = payload.analysis.academic_synthesis
        gaps = [
            {"eje": g.thematic_axis, "severidad": g.severity, "vacio": g.gap_description, "angulo": g.suggested_defense_angle}
            for g in payload.analysis.detected_gaps
        ]
        results_rule = (
            "En FDC_124 enfoca la pregunta 2 en Plan de actividades y la 3 en Resultados esperados y validación planteada."
            if payload.fdc_type == FdcType.FDC_124
            else "En FDC_125 enfoca la pregunta 2 en Metodología ejecutada y la 3 en Resultados y Conclusiones."
        )
        context_obj = {
            "formato": payload.fdc_type.value,
            "titulo": payload.project.title,
            "programa": payload.project.academic_program,
            "modalidad": payload.project.modality.value,
            "problema": syn.central_problem,
            "objetivo_general": syn.general_objective,
            "objetivos_especificos": syn.specific_objectives,
            "metodologia_o_plan": syn.research_type_and_approach,
            "tecnologias": syn.technologies_and_instruments,
            "resultados": syn.results_and_conclusions_summary,
            "vacios_detectados": gaps,
        }
        return f"{results_rule}\nContexto FDC:\n{json.dumps(context_obj, ensure_ascii=False)}"

    @staticmethod
    def _build_eval_prompt(payload: TurnEvaluationInput) -> str:
        rubric_info = [
            {"codigo": c.code, "peso": c.weight, "descriptor": c.descriptor}
            for c in payload.rubric.criteria
        ]
        syn = payload.analysis.academic_synthesis
        follow_rule = (
            "Este turno YA es la contrapregunta de seguimiento: establece needs_follow_up=false y follow_up_question=null."
            if payload.is_follow_up_turn
            else "Si detectas vacíos importantes, puedes proponer needs_follow_up=true con una contrapregunta breve."
        )
        eval_obj = {
            "proyecto": payload.project.title,
            "formato": payload.fdc_type.value,
            "sintesis": {
                "problema": syn.central_problem,
                "objetivo_general": syn.general_objective,
                "metodologia": syn.research_type_and_approach,
                "resultados": syn.results_and_conclusions_summary,
            },
            "rubrica": rubric_info,
            "eje": payload.question.thematic_axis,
            "foco_evaluacion": payload.question.evaluation_focus,
            "pregunta_formulada": payload.asked_text,
            "respuesta_estudiante": payload.student_transcript,
        }
        return f"{follow_rule}\nDatos del turno:\n{json.dumps(eval_obj, ensure_ascii=False)}"
