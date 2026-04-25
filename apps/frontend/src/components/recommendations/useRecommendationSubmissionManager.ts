import { computed, nextTick, reactive, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";
import type { useReferenceStore } from "../../stores/reference";

import { apiRequest } from "../../api/client";
import { formatUserActionError } from "../../utils/userFeedback";
import {
  buildRecommendationSubmissionWarningMessage,
  buildBatchRecommendationPayload,
  buildSingleRecommendationPayload,
  createRecommendationForm,
  hasRecommendationFormPendingChanges,
  validateRecommendationSubmission,
} from "./recommendationSubmission";
import type {
  BatchGenerateResponse,
  ExamOption,
  RecommendationFormState,
  RecommendationGenerateResponse,
  RecommendationHistoryItem,
  StudentOption,
} from "./types";

type ReferenceStore = ReturnType<typeof useReferenceStore>;

function reportError(error: unknown): void {
  ElMessage.error(formatUserActionError("生成推荐方案", error, "先确认学生、考试、位次或预估分数、招生计划和省份规则已准备好。"));
}

interface SubmitRecommendationOptions {
  setActiveTab: (tab: string) => void;
  loadHistory: () => Promise<void>;
  findHistoryItem: (schemeId: number) => RecommendationHistoryItem | undefined;
  viewScheme: (item: RecommendationHistoryItem) => Promise<void>;
}

interface SubmissionManagerOptions {
  referenceStore: ReferenceStore;
}

export function useRecommendationSubmissionManager(options: SubmissionManagerOptions) {
  const { referenceStore } = options;

  const generationMode = ref<"single" | "batch">("single");
  const syncingProvince = ref(false);
  const provinceAutoSynced = ref(false);
  const provinceAutoSyncSource = ref<"single" | "batch" | null>(null);
  const studentOptions = ref<StudentOption[]>([]);
  const examOptions = ref<ExamOption[]>([]);
  const latestGeneration = ref<RecommendationGenerateResponse | null>(null);
  const batchGeneration = ref<BatchGenerateResponse | null>(null);
  const generating = ref(false);

  const recommendationForm = reactive<RecommendationFormState>(createRecommendationForm());

  const isBatchMode = computed(() => generationMode.value === "batch");

  const selectedStudentLabel = computed(() => {
    if (isBatchMode.value) {
      return recommendationForm.student_ids.length ? `已选 ${recommendationForm.student_ids.length} 名学生` : "未选择";
    }
    const student = studentOptions.value.find((item) => item.id === recommendationForm.student_id);
    return student ? `${student.student_no} - ${student.name}` : "未选择";
  });

  const selectedExamLabel = computed(() => {
    const exam = examOptions.value.find((item) => item.id === recommendationForm.exam_id);
    return exam?.name ?? "未选择";
  });

  const recommendationModeLabel = computed(() =>
    isBatchMode.value ? "当前模式：批量生成" : "当前模式：单个学生",
  );

  const recommendationModeHint = computed(() =>
    isBatchMode.value
      ? buildBatchModeHint()
      : "单个学生模式会优先读取学生档案中的生源地，也支持切换正式分数、预估分数或区间模拟。",
  );

  async function loadStudentAndExamOptions(): Promise<void> {
    await referenceStore.loadCore();
    const [studentPayload, examPayload] = await Promise.all([
      apiRequest<{ items: StudentOption[] }>("/api/students?page=1&page_size=1000"),
      apiRequest<{ items: ExamOption[] }>("/api/exams?page=1&page_size=200"),
    ]);
    studentOptions.value = studentPayload.items;
    examOptions.value = examPayload.items;
  }

  async function resetRecommendationForm(): Promise<void> {
    if (hasRecommendationFormPendingChanges(recommendationForm)) {
      try {
        await ElMessageBox.confirm(
          "会清空当前推荐中心里的学生、考试、分数模式、筛选条件和补充说明。刚生成但还没回看的结果提示也会一起清空。是否继续？",
          "重置推荐参数",
          {
            type: "warning",
            confirmButtonText: "继续重置",
            cancelButtonText: "取消",
          },
        );
      } catch (error) {
        if (error === "cancel" || error === "close") return;
        reportError(error);
        return;
      }
    }
    const nextTargetYear = recommendationForm.target_year || new Date().getFullYear();
    Object.assign(recommendationForm, createRecommendationForm(), { target_year: nextTargetYear });
    latestGeneration.value = null;
    batchGeneration.value = null;
    provinceAutoSynced.value = false;
    provinceAutoSyncSource.value = null;
    ElMessage.success("推荐参数已重置");
  }

  async function submitRecommendationAction(options: SubmitRecommendationOptions): Promise<void> {
    const validationError = validateRecommendationSubmission(recommendationForm, isBatchMode.value, studentOptions.value);
    if (validationError) {
      ElMessage.warning(validationError);
      return;
    }
    const warningMessage = buildRecommendationSubmissionWarningMessage(
      recommendationForm,
      isBatchMode.value,
      studentOptions.value,
    );
    if (warningMessage) {
      try {
        await ElMessageBox.confirm(warningMessage, "生成前复核", {
          type: "warning",
          confirmButtonText: "继续生成",
          cancelButtonText: "取消",
        });
      } catch (error) {
        if (error === "cancel" || error === "close") return;
        reportError(error);
        return;
      }
    }

    try {
      generating.value = true;
      latestGeneration.value = null;
      batchGeneration.value = null;

      if (isBatchMode.value) {
        batchGeneration.value = await apiRequest<BatchGenerateResponse>("/api/recommendations/batch-generate", {
          method: "POST",
          body: JSON.stringify(buildBatchRecommendationPayload(recommendationForm)),
        });
        await options.loadHistory();
        ElMessage.success(batchGeneration.value.message);
        return;
      }

      latestGeneration.value = await apiRequest<RecommendationGenerateResponse>("/api/recommendations/generate", {
        method: "POST",
        body: JSON.stringify(buildSingleRecommendationPayload(recommendationForm)),
      });

      options.setActiveTab("recommendations");
      const generated = await loadGeneratedSchemeFromHistory(options, latestGeneration.value.scheme_id);
      if (generated) {
        await options.viewScheme(generated);
      }
      ElMessage.success("推荐方案生成成功");
    } catch (error) {
      reportError(error);
    } finally {
      generating.value = false;
    }
  }

  async function loadGeneratedSchemeFromHistory(
    options: SubmitRecommendationOptions,
    schemeId: number,
  ): Promise<RecommendationHistoryItem | undefined> {
    await options.loadHistory();
    let generated = options.findHistoryItem(schemeId);
    if (generated) {
      return generated;
    }

    await options.loadHistory();
    generated = options.findHistoryItem(schemeId);
    return generated;
  }

  function syncProvinceFromSelectedStudents(): void {
    if (isBatchMode.value) {
      if (provinceAutoSyncSource.value === "single" && recommendationForm.province.trim()) {
        clearAutoSyncedProvince();
      }
      const selectedStudents = studentOptions.value.filter((item) => recommendationForm.student_ids.includes(item.id));
      const provinces = Array.from(new Set(selectedStudents.map((item) => item.origin_province?.trim()).filter(Boolean))) as string[];
      if (provinces.length === 1 && (!recommendationForm.province.trim() || provinceAutoSynced.value)) {
        setAutoSyncedProvince(provinces[0], "batch");
        return;
      }
      if (provinces.length !== 1 && provinceAutoSynced.value) {
        clearAutoSyncedProvince();
      }
      return;
    }
    const selectedStudent = studentOptions.value.find((item) => item.id === recommendationForm.student_id);
    if (selectedStudent?.origin_province?.trim() && (!recommendationForm.province.trim() || provinceAutoSynced.value)) {
      setAutoSyncedProvince(selectedStudent.origin_province.trim(), "single");
    }
  }

  function setAutoSyncedProvince(value: string, source: "single" | "batch"): void {
    syncingProvince.value = true;
    recommendationForm.province = value;
    provinceAutoSynced.value = Boolean(value);
    provinceAutoSyncSource.value = value ? source : null;
    void nextTick(() => {
      syncingProvince.value = false;
    });
  }

  function clearAutoSyncedProvince(): void {
    syncingProvince.value = true;
    recommendationForm.province = "";
    provinceAutoSynced.value = false;
    provinceAutoSyncSource.value = null;
    void nextTick(() => {
      syncingProvince.value = false;
    });
  }

  function buildBatchModeHint(): string {
    const selectedStudents = studentOptions.value.filter((item) => recommendationForm.student_ids.includes(item.id));
    const provinces = Array.from(new Set(selectedStudents.map((item) => item.origin_province?.trim()).filter(Boolean))) as string[];
    const missingProvinceCount = selectedStudents.filter((item) => !item.origin_province?.trim()).length;
    if (recommendationForm.province.trim() && !provinceAutoSynced.value) {
      return `批量模式至少需要选择学生列表和参考考试；当前会统一按“${recommendationForm.province.trim()}”生成。`;
    }
    if (provinces.length > 1) {
      const missingSegment = missingProvinceCount ? `，另有 ${missingProvinceCount} 名学生仍未维护生源地` : "";
      return `批量模式至少需要选择学生列表和参考考试；当前会按各学生档案中的生源地分别生成：${provinces.join(" / ")}${missingSegment}。`;
    }
    if (provinces.length === 1) {
      const missingSegment = missingProvinceCount ? `，另有 ${missingProvinceCount} 名学生仍未维护生源地` : "";
      return `批量模式至少需要选择学生列表和参考考试；所选学生档案生源地一致，将默认按“${provinces[0]}”生成${missingSegment}。`;
    }
    return "批量模式至少需要选择学生列表和参考考试；如不设置统一生源地，将自动回退到各学生档案中的生源地省份。";
  }

  watch(
    () => recommendationForm.province,
    () => {
      if (!syncingProvince.value) {
        provinceAutoSynced.value = false;
        provinceAutoSyncSource.value = null;
      }
    },
  );

  watch(
    () => recommendationForm.student_id,
    () => {
      if (!isBatchMode.value) syncProvinceFromSelectedStudents();
    },
  );

  watch(
    () => recommendationForm.student_ids.slice(),
    () => {
      if (isBatchMode.value) syncProvinceFromSelectedStudents();
    },
  );

  watch(
    () => generationMode.value,
    () => {
      syncProvinceFromSelectedStudents();
    },
  );

  return {
    batchGeneration,
    examOptions,
    generating,
    generationMode,
    isBatchMode,
    latestGeneration,
    loadStudentAndExamOptions,
    recommendationForm,
    recommendationModeHint,
    recommendationModeLabel,
    resetRecommendationForm,
    selectedExamLabel,
    selectedStudentLabel,
    studentOptions,
    submitRecommendationAction,
  };
}
