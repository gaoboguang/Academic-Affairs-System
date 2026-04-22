import { describe, expect, it } from "vitest";

import {
  buildEmploymentDirectionCategorySections,
  createCollegeForm,
  createMajorForm,
  createProvinceVolunteerRuleForm,
  employmentDirectionUncategorizedLabel,
  uniqueStrings,
} from "../src/components/recommendations/helpers";
import type { EmploymentDirectionItem } from "../src/components/recommendations/types";

function buildEmploymentDirection(overrides: Partial<EmploymentDirectionItem> = {}): EmploymentDirectionItem {
  return {
    id: 1,
    name: "软件研发",
    category: "技术研发类",
    alias_names_json: [],
    description: null,
    common_job_types_json: [],
    common_industries_json: [],
    prefers_postgraduate: false,
    requires_certificate: false,
    requires_long_cycle: false,
    supports_art: false,
    risk_note: null,
    source_note: null,
    is_active: true,
    ...overrides,
  };
}

describe("recommendation helpers", () => {
  it("creates empty college forms with expected defaults", () => {
    expect(createCollegeForm()).toEqual({
      name: "",
      college_code: null,
      province: null,
      city: null,
      school_type: null,
      school_level_tags_json: [],
      intro: null,
      website: null,
      supports_art: false,
      note: null,
      alias_names: [],
      is_active: true,
    });
  });

  it("creates empty major forms with expected defaults", () => {
    expect(createMajorForm()).toEqual({
      name: "",
      major_code: null,
      category: null,
      direction: null,
      career_path: null,
      is_art_related: false,
      note: null,
      is_active: true,
    });
  });

  it("creates province volunteer rules with planning defaults", () => {
    expect(createProvinceVolunteerRuleForm()).toMatchObject({
      province: "广东",
      exam_mode: "3+1+2",
      batch: "",
      volunteer_limit: 45,
      volunteer_unit_type: "院校专业组",
      is_parallel: true,
      allow_adjustment: true,
      special_rules_json: [],
      note: null,
      is_active: true,
    });
    expect(createProvinceVolunteerRuleForm().year).toBeGreaterThanOrEqual(2026);
  });

  it("deduplicates and trims strings while dropping blanks", () => {
    expect(uniqueStrings([" 北京 ", "上海", "", "北京", null, undefined, "上海 "])).toEqual(["北京", "上海"]);
  });

  it("groups employment directions by category and keeps uncategorized items at the end", () => {
    const sections = buildEmploymentDirectionCategorySections([
      buildEmploymentDirection({ id: 1, name: "人工智能", category: "技术研发类" }),
      buildEmploymentDirection({ id: 2, name: "临床医学", category: "医药健康类" }),
      buildEmploymentDirection({ id: 3, name: "软件工程", category: "技术研发类" }),
      buildEmploymentDirection({ id: 4, name: "综合素养指导", category: null }),
    ]);

    expect(sections.map((item) => ({ label: item.label, count: item.count }))).toEqual([
      { label: "技术研发类", count: 2 },
      { label: "医药健康类", count: 1 },
      { label: employmentDirectionUncategorizedLabel, count: 1 },
    ]);
    expect(sections[0]?.directions.map((item) => item.name)).toEqual(["人工智能", "软件工程"]);
    expect(sections[2]?.directions[0]?.name).toBe("综合素养指导");
  });
});
