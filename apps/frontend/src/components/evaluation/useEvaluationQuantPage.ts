import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import type { UploadFile } from "element-plus";

import { apiRequest, openFile, uploadFile } from "../../api/client";
import { useReferenceStore } from "../../stores/reference";
import { formatUserActionError } from "../../utils/userFeedback";
import { formatEvaluationBatchStatus, semesterLabel } from "./helpers";
import type {
  EvaluationBatch,
  EvaluationBatchCompare,
  EvaluationImportFormState,
  EvaluationImportResponse,
  EvaluationOverview,
  EvaluationQuestion,
  EvaluationTeacherDetail,
  EvaluationTeacherTrend,
  EvaluationTemplate,
  QuantFiltersState,
  QuantFormState,
  QuantRecord,
  QuantSummary,
  RuleItem,
  RuleVersion,
  RuleVersionFormState,
  TeacherOption,
  TemplateFormState,
  UploadedAttachment,
} from "./types";

type EvaluationLoadKey =
  | "reference"
  | "teachers"
  | "templates"
  | "batches"
  | "overview"
  | "teacherDetail"
  | "comparison"
  | "rules"
  | "ruleItems"
  | "quant";

function currentMonthValue(): string {
  return new Date().toISOString().slice(0, 7);
}

export function useEvaluationQuantPage() {
  const referenceStore = useReferenceStore();
  const activeTab = ref("evaluation");

  const templates = ref<EvaluationTemplate[]>([]);
  const teacherOptions = ref<TeacherOption[]>([]);
  const batches = ref<EvaluationBatch[]>([]);
  const evaluationOverview = ref<EvaluationOverview | null>(null);
  const evaluationComparison = ref<EvaluationBatchCompare | null>(null);
  const evaluationDetail = ref<EvaluationTeacherDetail | null>(null);
  const evaluationTeacherTrend = ref<EvaluationTeacherTrend | null>(null);
  const evaluationImportResult = ref<EvaluationImportResponse | null>(null);

  const ruleVersions = ref<RuleVersion[]>([]);
  const ruleItemRows = ref<RuleItem[]>([]);
  const quantRecords = ref<QuantRecord[]>([]);
  const quantSummary = ref<QuantSummary[]>([]);

  const selectedRuleVersionId = ref<number | null>(null);
  const selectedBatchId = ref<number | null>(null);
  const selectedCompareBatchId = ref<number | null>(null);
  const selectedTeacherId = ref<number | null>(null);

  const templateDialogVisible = ref(false);
  const ruleVersionDialogVisible = ref(false);
  const quantDialogVisible = ref(false);

  const editingTemplateId = ref<number | null>(null);
  const editingRuleVersionId = ref<number | null>(null);
  const editingQuantRecordId = ref<number | null>(null);

  const savingTemplate = ref(false);
  const savingRuleVersion = ref(false);
  const savingRuleItems = ref(false);
  const savingQuant = ref(false);
  const uploadingQuantAttachments = ref(false);
  const importingEvaluation = ref(false);

  const loadingReference = ref(false);
  const loadingTeacherOptions = ref(false);
  const loadingTemplates = ref(false);
  const loadingBatches = ref(false);
  const loadingEvaluationOverview = ref(false);
  const loadingEvaluationComparison = ref(false);
  const loadingTeacherDetail = ref(false);
  const loadingRuleVersions = ref(false);
  const loadingRuleItems = ref(false);
  const loadingQuantData = ref(false);

  const referenceError = ref("");
  const teacherOptionsError = ref("");
  const templatesError = ref("");
  const batchesError = ref("");
  const evaluationOverviewError = ref("");
  const evaluationComparisonError = ref("");
  const teacherDetailError = ref("");
  const ruleVersionsError = ref("");
  const ruleItemsError = ref("");
  const quantDataError = ref("");
  const evaluationActionError = ref("");

  const evaluationImportForm = reactive<EvaluationImportFormState>({
    template_id: undefined,
    semester_id: undefined,
  });

  const quantFilters = reactive<QuantFiltersState>({
    semester_id: undefined,
    teacher_id: undefined,
    rule_version_id: undefined,
  });

  const templateForm = reactive<TemplateFormState>({
    name: "",
    target_type: "teacher",
  });

  const templateQuestions = ref<EvaluationQuestion[]>([]);

  const ruleVersionForm = reactive<RuleVersionFormState>({
    name: "",
    semester_id: undefined,
    is_default: false,
    status: "active",
    note: "",
    is_active: true,
  });

  const quantForm = reactive<QuantFormState>({
    teacher_id: undefined,
    class_id: undefined,
    semester_id: undefined,
    rule_item_id: undefined,
    record_month: "",
    score: undefined,
    description: "",
    attachments: [],
  });

  const templateDialogTitle = computed(() => (editingTemplateId.value ? "编辑评教模板" : "新增评教模板"));
  const ruleVersionDialogTitle = computed(() => (editingRuleVersionId.value ? "编辑规则版本" : "新增规则版本"));
  const quantDialogTitle = computed(() => (editingQuantRecordId.value ? "编辑量化记录" : "新增量化记录"));

  const quantRuleItemOptions = computed(() => ruleItemRows.value.filter((item) => item.id));
  const selectedBatchMeta = computed(() => batches.value.find((item) => item.id === selectedBatchId.value) ?? null);
  const selectedRuleVersionMeta = computed(
    () => ruleVersions.value.find((item) => item.id === selectedRuleVersionId.value) ?? null,
  );
  const currentSemesterLabel = computed(() => {
    const semesterId = evaluationImportForm.semester_id ?? quantFilters.semester_id;
    if (!semesterId) return "未选择";
    const semester = referenceStore.semesters.find((item) => item.id === semesterId);
    return semester ? semesterLabel(semester) : "未选择";
  });
  const currentBatchLabel = computed(() => selectedBatchMeta.value?.template_name ?? "未选择");
  const currentRuleVersionLabel = computed(() => selectedRuleVersionMeta.value?.name ?? "未选择");
  const guideCards = computed(() => [
    {
      label: "1. 评教模板",
      value: templates.value.length ? `${templates.value.length} 个模板` : "未配置",
      help: templates.value.length ? "模板就绪后再导入评教原始数据。" : "建议先创建评教模板。",
      tone: templates.value.length ? "tone-blue" : "tone-slate",
    },
    {
      label: "2. 当前批次",
      value: selectedBatchMeta.value ? formatEvaluationBatchStatus(selectedBatchMeta.value.status) : "未选择",
      help: selectedBatchMeta.value ? "可继续查看教师详情、批次对比和历史趋势。" : "请先导入或选择一个评教批次。",
      tone: selectedBatchMeta.value ? "tone-green" : "tone-slate",
    },
    {
      label: "3. 量化规则",
      value: selectedRuleVersionMeta.value ? currentRuleVersionLabel.value : "未选择",
      help: selectedRuleVersionMeta.value ? "新增记录前请确认当前规则版本。" : "请先选择一个量化规则版本。",
      tone: selectedRuleVersionMeta.value ? "tone-blue" : "tone-slate",
    },
    {
      label: "4. 量化记录",
      value: quantRecords.value.length ? `${quantRecords.value.length} 条` : "暂无",
      help: quantRecords.value.length ? "可按学期、教师和规则版本继续筛选。" : "可从当前规则版本开始新增量化记录。",
      tone: quantRecords.value.length ? "tone-amber" : "tone-slate",
    },
  ]);
  const compareBatchOptions = computed(() => {
    const currentBatch = selectedBatchMeta.value;
    return batches.value.filter(
      (item) => item.id !== selectedBatchId.value && (!currentBatch || item.template_id === currentBatch.template_id),
    );
  });
  const evaluationLoadErrorItems = computed(() => [
    {
      key: "reference" as const,
      label: "基础选项",
      message: referenceError.value,
      loading: loadingReference.value,
    },
    {
      key: "teachers" as const,
      label: "教师候选",
      message: teacherOptionsError.value,
      loading: loadingTeacherOptions.value,
    },
    {
      key: "templates" as const,
      label: "评教模板",
      message: templatesError.value,
      loading: loadingTemplates.value,
    },
    {
      key: "batches" as const,
      label: "评教批次",
      message: batchesError.value,
      loading: loadingBatches.value,
    },
    {
      key: "overview" as const,
      label: "批次总览",
      message: evaluationOverviewError.value,
      loading: loadingEvaluationOverview.value,
    },
    {
      key: "teacherDetail" as const,
      label: "教师评教详情",
      message: teacherDetailError.value,
      loading: loadingTeacherDetail.value,
    },
    {
      key: "comparison" as const,
      label: "批次对比",
      message: evaluationComparisonError.value,
      loading: loadingEvaluationComparison.value,
    },
    {
      key: "rules" as const,
      label: "量化规则版本",
      message: ruleVersionsError.value,
      loading: loadingRuleVersions.value,
    },
    {
      key: "ruleItems" as const,
      label: "量化规则项",
      message: ruleItemsError.value,
      loading: loadingRuleItems.value,
    },
    {
      key: "quant" as const,
      label: "量化记录与汇总",
      message: quantDataError.value,
      loading: loadingQuantData.value,
    },
  ].filter((item) => item.message));

  const evaluationWriteBusy = computed(() =>
    savingTemplate.value
    || savingRuleVersion.value
    || savingRuleItems.value
    || savingQuant.value
    || uploadingQuantAttachments.value
    || importingEvaluation.value,
  );
  const evaluationRefreshBusy = computed(() =>
    loadingReference.value
    || loadingTeacherOptions.value
    || loadingTemplates.value
    || loadingBatches.value
    || loadingEvaluationOverview.value
    || loadingEvaluationComparison.value
    || loadingTeacherDetail.value
    || loadingRuleVersions.value
    || loadingRuleItems.value
    || loadingQuantData.value,
  );
  const topActionsDisabled = computed(() => evaluationWriteBusy.value);
  const templateActionsDisabled = computed(() =>
    evaluationWriteBusy.value
    || loadingTemplates.value,
  );
  const evaluationImportDisabled = computed(() =>
    !evaluationImportForm.template_id
    || !evaluationImportForm.semester_id
    || evaluationWriteBusy.value
    || loadingReference.value
    || loadingTemplates.value
    || Boolean(referenceError.value)
    || Boolean(templatesError.value),
  );
  const batchActionsDisabled = computed(() =>
    evaluationWriteBusy.value
    || loadingBatches.value
    || loadingEvaluationOverview.value,
  );
  const evaluationOverviewControlsDisabled = computed(() =>
    evaluationWriteBusy.value
    || loadingEvaluationOverview.value
    || loadingEvaluationComparison.value
    || loadingTeacherDetail.value,
  );
  const ruleActionsDisabled = computed(() =>
    importingEvaluation.value
    || savingTemplate.value
    || savingRuleVersion.value
    || savingRuleItems.value
    || savingQuant.value
    || uploadingQuantAttachments.value
    || loadingRuleVersions.value,
  );
  const ruleItemControlsDisabled = computed(() =>
    ruleActionsDisabled.value
    || savingRuleItems.value
    || loadingRuleItems.value
    || Boolean(ruleItemsError.value)
    || !selectedRuleVersionId.value,
  );
  const quantControlsDisabled = computed(() =>
    evaluationWriteBusy.value
    || loadingQuantData.value
    || loadingReference.value
    || loadingTeacherOptions.value,
  );
  const createQuantRecordDisabled = computed(() =>
    quantControlsDisabled.value
    || loadingRuleItems.value
    || !selectedRuleVersionId.value
    || !quantRuleItemOptions.value.length
    || Boolean(teacherOptionsError.value)
    || Boolean(ruleItemsError.value),
  );
  const quantRowActionsDisabled = computed(() =>
    evaluationWriteBusy.value
    || loadingQuantData.value
    || Boolean(quantDataError.value),
  );

  const trendDeltaScore = computed(() => {
    const points = evaluationTeacherTrend.value?.points ?? [];
    if (points.length < 2) return null;
    return Number((points[points.length - 1].overall_avg_score - points[points.length - 2].overall_avg_score).toFixed(2));
  });

  const trendRankDelta = computed(() => {
    const points = evaluationTeacherTrend.value?.points ?? [];
    if (points.length < 2) return null;
    const currentRank = points[points.length - 1].rank;
    const previousRank = points[points.length - 2].rank;
    if (!currentRank || !previousRank) return null;
    return previousRank - currentRank;
  });

  const trendPeakScore = computed(() => {
    const points = evaluationTeacherTrend.value?.points ?? [];
    if (!points.length) return "-";
    return Math.max(...points.map((item) => item.overall_avg_score)).toFixed(2);
  });

  function buildTemplateWeightJson(): Record<string, number> | null {
    const bucket: Record<string, number> = {};
    for (const row of templateQuestions.value) {
      if (!row.dimension_name) continue;
      bucket[row.dimension_name] = Number(((bucket[row.dimension_name] ?? 0) + (row.weight ?? 0)).toFixed(2));
    }
    return Object.keys(bucket).length ? bucket : null;
  }

  function clearEvaluationActionError(): void {
    evaluationActionError.value = "";
  }

  function setEvaluationActionError(action: string, error: unknown, nextStep: string): void {
    const message = formatUserActionError(action, error, nextStep);
    evaluationActionError.value = message;
    ElMessage.error(message);
  }

  function setEvaluationActionWarning(message: string): void {
    evaluationActionError.value = message;
    ElMessage.warning(message);
  }

  function downloadEvaluationTemplate(): void {
    openFile(`/api/system/files?path=${encodeURIComponent("data/templates/evaluation_import_template.xlsx")}`);
  }

  function downloadQuantTemplate(): void {
    openFile(`/api/system/files?path=${encodeURIComponent("data/templates/adviser_quant_import_template.xlsx")}`);
  }

  function addTemplateQuestionRow(): void {
    templateQuestions.value.push({
      dimension_name: "",
      question_text: "",
      score_max: 5,
      weight: 1,
      sort_order: templateQuestions.value.length + 1,
      is_active: true,
    });
  }

  function removeTemplateQuestionRow(index: number): void {
    templateQuestions.value.splice(index, 1);
  }

  function resetTemplateForm(): void {
    editingTemplateId.value = null;
    templateForm.name = "";
    templateForm.target_type = "teacher";
    templateQuestions.value = [
      {
        dimension_name: "教学设计",
        question_text: "教学目标清晰，重难点明确",
        score_max: 5,
        weight: 1,
        sort_order: 1,
        is_active: true,
      },
    ];
  }

  function openCreateTemplate(): void {
    resetTemplateForm();
    templateDialogVisible.value = true;
  }

  function openEditTemplate(item: EvaluationTemplate): void {
    editingTemplateId.value = item.id;
    templateForm.name = item.name;
    templateForm.target_type = item.target_type;
    templateQuestions.value = item.questions.map((question) => ({ ...question }));
    templateDialogVisible.value = true;
  }

  async function saveTemplate(): Promise<void> {
    if (!templateForm.name.trim()) {
      setEvaluationActionWarning("模板名称不能为空");
      return;
    }
    if (
      !templateQuestions.value.length
      || templateQuestions.value.some((item) => !item.dimension_name.trim() || !item.question_text.trim())
    ) {
      setEvaluationActionWarning("请至少保留一条完整题目，且维度与题目不能为空");
      return;
    }
    try {
      clearEvaluationActionError();
      savingTemplate.value = true;
      const payload = {
        name: templateForm.name,
        target_type: templateForm.target_type,
        is_active: true,
        weight_json: buildTemplateWeightJson(),
        questions: templateQuestions.value.map((item) => ({
          dimension_name: item.dimension_name,
          question_text: item.question_text,
          score_max: item.score_max,
          weight: item.weight,
          sort_order: item.sort_order,
          is_active: true,
        })),
      };
      const path = editingTemplateId.value
        ? `/api/evaluation/templates/${editingTemplateId.value}`
        : "/api/evaluation/templates";
      const method = editingTemplateId.value ? "PUT" : "POST";
      await apiRequest(path, { method, body: JSON.stringify(payload) });
      templateDialogVisible.value = false;
      await loadTemplates();
      ElMessage.success("评教模板已保存");
    } catch (error) {
      setEvaluationActionError("保存评教模板", error, "请确认模板名称、对象类型、题目维度和分值填写完整后重新保存。");
    } finally {
      savingTemplate.value = false;
    }
  }

  async function loadTemplates(): Promise<void> {
    try {
      loadingTemplates.value = true;
      templatesError.value = "";
      templates.value = await apiRequest<EvaluationTemplate[]>("/api/evaluation/templates");
      if (!evaluationImportForm.template_id && templates.value.length) {
        evaluationImportForm.template_id = templates.value[0].id;
      }
    } catch (error) {
      templatesError.value = formatUserActionError("加载评教模板", error, "确认本地服务已启动，再刷新评教模板。");
      if (!templates.value.length) evaluationImportForm.template_id = undefined;
    } finally {
      loadingTemplates.value = false;
    }
  }

  async function loadBatches(): Promise<void> {
    try {
      loadingBatches.value = true;
      batchesError.value = "";
      const query = new URLSearchParams();
      if (evaluationImportForm.semester_id) query.set("semester_id", String(evaluationImportForm.semester_id));
      batches.value = await apiRequest<EvaluationBatch[]>(`/api/evaluation/batches?${query.toString()}`);
    } catch (error) {
      batchesError.value = formatUserActionError("加载评教批次", error, "确认学期筛选有效，再刷新评教批次。");
      batches.value = [];
      selectedBatchId.value = null;
      selectedCompareBatchId.value = null;
      selectedTeacherId.value = null;
      evaluationOverview.value = null;
      evaluationComparison.value = null;
      evaluationDetail.value = null;
      evaluationTeacherTrend.value = null;
    } finally {
      loadingBatches.value = false;
    }
  }

  async function handleEvaluationImport(file: UploadFile): Promise<void> {
    if (!file.raw || !evaluationImportForm.template_id || !evaluationImportForm.semester_id) {
      setEvaluationActionWarning("请先选择模板和学期");
      return;
    }
    try {
      clearEvaluationActionError();
      importingEvaluation.value = true;
      evaluationImportResult.value = await uploadFile<EvaluationImportResponse>("/api/evaluation/import", file.raw, {
        template_id: String(evaluationImportForm.template_id),
        semester_id: String(evaluationImportForm.semester_id),
      });
      await loadBatches();
      await selectBatch(evaluationImportResult.value.batch_id);
      ElMessage.success(evaluationImportResult.value.message);
    } catch (error) {
      setEvaluationActionError("导入评教数据", error, "请下载最新评教模板，确认表头、教师姓名、模板和学期匹配后重新导入。");
    } finally {
      importingEvaluation.value = false;
    }
  }

  async function selectBatch(batchId: number): Promise<void> {
    try {
      loadingEvaluationOverview.value = true;
      evaluationOverviewError.value = "";
      selectedBatchId.value = batchId;
      selectedCompareBatchId.value = null;
      selectedTeacherId.value = null;
      evaluationComparison.value = null;
      evaluationOverview.value = await apiRequest<EvaluationOverview>(`/api/evaluation/batches/${batchId}/overview`);
      const firstTeacher = evaluationOverview.value.teacher_summaries[0];
      if (firstTeacher) {
        await loadTeacherDetail(firstTeacher.teacher_id);
      } else {
        evaluationDetail.value = null;
        evaluationTeacherTrend.value = null;
      }
      const defaultCompareBatch = compareBatchOptions.value[0];
      if (defaultCompareBatch) {
        await loadEvaluationComparison(defaultCompareBatch.id);
      }
    } catch (error) {
      evaluationOverviewError.value = formatUserActionError("加载评教批次总览", error, "先刷新批次列表，再重新选择评教批次。");
      evaluationOverview.value = null;
      evaluationDetail.value = null;
      evaluationTeacherTrend.value = null;
      evaluationComparison.value = null;
    } finally {
      loadingEvaluationOverview.value = false;
    }
  }

  async function loadTeacherDetail(teacherId: number): Promise<void> {
    if (!selectedBatchId.value) return;
    try {
      loadingTeacherDetail.value = true;
      teacherDetailError.value = "";
      selectedTeacherId.value = teacherId;
      const templateId = selectedBatchMeta.value?.template_id;
      const [detail, trend] = await Promise.all([
        apiRequest<EvaluationTeacherDetail>(`/api/evaluation/batches/${selectedBatchId.value}/teachers/${teacherId}`),
        apiRequest<EvaluationTeacherTrend>(
          `/api/evaluation/teachers/${teacherId}/trend${templateId ? `?template_id=${templateId}` : ""}`,
        ),
      ]);
      evaluationDetail.value = detail;
      evaluationTeacherTrend.value = trend;
    } catch (error) {
      teacherDetailError.value = formatUserActionError("加载教师评教详情", error, "先确认当前批次仍存在，再重新查看该教师。");
      evaluationDetail.value = null;
      evaluationTeacherTrend.value = null;
    } finally {
      loadingTeacherDetail.value = false;
    }
  }

  async function loadEvaluationComparison(compareBatchId: number | null): Promise<void> {
    selectedCompareBatchId.value = compareBatchId;
    if (!selectedBatchId.value || !compareBatchId) {
      evaluationComparison.value = null;
      evaluationComparisonError.value = "";
      return;
    }
    try {
      loadingEvaluationComparison.value = true;
      evaluationComparisonError.value = "";
      evaluationComparison.value = await apiRequest<EvaluationBatchCompare>(
        `/api/evaluation/batches/${selectedBatchId.value}/compare?compare_batch_id=${compareBatchId}`,
      );
    } catch (error) {
      evaluationComparisonError.value = formatUserActionError("加载评教批次对比", error, "请选择同模板的历史批次后重试。");
      evaluationComparison.value = null;
    } finally {
      loadingEvaluationComparison.value = false;
    }
  }

  async function handleCompareBatchChange(value: number | string | undefined | null): Promise<void> {
    await loadEvaluationComparison(value ? Number(value) : null);
  }

  function resetRuleVersionForm(): void {
    editingRuleVersionId.value = null;
    ruleVersionForm.name = "";
    ruleVersionForm.semester_id = quantFilters.semester_id ?? evaluationImportForm.semester_id;
    ruleVersionForm.is_default = false;
    ruleVersionForm.status = "active";
    ruleVersionForm.note = "";
    ruleVersionForm.is_active = true;
  }

  function openCreateRuleVersion(): void {
    resetRuleVersionForm();
    ruleVersionDialogVisible.value = true;
  }

  async function saveRuleVersion(): Promise<void> {
    if (!ruleVersionForm.name.trim()) {
      setEvaluationActionWarning("规则版本名称不能为空");
      return;
    }
    try {
      clearEvaluationActionError();
      savingRuleVersion.value = true;
      const path = editingRuleVersionId.value
        ? `/api/adviser-quant/rules/${editingRuleVersionId.value}`
        : "/api/adviser-quant/rules";
      const method = editingRuleVersionId.value ? "PUT" : "POST";
      const result = await apiRequest<RuleVersion>(path, {
        method,
        body: JSON.stringify(ruleVersionForm),
      });
      ruleVersionDialogVisible.value = false;
      await loadRuleVersions();
      await selectRuleVersion(result.id);
      ElMessage.success("规则版本已保存");
    } catch (error) {
      setEvaluationActionError("保存量化规则版本", error, "请确认版本名称未重复，学期、默认版本和状态填写有效后重新保存。");
    } finally {
      savingRuleVersion.value = false;
    }
  }

  async function loadRuleVersions(): Promise<void> {
    try {
      loadingRuleVersions.value = true;
      ruleVersionsError.value = "";
      ruleVersions.value = await apiRequest<RuleVersion[]>("/api/adviser-quant/rules");
      if (!selectedRuleVersionId.value && ruleVersions.value.length) {
        await selectRuleVersion(ruleVersions.value[0].id);
      }
      if (!quantFilters.rule_version_id) {
        const defaultRule = ruleVersions.value.find((item) => item.is_default) ?? ruleVersions.value[0];
        quantFilters.rule_version_id = defaultRule?.id;
      }
    } catch (error) {
      ruleVersionsError.value = formatUserActionError("加载量化规则版本", error, "确认本地服务已启动，再刷新规则版本。");
      if (!ruleVersions.value.length) {
        selectedRuleVersionId.value = null;
        quantFilters.rule_version_id = undefined;
        ruleItemRows.value = [];
      }
    } finally {
      loadingRuleVersions.value = false;
    }
  }

  async function selectRuleVersion(ruleVersionId: number): Promise<void> {
    try {
      loadingRuleItems.value = true;
      ruleItemsError.value = "";
      selectedRuleVersionId.value = ruleVersionId;
      ruleItemRows.value = await apiRequest<RuleItem[]>(`/api/adviser-quant/rules/${ruleVersionId}/items`);
    } catch (error) {
      ruleItemsError.value = formatUserActionError("加载量化规则项", error, "先刷新规则版本，再重新选择当前规则。");
      ruleItemRows.value = [];
    } finally {
      loadingRuleItems.value = false;
    }
  }

  function addRuleItemRow(): void {
    ruleItemRows.value.push({
      item_name: "",
      item_type: "",
      default_score: 0,
      requires_attachment: false,
      sort_order: ruleItemRows.value.length + 1,
      is_active: true,
    });
  }

  function removeRuleItemRow(index: number): void {
    ruleItemRows.value.splice(index, 1);
  }

  async function saveRuleItems(): Promise<void> {
    if (!selectedRuleVersionId.value) {
      setEvaluationActionWarning("请先选择一个规则版本");
      return;
    }
    if (!ruleItemRows.value.length) {
      setEvaluationActionWarning("请至少保留一条规则项");
      return;
    }
    if (ruleItemRows.value.some((item) => !item.item_name.trim() || !item.item_type.trim())) {
      setEvaluationActionWarning("规则项名称和类型不能为空");
      return;
    }
    try {
      clearEvaluationActionError();
      savingRuleItems.value = true;
      ruleItemRows.value = await apiRequest<RuleItem[]>(`/api/adviser-quant/rules/${selectedRuleVersionId.value}/items`, {
        method: "POST",
        body: JSON.stringify(
          ruleItemRows.value.map((item) => ({
            item_name: item.item_name,
            item_type: item.item_type,
            default_score: item.default_score,
            requires_attachment: item.requires_attachment,
            note: item.note,
            sort_order: item.sort_order,
            is_active: true,
          })),
        ),
      });
      ElMessage.success("规则项已保存");
    } catch (error) {
      setEvaluationActionError("保存量化规则项", error, "请确认规则项名称、类型、分值和排序填写有效后重新保存。");
    } finally {
      savingRuleItems.value = false;
    }
  }

  function resetQuantForm(): void {
    editingQuantRecordId.value = null;
    quantForm.teacher_id = undefined;
    quantForm.class_id = undefined;
    quantForm.semester_id = quantFilters.semester_id ?? evaluationImportForm.semester_id;
    quantForm.rule_item_id = undefined;
    quantForm.record_month = currentMonthValue();
    quantForm.score = undefined;
    quantForm.description = "";
    quantForm.attachments = [];
  }

  function openCreateQuantRecord(): void {
    if (!selectedRuleVersionId.value) {
      setEvaluationActionWarning("请先选择一个规则版本");
      return;
    }
    if (!quantRuleItemOptions.value.length) {
      setEvaluationActionWarning("请先为当前规则版本配置规则项");
      return;
    }
    resetQuantForm();
    quantDialogVisible.value = true;
  }

  function openEditQuantRecord(item: QuantRecord): void {
    editingQuantRecordId.value = item.id;
    quantForm.teacher_id = item.teacher_id;
    quantForm.class_id = item.class_id ?? undefined;
    quantForm.semester_id = item.semester_id;
    quantForm.rule_item_id = item.rule_item_id;
    quantForm.record_month = item.record_month;
    quantForm.score = item.score;
    quantForm.description = item.description ?? "";
    quantForm.attachments = item.attachments.map((attachment) => attachment.file);
    quantDialogVisible.value = true;
  }

  function handleTemplateDialogClosed(): void {
    resetTemplateForm();
  }

  function handleRuleVersionDialogClosed(): void {
    resetRuleVersionForm();
  }

  function handleQuantDialogClosed(): void {
    resetQuantForm();
  }

  async function handleQuantAttachmentUpload(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const files = Array.from(input.files ?? []);
    if (!files.length) return;
    try {
      clearEvaluationActionError();
      uploadingQuantAttachments.value = true;
      const uploaded = await Promise.all(
        files.map((file) => uploadFile<UploadedAttachment>("/api/files/upload", file, { category: "adviser_quant" })),
      );
      quantForm.attachments.push(...uploaded);
      ElMessage.success(`已上传 ${uploaded.length} 个附件`);
      if (input) input.value = "";
    } catch (error) {
      setEvaluationActionError("上传量化附件", error, "请确认文件可读取且本地服务可访问后重新上传附件。");
    } finally {
      uploadingQuantAttachments.value = false;
    }
  }

  function removeQuantAttachment(fileId: number): void {
    quantForm.attachments = quantForm.attachments.filter((item) => item.id !== fileId);
  }

  async function saveQuantRecord(): Promise<void> {
    if (!quantForm.teacher_id || !quantForm.semester_id || !quantForm.rule_item_id || !quantForm.record_month) {
      setEvaluationActionWarning("教师、学期、量化项和月份不能为空");
      return;
    }
    if (quantForm.score === undefined || quantForm.score === null) {
      setEvaluationActionWarning("请填写量化分值");
      return;
    }
    if (uploadingQuantAttachments.value) {
      setEvaluationActionWarning("附件仍在上传，请等待上传完成后再保存记录");
      return;
    }
    try {
      clearEvaluationActionError();
      savingQuant.value = true;
      const path = editingQuantRecordId.value
        ? `/api/adviser-quant/records/${editingQuantRecordId.value}`
        : "/api/adviser-quant/records";
      const method = editingQuantRecordId.value ? "PUT" : "POST";
      await apiRequest(path, {
        method,
        body: JSON.stringify({
          teacher_id: quantForm.teacher_id,
          class_id: quantForm.class_id,
          semester_id: quantForm.semester_id,
          rule_item_id: quantForm.rule_item_id,
          record_month: quantForm.record_month,
          score: quantForm.score,
          description: quantForm.description || undefined,
          attachment_file_ids: quantForm.attachments.map((item) => item.id),
          is_active: true,
        }),
      });
      quantDialogVisible.value = false;
      await reloadQuantData();
      ElMessage.success("量化记录已保存");
    } catch (error) {
      setEvaluationActionError("保存量化记录", error, "请确认教师、学期、量化项、月份、分值和附件信息有效后重新保存。");
    } finally {
      savingQuant.value = false;
    }
  }

  async function loadQuantRecords(): Promise<void> {
    const query = new URLSearchParams();
    if (quantFilters.semester_id) query.set("semester_id", String(quantFilters.semester_id));
    if (quantFilters.teacher_id) query.set("teacher_id", String(quantFilters.teacher_id));
    quantRecords.value = await apiRequest<QuantRecord[]>(`/api/adviser-quant/records?${query.toString()}`);
    if (quantFilters.rule_version_id) {
      quantRecords.value = quantRecords.value.filter((item) => item.rule_version_id === quantFilters.rule_version_id);
    }
  }

  async function loadQuantSummary(): Promise<void> {
    if (!quantFilters.semester_id) {
      quantSummary.value = [];
      return;
    }
    const query = new URLSearchParams({ semester_id: String(quantFilters.semester_id) });
    if (quantFilters.teacher_id) query.set("teacher_id", String(quantFilters.teacher_id));
    if (quantFilters.rule_version_id) query.set("rule_version_id", String(quantFilters.rule_version_id));
    quantSummary.value = await apiRequest<QuantSummary[]>(`/api/adviser-quant/summary?${query.toString()}`);
  }

  async function reloadQuantData(): Promise<void> {
    try {
      loadingQuantData.value = true;
      quantDataError.value = "";
      await Promise.all([loadQuantRecords(), loadQuantSummary()]);
    } catch (error) {
      quantDataError.value = formatUserActionError("加载量化记录与汇总", error, "确认学期、教师和规则版本筛选有效，再重新查询。");
      quantRecords.value = [];
      quantSummary.value = [];
    } finally {
      loadingQuantData.value = false;
    }
  }

  function resetQuantFilters(): void {
    quantFilters.teacher_id = undefined;
    quantFilters.rule_version_id = ruleVersions.value.find((item) => item.is_default)?.id ?? ruleVersions.value[0]?.id;
    quantFilters.semester_id = evaluationImportForm.semester_id;
    void reloadQuantData();
  }

  async function loadTeacherOptions(): Promise<void> {
    try {
      loadingTeacherOptions.value = true;
      teacherOptionsError.value = "";
      const payload = await apiRequest<{ items: TeacherOption[] }>("/api/teachers?page=1&page_size=200");
      teacherOptions.value = payload.items;
    } catch (error) {
      teacherOptionsError.value = formatUserActionError("加载教师候选", error, "确认教师中心可访问，再刷新教师候选。");
      teacherOptions.value = [];
    } finally {
      loadingTeacherOptions.value = false;
    }
  }

  async function loadReferenceOptions(): Promise<void> {
    try {
      loadingReference.value = true;
      referenceError.value = "";
      await referenceStore.loadCore();
    } catch (error) {
      referenceError.value = formatUserActionError("加载基础选项", error, "确认基础数据接口可用，再重新加载基础选项。");
    } finally {
      loadingReference.value = false;
    }
  }

  async function retryEvaluationLoadItem(key: EvaluationLoadKey): Promise<void> {
    if (key === "reference") {
      await loadReferenceOptions();
      return;
    }
    if (key === "teachers") {
      await loadTeacherOptions();
      return;
    }
    if (key === "templates") {
      await loadTemplates();
      return;
    }
    if (key === "batches") {
      await loadBatches();
      return;
    }
    if (key === "overview") {
      if (selectedBatchId.value) await selectBatch(selectedBatchId.value);
      return;
    }
    if (key === "teacherDetail") {
      if (selectedTeacherId.value) await loadTeacherDetail(selectedTeacherId.value);
      return;
    }
    if (key === "comparison") {
      await loadEvaluationComparison(selectedCompareBatchId.value);
      return;
    }
    if (key === "rules") {
      await loadRuleVersions();
      return;
    }
    if (key === "ruleItems") {
      if (selectedRuleVersionId.value) await selectRuleVersion(selectedRuleVersionId.value);
      return;
    }
    await reloadQuantData();
  }

  onMounted(async () => {
    await loadReferenceOptions();
    const currentSemester = referenceStore.semesters.find((item) => item.is_current) ?? referenceStore.semesters[0];
    evaluationImportForm.semester_id = currentSemester?.id;
    quantFilters.semester_id = currentSemester?.id;
    await Promise.all([loadTeacherOptions(), loadTemplates(), loadRuleVersions()]);
    await Promise.all([loadBatches(), reloadQuantData()]);
    if (batches.value.length) {
      await selectBatch(batches.value[0].id);
    }
  });

  return {
    referenceStore,
    activeTab,
    templates,
    teacherOptions,
    batches,
    evaluationOverview,
    evaluationComparison,
    evaluationDetail,
    evaluationTeacherTrend,
    evaluationImportResult,
    ruleVersions,
    ruleItemRows,
    quantRecords,
    quantSummary,
    selectedRuleVersionId,
    selectedBatchId,
    selectedCompareBatchId,
    templateDialogVisible,
    ruleVersionDialogVisible,
    quantDialogVisible,
    savingTemplate,
    savingRuleVersion,
    savingRuleItems,
    savingQuant,
    uploadingQuantAttachments,
    importingEvaluation,
    evaluationActionError,
    evaluationWriteBusy,
    evaluationRefreshBusy,
    topActionsDisabled,
    templateActionsDisabled,
    evaluationImportDisabled,
    batchActionsDisabled,
    evaluationOverviewControlsDisabled,
    ruleActionsDisabled,
    ruleItemControlsDisabled,
    quantControlsDisabled,
    createQuantRecordDisabled,
    quantRowActionsDisabled,
    loadingReference,
    loadingTeacherOptions,
    loadingTemplates,
    loadingBatches,
    loadingEvaluationOverview,
    loadingEvaluationComparison,
    loadingTeacherDetail,
    loadingRuleVersions,
    loadingRuleItems,
    loadingQuantData,
    referenceError,
    teacherOptionsError,
    templatesError,
    batchesError,
    evaluationOverviewError,
    evaluationComparisonError,
    teacherDetailError,
    ruleVersionsError,
    ruleItemsError,
    quantDataError,
    evaluationImportForm,
    quantFilters,
    templateForm,
    templateQuestions,
    ruleVersionForm,
    quantForm,
    templateDialogTitle,
    ruleVersionDialogTitle,
    quantDialogTitle,
    quantRuleItemOptions,
    selectedRuleVersionMeta,
    currentSemesterLabel,
    currentBatchLabel,
    currentRuleVersionLabel,
    guideCards,
    evaluationLoadErrorItems,
    compareBatchOptions,
    trendDeltaScore,
    trendRankDelta,
    trendPeakScore,
    downloadEvaluationTemplate,
    downloadQuantTemplate,
    loadTemplates,
    loadBatches,
    handleEvaluationImport,
    selectBatch,
    openCreateTemplate,
    openEditTemplate,
    handleCompareBatchChange,
    loadTeacherDetail,
    loadRuleVersions,
    openCreateRuleVersion,
    selectRuleVersion,
    addRuleItemRow,
    saveRuleItems,
    removeRuleItemRow,
    reloadQuantData,
    openCreateQuantRecord,
    resetQuantFilters,
    retryEvaluationLoadItem,
    clearEvaluationActionError,
    openEditQuantRecord,
    handleTemplateDialogClosed,
    handleRuleVersionDialogClosed,
    handleQuantDialogClosed,
    addTemplateQuestionRow,
    removeTemplateQuestionRow,
    saveTemplate,
    saveRuleVersion,
    handleQuantAttachmentUpload,
    removeQuantAttachment,
    saveQuantRecord,
  };
}
