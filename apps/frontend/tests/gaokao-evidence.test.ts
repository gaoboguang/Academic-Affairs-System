import { describe, expect, it } from "vitest";

import {
  formatGaokaoCollegeEvidenceOptionLabel,
  resolveGaokaoEvidenceCollegeId,
} from "../src/utils/gaokaoEvidence";

describe("gaokao evidence helpers", () => {
  it("formats searchable college option labels for non-database users", () => {
    expect(
      formatGaokaoCollegeEvidenceOptionLabel({
        college_id: 101,
        college_name: "山东示例大学",
        college_code: "SD001",
        province: "山东",
      }),
    ).toBe("山东示例大学 · SD001 · 山东");
  });

  it("resolves evidence targets from selected option, numeric input or a single candidate", () => {
    expect(
      resolveGaokaoEvidenceCollegeId({
        keyword: "山东示例大学",
        selectedCollegeId: 101,
        candidates: [],
      }),
    ).toBe(101);

    expect(
      resolveGaokaoEvidenceCollegeId({
        keyword: "102",
        selectedCollegeId: null,
        candidates: [],
      }),
    ).toBe(102);

    expect(
      resolveGaokaoEvidenceCollegeId({
        keyword: "山东示例学院",
        selectedCollegeId: null,
        candidates: [
          {
            college_id: 103,
            college_name: "山东示例学院",
          },
        ],
      }),
    ).toBe(103);
  });
});
