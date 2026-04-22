import type {
  AdviserQuantInsightData,
  EvaluationInsightData,
  GrowthInsightData,
  ReportInsightCard,
  WorkloadInsightData,
} from "./reportInsightTypes";
import {
  formatNumber,
  pickMaxBy,
  pickMinBy,
  pickTopCategory,
  pickTopDimension,
  growthTypeLabel,
} from "./reportInsightShared";

export function buildWorkloadInsightCards(results: WorkloadInsightData[]): ReportInsightCard[] {
  if (!results.length) return [];

  const totalWorkload = results.reduce((sum, item) => sum + item.semester_workload, 0);
  const totalHours = results.reduce((sum, item) => sum + item.semester_hours, 0);
  const averageWorkload = totalWorkload / results.length;
  const maxTeacher = pickMaxBy(results, (item) => item.semester_workload);
  const focusTeacher = pickMaxBy(results, (item) => item.weekly_hours);

  const cards: ReportInsightCard[] = [
    {
      key: "workload_overview",
      title: "工作量整体状态",
      summary: `${results[0]?.semester_name ?? "当前学期"}共 ${results.length} 位教师，总工作量 ${formatNumber(totalWorkload)}`,
      detail: `总学期课时 ${formatNumber(totalHours)}，人均工作量 ${formatNumber(averageWorkload)}，规则版本 ${results[0]?.rule_version_name ?? "未指定"}。`,
      tone: "info",
    },
  ];

  if (maxTeacher) {
    cards.push({
      key: "workload_max_teacher",
      title: "工作量最高教师",
      summary: `${maxTeacher.teacher_name ?? "未命名教师"} 当前学期工作量最高`,
      detail: `学期工作量 ${formatNumber(maxTeacher.semester_workload)}，学期课时 ${formatNumber(maxTeacher.semester_hours)}，周课时 ${formatNumber(maxTeacher.weekly_hours)}。`,
      tone: "warning",
    });
  }

  if (focusTeacher && focusTeacher.teacher_name !== maxTeacher?.teacher_name) {
    cards.push({
      key: "workload_focus_teacher",
      title: "周课时最高教师",
      summary: `${focusTeacher.teacher_name ?? "未命名教师"} 当前周课时最高`,
      detail: `周课时 ${formatNumber(focusTeacher.weekly_hours)}，学期工作量 ${formatNumber(focusTeacher.semester_workload)}。导出前建议确认是否存在需额外说明的工作量来源。`,
      tone: "info",
    });
  }

  return cards;
}

export function buildEvaluationInsightCards(data: EvaluationInsightData): ReportInsightCard[] {
  const cards: ReportInsightCard[] = [
    {
      key: "evaluation_overview",
      title: "评教整体状态",
      summary: `${data.template_name} 当前覆盖 ${data.teacher_count} 位教师`,
      detail: `${data.semester_name ?? "未标注学期"}，批次 ID ${data.batch_id}。导出前建议先确认模板和学期是否对应当前批次。`,
      tone: "info",
    },
  ];

  const bestTeacher = pickMaxBy(data.teacher_summaries, (item) => item.overall_avg_score);
  if (bestTeacher) {
    cards.push({
      key: "evaluation_best_teacher",
      title: "当前领先教师",
      summary: `${bestTeacher.teacher_name} 当前综合均分最高`,
      detail: `综合均分 ${formatNumber(bestTeacher.overall_avg_score)}，响应数 ${bestTeacher.response_count}${bestTeacher.rank != null ? `，排名 ${bestTeacher.rank}` : ""}。`,
      tone: "success",
    });
  }

  const focusTeacher = pickMinBy(data.teacher_summaries, (item) => item.overall_avg_score);
  if (focusTeacher && focusTeacher.teacher_id !== bestTeacher?.teacher_id) {
    cards.push({
      key: "evaluation_focus_teacher",
      title: "需重点复核教师",
      summary: `${focusTeacher.teacher_name} 当前综合均分相对靠后`,
      detail: `综合均分 ${formatNumber(focusTeacher.overall_avg_score)}，响应数 ${focusTeacher.response_count}${focusTeacher.rank != null ? `，排名 ${focusTeacher.rank}` : ""}。`,
      tone: "warning",
    });
  }

  const topDimension = pickTopDimension(data.teacher_summaries);
  if (topDimension) {
    cards.push({
      key: "evaluation_dimension",
      title: "当前高频优势维度",
      summary: `${topDimension.name} 在本批次表现相对更强`,
      detail: `平均维度得分 ${formatNumber(topDimension.score)}。导出前可确认这是否符合本次模板重点。`,
      tone: "info",
    });
  }

  return cards;
}

