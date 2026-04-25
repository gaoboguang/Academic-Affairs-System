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
  requiredFields: ReportFormField[];
  optionalFields?: ReportFormField[];
  ruleOptionScope?: "workload" | "adviser" | null;
  buildPrintPreviewPath?: ((form: ReportPageFormState) => string | null) | null;
}

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
    requiredFields: ["exam_id", "student_id"],
    buildPrintPreviewPath: (form) =>
      form.student_id && form.exam_id ? studentAnalysisPrintPreviewPath(form.student_id, form.exam_id) : null,
  },
  class_analysis: {
    value: "class_analysis",
    label: "班级成绩分析报表",
    requiredFields: ["exam_id", "class_id"],
    buildPrintPreviewPath: (form) =>
      form.class_id && form.exam_id ? classAnalysisPrintPreviewPath(form.class_id, form.exam_id) : null,
  },
  grade_summary: {
    value: "grade_summary",
    label: "年级成绩汇总表",
    requiredFields: ["exam_id", "grade_id"],
    buildPrintPreviewPath: (form) =>
      form.grade_id && form.exam_id ? gradeSummaryPrintPreviewPath(form.grade_id, form.exam_id) : null,
  },
  teacher_analysis: {
    value: "teacher_analysis",
    label: "教师任教分析报表",
    requiredFields: ["exam_id", "teacher_id"],
    buildPrintPreviewPath: (form) =>
      form.teacher_id && form.exam_id ? teacherAnalysisPrintPreviewPath(form.teacher_id, form.exam_id) : null,
  },
  teacher_workload: {
    value: "teacher_workload",
    label: "教师课时与工作量报表",
    requiredFields: ["semester_id"],
    optionalFields: ["rule_version_id"],
    ruleOptionScope: "workload",
    buildPrintPreviewPath: (form) =>
      form.semester_id ? workloadPrintPreviewPath(form.semester_id, form.rule_version_id) : null,
  },
  growth_summary: {
    value: "growth_summary",
    label: "学生成长档案摘要",
    requiredFields: ["student_id"],
    buildPrintPreviewPath: (form) =>
      form.student_id ? growthSummaryPrintPreviewPath(form.student_id) : null,
  },
  recommendation_summary: {
    value: "recommendation_summary",
    label: "学生推荐报告",
    requiredFields: ["student_id", "scheme_id"],
    buildPrintPreviewPath: (form) =>
      form.student_id && form.scheme_id ? recommendationPrintPreviewPath(form.student_id, form.scheme_id) : null,
  },
  volunteer_draft_summary: {
    value: "volunteer_draft_summary",
    label: "学生志愿草稿",
    requiredFields: ["draft_id"],
    buildPrintPreviewPath: (form) =>
      form.draft_id ? volunteerDraftPrintPreviewPath(form.draft_id) : null,
  },
  evaluation_summary: {
    value: "evaluation_summary",
    label: "评教汇总报表",
    requiredFields: ["batch_id"],
    buildPrintPreviewPath: (form) =>
      form.batch_id ? evaluationSummaryPrintPreviewPath(form.batch_id) : null,
  },
  adviser_quant_summary: {
    value: "adviser_quant_summary",
    label: "班主任量化报表",
    requiredFields: ["semester_id"],
    optionalFields: ["rule_version_id"],
    ruleOptionScope: "adviser",
    buildPrintPreviewPath: (form) =>
      form.semester_id ? adviserQuantPrintPreviewPath(form.semester_id, form.rule_version_id) : null,
  },
};

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
