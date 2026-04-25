export type PathwayBooleanValue = boolean | null;

export interface StudentPathwayProfilePayload {
  province: string;
  candidate_type: string | null;
  exam_type: string | null;
  subject_combination: string | null;
  spring_exam_category: string | null;
  art_track: string | null;
  sports_track: string | null;
  has_gaokao_registration: PathwayBooleanValue;
  is_fresh_graduate: PathwayBooleanValue;
  is_vocational_student: PathwayBooleanValue;
  is_social_candidate: PathwayBooleanValue;
  has_high_school_equivalent: PathwayBooleanValue;
  accept_private_college: PathwayBooleanValue;
  accept_sino_foreign: PathwayBooleanValue;
  accept_junior_college: PathwayBooleanValue;
  accept_outside_province: PathwayBooleanValue;
  accept_early_batch: PathwayBooleanValue;
  accept_service_commitment: PathwayBooleanValue;
  accept_interview_or_physical_test: PathwayBooleanValue;
  career_preferences_json: Record<string, unknown>;
  region_preferences_json: Record<string, unknown>;
  family_constraints_json: Record<string, unknown>;
  known_body_limitations_json: Record<string, unknown>;
  materials_json: Record<string, boolean>;
  note: string | null;
  is_active: boolean;
}

export interface StudentPathwayProfile extends StudentPathwayProfilePayload {
  id: number | null;
  student_id: number;
  student_name?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface StudentPathwayRuleEvaluation {
  rule_code: string;
  rule_name: string;
  rule_type: string;
  severity: string;
  result: string;
  message?: string | null;
  manual_review_required: boolean;
  missing_material_key?: string | null;
}

export interface StudentPathwayMissingMaterial {
  rule_code: string;
  material_key: string;
  material_label?: string | null;
  gap_type?: string | null;
  message?: string | null;
  next_action?: string | null;
}

export interface StudentPathwayEvaluation {
  id: number | null;
  student_id: number;
  pathway_id: number;
  target_year: number;
  pathway_code?: string | null;
  pathway_name?: string | null;
  pathway_group?: string | null;
  status: string;
  status_label: string;
  score?: number | null;
  confidence_level: string;
  matched_rules_json: StudentPathwayRuleEvaluation[];
  failed_rules_json: StudentPathwayRuleEvaluation[];
  warning_rules_json: StudentPathwayRuleEvaluation[];
  missing_materials_json: StudentPathwayMissingMaterial[];
  recommendation_depth: string;
  summary?: string | null;
  next_actions_json: string[];
}

export interface StudentPathwayEvaluationResponse {
  student_id: number;
  target_year: number;
  profile: StudentPathwayProfile;
  evaluations: StudentPathwayEvaluation[];
}

export interface PathwayProfileReadinessItem {
  key: string;
  label: string;
  ready: boolean;
  value: string;
}

export interface PathwayMaterialChecklistItem {
  key: string;
  label: string;
  checked: boolean;
  help: string;
}

export interface AggregatedPathwayGap {
  key: string;
  label: string;
  count: number;
  pathways: string[];
  nextAction: string;
}

export interface PathwayStatusSummaryItem {
  status: string;
  label: string;
  count: number;
}

export const pathwayCandidateTypeOptions = [
  { value: "general", label: "普通类" },
  { value: "spring_exam", label: "春季高考" },
  { value: "independent_recruitment", label: "高职单招" },
  { value: "comprehensive_evaluation", label: "高职综评" },
  { value: "art", label: "艺术类" },
  { value: "sports", label: "体育类" },
];

export const pathwayExamTypeOptions = [
  { value: "summer_gaokao", label: "夏季高考" },
  { value: "spring_exam", label: "春季高考" },
  { value: "vocational_single_exam", label: "高职单招" },
  { value: "vocational_comprehensive", label: "高职综评" },
  { value: "sports_single_exam", label: "体育单招" },
  { value: "high_level_sports", label: "高水平运动队" },
];

export const pathwayBooleanOptions: Array<{ value: PathwayBooleanValue; label: string }> = [
  { value: true, label: "已确认" },
  { value: false, label: "不符合 / 不接受" },
  { value: null, label: "未确认" },
];

export const pathwayMaterialDefinitions: Array<{ key: string; label: string; help: string }> = [
  { key: "gaokao_registration", label: "高考报名确认材料", help: "报名信息、报名确认截图或校内核验记录。" },
  { key: "special_type_score_line_ready", label: "特殊类型控制线或分数线确认", help: "当年控制线发布后再用于特殊类型初筛。" },
  { key: "special_type_qualification", label: "特殊类型资格名单或测试材料", help: "高校专项、综合评价或其他特殊类型的报名、测试、名单材料。" },
  { key: "high_school_equivalent", label: "高中阶段毕业证书或同等学力材料", help: "社会人员走单招等路径时需要人工核验。" },
  { key: "retired_soldier_identity", label: "退役士兵身份或免试资格材料", help: "退役士兵走单招时需单独核对测试方式或免试条件。" },
  { key: "single_exam_major_category_match", label: "单招目标专业类别或技能测试匹配材料", help: "确认目标专业、技能测试或适应性测试与学生身份和专业基础匹配。" },
  { key: "single_exam_college_chapter_plan", label: "单招院校章程和分专业计划", help: "正式报名前逐校核对报名时间、测试方式、专业类别和录取规则。" },
  { key: "comprehensive_quality_evaluation", label: "综合素质评价材料", help: "高职综评路径需要提前整理。" },
  { key: "comprehensive_test_or_interview", label: "综评素质测试或面试安排", help: "不同院校测试方式和成绩组成不同，需要逐校核对。" },
  { key: "comprehensive_college_chapter_plan", label: "综评院校章程和分专业计划", help: "缺章程或分专业计划时只能保留人工核验提醒。" },
  { key: "spring_exam_skill_score", label: "春季高考知识与技能考试成绩", help: "春考本科/专科初筛需要结合知识与技能考试成绩。" },
  { key: "spring_exam_score_line", label: "春季高考类别分数线", help: "按专业类别核对本科或专科批分数线。" },
  { key: "spring_exam_college_plan_chapter", label: "春季高考分专业计划和院校章程", help: "核对目标院校是否按对应专业类别招生及章程限制。" },
  { key: "art_exam_score", label: "艺术统考、校考或联考成绩", help: "艺术类路径仅能在成绩和文化线明确后初筛。" },
  { key: "sports_test_score", label: "体育专业测试成绩", help: "体育常规批需要结合体育专业测试成绩。" },
  { key: "athlete_level_certificate", label: "体育单招运动员技术等级证书", help: "体育单招路径需要核对等级、项目和报名系统。" },
  { key: "high_level_athlete_level", label: "高水平运动队运动员等级材料", help: "高水平运动队通常要求一级及以上等级并逐校核验。" },
];

const profileFieldLabels: Record<string, string> = {
  province: "生源地",
  candidate_type: "考生类型",
  exam_type: "考试类型",
  subject_combination: "选科组合",
  spring_exam_category: "春考专业类别",
  art_track: "艺术类别",
  sports_track: "体育类别",
  has_gaokao_registration: "高考报名状态",
  is_fresh_graduate: "普通高中应届状态",
  is_vocational_student: "中职学生身份",
  is_social_candidate: "社会人员身份",
  has_high_school_equivalent: "高中阶段学历或同等学力",
  accept_private_college: "民办院校接受度",
  accept_sino_foreign: "中外合作接受度",
  accept_junior_college: "专科接受度",
  accept_outside_province: "省外院校接受度",
  accept_early_batch: "提前批接受度",
  accept_service_commitment: "定向服务约束接受度",
  accept_interview_or_physical_test: "面试体检政审接受度",
};

const statusOrder = ["suitable", "possible", "manual_review", "insufficient_data", "not_recommended", "not_applicable"];

export function createStudentPathwayProfileForm(): StudentPathwayProfilePayload {
  return {
    province: "山东",
    candidate_type: "general",
    exam_type: "summer_gaokao",
    subject_combination: null,
    spring_exam_category: null,
    art_track: null,
    sports_track: null,
    has_gaokao_registration: null,
    is_fresh_graduate: null,
    is_vocational_student: null,
    is_social_candidate: null,
    has_high_school_equivalent: null,
    accept_private_college: null,
    accept_sino_foreign: null,
    accept_junior_college: null,
    accept_outside_province: null,
    accept_early_batch: null,
    accept_service_commitment: null,
    accept_interview_or_physical_test: null,
    career_preferences_json: {},
    region_preferences_json: {},
    family_constraints_json: {},
    known_body_limitations_json: {},
    materials_json: createDefaultMaterials(),
    note: null,
    is_active: true,
  };
}

export function createDefaultMaterials(): Record<string, boolean> {
  return Object.fromEntries(pathwayMaterialDefinitions.map((item) => [item.key, false]));
}

export function applyPathwayProfileToForm(
  form: StudentPathwayProfilePayload,
  profile: StudentPathwayProfile,
): void {
  Object.assign(form, {
    province: profile.province || "山东",
    candidate_type: profile.candidate_type ?? null,
    exam_type: profile.exam_type ?? null,
    subject_combination: profile.subject_combination ?? null,
    spring_exam_category: profile.spring_exam_category ?? null,
    art_track: profile.art_track ?? null,
    sports_track: profile.sports_track ?? null,
    has_gaokao_registration: profile.has_gaokao_registration ?? null,
    is_fresh_graduate: profile.is_fresh_graduate ?? null,
    is_vocational_student: profile.is_vocational_student ?? null,
    is_social_candidate: profile.is_social_candidate ?? null,
    has_high_school_equivalent: profile.has_high_school_equivalent ?? null,
    accept_private_college: profile.accept_private_college ?? null,
    accept_sino_foreign: profile.accept_sino_foreign ?? null,
    accept_junior_college: profile.accept_junior_college ?? null,
    accept_outside_province: profile.accept_outside_province ?? null,
    accept_early_batch: profile.accept_early_batch ?? null,
    accept_service_commitment: profile.accept_service_commitment ?? null,
    accept_interview_or_physical_test: profile.accept_interview_or_physical_test ?? null,
    career_preferences_json: profile.career_preferences_json ?? {},
    region_preferences_json: profile.region_preferences_json ?? {},
    family_constraints_json: profile.family_constraints_json ?? {},
    known_body_limitations_json: profile.known_body_limitations_json ?? {},
    materials_json: normalizeMaterials(profile.materials_json),
    note: profile.note ?? null,
    is_active: profile.is_active,
  });
}

export function buildStudentPathwayProfilePayload(form: StudentPathwayProfilePayload): StudentPathwayProfilePayload {
  return {
    ...form,
    province: normalizeString(form.province) ?? "山东",
    candidate_type: normalizeString(form.candidate_type),
    exam_type: normalizeString(form.exam_type),
    subject_combination: normalizeString(form.subject_combination),
    spring_exam_category: normalizeString(form.spring_exam_category),
    art_track: normalizeString(form.art_track),
    sports_track: normalizeString(form.sports_track),
    career_preferences_json: form.career_preferences_json ?? {},
    region_preferences_json: form.region_preferences_json ?? {},
    family_constraints_json: form.family_constraints_json ?? {},
    known_body_limitations_json: form.known_body_limitations_json ?? {},
    materials_json: normalizeMaterials(form.materials_json),
    note: normalizeString(form.note),
  };
}

export function buildPathwayProfileReadiness(form: StudentPathwayProfilePayload): PathwayProfileReadinessItem[] {
  const items: Array<{ key: keyof StudentPathwayProfilePayload; label: string; value: unknown }> = [
    { key: "province", label: "生源地", value: form.province },
    { key: "candidate_type", label: "考生类型", value: form.candidate_type },
    { key: "subject_combination", label: "选科组合", value: form.subject_combination },
    { key: "has_gaokao_registration", label: "高考报名", value: form.has_gaokao_registration },
    { key: "accept_junior_college", label: "专科意向", value: form.accept_junior_college },
    { key: "accept_early_batch", label: "提前批意向", value: form.accept_early_batch },
    { key: "accept_service_commitment", label: "定向服务意向", value: form.accept_service_commitment },
    { key: "accept_interview_or_physical_test", label: "体检面试政审意向", value: form.accept_interview_or_physical_test },
  ];
  return items.map((item) => ({
    key: item.key,
    label: item.label,
    ready: hasProfileValue(item.value),
    value: formatProfileValue(item.value),
  }));
}

export function buildPathwayMaterialChecklist(materials: Record<string, unknown>): PathwayMaterialChecklistItem[] {
  const normalized = normalizeMaterials(materials);
  return pathwayMaterialDefinitions.map((item) => ({
    ...item,
    checked: normalized[item.key] === true,
  }));
}

export function collectStudentPathwayGaps(evaluations: StudentPathwayEvaluation[]): AggregatedPathwayGap[] {
  const byKey = new Map<string, AggregatedPathwayGap>();
  evaluations.forEach((evaluation) => {
    evaluation.missing_materials_json.forEach((item) => {
      const key = item.material_key || item.rule_code;
      const current = byKey.get(key) ?? {
        key,
        label: item.material_label || formatPathwayMaterialKey(key),
        count: 0,
        pathways: [],
        nextAction: item.next_action || item.message || "补齐该项后重新评估。",
      };
      current.count += 1;
      if (evaluation.pathway_name && !current.pathways.includes(evaluation.pathway_name)) {
        current.pathways.push(evaluation.pathway_name);
      }
      byKey.set(key, current);
    });
  });
  return [...byKey.values()].sort((left, right) => right.count - left.count || left.label.localeCompare(right.label, "zh-CN"));
}

export function summarizePathwayStatuses(evaluations: StudentPathwayEvaluation[]): PathwayStatusSummaryItem[] {
  const counts = new Map<string, { label: string; count: number }>();
  evaluations.forEach((item) => {
    const current = counts.get(item.status) ?? { label: item.status_label || formatPathwayStatus(item.status), count: 0 };
    current.count += 1;
    counts.set(item.status, current);
  });
  return [...counts.entries()]
    .map(([status, item]) => ({ status, label: item.label, count: item.count }))
    .sort((left, right) => statusOrder.indexOf(left.status) - statusOrder.indexOf(right.status));
}

export function formatPathwayMaterialKey(key: string): string {
  const material = pathwayMaterialDefinitions.find((item) => item.key === key);
  return material?.label ?? profileFieldLabels[key] ?? key;
}

export function formatPathwayStatus(status: string): string {
  const mapping: Record<string, string> = {
    suitable: "适合关注",
    possible: "可能适合",
    not_recommended: "不建议",
    insufficient_data: "信息不足",
    manual_review: "需人工复核",
    not_applicable: "当前不适用",
  };
  return mapping[status] ?? status;
}

export function pathwayStatusTagType(status: string): "success" | "warning" | "danger" | "info" | "primary" {
  if (status === "suitable") return "success";
  if (status === "possible" || status === "manual_review") return "warning";
  if (status === "not_recommended") return "danger";
  if (status === "insufficient_data") return "info";
  return "primary";
}

function normalizeMaterials(materials: Record<string, unknown> | null | undefined): Record<string, boolean> {
  const normalized = createDefaultMaterials();
  Object.entries(materials ?? {}).forEach(([key, value]) => {
    normalized[key] = value === true;
  });
  return normalized;
}

function normalizeString(value: string | null | undefined): string | null {
  const normalized = value?.trim();
  return normalized ? normalized : null;
}

function hasProfileValue(value: unknown): boolean {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.trim().length > 0;
  return true;
}

function formatProfileValue(value: unknown): string {
  if (value === true) return "已确认";
  if (value === false) return "不符合 / 不接受";
  if (typeof value === "string" && value.trim()) return value.trim();
  return "未确认";
}
