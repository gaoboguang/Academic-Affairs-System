import {
  formatPathwayMaterialKey,
  formatPathwayStatus,
  pathwayCandidateTypeOptions,
  pathwayExamTypeOptions,
  pathwayStatusTagType,
  type AggregatedPathwayGap,
  type PathwayStatusSummaryItem,
  type StudentPathwayEvaluation,
  type StudentPathwayProfile,
} from "../students/studentPathwayProfile";
import type { ShandongPublicationStatus, ShandongRecommendationDataHealth } from "../recommendations/types";

export interface PathwayCenterStudentOption {
  id: number;
  student_no: string;
  name: string;
  current_grade_name?: string | null;
  current_class_name?: string | null;
  student_type?: string | null;
  origin_province?: string | null;
}

export interface GaokaoPathwayRead {
  id: number;
  province: string;
  pathway_code: string;
  pathway_name: string;
  pathway_group: string;
  student_type?: string | null;
  exam_type?: string | null;
  batch_name?: string | null;
  volunteer_mode?: string | null;
  max_volunteer_count?: number | null;
  recommendation_depth: string;
  status: string;
  source_document_id?: number | null;
  summary?: string | null;
  risk_level?: string | null;
  notes_json?: Record<string, unknown> | null;
  is_active: boolean;
}

export interface PathwayCenterProfileItem {
  key: string;
  label: string;
  value: string;
  filled: boolean;
}

export interface PathwayCenterCard {
  pathwayId: number;
  code: string;
  name: string;
  group: string;
  status: string;
  statusLabel: string;
  statusType: ReturnType<typeof pathwayStatusTagType>;
  score?: number | null;
  confidenceLabel: string;
  depthLabel: string;
  depthHelp: string;
  applicableObject: string;
  volunteerMode: string;
  summary: string;
  keyRequirements: string[];
  missingMaterials: string[];
  riskMessages: string[];
  nextActions: string[];
  canOpenRecommendation: boolean;
  evaluation: StudentPathwayEvaluation;
  pathway?: GaokaoPathwayRead;
}

export interface PathwayCenterAction {
  key: string;
  title: string;
  detail: string;
  tone: "primary" | "warning" | "danger" | "info" | "success";
}

export function formatPathwayStudentOption(student: PathwayCenterStudentOption): string {
  const meta = [student.student_no, student.current_grade_name, student.current_class_name]
    .filter(Boolean)
    .join(" · ");
  return meta ? `${student.name}（${meta}）` : student.name;
}

export function buildPathwayProfileSummary(profile: StudentPathwayProfile | null): PathwayCenterProfileItem[] {
  if (!profile) return [];
  return [
    {
      key: "province",
      label: "生源地",
      value: profile.province || "未维护",
      filled: Boolean(profile.province),
    },
    {
      key: "candidate_type",
      label: "考生类型",
      value: formatOptionLabel(pathwayCandidateTypeOptions, profile.candidate_type),
      filled: Boolean(profile.candidate_type),
    },
    {
      key: "exam_type",
      label: "考试类型",
      value: formatOptionLabel(pathwayExamTypeOptions, profile.exam_type),
      filled: Boolean(profile.exam_type),
    },
    {
      key: "subject_combination",
      label: "选科组合",
      value: profile.subject_combination || "未维护",
      filled: Boolean(profile.subject_combination),
    },
    {
      key: "spring_exam_category",
      label: "春考类别",
      value: profile.spring_exam_category || "未维护",
      filled: Boolean(profile.spring_exam_category),
    },
    {
      key: "gaokao_registration",
      label: "高考报名",
      value: formatBooleanValue(profile.has_gaokao_registration),
      filled: profile.has_gaokao_registration !== null && profile.has_gaokao_registration !== undefined,
    },
    {
      key: "fresh_graduate",
      label: "普通高中应届",
      value: formatBooleanValue(profile.is_fresh_graduate),
      filled: profile.is_fresh_graduate !== null && profile.is_fresh_graduate !== undefined,
    },
    {
      key: "vocational_student",
      label: "中职学生",
      value: formatBooleanValue(profile.is_vocational_student),
      filled: profile.is_vocational_student !== null && profile.is_vocational_student !== undefined,
    },
    {
      key: "social_candidate",
      label: "社会人员",
      value: formatBooleanValue(profile.is_social_candidate),
      filled: profile.is_social_candidate !== null && profile.is_social_candidate !== undefined,
    },
    {
      key: "junior_college",
      label: "专科意向",
      value: formatBooleanValue(profile.accept_junior_college),
      filled: profile.accept_junior_college !== null && profile.accept_junior_college !== undefined,
    },
    {
      key: "early_batch",
      label: "提前批意向",
      value: formatBooleanValue(profile.accept_early_batch),
      filled: profile.accept_early_batch !== null && profile.accept_early_batch !== undefined,
    },
  ];
}

