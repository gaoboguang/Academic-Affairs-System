import type {
  PanoramaDataset,
  PanoramaExamPoint,
  PanoramaExamTimelineRow,
  PanoramaInsightCard,
  PanoramaMetricCard,
  PanoramaSubjectPriorityRow,
  PanoramaSubjectTrendRow,
  PanoramaYearCompetitionRow,
} from "./types";

function deltaTone(delta: number): string {
  if (delta > 0) return "tone-green";
  if (delta < 0) return "tone-amber";
  return "tone-slate";
}

export function bestExamPoint(points: PanoramaExamPoint[]): PanoramaExamPoint | null {
  if (!points.length) return null;
  return [...points].sort((left, right) => right.total_average - left.total_average)[0];
}

export function latestExamPoint(points: PanoramaExamPoint[]): PanoramaExamPoint | null {
  if (!points.length) return null;
  return [...points].sort((left, right) => left.exam_date.localeCompare(right.exam_date)).at(-1) ?? null;
}

export function previousExamPoint(points: PanoramaExamPoint[]): PanoramaExamPoint | null {
  const sorted = [...points].sort((left, right) => left.exam_date.localeCompare(right.exam_date));
  return sorted.length >= 2 ? sorted.at(-2) ?? null : null;
}

export function buildPanoramaMetricCards(panorama: PanoramaDataset | null): PanoramaMetricCard[] {
  if (!panorama) return [];

  const latest = latestExamPoint(panorama.exam_points);
  const previous = previousExamPoint(panorama.exam_points);
  const best = bestExamPoint(panorama.exam_points);

  const averageDelta = latest && previous ? Number((latest.total_average - previous.total_average).toFixed(2)) : null;
  const bestYear = [...panorama.year_summaries].sort((left, right) => right.average_score - left.average_score)[0] ?? null;
  const strongestSubject = buildPanoramaSubjectTrendRows(panorama).sort(
    (left, right) => Number(right.latest_average) - Number(left.latest_average),
  )[0];

  return [
    {
      label: "覆盖学年",
      value: panorama.academic_year_count,
      help: "当前全景对比包含的学年数量。",
      tone: "tone-blue",
    },
    {
      label: "考试场次",
      value: panorama.exam_count,
      help: "纳入全景对比的趋势考试数量。",
      tone: "tone-slate",
    },
    {
      label: "最近均分变化",
      value: averageDelta === null ? "-" : (averageDelta > 0 ? `+${averageDelta}` : averageDelta),
      help: latest && previous ? `${previous.exam_name} -> ${latest.exam_name}` : "需要至少两场考试才会显示变化。",
      tone: averageDelta === null ? "tone-slate" : deltaTone(averageDelta),
    },
    {
      label: "最佳学年",
      value: bestYear?.academic_year_name ?? "-",
      help: bestYear ? `平均均分 ${bestYear.average_score}` : "当前还没有可比较的学年摘要。",
      tone: "tone-amber",
    },
    {
      label: "最佳场次",
      value: best?.exam_name ?? "-",
      help: best ? `均分 ${best.total_average}` : "当前还没有可比较的考试数据。",
      tone: "tone-blue",
    },
    {
      label: "优势学科",
      value: strongestSubject?.subject_name ?? "-",
      help: strongestSubject ? `最近均分 ${strongestSubject.latest_average}` : "当前还没有可比较的学科趋势。",
      tone: "tone-green",
    },
  ];
}

export function buildPanoramaSubjectTrendRows(panorama: PanoramaDataset | null): PanoramaSubjectTrendRow[] {
  if (!panorama) return [];
  return panorama.subject_trends.map((item) => {
    const points = [...item.points].sort((left, right) => left.exam_date.localeCompare(right.exam_date));
    const first = points[0];
    const latest = points.at(-1) ?? first;
    return {
      subject_id: item.subject_id,
      subject_name: item.subject_name,
      exam_count: points.length,
      first_average: first?.average_score ?? "-",
      latest_average: latest?.average_score ?? "-",
      delta_average: first && latest ? Number((latest.average_score - first.average_score).toFixed(2)) : "-",
      latest_excellent_rate: latest?.excellent_rate ?? "-",
    };
  });
}

