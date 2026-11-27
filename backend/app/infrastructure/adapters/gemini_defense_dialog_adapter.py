"""Adaptador Gemini para planificación conversacional de preguntas y evaluación oral."""
from collections.abc import Callable
import json
import time
from typing import Any
import unicodedata

from pydantic import ValidationError

from app.domain.entities.defense_session import PlannedQuestion
from app.domain.entities.fdc_document import FdcType
from app.domain.entities.project import Project
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
from app.domain.strategies.defense_stage_policy import resolve_defense_stage_policy
from app.infrastructure.adapters.gemini_client_helper import (
    build_gemini_client,
    execute_with_failover,
    extract_status_code,
)
from app.infrastructure.adapters.gemini_defense_schemas import (
    DefenseSessionPlanSchema,
    TurnEvaluationSchema,
)


def extract_student_first_name(project: Project) -> str:
    """Obtiene el saludo con los nombres de todos los sustentantes del proyecto."""
    return project.formatted_authors_greeting()


def default_source_section(index: int, fdc_type: FdcType) -> str:
    """Delega la sección documental por defecto a la política pura de etapa."""
    return resolve_defense_stage_policy(fdc_type).default_source_section(index)


def _normalize_key(value: str) -> str:
    stripped = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(ch for ch in stripped if not unicodedata.combining(ch))


