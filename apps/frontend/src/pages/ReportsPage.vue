<template>
  <AppPage
    title="输出中心"
    eyebrow="输出中心 / 报表工作流"
    description="按业务域选择交付物，生成前先看用途、必要参数、数据来源、导出格式和风险标签。"
    :meta="reportsPageMeta"
  >
    <template #actions>
        <el-button :loading="optionsLoading" @click="loadOptions">刷新选项</el-button>
        <el-button type="primary" plain :loading="recordsLoading" @click="loadExportRecords">刷新记录</el-button>
    </template>

    <el-alert
      v-if="pageLoadError"
      class="page-alert"
      type="error"
      show-icon
      :closable="false"
      :title="pageLoadError"
    />

    <section class="overview-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">导出流</div>
        <h3>{{ currentReportTypeLabel }}</h3>
        <p>先确定报表类型，再补齐考试、学生、教师、学期或推荐方案等依赖参数，最后统一从导出记录回看结果。</p>
      </article>
      <article v-for="item in overviewCards" :key="item.label" class="soft-card overview-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head compact">
        <div>
          <h3>报表参数</h3>
          <p>不同报表类型会动态暴露所需参数，避免在一个大表单里混杂无关字段。</p>
        </div>
      </div>
      <div class="filter-grid">
        <el-select v-model="form.report_type" placeholder="报表类型">
          <el-option
            v-for="item in reportTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-select v-if="requiresExam" v-model="form.exam_id" filterable placeholder="考试">
          <el-option
            v-for="exam in examOptions"
            :key="exam.id"
            :label="exam.name"
            :value="exam.id"
          />
        </el-select>
        <el-select v-if="requiresStudent" v-model="form.student_id" filterable placeholder="学生">
          <el-option
            v-for="student in studentOptions"
            :key="student.id"
            :label="`${student.student_no} - ${student.name}`"
            :value="student.id"
          />
        </el-select>
        <el-select v-if="requiresScheme" v-model="form.scheme_id" filterable placeholder="推荐方案">
          <el-option
            v-for="item in recommendationOptions"
            :key="item.scheme_id"
            :label="`${item.student_name} / ${item.scheme_name}`"
            :value="item.scheme_id"
          />
        </el-select>
        <el-select v-if="requiresDraft" v-model="form.draft_id" filterable placeholder="志愿草稿">
          <el-option
            v-for="item in volunteerDraftOptions"
            :key="item.id"
            :label="`${item.student_name ?? '-'} / ${item.name}`"
            :value="item.id"
          />
        </el-select>
        <el-select v-if="requiresBatch" v-model="form.batch_id" filterable placeholder="评教批次">
          <el-option
            v-for="item in evaluationBatchOptions"
            :key="item.id"
            :label="`${item.template_name ?? '-'} / ${item.semester_name ?? '-'}`"
            :value="item.id"
          />
        </el-select>
        <el-select v-if="requiresClass" v-model="form.class_id" filterable placeholder="班级">
          <el-option
            v-for="item in referenceStore.classes"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select v-if="requiresGrade" v-model="form.grade_id" filterable placeholder="年级">
          <el-option
            v-for="item in referenceStore.grades"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select v-if="requiresTeacher" v-model="form.teacher_id" filterable placeholder="教师">
          <el-option
            v-for="teacher in teacherOptions"
            :key="teacher.id"
            :label="teacher.name"
            :value="teacher.id"
          />
        </el-select>
        <el-select v-if="requiresSemester" v-model="form.semester_id" filterable placeholder="学期">
          <el-option
            v-for="semester in referenceStore.semesters"
            :key="semester.id"
            :label="semesterLabel(semester)"
            :value="semester.id"
          />
        </el-select>
        <el-select v-if="optionalRuleVersion" v-model="form.rule_version_id" clearable filterable placeholder="规则版本，可选">
          <el-option
            v-for="rule in currentRuleOptions"
            :key="rule.id"
            :label="rule.name"
            :value="rule.id"
          />
        </el-select>
        <el-date-picker
          v-if="usesStartDate"
          v-model="form.start_date"
          value-format="YYYY-MM-DD"
          placeholder="开始日期，可选"
        />
        <el-date-picker
          v-if="usesEndDate"
          v-model="form.end_date"
          value-format="YYYY-MM-DD"
          placeholder="结束日期，可选"
        />
      </div>
      <div class="action-row toolbar-row">
        <el-button type="primary" :loading="exporting" @click="exportReport">生成报表</el-button>
        <el-button
          v-if="supportsPrintPreview"
          :disabled="Boolean(missingRequiredFields.length) || !printPreviewPath"
          @click="openPrintPreview"
        >
          打印预览
        </el-button>
        <el-button @click="loadExportRecords">刷新记录</el-button>
      </div>
      <el-alert
        v-if="missingRequiredFields.length"
        class="report-alert"
        type="warning"
        show-icon
        :closable="false"
        :title="`当前报表还缺少：${missingRequiredFields.join('、')}`"
      />
      <el-alert
        v-for="item in scoreReportGuardMessages"
        :key="item"
        class="report-alert"
        type="warning"
        show-icon
        :closable="false"
        :title="item"
      />
      <ReportInsightPanel
        v-if="showReportInsightSection"
        :description="reportInsightDescription"
        :loading="reportInsightLoading"
        :error="reportInsightError"
        :loaded="reportInsightLoaded"
        :cards="reportInsightCards"
        :groups="reportInsightGroups"
        @retry="reloadReportInsights"
      />
    </section>

    <section class="soft-card panel-block">
      <div class="section-head compact">
        <div>
          <h3>输出目录</h3>
          <p>按业务域查看每种报表适合什么场景，生成前先确认参数、来源和风险。</p>
        </div>
      </div>
      <div class="report-domain-stack">
        <article v-for="group in groupedReportCatalog" :key="group.key" class="report-domain">
          <div class="report-domain-head">
            <div>
              <strong>{{ group.label }}</strong>
              <p>{{ group.description }}</p>
            </div>
            <el-tag effect="light">{{ group.items.length }} 项</el-tag>
          </div>
          <div class="report-card-grid">
            <button
              v-for="item in group.items"
              :key="item.value"
              class="report-catalog-card"
              :class="{ selected: item.value === form.report_type }"
              type="button"
              @click="form.report_type = item.value"
            >
              <span>{{ item.label }}</span>
              <strong>{{ item.purpose }}</strong>
              <small>必要参数：{{ item.requiredParams.length ? item.requiredParams.join("、") : "无" }}</small>
              <small>数据来源：{{ item.dataSources.join("、") }}</small>
              <small>格式：{{ item.formats.join("、") }}</small>
              <div class="risk-tag-row">
                <el-tag v-for="risk in item.riskTags" :key="risk" size="small" type="warning" effect="light">
                  {{ risk }}
                </el-tag>
              </div>
            </button>
          </div>
        </article>
      </div>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>导出记录</h3>
          <p>记录报表类型、参数、导出时间和下载入口，方便复现。</p>
        </div>
      </div>
      <div class="table-shell">
        <el-table :data="exportRecords" stripe v-loading="recordsLoading">
          <el-table-column label="报表名称" prop="report_name" min-width="180" />
          <el-table-column label="类型" min-width="140">
            <template #default="{ row }">
              {{ formatReportType(row.report_type) }}
            </template>
          </el-table-column>
          <el-table-column label="导出参数" min-width="260">
            <template #default="{ row }">
              {{ formatParams(row.params_json) }}
            </template>
          </el-table-column>
          <el-table-column label="导出时间" prop="exported_at" min-width="170" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="exportStatusType(row.status)" effect="light">
                {{ formatExportStatus(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openFile(row.download_url)">下载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty
        v-if="!recordsLoading && !exportRecords.length"
        description="暂无导出记录。请先在上方选择报表类型并补齐参数，再点击“生成报表”。"
      />
    </section>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest, openFile } from "../api/client";
import ReportInsightPanel from "../components/reports/ReportInsightPanel.vue";
import { AppPage } from "../components/ui";
import {
  createEmptyReportInsightDataState,
  fetchReportInsightData,
} from "../components/reports/reportInsightLoader";
import {
  buildReportInsightCards,
  buildReportInsightGroups,
  getReportInsightDescription,
  shouldShowReportInsightSection,
} from "../components/reports/reportInsightPresenter";
import {
  resolveRecommendationReportInsightContext,
} from "../components/reports/reportInsights";
import {
  buildReportExportPayload,
  formatReportExportParams,
  getGroupedReportCatalog,
  getMissingRequiredReportFields,
  getMissingRequiredReportFieldsMessage,
  getReportPrintPreviewPath,
  getReportRuleOptionScope,
  getReportTypeLabel,
  REPORT_TYPE_OPTIONS,
  reportTypeUsesField,
} from "../components/reports/reportTypeConfig";
import {
  type OptionItem,
  useReferenceStore,
} from "../stores/reference";
import { formatUserActionError } from "../utils/userFeedback";
import { buildScoreReportGuardMessages } from "../utils/scoreReadiness";

interface ExamOption {
  id: number;
  name: string;
}

interface StudentOption {
  id: number;
  student_no: string;
  name: string;
}

interface TeacherOption {
  id: number;
  name: string;
}

interface RuleVersion {
  id: number;
  name: string;
}

interface RecommendationOption {
  scheme_id: number;
  scheme_name: string;
  student_id: number;
  student_name: string;
  province: string;
  target_year?: number | null;
  score_input_label?: string | null;
  score_confidence?: string | null;
  reference_exam_name?: string | null;
  use_historical_mapping?: boolean;
  generated_at: string;
}

interface EvaluationBatchOption {
  id: number;
  template_name?: string | null;
  semester_name?: string | null;
}

interface VolunteerDraftOption {
  id: number;
  name: string;
  student_id: number;
  student_name?: string | null;
  exam_id: number;
  exam_name?: string | null;
  batch?: string | null;
  exam_mode?: string | null;
  item_count: number;
}

interface ExportRecord {
  id: number;
  report_type: string;
  report_name: string;
  params_json?: Record<string, unknown> | null;
  exported_at: string;
  status: string;
  download_url: string;
}

const referenceStore = useReferenceStore();
const route = useRoute();
const examOptions = ref<ExamOption[]>([]);
const studentOptions = ref<StudentOption[]>([]);
const teacherOptions = ref<TeacherOption[]>([]);
const ruleVersions = ref<RuleVersion[]>([]);
const adviserRuleVersions = ref<RuleVersion[]>([]);
const recommendationOptions = ref<RecommendationOption[]>([]);
const volunteerDraftOptions = ref<VolunteerDraftOption[]>([]);
const evaluationBatchOptions = ref<EvaluationBatchOption[]>([]);
const exportRecords = ref<ExportRecord[]>([]);
const reportInsightData = ref(createEmptyReportInsightDataState());
const reportInsightLoading = ref(false);
const reportInsightLoaded = ref(false);
const reportInsightError = ref("");
const exporting = ref(false);
const optionsLoading = ref(false);
const recordsLoading = ref(false);
const pageLoadError = ref("");
const scoreRecordTotal = ref(0);
const reportTypeOptions = REPORT_TYPE_OPTIONS;
const groupedReportCatalog = getGroupedReportCatalog();

const form = reactive({
  report_type: "student_analysis",
  exam_id: undefined as number | undefined,
  student_id: undefined as number | undefined,
  scheme_id: undefined as number | undefined,
  draft_id: undefined as number | undefined,
  batch_id: undefined as number | undefined,
  class_id: undefined as number | undefined,
  grade_id: undefined as number | undefined,
  teacher_id: undefined as number | undefined,
  semester_id: undefined as number | undefined,
  rule_version_id: undefined as number | undefined,
  start_date: undefined as string | undefined,
  end_date: undefined as string | undefined,
});

const requiresExam = computed(() => reportTypeUsesField(form.report_type, "exam_id"));
const requiresStudent = computed(() => reportTypeUsesField(form.report_type, "student_id"));
const requiresClass = computed(() => reportTypeUsesField(form.report_type, "class_id"));
const requiresGrade = computed(() => reportTypeUsesField(form.report_type, "grade_id"));
const requiresTeacher = computed(() => reportTypeUsesField(form.report_type, "teacher_id"));
const requiresSemester = computed(() => reportTypeUsesField(form.report_type, "semester_id"));
const optionalRuleVersion = computed(() => reportTypeUsesField(form.report_type, "rule_version_id"));
const usesStartDate = computed(() => reportTypeUsesField(form.report_type, "start_date"));
const usesEndDate = computed(() => reportTypeUsesField(form.report_type, "end_date"));
const requiresScheme = computed(() => reportTypeUsesField(form.report_type, "scheme_id"));
const requiresDraft = computed(() => reportTypeUsesField(form.report_type, "draft_id"));
const requiresBatch = computed(() => reportTypeUsesField(form.report_type, "batch_id"));
const currentRuleOptions = computed(() =>
  getReportRuleOptionScope(form.report_type) === "adviser" ? adviserRuleVersions.value : ruleVersions.value,
);
const printPreviewPath = computed(() => getReportPrintPreviewPath(form));
const supportsPrintPreview = computed(() => Boolean(printPreviewPath.value));
const currentReportTypeLabel = computed(() => getReportTypeLabel(form.report_type));
const reportsPageMeta = computed(() => [
  { label: "报表类型", value: reportTypeOptions.length },
  { label: "当前类型", value: currentReportTypeLabel.value },
  { label: "导出记录", value: exportRecords.value.length },
  { label: "推荐方案", value: recommendationOptions.value.length },
  { label: "志愿草稿", value: volunteerDraftOptions.value.length },
]);
const missingRequiredFields = computed(() => getMissingRequiredReportFields(form));
const missingRequiredFieldsMessage = computed(() => getMissingRequiredReportFieldsMessage(form));
const scoreReportGuardMessages = computed(() =>
  buildScoreReportGuardMessages(form.report_type, {
    examCount: examOptions.value.length,
    scoreRecordTotal: scoreRecordTotal.value,
  }),
);
const overviewCards = computed(() => [
  {
    label: "考试依赖",
    value: requiresExam.value ? "需要" : "可选",
    help: "当前报表是否要求先选择考试。",
    tone: "tone-blue",
  },
  {
    label: "规则版本",
    value: currentRuleOptions.value.length,
    help: "工作量和班主任量化报表可选的规则版本数。",
    tone: "tone-amber",
  },
  {
    label: "最近导出",
    value: exportRecords.value[0] ? formatExportStatus(exportRecords.value[0].status) : "暂无",
    help: "最近一次导出记录的状态。",
    tone: "tone-slate",
  },
]);
const currentRecommendationOption = computed(
  () => recommendationOptions.value.find((item) => item.scheme_id === form.scheme_id) ?? null,
);
const currentRecommendationInsightContext = computed(() =>
  resolveRecommendationReportInsightContext(recommendationOptions.value, currentRecommendationOption.value),
);
const reportInsightCards = computed(() =>
  buildReportInsightCards(
    form.report_type,
    reportInsightData.value,
    currentRecommendationInsightContext.value.currentOption,
    currentRecommendationInsightContext.value.compareOption,
  ),
);
const reportInsightGroups = computed(() =>
  buildReportInsightGroups(form.report_type, reportInsightCards.value),
);
const reportInsightDescription = computed(() => getReportInsightDescription(form.report_type));
const showReportInsightSection = computed(
  () =>
    shouldShowReportInsightSection({
      loading: reportInsightLoading.value,
      error: reportInsightError.value,
      loaded: reportInsightLoaded.value,
      cards: reportInsightCards.value,
    }),
);

function semesterLabel(item: OptionItem): string {
  return item.academic_year_name ? `${item.academic_year_name} ${item.name}` : item.name;
}

function formatReportType(reportType: string): string {
  return getReportTypeLabel(reportType);
}

function formatExportStatus(status: string): string {
  const mapping: Record<string, string> = {
    success: "成功",
    processing: "处理中",
    failed: "失败",
  };
  return mapping[status] ?? status;
}

function exportStatusType(status: string): "success" | "info" | "danger" {
  if (status === "success") return "success";
  if (status === "failed") return "danger";
  return "info";
}

function formatParams(value?: Record<string, unknown> | null): string {
  return formatReportExportParams(value);
}

async function loadOptions(): Promise<void> {
  optionsLoading.value = true;
  pageLoadError.value = "";
  try {
    await referenceStore.loadCore();
    const [examPayload, studentPayload, teacherPayload, rulePayload, adviserRulePayload, draftPayload] = await Promise.all([
      apiRequest<{ items: ExamOption[] }>("/api/exams?page=1&page_size=100"),
      apiRequest<{ items: StudentOption[] }>("/api/students?page=1&page_size=200"),
      apiRequest<{ items: TeacherOption[] }>("/api/teachers?page=1&page_size=200"),
      apiRequest<RuleVersion[]>("/api/workload/rules"),
      apiRequest<RuleVersion[]>("/api/adviser-quant/rules"),
      apiRequest<VolunteerDraftOption[]>("/api/recommendations/volunteer-drafts"),
    ]);
    recommendationOptions.value = await apiRequest<RecommendationOption[]>("/api/recommendations/history");
    evaluationBatchOptions.value = await apiRequest<EvaluationBatchOption[]>("/api/evaluation/batches");
    try {
      const dashboardPayload = await apiRequest<{ score_record_total?: number }>("/api/dashboard/summary");
      scoreRecordTotal.value = dashboardPayload.score_record_total ?? 0;
    } catch {
      scoreRecordTotal.value = 0;
    }
    volunteerDraftOptions.value = draftPayload;
    examOptions.value = examPayload.items;
    studentOptions.value = studentPayload.items;
    teacherOptions.value = teacherPayload.items;
    ruleVersions.value = rulePayload;
    adviserRuleVersions.value = adviserRulePayload;
  } catch (error) {
    pageLoadError.value = formatUserActionError("刷新报表选项", error, "确认考试、学生、教师或推荐数据接口可用后重试。");
    ElMessage.error(pageLoadError.value);
  } finally {
    optionsLoading.value = false;
  }
}

async function loadExportRecords(): Promise<void> {
  recordsLoading.value = true;
  pageLoadError.value = "";
  try {
    exportRecords.value = await apiRequest<ExportRecord[]>("/api/reports/exports");
  } catch (error) {
    pageLoadError.value = formatUserActionError("刷新导出记录", error, "确认本地服务已启动后重试；不影响你重新生成报表。");
    ElMessage.error(pageLoadError.value);
  } finally {
    recordsLoading.value = false;
  }
}

async function loadReportInsights(): Promise<void> {
  reportInsightError.value = "";
  reportInsightLoaded.value = false;
  reportInsightData.value = createEmptyReportInsightDataState();
  if (missingRequiredFields.value.length) {
    reportInsightLoading.value = false;
    return;
  }
  reportInsightLoading.value = true;
  try {
    reportInsightData.value = await fetchReportInsightData(form, apiRequest, {
      recommendationCompareSchemeId: currentRecommendationInsightContext.value.compareScheme?.scheme_id,
    });
    reportInsightLoaded.value = true;
  } finally {
    reportInsightLoading.value = false;
  }
}

async function reloadReportInsights(): Promise<void> {
  try {
    await loadReportInsights();
  } catch (error) {
    reportInsightError.value = formatUserActionError("加载导出前摘要", error, "先确认所选参数正确，再点击重试摘要加载。");
    reportInsightLoading.value = false;
    reportInsightLoaded.value = true;
  }
}

async function exportReport(): Promise<void> {
  try {
    if (missingRequiredFields.value.length) {
      ElMessage.warning(missingRequiredFieldsMessage.value);
      return;
    }
    if (scoreReportGuardMessages.value.length) {
      ElMessage.warning(scoreReportGuardMessages.value[0]);
      return;
    }
    exporting.value = true;
    const payload = buildReportExportPayload(form);
    const result = await apiRequest<ExportRecord>("/api/reports/export", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await loadExportRecords();
    openFile(result.download_url);
    ElMessage.success("报表已生成");
  } catch (error) {
    ElMessage.error(formatUserActionError("生成报表", error, "先确认报表参数完整；如果仍失败，请回到对应业务页复核源数据。"));
  } finally {
    exporting.value = false;
  }
}

function openPrintPreview(): void {
  if (!printPreviewPath.value) {
    ElMessage.warning(missingRequiredFieldsMessage.value);
    return;
  }
  openFile(printPreviewPath.value);
}

watch(
  () => form.scheme_id,
  (schemeId) => {
    if (!schemeId) return;
    const current = recommendationOptions.value.find((item) => item.scheme_id === schemeId);
    if (current && form.report_type === "recommendation_summary") {
      form.student_id = current.student_id;
    }
  },
);

watch(
  () =>
    [
      form.report_type,
      form.scheme_id,
      form.draft_id,
      form.student_id,
      form.exam_id,
      form.class_id,
      form.grade_id,
      form.teacher_id,
      form.semester_id,
      form.rule_version_id,
      form.batch_id,
      form.start_date,
      form.end_date,
      currentRecommendationInsightContext.value.compareScheme?.scheme_id,
    ] as const,
  async () => {
    try {
      await loadReportInsights();
    } catch (error) {
      reportInsightError.value = formatUserActionError("加载导出前摘要", error, "先确认所选参数正确，再点击重试摘要加载。");
      reportInsightLoading.value = false;
      reportInsightLoaded.value = true;
      reportInsightData.value = createEmptyReportInsightDataState();
    }
  },
  { immediate: true },
);

onMounted(async () => {
  try {
    applyRoutePrefill();
    await loadOptions();
    await loadExportRecords();
  } catch (error) {
    ElMessage.error(formatUserActionError("加载报表中心", error, "确认本地服务已启动后，分别点击“刷新选项”和“刷新记录”。"));
  }
});

function applyRoutePrefill(): void {
  const reportType = typeof route.query.report_type === "string" ? route.query.report_type : "";
  if (reportType) form.report_type = reportType;
  for (const field of ["exam_id", "student_id", "scheme_id", "draft_id", "batch_id", "class_id", "grade_id", "teacher_id", "semester_id", "rule_version_id"] as const) {
    const value = route.query[field];
    if (typeof value === "string" && value) {
      form[field] = Number(value);
    }
  }
  if (typeof route.query.start_date === "string") form.start_date = route.query.start_date;
  if (typeof route.query.end_date === "string") form.end_date = route.query.end_date;
}
</script>

<style scoped>
.page-alert {
  margin-top: -4px;
}

.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) repeat(3, minmax(0, 0.75fr));
  gap: 16px;
}

.overview-panel,
.overview-card {
  padding: 24px;
}

.overview-panel {
  background:
    radial-gradient(circle at top left, rgba(180, 219, 243, 0.32), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(244, 248, 252, 0.94));
}

.overview-kicker {
  display: inline-flex;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f6c98;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.overview-panel h3 {
  margin: 14px 0 0;
  color: #1f3448;
  font-size: 28px;
  line-height: 1.25;
}

.overview-panel p {
  margin: 12px 0 0;
  color: #62788c;
  line-height: 1.7;
}

.overview-card {
  display: grid;
  align-content: end;
  gap: 10px;
}

.overview-card span {
  color: #6d8194;
  font-size: 13px;
}

.overview-card strong {
  color: #1f3245;
  font-size: 30px;
  font-weight: 760;
}

.overview-card p {
  margin: 0;
  color: #73879b;
  line-height: 1.55;
  font-size: 13px;
}

.tone-blue {
  box-shadow: inset 0 4px 0 rgba(31, 108, 152, 0.78);
}

.tone-amber {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.84);
}

.tone-slate {
  box-shadow: inset 0 4px 0 rgba(92, 111, 129, 0.74);
}

.toolbar-row {
  margin-top: 14px;
}

.report-alert {
  margin-top: 14px;
}

.report-domain-stack {
  display: grid;
  gap: 16px;
}

.report-domain {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid #e2ebf3;
  border-radius: 8px;
  background: #fbfdff;
}

.report-domain-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.report-domain-head strong {
  color: #1f3448;
  font-size: 16px;
}

.report-domain-head p {
  margin: 4px 0 0;
  color: #60748a;
  line-height: 1.55;
}

.report-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}

.report-catalog-card {
  display: grid;
  gap: 8px;
  min-height: 184px;
  padding: 14px;
  border: 1px solid #dce7f1;
  border-radius: 8px;
  background: #fff;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.report-catalog-card.selected {
  border-color: #1f6c98;
  box-shadow: inset 0 4px 0 rgba(31, 108, 152, 0.78);
}

.report-catalog-card span {
  color: #1f6c98;
  font-weight: 740;
}

.report-catalog-card strong {
  color: #27394a;
  line-height: 1.5;
}

.report-catalog-card small {
  color: #667b8f;
  line-height: 1.5;
}

.risk-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.section-head {
  margin-bottom: 16px;
}

.section-head h3 {
  margin: 0;
  font-size: 18px;
}

.section-head p {
  margin: 6px 0 0;
  color: #60748a;
  line-height: 1.6;
}

@media (max-width: 1180px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
