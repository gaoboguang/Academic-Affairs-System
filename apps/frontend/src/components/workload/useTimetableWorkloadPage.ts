import { computed, onMounted, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";

import { apiRequest, openFile, uploadFile } from "../../api/client";
import { useReferenceStore } from "../../stores/reference";
import { formatUserActionError } from "../../utils/userFeedback";
import type { ImportFeedbackResult } from "../../utils/importFeedback";
import { dimensionOptions, formatSemesterLabel, ruleVersionStatusOptions } from "./helpers";
import {
  buildTimetableReviewCards,
  buildTimetableReviewSummary,
  buildWorkloadPrecheckMessages,
  buildWorkloadResultReviewCards,
} from "./workloadReview";
import type {
  CreateRuleForm,
  EntryFormState,
  ExtraFormState,
  ExtraItem,
  RuleItem,
  RuleVersionItem,
  StatusCard,
  TeacherOption,
  TimetableBatchItem,
  TimetableEntryItem,
  WorkloadResultItem,
} from "./types";

function reportError(error: unknown): void {
  ElMessage.error(formatUserActionError("处理课表工作量", error, "先确认已选择学期、批次和规则版本；如果仍失败，请刷新页面数据后重试。"));
}

export function useTimetableWorkloadPage() {
  const referenceStore = useReferenceStore();

  const activeTab = ref("timetable");
  const teacherOptions = ref<TeacherOption[]>([]);
  const ruleVersions = ref<RuleVersionItem[]>([]);
  const ruleItems = ref<RuleItem[]>([]);
  const timetableBatches = ref<TimetableBatchItem[]>([]);
  const timetableEntries = ref<TimetableEntryItem[]>([]);
  const extras = ref<ExtraItem[]>([]);
  const results = ref<WorkloadResultItem[]>([]);

  const selectedSemesterId = ref<number | null>(null);
  const selectedRuleVersionId = ref<number | null>(null);
  const selectedBatchId = ref<number | null>(null);
  const unresolvedOnly = ref(false);
  const timetableViewMode = ref<"raw" | "teacher" | "class">("raw");

  const selectedTimetableFile = ref<File | null>(null);
  const timetableImportResult = ref<(ImportFeedbackResult & { batch_id: number; unresolved_rows: number }) | null>(null);
  const fileInputKey = ref(0);
  const importRemark = ref("");

  const importing = ref(false);
  const savingEntry = ref(false);
  const creatingRuleVersion = ref(false);
  const savingRuleItems = ref(false);
  const savingExtra = ref(false);
  const calculating = ref(false);

  const entryDialogVisible = ref(false);
  const ruleDialogVisible = ref(false);
  const resultDrawerVisible = ref(false);

  const entryForm = ref<EntryFormState>({
    teacher_id: undefined,
    class_id: undefined,
    subject_id: undefined,
    course_type: undefined,
    note: "",
    is_active: true,
  });

  const newRuleForm = ref<CreateRuleForm>({
    name: "",
    semester_id: null,
    is_default: false,
    status: "active",
    note: "",
    is_active: true,
  });

  const extraForm = ref<ExtraFormState>({
    teacher_id: undefined,
    item_name: "",
    quantity: 0,
    coefficient: 1,
    amount: null,
    note: "",
  });

  const activeResult = ref<WorkloadResultItem | null>(null);

  const semesterOptions = computed(() => referenceStore.semesters);
  const courseTypeOptions = computed(() => referenceStore.dicts.course_type ?? []);
  const currentBatch = computed(() => timetableBatches.value.find((item) => item.id === selectedBatchId.value) ?? null);
  const totalWorkload = computed(() =>
    results.value.reduce((sum, item) => sum + item.semester_workload, 0).toFixed(2),
  );
  const currentSemesterLabel = computed(() =>
    semesterOptions.value.find((item) => item.id === selectedSemesterId.value)?.name
      ? formatSemesterLabel(semesterOptions.value.find((item) => item.id === selectedSemesterId.value)!)
      : "未选择学期",
  );
  const currentRuleLabel = computed(() =>
    ruleVersions.value.find((item) => item.id === selectedRuleVersionId.value)?.name ?? "未选择规则",
  );
  const timetableReviewSummary = computed(() => buildTimetableReviewSummary(timetableEntries.value));
  const timetableReviewCards = computed(() => buildTimetableReviewCards(timetableReviewSummary.value));
  const workloadPrecheckMessages = computed(() =>
    buildWorkloadPrecheckMessages({
      selectedSemesterId: selectedSemesterId.value,
      selectedRuleVersionId: selectedRuleVersionId.value,
      currentBatch: currentBatch.value,
      ruleItemCount: ruleItems.value.length,
      reviewSummary: timetableReviewSummary.value,
    }),
  );
  const workloadResultReviewCards = computed(() => buildWorkloadResultReviewCards(results.value));
  const overviewCards = computed<StatusCard[]>(() => [
    {
      label: "课表批次",
      value: timetableBatches.value.length,
      help: "当前学期可用的课表导入批次数量。",
      tone: "tone-blue",
    },
    {
      label: "规则项",
      value: ruleItems.value.length,
      help: "当前规则版本下的有效规则项数量。",
      tone: "tone-amber",
    },
    {
      label: "附加项",
      value: extras.value.length,
      help: "当前学期已补录的附加量化项数量。",
      tone: "tone-slate",
    },
  ]);

  const processCards = computed<StatusCard[]>(() => [
    {
      label: "1. 课表批次",
      value: currentBatch.value?.source_filename ?? "未选择",
      help: currentBatch.value ? "已选择当前参与计算的课表批次。" : "请先导入或选择一个课表批次。",
      tone: currentBatch.value ? "tone-blue" : "tone-slate",
    },
    {
      label: "2. 未匹配修正",
      value: currentBatch.value ? (currentBatch.value.unresolved_count ? `待处理 ${currentBatch.value.unresolved_count}` : "已完成") : "未开始",
      help: currentBatch.value?.unresolved_count
        ? "未修正条目不会参与课时统计。"
        : "当前批次没有待修正条目，或尚未选择批次。",
      tone: currentBatch.value?.unresolved_count ? "tone-amber" : "tone-green",
    },
    {
      label: "3. 规则版本",
      value: selectedRuleVersionId.value ? currentRuleLabel.value : "未选择",
      help: selectedRuleVersionId.value ? "切换规则版本后建议重新查看结果。" : "请先选择一个规则版本。",
      tone: selectedRuleVersionId.value ? "tone-blue" : "tone-slate",
    },
    {
      label: "4. 结果输出",
      value: results.value.length ? `${results.value.length} 位教师` : "尚未计算",
      help: results.value.length ? "可继续查看明细或导出结果。" : "完成以上步骤后再执行工作量计算。",
      tone: results.value.length ? "tone-green" : "tone-slate",
    },
  ]);

  function resetExtraForm(): void {
    extraForm.value = {
      teacher_id: undefined,
      item_name: "",
      quantity: 0,
      coefficient: 1,
      amount: null,
      note: "",
    };
  }

  function resetEntryForm(): void {
    entryForm.value = {
      teacher_id: undefined,
      class_id: undefined,
      subject_id: undefined,
      course_type: undefined,
      note: "",
      is_active: true,
    };
  }

  function resetNewRuleForm(): void {
    newRuleForm.value = {
      name: "",
      semester_id: selectedSemesterId.value,
      is_default: false,
      status: ruleVersionStatusOptions[0].value,
      note: "",
      is_active: true,
    };
  }

  async function loadTeachers(): Promise<void> {
    const payload = await apiRequest<{ items: TeacherOption[] }>("/api/teachers?page=1&page_size=200");
    teacherOptions.value = payload.items;
  }

  async function loadRuleVersions(): Promise<void> {
    const payload = await apiRequest<RuleVersionItem[]>("/api/workload/rules");
    ruleVersions.value = payload;
    if (!payload.length) {
      selectedRuleVersionId.value = null;
      return;
    }
    const exists = payload.some((item) => item.id === selectedRuleVersionId.value);
    if (exists) return;
    selectedRuleVersionId.value = payload.find((item) => item.is_default)?.id ?? payload[0].id;
  }

  async function loadRuleItems(): Promise<void> {
    if (!selectedRuleVersionId.value) {
      ruleItems.value = [];
      return;
    }
    ruleItems.value = await apiRequest<RuleItem[]>(`/api/workload/rules/${selectedRuleVersionId.value}/items`);
  }

  async function loadBatches(): Promise<void> {
    if (!selectedSemesterId.value) {
      timetableBatches.value = [];
      selectedBatchId.value = null;
      return;
    }
    const payload = await apiRequest<TimetableBatchItem[]>(
      `/api/timetable/batches?semester_id=${selectedSemesterId.value}`,
    );
    timetableBatches.value = payload;
    if (!payload.length) {
      selectedBatchId.value = null;
      timetableEntries.value = [];
      return;
    }
    const exists = payload.some((item) => item.id === selectedBatchId.value);
    if (!exists) {
      selectedBatchId.value = payload[0].id;
    }
  }

  async function loadEntries(): Promise<void> {
    if (!selectedBatchId.value) {
      timetableEntries.value = [];
      return;
    }
    timetableEntries.value = await apiRequest<TimetableEntryItem[]>(
      `/api/timetable/batches/${selectedBatchId.value}/entries?unresolved_only=${unresolvedOnly.value}`,
    );
  }

  async function loadExtras(): Promise<void> {
    if (!selectedSemesterId.value) {
      extras.value = [];
      return;
    }
    extras.value = await apiRequest<ExtraItem[]>(`/api/workload/extras?semester_id=${selectedSemesterId.value}`);
  }

  async function loadResults(): Promise<void> {
    if (!selectedSemesterId.value || !selectedRuleVersionId.value) {
      results.value = [];
      return;
    }
    results.value = await apiRequest<WorkloadResultItem[]>(
      `/api/workload/results?semester_id=${selectedSemesterId.value}&rule_version_id=${selectedRuleVersionId.value}`,
    );
  }

  async function refreshAll(): Promise<void> {
    try {
      await loadTeachers();
      await loadRuleVersions();
      await Promise.all([loadBatches(), loadExtras(), loadResults()]);
      await loadEntries();
    } catch (error) {
      reportError(error);
    }
  }

  function handleTimetableFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    selectedTimetableFile.value = input.files?.[0] ?? null;
  }

  async function importTimetable(): Promise<void> {
    if (!selectedSemesterId.value || !selectedTimetableFile.value) return;
    try {
      importing.value = true;
      const payload = await uploadFile<ImportFeedbackResult & { batch_id: number; unresolved_rows: number }>(
        "/api/timetable/import",
        selectedTimetableFile.value,
        {
          semester_id: String(selectedSemesterId.value),
          remark: importRemark.value,
        },
      );
      timetableImportResult.value = payload;
      ElMessage({
        type: payload.failed_rows || payload.unresolved_rows ? "warning" : "success",
        message: payload.message,
      });
      selectedBatchId.value = payload.batch_id;
      selectedTimetableFile.value = null;
      importRemark.value = "";
      fileInputKey.value += 1;
      await Promise.all([loadBatches(), loadResults()]);
      await loadEntries();
    } catch (error) {
      reportError(error);
    } finally {
      importing.value = false;
    }
  }

  function selectBatch(batchId: number): void {
    selectedBatchId.value = batchId;
    activeTab.value = "timetable";
  }

  function openEntryDialog(row: TimetableEntryItem): void {
    entryForm.value = {
      id: row.id,
      teacher_id: row.teacher_id ?? undefined,
      class_id: row.class_id ?? undefined,
      subject_id: row.subject_id ?? undefined,
      course_type: row.course_type ?? undefined,
      note: row.note ?? "",
      is_active: row.is_active,
    };
    entryDialogVisible.value = true;
  }

  function handleEntryDialogClosed(): void {
    resetEntryForm();
  }

  async function saveEntry(): Promise<void> {
    if (!entryForm.value.id) return;
    try {
      savingEntry.value = true;
      await apiRequest<TimetableEntryItem>(`/api/timetable/entries/${entryForm.value.id}`, {
        method: "PUT",
        body: JSON.stringify({
          teacher_id: entryForm.value.teacher_id ?? null,
          class_id: entryForm.value.class_id ?? null,
          subject_id: entryForm.value.subject_id ?? null,
          course_type: entryForm.value.course_type ?? null,
          note: entryForm.value.note ?? "",
          is_active: entryForm.value.is_active,
        }),
      });
      entryDialogVisible.value = false;
      ElMessage.success("课表条目已更新");
      await Promise.all([loadBatches(), loadEntries()]);
    } catch (error) {
      reportError(error);
    } finally {
      savingEntry.value = false;
    }
  }

  function addRuleItem(): void {
    ruleItems.value.push({
      dimension_type: dimensionOptions[0].value,
      match_key: "",
      coefficient: 1,
      fixed_value: null,
      note: "",
      is_active: true,
    });
  }

  function removeRuleItem(index: number): void {
    ruleItems.value.splice(index, 1);
  }

  async function saveRuleItems(): Promise<void> {
    if (!selectedRuleVersionId.value) return;
    try {
      savingRuleItems.value = true;
      const payload = ruleItems.value.map((item) => ({
        dimension_type: item.dimension_type,
        match_key: item.match_key.trim(),
        coefficient: item.coefficient ?? null,
        fixed_value: item.fixed_value ?? null,
        note: item.note?.trim() ?? null,
        is_active: item.is_active,
      }));
      if (payload.some((item) => !item.dimension_type || !item.match_key)) {
        throw new Error("规则项的维度和匹配值不能为空");
      }
      ruleItems.value = await apiRequest<RuleItem[]>(
        `/api/workload/rules/${selectedRuleVersionId.value}/items`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      );
      ElMessage.success("规则项已保存");
    } catch (error) {
      reportError(error);
    } finally {
      savingRuleItems.value = false;
    }
  }

  async function createRuleVersion(): Promise<void> {
    if (!newRuleForm.value.name.trim()) {
      ElMessage.warning("请填写规则名称");
      return;
    }
    try {
      creatingRuleVersion.value = true;
      const payload = await apiRequest<RuleVersionItem>("/api/workload/rules", {
        method: "POST",
        body: JSON.stringify({
          name: newRuleForm.value.name.trim(),
          semester_id: newRuleForm.value.semester_id ?? null,
          is_default: newRuleForm.value.is_default,
          status: newRuleForm.value.status,
          note: newRuleForm.value.note.trim() || null,
          is_active: newRuleForm.value.is_active,
        }),
      });
      ruleDialogVisible.value = false;
      resetNewRuleForm();
      await loadRuleVersions();
      selectedRuleVersionId.value = payload.id;
      ElMessage.success("规则版本已创建");
    } catch (error) {
      reportError(error);
    } finally {
      creatingRuleVersion.value = false;
    }
  }

  function openRuleVersionDialog(): void {
    resetNewRuleForm();
    ruleDialogVisible.value = true;
  }

  function handleRuleDialogClosed(): void {
    resetNewRuleForm();
  }

  async function createExtra(): Promise<void> {
    if (!selectedSemesterId.value) {
      ElMessage.warning("请先选择学期");
      return;
    }
    if (!extraForm.value.teacher_id || !extraForm.value.item_name.trim()) {
      ElMessage.warning("请填写教师和项目名称");
      return;
    }
    try {
      savingExtra.value = true;
      await apiRequest<ExtraItem>("/api/workload/extras", {
        method: "POST",
        body: JSON.stringify({
          teacher_id: extraForm.value.teacher_id,
          semester_id: selectedSemesterId.value,
          item_name: extraForm.value.item_name.trim(),
          quantity: extraForm.value.quantity,
          coefficient: extraForm.value.coefficient,
          amount: extraForm.value.amount ?? null,
          note: extraForm.value.note.trim() || null,
          is_active: true,
        }),
      });
      resetExtraForm();
      await Promise.all([loadExtras(), loadResults()]);
      ElMessage.success("附加项已新增");
    } catch (error) {
      reportError(error);
    } finally {
      savingExtra.value = false;
    }
  }

  async function calculateWorkload(): Promise<void> {
    if (!selectedSemesterId.value || !selectedRuleVersionId.value) {
      ElMessage.warning("请先选择学期和规则版本");
      return;
    }
    try {
      const blockingMessages = workloadPrecheckMessages.value.filter((item) =>
        item.includes("请选择") || item.includes("没有规则项"),
      );
      if (blockingMessages.length) {
        ElMessage.warning(blockingMessages.join("；"));
        return;
      }
      if (currentBatch.value?.unresolved_count) {
        await ElMessageBox.confirm(
          "当前批次仍有未匹配条目，未修正条目不会参与课时统计。是否继续计算？",
          "继续计算",
          { type: "warning" },
        );
      }
      calculating.value = true;
      const payload = await apiRequest<{ message: string; result_count: number }>("/api/workload/calculate", {
        method: "POST",
        body: JSON.stringify({
          semester_id: selectedSemesterId.value,
          rule_version_id: selectedRuleVersionId.value,
          batch_id: selectedBatchId.value,
        }),
      });
      await loadResults();
      activeTab.value = "results";
      ElMessage.success(`${payload.message}，共生成 ${payload.result_count} 位教师结果`);
    } catch (error) {
      if (error === "cancel" || error === "close") return;
      reportError(error);
    } finally {
      calculating.value = false;
    }
  }

  function downloadTimetableTemplate(): void {
    openFile(
      `/api/system/files?path=${encodeURIComponent("data/templates/timetable_import_template.xlsx")}`,
    );
  }

  function exportResults(): void {
    if (!selectedSemesterId.value || !selectedRuleVersionId.value) return;
    openFile(
      `/api/workload/results/export?semester_id=${selectedSemesterId.value}&rule_version_id=${selectedRuleVersionId.value}`,
    );
  }

  function openResultDrawer(row: WorkloadResultItem): void {
    activeResult.value = row;
    resultDrawerVisible.value = true;
  }

  watch(selectedBatchId, async () => {
    try {
      await loadEntries();
    } catch (error) {
      reportError(error);
    }
  });

  watch(unresolvedOnly, async () => {
    try {
      await loadEntries();
    } catch (error) {
      reportError(error);
    }
  });

  watch(selectedSemesterId, async () => {
    try {
      await Promise.all([loadBatches(), loadExtras(), loadResults()]);
    } catch (error) {
      reportError(error);
    }
  });

  watch(selectedRuleVersionId, async () => {
    try {
      await Promise.all([loadRuleItems(), loadResults()]);
    } catch (error) {
      reportError(error);
    }
  });

  onMounted(async () => {
    try {
      await referenceStore.loadAll();
      const currentSemester = semesterOptions.value.find((item) => item.is_current) ?? semesterOptions.value[0];
      selectedSemesterId.value = currentSemester?.id ?? null;
      await refreshAll();
    } catch (error) {
      reportError(error);
    }
  });

  return {
    referenceStore,
    activeTab,
    teacherOptions,
    ruleVersions,
    ruleItems,
    timetableBatches,
    timetableEntries,
    extras,
    results,
    selectedSemesterId,
    selectedRuleVersionId,
    selectedBatchId,
    unresolvedOnly,
    timetableViewMode,
    selectedTimetableFile,
    timetableImportResult,
    fileInputKey,
    importRemark,
    importing,
    savingEntry,
    creatingRuleVersion,
    savingRuleItems,
    savingExtra,
    calculating,
    entryDialogVisible,
    ruleDialogVisible,
    resultDrawerVisible,
    entryForm,
    newRuleForm,
    extraForm,
    activeResult,
    semesterOptions,
    courseTypeOptions,
    currentBatch,
    totalWorkload,
    currentSemesterLabel,
    currentRuleLabel,
    timetableReviewSummary,
    timetableReviewCards,
    workloadPrecheckMessages,
    workloadResultReviewCards,
    overviewCards,
    processCards,
    refreshAll,
    handleTimetableFileChange,
    importTimetable,
    selectBatch,
    openEntryDialog,
    handleEntryDialogClosed,
    saveEntry,
    addRuleItem,
    removeRuleItem,
    saveRuleItems,
    createRuleVersion,
    openRuleVersionDialog,
    handleRuleDialogClosed,
    createExtra,
    calculateWorkload,
    downloadTimetableTemplate,
    exportResults,
    openResultDrawer,
  };
}
