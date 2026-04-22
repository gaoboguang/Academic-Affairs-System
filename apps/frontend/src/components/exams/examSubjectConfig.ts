import type { OptionItem } from "../../stores/reference";

type SubjectLike = Pick<OptionItem, "id" | "code" | "name"> & {
  sort_order?: number;
  is_in_total_default?: boolean;
};

export interface ExamSubjectDraftRow {
  subject_id: number | null;
  full_score: number;
  excellent_line: number | null;
  pass_line: number | null;
  is_in_total: boolean;
  sort_order: number;
  is_active: boolean;
}

export interface ExamSubjectOption extends OptionItem {
  sort_order?: number;
  is_in_total_default?: boolean;
  defaultFullScore: number;
  isStandard: boolean;
}

const SUBJECT_PRIORITY = [
  "chinese",
  "math",
  "english",
  "japanese",
  "russian",
  "physics",
  "chemistry",
  "biology",
  "politics",
  "history",
  "geography",
];

const STANDARD_SUBJECT_CODES = new Set([
  "chinese",
  "math",
  "english",
  "physics",
  "chemistry",
  "biology",
  "politics",
  "history",
  "geography",
]);

const DEFAULT_FULL_SCORE_BY_CODE: Record<string, number> = {
  chinese: 150,
  math: 150,
  english: 150,
  japanese: 150,
  russian: 150,
  physics: 100,
  chemistry: 100,
  biology: 100,
  politics: 100,
  history: 100,
  geography: 100,
};

const DEFAULT_FULL_SCORE_BY_NAME: Record<string, number> = {
  语文: 150,
  数学: 150,
  英语: 150,
  日语: 150,
  俄语: 150,
  物理: 100,
  化学: 100,
  生物: 100,
  政治: 100,
  历史: 100,
  地理: 100,
};

function normalizeSubjectCode(subject: Pick<SubjectLike, "code" | "name">): string {
  return String(subject.code || "").trim().toLowerCase();
}

function getSubjectPriority(subject: Pick<SubjectLike, "code" | "name" | "sort_order">): number {
  const code = normalizeSubjectCode(subject);
  const presetIndex = SUBJECT_PRIORITY.indexOf(code);
  if (presetIndex >= 0) {
    return presetIndex;
  }
  return typeof subject.sort_order === "number" ? SUBJECT_PRIORITY.length + subject.sort_order : SUBJECT_PRIORITY.length + 99;
}

export function getExamSubjectDefaultFullScore(subject: Pick<SubjectLike, "code" | "name">): number {
  const code = normalizeSubjectCode(subject);
  if (code && DEFAULT_FULL_SCORE_BY_CODE[code] != null) {
    return DEFAULT_FULL_SCORE_BY_CODE[code];
  }
  const name = String(subject.name || "").trim();
  if (name && DEFAULT_FULL_SCORE_BY_NAME[name] != null) {
    return DEFAULT_FULL_SCORE_BY_NAME[name];
  }
  return 100;
}

export function isStandardExamSubject(subject: Pick<SubjectLike, "code" | "name">): boolean {
  const code = normalizeSubjectCode(subject);
  if (code) {
    return STANDARD_SUBJECT_CODES.has(code);
  }
  const name = String(subject.name || "").trim();
  return ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理"].includes(name);
}

export function buildExamSubjectOptions(subjects: SubjectLike[]): ExamSubjectOption[] {
  return [...subjects]
    .sort((left, right) => {
      const priorityGap = getSubjectPriority(left) - getSubjectPriority(right);
      if (priorityGap !== 0) {
        return priorityGap;
      }
      return String(left.name || "").localeCompare(String(right.name || ""), "zh-Hans-CN");
    })
    .map((item) => ({
      ...item,
      defaultFullScore: getExamSubjectDefaultFullScore(item),
      isStandard: isStandardExamSubject(item),
    }));
}

export function buildDefaultExamSubjectRow(
  subject: Pick<SubjectLike, "id" | "code" | "name" | "is_in_total_default">,
  sortOrder: number,
): ExamSubjectDraftRow {
  return {
    subject_id: subject.id,
    full_score: getExamSubjectDefaultFullScore(subject),
    excellent_line: null,
    pass_line: null,
    is_in_total: subject.is_in_total_default ?? true,
    sort_order: sortOrder,
    is_active: true,
  };
}

export function getStandardExamSubjectIds(subjects: SubjectLike[]): number[] {
  return buildExamSubjectOptions(subjects)
    .filter((item) => item.isStandard)
    .map((item) => item.id);
}

export function syncExamSubjectRows(
  selectedSubjectIds: number[],
  subjects: SubjectLike[],
  currentRows: ExamSubjectDraftRow[],
): ExamSubjectDraftRow[] {
  const selectedIdSet = new Set(selectedSubjectIds);
  const rowMap = new Map<number, ExamSubjectDraftRow>();
  for (const row of currentRows) {
    if (row.subject_id != null) {
      rowMap.set(row.subject_id, row);
    }
  }
  const orderedSelections = buildExamSubjectOptions(subjects).filter((item) => selectedIdSet.has(item.id));
  return orderedSelections.map((subject, index) => {
    const existing = rowMap.get(subject.id);
    if (existing) {
      return existing;
    }
    return buildDefaultExamSubjectRow(subject, index + 1);
  });
}
