import { uniqueStrings } from "./helpers";
import {
  buildScoreInputPayload,
  normalizeOptionalString,
  validateScoreInputFields,
} from "./scoreInput";
export {
  buildVolunteerBoundaryInsightCards,
  buildVolunteerDraftBoundaryInsightCards,
  buildVolunteerRuleInsightCards,
  buildVolunteerRuleInsightCardsFromRules,
} from "./volunteerWorkbenchInsights";
import type {
  StudentCareerPreference,
  StudentCareerPreferencePayload,
  VolunteerDraftComparisonEntry,
  VolunteerDraftComparisonSummary,
  VolunteerDraftCheckItem,
  VolunteerEmploymentHintStatus,
  VolunteerEmploymentProfile,
  VolunteerDraftItem,
  VolunteerDraftSavePayload,
  VolunteerDraftSummary,
  VolunteerDraftViewSection,
  VolunteerWorkbenchExplanation,
  VolunteerWorkbenchCandidate,
  VolunteerWorkbenchFormState,
  ProvinceVolunteerRule,
  VolunteerWorkbenchPreviewPayload,
  VolunteerWorkbenchPreviewResponse,
} from "./types";

export interface VolunteerDraftMutationResult {
  items: VolunteerDraftItem[];
  added: boolean;
  reason?: "duplicate" | "limit";
}

function normalizeDraft(items: VolunteerDraftItem[]): VolunteerDraftItem[] {
  return items.map((item, index) => ({
    ...item,
    order: index + 1,
  }));
}

const volunteerDraftResultSections: Array<{
  key: VolunteerDraftViewSection["key"];
  label: VolunteerDraftViewSection["label"];
  description: VolunteerDraftViewSection["description"];
  tagType: VolunteerDraftViewSection["tagType"];
}> = [
  {
    key: "challenge",
    label: "冲刺志愿",
    description: "通常放在靠前位置，用来保留可冲院校或专业机会。",
    tagType: "danger",
  },
  {
    key: "steady",
    label: "稳妥志愿",
    description: "适合作为中段主体，兼顾命中率和院校层次。",
    tagType: "warning",
  },
  {
    key: "safe",
    label: "保底志愿",
    description: "建议在后段保留足够数量，避免整张草稿过度冒进。",
    tagType: "success",
  },
];

const postgraduateKeywords = ["读研", "研究生", "硕士", "博士", "深造"];
const certificateKeywords = [
  "资格证",
  "执业",
  "注册",
  "持证",
  "证书",
  "教师资格",
  "法考",
  "注会",
  "医师",
];

const careerPriorityFocusLabels: Record<string, string> = {
  stability: "稳定性",
  salary: "薪酬",
  interest: "兴趣",
  long_term: "长远发展",
};

const scoreInputModeLabels: Record<string, string> = {
  actual_rank: "正式位次",
  actual_score: "正式分数",
  estimated_score: "预估分数",
  estimated_score_and_rank: "预估分 + 预估位次",
  score_range: "分数区间",
  rank_range: "位次区间",
};

const candidateTypeLabels: Record<string, string> = {
  general: "普通类",
  art: "艺体类",
  sports: "体育类",
  fine_art: "美术类",
  music: "音乐类",
  dance: "舞蹈类",
  media: "传媒类",
  spring_exam: "春季高考",
  independent_recruitment: "单独招生",
  comprehensive_evaluation: "综合评价招生",
};

const riskPreferenceLabels: Record<string, string> = {
  conservative: "保守",
  balanced: "平衡",
  aggressive: "激进",
};

const resultTypeLabels: Record<string, string> = {
  challenge: "冲刺",
  steady: "稳妥",
  safe: "保底",
};

export function createVolunteerWorkbenchForm(): VolunteerWorkbenchFormState {
  return {
    student_id: undefined,
    exam_id: undefined,
    province: "山东",
    target_year: new Date().getFullYear(),
    batch: "",
    exam_mode: "",
    candidate_type: "",
    score_input_mode: "actual_rank",
    score_range_min: undefined,
    score_range_max: undefined,
    rank_range_min: undefined,
    rank_range_max: undefined,
    reference_exam_name: "",
    use_historical_mapping: false,
    risk_preference: "balanced",
    target_regions_json: [],
    school_level_tags_json: [],
    major_keyword: "",
    subject_combination: "",
    primary_direction_id: undefined,
    secondary_direction_id: undefined,
    alternative_direction_id: undefined,
    priority_focuses_json: [],
    preferred_industries_json: [],
    preferred_job_types_json: [],
    target_employment_cities_json: [],
    accepts_postgraduate: false,
    accepts_public_service: false,
    accepts_certificate: false,
    accepts_long_training: false,
    student_rank_override: undefined,
    comprehensive_score: undefined,
    professional_score: undefined,
    culture_score: undefined,
    note: "",
  };
}