export function buildPanoramaSubjectPriorityRows(panorama: PanoramaDataset | null): PanoramaSubjectPriorityRow[] {
  if (!panorama) return [];

  return panorama.subject_trends.map((item) => {
    const points = [...item.points].sort((left, right) => left.exam_date.localeCompare(right.exam_date));
    const first = points[0];
    const latest = points.at(-1) ?? first;
    const averages = points.map((point) => point.average_score);
    const deltas = points.slice(1).map((point, index) => point.average_score - points[index].average_score);
    const deltaAverage = first && latest ? Number((latest.average_score - first.average_score).toFixed(2)) : 0;
    const deltaExcellentRate =
      first && latest ? Number((latest.excellent_rate - first.excellent_rate).toFixed(2)) : 0;
    const swing =
      averages.length > 0 ? Number((Math.max(...averages) - Math.min(...averages)).toFixed(2)) : 0;
    const rising = deltas.length > 0 && deltas.every((value) => value >= -0.5);
    const falling = deltas.length > 0 && deltas.every((value) => value <= 0.5);

    let trendLabel = "基本持平";
    if (deltaAverage >= 6 && rising) {
      trendLabel = "持续抬升";
    } else if (deltaAverage >= 3) {
      trendLabel = swing >= 8 ? "波动抬升" : "稳步抬升";
    } else if (deltaAverage <= -6 && falling) {
      trendLabel = "持续回落";
    } else if (deltaAverage <= -3) {
      trendLabel = "波动回落";
    } else if (swing >= 8) {
      trendLabel = "高位震荡";
    }

    let riskScore = 0;
    if (deltaAverage <= -6) riskScore += 3;
    else if (deltaAverage <= -3) riskScore += 2;
    if (latest && latest.excellent_rate < 35) riskScore += 2;
    else if (latest && latest.excellent_rate < 50) riskScore += 1;
    if (swing >= 10) riskScore += 2;
    else if (swing >= 6) riskScore += 1;
    if (latest && latest.average_score < 90) riskScore += 1;

    let focusLabel = "常规跟进";
    if (riskScore >= 4) {
      focusLabel = "风险预警";
    } else if (deltaAverage >= 6 && (latest?.average_score ?? 0) < 110) {
      focusLabel = "重点拉升";
    } else if ((latest?.average_score ?? 0) >= 105 && deltaAverage >= 0) {
      focusLabel = "优势巩固";
    } else if (swing >= 8) {
      focusLabel = "保持观察";
    }

    const alertLevel = riskScore >= 5 ? "高关注" : riskScore >= 3 ? "中关注" : "低关注";
    const momentumScore = Number(
      (
        deltaAverage * 2 +
        deltaExcellentRate +
        Math.max(0, ((latest?.average_score ?? 0) - 90) / 10) -
        riskScore
      ).toFixed(2),
    );

    return {
      subject_id: item.subject_id,
      subject_name: item.subject_name,
      latest_average: latest?.average_score ?? "-",
      delta_average: deltaAverage,
      latest_excellent_rate: latest?.excellent_rate ?? "-",
      delta_excellent_rate: deltaExcellentRate,
      swing,
      trendLabel,
      focusLabel,
      alertLevel,
      momentumScore,
      riskScore,
    };
  });
}

export function buildPanoramaInsightCards(panorama: PanoramaDataset | null): PanoramaInsightCard[] {
  if (!panorama) return [];
  const latest = latestExamPoint(panorama.exam_points);
  const previous = previousExamPoint(panorama.exam_points);
  const subjectRows = buildPanoramaSubjectTrendRows(panorama).sort(
    (left, right) => Number(right.delta_average) - Number(left.delta_average),
  );
  const strongest = subjectRows[0];
  const weakest = [...subjectRows].sort((left, right) => Number(left.delta_average) - Number(right.delta_average))[0];
  const latestExcellent = latest?.excellent_rate ?? null;
  const previousExcellent = previous?.excellent_rate ?? null;
  const excellentDelta =
    latestExcellent !== null && previousExcellent !== null
      ? Number((latestExcellent - previousExcellent).toFixed(2))
      : null;

  return [
    {
      label: "优秀率变化",
      value: excellentDelta === null ? "-" : (excellentDelta > 0 ? `+${excellentDelta}` : excellentDelta),
      help: latest && previous ? `${previous.exam_name} -> ${latest.exam_name}` : "需要至少两场考试才会显示变化。",
      tone: excellentDelta === null ? "tone-slate" : deltaTone(excellentDelta),
    },
    {
      label: "最近前30名",
      value: latest?.top30_count ?? "-",
      help: latest ? `${latest.exam_name} 的前30名人数` : "当前暂无考试数据。",
      tone: "tone-blue",
    },
    {
      label: "拉升最快学科",
      value: strongest?.subject_name ?? "-",
      help: strongest ? `均分变化 ${strongest.delta_average}` : "当前暂无学科趋势数据。",
      tone: "tone-green",
    },
    {
      label: "回落学科",
      value: weakest?.subject_name ?? "-",
      help: weakest ? `均分变化 ${weakest.delta_average}` : "当前暂无学科趋势数据。",
      tone: weakest && Number(weakest.delta_average) < 0 ? "tone-amber" : "tone-slate",
    },
  ];
}

export function buildPanoramaYearCompetitionRows(panorama: PanoramaDataset | null): PanoramaYearCompetitionRow[] {
  if (!panorama) return [];
  const bestAverage = Math.max(...panorama.year_summaries.map((item) => item.average_score));
  return panorama.year_summaries.map((item) => ({
    ...item,
    leadLabel: item.average_score === bestAverage ? "当前领先" : "追赶中",
  }));
}

export function buildPanoramaExamTimelineRows(panorama: PanoramaDataset | null): PanoramaExamTimelineRow[] {
  if (!panorama) return [];
  const sorted = [...panorama.exam_points].sort((left, right) => left.exam_date.localeCompare(right.exam_date));
  return sorted.map((item, index) => {
    const previous = sorted[index - 1];
    return {
      ...item,
      delta_average: previous ? Number((item.total_average - previous.total_average).toFixed(2)) : "-",
      delta_top30: previous ? item.top30_count - previous.top30_count : "-",
    };
  });
}
