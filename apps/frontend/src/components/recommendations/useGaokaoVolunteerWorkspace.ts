import { computed, reactive, ref, watch } from "vue";
import type { Ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";

import { apiRequest, openFile } from "../../api/client";
import { volunteerDraftPrintPreviewPath } from "../../utils/print";
import { uniqueStrings } from "./helpers";
import { buildVolunteerDraftOutputWarningMessage } from "./recommendationOutputGuards";
import {
  applyStudentCareerPreferenceToForm,
  appendVolunteerDraftItem,
  buildStudentCareerPreferencePayload,
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
  validateVolunteerDraftName,
  validateVolunteerWorkbenchForm,
} from "./volunteerWorkbench";
import type {
  EmploymentDirectionItem,
  ProvinceVolunteerRule,
  RecommendationFormState,
  ExportRecord,
  StudentCareerPreference,
  VolunteerDraftDetail,
  VolunteerDraftItem,
  VolunteerDraftSummary,
  VolunteerWorkbenchCandidate,
  VolunteerWorkbenchPreviewResponse,
} from "./types";

interface VolunteerWorkspaceOptions {
  recommendationForm: RecommendationFormState;
  planYearOptions: Ref<number[]>;
  batchOptions: Ref<string[]>;
  examModeOptions: Ref<string[]>;
  employmentDirections: Ref<EmploymentDirectionItem[]>;
}

function reportError(error: unknown): void {
  ElMessage.error((error as Error).message);
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
  const workbenchLoading = ref(false);
  const volunteerDraft = ref<VolunteerDraftItem[]>([]);
  const volunteerDraftName = ref("");
  const currentVolunteerDraftId = ref<number>();
  const savedVolunteerDrafts = ref<VolunteerDraftSummary[]>([]);
  const loadingVolunteerDrafts = ref(false);
  const savingVolunteerDraft = ref(false);
  const exportingVolunteerDraftId = ref<number | null>(null);
  const deletingVolunteerDraftId = ref<number | null>(null);
  const persistedVolunteerRule = ref<ProvinceVolunteerRule | null>(null);
  const compareVolunteerDraftId = ref<number>();
  const compareVolunteerDraftLoading = ref(false);
  const compareVolunteerDraftDetail = ref<VolunteerDraftDetail | null>(null);
  const studentCareerPreference = ref<StudentCareerPreference | null>(null);
  const loadingStudentCareerPreference = ref(false);
  const savingStudentCareerPreference = ref(false);

  const workbenchYearOptions = computed(() =>
    Array.from(new Set([...(options.planYearOptions.value || []), volunteerWorkbenchForm.target_year].filter(Boolean) as number[])).sort(
      (left, right) => right - left,
    ),
  );
  const workbenchBatchOptions = computed(() =>
    uniqueStrings([
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
    () => [volunteerWorkbenchForm.student_id, volunteerWorkbenchForm.exam_id] as const,
    () => {
      clearVolunteerDraftComparison();
      void loadVolunteerDrafts();
    },
    { immediate: true },
  );

  watch(
    () => volunteerWorkbenchForm.student_id,
    () => {
      void loadStudentCareerPreference();
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
        "会用推荐中心当前条件覆盖工作台里的学生、考试、分数模式和筛选项。当前候选池和志愿草稿不会立即清空，但刷新后会按新条件重新解释。是否继续？",
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
      province: volunteerWorkbenchForm.province || options.recommendationForm.province || "广东",
      target_year: workbenchYearOptions.value[0] ?? new Date().getFullYear(),
    });
    workbenchPreview.value = null;
    volunteerDraft.value = [];
    volunteerDraftName.value = "";
    currentVolunteerDraftId.value = undefined;
    persistedVolunteerRule.value = null;
    studentCareerPreference.value = null;
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
        "会清空当前工作台里的筛选条件、候选池结果、草稿内容和当前草稿绑定关系。未保存的临时调整不会保留。是否继续？",
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
      const preview = await apiRequest<VolunteerWorkbenchPreviewResponse>(
        "/api/recommendations/volunteer-workbench/preview",
        {
          method: "POST",
          body: JSON.stringify(buildVolunteerWorkbenchPayload(volunteerWorkbenchForm)),
        },
      );
      workbenchPreview.value = preview;
      volunteerDraft.value = reconcileDraftItems(
        preview,
        volunteerDraft.value,
        options.preserveDraftItems ?? true,
        volunteerLimit.value,
      );

      if (!preview.candidate_count) {
        if (!options.silent) ElMessage.info("当前条件下暂无可加入候选池的招生计划");
        return;
      }
      if (!options.silent) ElMessage.success(`候选池已刷新，共 ${preview.candidate_count} 条可选计划`);
    } catch (error) {
      reportError(error);
    } finally {
      workbenchLoading.value = false;
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
      return;
    }
    try {
      loadingVolunteerDrafts.value = true;
      const query = new URLSearchParams();
      query.set("student_id", String(volunteerWorkbenchForm.student_id));
      if (volunteerWorkbenchForm.exam_id) query.set("exam_id", String(volunteerWorkbenchForm.exam_id));
      savedVolunteerDrafts.value = await apiRequest<VolunteerDraftSummary[]>(
        `/api/recommendations/volunteer-drafts?${query.toString()}`,
      );
    } catch (error) {
      reportError(error);
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

  async function loadStudentCareerPreference(): Promise<void> {
    if (!volunteerWorkbenchForm.student_id) {
      studentCareerPreference.value = null;
      return;
    }
    try {
      loadingStudentCareerPreference.value = true;
      studentCareerPreference.value = await apiRequest<StudentCareerPreference | null>(
        `/api/students/${volunteerWorkbenchForm.student_id}/career-preference`,
      );
    } catch (error) {
      reportError(error);
      studentCareerPreference.value = null;
    } finally {
      loadingStudentCareerPreference.value = false;
    }
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
      compareVolunteerDraftDetail.value = await apiRequest<VolunteerDraftDetail>(
        `/api/recommendations/volunteer-drafts/${draftId}`,
      );
    } catch (error) {
      clearVolunteerDraftComparison();
      reportError(error);
    } finally {
      compareVolunteerDraftLoading.value = false;
    }
  }

  function clearVolunteerDraftComparison(): void {
    compareVolunteerDraftId.value = undefined;
    compareVolunteerDraftDetail.value = null;
    compareVolunteerDraftLoading.value = false;
  }

  return {
    addVolunteerCandidate,
    applyStudentCareerPreference,
    compareVolunteerDraftId,
    compareVolunteerDraftLoading,
    compareVolunteerDraftOptions,
    currentVolunteerDraftId,
    deleteVolunteerDraft,
    deletingVolunteerDraftId,
    exportVolunteerDraft,
    exportingVolunteerDraftId,
    loadVolunteerWorkbenchPreview,
    loadVolunteerDraftDetail,
    loadVolunteerDrafts,
    loadVolunteerDraftComparison,
    loadingVolunteerDrafts,
    loadingStudentCareerPreference,
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