export function buildAdviserQuantInsightCards(summary: AdviserQuantInsightData[]): ReportInsightCard[] {
  if (!summary.length) return [];

  const totalScore = summary.reduce((sum, item) => sum + item.total_score, 0);
  const totalRecordCount = summary.reduce((sum, item) => sum + item.record_count, 0);
  const topTeacher = pickMaxBy(summary, (item) => item.total_score);
  const focusTeacher = pickMaxBy(summary, (item) => item.negative_score);

  const cards: ReportInsightCard[] = [
    {
      key: "adviser_overview",
      title: "量化整体状态",
      summary: `${summary[0]?.semester_name ?? "当前学期"}共 ${summary.length} 位教师进入量化汇总`,
      detail: `总分合计 ${formatNumber(totalScore)}，记录数 ${totalRecordCount}，规则版本 ${summary[0]?.rule_version_name ?? "未指定"}。`,
      tone: "info",
    },
  ];

  if (topTeacher) {
    cards.push({
      key: "adviser_top_teacher",
      title: "总分最高教师",
      summary: `${topTeacher.teacher_name} 当前总分最高`,
      detail: `总分 ${formatNumber(topTeacher.total_score)}，加分 ${formatNumber(topTeacher.positive_score)}，扣分 ${formatNumber(topTeacher.negative_score)}。`,
      tone: "success",
    });
  }

  if (focusTeacher && focusTeacher.teacher_id !== topTeacher?.teacher_id && focusTeacher.negative_score > 0) {
    cards.push({
      key: "adviser_focus_teacher",
      title: "扣分较多教师",
      summary: `${focusTeacher.teacher_name} 当前扣分最多`,
      detail: `扣分 ${formatNumber(focusTeacher.negative_score)}，记录数 ${focusTeacher.record_count}，班级 ${focusTeacher.class_names.join(" / ") || "-"}。`,
      tone: "warning",
    });
  }

  const topCategory = pickTopCategory(summary);
  if (topCategory) {
    cards.push({
      key: "adviser_category",
      title: "高频得分类别",
      summary: `${topCategory.name} 当前累计分值最高`,
      detail: `累计分值 ${formatNumber(topCategory.score)}。导出前可结合规则版本确认该类别是否为本学期重点。`,
      tone: "info",
    });
  }

  return cards;
}

export function buildGrowthInsightCards(data: GrowthInsightData): ReportInsightCard[] {
  const attachmentCount = data.records.reduce((sum, item) => sum + item.attachments.length, 0);
  const recordTypeMap = new Map<string, number>();
  for (const item of data.records) {
    recordTypeMap.set(item.record_type, (recordTypeMap.get(item.record_type) ?? 0) + 1);
  }
  const dominantType = Array.from(recordTypeMap.entries()).sort((a, b) => b[1] - a[1])[0] ?? null;
  const latestRecord = [...data.records].sort((a, b) => String(b.occurred_on).localeCompare(String(a.occurred_on)))[0] ?? null;

  const cards: ReportInsightCard[] = [
    {
      key: "growth_overview",
      title: "成长档案整体状态",
      summary: `${data.profile.student.name} 当前共有 ${data.records.length} 条成长记录`,
      detail: `成长类型 ${recordTypeMap.size} 类，附件 ${attachmentCount} 个。导出前建议先确认是否需要补齐最近阶段的记录。`,
      tone: "info",
    },
  ];

  if (dominantType) {
    cards.push({
      key: "growth_type",
      title: "高频成长类型",
      summary: `${growthTypeLabel(dominantType[0])} 当前记录最多`,
      detail: `共 ${dominantType[1]} 条，适合在导出汇报时作为该学生当前成长档案的主要线索。`,
      tone: "info",
    });
  }

  if (latestRecord) {
    cards.push({
      key: "growth_latest",
      title: "最近一条记录",
      summary: `${latestRecord.occurred_on} · ${latestRecord.title}`,
      detail: `${growthTypeLabel(latestRecord.record_type)}${latestRecord.owner_name ? ` / 责任人 ${latestRecord.owner_name}` : ""}。`,
      tone: "success",
    });
  }

  if (!data.records.length) {
    cards.push({
      key: "growth_empty",
      title: "当前暂无成长记录",
      summary: "导出结果会以空档案形式呈现",
      detail: "若准备正式汇报，建议先补录关键成长事件、谈话记录或奖励处分信息。",
      tone: "warning",
    });
  }

  return cards;
}
