import { describe, expect, it } from "vitest";

import {
  buildExamSubjectOptions,
  getExamSubjectDefaultFullScore,
  getStandardExamSubjectIds,
  syncExamSubjectRows,
} from "../src/components/exams/examSubjectConfig";
import type { OptionItem } from "../src/stores/reference";

const subjectOptions: Array<OptionItem & { sort_order: number; is_in_total_default: boolean }> = [
  { id: 1, code: "chinese", name: "语文", sort_order: 1, is_in_total_default: true },
  { id: 2, code: "math", name: "数学", sort_order: 2, is_in_total_default: true },
  { id: 3, code: "english", name: "英语", sort_order: 3, is_in_total_default: true },
  { id: 4, code: "japanese", name: "日语", sort_order: 4, is_in_total_default: true },
  { id: 5, code: "physics", name: "物理", sort_order: 5, is_in_total_default: true },
  { id: 6, code: "history", name: "历史", sort_order: 6, is_in_total_default: true },
];

describe("exam subject config", () => {
  it("assigns expected default full scores for core and small language subjects", () => {
    expect(getExamSubjectDefaultFullScore({ code: "chinese", name: "语文" })).toBe(150);
    expect(getExamSubjectDefaultFullScore({ code: "english", name: "英语" })).toBe(150);
    expect(getExamSubjectDefaultFullScore({ code: "japanese", name: "日语" })).toBe(150);
    expect(getExamSubjectDefaultFullScore({ code: "physics", name: "物理" })).toBe(100);
    expect(getExamSubjectDefaultFullScore({ code: "history", name: "历史" })).toBe(100);
  });

  it("returns the standard nine-subject preset without small languages", () => {
    expect(getStandardExamSubjectIds(subjectOptions)).toEqual([1, 2, 3, 5, 6]);
  });

  it("preserves edited rows and creates defaults for newly checked subjects", () => {
    const rows = syncExamSubjectRows(
      [1, 4, 5],
      subjectOptions,
      [
        {
          subject_id: 1,
          full_score: 160,
          excellent_line: 120,
          pass_line: 96,
          is_in_total: true,
          sort_order: 8,
          is_active: true,
        },
      ],
    );

    expect(rows).toEqual([
      expect.objectContaining({
        subject_id: 1,
        full_score: 160,
        excellent_line: 120,
        pass_line: 96,
        sort_order: 8,
      }),
      expect.objectContaining({
        subject_id: 4,
        full_score: 150,
        excellent_line: null,
        pass_line: null,
        is_in_total: true,
      }),
      expect.objectContaining({
        subject_id: 5,
        full_score: 100,
        excellent_line: null,
        pass_line: null,
        is_in_total: true,
      }),
    ]);
  });

  it("keeps built-in subject ordering stable for the checkbox list", () => {
    const ordered = buildExamSubjectOptions([...subjectOptions].reverse());
    expect(ordered.map((item) => item.code)).toEqual([
      "chinese",
      "math",
      "english",
      "japanese",
      "physics",
      "history",
    ]);
  });
});
