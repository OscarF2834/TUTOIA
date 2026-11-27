import type { DefenseState } from "@/domain/models/defense";

export interface AvatarStageProps {
  state: DefenseState;
  audioLevel: number;
  frequencyBins: ReadonlyArray<number>;
  statusLabel: string;
  subLabel?: string;
}
