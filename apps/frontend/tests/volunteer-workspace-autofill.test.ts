import { beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick, ref } from "vue";

import { createRecommendationForm } from "../src/components/recommendations/recommendationSubmission";
import type { EmploymentDirectionItem } from "../src/components/recommendations/types";

const apiRequestMock = vi.fn();

function buildVolunteerGuideOptionsResponse() {
  return {
    province: "山东",
    year: 2026,
    candidate_types: [{ value: "general", label: "普通类" }],
    art_tracks: [],
    batches: [{ value: "本科批", label: "本科批" }],
    batch_aliases: {},
    score_input_modes: [{ value: "estimated_score", label: "校内分数估算" }],
    art_score_formulas: {},
    maintained_rule_batches: ["本科批"],
  };
}

vi.mock("../src/api/client", () => ({
  apiRequest: apiRequestMock,
  openFile: vi.fn(),
}));

vi.mock("element-plus/es/components/message/index", () => ({
  default: {
    error: vi.fn(),
    info: vi.fn(),
    success: vi.fn(),
    warning: vi.fn(),
  },
}));

vi.mock("element-plus/es/components/message-box/index", () => ({
  default: {
    confirm: vi.fn(),
  },
}));

async function flushAsyncUpdates(): Promise<void> {
  await nextTick();
  await Promise.resolve();
  await nextTick();
}

function buildWorkspaceOptions() {
  return {
    recommendationForm: createRecommendationForm(),
    planYearOptions: ref([2026]),
    batchOptions: ref(["本科批"]),
    examModeOptions: ref(["物理类"]),
    examOptions: ref([
      { id: 2, name: "202604高三二模" },
      { id: 3, name: "202605高三三模" },
    ]),
    employmentDirections: ref<EmploymentDirectionItem[]>([]),
  };
}

