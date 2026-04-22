export interface TeacherOption {
  id: number;
  name: string;
}

export interface TimetableBatchItem {
  id: number;
  semester_id: number;
  semester_name?: string | null;
  source_filename?: string | null;
  import_time: string;
  status: string;
  remark?: string | null;
  entry_count: number;
  unresolved_count: number;
  is_active: boolean;
}

export interface TimetableEntryItem {
  id: number;
  batch_id: number;
  semester_id: number;
  weekday: number;
  period_no: number;
  teacher_id?: number | null;
  teacher_name?: string | null;
  class_id?: number | null;
  class_name?: string | null;
  subject_id?: number | null;
  subject_name?: string | null;
  course_type?: string | null;
  week_rule: string;
  week_list_json?: number[] | null;
  note?: string | null;
  mapping_status: string;
  raw_teacher_name?: string | null;
  raw_class_name?: string | null;
  raw_subject_name?: string | null;
  raw_course_type?: string | null;
  is_active: boolean;
}

export interface RuleVersionItem {
  id: number;
  name: string;
  semester_id?: number | null;
  semester_name?: string | null;
  is_default: boolean;
  status: string;
  note?: string | null;
  is_active: boolean;
}

export interface RuleItem {
  id?: number;
  dimension_type: string;
  match_key: string;
  coefficient?: number | null;
  fixed_value?: number | null;
  note?: string | null;
  is_active: boolean;
}

export interface ExtraItem {
  id: number;
  teacher_id: number;
  teacher_name?: string | null;
  semester_id: number;
  item_name: string;
  quantity: number;
  coefficient: number;
  amount?: number | null;
  note?: string | null;
  is_active: boolean;
}

export interface ResultDetailRow {
  weekday: number;
  period_no: number;
  class_name?: string | null;
  subject_name?: string | null;
  course_type?: string | null;
  active_week_count: number;
  coefficient: number;
  coefficient_breakdown?: Record<string, number>;
  semester_contribution: number;
}

export interface ResultExtraRow {
  item_name: string;
  quantity: number;
  coefficient: number;
  amount: number;
}

export interface WorkloadResultItem {
  id: number;
  teacher_id: number;
  teacher_name?: string | null;
  semester_id: number;
  semester_name?: string | null;
  rule_version_id: number;
  rule_version_name?: string | null;
  weekly_hours: number;
  monthly_hours_json?: Record<string, number> | null;
  semester_hours: number;
  semester_workload: number;
  snapshot_json?: {
    batch_id?: number;
    batch_filename?: string | null;
    entry_count?: number;
    head_teacher_bonus?: number;
    details?: ResultDetailRow[];
    extras?: ResultExtraRow[];
  } | null;
  calculated_at: string;
  is_active: boolean;
}

export interface CreateRuleForm {
  name: string;
  semester_id?: number | null;
  is_default: boolean;
  status: string;
  note: string;
  is_active: boolean;
}

export interface EntryFormState {
  id?: number;
  teacher_id?: number | null;
  class_id?: number | null;
  subject_id?: number | null;
  course_type?: string | null;
  note?: string | null;
  is_active: boolean;
}

export interface ExtraFormState {
  teacher_id?: number;
  item_name: string;
  quantity: number;
  coefficient: number;
  amount?: number | null;
  note: string;
}

export interface StatusCard {
  label: string;
  value: string | number;
  help: string;
  tone: string;
}
