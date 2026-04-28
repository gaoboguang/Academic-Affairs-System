import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

const apiRequestMock = vi.fn();
const uploadFileMock = vi.fn();

vi.mock("../src/api/client", () => ({
  apiRequest: apiRequestMock,
  openFile: vi.fn(),
  uploadFile: uploadFileMock,
}));

vi.mock("element-plus/es/components/message/index", () => ({
  default: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
  },
}));

vi.mock("element-plus/es/components/message-box/index", () => ({
  default: {
    confirm: vi.fn(),
  },
}));

describe("recommendation large table loading", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
    uploadFileMock.mockReset();
  });

  it("loads majors and admissions through paginated endpoints", async () => {
    const { useRecommendationCatalogManager } = await import(
      "../src/components/recommendations/useRecommendationCatalogManager"
    );
    const manager = useRecommendationCatalogManager();

    apiRequestMock.mockResolvedValueOnce({
      items: [{ id: 1, name: "软件工程", is_art_related: false, is_active: true }],
      total: 27889,
      page: 2,
      page_size: 100,
    });
    manager.majorFilters.keyword = "软件";
    manager.majorPagination.page = 2;
    manager.majorPagination.page_size = 100;
    await manager.loadMajors();

    expect(apiRequestMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/api/majors/page?"),
    );
    expect(apiRequestMock.mock.calls.at(-1)?.[0]).toContain("keyword=%E8%BD%AF%E4%BB%B6");
    expect(manager.majors.value).toHaveLength(1);
    expect(manager.majorPagination.total).toBe(27889);

    apiRequestMock.mockResolvedValueOnce({
      items: [{ id: 1, year: 2025, province: "山东", batch: "常规批", college_id: 1, student_type: "general", is_active: true }],
      total: 183121,
      page: 1,
      page_size: 50,
    });
    await manager.loadAdmissions({ resetPage: true });

    expect(apiRequestMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/api/admissions/page?"),
    );
    expect(manager.admissions.value).toHaveLength(1);
    expect(manager.admissionPagination.total).toBe(183121);
  });

  it("loads enrollment plans through the paginated endpoint", async () => {
    const { useGaokaoPlanningManager } = await import(
      "../src/components/recommendations/useGaokaoPlanningManager"
    );
    const manager = useGaokaoPlanningManager({ collegeDirectory: ref([]) });

    apiRequestMock.mockResolvedValueOnce({
      items: [
        {
          id: 1,
          year: 2024,
          province: "山东",
          batch: "常规批",
          exam_mode: "3+3",
          college_id: 1,
          major_group_code: "001",
          plan_count: 1,
          student_type: "general",
          is_active: true,
        },
      ],
      total: 62029,
      page: 1,
      page_size: 50,
    });
    await manager.loadEnrollmentPlans({ resetPage: true });

    expect(apiRequestMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/api/enrollment-plans/page?"),
    );
    expect(manager.enrollmentPlans.value).toHaveLength(1);
    expect(manager.enrollmentPlanPagination.total).toBe(62029);
  });
});
