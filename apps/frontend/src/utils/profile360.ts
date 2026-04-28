export interface Profile360Tag {
  label: string;
  detail: string;
  type: "success" | "warning" | "danger" | "info";
}

export interface Profile360Action {
  label: string;
  detail: string;
  path: string;
}

export interface Student360Input {
  examCount: number;
  growthRecordCount: number;
  recommendationCount: number;
  attachmentCount: number;
  classTransferCount: number;
  studentType?: string | null;
  attendanceImported?: boolean;
  behaviorImported?: boolean;
  riskLevel?: "urgent" | "follow_up" | "watch" | "normal" | null;
}

export interface Teacher360Input {
  activeAssignmentCount: number;
  examTrendCount: number;
  peerComparisonCount: number;
  hasSubject: boolean;
}

export function buildStudent360RiskTags(input: Student360Input): Profile360Tag[] {
  const tags: Profile360Tag[] = [];
  if (input.examCount <= 0) {
    tags.push({ label: "成绩数据缺失", detail: "当前还没有可用于趋势和排名分析的成绩记录。", type: "danger" });
  }
  if (input.riskLevel === "urgent") {
    tags.push({ label: "紧急跟进", detail: "考勤、行为或成绩波动触发了高优先级跟进。", type: "danger" });
  } else if (input.riskLevel === "follow_up") {
    tags.push({ label: "需要跟进", detail: "近期存在出勤、行为或成绩方面的跟进信号。", type: "warning" });
  } else if (input.riskLevel === "watch") {
    tags.push({ label: "持续观察", detail: "当前数据不完整或存在轻微波动，建议保持观察。", type: "info" });
  }
  if (input.attendanceImported === false) {
    tags.push({ label: "考勤未导入", detail: "缺少近阶段考勤数据，不能按 0 风险判断。", type: "warning" });
  }
  if (input.behaviorImported === false) {
    tags.push({ label: "行为未导入", detail: "缺少近阶段行为记录，不能按 0 风险判断。", type: "warning" });
  }
  if (input.classTransferCount > 0) {
    tags.push({ label: "近期调班需复核", detail: "已有调班系统事件，查看分析前先确认生效日期和班级口径。", type: "warning" });
  }
  if (input.growthRecordCount <= 0) {
    tags.push({ label: "成长档案缺记录", detail: "暂无成长记录，综合评价材料和过程性证据还不完整。", type: "info" });
  }
  if (input.recommendationCount <= 0) {
    tags.push({ label: "暂无推荐记录", detail: "还没有生成过升学推荐方案。", type: "info" });
  }
  if (input.attachmentCount <= 0) {
    tags.push({ label: "附件材料缺口", detail: "未挂接证件、获奖证明或成长档案附件。", type: "warning" });
  }
  if (input.studentType && !["general", "repeat"].includes(input.studentType)) {
    tags.push({ label: "特殊类型仅初筛", detail: "特殊类型推荐需逐校核对章程、资格材料和专门录取结果。", type: "warning" });
  }
  return tags;
}

export function buildStudent360Actions(studentId: number): Profile360Action[] {
  return [
    { label: "成绩趋势", detail: "查看最近考试、排名和薄弱学科。", path: "/analytics" },
    { label: "成长时间线", detail: "查看成长记录、调班系统事件和附件。", path: `/growth-archive?student_id=${studentId}` },
    { label: "升学画像", detail: "维护路径画像、材料缺口和资格初筛。", path: `/gaokao-pathways?student_id=${studentId}` },
    { label: "推荐记录", detail: "生成或回看冲稳保方案。", path: "/recommendations" },
    { label: "学生跟进包", detail: "汇总成绩、考勤、行为和成长记录。", path: `/reports?report_type=student_followup_package&student_id=${studentId}` },
    { label: "报表导出", detail: "到报表中心导出可交接材料。", path: "/reports" },
  ];
}

export function buildTeacher360RiskTags(input: Teacher360Input): Profile360Tag[] {
  const tags: Profile360Tag[] = [];
  if (!input.hasSubject) {
    tags.push({ label: "任教学科未设置", detail: "缺少当前学科会影响同科对比和考试分析。", type: "warning" });
  }
  if (input.activeAssignmentCount <= 0) {
    tags.push({ label: "任教关系缺失", detail: "当前没有在用任教关系，无法形成班级成绩关联。", type: "danger" });
  }
  if (input.examTrendCount <= 0) {
    tags.push({ label: "考试样本不足", detail: "暂无关联考试趋势，先导入成绩并确认任教关系。", type: "info" });
  }
  if (input.peerComparisonCount <= 1) {
    tags.push({ label: "同科对比不足", detail: "同学科样本太少，横向比较只能作为提示。", type: "info" });
  }
  return tags;
}

export function buildTeacher360Actions(): Profile360Action[] {
  return [
    { label: "任教关系", detail: "维护学期、年级、班级和任教学科。", path: "/teachers" },
    { label: "课表与工作量", detail: "核对课表批次和工作量计算结果。", path: "/workload" },
    { label: "评教量化", detail: "查看评教模板、导入批次和汇总分析。", path: "/evaluation-quant" },
    { label: "班级成绩表现", detail: "查看教师关联考试和班级表现。", path: "/analytics" },
    { label: "报表导出", detail: "导出教师分析、工作量或评教报表。", path: "/reports" },
  ];
}