export function validateVolunteerWorkbenchForm(form: VolunteerWorkbenchFormState): string | null {
  if (!form.student_id || !form.exam_id) {
    return "学生志愿工作台至少需要选择学生和参考考试";
  }
  if (!form.province.trim()) {
    return "省份不能为空";
  }
  const scoreValidationError = validateScoreInputFields(form);
  if (scoreValidationError) {
    return scoreValidationError;
  }
  const directionValidationError = validateCareerPreferenceDirections(
    form.primary_direction_id,
    form.secondary_direction_id,
    form.alternative_direction_id,
  );
  if (directionValidationError) {
    return directionValidationError;
  }
  return null;
}

export function validateVolunteerDraftName(name: string, draftItems: VolunteerDraftItem[]): string | null {
  if (!name.trim()) {
    return "草稿名称不能为空";
  }
  if (!draftItems.length) {
    return "至少加入 1 条志愿后才能保存草稿";
  }
  return null;
}

export function buildVolunteerWorkbenchPayload(
  form: VolunteerWorkbenchFormState,
): VolunteerWorkbenchPreviewPayload {
  return {
    student_id: form.student_id as number,
    exam_id: form.exam_id as number,
    province: form.province,
    target_year: form.target_year,
    batch: normalizeOptionalString(form.batch),
    exam_mode: normalizeOptionalString(form.exam_mode),
    candidate_type: normalizeOptionalString(form.candidate_type) ?? "",
    ...buildScoreInputPayload(form),
    target_regions_json: uniqueStrings(form.target_regions_json),
    school_level_tags_json: uniqueStrings(form.school_level_tags_json),
    major_keyword: normalizeOptionalString(form.major_keyword),
    subject_combination: normalizeOptionalString(form.subject_combination),
    ...buildStudentCareerPreferencePayload(form),
    student_rank_override: form.student_rank_override,
    comprehensive_score: form.comprehensive_score,
    professional_score: form.professional_score,
    culture_score: form.culture_score,
    note: normalizeOptionalString(form.note),
  };
}

export function buildVolunteerDraftPayload(
  name: string,
  form: VolunteerWorkbenchFormState,
  items: VolunteerDraftItem[],
  selectedRule: ProvinceVolunteerRule | null,
): VolunteerDraftSavePayload {
  return {
    name: name.trim(),
    student_id: form.student_id as number,
    exam_id: form.exam_id as number,
    province: form.province,
    target_year: form.target_year as number,
    batch: normalizeOptionalString(form.batch),
    exam_mode: normalizeOptionalString(form.exam_mode),
    candidate_type: normalizeOptionalString(form.candidate_type) ?? "",
    ...buildScoreInputPayload(form),
    target_regions_json: uniqueStrings(form.target_regions_json),
    school_level_tags_json: uniqueStrings(form.school_level_tags_json),
    major_keyword: normalizeOptionalString(form.major_keyword),
    subject_combination: normalizeOptionalString(form.subject_combination),
    ...buildStudentCareerPreferencePayload(form),
    student_rank_override: form.student_rank_override,
    comprehensive_score: form.comprehensive_score,
    professional_score: form.professional_score,
    culture_score: form.culture_score,
    note: normalizeOptionalString(form.note),
    selected_rule: selectedRule,
    items: items.map((item) => ({
      order: item.order,
      plan_id: item.plan_id,
      candidate: item.candidate,
    })),
  };
}

export function buildStudentCareerPreferencePayload(
  form: VolunteerWorkbenchFormState,
): StudentCareerPreferencePayload {
  return normalizeVolunteerCareerPreference(form);
}

export function applyStudentCareerPreferenceToForm(
  form: VolunteerWorkbenchFormState,
  preference: StudentCareerPreference | StudentCareerPreferencePayload | null,
): void {
  form.primary_direction_id = preference?.primary_direction_id;
  form.secondary_direction_id = preference?.secondary_direction_id;
  form.alternative_direction_id = preference?.alternative_direction_id;
  form.priority_focuses_json = [...(preference?.priority_focuses_json ?? [])];
  form.preferred_industries_json = [...(preference?.preferred_industries_json ?? [])];
  form.preferred_job_types_json = [...(preference?.preferred_job_types_json ?? [])];
  form.target_employment_cities_json = [...(preference?.target_employment_cities_json ?? [])];
  form.accepts_postgraduate = preference?.accepts_postgraduate ?? false;
  form.accepts_public_service = preference?.accepts_public_service ?? false;
  form.accepts_certificate = preference?.accepts_certificate ?? false;
  form.accepts_long_training = preference?.accepts_long_training ?? false;
}

export function appendVolunteerDraftItem(
  items: VolunteerDraftItem[],
  candidate: VolunteerWorkbenchCandidate,
  limit?: number,
): VolunteerDraftMutationResult {
  if (items.some((item) => item.plan_id === candidate.plan_id)) {
    return { items: normalizeDraft(items), added: false, reason: "duplicate" };
  }
  if (limit !== undefined && items.length >= limit) {
    return { items: normalizeDraft(items), added: false, reason: "limit" };
  }
  return {
    items: normalizeDraft([
      ...items,
      {
        order: items.length + 1,
        plan_id: candidate.plan_id,
        candidate,
      },
    ]),
    added: true,
  };
}