export function buildPathwayCenterCards(
  evaluations: StudentPathwayEvaluation[],
  pathways: GaokaoPathwayRead[],
): PathwayCenterCard[] {
  const byId = new Map(pathways.map((item) => [item.id, item]));
  return [...evaluations]
    .sort((left, right) => compareEvaluationPriority(left, right))
    .map((evaluation) => {
      const pathway = byId.get(evaluation.pathway_id);
      const depth = formatRecommendationDepth(evaluation.recommendation_depth || pathway?.recommendation_depth);
      const keyRequirements = buildRequirementLines(evaluation, pathway);
      const missingMaterials = evaluation.missing_materials_json.map((item) => (
        item.material_label || formatPathwayMaterialKey(item.material_key || item.rule_code)
      ));
      const riskMessages = buildRiskMessages(evaluation, pathway);
      const nextActions = uniqueNonEmpty(evaluation.next_actions_json).slice(0, 4);
      return {
        pathwayId: evaluation.pathway_id,
        code: evaluation.pathway_code || pathway?.pathway_code || String(evaluation.pathway_id),
        name: evaluation.pathway_name || pathway?.pathway_name || "未命名路径",
        group: evaluation.pathway_group || pathway?.pathway_group || "升学路径",
        status: evaluation.status,
        statusLabel: evaluation.status_label || formatPathwayStatus(evaluation.status),
        statusType: pathwayStatusTagType(evaluation.status),
        score: evaluation.score,
        confidenceLabel: formatConfidence(evaluation.confidence_level),
        depthLabel: depth.label,
        depthHelp: depth.help,
        applicableObject: buildApplicableObject(pathway),
        volunteerMode: pathway?.volunteer_mode || "按当年政策和高校章程核验",
        summary: evaluation.summary || pathway?.summary || "该路径需要结合学生画像、官方公告和高校章程继续核对。",
        keyRequirements,
        missingMaterials,
        riskMessages,
        nextActions,
        canOpenRecommendation: (evaluation.pathway_code || pathway?.pathway_code) === "summer_general_regular"
          && (evaluation.recommendation_depth || pathway?.recommendation_depth) === "full_rank_recommendation",
        evaluation,
        pathway,
      };
    });
}

export function buildPathwayCenterActions(
  cards: PathwayCenterCard[],
  gaps: AggregatedPathwayGap[],
  dataHealth: ShandongRecommendationDataHealth | null,
): PathwayCenterAction[] {
  const actions: PathwayCenterAction[] = [];
  const firstRecommendationCard = cards.find((item) => item.canOpenRecommendation && item.status !== "not_recommended");
  if (firstRecommendationCard) {
    actions.push({
      key: "recommendation-entry",
      title: "普通类常规批可以继续看冲稳保候选",
      detail: "进入山东普通类推荐工作台后，仍要以 2026 官方计划和高校章程复核结果。",
      tone: "primary",
    });
  }
  gaps.slice(0, 3).forEach((gap) => {
    actions.push({
      key: `gap-${gap.key}`,
      title: `补齐${gap.label}`,
      detail: `${gap.nextAction} 影响路径：${gap.pathways.join("、") || "待评估路径"}`,
      tone: "warning",
    });
  });
  if (dataHealth?.gaps.length) {
    actions.push({
      key: "data-health",
      title: "先保留数据风险说明",
      detail: `${dataHealth.summary || "当前仍有数据缺口"}；正式填报前继续查看高考数据页和官方来源。`,
      tone: "danger",
    });
  }
  if (!actions.length) {
    actions.push({
      key: "manual-review",
      title: "进入逐校人工复核",
      detail: "当前没有明显材料缺口，但仍需核对官方公告、报名时间、目标高校章程和体检限制。",
      tone: "success",
    });
  }
  return dedupeActions(actions).slice(0, 5);
}

