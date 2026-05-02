export type ScoreImportLayoutType = "wide" | "long";

export interface ScoreImportMapping {
  layout_type: ScoreImportLayoutType;
  sheet_name?: string | null;
  header_row: number;
  field_mapping: Record<string, string>;
  subject_mapping: Record<string, string>;
  subject_score_types: Record<string, "original" | "converted" | "display">;
  ignored_columns: string[];
  metadata_mapping?: Record<string, string>;
}

export interface ScoreImportColumn {
  header: string;
  role?: string | null;
  metadata_role?: string | null;
  subject_name?: string | null;
  score_value_type?: "original" | "converted" | "display" | null;
  ignored?: boolean;
}

export interface ScoreImportPreview {
  source_filename?: string | null;
  sheet_name?: string | null;
  header_row: number;
  layout_type: ScoreImportLayoutType;
  confidence: number;
  messages: string[];
  columns: ScoreImportColumn[];
  sample_rows: Record<string, unknown>[];
  normalized_preview: Record<string, unknown>[];
  mapping: ScoreImportMapping;
  import_ready: boolean;
  source_row_count: number;
  detected_record_count: number;
}

export interface ScoreImportProfile {
  id: number;
  name: string;
  layout_type: ScoreImportLayoutType;
  sheet_name?: string | null;
  header_row: number;
  field_mapping_json: Record<string, string>;
  subject_mapping_json: Record<string, string>;
  subject_score_type_json: Record<string, "original" | "converted" | "display">;
  ignored_columns_json: string[];
  metadata_mapping_json: Record<string, string>;
  description?: string | null;
  is_active: boolean;
}

export const SCORE_IMPORT_FIELD_OPTIONS = [
  { value: "student_no", label: "学号/考号", required: true },
  { value: "student_name", label: "姓名", required: false },
  { value: "class_name", label: "班级", required: false },
  { value: "subject", label: "科目", required: false },
  { value: "score", label: "分数", required: false },
  { value: "absent_flag", label: "缺考标记", required: false },
  { value: "note", label: "备注", required: false },
  { value: "exam_name", label: "考试名称", required: false },
] as const;

export function cloneScoreImportMapping(mapping: ScoreImportMapping): ScoreImportMapping {
  return {
    layout_type: mapping.layout_type,
    sheet_name: mapping.sheet_name ?? null,
    header_row: mapping.header_row,
    field_mapping: { ...mapping.field_mapping },
    subject_mapping: { ...mapping.subject_mapping },
    subject_score_types: { ...(mapping.subject_score_types ?? {}) },
    ignored_columns: [...mapping.ignored_columns],
    metadata_mapping: { ...(mapping.metadata_mapping ?? {}) },
  };
}

export function getScoreImportHeaders(preview: ScoreImportPreview | null): string[] {
  if (!preview) return [];
  return preview.columns.map((item) => item.header).filter(Boolean);
}

export function getUnassignedScoreColumns(preview: ScoreImportPreview | null, mapping: ScoreImportMapping): string[] {
  const headers = getScoreImportHeaders(preview);
  const assigned = new Set([
    ...Object.values(mapping.field_mapping),
    ...Object.values(mapping.metadata_mapping ?? {}),
    ...mapping.ignored_columns,
  ]);
  return headers.filter((header) => !assigned.has(header));
}

export function buildScoreImportMappingPayload(mapping: ScoreImportMapping): string {
  return JSON.stringify({
    ...cloneScoreImportMapping(mapping),
    subject_mapping: Object.fromEntries(
      Object.entries(mapping.subject_mapping).filter(([, subjectName]) => Boolean(subjectName)),
    ),
    subject_score_types: Object.fromEntries(
      Object.entries(mapping.subject_score_types ?? {}).filter(([header]) => Boolean(mapping.subject_mapping[header])),
    ),
  });
}

export function buildScoreImportReadinessText(
  preview: ScoreImportPreview | null,
  mapping: ScoreImportMapping | null = preview?.mapping ?? null,
): string {
  if (!preview) return "请先上传成绩文件并完成识别。";
  if (!mapping?.field_mapping.student_no) return "当前映射还不能导入，请先指定学号/考号列。";
  if (mapping.layout_type === "long" && (!mapping.field_mapping.subject || !mapping.field_mapping.score)) {
    return "长表导入还需要指定科目列和分数列。";
  }
  if (
    mapping.layout_type === "wide" &&
    !Object.values(mapping.subject_mapping).some((subjectName) => Boolean(subjectName))
  ) {
    return "宽表导入还需要至少指定一个科目成绩列。";
  }
  if (preview.confidence < 0.7) return "识别置信度偏低，建议人工核对字段后再执行导入。";
  return `已识别 ${preview.detected_record_count} 条成绩记录，可执行导入。`;
}