export function removeVolunteerDraftItem(items: VolunteerDraftItem[], planId: number): VolunteerDraftItem[] {
  return normalizeDraft(items.filter((item) => item.plan_id !== planId));
}

export function moveVolunteerDraftItem(
  items: VolunteerDraftItem[],
  planId: number,
  direction: "up" | "down",
): VolunteerDraftItem[] {
  const index = items.findIndex((item) => item.plan_id === planId);
  if (index === -1) return normalizeDraft(items);
  const nextIndex = direction === "up" ? index - 1 : index + 1;
  if (nextIndex < 0 || nextIndex >= items.length) return normalizeDraft(items);
  const nextItems = [...items];
  const [current] = nextItems.splice(index, 1);
  nextItems.splice(nextIndex, 0, current);
  return normalizeDraft(nextItems);
}

export function reorderVolunteerDraftItem(
  items: VolunteerDraftItem[],
  planId: number,
  targetPlanId: number,
): VolunteerDraftItem[] {
  const sourceIndex = items.findIndex((item) => item.plan_id === planId);
  const targetIndex = items.findIndex((item) => item.plan_id === targetPlanId);
  if (sourceIndex === -1 || targetIndex === -1 || sourceIndex === targetIndex) {
    return normalizeDraft(items);
  }
  const nextItems = [...items];
  const [current] = nextItems.splice(sourceIndex, 1);
  const insertIndex = sourceIndex < targetIndex ? targetIndex : targetIndex;
  nextItems.splice(insertIndex, 0, current);
  return normalizeDraft(nextItems);
}

export function buildVolunteerDraftViewSections(draftItems: VolunteerDraftItem[]): VolunteerDraftViewSection[] {
  return volunteerDraftResultSections.map((section) => ({
    ...section,
    items: draftItems.filter((item) => item.candidate.result_type === section.key),
  }));
}

export function hasVolunteerCareerPreferenceContent(
  value: VolunteerWorkbenchFormState | StudentCareerPreference | StudentCareerPreferencePayload | null | undefined,
): boolean {
  const payload = normalizeVolunteerCareerPreference(value);
  return Boolean(
    payload.primary_direction_id
    || payload.secondary_direction_id
    || payload.alternative_direction_id
    || payload.priority_focuses_json.length
    || payload.preferred_industries_json.length
    || payload.preferred_job_types_json.length
    || payload.target_employment_cities_json.length
    || payload.accepts_postgraduate
    || payload.accepts_public_service
    || payload.accepts_certificate
    || payload.accepts_long_training,
  );
}

export function isSameVolunteerCareerPreference(
  left: VolunteerWorkbenchFormState | StudentCareerPreference | StudentCareerPreferencePayload | null | undefined,
  right: VolunteerWorkbenchFormState | StudentCareerPreference | StudentCareerPreferencePayload | null | undefined,
): boolean {
  return JSON.stringify(normalizeVolunteerCareerPreference(left)) === JSON.stringify(normalizeVolunteerCareerPreference(right));
}

export function hasVolunteerWorkbenchPendingChanges(
  form: VolunteerWorkbenchFormState,
  draftItems: VolunteerDraftItem[],
  preview: VolunteerWorkbenchPreviewResponse | null,
  currentDraftId?: number,
): boolean {
  if (draftItems.length || preview || currentDraftId) {
    return true;
  }

  const defaultForm = createVolunteerWorkbenchForm();
  if (form.student_id || form.exam_id) {
    return true;
  }
  if (form.province !== defaultForm.province) {
    return true;
  }
  if ((form.target_year ?? defaultForm.target_year) !== defaultForm.target_year) {
    return true;
  }
  if (normalizeOptionalString(form.batch) || normalizeOptionalString(form.exam_mode) || normalizeOptionalString(form.candidate_type)) {
    return true;
  }
  if (form.score_input_mode !== defaultForm.score_input_mode) {
    return true;
  }
  if (form.use_historical_mapping !== defaultForm.use_historical_mapping || form.risk_preference !== defaultForm.risk_preference) {
    return true;
  }
  if (uniqueStrings(form.target_regions_json).length || uniqueStrings(form.school_level_tags_json).length) {
    return true;
  }
  if (normalizeOptionalString(form.major_keyword) || normalizeOptionalString(form.subject_combination)) {
    return true;
  }
  if (hasVolunteerCareerPreferenceContent(form)) {
    return true;
  }
  if (
    form.student_rank_override !== undefined
    || form.comprehensive_score !== undefined
    || form.professional_score !== undefined
    || form.culture_score !== undefined
    || form.score_range_min !== undefined
    || form.score_range_max !== undefined
    || form.rank_range_min !== undefined
    || form.rank_range_max !== undefined
  ) {
    return true;
  }
  if (normalizeOptionalString(form.reference_exam_name) || normalizeOptionalString(form.note)) {
    return true;
  }
  return false;
}

export function formatVolunteerDraftItemLabel(item: VolunteerDraftItem): string {
  return [
    item.candidate.college_name,
    item.candidate.major_name || item.candidate.major_group_code || "院校级计划",
  ]
    .filter(Boolean)
    .join(" / ");
}