export function buildPublicationStatusHighlights(
  dataHealth: ShandongRecommendationDataHealth | null,
): ShandongPublicationStatus[] {
  if (!dataHealth) return [];
  const priority = [
    "summer_general_plan",
    "summer_general_score_rank",
    "summer_general_score_line",
    "summer_general_admission",
    "single_comprehensive_policy",
    "single_comprehensive_plan_limit",
  ];
  return [...dataHealth.publication_status]
    .sort((left, right) => {
      const leftIndex = priority.indexOf(left.key);
      const rightIndex = priority.indexOf(right.key);
      return normalizePriorityIndex(leftIndex) - normalizePriorityIndex(rightIndex);
    })
    .slice(0, 6);
}

export function buildStatusSummaryCopy(summary: PathwayStatusSummaryItem[]): string {
  if (!summary.length) return "暂无路径评估结果";
  return summary.map((item) => `${item.label} ${item.count}`).join("，");
}

export function formatPathwayStatusTone(tone: PathwayCenterAction["tone"]): "success" | "warning" | "danger" | "info" | "primary" {
  return tone;
}

function buildRequirementLines(
  evaluation: StudentPathwayEvaluation,
  pathway?: GaokaoPathwayRead,
): string[] {
  const ruleNames = [
    ...evaluation.failed_rules_json,
    ...evaluation.warning_rules_json,
    ...evaluation.matched_rules_json,
  ]
    .map((item) => item.rule_name)
    .filter((item): item is string => Boolean(item));
  const lines = uniqueNonEmpty([
    ...d6PathwayRequirementHints(evaluation.pathway_code || pathway?.pathway_code),
    pathway?.batch_name ? `批次：${pathway.batch_name}` : "",
    pathway?.volunteer_mode ? `志愿方式：${pathway.volunteer_mode}` : "",
    ...ruleNames,
  ]);
  if (lines.length) return lines.slice(0, 5);
  return uniqueNonEmpty([pathway?.summary || evaluation.summary || "以当前路径规则和学生画像为准。"]);
}

function buildRiskMessages(
  evaluation: StudentPathwayEvaluation,
  pathway?: GaokaoPathwayRead,
): string[] {
  const warningMessages = [
    ...evaluation.failed_rules_json,
    ...evaluation.warning_rules_json,
  ]
    .map((item) => item.message || item.rule_name)
    .filter((item): item is string => Boolean(item));
  const boundary = typeof pathway?.notes_json?.boundary === "string" ? pathway.notes_json.boundary : "";
  const officialBoundary = typeof pathway?.notes_json?.official_boundary === "string" ? pathway.notes_json.official_boundary : "";
  const riskLevel = formatRiskLevel(pathway?.risk_level);
  const d6Boundary = d6PathwayBoundaryMessage(evaluation.pathway_code || pathway?.pathway_code);
  return uniqueNonEmpty([
    d6Boundary,
    ...warningMessages,
    boundary,
    officialBoundary,
    riskLevel,
  ]).slice(0, 4);
}

function d6PathwayRequirementHints(code?: string | null): string[] {
  const mapping: Record<string, string[]> = {
    vocational_single_exam: [
      "报名：已完成山东高考报名，并核对目标院校单招报名时间",
      "身份：中职应届、社会人员等身份需在画像中确认",
      "测试：文化素质、专业技能、适应性测试或退役士兵测试方式需逐校核验",
      "复核：缺院校章程或分专业计划时只能人工核验",
    ],
    vocational_comprehensive: [
      "报名：已完成山东高考报名",
      "身份：普通高中应届毕业生",
      "材料：综合素质评价、素质测试或面试安排",
      "复核：缺院校章程或分专业计划时只能人工核验",
    ],
    spring_exam_undergrad: [
      "身份：春季高考考生",
      "类别：只能在对应春考专业类别内初筛",
      "材料：知识与技能考试成绩、类别分数线",
      "复核：缺春考分专业计划或院校章程时只能人工核验",
    ],
    spring_exam_junior: [
      "身份：春季高考考生",
      "类别：只能在对应春考专业类别内初筛",
      "材料：知识与技能考试成绩、类别分数线",
      "复核：缺春考分专业计划或院校章程时只能人工核验",
    ],
  };
  return code ? mapping[code] ?? [] : [];
}

