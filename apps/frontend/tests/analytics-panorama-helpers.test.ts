import { describe, expect, it } from "vitest";

import {
  buildPanoramaExamTimelineRows,
  buildPanoramaInsightCards,
  buildPanoramaMetricCards,
  buildPanoramaSubjectPriorityRows,
  buildPanoramaSubjectTrendRows,
  buildPanoramaYearCompetitionRows,
} from "../src/components/analytics/helpers";
import type { GradePanoramaResponse } from "../src/components/analytics/types";

const panorama: GradePanoramaResponse = {
  grade_id: 1,
  grade_name: "高一",
  academic_year_count: 2,
  exam_count: 2,
  year_summaries: [
    {
      academic_year_id: 1,
      academic_year_name: "2024-2025",
      exam_count: 1,
      average_score: 205,
      average_excellent_rate: 33.33,
      best_exam_name: "2025届高一4月月考",
      latest_exam_name: "2025届高一4月月考",
    },
    {
      academic_year_id: 2,
      academic_year_name: "2025-2026",
      exam_count: 1,
      average_score: 222.33,
      average_excellent_rate: 66.67,
      best_exam_name: "2026届高一4月月考",
      latest_exam_name: "2026届高一4月月考",
    },
  ],
  exam_points: [
    {
      exam_id: 1,
      exam_name: "2025届高一4月月考",
      exam_date: "2025-04-10",
      academic_year_id: 1,
      academic_year_name: "2024-2025",
      semester_name: "下学期",
      student_count: 3,
      total_average: 205,
      total_median: 212,
      excellent_rate: 33.33,
      top10_count: 3,
      top30_count: 3,
    },
    {
      exam_id: 2,
      exam_name: "2026届高一4月月考",
      exam_date: "2026-04-10",
      academic_year_id: 2,
      academic_year_name: "2025-2026",
      semester_name: "下学期",
      student_count: 3,
      total_average: 222.33,
      total_median: 230,
      excellent_rate: 66.67,
      top10_count: 3,
      top30_count: 3,
    },
  ],
  subject_trends: [
    {
      subject_id: 1,
      subject_name: "语文",
      points: [
        {
          exam_id: 1,
          exam_name: "2025届高一4月月考",
          exam_date: "2025-04-10",
          academic_year_name: "2024-2025",
          average_score: 99.33,
          excellent_rate: 33.33,
          valid_count: 3,
        },
        {
          exam_id: 2,
          exam_name: "2026届高一4月月考",
          exam_date: "2026-04-10",
          academic_year_name: "2025-2026",
          average_score: 108.67,
          excellent_rate: 66.67,
          valid_count: 3,
        },
      ],
    },
    {
      subject_id: 2,
      subject_name: "数学",
      points: [
        {
          exam_id: 1,
          exam_name: "2025届高一4月月考",
          exam_date: "2025-04-10",
          academic_year_name: "2024-2025",
          average_score: 105.67,
          excellent_rate: 33.33,
          valid_count: 3,
        },
        {
          exam_id: 2,
          exam_name: "2026届高一4月月考",
          exam_date: "2026-04-10",
          academic_year_name: "2025-2026",
          average_score: 98.67,
          excellent_rate: 16.67,
          valid_count: 3,
        },
      ],
    },
  ],
};

describe("analytics panorama helpers", () => {
  it("builds dashboard metric cards from panorama data", () => {
    const cards = buildPanoramaMetricCards(panorama);
    expect(cards).toHaveLength(6);
    expect(cards[0]?.value).toBe(2);
    expect(cards[2]?.value).toBe("+17.33");
    expect(cards[3]?.value).toBe("2025-2026");
  });

  it("builds subject trend rows with deltas", () => {
    const rows = buildPanoramaSubjectTrendRows(panorama);
    expect(rows).toHaveLength(2);
    expect(rows[0]?.subject_name).toBe("语文");
    expect(rows[0]?.delta_average).toBe(9.34);
    expect(rows[1]?.latest_average).toBe(98.67);
  });

  it("builds insight cards from latest panorama changes", () => {
    const cards = buildPanoramaInsightCards(panorama);
    expect(cards).toHaveLength(4);
    expect(cards[0]?.value).toBe("+33.34");
    expect(cards[2]?.value).toBe("语文");
    expect(cards[3]?.value).toBe("数学");
  });

  it("builds year competition rows with lead labels", () => {
    const rows = buildPanoramaYearCompetitionRows(panorama);
    expect(rows).toHaveLength(2);
    expect(rows[1]?.leadLabel).toBe("当前领先");
  });

  it("builds exam timeline rows with deltas", () => {
    const rows = buildPanoramaExamTimelineRows(panorama);
    expect(rows).toHaveLength(2);
    expect(rows[0]?.delta_average).toBe("-");
    expect(rows[1]?.delta_average).toBe(17.33);
    expect(rows[1]?.delta_top30).toBe(0);
  });

  it("builds subject priority rows for attack and risk views", () => {
    const rows = buildPanoramaSubjectPriorityRows(panorama);
    expect(rows).toHaveLength(2);
    expect(rows[0]?.trendLabel).toBe("持续抬升");
    expect(rows[0]?.focusLabel).toBe("重点拉升");
    expect(rows[1]?.trendLabel).toBe("持续回落");
    expect(rows[1]?.focusLabel).toBe("风险预警");
    expect(rows[1]?.alertLevel).toBe("高关注");
  });
});