export function formatVolunteerDraftSummaryLabel(item: Pick<VolunteerDraftSummary, "name" | "batch" | "exam_mode">): string {
  const segments = [item.name, item.batch || "未设批次", item.exam_mode || "未设模式"].filter(Boolean);
  return segments.join(" / ");
}

export function buildVolunteerEmploymentProfile(candidate: VolunteerWorkbenchCandidate): VolunteerEmploymentProfile {
  const majorDirection = normalizeOptionalString(candidate.major_direction ?? "");
  const careerPath = normalizeOptionalString(candidate.career_path ?? "");
  const majorNote = normalizeOptionalString(candidate.major_note ?? "");
  const matchedDirections = (candidate.matched_direction_names_json ?? []).filter(Boolean);
  const backendSummary = normalizeOptionalString(candidate.career_match_summary ?? "");
  const mergedSummary = [careerPath, majorNote].filter(Boolean).join("；");
  const targetDirection = matchedDirections.join(" / ") || majorDirection || extractCareerDirection(careerPath) || "待维护";
  return {
    targetDirection,
    matchStrength: normalizeEmploymentMatchStrength(
      candidate.career_match_strength,
      Boolean(matchedDirections.length || majorDirection),
      Boolean(careerPath || majorNote),
    ),
    needsPostgraduate:
      typeof candidate.requires_postgraduate_path === "boolean"
        ? candidate.requires_postgraduate_path
          ? "yes"
          : "not_explicit"
        : detectEmploymentHint([careerPath, majorNote], postgraduateKeywords),
    needsCertificate:
      typeof candidate.requires_certificate_path === "boolean"
        ? candidate.requires_certificate_path
          ? "yes"
          : "not_explicit"
        : detectEmploymentHint([careerPath, majorNote], certificateKeywords),
    summary: backendSummary || mergedSummary || majorDirection || "当前专业画像还未维护就业方向说明。",
  };
}

export function buildVolunteerCandidateLayeringCopy(candidate: VolunteerWorkbenchCandidate): string {
  const resultLabel = resultTypeLabels[candidate.result_type] ?? candidate.result_type;
  const details: string[] = [];
  if (candidate.score_basis === "rank" && candidate.ratio !== undefined && candidate.ratio !== null && candidate.reference_rank) {
    details.push(
      `按位次分层：当前位次与参考位次比值约为 ${candidate.ratio.toFixed(4)}，参考位次 ${candidate.reference_rank}。`,
    );
  } else if ((candidate.score_basis === "score" || candidate.score_basis === "comprehensive_score") && candidate.latest_min_score !== undefined && candidate.latest_min_score !== null) {
    const scoreValue = candidate.latest_min_score;
    details.push(`按分数参考：最近最低分 ${scoreValue}，当前结果按分数差额落层。`);
  } else {
    details.push("当前分层依据仍以已有录取参考为主，需结合原始数据人工复核。");
  }
  if (candidate.risk_flags_json.includes("rank_missing")) {
    details.push("当前缺少稳定位次口径，已改按分数参考。");
  }
  if (candidate.risk_flags_json.includes("sample_insufficient")) {
    details.push("当前位次样本偏少，分层稳定性有限。");
  }
  return `${resultLabel}判断：${details.join("")}`;
}

export function buildVolunteerCandidateRuleCopy(candidate: VolunteerWorkbenchCandidate): string | null {
  if (!candidate.matched_rule_exam_mode && !candidate.matched_rule_batch) {
    return null;
  }
  const parts = [
    candidate.province,
    String(candidate.year),
    candidate.matched_rule_exam_mode,
    candidate.matched_rule_batch,
  ].filter(Boolean);
  const suffix = candidate.matched_rule_is_baseline
    ? "系统基线"
    : candidate.matched_rule_candidate_type
      ? "专用规则"
      : "通用规则";
  return `命中规则：${parts.join(" / ")} · ${suffix}`;
}

export function buildVolunteerCandidateReferenceCopy(candidate: VolunteerWorkbenchCandidate): string | null {
  if (!candidate.reference_scope && !candidate.reference_record_count) {
    return null;
  }
  const scopeLabel = candidate.reference_scope === "college"
    ? "院校线参考"
    : candidate.reference_scope === "score_line"
      ? "省控线参考"
      : candidate.reference_scope === "plan_only"
        ? "计划清单参考"
      : "专业线参考";
  const yearLabel = candidate.reference_years_json.length ? `${candidate.reference_years_json.join(" / ")} 年` : "年份待补";
  const sampleLabel = candidate.reference_scope === "score_line"
    ? "省级控制线口径"
    : candidate.reference_scope === "plan_only"
      ? "当年计划口径"
      : `${candidate.reference_record_count} 条样本`;
  const sourceLabel = candidate.reference_source_notes_json.length
    ? `来源：${candidate.reference_source_notes_json.join("；")}`
    : null;
  return [scopeLabel, yearLabel, sampleLabel, sourceLabel].filter(Boolean).join(" · ");
}