function d6PathwayBoundaryMessage(code?: string | null): string {
  if (!code) return "";
  if (["vocational_single_exam", "vocational_comprehensive", "spring_exam_undergrad", "spring_exam_junior"].includes(code)) {
    return "当前只做资格初筛和人工复核清单，不输出录取概率。";
  }
  return "";
}

function buildApplicableObject(pathway?: GaokaoPathwayRead): string {
  if (!pathway) return "按学生画像和路径规则判断";
  const parts = [
    formatStudentType(pathway.student_type),
    formatExamType(pathway.exam_type),
    pathway.batch_name,
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : "按学生画像和路径规则判断";
}

function formatRecommendationDepth(depth?: string | null): { label: string; help: string } {
  const mapping: Record<string, { label: string; help: string }> = {
    full_rank_recommendation: {
      label: "可接完整位次推荐",
      help: "可进入山东普通类推荐工作台查看冲稳保候选。",
    },
    eligibility_screening: {
      label: "资格初筛",
      help: "只判断是否具备继续关注的基本条件，不输出录取概率。",
    },
    policy_notice: {
      label: "政策提醒",
      help: "主要用于报名、材料和章程核验提醒。",
    },
    manual_review_required: {
      label: "必须人工复核",
      help: "需要人工核对官方公告、测试安排或院校章程。",
    },
  };
  return mapping[String(depth || "")] ?? {
    label: "需结合规则复核",
    help: "当前路径不能直接理解为录取概率。",
  };
}

function formatConfidence(value?: string | null): string {
  const mapping: Record<string, string> = {
    high: "较明确",
    medium: "中等",
    low: "待补充",
  };
  return mapping[String(value || "")] ?? "待确认";
}

function formatStudentType(value?: string | null): string {
  const mapping: Record<string, string> = {
    general: "普通类学生",
    spring_exam: "春季高考学生",
    art: "艺术类学生",
    sports: "体育类学生",
    vocational_or_social: "中职或社会人员",
  };
  return value ? mapping[value] ?? value : "";
}

function formatExamType(value?: string | null): string {
  const mapping: Record<string, string> = {
    summer_gaokao: "夏季高考",
    spring_gaokao: "春季高考",
    art_gaokao: "艺术类",
    sports_gaokao: "体育类",
    vocational_single_exam: "高职单招",
    vocational_comprehensive: "高职综评",
    sports_single_exam: "体育单招",
    high_level_sports: "高水平运动队",
  };
  return value ? mapping[value] ?? value : "";
}

function formatOptionLabel(options: Array<{ value: string; label: string }>, value?: string | null): string {
  if (!value) return "未维护";
  return options.find((item) => item.value === value)?.label ?? value;
}

function formatBooleanValue(value?: boolean | null): string {
  if (value === true) return "已确认";
  if (value === false) return "不符合 / 不接受";
  return "未确认";
}

function formatRiskLevel(value?: string | null): string {
  const mapping: Record<string, string> = {
    high: "该路径政策和材料风险较高，必须人工复核。",
    medium: "该路径仍需核验 2026 官方计划、分数线或高校章程。",
    low: "该路径暂无高风险标记，仍需正式填报前复核。",
  };
  return value ? mapping[value] ?? value : "";
}

function compareEvaluationPriority(left: StudentPathwayEvaluation, right: StudentPathwayEvaluation): number {
  const statusRank: Record<string, number> = {
    suitable: 0,
    possible: 1,
    manual_review: 2,
    insufficient_data: 3,
    not_recommended: 4,
    not_applicable: 5,
  };
  return (statusRank[left.status] ?? 9) - (statusRank[right.status] ?? 9)
    || (right.score ?? 0) - (left.score ?? 0)
    || String(left.pathway_name || "").localeCompare(String(right.pathway_name || ""), "zh-CN");
}

function uniqueNonEmpty(values: Array<string | null | undefined>): string[] {
  return [...new Set(values.map((item) => item?.trim()).filter((item): item is string => Boolean(item)))];
}

function dedupeActions(actions: PathwayCenterAction[]): PathwayCenterAction[] {
  const seen = new Set<string>();
  return actions.filter((item) => {
    const key = `${item.title}-${item.detail}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function normalizePriorityIndex(index: number): number {
  return index === -1 ? 999 : index;
}