def _map_criterion_scores(parsed_scores: list[Any], rubric: Any) -> dict[str, tuple[float, str]]:
    """Mapea puntajes por code o label normalizado a los códigos exactos de rubrica_uts.json."""
    by_code = {_normalize_key(c.code): c.code for c in rubric.criteria}
    by_label = {_normalize_key(c.label): c.code for c in rubric.criteria}
    mapped: dict[str, tuple[float, str]] = {}
    for item in parsed_scores:
        norm = _normalize_key(item.code)
        target_code = by_code.get(norm) or by_label.get(norm)
        if target_code is None:
            target_code = next((c.code for lbl, c in ((k, v) for k, v in by_label.items()) if norm in lbl or lbl in norm), norm)
        mapped[target_code] = (round(float(item.score), 2), item.rationale.strip())
    return mapped


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
        """Genera 4 preguntas base conversacionales alineadas a la etapa y perfil de jurado."""
        started = time.perf_counter()
        student_name = extract_student_first_name(payload.project)
        is_team = payload.project.is_team()
        stage_policy = resolve_defense_stage_policy(payload.fdc_type)
        system_instruction = (
            f"Eres AURA, jurado evaluador masculino de las UTS en diálogo oral directo con {student_name}. "
            f"{payload.jury_strategy.build_question_generation_guidance(payload.fdc_type, student_name, is_team)} "
            f"{stage_policy.build_question_arc(student_name, payload.project.title, is_team)} "
            "Indica source_section legible en cada pregunta y genera hasta 50 términos técnicos del FDC para STT."
        )
        prompt = self._build_plan_prompt(payload, student_name)
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
                source_section=q.source_section.strip() or stage_policy.default_source_section(idx),
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
        """Contrasta la respuesta oral contra el FDC real respetando la etapa documental."""
        started = time.perf_counter()
        student_name = extract_student_first_name(payload.project)
        is_team = payload.project.is_team()
        system_instruction = (
            f"Eres AURA, jurado evaluador masculino de las UTS conversando con {student_name}. "
            f"{payload.jury_strategy.build_turn_evaluation_guidance(payload.fdc_type, student_name, is_team)} "
            "Contrasta lo respondido oralmente contra el contenido real del FDC. "
            "Califica los 4 criterios (pertinencia, coherencia, fundamentacion, metodologia) en escala 0.0 a 5.0. "
            "En transition_message redacta 1 o 2 frases humanas y cercanas usando el nombre del estudiante que reaccionen "
            "a lo que acaba de explicar y den paso fluido al siguiente eje (sin repetir textualmente siguiente_pregunta_planeada). "
            "Si necesitas contrapregunta, redáctala en tono natural y directo empezando con una breve reacción a lo dicho."
        )
        prompt = self._build_eval_prompt(payload, student_name)
        schema = TurnEvaluationSchema.model_json_schema()

        raw_text, used_model = execute_with_failover(
            self._models,
            self._max_retries,
            self._base_delay,
            lambda model: self._invoke_structured(model, system_instruction, prompt, schema),
        )
        parsed = self._validate_json(TurnEvaluationSchema, raw_text, used_model)
        scores = _map_criterion_scores(parsed.criterion_scores, payload.rubric)
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
    def _build_plan_prompt(payload: DefensePreparationInput, student_name: str) -> str:
        syn = payload.analysis.academic_synthesis
        context_obj: dict[str, Any] = {
            "formato": payload.fdc_type.value,
            "nombre_estudiante": student_name,
            "sustentantes": payload.project.author_first_names(),
            "es_equipo": payload.project.is_team(),
            "titulo": payload.project.title,
            "programa": payload.project.academic_program,
            "modalidad": payload.project.modality.value,
            "problema": syn.central_problem,
            "pregunta_problema": syn.research_question,
            "objetivo_general": syn.general_objective,
            "objetivos_especificos": syn.specific_objectives,
            "metodologia_o_plan": syn.research_type_and_approach,
            "fases": syn.phases_or_stages,
            "tecnologias": syn.technologies_and_instruments,
            "resultados": syn.results_and_conclusions_summary,
            "alcance_validacion": syn.validation_scope,
        }
        if payload.jury_strategy.include_gaps_in_base_questions:
            context_obj["vacios_detectados"] = [
                {
                    "eje": g.thematic_axis,
                    "severidad": g.severity,
                    "vacio": g.gap_description,
                    "angulo": g.suggested_defense_angle,
                }
                for g in payload.analysis.detected_gaps
            ]
        return f"Contexto FDC ({payload.fdc_type.value}):\n{json.dumps(context_obj, ensure_ascii=False)}"

    @staticmethod
    def _build_eval_prompt(payload: TurnEvaluationInput, student_name: str) -> str:
        rubric_info = [{"codigo": c.code, "peso": c.weight, "descriptor": c.descriptor} for c in payload.rubric.criteria]
        syn = payload.analysis.academic_synthesis
        follow_rule = (
            "Este turno YA es la contrapregunta: establece needs_follow_up=false y follow_up_question=null."
            if payload.is_follow_up_turn
            else "Usa focos_aclaracion_apoyo solo si la respuesta fue muy vaga, incompleta o contradictoria para activar needs_follow_up=true con una contrapregunta constructiva."
        )
        eval_obj = {
            "nombre_estudiante": student_name,
            "sustentantes": payload.project.author_first_names(),
            "es_equipo": payload.project.is_team(),
            "proyecto": payload.project.title,
            "formato": payload.fdc_type.value,
            "contenido_fdc": {
                "problema": syn.central_problem,
                "objetivo_general": syn.general_objective,
                "objetivos_especificos": syn.specific_objectives,
                "metodologia_o_plan": syn.research_type_and_approach,
                "fases": syn.phases_or_stages,
                "tecnologias": syn.technologies_and_instruments,
                "resultados": syn.results_and_conclusions_summary,
                "alcance_validacion": syn.validation_scope,
                "focos_aclaracion_apoyo": [g.gap_description for g in payload.analysis.detected_gaps],
            },
            "rubrica": rubric_info,
            "eje": payload.question.thematic_axis,
            "seccion_fdc": payload.question.source_section,
            "foco_evaluacion": payload.question.evaluation_focus,
            "pregunta_formulada": payload.asked_text,
            "respuesta_estudiante": payload.student_transcript,
            "siguiente_pregunta_planeada": payload.next_planned_question.question_text if payload.next_planned_question else None,
        }
        return f"{follow_rule}\nDatos del turno:\n{json.dumps(eval_obj, ensure_ascii=False)}"