export function buildVolunteerCandidateExplanationNotes(candidate: VolunteerWorkbenchCandidate): string[] {
  const notes: string[] = [];

  if (candidate.matched_rule_is_baseline) {
    notes.push("当前只命中系统基线，说明该省该年缺少更细规则，志愿上限、单位结构和征集志愿仍需按当年公告复核。");
  } else if (candidate.matched_rule_candidate_type) {
    const candidateTypeLabel = candidateTypeLabels[candidate.matched_rule_candidate_type] ?? candidate.matched_rule_candidate_type;
    notes.push(`当前命中${candidateTypeLabel}专用规则；同省同年其他类别可能适用不同志愿结构。`);
  } else if (candidate.matched_rule_exam_mode || candidate.matched_rule_batch) {
    notes.push("当前按通用规则解释；若后续补齐更细类别规则，候选顺序和说明可能变化。");
  }

  if (candidate.match_tags_json.includes("兼容模式命中")) {
    notes.push(`当前请求模式与计划模式不完全一致，系统按“${candidate.exam_mode}”兼容口径预览，填报前需复核该省当年模式细则。`);
  }

  if (candidate.reference_scope === "college" && candidate.major_id) {
    notes.push("当前专业缺少专业线，先回退到院校线参考；同校不同专业结果仍可能继续变化。");
  }

  if (candidate.risk_flags_json.includes("general_reference_fallback")) {
    notes.push("当前缺少该类别专门录取结果，先按普通类录取结果做方向性参考；这不是该类别专门录取把握，正式填报前仍需结合类别公告、批次规则和学校章程复核。");
  }

  if (candidate.reference_scope === "score_line") {
    notes.push("当前结果只按省级控制线做资格初筛，不能直接视作院校或专业录取把握。");
  }

  if (candidate.reference_scope === "plan_only") {
    notes.push("当前结果只按当年招生计划清单做方向性初筛，不能直接作为冲稳保或录取把握判断。");
  }

  if (candidate.reference_record_count > 0 && candidate.province.trim()) {
    const yearLabel = candidate.reference_years_json.length
      ? `${candidate.reference_years_json.join(" / ")} 年`
      : "现有年份";
    notes.push(`录取参考只取 ${candidate.province} ${yearLabel} 样本，同校跨省结果不同属于正常口径差异。`);
  }

  const staleReferenceGap = getVolunteerReferenceYearGap(candidate.year, candidate.reference_years_json);
  if (staleReferenceGap !== null && staleReferenceGap >= 2) {
    notes.push(
      `当前录取参考最近只到 ${Math.max(...candidate.reference_years_json)} 年，与 ${candidate.year} 目标年相差 ${staleReferenceGap} 年；若近一年数据尚未补齐，排序和解释会偏保守。`,
    );
  }

  if (candidate.match_tags_json.includes("待核对选科") && normalizeOptionalString(candidate.subject_requirement ?? "")) {
    notes.push(`该计划要求“${candidate.subject_requirement}”，最终填报前仍需核对选科限制。`);
  }

  return uniqueStrings(notes);
}

function volunteerDraftComparisonKey(item: VolunteerDraftItem): string {
  if (item.plan_id) return String(item.plan_id);
  return [
    item.candidate.college_id,
    item.candidate.major_id ?? 0,
    item.candidate.major_group_code ?? "",
    item.candidate.batch,
    item.candidate.exam_mode,
  ].join("-");
}

function volunteerDraftComparisonLabel(item: VolunteerDraftItem): string {
  return [
    item.candidate.college_name,
    item.candidate.major_name || item.candidate.major_group_code || "院校级计划",
  ]
    .filter(Boolean)
    .join(" / ");
}

function buildVolunteerDraftComparisonEntry(
  currentItem: VolunteerDraftItem | undefined,
  compareItem: VolunteerDraftItem | undefined,
): VolunteerDraftComparisonEntry {
  const item = currentItem ?? compareItem;
  return {
    key: currentItem ? volunteerDraftComparisonKey(currentItem) : volunteerDraftComparisonKey(compareItem as VolunteerDraftItem),
    label: volunteerDraftComparisonLabel(item as VolunteerDraftItem),
    currentOrder: currentItem?.order,
    compareOrder: compareItem?.order,
    currentType: currentItem?.candidate.result_type,
    compareType: compareItem?.candidate.result_type,
  };
}

export function buildVolunteerDraftComparison(
  currentItems: VolunteerDraftItem[],
  compareItems: VolunteerDraftItem[],
): VolunteerDraftComparisonSummary {
  const currentMap = new Map(currentItems.map((item) => [volunteerDraftComparisonKey(item), item]));
  const compareMap = new Map(compareItems.map((item) => [volunteerDraftComparisonKey(item), item]));

  const added: VolunteerDraftComparisonEntry[] = [];
  const removed: VolunteerDraftComparisonEntry[] = [];
  const reordered: VolunteerDraftComparisonEntry[] = [];
  const regrouped: VolunteerDraftComparisonEntry[] = [];
  let commonCount = 0;

  currentMap.forEach((currentItem, key) => {
    const compareItem = compareMap.get(key);
    if (!compareItem) {
      added.push(buildVolunteerDraftComparisonEntry(currentItem, undefined));
      return;
    }
    commonCount += 1;
    if (currentItem.order !== compareItem.order) {
      reordered.push(buildVolunteerDraftComparisonEntry(currentItem, compareItem));
    }
    if (currentItem.candidate.result_type !== compareItem.candidate.result_type) {
      regrouped.push(buildVolunteerDraftComparisonEntry(currentItem, compareItem));
    }
  });

  compareMap.forEach((compareItem, key) => {
    if (!currentMap.has(key)) {
      removed.push(buildVolunteerDraftComparisonEntry(undefined, compareItem));
    }
  });

  return {
    added,
    removed,
    reordered,
    regrouped,
    commonCount,
  };
}

