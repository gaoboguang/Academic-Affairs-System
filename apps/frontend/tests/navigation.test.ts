import { describe, expect, it } from "vitest";

import { navSections, resolveNavItem } from "../src/layouts/navigation";

describe("navigation", () => {
  it("exposes stable top-level sections", () => {
    expect(navSections.map((section) => section.id)).toEqual(["home", "base", "teaching", "decision"]);
  });

  it("matches detail routes by prefix", () => {
    const studentItem = resolveNavItem("/students/42");
    const teacherItem = resolveNavItem("/teachers/99");

    expect(studentItem.path).toBe("/students");
    expect(studentItem.sectionId).toBe("base");
    expect(teacherItem.path).toBe("/teachers");
    expect(teacherItem.sectionId).toBe("base");
  });

  it("exposes the gaokao data cockpit in the decision section", () => {
    const gaokaoItem = resolveNavItem("/gaokao-data");

    expect(gaokaoItem.path).toBe("/gaokao-data");
    expect(gaokaoItem.sectionId).toBe("decision");
    expect(gaokaoItem.label).toBe("高考数据");
  });

  it("falls back to dashboard for unknown paths", () => {
    expect(resolveNavItem("/unknown").path).toBe("/");
  });
});
