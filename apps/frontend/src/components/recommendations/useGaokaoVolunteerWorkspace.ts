import { computed, reactive, ref, watch } from "vue";
import type { Ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";

import { apiRequest, openFile } from "../../api/client";
import { volunteerDraftPrintPreviewPath } from "../../utils/print";
import { formatUserActionError } from "../../utils/userFeedback";
import { uniqueStrings } from "./helpers";
import { buildVolunteerDraftOutputWarningMessage } from "./recommendationOutputGuards";
import {
  buildVolunteerGuideReadiness,
  buildVolunteerGuideStepCards,
  calculateVolunteerArtComprehensiveScore,
  groupVolunteerGuideCandidates,
  normalizeVolunteerBatchAlias,
} from "./volunteerGuide";
import {
  applyStudentCareerPreferenceToForm,
  applyStudentPathwayProfileToForm,
  appendVolunteerDraftItem,
  applyVolunteerExamScoreAutofill,
  buildStudentCareerPreferencePayload,
  buildVolunteerExamScoreAutofillNotice,
  buildVolunteerDraftComparison,
  buildVolunteerDraftChecks,
  buildVolunteerDraftPayload,
  buildVolunteerWorkbenchExplanation,
  buildVolunteerWorkbenchPayload,
  createVolunteerWorkbenchForm,
  formatVolunteerDraftItemLabel,
  formatVolunteerDraftSummaryLabel,
  hasVolunteerCareerPreferenceContent,
  hasVolunteerWorkbenchPendingChanges,
  isSameVolunteerCareerPreference,
  moveVolunteerDraftItem,
  reorderVolunteerDraftItem,
  removeVolunteerDraftItem,
  shouldApplyVolunteerExamScoreAutofill,
  upsertVolunteerDraftSummary,
  validateVolunteerDraftName,
  validateVolunteerWorkbenchForm,
} from "./volunteerWorkbench";
import type {
  VolunteerExamScoreAutofillNotice,
  VolunteerExamScoreAutofillSource,
  VolunteerExamScoreAutofillStatus,
} from "./volunteerWorkbench";
import type {
  EmploymentDirectionItem,
  ExamOption,
  ProvinceVolunteerRule,
  RecommendationFormState,
  ExportRecord,
  StudentCareerPreference,
  VolunteerDraftDetail,
  VolunteerDraftItem,
  VolunteerDraftSummary,
  VolunteerGuidePreviewResponse,
  VolunteerGuideOptions,
  VolunteerWorkbenchCandidate,
  VolunteerWorkbenchPreviewResponse,
} from "./types";

interface VolunteerWorkspaceOptions {
  recommendationForm: RecommendationFormState;
  planYearOptions: Ref<number[]>;
  batchOptions: Ref<string[]>;
  examModeOptions: Ref<string[]>;
  examOptions: Ref<ExamOption[]>;
  employmentDirections: Ref<EmploymentDirectionItem[]>;
}

interface ExamAnalyzableStudentItem {
  id: number;
  student_no: string;
  name: string;
  total_score?: number | null;
  grade_rank?: number | null;
}

interface ExamAnalyzableStudentListResponse {
  exam_id: number;
  total: number;
  items: ExamAnalyzableStudentItem[];
}

function reportError(error: unknown): void {
  ElMessage.error(formatUserActionError("处理志愿推荐向导", error, "先确认学生、考试、批次、规则和草稿状态正确；如果仍失败，请重新生成智能筛选后重试。"));
}

function buildWorkspaceLoadError(action: string, error: unknown): string {
  return formatUserActionError(action, error, "可先重试当前区块；如果仍失败，再检查本地服务或刷新页面。");
}

async function confirmWarningAction(message: string, title: string, confirmButtonText: string): Promise<boolean> {
  try {
    await ElMessageBox.confirm(message, title, {
      type: "warning",
      confirmButtonText,
      cancelButtonText: "取消",
    });
    return true;
  } catch (error) {
    if (error === "cancel" || error === "close") {
      return false;
    }
    reportError(error);
    return false;
  }
}

export function useGaokaoVolunteerWorkspace(options: VolunteerWorkspaceOptions) {
  const volunteerWorkbenchForm = reactive(createVolunteerWorkbenchForm());
  const workbenchPreview = ref<VolunteerWorkbenchPreviewResponse | null>(null);
  const volunteerGuidePreview = ref<VolunteerGuidePreviewResponse | null>(null);
  const workbenchPreviewError = ref("");
  const workbenchLoading = ref(false);
  const volunteerDraft = ref<VolunteerDraftItem[]>([]);
  const volunteerDraftName = ref("");
  const currentVolunteerDraftId = ref<number>();
  const savedVolunteerDrafts = ref<VolunteerDraftSummary[]>([]);
  const volunteerDraftsError = ref("");
  const loadingVolunteerDrafts = ref(false);
  const savingVolunteerDraft = ref(false);
  const exportingVolunteerDraftId = ref<number | null>(null);
  const deletingVolunteerDraftId = ref<number | null>(null);
  const persistedVolunteerRule = ref<ProvinceVolunteerRule | null>(null);
  const compareVolunteerDraftId = ref<number>();
  const compareVolunteerDraftLoading = ref(false);
  const compareVolunteerDraftError = ref("");
  const compareVolunteerDraftDetail = ref<VolunteerDraftDetail | null>(null);
  const studentCareerPreference = ref<StudentCareerPreference | null>(null);
  const studentProfileError = ref("");
  const loadingStudentCareerPreference = ref(false);
  const savingStudentCareerPreference = ref(false);
  const loadingExamScoreAutofill = ref(false);
  const loadingVolunteerGuideOptions = ref(false);
  const volunteerGuideOptions = ref<VolunteerGuideOptions | null>(null);
  const volunteerGuideOptionsError = ref("");
  const currentExamScoreAutofillSource = ref<VolunteerExamScoreAutofillSource | null>(null);
  const lastAppliedExamScoreAutofillSource = ref<VolunteerExamScoreAutofillSource | null>(null);
  const examScoreAutofillStatus = ref<VolunteerExamScoreAutofillStatus>("idle");
  const examScoreAutofillNotice = computed<VolunteerExamScoreAutofillNotice | null>(() =>
    buildVolunteerExamScoreAutofillNotice(examScoreAutofillStatus.value, currentExamScoreAutofillSource.value),
  );

  const workbenchYearOptions = computed(() =>
    Array.from(new Set([...(options.planYearOptions.value || []), volunteerWorkbenchForm.target_year].filter(Boolean) as number[])).sort(
      (left, right) => right - left,
    ),
  );
  const workbenchBatchOptions = computed(() =>
    uniqueStrings([
      ...(volunteerGuideOptions.value?.batches.map((item) => item.value) ?? []),
      ...options.batchOptions.value,
      ...(workbenchPreview.value?.applicable_rules ?? []).map((item) => item.batch),
      volunteerWorkbenchForm.batch,
    ]),
  );
  const workbenchExamModeOptions = computed(() =>
    uniqueStrings([
      ...options.examModeOptions.value,
      ...(workbenchPreview.value?.applicable_rules ?? []).map((item) => item.exam_mode),
      volunteerWorkbenchForm.exam_mode,
    ]),
  );

  const selectedVolunteerRule = computed(() => {
    const rules = workbenchPreview.value?.applicable_rules ?? [];
    if (!rules.length) return persistedVolunteerRule.value;
    return (
      rules.find(
        (item) =>
          (!volunteerWorkbenchForm.batch || item.batch === volunteerWorkbenchForm.batch)
          && (!volunteerWorkbenchForm.exam_mode || item.exam_mode === volunteerWorkbenchForm.exam_mode),
      ) ?? rules[0]
    );
  });

  const volunteerLimit = computed(() => selectedVolunteerRule.value?.volunteer_limit);
  const remainingVolunteerSlots = computed(() =>
    volunteerLimit.value === undefined ? null : Math.max(volunteerLimit.value - volunteerDraft.value.length, 0),
  );
  const selectedDraftPlanIds = computed(() => new Set(volunteerDraft.value.map((item) => item.plan_id)));
  const workbenchExplanation = computed(() =>
    buildVolunteerWorkbenchExplanation(
      volunteerWorkbenchForm,
      workbenchPreview.value,
      selectedVolunteerRule.value,
      employmentDirectionNameMap.value,
    ),
  );
  const volunteerDraftChecks = computed(() =>
    buildVolunteerDraftChecks(volunteerDraft.value, selectedVolunteerRule.value, remainingVolunteerSlots.value),
  );
  const volunteerGuideReadiness = computed(() => buildVolunteerGuideReadiness(volunteerGuidePreview.value));
  const volunteerGuideStepCards = computed(() => buildVolunteerGuideStepCards(volunteerGuidePreview.value, volunteerDraft.value.length));
  const volunteerGuideGroups = computed(() => groupVolunteerGuideCandidates(volunteerGuidePreview.value));
  const compareVolunteerDraftOptions = computed(() =>
    savedVolunteerDrafts.value.filter((item) => item.id !== currentVolunteerDraftId.value),
  );
  const volunteerDraftComparison = computed(() => {
    if (!compareVolunteerDraftDetail.value) return null;
    return buildVolunteerDraftComparison(volunteerDraft.value, mapDraftDetailItems(compareVolunteerDraftDetail.value));
  });
  const employmentDirectionNameMap = computed(
    () => new Map(options.employmentDirections.value.map((item) => [item.id, item.name])),
  );
  const workbenchCareerIndustryOptions = computed(() =>
    uniqueStrings(options.employmentDirections.value.flatMap((item) => item.common_industries_json ?? [])),
  );
  const workbenchCareerJobTypeOptions = computed(() =>
    uniqueStrings(options.employmentDirections.value.flatMap((item) => item.common_job_types_json ?? [])),
  );
  const volunteerSelectedArtFormula = computed(() =>
    calculateVolunteerArtComprehensiveScore(
      volunteerGuideOptions.value,
      volunteerWorkbenchForm.art_track,
      volunteerWorkbenchForm.culture_score,
      volunteerWorkbenchForm.professional_score,
    ),
  );

  watch(
    () => options.planYearOptions.value,
    (years) => {
      if (!volunteerWorkbenchForm.target_year && years.length) {
        volunteerWorkbenchForm.target_year = years[0];
      }
    },
    { immediate: true },
  );

  watch(
    () => [volunteerWorkbenchForm.province, volunteerWorkbenchForm.target_year] as const,
    (next, previous) => {
      if (previous && next[0] === previous[0] && next[1] === previous[1]) return;
      void loadVolunteerGuideOptions();
    },
    { immediate: true },
  );

  watch(
    () => [volunteerWorkbenchForm.student_id, volunteerWorkbenchForm.exam_id] as const,
    () => {
      clearVolunteerDraftComparison();
      void loadVolunteerDrafts();
      void loadCurrentExamScoreForWorkbench();
    },
    { immediate: true },
  );

  watch(
    () => [
      volunteerWorkbenchForm.score_input_mode,
      volunteerWorkbenchForm.comprehensive_score,
      volunteerWorkbenchForm.culture_score,
      volunteerWorkbenchForm.student_rank_override,
      volunteerWorkbenchForm.reference_exam_name,
    ] as const,
    () => {
      syncExamScoreAutofillStatusWithForm();
    },
  );

  watch(
    () => volunteerWorkbenchForm.student_id,
    () => {
      void syncSelectedStudentProfile();
    },
    { immediate: true },
  );

  function syncFromRecommendationForm(): void {
    volunteerWorkbenchForm.student_id = options.recommendationForm.student_id;
    volunteerWorkbenchForm.exam_id = options.recommendationForm.exam_id;
    volunteerWorkbenchForm.province = options.recommendationForm.province || volunteerWorkbenchForm.province;
    volunteerWorkbenchForm.target_year = options.recommendationForm.target_year || volunteerWorkbenchForm.target_year;
    volunteerWorkbenchForm.target_regions_json = [...options.recommendationForm.target_regions_json];
    volunteerWorkbenchForm.school_level_tags_json = [...options.recommendationForm.school_level_tags_json];
    volunteerWorkbenchForm.major_keyword = options.recommendationForm.major_keyword;
    volunteerWorkbenchForm.subject_combination = options.recommendationForm.subject_combination;
    volunteerWorkbenchForm.score_input_mode = options.recommendationForm.score_input_mode;
    volunteerWorkbenchForm.score_range_min = options.recommendationForm.score_range_min;
    volunteerWorkbenchForm.score_range_max = options.recommendationForm.score_range_max;
    volunteerWorkbenchForm.rank_range_min = options.recommendationForm.rank_range_min;
    volunteerWorkbenchForm.rank_range_max = options.recommendationForm.rank_range_max;
    volunteerWorkbenchForm.reference_exam_name = options.recommendationForm.reference_exam_name;
    volunteerWorkbenchForm.use_historical_mapping = options.recommendationForm.use_historical_mapping;
    volunteerWorkbenchForm.risk_preference = options.recommendationForm.risk_preference;
    volunteerWorkbenchForm.student_rank_override = options.recommendationForm.student_rank_override;
    volunteerWorkbenchForm.comprehensive_score = options.recommendationForm.comprehensive_score;
    volunteerWorkbenchForm.professional_score = options.recommendationForm.professional_score;
    volunteerWorkbenchForm.culture_score = options.recommendationForm.culture_score;
    volunteerWorkbenchForm.note = options.recommendationForm.note;
    if (!volunteerWorkbenchForm.target_year && workbenchYearOptions.value.length) {
      volunteerWorkbenchForm.target_year = workbenchYearOptions.value[0];
    }
  }

  async function syncVolunteerWorkbenchFromRecommendation(): Promise<void> {
    const shouldConfirm = hasVolunteerWorkbenchPendingChanges(
      volunteerWorkbenchForm,
      volunteerDraft.value,
      workbenchPreview.value,
      currentVolunteerDraftId.value,
    );
    if (shouldConfirm) {
      const confirmed = await confirmWarningAction(
        "会用推荐中心当前条件覆盖向导里的学生、考试、成绩/位次来源和筛选项。当前智能筛选结果和志愿草稿不会立即清空，但重新生成后会按新条件解释。是否继续？",
        "沿用推荐条件",
        "继续覆盖",
      );
      if (!confirmed) {
        return;
      }
    }
    syncFromRecommendationForm();
    ElMessage.success("已带入推荐中心条件");
  }

  function performVolunteerWorkbenchReset(): void {
    Object.assign(volunteerWorkbenchForm, createVolunteerWorkbenchForm(), {
      province: volunteerWorkbenchForm.province || options.recommendationForm.province || "山东",
      target_year: workbenchYearOptions.value[0] ?? new Date().getFullYear(),
    });
    workbenchPreview.value = null;
    volunteerGuidePreview.value = null;
    workbenchPreviewError.value = "";
    volunteerDraft.value = [];
    volunteerDraftName.value = "";
    currentVolunteerDraftId.value = undefined;
    volunteerDraftsError.value = "";
    persistedVolunteerRule.value = null;
    studentCareerPreference.value = null;
    studentProfileError.value = "";
    currentExamScoreAutofillSource.value = null;
    lastAppliedExamScoreAutofillSource.value = null;
    examScoreAutofillStatus.value = "idle";
    clearVolunteerDraftComparison();
  }

  async function resetVolunteerWorkbench(): Promise<void> {
    const shouldConfirm = hasVolunteerWorkbenchPendingChanges(
      volunteerWorkbenchForm,
      volunteerDraft.value,
      workbenchPreview.value,
      currentVolunteerDraftId.value,
    );
    if (shouldConfirm) {
      const confirmed = await confirmWarningAction(
        "会清空当前向导里的筛选条件、智能筛选结果、草稿内容和当前草稿绑定关系。未保存的临时调整不会保留。是否继续？",
        "清空工作台",
        "继续清空",
      );
      if (!confirmed) {
        return;
      }
    }
    performVolunteerWorkbenchReset();
    ElMessage.success("工作台已清空");
  }

  async function loadVolunteerWorkbenchPreview(options: { preserveDraftItems?: boolean; silent?: boolean } = {}): Promise<void> {
    const validationError = validateVolunteerWorkbenchForm(volunteerWorkbenchForm);
    if (validationError) {
      ElMessage.warning(validationError);
      return;
    }

    try {
      workbenchLoading.value = true;
      workbenchPreviewError.value = "";
      const guide = await apiRequest<VolunteerGuidePreviewResponse>(
        "/api/recommendations/volunteer-guide/preview",
        {
          method: "POST",
          body: JSON.stringify(buildVolunteerWorkbenchPayload(volunteerWorkbenchForm)),
        },
      );
      applyNormalizedGuideFields(guide);
      volunteerGuidePreview.value = guide;
      const preview = guideToWorkbenchPreview(guide);
      workbenchPreview.value = preview;
      volunteerDraft.value = reconcileDraftItems(
        preview,
        volunteerDraft.value,
        options.preserveDraftItems ?? true,
        volunteerLimit.value,
      );

      if (!preview.candidate_count) {
        if (!options.silent) ElMessage.info("当前条件下暂无可加入志愿表的候选；请查看上方就绪提示。");
        return;
      }
      if (!options.silent) ElMessage.success(`智能筛选已生成，共 ${preview.candidate_count} 条可选计划`);
    } catch (error) {
      workbenchPreviewError.value = buildWorkspaceLoadError("生成智能筛选", error);
      volunteerGuidePreview.value = null;
      workbenchPreview.value = null;
    } finally {
      workbenchLoading.value = false;
    }
  }

  async function loadVolunteerGuideOptions(): Promise<void> {
    const province = volunteerWorkbenchForm.province || "山东";
    const year = volunteerWorkbenchForm.target_year || new Date().getFullYear();
    try {
      loadingVolunteerGuideOptions.value = true;
      volunteerGuideOptionsError.value = "";
      const query = new URLSearchParams({ province, year: String(year) });
      const payload = await apiRequest<VolunteerGuideOptions>(`/api/recommendations/volunteer-guide/options?${query.toString()}`);
      volunteerGuideOptions.value = payload;
      const normalizedBatch = normalizeVolunteerBatchAlias(volunteerWorkbenchForm.batch, payload);
      if (normalizedBatch && normalizedBatch !== volunteerWorkbenchForm.batch) {
        volunteerWorkbenchForm.batch = normalizedBatch;
      }
    } catch (error) {
      volunteerGuideOptions.value = null;
      volunteerGuideOptionsError.value = buildWorkspaceLoadError("读取志愿字段选项", error);
    } finally {
      loadingVolunteerGuideOptions.value = false;
    }
  }

  function applyNormalizedGuideFields(guide: VolunteerGuidePreviewResponse): void {
    if (guide.normalized_batch && guide.normalized_batch !== volunteerWorkbenchForm.batch) {
      volunteerWorkbenchForm.batch = guide.normalized_batch;
    }
    if (guide.candidate_type && guide.candidate_type !== volunteerWorkbenchForm.candidate_type) {
      volunteerWorkbenchForm.candidate_type = guide.candidate_type;
    }
    if ((guide.art_track ?? "") !== (volunteerWorkbenchForm.art_track || "")) {
      volunteerWorkbenchForm.art_track = guide.art_track ?? "";
    }
  }

  function addVolunteerCandidate(candidate: VolunteerWorkbenchCandidate): void {
    const result = appendVolunteerDraftItem(volunteerDraft.value, candidate, volunteerLimit.value);
    volunteerDraft.value = result.items;
    if (result.added) {
      ElMessage.success("已加入志愿表");
      return;
    }
    if (result.reason === "duplicate") {
      ElMessage.warning("该计划已在志愿表中");
      return;
    }
    if (result.reason === "limit") {
      ElMessage.warning(`当前批次志愿上限为 ${volunteerLimit.value}`);
    }
  }

  async function removeVolunteerCandidate(planId: number): Promise<void> {
    const targetItem = volunteerDraft.value.find((item) => item.plan_id === planId);
    if (!targetItem) {
      return;
    }
    const confirmed = await confirmWarningAction(
      `会把“${formatVolunteerDraftItemLabel(targetItem)}”从当前志愿草稿中移除，顺序也会随之重排。是否继续？`,
      "移除志愿",
      "继续移除",
    );
    if (!confirmed) {
      return;
    }
    volunteerDraft.value = removeVolunteerDraftItem(volunteerDraft.value, planId);
    ElMessage.success("已从志愿草稿移除");
  }

  function moveVolunteerCandidate(planId: number, direction: "up" | "down"): void {
    volunteerDraft.value = moveVolunteerDraftItem(volunteerDraft.value, planId, direction);
  }

  function reorderVolunteerCandidate(planId: number, targetPlanId: number): void {
    volunteerDraft.value = reorderVolunteerDraftItem(volunteerDraft.value, planId, targetPlanId);
  }

  async function loadVolunteerDrafts(): Promise<void> {
    if (!volunteerWorkbenchForm.student_id) {
      savedVolunteerDrafts.value = [];
      volunteerDraftsError.value = "";
      return;
    }
    try {
      loadingVolunteerDrafts.value = true;
      volunteerDraftsError.value = "";
      const query = new URLSearchParams();
      query.set("student_id", String(volunteerWorkbenchForm.student_id));
      if (volunteerWorkbenchForm.exam_id) query.set("exam_id", String(volunteerWorkbenchForm.exam_id));
      savedVolunteerDrafts.value = await apiRequest<VolunteerDraftSummary[]>(
        `/api/recommendations/volunteer-drafts?${query.toString()}`,
      );
    } catch (error) {
      volunteerDraftsError.value = buildWorkspaceLoadError("加载历史草稿", error);
      savedVolunteerDrafts.value = [];
    } finally {
      loadingVolunteerDrafts.value = false;
    }
  }

  async function persistVolunteerDraft(mode: "save" | "save-as"): Promise<void> {
    const validationError = validateVolunteerWorkbenchForm(volunteerWorkbenchForm) || validateVolunteerDraftName(volunteerDraftName.value, volunteerDraft.value);
    if (validationError) {
      ElMessage.warning(validationError);
      return;
    }

    try {
      savingVolunteerDraft.value = true;
      const payload = buildVolunteerDraftPayload(
        volunteerDraftName.value,
        volunteerWorkbenchForm,
        volunteerDraft.value,
        selectedVolunteerRule.value,
      );
      const path = mode === "save-as"
        ? "/api/recommendations/volunteer-drafts"
        : currentVolunteerDraftId.value
        ? `/api/recommendations/volunteer-drafts/${currentVolunteerDraftId.value}`
        : "/api/recommendations/volunteer-drafts";
      const method = mode === "save-as" ? "POST" : currentVolunteerDraftId.value ? "PUT" : "POST";
      const savedDraft = await apiRequest<VolunteerDraftDetail>(path, {
        method,
        body: JSON.stringify(payload),
      });
      currentVolunteerDraftId.value = savedDraft.id;
      volunteerDraftName.value = savedDraft.name;
      persistedVolunteerRule.value = savedDraft.selected_rule ?? null;
      volunteerDraft.value = mapDraftDetailItems(savedDraft);
      savedVolunteerDrafts.value = upsertVolunteerDraftSummary(savedVolunteerDrafts.value, savedDraft);
      await loadVolunteerDrafts();
      ElMessage.success(mode === "save-as" ? "已另存为新草稿" : "志愿草稿已保存");
    } catch (error) {
      reportError(error);
    } finally {
      savingVolunteerDraft.value = false;
    }
  }

  async function saveVolunteerDraft(): Promise<void> {
    await persistVolunteerDraft("save");
  }

  async function saveVolunteerDraftAsNew(): Promise<void> {
    await persistVolunteerDraft("save-as");
  }

  async function loadVolunteerDraftDetail(draftId: number): Promise<void> {
    if (draftId !== currentVolunteerDraftId.value) {
      const shouldConfirm = hasVolunteerWorkbenchPendingChanges(
        volunteerWorkbenchForm,
        volunteerDraft.value,
        workbenchPreview.value,
        currentVolunteerDraftId.value,
      );
      if (shouldConfirm) {
        const targetDraft = savedVolunteerDrafts.value.find((item) => item.id === draftId);
        const confirmed = await confirmWarningAction(
          `会用历史草稿“${formatVolunteerDraftSummaryLabel(targetDraft ?? { name: `草稿 ${draftId}`, batch: null, exam_mode: null })}”覆盖当前工作台内容。未保存的临时调整不会保留。是否继续？`,
          "加载历史草稿",
          "继续加载",
        );
        if (!confirmed) {
          return;
        }
      }
    }
    try {
      workbenchLoading.value = true;
      const detail = await apiRequest<VolunteerDraftDetail>(`/api/recommendations/volunteer-drafts/${draftId}`);
      currentVolunteerDraftId.value = detail.id;
      volunteerDraftName.value = detail.name;
      persistedVolunteerRule.value = detail.selected_rule ?? null;
      Object.assign(volunteerWorkbenchForm, {
        student_id: detail.student_id,
        exam_id: detail.exam_id,
        province: detail.province,
        target_year: detail.target_year,
        batch: detail.batch ?? "",
        exam_mode: detail.exam_mode ?? "",
        candidate_type: detail.candidate_type ?? "",
        art_track: detail.art_track ?? "",
        score_input_mode: detail.score_input_mode ?? "actual_rank",
        score_range_min: detail.score_range_min ?? undefined,
        score_range_max: detail.score_range_max ?? undefined,
        rank_range_min: detail.rank_range_min ?? undefined,
        rank_range_max: detail.rank_range_max ?? undefined,
        reference_exam_name: detail.reference_exam_name ?? "",
        use_historical_mapping: detail.use_historical_mapping ?? false,
        risk_preference: detail.risk_preference ?? "balanced",
        target_regions_json: [...detail.target_regions_json],
        school_level_tags_json: [...detail.school_level_tags_json],
        major_keyword: detail.major_keyword ?? "",
        subject_combination: detail.subject_combination ?? "",
        primary_direction_id: detail.primary_direction_id ?? undefined,
        secondary_direction_id: detail.secondary_direction_id ?? undefined,
        alternative_direction_id: detail.alternative_direction_id ?? undefined,
        priority_focuses_json: [...detail.priority_focuses_json],
        preferred_industries_json: [...detail.preferred_industries_json],
        preferred_job_types_json: [...detail.preferred_job_types_json],
        target_employment_cities_json: [...detail.target_employment_cities_json],
        accepts_postgraduate: detail.accepts_postgraduate,
        accepts_public_service: detail.accepts_public_service,
        accepts_certificate: detail.accepts_certificate,
        accepts_long_training: detail.accepts_long_training,
        student_rank_override: detail.student_rank_override ?? undefined,
        comprehensive_score: detail.comprehensive_score ?? undefined,
        professional_score: detail.professional_score ?? undefined,
        culture_score: detail.culture_score ?? undefined,
        note: detail.note ?? "",
      });
      volunteerDraft.value = mapDraftDetailItems(detail);
      if (compareVolunteerDraftId.value === draftId) {
        clearVolunteerDraftComparison();
      }
      await loadVolunteerWorkbenchPreview({ preserveDraftItems: true, silent: true });
      ElMessage.success("已加载志愿草稿");
    } catch (error) {
      reportError(error);
    } finally {
      workbenchLoading.value = false;
    }
  }

  async function syncSelectedStudentProfile(): Promise<void> {
    const studentId = volunteerWorkbenchForm.student_id;
    if (!studentId) {
      studentCareerPreference.value = null;
      studentProfileError.value = "";
      return;
    }
    const province = volunteerWorkbenchForm.province || "山东";
    try {
      loadingStudentCareerPreference.value = true;
      studentProfileError.value = "";
      const profile = await apiRequest<Record<string, unknown> | null>(
        `/api/gaokao/students/${studentId}/pathway-profile?province=${encodeURIComponent(province)}`,
      );
      // Pathway profile is the single source of truth; we no longer mirror to
      // a separate career-preference table here.
      studentCareerPreference.value = null;
      applyStudentPathwayProfileToForm(volunteerWorkbenchForm, profile as never);
    } catch (error) {
      studentProfileError.value = buildWorkspaceLoadError("读取学生升学画像", error);
      studentCareerPreference.value = null;
    } finally {
      loadingStudentCareerPreference.value = false;
    }
  }

  function resolveExamName(examId: number): string {
    return options.examOptions.value.find((item) => item.id === examId)?.name ?? `考试 ${examId}`;
  }

  function setExamScoreAutofillSource(
    source: VolunteerExamScoreAutofillSource,
    forceApply = false,
  ): void {
    currentExamScoreAutofillSource.value = source;
    if (!forceApply && !shouldApplyVolunteerExamScoreAutofill(volunteerWorkbenchForm, lastAppliedExamScoreAutofillSource.value)) {
      examScoreAutofillStatus.value = "manual_override";
      return;
    }
    applyVolunteerExamScoreAutofill(volunteerWorkbenchForm, source);
    lastAppliedExamScoreAutofillSource.value = source;
    examScoreAutofillStatus.value = "applied";
  }

  function clearPreviousExamScoreAutofillIfCurrent(): void {
    const previousSource = lastAppliedExamScoreAutofillSource.value;
    if (!previousSource || !shouldApplyVolunteerExamScoreAutofill(volunteerWorkbenchForm, previousSource)) {
      return;
    }
    volunteerWorkbenchForm.score_input_mode = "actual_rank";
    volunteerWorkbenchForm.comprehensive_score = undefined;
    volunteerWorkbenchForm.culture_score = undefined;
    volunteerWorkbenchForm.student_rank_override = undefined;
    volunteerWorkbenchForm.reference_exam_name = "";
    lastAppliedExamScoreAutofillSource.value = null;
  }

  async function loadCurrentExamScoreForWorkbench(): Promise<void> {
    const studentId = volunteerWorkbenchForm.student_id;
    const examId = volunteerWorkbenchForm.exam_id;
    if (!studentId || !examId) {
      currentExamScoreAutofillSource.value = null;
      examScoreAutofillStatus.value = "idle";
      return;
    }

    try {
      loadingExamScoreAutofill.value = true;
      const payload = await apiRequest<ExamAnalyzableStudentListResponse>(`/api/analytics/exams/${examId}/students`);
      if (volunteerWorkbenchForm.student_id !== studentId || volunteerWorkbenchForm.exam_id !== examId) {
        return;
      }
      const examStudent = payload.items.find((item) => item.id === studentId);
      if (!examStudent) {
        clearPreviousExamScoreAutofillIfCurrent();
        currentExamScoreAutofillSource.value = null;
        examScoreAutofillStatus.value = "not_found";
        return;
      }
      const source: VolunteerExamScoreAutofillSource = {
        student_id: studentId,
        exam_id: examId,
        exam_name: resolveExamName(examId),
        total_score: examStudent.total_score ?? null,
        grade_rank: examStudent.grade_rank ?? null,
      };
      if (source.total_score === undefined || source.total_score === null) {
        clearPreviousExamScoreAutofillIfCurrent();
        currentExamScoreAutofillSource.value = source;
        examScoreAutofillStatus.value = "missing_score";
        return;
      }
      setExamScoreAutofillSource(source);
    } catch {
      if (volunteerWorkbenchForm.student_id === studentId && volunteerWorkbenchForm.exam_id === examId) {
        currentExamScoreAutofillSource.value = null;
        examScoreAutofillStatus.value = "load_error";
      }
    } finally {
      loadingExamScoreAutofill.value = false;
    }
  }

  function syncExamScoreAutofillStatusWithForm(): void {
    const source = currentExamScoreAutofillSource.value;
    if (!source || !["applied", "needs_rank", "manual_override"].includes(examScoreAutofillStatus.value)) {
      return;
    }
    const stillCurrent = shouldApplyVolunteerExamScoreAutofill(volunteerWorkbenchForm, source);
    if (!stillCurrent) {
      examScoreAutofillStatus.value = "manual_override";
      return;
    }
    examScoreAutofillStatus.value = "applied";
  }

  function applyCurrentExamScoreToWorkbench(): void {
    if (!currentExamScoreAutofillSource.value || currentExamScoreAutofillSource.value.total_score === undefined || currentExamScoreAutofillSource.value.total_score === null) {
      ElMessage.warning("当前考试没有可用总分，需要手动填写成绩/位次");
      return;
    }
    setExamScoreAutofillSource(currentExamScoreAutofillSource.value, true);
    ElMessage.success("已使用本次考试成绩");
  }

  async function applyStudentCareerPreference(): Promise<void> {
    if (!studentCareerPreference.value) {
      ElMessage.info("当前学生还没有已保存的职业意向");
      return;
    }
    if (
      hasVolunteerCareerPreferenceContent(volunteerWorkbenchForm)
      && !isSameVolunteerCareerPreference(volunteerWorkbenchForm, studentCareerPreference.value)
    ) {
      const confirmed = await confirmWarningAction(
        "会用该学生已保存的职业意向覆盖当前工作台里的方向、行业、岗位和可接受路径设置。是否继续？",
        "载入学生偏好",
        "继续覆盖",
      );
      if (!confirmed) {
        return;
      }
    }
    applyStudentCareerPreferenceToForm(volunteerWorkbenchForm, studentCareerPreference.value);
    ElMessage.success("已带入学生职业意向");
  }

  async function saveStudentCareerPreference(): Promise<void> {
    if (!volunteerWorkbenchForm.student_id) {
      ElMessage.warning("请先选择学生后再保存职业意向");
      return;
    }

    const payload = buildStudentCareerPreferencePayload(volunteerWorkbenchForm);
    if (!hasVolunteerCareerPreferenceContent(payload)) {
      ElMessage.warning("请至少填写一个方向、偏好或可接受路径后再保存");
      return;
    }

    try {
      savingStudentCareerPreference.value = true;
      const method = studentCareerPreference.value ? "PUT" : "POST";
      studentCareerPreference.value = await apiRequest<StudentCareerPreference>(
        `/api/students/${volunteerWorkbenchForm.student_id}/career-preference`,
        {
          method,
          body: JSON.stringify(payload),
        },
      );
      ElMessage.success("学生职业意向已保存");
    } catch (error) {
      reportError(error);
    } finally {
      savingStudentCareerPreference.value = false;
    }
  }

  async function deleteVolunteerDraft(draftId: number): Promise<void> {
    const targetDraft = savedVolunteerDrafts.value.find((item) => item.id === draftId);
    const confirmed = await confirmWarningAction(
      `删除后将无法再次直接加载“${formatVolunteerDraftSummaryLabel(targetDraft ?? { name: `草稿 ${draftId}`, batch: null, exam_mode: null })}”。当前工作台里已展开的内容不会自动清空。是否继续？`,
      "删除志愿草稿",
      "继续删除",
    );
    if (!confirmed) {
      return;
    }
    try {
      deletingVolunteerDraftId.value = draftId;
      await apiRequest<{ message: string }>(`/api/recommendations/volunteer-drafts/${draftId}`, { method: "DELETE" });
      if (currentVolunteerDraftId.value === draftId) {
        currentVolunteerDraftId.value = undefined;
        volunteerDraftName.value = "";
        persistedVolunteerRule.value = null;
      }
      if (compareVolunteerDraftId.value === draftId) {
        clearVolunteerDraftComparison();
      }
      await loadVolunteerDrafts();
      ElMessage.success("志愿草稿已删除");
    } catch (error) {
      reportError(error);
    } finally {
      deletingVolunteerDraftId.value = null;
    }
  }

  async function openVolunteerDraftPrintPreview(): Promise<void> {
    if (!currentVolunteerDraftId.value) {
      ElMessage.warning("请先保存或加载志愿草稿后再打印");
      return;
    }
    const warningMessage = buildVolunteerDraftOutputWarningMessage(volunteerDraftChecks.value);
    if (warningMessage) {
      const confirmed = await confirmWarningAction(warningMessage, "打印前复核", "仍要打印");
      if (!confirmed) {
        return;
      }
    }
    openFile(volunteerDraftPrintPreviewPath(currentVolunteerDraftId.value));
  }

  async function exportVolunteerDraft(): Promise<void> {
    if (!currentVolunteerDraftId.value) {
      ElMessage.warning("请先保存或加载志愿草稿后再导出");
      return;
    }
    const warningMessage = buildVolunteerDraftOutputWarningMessage(volunteerDraftChecks.value);
    if (warningMessage) {
      const confirmed = await confirmWarningAction(warningMessage, "导出前复核", "仍要导出");
      if (!confirmed) {
        return;
      }
    }
    try {
      exportingVolunteerDraftId.value = currentVolunteerDraftId.value;
      const result = await apiRequest<ExportRecord>("/api/reports/export", {
        method: "POST",
        body: JSON.stringify({
          report_type: "volunteer_draft_summary",
          draft_id: currentVolunteerDraftId.value,
        }),
      });
      openFile(result.download_url);
      ElMessage.success("志愿草稿已导出");
    } catch (error) {
      reportError(error);
    } finally {
      exportingVolunteerDraftId.value = null;
    }
  }

  async function loadVolunteerDraftComparison(draftId?: number): Promise<void> {
    if (!draftId || draftId === currentVolunteerDraftId.value) {
      clearVolunteerDraftComparison();
      return;
    }
    try {
      compareVolunteerDraftLoading.value = true;
      compareVolunteerDraftId.value = draftId;
      compareVolunteerDraftError.value = "";
      compareVolunteerDraftDetail.value = await apiRequest<VolunteerDraftDetail>(
        `/api/recommendations/volunteer-drafts/${draftId}`,
      );
    } catch (error) {
      compareVolunteerDraftDetail.value = null;
      compareVolunteerDraftError.value = buildWorkspaceLoadError("加载草稿对比", error);
    } finally {
      compareVolunteerDraftLoading.value = false;
    }
  }

  function clearVolunteerDraftComparison(): void {
    compareVolunteerDraftId.value = undefined;
    compareVolunteerDraftDetail.value = null;
    compareVolunteerDraftLoading.value = false;
    compareVolunteerDraftError.value = "";
  }

  return {
    addVolunteerCandidate,
    applyCurrentExamScoreToWorkbench,
    applyStudentCareerPreference,
    compareVolunteerDraftId,
    compareVolunteerDraftError,
    compareVolunteerDraftLoading,
    compareVolunteerDraftOptions,
    currentVolunteerDraftId,
    deleteVolunteerDraft,
    deletingVolunteerDraftId,
    exportVolunteerDraft,
    exportingVolunteerDraftId,
    examScoreAutofillNotice,
    loadVolunteerWorkbenchPreview,
    workbenchPreviewError,
    loadingVolunteerGuideOptions,
    volunteerGuideOptionsError,
    loadVolunteerDraftDetail,
    loadVolunteerDrafts,
    loadVolunteerDraftComparison,
    loadingVolunteerDrafts,
    volunteerDraftsError,
    loadingExamScoreAutofill,
    loadingStudentCareerPreference,
    studentProfileError,
    moveVolunteerCandidate,
    openVolunteerDraftPrintPreview,
    remainingVolunteerSlots,
    removeVolunteerCandidate,
    reorderVolunteerCandidate,
    resetVolunteerWorkbench,
    saveVolunteerDraft,
    saveVolunteerDraftAsNew,
    savedVolunteerDrafts,
    savingVolunteerDraft,
    selectedDraftPlanIds,
    studentCareerPreference,
    selectedVolunteerRule,
    saveStudentCareerPreference,
    syncVolunteerWorkbenchFromRecommendation,
    syncFromRecommendationForm,
    volunteerDraft,
    volunteerDraftComparison,
    volunteerDraftName,
    volunteerDraftChecks,
    volunteerGuideGroups,
    volunteerGuideOptions,
    volunteerSelectedArtFormula,
    volunteerGuidePreview,
    volunteerGuideReadiness,
    volunteerGuideStepCards,
    volunteerLimit,
    volunteerWorkbenchForm,
    workbenchExplanation,
    workbenchBatchOptions,
    workbenchCareerIndustryOptions,
    workbenchCareerJobTypeOptions,
    workbenchExamModeOptions,
    workbenchLoading,
    workbenchPreview,
    workbenchYearOptions,
    savingStudentCareerPreference,
  };
}

export function guideToWorkbenchPreview(guide: VolunteerGuidePreviewResponse): VolunteerWorkbenchPreviewResponse {
  const candidates = groupVolunteerGuideCandidates(guide).flatMap((group) => group.candidates.map((item) => item.candidate));
  return {
    student_id: guide.student_id,
    student_name: guide.student_name,
    exam_id: guide.exam_id,
    exam_name: guide.exam_name,
    province: guide.province,
    target_year: guide.target_year,
    student_type: guide.student_type,
    candidate_type: guide.candidate_type,
    art_track: guide.art_track,
    normalized_batch: guide.normalized_batch,
    total_score: guide.source_preview.total_score ?? 0,
    culture_score: guide.source_preview.culture_score ?? null,
    professional_score: guide.source_preview.professional_score ?? null,
    art_comprehensive_score: guide.source_preview.art_comprehensive_score ?? null,
    snapshot_rank: null,
    effective_rank: guide.source_preview.effective_rank ?? null,
    score_input_mode: guide.score_input_mode ?? guide.source_preview.score_input_mode,
    score_input_label: guide.source_preview.score_input_label,
    score_confidence: guide.source_preview.score_confidence,
    input_notes: [
      ...guide.input_notes,
      ...guide.readiness.items.map((item) => item.detail),
      ...guide.next_actions.map((item) => item.detail),
    ],
    rule_alerts: [
      ...guide.rule_alerts,
      ...guide.readiness.items
        .filter((item) => item.code !== "not_generated" && !guide.rule_alerts.some((alert) => alert.code === item.code))
        .map((item) => ({
          code: item.code,
          level: item.level === "blocking" ? "warning" : "info",
          title: item.title,
          detail: item.detail,
        })),
    ],
    applicable_rule_count: guide.applicable_rule_count,
    applicable_rules: guide.applicable_rules,
    candidate_count: guide.source_preview.candidate_count,
    returned_candidate_count: guide.source_preview.returned_candidate_count,
    is_candidate_truncated: guide.source_preview.is_candidate_truncated,
    candidates,
  };
}

function mapDraftDetailItems(detail: VolunteerDraftDetail): VolunteerDraftItem[] {
  return detail.items.map((item) => ({
    order: item.order,
    plan_id: item.plan_id ?? item.candidate.plan_id,
    candidate: item.candidate,
  }));
}

function reconcileDraftItems(
  preview: VolunteerWorkbenchPreviewResponse,
  currentItems: VolunteerDraftItem[],
  preserveMissingItems: boolean,
  limit?: number,
): VolunteerDraftItem[] {
  const candidateMap = new Map(preview.candidates.map((item) => [item.plan_id, item]));
  const nextItems = currentItems
    .filter((item) => preserveMissingItems || candidateMap.has(item.plan_id))
    .map((item) => ({
      ...item,
      candidate: candidateMap.get(item.plan_id) ?? item.candidate,
    }));
  return limit !== undefined ? nextItems.slice(0, limit) : nextItems;
}