function formatOptionalNumber(value?: number | null): string | null {
  if (value === undefined || value === null) return null;
  return String(value);
}

function getVolunteerReferenceYearGap(targetYear: number, referenceYears: number[]): number | null {
  if (!referenceYears.length) {
    return null;
  }
  const latestYear = Math.max(...referenceYears);
  if (!Number.isFinite(latestYear)) {
    return null;
  }
  return targetYear - latestYear;
}

function collectActiveSoftFilters(form: VolunteerWorkbenchFormState): string[] {
  const labels: string[] = [];
  if (normalizeOptionalString(form.subject_combination)) labels.push("选科组合");
  if (uniqueStrings(form.target_regions_json).length) labels.push("目标地区");
  if (uniqueStrings(form.school_level_tags_json).length) labels.push("院校层级");
  if (normalizeOptionalString(form.major_keyword)) labels.push("专业关键词");
  return labels;
}

export function buildVolunteerWorkbenchExplanation(
  form: VolunteerWorkbenchFormState,
  preview: VolunteerWorkbenchPreviewResponse | null,
  selectedRule: ProvinceVolunteerRule | null,
  directionNameMap: Map<number, string> = new Map(),
): VolunteerWorkbenchExplanation {
  const items = [
    { label: "省份", value: form.province },
    { label: "年份", value: String(form.target_year ?? new Date().getFullYear()) },
  ];

  if (normalizeOptionalString(form.batch)) {
    items.push({ label: "批次", value: form.batch.trim() });
  }
  if (normalizeOptionalString(form.exam_mode)) {
    items.push({ label: "模式", value: form.exam_mode.trim() });
  }
  if (normalizeOptionalString(form.candidate_type)) {
    items.push({ label: "类别", value: candidateTypeLabels[form.candidate_type.trim()] ?? form.candidate_type.trim() });
  }
  items.push({ label: "分数模式", value: scoreInputModeLabels[form.score_input_mode] ?? form.score_input_mode });

  const targetRegions = uniqueStrings(form.target_regions_json);
  if (targetRegions.length) {
    items.push({ label: "地区", value: targetRegions.join(" / ") });
  }

  const schoolLevels = uniqueStrings(form.school_level_tags_json);
  if (schoolLevels.length) {
    items.push({ label: "层级", value: schoolLevels.join(" / ") });
  }

  if (normalizeOptionalString(form.major_keyword)) {
    items.push({ label: "专业", value: form.major_keyword.trim() });
  }
  if (normalizeOptionalString(form.subject_combination)) {
    items.push({ label: "选科", value: form.subject_combination.trim() });
  }

  const selectedDirections = [
    { label: "首选方向", id: form.primary_direction_id },
    { label: "次选方向", id: form.secondary_direction_id },
    { label: "替代方向", id: form.alternative_direction_id },
  ]
    .map((item) => {
      if (!item.id) return null;
      return { label: item.label, value: directionNameMap.get(item.id) ?? `方向 ${item.id}` };
    })
    .filter((item): item is { label: string; value: string } => Boolean(item));
  items.push(...selectedDirections);

  if (form.priority_focuses_json.length) {
    items.push({
      label: "偏好重点",
      value: uniqueStrings(form.priority_focuses_json).map((item) => careerPriorityFocusLabels[item] ?? item).join(" / "),
    });
  }

  const preferredIndustries = uniqueStrings(form.preferred_industries_json);
  if (preferredIndustries.length) {
    items.push({ label: "目标行业", value: preferredIndustries.join(" / ") });
  }

  const preferredJobTypes = uniqueStrings(form.preferred_job_types_json);
  if (preferredJobTypes.length) {
    items.push({ label: "目标岗位", value: preferredJobTypes.join(" / ") });
  }

  const targetCities = uniqueStrings(form.target_employment_cities_json);
  if (targetCities.length) {
    items.push({ label: "就业城市", value: targetCities.join(" / ") });
  }

  const effectiveRank = formatOptionalNumber(form.student_rank_override ?? preview?.effective_rank ?? preview?.snapshot_rank);
  if (effectiveRank && form.score_input_mode !== "actual_score" && form.score_input_mode !== "estimated_score" && form.score_input_mode !== "score_range") {
    items.push({ label: "位次", value: effectiveRank });
  }

  const totalScore = formatOptionalNumber(form.comprehensive_score ?? preview?.total_score);
  if (totalScore && form.score_input_mode !== "rank_range" && form.score_input_mode !== "score_range") {
    items.push({ label: "总分", value: totalScore });
  }
  if (form.score_range_min !== undefined && form.score_range_max !== undefined) {
    items.push({ label: "分数区间", value: `${form.score_range_min} - ${form.score_range_max}` });
  }
  if (form.rank_range_min !== undefined && form.rank_range_max !== undefined) {
    items.push({ label: "位次区间", value: `${form.rank_range_min} - ${form.rank_range_max}` });
  }
  if (normalizeOptionalString(form.reference_exam_name)) {
    items.push({ label: "参考考试", value: form.reference_exam_name.trim() });
  }
  if (form.score_input_mode === "score_range" || form.score_input_mode === "rank_range") {
    items.push({ label: "风险偏好", value: riskPreferenceLabels[form.risk_preference] ?? form.risk_preference });
  }

  const batchLabel = normalizeOptionalString(form.batch) ?? "全部批次";
  const examModeLabel = normalizeOptionalString(form.exam_mode) ?? "全部模式";
  const notes = [`先按 ${form.province} / ${form.target_year ?? new Date().getFullYear()} / ${batchLabel} / ${examModeLabel} 限定招生计划范围。`];
  notes.push(`当前分数输入模式为“${scoreInputModeLabels[form.score_input_mode] ?? form.score_input_mode}”。`);
  if (form.use_historical_mapping) {
    notes.push("已开启历年映射估算提示，正式出分后建议重新核算。");
  }

  const softFilters = collectActiveSoftFilters(form);
  if (softFilters.length) {
    notes.push(`本次附加筛选包含 ${softFilters.join("、")}。`);
  }

  if (selectedDirections.length || preferredIndustries.length || preferredJobTypes.length) {
    notes.push("当前职业意向已记录到工作台和草稿中，后续可直接复用到排序增强与结果解释。");
  }

  const acceptanceFlags = [
    form.accepts_postgraduate ? "接受读研路径" : null,
    form.accepts_public_service ? "接受考公/考编路径" : null,
    form.accepts_certificate ? "接受资格证路径" : null,
    form.accepts_long_training ? "接受长培养周期" : null,
  ].filter(Boolean);
  if (acceptanceFlags.length) {
    notes.push(`当前可接受路径：${acceptanceFlags.join("、")}。`);
  }

  const hasRuleSpecificNote = Boolean(
    preview?.input_notes.some((item) =>
      ["省份规则", "批次规则", "模式规则", "通用考生规则", "系统基线", "志愿上限与单位类型"].some((keyword) =>
        item.includes(keyword),
      ),
    ),
  );

  if (selectedRule) {
    notes.push(
      `当前命中 ${selectedRule.province} ${selectedRule.year} ${selectedRule.exam_mode} ${selectedRule.batch} 规则，志愿上限 ${selectedRule.volunteer_limit}，单位类型为 ${selectedRule.volunteer_unit_type}。`,
    );
    if (selectedRule.special_rules_json.length) {
      notes.push(`规则附加要求：${selectedRule.special_rules_json.join("；")}。`);
    }
  } else if (!hasRuleSpecificNote) {
    notes.push("当前未命中明确省份规则，上限与志愿单位需人工复核。");
  }

  if (!preview) {
    notes.push("选择学生与考试后刷新候选池，系统才会生成候选计划和风险分层。");
    return { items, notes };
  }

  if (preview.input_notes.length) {
    notes.push(...preview.input_notes);
  }

  if (preview.candidate_count) {
    const rankBasis = formatOptionalNumber(preview.effective_rank);
    notes.push(
      rankBasis
        ? `当前候选池已按生效位次 ${rankBasis} 与近年录取基线做冲稳保分层。`
        : "当前候选池已按近年录取基线做冲稳保分层，但位次仍需人工复核。",
    );
  } else {
    notes.push(
      softFilters.length
        ? `当前没有命中候选计划，建议优先放宽 ${softFilters.join("、")} 后再刷新。`
        : "当前没有命中候选计划，建议回看招生计划、录取基线或位次条件是否完整。",
    );
  }

  return { items, notes };
}

