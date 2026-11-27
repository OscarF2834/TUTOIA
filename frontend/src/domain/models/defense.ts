export type DefenseState =
  | "PREPARING"
  | "AURA_SPEAKING"
  | "LISTENING_STUDENT"
  | "EVALUATING_TURN"
  | "COMPLETED";

export type JuryProfile = "ESTANDAR_UTS" | "TECNICO_RIGUROSO";

export type DefenseInputMode = "AUDIO" | "TEXT";

export type DefenseVerdict = "APROBADO" | "APLAZADO" | "NO_APROBADO";

export interface PlannedQuestion {
  index: number;
  thematicAxis: string;
  questionText: string;
  evaluationFocus: string;
  sourceSection: string;
}

export interface RubricCriterionScore {
  code: string;
  label: string;
  weight: number;
  score: number;
  rationale: string;
}

export interface DefenseTurn {
  id: string;
  turnNumber: number;
  questionIndex: number;
  isFollowUp: boolean;
  thematicAxis: string;
  auraQuestionText: string;
  studentTranscript: string;
  inputMode: DefenseInputMode;
  weightedScore: number;
  criteria: RubricCriterionScore[];
  turnFeedback: string;
  needsFollowUp: boolean;
  latencyMs: number;
  createdAt: string;
}

export interface FinalDefenseSummary {
  verdict: DefenseVerdict;
  criteriaAverages: Record<string, number>;
  strengths: string[];
  improvements: string[];
  closingMessage: string;
  humanInTheLoopNotice: string;
}

export interface DefenseSession {
  sessionId: string;
  fdcDocumentId: string;
  juryProfile: JuryProfile;
  state: DefenseState;
  currentQuestionIndex: number;
  totalQuestions: number;
  activeQuestionText: string;
  isFollowUpPending: boolean;
  plannedQuestions: PlannedQuestion[];
  customVocabulary: string[];
  turns: DefenseTurn[];
  overallScore: number | null;
  finalSummary: FinalDefenseSummary | null;
  createdAt: string;
  completedAt: string | null;
}

export interface TurnSubmissionResult {
  sessionId: string;
  state: DefenseState;
  currentQuestionIndex: number;
  evaluatedTurn: DefenseTurn;
  nextQuestionText: string | null;
  isFollowUpPending: boolean;
  isCompleted: boolean;
  overallScore: number | null;
  finalSummary: FinalDefenseSummary | null;
}

export interface CreateDefenseSessionRequest {
  fdcDocumentId: string;
  juryProfile: JuryProfile;
}
