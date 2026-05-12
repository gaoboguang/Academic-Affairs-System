import { beforeEach, describe, expect, it, vi } from "vitest";

const apiRequestMock = vi.fn();
const pushMock = vi.fn();

vi.mock("../src/api/client", () => ({
  apiRequest: apiRequestMock,
}));

vi.mock("element-plus/es/components/message/index", () => ({
  default: {
    error: vi.fn(),
  },
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({ push: pushMock }),
}));

describe("college catalog browser", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
    pushMock.mockReset();
  });

  it("loads college catalog summaries through the read-only paginated endpoint", async () => {
    const { useCollegeCatalogBrowser } = await import("../src/components/colleges/useCollegeCatalogBrowser");
    const browser = useCollegeCatalogBrowser();
    apiRequestMock.mockResolvedValueOnce({
      items: [
        {
          id: 1,
          name: "山东样例大学",
          college_code: "A001",
          province: "山东",
          city: "济南市",
          school_type: "综合类",
          school_level_tags_json: ["双一流"],
          supports_art: false,
          has_profile: true,
          plan_count: 12,
          admission_count: 8,
          latest_plan_year: 2025,
          latest_admission_year: 2024,
          is_active: true,
        },
      ],
      total: 4404,
      page: 2,
      page_size: 100,
    });

    browser.filters.keyword = "山东";
    browser.filters.province = "山东";
    browser.filters.school_type = "综合类";
    browser.filters.level_tag = "双一流";
    browser.filters.has_profile = "true";
    browser.filters.has_admission_data = "true";
    browser.pagination.page = 2;
    browser.pagination.page_size = 100;
    await browser.loadCatalog();

    expect(apiRequestMock).toHaveBeenCalledWith(expect.stringContaining("/api/colleges/catalog/page?"));
    const path = apiRequestMock.mock.calls[0][0] as string;
    expect(path).toContain("keyword=%E5%B1%B1%E4%B8%9C");
    expect(path).toContain("province=%E5%B1%B1%E4%B8%9C");
    expect(path).toContain("school_type=%E7%BB%BC%E5%90%88%E7%B1%BB");
    expect(path).toContain("level_tag=%E5%8F%8C%E4%B8%80%E6%B5%81");
    expect(path).toContain("has_profile=true");
    expect(path).toContain("has_admission_data=true");
    expect(path).toContain("page=2");
    expect(path).toContain("page_size=100");
    expect(browser.colleges.value).toHaveLength(1);
    expect(browser.pagination.total).toBe(4404);
  });

  it("resets filters and opens college details", async () => {
    const { useCollegeCatalogBrowser } = await import("../src/components/colleges/useCollegeCatalogBrowser");
    const browser = useCollegeCatalogBrowser();
    apiRequestMock.mockResolvedValueOnce({ items: [], total: 0, page: 1, page_size: 50 });

    browser.filters.keyword = "测试";
    browser.filters.province = "山东";
    browser.filters.has_profile = "true";
    await browser.resetFilters();

    expect(browser.filters.keyword).toBe("");
    expect(browser.filters.province).toBe("");
    expect(browser.filters.has_profile).toBe("all");
    expect(apiRequestMock).toHaveBeenCalledWith(expect.stringContaining("page=1"));

    browser.openDetail(42);
    expect(pushMock).toHaveBeenCalledWith("/colleges/42");
  });
});
