import {
  adviserQuantPrintPreviewPath,
  classAnalysisPrintPreviewPath,
  evaluationSummaryPrintPreviewPath,
  gradeSummaryPrintPreviewPath,
  growthSummaryPrintPreviewPath,
  recommendationPrintPreviewPath,
  studentAnalysisPrintPreviewPath,
  teacherAnalysisPrintPreviewPath,
  volunteerDraftPrintPreviewPath,
  workloadPrintPreviewPath,
} from "../../utils/print";

export type ReportFormField =
  | "exam_id"
  | "student_id"
  | "scheme_id"
  | "draft_id"
  | "batch_id"
  | "class_id"
  | "grade_id"
  | "teacher_id"
  | "semester_id"
  | "rule_version_id";

export interface ReportPageFormState {
  report_type: string;
  exam_id?: number;
  student_id?: number;
  scheme_id?: number;
  draft_id?: number;
  batch_id?: number;
  class_id?: number;
  grade_id?: number;
  teacher_id?: number;
  semester_id?: number;
  rule_version_id?: number;
}

interface ReportTypeConfig {
  value: string;
  label: string;
  domain: ReportDomain;
  purpose: string;
  dataSources: string[];
  formats: string[];
  riskTags: string[];
  requiredFields: ReportFormField[];
  optionalFields?: ReportFormField[];
  ruleOptionScope?: "workload" | "adviser" | null;
  buildPrintPreviewPath?: ((form: ReportPageFormState) => string | null) | null;
}

export type ReportDomain =
  | "students"
  | "scores"
  | "teachers"
  | "workload"
  | "evaluation"
  | "growth"
  | "gaokao"
  | "volunteer"
  | "system";

export interface ReportDomainGroup {
  key: ReportDomain;
  label: string;
  description: string;
}

export interface ReportTypeCatalogItem {
  value: string;
  label: string;
  domain: ReportDomain;
  purpose: string;
  requiredParams: string[];
  dataSources: string[];
  formats: string[];
  riskTags: string[];
}

export const REPORT_DOMAIN_GROUPS: ReportDomainGroup[] = [
  { key: "students", label: "学生", description: "面向单个学生的画像、成绩和成长输出。" },
  { key: "scores", label: "考试成绩", description: "面向考试、班级、年级和学科统计的输出。" },
  { key: "teachers", label: "教师", description: "面向任课教师教学分析的输出。" },
  { key: "workload", label: "工作量", description: "面向课表、规则版本和教师课时核算的输出。" },
  { key: "evaluation", label: "评教量化", description: "面向评教批次和班主任量化结果的输出。" },
  { key: "growth", label: "成长档案", description: "面向学生成长记录留档和沟通的输出。" },
  { key: "gaokao", label: "高考推荐", description: "面向升学推荐、风险提示和证据链复核的输出。" },
  { key: "volunteer", label: "志愿草稿", description: "面向志愿草稿打印、复核和留档的输出。" },
  { key: "system", label: "系统数据", description: "面向系统备份、数据安全和操作留痕的输出。" },
];

const REPORT_FIELD_LABELS: Record<ReportFormField, string> = {
  exam_id: "考试",
  student_id: "学生",
  scheme_id: "推荐方案",
  draft_id: "志愿草稿",
  batch_id: "评教批次",
  class_id: "班级",
  grade_id: "年级",
  teacher_id: "教师",
  semester_id: "学期",
  rule_version_id: "规则版本",
};

const REPORT_TYPE_LABEL_FALLBACKS: Record<string, string> = {
  shandong_recommendation_summary: "山东普通类冲稳保推荐报告",
};

const REPORT_PARAM_LABELS: Record<string, string> = {
  ...REPORT_FIELD_LABELS,
  report_type: "报表类型",
  student_name: "学生",
  target_year: "目标年份",
  source_mode: "输入来源",
  predicted_rank: "预估位次",
};

export const REPORT_TYPE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "student_analysis", label: "学生成绩分析单" },
  { value: "class_analysis", label: "班级成绩分析报表" },
  { value: "grade_summary", label: "年级成绩汇总表" },
  { value: "teacher_analysis", label: "教师任教分析报表" },
  { value: "teacher_workload", label: "教师课时与工作量报表" },
  { value: "growth_summary", label: "学生成长档案摘要" },
  { value: "recommendation_summary", label: "学生推荐报告" },
  { value: "volunteer_draft_summary", label: "学生志愿草稿" },
  { value: "evaluation_summary", label: "评教汇总报表" },
  { value: "adviser_quant_summary", label: "班主任量化报表" },
];

