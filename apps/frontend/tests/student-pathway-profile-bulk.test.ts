import { describe, expect, it } from "vitest";

import {
  buildPathwayProfileBulkActions,
  pathwayProfileBulkEndpoints,
} from "../src/components/students/pathwayProfileBulk";

describe("student pathway profile bulk helpers", () => {
  it("keeps bulk template, export and import endpoints together", () => {
    expect(pathwayProfileBulkEndpoints.template).toBe("/api/gaokao/pathway-profiles/template");
    expect(pathwayProfileBulkEndpoints.export).toBe("/api/gaokao/pathway-profiles/export");
    expect(pathwayProfileBulkEndpoints.import).toBe("/api/gaokao/pathway-profiles/import");
  });

  it("describes the student-center bulk actions in teacher-facing language", () => {
    expect(buildPathwayProfileBulkActions()).toEqual([
      { label: "升学画像模板", endpoint: "/api/gaokao/pathway-profiles/template" },
      { label: "下载画像数据", endpoint: "/api/gaokao/pathway-profiles/export" },
      { label: "上传画像", endpoint: "/api/gaokao/pathway-profiles/import" },
    ]);
  });
});