describe("volunteer workspace exam score autofill", () => {
  beforeEach(() => {
    apiRequestMock.mockReset();
    apiRequestMock.mockImplementation((path: string) => {
      if (path === "/api/students/1/career-preference") {
        return Promise.resolve(null);
      }
      if (path.startsWith("/api/recommendations/volunteer-guide/options?")) {
        return Promise.resolve(buildVolunteerGuideOptionsResponse());
      }
      if (path.startsWith("/api/recommendations/volunteer-drafts?")) {
        return Promise.resolve([]);
      }
      throw new Error(`unexpected api call: ${path}`);
    });
  });

  it("fills local exam score without school rank after selecting a student and reference exam", async () => {
    apiRequestMock.mockImplementation((path: string) => {
      if (path.startsWith("/api/recommendations/volunteer-guide/options?")) {
        return Promise.resolve(buildVolunteerGuideOptionsResponse());
      }
      if (path === "/api/analytics/exams/2/students") {
        return Promise.resolve({
          exam_id: 2,
          total: 1,
          items: [{ id: 1, student_no: "2026001", name: "张三", total_score: 582, grade_rank: 123 }],
        });
      }
      if (path === "/api/students/1/career-preference") return Promise.resolve(null);
      if (path.startsWith("/api/recommendations/volunteer-drafts?")) return Promise.resolve([]);
      throw new Error(`unexpected api call: ${path}`);
    });

    const { useGaokaoVolunteerWorkspace } = await import("../src/components/recommendations/useGaokaoVolunteerWorkspace");
    const workspace = useGaokaoVolunteerWorkspace(buildWorkspaceOptions());

    workspace.volunteerWorkbenchForm.student_id = 1;
    workspace.volunteerWorkbenchForm.exam_id = 2;
    await flushAsyncUpdates();

    expect(workspace.volunteerWorkbenchForm.score_input_mode).toBe("estimated_score");
    expect(workspace.volunteerWorkbenchForm.comprehensive_score).toBe(582);
    expect(workspace.volunteerWorkbenchForm.student_rank_override).toBeUndefined();
    expect(workspace.volunteerWorkbenchForm.reference_exam_name).toBe("202604高三二模");
    expect(workspace.examScoreAutofillNotice.value?.title).toBe("考试成绩已带入");
    expect(workspace.examScoreAutofillNotice.value?.detail).toContain("校内考试口径，仅作模拟参考");
  });

  it("does not overwrite manual score edits but exposes one-click apply", async () => {
    apiRequestMock.mockImplementation((path: string) => {
      if (path.startsWith("/api/recommendations/volunteer-guide/options?")) {
        return Promise.resolve(buildVolunteerGuideOptionsResponse());
      }
      if (path === "/api/analytics/exams/2/students") {
        return Promise.resolve({
          exam_id: 2,
          total: 1,
          items: [{ id: 1, student_no: "2026001", name: "张三", total_score: 582, grade_rank: 123 }],
        });
      }
      if (path === "/api/students/1/career-preference") return Promise.resolve(null);
      if (path.startsWith("/api/recommendations/volunteer-drafts?")) return Promise.resolve([]);
      throw new Error(`unexpected api call: ${path}`);
    });

    const { useGaokaoVolunteerWorkspace } = await import("../src/components/recommendations/useGaokaoVolunteerWorkspace");
    const workspace = useGaokaoVolunteerWorkspace(buildWorkspaceOptions());

    workspace.volunteerWorkbenchForm.score_input_mode = "estimated_score";
    workspace.volunteerWorkbenchForm.comprehensive_score = 590;
    workspace.volunteerWorkbenchForm.student_rank_override = 110;
    workspace.volunteerWorkbenchForm.reference_exam_name = "手动调整";
    workspace.volunteerWorkbenchForm.student_id = 1;
    workspace.volunteerWorkbenchForm.exam_id = 2;
    await flushAsyncUpdates();

    expect(workspace.volunteerWorkbenchForm.comprehensive_score).toBe(590);
    expect(workspace.volunteerWorkbenchForm.student_rank_override).toBe(110);
    expect(workspace.examScoreAutofillNotice.value?.canApply).toBe(true);

    workspace.applyCurrentExamScoreToWorkbench();

    expect(workspace.volunteerWorkbenchForm.comprehensive_score).toBe(582);
    expect(workspace.volunteerWorkbenchForm.student_rank_override).toBeUndefined();
    expect(workspace.volunteerWorkbenchForm.reference_exam_name).toBe("202604高三二模");
  });

  it("updates values when switching exams if the old values came from autofill", async () => {
    apiRequestMock.mockImplementation((path: string) => {
      if (path.startsWith("/api/recommendations/volunteer-guide/options?")) {
        return Promise.resolve(buildVolunteerGuideOptionsResponse());
      }
      if (path === "/api/analytics/exams/2/students") {
        return Promise.resolve({
          exam_id: 2,
          total: 1,
          items: [{ id: 1, student_no: "2026001", name: "张三", total_score: 582, grade_rank: 123 }],
        });
      }
      if (path === "/api/analytics/exams/3/students") {
        return Promise.resolve({
          exam_id: 3,
          total: 1,
          items: [{ id: 1, student_no: "2026001", name: "张三", total_score: 601, grade_rank: 88 }],
        });
      }
      if (path === "/api/students/1/career-preference") return Promise.resolve(null);
      if (path.startsWith("/api/recommendations/volunteer-drafts?")) return Promise.resolve([]);
      throw new Error(`unexpected api call: ${path}`);
    });

    const { useGaokaoVolunteerWorkspace } = await import("../src/components/recommendations/useGaokaoVolunteerWorkspace");
    const workspace = useGaokaoVolunteerWorkspace(buildWorkspaceOptions());

    workspace.volunteerWorkbenchForm.student_id = 1;
    workspace.volunteerWorkbenchForm.exam_id = 2;
    await flushAsyncUpdates();
    workspace.volunteerWorkbenchForm.exam_id = 3;
    await flushAsyncUpdates();

    expect(workspace.volunteerWorkbenchForm.comprehensive_score).toBe(601);
    expect(workspace.volunteerWorkbenchForm.student_rank_override).toBeUndefined();
    expect(workspace.volunteerWorkbenchForm.reference_exam_name).toBe("202605高三三模");
  });

  it("shows a missing-rank notice when the selected exam only has total score", async () => {
    apiRequestMock.mockImplementation((path: string) => {
      if (path.startsWith("/api/recommendations/volunteer-guide/options?")) {
        return Promise.resolve(buildVolunteerGuideOptionsResponse());
      }
      if (path === "/api/analytics/exams/2/students") {
        return Promise.resolve({
          exam_id: 2,
          total: 1,
          items: [{ id: 1, student_no: "2026001", name: "张三", total_score: 582, grade_rank: null }],
        });
      }
      if (path === "/api/students/1/career-preference") return Promise.resolve(null);
      if (path.startsWith("/api/recommendations/volunteer-drafts?")) return Promise.resolve([]);
      throw new Error(`unexpected api call: ${path}`);
    });

    const { useGaokaoVolunteerWorkspace } = await import("../src/components/recommendations/useGaokaoVolunteerWorkspace");
    const workspace = useGaokaoVolunteerWorkspace(buildWorkspaceOptions());

    workspace.volunteerWorkbenchForm.student_id = 1;
    workspace.volunteerWorkbenchForm.exam_id = 2;
    await flushAsyncUpdates();

    expect(workspace.volunteerWorkbenchForm.comprehensive_score).toBe(582);
    expect(workspace.volunteerWorkbenchForm.student_rank_override).toBeUndefined();
    expect(workspace.examScoreAutofillNotice.value?.detail).toContain("校内名次不用于志愿推荐");
  });
});
