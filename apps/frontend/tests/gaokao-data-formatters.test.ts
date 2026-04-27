import { describe, expect, it } from "vitest";

import {
  formatGroupChapterCell,
  formatMonitorStatus,
  formatSourceMode,
  statusTagType,
} from "../src/components/gaokao-data/gaokaoDataFormatters";

describe("gaokao data formatters", () => {
  it("keeps page copy helpers outside the large page component", () => {
    expect(formatSourceMode("db_rc1_live")).toBe("本地高考只读库");
    expect(formatMonitorStatus("pending_official_release")).toBe("待官方发布");
    expect(statusTagType("missing")).toBe("danger");
    expect(formatGroupChapterCell({ fallback_url: "https://example.edu/path/" })).toBe("example.edu（备用）");
  });
});
