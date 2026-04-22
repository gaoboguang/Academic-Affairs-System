import type {
  AdviserQuantInsightData,
  EvaluationTeacherInsight,
  ReportInsightTone,
  StudentAnalysisSubjectInsight,
  TeacherAssignmentInsight,
} from "./reportInsightTypes";

export function formatNumber(value: number): string {
  const digits = Number.isInteger(value) ? 0 : 2;
  return value.toFixed(digits).replace(/\.?0+$/, "");
}

export function formatPercent(value: number): string {
  return `${formatNumber(value)}%`;
}

export function pickMaxBy<T>(items: T[], getValue: (item: T) => number): T | null {
  if (!items.length) return null;
  return items.reduce((best, current) => (getValue(current) > getValue(best) ? current : best));
}

export function pickMinBy<T>(items: T[], getValue: (item: T) => number): T | null {
  if (!items.length) return null;
  return items.reduce((best, current) => (getValue(current) < getValue(best) ? current : best));
}

export function buildStudentSubjectDetail(subject: StudentAnalysisSubjectInsight, fallback: string): string {
  const parts: string[] = [];
  if (typeof subject.score === "number") {
    parts.push(`分数 ${formatNumber(subject.score)}`);
  }
  if (subject.class_rank != null) {
    parts.push(`班级第 ${subject.class_rank}`);
  }
  if (subject.grade_rank != null) {
    parts.push(`年级第 ${subject.grade_rank}`);
  }
  if (typeof subject.grade_percentile === "number") {
    parts.push(`年百分位 ${formatPercent(subject.grade_percentile)}`);
  } else if (typeof subject.class_percentile === "number") {
    parts.push(`班百分位 ${formatPercent(subject.class_percentile)}`);
  }
  if (typeof subject.score_delta === "number") {
    parts.push(`较上次 ${subject.score_delta > 0 ? "+" : "-"}${formatNumber(Math.abs(subject.score_delta))} 分`);
  }
  return parts.join(" / ") || fallback;
}

export function pickStudentStrongestSubject(subjects: StudentAnalysisSubjectInsight[]): StudentAnalysisSubjectInsight | null {
  return pickMaxBy(
    subjects.filter((item) => getStudentStandingScore(item) != null),
    (item) => getStudentStandingScore(item) ?? Number.NEGATIVE_INFINITY,
  );
}

export function pickStudentFocusSubject(subjects: StudentAnalysisSubjectInsight[]): StudentAnalysisSubjectInsight | null {
  return pickMinBy(
    subjects.filter((item) => getStudentStandingScore(item) != null),
    (item) => getStudentStandingScore(item) ?? Number.POSITIVE_INFINITY,
  );
}

export function formatTeacherAssignment(item: TeacherAssignmentInsight): string {
  const segments = [item.class_name, item.subject_name].filter((value) => value && value.trim());
  return segments.join(" / ") || "未命名任教拆分";
}

export function pickTopDimension(items: EvaluationTeacherInsight[]): { name: string; score: number } | null {
  const scores = new Map<string, { total: number; count: number }>();
  for (const item of items) {
    for (const [name, score] of Object.entries(item.dimension_scores_json ?? {})) {
      const current = scores.get(name) ?? { total: 0, count: 0 };
      current.total += score;
      current.count += 1;
      scores.set(name, current);
    }
  }
  const rows = Array.from(scores.entries()).map(([name, value]) => ({
    name,
    score: value.total / value.count,
  }));
  return pickMaxBy(rows, (item) => item.score);
}

export function pickTopCategory(items: AdviserQuantInsightData[]): { name: string; score: number } | null {
  const scores = new Map<string, number>();
  for (const item of items) {
    for (const [name, score] of Object.entries(item.category_scores_json ?? {})) {
      scores.set(name, (scores.get(name) ?? 0) + score);
    }
  }
  const rows = Array.from(scores.entries()).map(([name, score]) => ({ name, score }));
  return pickMaxBy(rows, (item) => item.score);
}

export function growthTypeLabel(value: string): string {
  const mapping: Record<string, string> = {
    reward: "奖励记录",
    discipline: "处分记录",
    activity: "活动记录",
    cadre: "干部任职",
    interview: "谈话记录",
    home_school: "家校沟通",
    mental_health: "心理关注",
    quality_eval: "综合素质评价",
    other: "其他",
  };
  return mapping[value] ?? value;
}

export function trendToneByDelta(delta: number): ReportInsightTone {
  if (delta > 0) return "success";
  if (delta < 0) return "warning";
  return "info";
}

function getStudentStandingScore(subject: StudentAnalysisSubjectInsight): number | null {
  if (typeof subject.grade_percentile === "number") {
    return subject.grade_percentile;
  }
  if (typeof subject.class_percentile === "number") {
    return subject.class_percentile;
  }
  if (typeof subject.score === "number") {
    return subject.score;
  }
  return null;
}
