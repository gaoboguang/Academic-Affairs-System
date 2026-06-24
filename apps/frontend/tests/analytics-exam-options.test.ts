import { describe, expect, it } from "vitest";

import {
  filterOptionsByExamParticipants,
  pickScopedOptionId,
  type ExamParticipantOption,
  type NamedOption,
} from "../src/components/analytics/examParticipantOptions";

const allClasses: NamedOption[] = [
  { id: 1, name: "高三1班" },
  { id: 2, name: "高三2班" },
  { id: 3, name: "高一1班" },
  { id: 4, name: "高二1班" },
];

const participants: ExamParticipantOption[] = [
  { id: 101, name: "张三", current_class_id: 1, current_grade_id: 30 },
  { id: 102, name: "李四", current_class_id: 2, current_grade_id: 30 },
  { id: 103, name: "王五", current_class_id: 1, current_grade_id: 30 },
];

describe("analytics exam scoped options", () => {
  it("only keeps classes that have students in the selected exam", () => {
    expect(filterOptionsByExamParticipants(allClasses, participants, "current_class_id")).toEqual([
      { id: 1, name: "高三1班" },
      { id: 2, name: "高三2班" },
    ]);
  });

  it("resets stale class selections to the first participating class", () => {
    const scopedClasses = filterOptionsByExamParticipants(allClasses, participants, "current_class_id");

    expect(pickScopedOptionId(scopedClasses, 3)).toBe(1);
    expect(pickScopedOptionId(scopedClasses, 2)).toBe(2);
    expect(pickScopedOptionId([], 2)).toBeNull();
  });
});