const REPORT_TYPE_CONFIGS: Record<string, ReportTypeConfig> = {
  student_analysis: {
    value: "student_analysis",
    label: "学生成绩分析单",
    domain: "students",
    purpose: "给学生或家长查看单次考试表现、学科短板和排名位置。",
    dataSources: ["考试成绩", "学生档案", "班级/年级统计"],
    formats: ["Excel", "打印预览"],
    riskTags: ["需选择考试", "需选择学生", "缺成绩时不可生成"],
    requiredFields: ["exam_id", "student_id"],
    buildPrintPreviewPath: (form) =>
      form.student_id && form.exam_id ? studentAnalysisPrintPreviewPath(form.student_id, form.exam_id) : null,
  },
  class_analysis: {
    value: "class_analysis",
    label: "班级成绩分析报表",
    domain: "scores",
    purpose: "给班主任和年级组查看班级整体成绩分布与学科表现。",
    dataSources: ["考试成绩", "班级名单", "学科统计"],
    formats: ["Excel", "打印预览"],
    riskTags: ["需选择考试", "需选择班级", "缺成绩时不可生成"],
    requiredFields: ["exam_id", "class_id"],
    buildPrintPreviewPath: (form) =>
      form.class_id && form.exam_id ? classAnalysisPrintPreviewPath(form.class_id, form.exam_id) : null,
  },
  grade_summary: {
    value: "grade_summary",
    label: "年级成绩汇总表",
    domain: "scores",
    purpose: "给年级组汇总单次考试的班级对比、学科均分和整体分布。",
    dataSources: ["考试成绩", "年级班级结构", "学科统计"],
    formats: ["Excel", "打印预览"],
    riskTags: ["需选择考试", "需选择年级", "缺成绩时不可生成"],
    requiredFields: ["exam_id", "grade_id"],
    buildPrintPreviewPath: (form) =>
      form.grade_id && form.exam_id ? gradeSummaryPrintPreviewPath(form.grade_id, form.exam_id) : null,
  },
  teacher_analysis: {
    value: "teacher_analysis",
    label: "教师任教分析报表",
    domain: "teachers",
    purpose: "给任课教师和教务处查看任教班级的考试表现。",
    dataSources: ["考试成绩", "任课关系", "教师档案"],
    formats: ["Excel", "打印预览"],
    riskTags: ["需选择考试", "需选择教师", "缺成绩时不可生成"],
    requiredFields: ["exam_id", "teacher_id"],
    buildPrintPreviewPath: (form) =>
      form.teacher_id && form.exam_id ? teacherAnalysisPrintPreviewPath(form.teacher_id, form.exam_id) : null,
  },
  teacher_workload: {
    value: "teacher_workload",
    label: "教师课时与工作量报表",
    domain: "workload",
    purpose: "用于核对教师课时、规则版本和工作量结果。",
    dataSources: ["课表", "工作量规则", "计算结果"],
    formats: ["Excel", "打印预览"],
    riskTags: ["需选择学期", "建议核对规则版本", "暂无结果时不可生成"],
    requiredFields: ["semester_id"],
    optionalFields: ["rule_version_id"],
    ruleOptionScope: "workload",
    buildPrintPreviewPath: (form) =>
      form.semester_id ? workloadPrintPreviewPath(form.semester_id, form.rule_version_id) : null,
  },
  growth_summary: {
    value: "growth_summary",
    label: "学生成长档案摘要",
    domain: "growth",
    purpose: "用于汇总学生奖励、处分、谈话和成长记录。",
    dataSources: ["成长档案", "附件记录", "学生档案"],
    formats: ["Excel", "打印预览"],
    riskTags: ["需选择学生", "无成长记录时不可生成"],
    requiredFields: ["student_id"],
    buildPrintPreviewPath: (form) =>
      form.student_id ? growthSummaryPrintPreviewPath(form.student_id) : null,
  },
  recommendation_summary: {
    value: "recommendation_summary",
    label: "学生推荐报告",
    domain: "gaokao",
    purpose: "用于输出学生高考推荐结果、风险标签和数据证据链。",
    dataSources: ["推荐方案", "录取数据", "招生计划", "章程限制"],
    formats: ["Excel", "打印预览"],
    riskTags: ["需选择推荐方案", "保留风险标签", "需人工复核章程"],
    requiredFields: ["student_id", "scheme_id"],
    buildPrintPreviewPath: (form) =>
      form.student_id && form.scheme_id ? recommendationPrintPreviewPath(form.student_id, form.scheme_id) : null,
  },
  volunteer_draft_summary: {
    value: "volunteer_draft_summary",
    label: "学生志愿草稿",
    domain: "volunteer",
    purpose: "用于输出学生志愿草稿、规则差异和复核提醒。",
    dataSources: ["志愿草稿", "省份规则", "招生计划", "推荐候选"],
    formats: ["Excel", "打印预览"],
    riskTags: ["需选择志愿草稿", "保留规则提醒", "需复核选科"],
    requiredFields: ["draft_id"],
    buildPrintPreviewPath: (form) =>
      form.draft_id ? volunteerDraftPrintPreviewPath(form.draft_id) : null,
  },
  evaluation_summary: {
    value: "evaluation_summary",
    label: "评教汇总报表",
    domain: "evaluation",
    purpose: "用于汇总评教批次中教师维度得分和反馈情况。",
    dataSources: ["评教批次", "评教模板", "教师维度统计"],
    formats: ["Excel", "打印预览"],
    riskTags: ["需选择评教批次", "空批次不可生成"],
    requiredFields: ["batch_id"],
    buildPrintPreviewPath: (form) =>
      form.batch_id ? evaluationSummaryPrintPreviewPath(form.batch_id) : null,
  },
  adviser_quant_summary: {
    value: "adviser_quant_summary",
    label: "班主任量化报表",
    domain: "evaluation",
    purpose: "用于输出班主任量化积分、规则版本和明细记录。",
    dataSources: ["量化规则", "量化记录", "教师/班级档案"],
    formats: ["Excel", "打印预览"],
    riskTags: ["需选择学期", "建议核对规则版本", "暂无结果时不可生成"],
    requiredFields: ["semester_id"],
    optionalFields: ["rule_version_id"],
    ruleOptionScope: "adviser",
    buildPrintPreviewPath: (form) =>
      form.semester_id ? adviserQuantPrintPreviewPath(form.semester_id, form.rule_version_id) : null,
  },
};

