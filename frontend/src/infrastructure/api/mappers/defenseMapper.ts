import type {
  DefenseInputMode,
  DefenseSession,
  DefenseState,
  DefenseTurn,
  DefenseVerdict,
  FinalDefenseSummary,
  JuryProfile,
  PlannedQuestion,
  RubricCriterionScore,
  TurnSubmissionResult,
} from "@/domain/models/defense";

export interface PlannedQuestionDto {
  index: number;
  thematic_axis: string;
  question_text: string;
  evaluation_focus: string;
  source_section?: string;
}

export interface CriterionScoreDto {
  code: string;
  label: string;
  weight: number;
  score: number;
  rationale: string;
}

export interface DefenseTurnDto {
  id: string;
  turn_number: number;
  question_index: number;
  is_follow_up: boolean;
  thematic_axis: string;
  aura_question_text: string;
  student_transcript: string;
  input_mode: DefenseInputMode;
  weighted_score: number;
  criteria: CriterionScoreDto[];
  turn_feedback: string;
  needs_follow_up: boolean;
  latency_ms: number;
  created_at: string;
}

export interface FinalDefenseSummaryDto {
  verdict: DefenseVerdict;
  criteria_averages: Record<string, number>;
  strengths: string[];
  improvements: string[];
  closing_message: string;
  human_in_the_loop_notice: string;
}

export interface DefenseSessionResponseDto {
  session_id: string;
  fdc_document_id: string;
  jury_profile: JuryProfile;
  state: DefenseState;
  current_question_index: number;
  total_questions: number;
  active_question_text: string;
  is_follow_up_pending: boolean;
  planned_questions: PlannedQuestionDto[];
  custom_vocabulary: string[];
  turns: DefenseTurnDto[];
  overall_score: number | null;
  final_summary: FinalDefenseSummaryDto | null;
  created_at: string;
  completed_at: string | null;
}

export interface TurnSubmissionResponseDto {
  session_id: string;
  state: DefenseState;
  current_question_index: number;
  evaluated_turn: DefenseTurnDto;
  next_question_text: string | null;
  is_follow_up_pending: boolean;
  is_completed: boolean;
  overall_score: number | null;
  final_summary: FinalDefenseSummaryDto | null;
}

function mapPlannedQuestion(dto: PlannedQuestionDto): PlannedQuestion {
  return {
    index: dto.index,
    thematicAxis: dto.thematic_axis,
    questionText: dto.question_text,
    evaluationFocus: dto.evaluation_focus,
    sourceSection: dto.source_section ?? "",
  };
}

function mapCriterionScore(dto: CriterionScoreDto): RubricCriterionScore {
  return {
    code: dto.code,
    label: dto.label,
    weight: dto.weight,
    score: dto.score,
    rationale: dto.rationale,
  };
}

function mapTurn(dto: DefenseTurnDto): DefenseTurn {
  return {
    id: dto.id,
    turnNumber: dto.turn_number,
    questionIndex: dto.question_index,
    isFollowUp: dto.is_follow_up,
    thematicAxis: dto.thematic_axis,
    auraQuestionText: dto.aura_question_text,
    studentTranscript: dto.student_transcript,
    inputMode: dto.input_mode,
    weightedScore: dto.weighted_score,
    criteria: dto.criteria.map(mapCriterionScore),
    turnFeedback: dto.turn_feedback,
    needsFollowUp: dto.needs_follow_up,
    latencyMs: dto.latency_ms,
    createdAt: dto.created_at,
  };
}

function mapFinalSummary(dto: FinalDefenseSummaryDto): FinalDefenseSummary {
  return {
    verdict: dto.verdict,
    criteriaAverages: dto.criteria_averages,
    strengths: dto.strengths,
    improvements: dto.improvements,
    closingMessage: dto.closing_message,
    humanInTheLoopNotice: dto.human_in_the_loop_notice,
  };
}

export function mapDefenseSessionDtoToDomain(dto: DefenseSessionResponseDto): DefenseSession {
  return {
    sessionId: dto.session_id,
    fdcDocumentId: dto.fdc_document_id,
    juryProfile: dto.jury_profile,
    state: dto.state,
    currentQuestionIndex: dto.current_question_index,
    totalQuestions: dto.total_questions,
    activeQuestionText: dto.active_question_text,
    isFollowUpPending: dto.is_follow_up_pending,
    plannedQuestions: dto.planned_questions.map(mapPlannedQuestion),
    customVocabulary: dto.custom_vocabulary,
    turns: dto.turns.map(mapTurn),
    overallScore: dto.overall_score,
    finalSummary: dto.final_summary ? mapFinalSummary(dto.final_summary) : null,
    createdAt: dto.created_at,
    completedAt: dto.completed_at,
  };
}

export function mapTurnSubmissionDtoToDomain(dto: TurnSubmissionResponseDto): TurnSubmissionResult {
  return {
    sessionId: dto.session_id,
    state: dto.state,
    currentQuestionIndex: dto.current_question_index,
    evaluatedTurn: mapTurn(dto.evaluated_turn),
    nextQuestionText: dto.next_question_text,
    isFollowUpPending: dto.is_follow_up_pending,
    isCompleted: dto.is_completed,
    overallScore: dto.overall_score,
    finalSummary: dto.final_summary ? mapFinalSummary(dto.final_summary) : null,
  };
}

export function mergeTurnSubmissionIntoSession(
  session: DefenseSession,
  result: TurnSubmissionResult,
): DefenseSession {
  const alreadyPresent = session.turns.some((turn) => turn.id === result.evaluatedTurn.id);
  const turns = alreadyPresent ? session.turns : [...session.turns, result.evaluatedTurn];
  const activeQuestionText = result.isCompleted
    ? (result.finalSummary?.closingMessage ?? session.activeQuestionText)
    : (result.nextQuestionText ?? session.activeQuestionText);

  return {
    ...session,
    state: result.state,
    currentQuestionIndex: result.currentQuestionIndex,
    activeQuestionText,
    isFollowUpPending: result.isFollowUpPending,
    turns,
    overallScore: result.overallScore,
    finalSummary: result.finalSummary ?? session.finalSummary,
    completedAt: result.isCompleted
      ? (session.completedAt ?? new Date().toISOString())
      : session.completedAt,
  };
}
