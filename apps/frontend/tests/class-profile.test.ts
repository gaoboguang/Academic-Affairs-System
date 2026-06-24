import { describe, expect, it } from "vitest";

import {
  buildTeachingSetupPath,
  buildClassOverviewCards,
  buildClassProfileCards,
  filterClasses,
  formatClassTeachers,
  formatPercent,
  formatScore,
  getTeachingSetupLabel,
  type ClassesOverviewResponse,
  type ClassOverviewItem,
  type ClassProfileResponse,
} from "../src/components/classes/classProfile";

const classOne: ClassOverviewItem = {
  class_id: 1,
  class_name: "1班",
  grade_id: 1,
  grade_name: "高一",
  class_type: "key",
  head_teacher_id: 1,
  head_teacher_name: "李语文",
  student_count: 2,
  active_student_count: 2,
  teacher_count: 2,
  teacher_summary: [
    { teacher_id: 1, teacher_name: "李语文", subject_id: 1, subject_name: "语文", course_type: "regular" },
    { teacher_id: 2, teacher_name: "王数学", subject_id: 2, subject_name: "数学", course_type: "regular" },
  ],
  honor_count: 1,
  latest_honor: {
    id: 1,
    class_id: 1,
    title: "校级先进班集体",
    honor_level: "校级",
    awarded_on: "2026-04-20",
    is_active: true,
  },
  score_summary: { exam_id: 1, exam_name: "月考", sample_count: 2, average_score: 245 },
  risk_summary: { follow_up_count: 1, urgent_count: 0, score_risk_count: 1, planning_risk_count: 0, growth_record_count: 1 },
  teaching_complete: true,
};

const classTwo: ClassOverviewItem = {
  ...classOne,
  class_id: 2,
  class_name: "2班",
  class_type: "normal",
  head_teacher_id: null,
  head_teacher_name: null,
  active_student_count: 1,
  teacher_count: 0,
  teacher_summary: [],
  honor_count: 0,
  latest_honor: null,
  score_summary: { sample_count: 0 },
  risk_summary: { follow_up_count: 0, urgent_count: 0, score_risk_count: 0, planning_risk_count: 0, growth_record_count: 0 },
  teaching_complete: false,
};

describe("class profile helpers", () => {
  it("formats class profile values", () => {
    expect(formatPercent(0.5)).toBe("50.0%");
    expect(formatScore(245)).toBe("245");
    expect(formatScore(245.25)).toBe("245.3");
    expect(formatClassTeachers(classOne.teacher_summary)).toBe("语文-李语文、数学-王数学");
    expect(formatClassTeachers([])).toBe("暂无任课");
  });

  it("builds overview and profile cards from aggregate payloads", () => {
    const overview: ClassesOverviewResponse = {
      semester_id: 2,
      semester_name: "2025-2026 下学期",
      exam_id: 1,
      exam_name: "月考",
      total_classes: 2,
      total_students: 3,
      total_honors: 1,
      grades: [
        {
          grade_id: 1,
          grade_name: "高一",
          class_count: 2,
          student_count: 3,
          active_student_count: 3,
          head_teacher_coverage: 0.5,
          teaching_complete_rate: 0.5,
          latest_exam_sample_count: 2,
          honor_count: 1,
          classes: [classOne, classTwo],
        },
      ],
    };
    expect(buildClassOverviewCards(overview).map((item) => item.value)).toEqual([1, 2, 3, "50.0%", 1]);

    const profile: ClassProfileResponse = {
      overview: classOne,
      honors: [classOne.latest_honor!],
      students: [],
      assignments: [],
    };
    expect(buildClassProfileCards(profile).map((item) => item.value)).toEqual([2, 2, 1, 2, 1]);
  });

  it("filters classes by coverage, honor and keyword", () => {
    expect(filterClasses([classOne, classTwo], { keyword: "先进", honor: "has" }).map((item) => item.class_id)).toEqual([1]);
    expect(filterClasses([classOne, classTwo], { headTeacher: "missing" }).map((item) => item.class_id)).toEqual([2]);
    expect(filterClasses([classOne, classTwo], { teaching: "complete" }).map((item) => item.class_id)).toEqual([1]);
    expect(filterClasses([classOne, classTwo], { classType: "normal" }).map((item) => item.class_id)).toEqual([2]);
  });

  it("builds teaching setup entry labels and deep links", () => {
    expect(getTeachingSetupLabel(classOne)).toBe("维护任课");
    expect(getTeachingSetupLabel(classTwo)).toBe("设置任课");
    expect(buildTeachingSetupPath(12)).toBe("/classes/12?tab=teachers&action=assignment");
  });
});
