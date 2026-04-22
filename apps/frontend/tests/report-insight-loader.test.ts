import { describe, expect, it } from "vitest";

import {
  createEmptyReportInsightDataState,
  fetchReportInsightData,
} from "../src/components/reports/reportInsightLoader";

describe("report insight loader", () => {
  it("creates an empty report insight state", () => {
    expect(createEmptyReportInsightDataState()).toEqual({
      recommendationResults: [],
      recommendationCompareResults: [],
      volunteerDraftDetail: null,
      studentAnalysis: null,
      classAnalysis: null,
      gradeAnalysis: null,
      teacherAnalysis: null,
      workloadResults: [],
      evaluationOverview: null,
      adviserSummary: [],
      growthInsight: null,
    });
  });

  it("loads recommendation summary results for the selected scheme and student", async () => {
    const calls: string[] = [];
    const data = await fetchReportInsightData(
      {
        report_type: "recommendation_summary",
        scheme_id: 23,
        student_id: 7,
      },
      async <T>(url: string): Promise<T> => {
        calls.push(url);
        return [
          {
            id: 1,
            student_id: 7,
            exam_id: 5,
            scheme_id: 23,
            result_type: "steady",
            college_id: 11,
            score_basis: "rank",
            generated_at: "2026-04-12T00:00:00",
            is_active: true,
          },
        ] as T;
      },
    );

    expect(calls).toEqual(["/api/recommendations/history/23/results?student_id=7"]);
    expect(data.recommendationResults).toHaveLength(1);
    expect(data.recommendationCompareResults).toEqual([]);
    expect(data.volunteerDraftDetail).toBeNull();
    expect(data.studentAnalysis).toBeNull();
  });

  it("loads recommendation comparison results when compare scheme is provided", async () => {
    const calls: string[] = [];
    const data = await fetchReportInsightData(
      {
        report_type: "recommendation_summary",
        scheme_id: 23,
        student_id: 7,
      },
      async <T>(url: string): Promise<T> => {
        calls.push(url);
        return [
          {
            id: url.includes("/27/") ? 2 : 1,
            student_id: 7,
            exam_id: 5,
            scheme_id: url.includes("/27/") ? 27 : 23,
            result_type: "steady",
            college_id: 11,
            score_basis: "rank",
            generated_at: "2026-04-12T00:00:00",
            is_active: true,
          },
        ] as T;
      },
      {
        recommendationCompareSchemeId: 27,
      },
    );

    expect(calls).toEqual([
      "/api/recommendations/history/23/results?student_id=7",
      "/api/recommendations/history/27/results?student_id=7",
    ]);
    expect(data.recommendationResults[0]?.scheme_id).toBe(23);
    expect(data.recommendationCompareResults[0]?.scheme_id).toBe(27);
  });

  it("loads workload summary with semester and rule version query", async () => {
    const calls: string[] = [];
    const data = await fetchReportInsightData(
      {
        report_type: "teacher_workload",
        semester_id: 9,
        rule_version_id: 3,
      },
      async <T>(url: string): Promise<T> => {
        calls.push(url);
        return [
          {
            semester_name: "2025-2026 下学期",
            rule_version_name: "默认规则 v3",
            teacher_name: "张老师",
            weekly_hours: 18,
            semester_hours: 324,
            semester_workload: 356,
          },
        ] as T;
      },
    );

    expect(calls).toEqual(["/api/workload/results?semester_id=9&rule_version_id=3"]);
    expect(data.workloadResults[0]?.teacher_name).toBe("张老师");
    expect(data.recommendationResults).toEqual([]);
  });

  it("loads growth summary by combining profile and record timeline", async () => {
    const calls: string[] = [];
    const data = await fetchReportInsightData(
      {
        report_type: "growth_summary",
        student_id: 18,
      },
      async <T>(url: string): Promise<T> => {
        calls.push(url);
        if (url === "/api/students/18/profile") {
          return {
            student: {
              student_no: "2026018",
              name: "陈同学",
              current_grade_name: "高二",
              current_class_name: "1班",
            },
          } as T;
        }
        return {
          items: [
            {
              id: 1,
              occurred_on: "2026-04-12",
              record_type: "activity",
              title: "社会实践",
              attachments: [],
            },
          ],
          total: 1,
        } as T;
      },
    );

    expect(calls).toEqual([
      "/api/students/18/profile",
      "/api/archives/students/18/records",
    ]);
    expect(data.growthInsight?.profile.student.name).toBe("陈同学");
    expect(data.growthInsight?.records).toHaveLength(1);
  });
});