function validateCareerPreferenceDirections(
  primaryDirectionId?: number,
  secondaryDirectionId?: number,
  alternativeDirectionId?: number,
): string | null {
  const selectedIds = [primaryDirectionId, secondaryDirectionId, alternativeDirectionId].filter(
    (item): item is number => typeof item === "number",
  );
  if (selectedIds.length !== new Set(selectedIds).size) {
    return "首选、次选和替代就业方向不能重复";
  }
  return null;
}

export function buildVolunteerDraftChecks(
  draftItems: VolunteerDraftItem[],
  selectedRule: ProvinceVolunteerRule | null,
  remainingSlots: number | null,
): VolunteerDraftCheckItem[] {
  const checks: VolunteerDraftCheckItem[] = [];

  checks.push(
    draftItems.length
      ? {
          level: "success",
          title: `当前草稿已纳入 ${draftItems.length} 条志愿`,
          detail: "可以继续排序、补齐保底项，或直接保存后打印导出。",
        }
      : {
          level: "warning",
          title: "当前还没有形成志愿表草稿",
          detail: "先从左侧候选池加入至少 1 条计划，再进行保存或导出。",
        },
  );

  if (!selectedRule) {
    checks.push({
      level: "info",
      title: "未命中明确省份规则",
      detail: "当前上限、志愿单位和调剂要求仍需人工复核，不建议直接定稿。",
    });
  } else if (remainingSlots === null) {
    checks.push({
      level: "info",
      title: "当前规则未设置可计算的剩余志愿位",
      detail: "请结合省份规则手工确认志愿数是否超限。",
    });
  } else if (remainingSlots > 0) {
    checks.push({
      level: "warning",
      title: `还有 ${remainingSlots} 个志愿位待补齐`,
      detail: "建议补齐稳妥或保底项，避免只保留少量候选后直接定稿。",
    });
  } else {
    checks.push({
      level: "success",
      title: "当前志愿数已达到规则上限",
      detail: "若仍需调整，请先移除或重排现有志愿，再加入新的候选计划。",
    });
  }

  if (!draftItems.length) {
    checks.push({
      level: "info",
      title: "加入志愿后再检查保底和风险项",
      detail: "系统会在形成草稿后提示保底不足、选科复核和专业线缺失等风险。",
    });
    return checks;
  }

  const safeCount = draftItems.filter((item) => item.candidate.result_type === "safe").length;
  checks.push(
    safeCount
      ? {
          level: "success",
          title: `当前草稿已包含 ${safeCount} 条保底志愿`,
          detail: "基础保底提醒已满足，可继续检查排序和调剂策略。",
        }
      : {
          level: "warning",
          title: "当前草稿暂未包含保底志愿",
          detail: "建议至少补 1 条保底计划，避免草稿过度集中在冲刺或稳妥层。",
        },
  );

  const subjectCheckCount = draftItems.filter((item) =>
    item.candidate.risk_flags_json.includes("subject_requirement_check")).length;
  checks.push(
    subjectCheckCount
      ? {
          level: "warning",
          title: `${subjectCheckCount} 条志愿仍需复核选科要求`,
          detail: "导出或定稿前需逐条确认招生章程中的选科限制是否满足。",
        }
      : {
          level: "success",
          title: "当前草稿未发现待复核的选科提示",
          detail: "已选志愿暂未命中“需复核选科要求”风险标记。",
        },
  );

  const fallbackCount = draftItems.filter((item) =>
    item.candidate.risk_flags_json.includes("major_baseline_missing")).length;
  if (fallbackCount) {
    checks.push({
      level: "info",
      title: `${fallbackCount} 条志愿按院校线做了专业参考`,
      detail: "这些计划缺少专业线，只能先按院校近年录取基线参考，建议人工复核。",
    });
  }

  return checks;
}

