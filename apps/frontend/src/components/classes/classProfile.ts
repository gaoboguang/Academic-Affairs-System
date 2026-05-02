import type { StatCardItem } from "../ui";

export interface ClassHonorRead {
  id: number;
  class_id: number;
  title: string;
  honor_level?: string | null;
  awarded_on?: string | null;
  source?: string | null;
  note?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ClassTeacherSummary {
  teacher_id: number;
  teacher_name: string;
  subject_id?: number | null;
  subject_name?: string | null;
  course_type?: string | null;
  weekly_periods_manual?: number | null;
}

export interface ClassScoreSummary {
  exam_id?: number | null;
  exam_name?: string | null;
  sample_count: number;
  average_score?: number | null;
  max_score?: number | null;
  min_score?: number | null;
}

export interface ClassRiskSummary {
  follow_up_count: number;
  urgent_count: number;
  attendance_risk_count: number;
  behavior_risk_count: number;
}

export interface ClassOverviewItem {
  class_id: number;
  class_name: string;
  grade_id: number;
  grade_name?: string | null;
  class_type?: string | null;
  head_teacher_id?: number | null;
  head_teacher_name?: string | null;
  student_count: number;
  active_student_count: number;
  teacher_count: number;
  teacher_summary: ClassTeacherSummary[];
  honor_count: number;
  latest_honor?: ClassHonorRead | null;
  score_summary: ClassScoreSummary;
  risk_summary: ClassRiskSummary;
  teaching_complete: boolean;
}

export interface GradeOverviewGroup {
  grade_id: number;
  grade_name: string;
  class_count: number;
  student_count: number;
  active_student_count: number;
  head_teacher_coverage: number;
  teaching_complete_rate: number;
  latest_exam_sample_count: number;
  honor_count: number;
  classes: ClassOverviewItem[];
}

export interface ClassesOverviewResponse {
  semester_id?: number | null;
  semester_name?: string | null;
  exam_id?: number | null;
  exam_name?: string | null;
  grades: GradeOverviewGroup[];
  total_classes: number;
  total_students: number;
  total_honors: number;
}

export interface StudentListItem {
  id: number;
  student_no: string;
  name: string;
  gender?: string | null;
  current_grade_id?: number | null;
  current_grade_name?: string | null;
  current_class_id?: number | null;
  current_class_name?: string | null;
  status?: string | null;
  student_type?: string | null;
  art_track?: string | null;
  phone?: string | null;
  is_active: boolean;
}

export interface AssignmentItem {
  id: number;
  teacher_id: number;
  teacher_name?: string | null;
  semester_id: number;
  semester_name?: string | null;
  grade_id?: number | null;
  grade_name?: string | null;
  class_id?: number | null;
  class_name?: string | null;
  subject_id?: number | null;
  subject_name?: string | null;
  course_type?: string | null;
  weekly_periods_manual?: number | null;
  is_active: boolean;
}

export interface ClassProfileResponse {
  overview: ClassOverviewItem;
  honors: ClassHonorRead[];
  students: StudentListItem[];
  assignments: AssignmentItem[];
}

export interface GradeProfileResponse {
  grade: GradeOverviewGroup;
  classes: ClassOverviewItem[];
}

export function formatPercent(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return "-";
  return `${(value * 100).toFixed(1)}%`;
}

export function formatScore(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return "-";
  return value.toFixed(1).replace(/\.0$/, "");
}

export function formatClassTeachers(teachers: ClassTeacherSummary[], limit = 3): string {
  if (!teachers.length) return "暂无任课";
  const labels = teachers.slice(0, limit).map((item) =>
    item.subject_name ? `${item.subject_name}-${item.teacher_name}` : item.teacher_name,
  );
  const suffix = teachers.length > limit ? ` 等 ${teachers.length} 位` : "";
  return `${labels.join("、")}${suffix}`;
}

export function buildClassOverviewCards(payload: ClassesOverviewResponse | null): StatCardItem[] {
  const groups = payload?.grades ?? [];
  const classCount = payload?.total_classes ?? 0;
  const studentCount = payload?.total_students ?? 0;
  const honorCount = payload?.total_honors ?? 0;
  const weightedCoverage = classCount
    ? groups.reduce((sum, item) => sum + item.head_teacher_coverage * item.class_count, 0) / classCount
    : 0;
  return [
    { label: "年级", value: groups.length, help: "当前纳入速览的年级数量。", tone: "primary" },
    { label: "班级", value: classCount, help: "当前筛选范围内的班级数量。", tone: "neutral" },
    { label: "学生", value: studentCount, help: "按学生当前班级统计的在读学生。", tone: "success" },
    { label: "班主任覆盖", value: formatPercent(weightedCoverage), help: "已维护班主任的班级比例。", tone: "warning" },
    { label: "班级荣誉", value: honorCount, help: "结构化班级荣誉记录数量。", tone: "neutral" },
  ];
}

export function buildClassProfileCards(profile: ClassProfileResponse | null): StatCardItem[] {
  const overview = profile?.overview;
  return [
    { label: "学生", value: overview?.active_student_count ?? 0, help: "当前班级在读学生数。", tone: "primary" },
    { label: "任课教师", value: overview?.teacher_count ?? 0, help: "当前学期维护的任课教师数。", tone: "success" },
    { label: "班级荣誉", value: overview?.honor_count ?? 0, help: "已记录的结构化班级荣誉。", tone: "neutral" },
    { label: "成绩样本", value: overview?.score_summary.sample_count ?? 0, help: "当前考试下可用于班级画像的样本。", tone: "warning" },
    { label: "需跟进", value: overview?.risk_summary.follow_up_count ?? 0, help: "近 30 天考勤/行为触发的跟进信号。", tone: "neutral" },
  ];
}

export function filterClasses(
  classes: ClassOverviewItem[],
  filters: {
    keyword?: string;
    classType?: string;
    headTeacher?: "all" | "assigned" | "missing";
    teaching?: "all" | "complete" | "missing";
    honor?: "all" | "has" | "none";
  },
): ClassOverviewItem[] {
  const keyword = filters.keyword?.trim();
  return classes.filter((item) => {
    if (keyword) {
      const text = [
        item.grade_name,
        item.class_name,
        item.head_teacher_name,
        formatClassTeachers(item.teacher_summary, 8),
        item.latest_honor?.title,
      ].filter(Boolean).join(" ");
      if (!text.includes(keyword)) return false;
    }
    if (filters.classType && item.class_type !== filters.classType) return false;
    if (filters.headTeacher === "assigned" && !item.head_teacher_id) return false;
    if (filters.headTeacher === "missing" && item.head_teacher_id) return false;
    if (filters.teaching === "complete" && !item.teaching_complete) return false;
    if (filters.teaching === "missing" && item.teaching_complete) return false;
    if (filters.honor === "has" && item.honor_count <= 0) return false;
    if (filters.honor === "none" && item.honor_count > 0) return false;
    return true;
  });
}
