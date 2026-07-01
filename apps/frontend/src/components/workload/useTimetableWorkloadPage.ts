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

type WorkloadLoadKey =
  | "reference"
  | "teachers"
  | "ruleVersions"
  | "ruleItems"
  | "batches"
  | "entries"
  | "extras"
  | "results";

interface WorkloadLoadErrorItem {
  key: WorkloadLoadKey;
  label: string;
  message: string;
  loading: boolean;
}

function buildLoadError(action: string, error: unknown): string {
  return formatUserActionError(action, error, "可先重试当前区块；如果仍失败，再刷新页面或检查本地后端服务。");
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

  const loadingReference = ref(false);
  const loadingTeacherOptions = ref(false);
  const loadingRuleVersions = ref(false);
  const loadingRuleItems = ref(false);
  const loadingBatches = ref(false);
  const loadingEntries = ref(false);
  const loadingExtras = ref(false);
  const loadingResults = ref(false);

  const referenceError = ref("");
  const teacherOptionsError = ref("");
  const ruleVersionsError = ref("");
  const ruleItemsError = ref("");
  const batchesError = ref("");
  const entriesError = ref("");
  const extrasError = ref("");
  const resultsError = ref("");
  const workloadActionError = ref("");

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
  const workloadWriteBusy = computed(() =>
    importing.value
    || savingEntry.value
    || creatingRuleVersion.value
    || savingRuleItems.value
    || savingExtra.value
    || calculating.value,
  );
  const workloadRefreshBusy = computed(() =>
    loadingReference.value
    || loadingTeacherOptions.value
    || loadingRuleVersions.value
    || loadingRuleItems.value
    || loadingBatches.value
    || loadingEntries.value
    || loadingExtras.value
    || loadingResults.value,
  );
  const workloadSelectionDisabled = computed(() => workloadWriteBusy.value);
  const calculateDisabled = computed(() =>
    (workloadWriteBusy.value && !calculating.value)
    || loadingReference.value
    || loadingRuleVersions.value
    || loadingRuleItems.value
    || loadingBatches.value
    || loadingEntries.value
    || !selectedSemesterId.value
    || !selectedRuleVersionId.value,
  );
  const exportResultsDisabled = computed(() =>
    !results.value.length
    || loadingResults.value
    || Boolean(resultsError.value)
    || workloadWriteBusy.value,
  );
  const timetableImportDisabled = computed(() =>
    !selectedSemesterId.value
    || !selectedTimetableFile.value
    || workloadWriteBusy.value
    || loadingReference.value
    || Boolean(referenceError.value),
  );
  const timetablePanelActionsDisabled = computed(() =>
    workloadWriteBusy.value
    || loadingBatches.value
    || loadingEntries.value,
  );
  const ruleActionsDisabled = computed(() =>
    importing.value
    || savingEntry.value
    || creatingRuleVersion.value
    || calculating.value
    || loadingRuleVersions.value
    || Boolean(ruleVersionsError.value),
  );
  const ruleItemControlsDisabled = computed(() =>
    ruleActionsDisabled.value
    || savingRuleItems.value
    || loadingRuleItems.value
    || Boolean(ruleItemsError.value),
  );
  const extraControlsDisabled = computed(() =>
    workloadWriteBusy.value
    || loadingTeacherOptions.value
    || loadingExtras.value
    || Boolean(teacherOptionsError.value)
    || Boolean(extrasError.value)
    || !selectedSemesterId.value,
  );
  const overviewCards = computed<StatusCard[]>(() => [
    {
      label: "课表批次",
      value: batchesError.value ? "加载失败" : timetableBatches.value.length,
      help: batchesError.value ? "课表批次暂时不可用，请重试当前区块。" : "当前学期可用的课表导入批次数量。",
      tone: batchesError.value ? "tone-red" : "tone-blue",
    },
    {
      label: "规则项",
      value: ruleItemsError.value ? "加载失败" : ruleItems.value.length,
      help: ruleItemsError.value ? "规则项暂时不可用，请重试当前区块。" : "当前规则版本下的有效规则项数量。",
      tone: ruleItemsError.value ? "tone-red" : "tone-amber",
    },
    {
      label: "附加项",
      value: extrasError.value ? "加载失败" : extras.value.length,
      help: extrasError.value ? "附加项暂时不可用，请重试当前区块。" : "当前学期已补录的附加量化项数量。",
      tone: extrasError.value ? "tone-red" : "tone-slate",
    },
  ]);

  const workloadLoadErrorItems = computed<WorkloadLoadErrorItem[]>(() => {
    const items: WorkloadLoadErrorItem[] = [
      {
        key: "reference",
        label: "基础选项",
        message: referenceError.value,
        loading: loadingReference.value,
      },
      {
        key: "teachers",
        label: "教师候选",
        message: teacherOptionsError.value,
        loading: loadingTeacherOptions.value,
      },
      {
        key: "ruleVersions",
        label: "规则版本",
        message: ruleVersionsError.value,
        loading: loadingRuleVersions.value,
      },
      {
        key: "ruleItems",
        label: "规则项",
        message: ruleItemsError.value,
        loading: loadingRuleItems.value,
      },
      {
        key: "batches",
        label: "课表批次",
        message: batchesError.value,
        loading: loadingBatches.value,
      },
      {
        key: "entries",
        label: "课表条目",
        message: entriesError.value,
        loading: loadingEntries.value,
      },
      {
        key: "extras",
        label: "附加项",
        message: extrasError.value,
        loading: loadingExtras.value,
      },
      {
        key: "results",
        label: "工作量结果",
        message: resultsError.value,
        loading: loadingResults.value,
      },
    ];
    return items.filter((item) => item.message);
  });

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

  function clearWorkloadActionError(): void {
    workloadActionError.value = "";
  }

  function setWorkloadActionError(action: string, error: unknown, nextStep: string): void {
    const message = formatUserActionError(action, error, nextStep);
    workloadActionError.value = message;
    ElMessage.error(message);
  }

  function setWorkloadActionWarning(message: string): void {
    workloadActionError.value = message;
    ElMessage.warning(message);
  }

  async function loadReferenceOptions(): Promise<void> {
    try {
      loadingReference.value = true;
      referenceError.value = "";
      await referenceStore.loadAll();
      const currentSemester = semesterOptions.value.find((item) => item.is_current) ?? semesterOptions.value[0];
      if (!selectedSemesterId.value || !semesterOptions.value.some((item) => item.id === selectedSemesterId.value)) {
        selectedSemesterId.value = currentSemester?.id ?? null;
      }
    } catch (error) {
      referenceError.value = buildLoadError("加载基础选项", error);
    } finally {
      loadingReference.value = false;
    }
  }

  async function loadTeachers(): Promise<void> {
    try {
      loadingTeacherOptions.value = true;
      teacherOptionsError.value = "";
      const payload = await apiRequest<{ items: TeacherOption[] }>("/api/teachers?page=1&page_size=200");
      teacherOptions.value = payload.items;
    } catch (error) {
      teacherOptionsError.value = buildLoadError("加载教师候选", error);
      teacherOptions.value = [];
    } finally {
      loadingTeacherOptions.value = false;
    }
  }

  async function loadRuleVersions(): Promise<void> {
    try {
      loadingRuleVersions.value = true;
      ruleVersionsError.value = "";
      const payload = await apiRequest<RuleVersionItem[]>("/api/workload/rules");
      ruleVersions.value = payload;
      if (!payload.length) {
        selectedRuleVersionId.value = null;
        return;
      }
      const exists = payload.some((item) => item.id === selectedRuleVersionId.value);
      if (exists) return;
      selectedRuleVersionId.value = payload.find((item) => item.is_default)?.id ?? payload[0].id;
    } catch (error) {
      ruleVersionsError.value = buildLoadError("加载规则版本", error);
      ruleVersions.value = [];
      selectedRuleVersionId.value = null;
      ruleItems.value = [];
      results.value = [];
    } finally {
      loadingRuleVersions.value = false;
    }
  }

  async function loadRuleItems(): Promise<void> {
    if (!selectedRuleVersionId.value) {
      ruleItems.value = [];
      ruleItemsError.value = "";
      return;
    }
    try {
      loadingRuleItems.value = true;
      ruleItemsError.value = "";
      ruleItems.value = await apiRequest<RuleItem[]>(`/api/workload/rules/${selectedRuleVersionId.value}/items`);
    } catch (error) {
      ruleItemsError.value = buildLoadError("加载规则项", error);
      ruleItems.value = [];
    } finally {
      loadingRuleItems.value = false;
    }
  }

  async function loadBatches(): Promise<void> {
    if (!selectedSemesterId.value) {
      timetableBatches.value = [];
      selectedBatchId.value = null;
      batchesError.value = "";
      return;
    }
    try {
      loadingBatches.value = true;
      batchesError.value = "";
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
    } catch (error) {
      batchesError.value = buildLoadError("加载课表批次", error);
      timetableBatches.value = [];
      selectedBatchId.value = null;
      timetableEntries.value = [];
    } finally {
      loadingBatches.value = false;
    }
  }

  async function loadEntries(): Promise<void> {
    if (!selectedBatchId.value) {
      timetableEntries.value = [];
      entriesError.value = "";
      return;
    }
    try {
      loadingEntries.value = true;
      entriesError.value = "";
      timetableEntries.value = await apiRequest<TimetableEntryItem[]>(
        `/api/timetable/batches/${selectedBatchId.value}/entries?unresolved_only=${unresolvedOnly.value}`,
      );
    } catch (error) {
      entriesError.value = buildLoadError("加载课表条目", error);
      timetableEntries.value = [];
    } finally {
      loadingEntries.value = false;
    }
  }

  async function loadExtras(): Promise<void> {
    if (!selectedSemesterId.value) {
      extras.value = [];
      extrasError.value = "";
      return;
    }
    try {
      loadingExtras.value = true;
      extrasError.value = "";
      extras.value = await apiRequest<ExtraItem[]>(`/api/workload/extras?semester_id=${selectedSemesterId.value}`);
    } catch (error) {
      extrasError.value = buildLoadError("加载附加项", error);
      extras.value = [];
    } finally {
      loadingExtras.value = false;
    }
  }

  async function loadResults(): Promise<void> {
    if (!selectedSemesterId.value || !selectedRuleVersionId.value) {
      results.value = [];
      resultsError.value = "";
      return;
    }
    try {
      loadingResults.value = true;
      resultsError.value = "";
      results.value = await apiRequest<WorkloadResultItem[]>(
        `/api/workload/results?semester_id=${selectedSemesterId.value}&rule_version_id=${selectedRuleVersionId.value}`,
      );
    } catch (error) {
      resultsError.value = buildLoadError("加载工作量结果", error);
      results.value = [];
      activeResult.value = null;
      resultDrawerVisible.value = false;
    } finally {
      loadingResults.value = false;
    }
  }

  async function refreshAll(): Promise<void> {
    clearWorkloadActionError();
    await loadReferenceOptions();
    await Promise.all([loadTeachers(), loadRuleVersions()]);
    await Promise.all([loadBatches(), loadExtras(), loadResults()]);
    await Promise.all([loadRuleItems(), loadEntries()]);
  }

  function handleTimetableFileChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    selectedTimetableFile.value = input.files?.[0] ?? null;
  }

  async function importTimetable(): Promise<void> {
    if (!selectedSemesterId.value || !selectedTimetableFile.value) {
      setWorkloadActionWarning("请先选择学期和课表文件。");
      return;
    }
    try {
      clearWorkloadActionError();
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
      setWorkloadActionError("导入课表", error, "请下载最新课表模板，确认学期、表头和教师/班级/学科信息后重新导入。");
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
    if (!entryForm.value.id) {
      setWorkloadActionWarning("当前课表条目无效，请重新选择条目后再修正。");
      return;
    }
    try {
      clearWorkloadActionError();
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
      setWorkloadActionError("保存课表条目修正", error, "请确认教师、班级、学科和课程类型仍在基础数据中，再重新保存。");
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
    if (!selectedRuleVersionId.value) {
      setWorkloadActionWarning("请先选择规则版本。");
      return;
    }
    try {
      clearWorkloadActionError();
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
      setWorkloadActionError("保存工作量规则项", error, "请确认每条规则都有维度和匹配值，系数或固定量填写有效后再保存。");
    } finally {
      savingRuleItems.value = false;
    }
  }

  async function createRuleVersion(): Promise<void> {
    if (!newRuleForm.value.name.trim()) {
      setWorkloadActionWarning("请填写规则名称。");
      return;
    }
    try {
      clearWorkloadActionError();
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
      setWorkloadActionError("创建工作量规则版本", error, "请确认规则名称未重复，适用学期和状态填写有效后重试。");
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
      setWorkloadActionWarning("请先选择学期。");
      return;
    }
    if (!extraForm.value.teacher_id || !extraForm.value.item_name.trim()) {
      setWorkloadActionWarning("请填写教师和项目名称。");
      return;
    }
    try {
      clearWorkloadActionError();
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
      setWorkloadActionError("新增工作量附加项", error, "请确认教师、数量、系数或固定量填写有效后重试。");
    } finally {
      savingExtra.value = false;
    }
  }

  async function calculateWorkload(): Promise<void> {
    if (!selectedSemesterId.value || !selectedRuleVersionId.value) {
      setWorkloadActionWarning("请先选择学期和规则版本。");
      return;
    }
    try {
      const blockingMessages = workloadPrecheckMessages.value.filter((item) =>
        item.includes("请选择") || item.includes("没有规则项"),
      );
      if (blockingMessages.length) {
        setWorkloadActionWarning(blockingMessages.join("；"));
        return;
      }
      clearWorkloadActionError();
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
      setWorkloadActionError("计算教师工作量", error, "请确认课表批次、规则项和附加项数据完整，再重新计算。");
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
    await loadEntries();
  });

  watch(unresolvedOnly, async () => {
    await loadEntries();
  });

  watch(selectedSemesterId, async () => {
    await Promise.all([loadBatches(), loadExtras(), loadResults()]);
  });

  watch(selectedRuleVersionId, async () => {
    await Promise.all([loadRuleItems(), loadResults()]);
  });

  onMounted(async () => {
    await refreshAll();
  });

  async function retryWorkloadLoadItem(key: WorkloadLoadKey): Promise<void> {
    if (key === "reference") {
      await loadReferenceOptions();
      return;
    }
    if (key === "teachers") {
      await loadTeachers();
      return;
    }
    if (key === "ruleVersions") {
      await loadRuleVersions();
      await Promise.all([loadRuleItems(), loadResults()]);
      return;
    }
    if (key === "ruleItems") {
      await loadRuleItems();
      return;
    }
    if (key === "batches") {
      await loadBatches();
      await loadEntries();
      return;
    }
    if (key === "entries") {
      await loadEntries();
      return;
    }
    if (key === "extras") {
      await loadExtras();
      return;
    }
    await loadResults();
  }

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
    loadingReference,
    loadingTeacherOptions,
    loadingRuleVersions,
    loadingRuleItems,
    loadingBatches,
    loadingEntries,
    loadingExtras,
    loadingResults,
    workloadActionError,
    workloadWriteBusy,
    workloadRefreshBusy,
    workloadSelectionDisabled,
    calculateDisabled,
    exportResultsDisabled,
    timetableImportDisabled,
    timetablePanelActionsDisabled,
    ruleActionsDisabled,
    ruleItemControlsDisabled,
    extraControlsDisabled,
    referenceError,
    teacherOptionsError,
    ruleVersionsError,
    ruleItemsError,
    batchesError,
    entriesError,
    extrasError,
    resultsError,
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
    workloadLoadErrorItems,
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
    retryWorkloadLoadItem,
    clearWorkloadActionError,
  };
}