function extractCareerDirection(value?: string): string | undefined {
  if (!value) return undefined;
  const [firstSegment] = value.split(/[、,，/；;]/);
  return normalizeOptionalString(firstSegment ?? "");
}

function detectEmploymentHint(
  values: Array<string | undefined>,
  keywords: string[],
): VolunteerEmploymentHintStatus {
  const normalizedValues = values.filter(Boolean) as string[];
  if (!normalizedValues.length) {
    return "pending";
  }
  const sourceText = normalizedValues.join(" ");
  return keywords.some((keyword) => sourceText.includes(keyword)) ? "yes" : "not_explicit";
}

function normalizeEmploymentMatchStrength(
  value: string | null | undefined,
  hasDirection: boolean,
  hasProfileCopy: boolean,
): VolunteerEmploymentProfile["matchStrength"] {
  if (value === "core" || value === "high" || value === "medium" || value === "transferable") {
    return value;
  }
  if (hasDirection && hasProfileCopy) {
    return "core";
  }
  if (hasDirection || hasProfileCopy) {
    return "transferable";
  }
  return "pending";
}

function normalizeVolunteerCareerPreference(
  value: VolunteerWorkbenchFormState | StudentCareerPreference | StudentCareerPreferencePayload | null | undefined,
): StudentCareerPreferencePayload {
  return {
    primary_direction_id: value?.primary_direction_id,
    secondary_direction_id: value?.secondary_direction_id,
    alternative_direction_id: value?.alternative_direction_id,
    priority_focuses_json: uniqueStrings(value?.priority_focuses_json ?? []) as StudentCareerPreferencePayload["priority_focuses_json"],
    preferred_industries_json: uniqueStrings(value?.preferred_industries_json ?? []),
    preferred_job_types_json: uniqueStrings(value?.preferred_job_types_json ?? []),
    target_employment_cities_json: uniqueStrings(value?.target_employment_cities_json ?? []),
    accepts_postgraduate: value?.accepts_postgraduate ?? false,
    accepts_public_service: value?.accepts_public_service ?? false,
    accepts_certificate: value?.accepts_certificate ?? false,
    accepts_long_training: value?.accepts_long_training ?? false,
  };
}