export function getReportCatalogItem(reportType: string): ReportTypeCatalogItem | null {
  const config = REPORT_TYPE_CONFIGS[reportType];
  if (!config) return null;
  return {
    value: config.value,
    label: config.label,
    domain: config.domain,
    purpose: config.purpose,
    requiredParams: config.requiredFields.map((field) => REPORT_FIELD_LABELS[field]),
    dataSources: config.dataSources,
    formats: config.formats,
    riskTags: config.riskTags,
  };
}

export function getGroupedReportCatalog(): Array<ReportDomainGroup & { items: ReportTypeCatalogItem[] }> {
  return REPORT_DOMAIN_GROUPS.map((group) => ({
    ...group,
    items: Object.values(REPORT_TYPE_CONFIGS)
      .filter((config) => config.domain === group.key)
      .map((config) => getReportCatalogItem(config.value))
      .filter((item): item is ReportTypeCatalogItem => Boolean(item)),
  })).filter((group) => group.items.length > 0);
}

export function getReportTypeLabel(reportType: string): string {
  return REPORT_TYPE_CONFIGS[reportType]?.label ?? REPORT_TYPE_LABEL_FALLBACKS[reportType] ?? reportType;
}

export function reportTypeUsesField(reportType: string, field: ReportFormField): boolean {
  const config = REPORT_TYPE_CONFIGS[reportType];
  if (!config) return false;
  return config.requiredFields.includes(field) || Boolean(config.optionalFields?.includes(field));
}

export function getMissingRequiredReportFields(form: ReportPageFormState): string[] {
  const config = REPORT_TYPE_CONFIGS[form.report_type];
  if (!config) return [];
  return config.requiredFields.filter((field) => !form[field]).map((field) => REPORT_FIELD_LABELS[field]);
}

export function getMissingRequiredReportFieldsMessage(form: ReportPageFormState): string {
  const fields = getMissingRequiredReportFields(form);
  return fields.length ? `请先补齐：${fields.join("、")}` : "";
}

export function formatReportExportParams(value?: Record<string, unknown> | null): string {
  if (!value || !Object.keys(value).length) return "-";
  return Object.entries(value)
    .filter(([, item]) => item !== null && item !== undefined)
    .map(([key, item]) => {
      if (key === "report_type") {
        return `报表类型=${getReportTypeLabel(String(item))}`;
      }
      const label = REPORT_PARAM_LABELS[key] ?? key;
      return `${label}=${item}`;
    })
    .join(" / ") || "-";
}

export function getReportRuleOptionScope(reportType: string): "workload" | "adviser" | null {
  return REPORT_TYPE_CONFIGS[reportType]?.ruleOptionScope ?? null;
}

export function getReportPrintPreviewPath(form: ReportPageFormState): string | null {
  return REPORT_TYPE_CONFIGS[form.report_type]?.buildPrintPreviewPath?.(form) ?? null;
}

export function buildReportExportPayload(form: ReportPageFormState): Record<string, unknown> {
  const payload: Record<string, unknown> = { report_type: form.report_type };
  const fields: ReportFormField[] = [
    "exam_id",
    "student_id",
    "class_id",
    "grade_id",
    "teacher_id",
    "semester_id",
    "rule_version_id",
    "scheme_id",
    "draft_id",
    "batch_id",
  ];

  for (const field of fields) {
    const value = form[field];
    if (value != null) {
      payload[field] = value;
    }
  }

  return payload;
}
