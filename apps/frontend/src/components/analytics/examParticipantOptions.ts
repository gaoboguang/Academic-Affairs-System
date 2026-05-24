export interface NamedOption {
  id: number;
  name: string;
}

export interface ExamParticipantOption {
  id: number;
  name: string;
  current_class_id?: number | null;
  current_grade_id?: number | null;
}

export function filterOptionsByExamParticipants<T extends NamedOption>(
  options: T[],
  participants: ExamParticipantOption[],
  participantKey: "current_class_id" | "current_grade_id",
): T[] {
  const participatingIds = new Set(
    participants
      .map((item) => item[participantKey])
      .filter((value): value is number => typeof value === "number"),
  );
  return options.filter((item) => participatingIds.has(item.id));
}

export function pickScopedOptionId<T extends NamedOption>(options: T[], currentId: number | null): number | null {
  if (currentId && options.some((item) => item.id === currentId)) {
    return currentId;
  }
  return options[0]?.id ?? null;
}
