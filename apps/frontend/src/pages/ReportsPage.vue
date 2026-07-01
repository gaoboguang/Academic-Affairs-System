<template>
  <AppPage
    title="报表中心"
    eyebrow="决策输出 / 报表中心"
    description="选择要交付的报表，补齐必要参数后生成 Excel 或打开打印预览。"
    :meta="reportsPageMeta"
  >
    <template #actions>
      <el-button :loading="optionsLoading" @click="loadOptions(true)">刷新选项</el-button>
      <el-button type="primary" plain :loading="recordsLoading" @click="loadExportRecords(true)">刷新记录</el-button>
    </template>

    <el-alert
      v-if="loadErrorItems.length"
      class="page-alert"
      type="error"
      show-icon
      :closable="false"
      title="报表中心部分数据加载失败"
    >
      <template #default>
        <ul class="load-error-list">
          <li v-for="item in loadErrorItems" :key="item.label">
            <strong>{{ item.label }}</strong>
            <span>{{ item.message }}</span>
          </li>
        </ul>
        <div class="action-row toolbar-row">
          <el-button v-if="optionsLoadError" size="small" type="danger" plain :loading="optionsLoading" @click="loadOptions(true)">
            重新加载选项
          </el-button>
          <el-button v-if="recordsLoadError" size="small" type="danger" plain :loading="recordsLoading" @click="loadExportRecords(true)">
            重新加载记录
          </el-button>
        </div>
      </template>
    </el-alert>

    <section class="report-workspace">
      <aside class="soft-card report-picker" aria-label="报表类型选择">
        <div class="section-head compact">
          <div>
            <h3>选择报表</h3>
            <p>先按使用场景缩小范围，再点选具体报表。</p>
          </div>
        </div>

        <div class="domain-tabs" role="tablist" aria-label="报表场景">
          <button
            v-for="group in groupedReportCatalog"
            :key="group.key"
            class="domain-tab"
            :class="{ active: group.key === selectedCatalogDomain }"
            :disabled="formInteractionDisabled"
            type="button"
            @click="selectedCatalogDomain = group.key"
          >
            {{ group.label }}
          </button>
        </div>

        <div class="active-domain-copy" v-if="activeDomainGroup">
          <strong>{{ activeDomainGroup.label }}</strong>
          <p>{{ activeDomainGroup.description }}</p>
        </div>

        <div class="report-list">
          <button
            v-for="item in activeDomainReports"
            :key="item.value"
            class="report-list-item"
            :class="{ selected: item.value === form.report_type }"
            :disabled="formInteractionDisabled"
            type="button"
            @click="selectReportType(item.value)"
          >
            <div>
              <strong>{{ item.label }}</strong>
              <span>{{ item.purpose }}</span>
            </div>
            <small>{{ item.requiredParams.length ? item.requiredParams.join("、") : "无需参数" }}</small>
          </button>
        </div>
      </aside>

      <section class="soft-card panel-block report-form-panel">
        <div class="section-head compact">
          <div>
            <h3>报表参数</h3>
            <p>只显示当前报表需要的条件。</p>
          </div>
        </div>
        <el-alert
          v-if="optionsLoadError"
          class="report-alert"
          type="error"
          show-icon
          :closable="false"
          :title="optionsLoadError"
        >
          <template #default>
            <el-button size="small" type="danger" plain :loading="optionsLoading" @click="loadOptions(true)">
              重新加载报表选项
            </el-button>
          </template>
        </el-alert>

        <div v-if="currentReportCatalogItem" class="current-report-strip">
          <div>
            <span>当前报表</span>
            <strong>{{ currentReportCatalogItem.label }}</strong>
            <p>{{ currentReportCatalogItem.purpose }}</p>
          </div>
          <dl>
            <div>
              <dt>必要参数</dt>
              <dd>{{ currentReportCatalogItem.requiredParams.length ? currentReportCatalogItem.requiredParams.join("、") : "无" }}</dd>
            </div>
            <div>
              <dt>数据来源</dt>
              <dd>{{ currentReportCatalogItem.dataSources.join("、") }}</dd>
            </div>
            <div>
              <dt>格式</dt>
              <dd>{{ currentReportCatalogItem.formats.join("、") }}</dd>
            </div>
          </dl>
          <div class="risk-tag-row">
            <el-tag v-for="risk in currentReportCatalogItem.riskTags" :key="risk" size="small" type="warning" effect="light">
              {{ risk }}
            </el-tag>
          </div>
        </div>

        <div class="filter-grid">
          <el-select v-model="form.report_type" placeholder="报表类型" :disabled="formInteractionDisabled">
            <el-option
              v-for="item in reportTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-select v-if="requiresExam" v-model="form.exam_id" filterable placeholder="考试" :disabled="formInteractionDisabled">
            <el-option
              v-for="exam in examOptions"
              :key="exam.id"
              :label="exam.name"
              :value="exam.id"
            />
          </el-select>
          <el-select v-if="requiresStudent" v-model="form.student_id" filterable placeholder="学生" :disabled="formInteractionDisabled">
            <el-option
              v-for="student in studentOptions"
              :key="student.id"
              :label="`${student.student_no} - ${student.name}`"
              :value="student.id"
            />
          </el-select>
          <el-select v-if="requiresScheme" v-model="form.scheme_id" filterable placeholder="推荐方案" :disabled="formInteractionDisabled">
            <el-option
              v-for="item in recommendationOptions"
              :key="item.scheme_id"
              :label="`${item.student_name} / ${item.scheme_name}`"
              :value="item.scheme_id"
            />
          </el-select>
          <el-select v-if="requiresDraft" v-model="form.draft_id" filterable placeholder="志愿草稿" :disabled="formInteractionDisabled">
            <el-option
              v-for="item in volunteerDraftOptions"
              :key="item.id"
              :label="`${item.student_name ?? '-'} / ${item.name}`"
              :value="item.id"
            />
          </el-select>
          <el-select v-if="requiresBatch" v-model="form.batch_id" filterable placeholder="评教批次" :disabled="formInteractionDisabled">
            <el-option
              v-for="item in evaluationBatchOptions"
              :key="item.id"
              :label="`${item.template_name ?? '-'} / ${item.semester_name ?? '-'}`"
              :value="item.id"
            />
          </el-select>
          <el-select v-if="requiresClass" v-model="form.class_id" filterable placeholder="班级" :disabled="formInteractionDisabled">
            <el-option
              v-for="item in referenceStore.classes"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
          <el-select v-if="requiresGrade" v-model="form.grade_id" filterable placeholder="年级" :disabled="formInteractionDisabled">
            <el-option
              v-for="item in referenceStore.grades"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
          <el-select v-if="requiresTeacher" v-model="form.teacher_id" filterable placeholder="教师" :disabled="formInteractionDisabled">
            <el-option
              v-for="teacher in teacherOptions"
              :key="teacher.id"
              :label="teacher.name"
              :value="teacher.id"
            />
          </el-select>
          <el-select v-if="requiresSemester" v-model="form.semester_id" filterable placeholder="学期" :disabled="formInteractionDisabled">
            <el-option
              v-for="semester in referenceStore.semesters"
              :key="semester.id"
              :label="semesterLabel(semester)"
              :value="semester.id"
            />
          </el-select>
          <el-select
            v-if="optionalRuleVersion"
            v-model="form.rule_version_id"
            clearable
            filterable
            placeholder="规则版本，可选"
            :disabled="formInteractionDisabled"
          >
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
            :disabled="formInteractionDisabled"
          />
          <el-date-picker
            v-if="usesEndDate"
            v-model="form.end_date"
            value-format="YYYY-MM-DD"
            placeholder="结束日期，可选"
            :disabled="formInteractionDisabled"
          />
        </div>
        <div class="action-row toolbar-row">
          <el-button type="primary" :loading="exporting" :disabled="optionsLoading" @click="exportReport">
            生成报表
          </el-button>
          <el-button
            v-if="supportsPrintPreview"
            :disabled="printPreviewDisabled"
            @click="openPrintPreview"
          >
            打印预览
          </el-button>
        </div>
        <el-alert
          v-if="exportActionError"
          class="report-alert"
          type="error"
          show-icon
          :closable="false"
          title="报表生成失败"
        >
          <template #default>
            <div class="action-row toolbar-row">
              <span>{{ exportActionError }}</span>
              <el-button size="small" type="danger" plain :loading="exporting" @click="exportReport">
                重新生成报表
              </el-button>
            </div>
          </template>
        </el-alert>
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
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>导出记录</h3>
          <p>记录报表类型、参数、导出时间和下载入口，方便复现。</p>
        </div>
        <el-button :loading="recordsLoading" @click="loadExportRecords(true)">刷新记录</el-button>
      </div>
      <el-alert
        v-if="recordsLoadError"
        class="report-alert"
        type="error"
        show-icon
        :closable="false"
        :title="recordsLoadError"
      >
        <template #default>
          <el-button size="small" type="danger" plain :loading="recordsLoading" @click="loadExportRecords(true)">
            重新加载导出记录
          </el-button>
        </template>
      </el-alert>
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
              <el-button link type="primary" :disabled="recordsLoading || !row.download_url" @click="openFile(row.download_url)">
                下载
              </el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="exportRecordsEmptyDescription">
              <el-button
                v-if="recordsLoadError"
                type="primary"
                plain
                :loading="recordsLoading"
                @click="loadExportRecords(true)"
              >
                重新加载导出记录
              </el-button>
            </el-empty>
          </template>
        </el-table>
      </div>
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
  getReportCatalogItem,
  getReportCatalogItemsByDomain,
  getReportDomainForType,
  getGroupedReportCatalog,
  getMissingRequiredReportFields,
  getMissingRequiredReportFieldsMessage,
  getReportPrintPreviewPath,
  getReportRuleOptionScope,
  getReportTypeLabel,
  type ReportDomain,
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
const optionsLoadError = ref("");
const recordsLoadError = ref("");
const exportActionError = ref("");
const scoreRecordTotal = ref(0);
const reportTypeOptions = REPORT_TYPE_OPTIONS;
const groupedReportCatalog = getGroupedReportCatalog();
const selectedCatalogDomain = ref<ReportDomain>(getReportDomainForType("student_analysis") ?? "students");

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
const currentReportCatalogItem = computed(() => getReportCatalogItem(form.report_type));
const activeDomainGroup = computed(
  () => groupedReportCatalog.find((group) => group.key === selectedCatalogDomain.value) ?? groupedReportCatalog[0] ?? null,
);
const activeDomainReports = computed(() => getReportCatalogItemsByDomain(selectedCatalogDomain.value));
const printPreviewPath = computed(() => getReportPrintPreviewPath(form));
const supportsPrintPreview = computed(() => Boolean(printPreviewPath.value));
const currentReportTypeLabel = computed(() => getReportTypeLabel(form.report_type));
const reportsPageMeta = computed(() => [
  { label: "报表类型", value: reportTypeOptions.length },
  { label: "当前类型", value: currentReportTypeLabel.value },
  { label: "导出记录", value: recordsLoadError.value ? "加载失败" : exportRecords.value.length },
  { label: "推荐方案", value: optionsLoadError.value ? "加载失败" : recommendationOptions.value.length },
  { label: "志愿草稿", value: optionsLoadError.value ? "加载失败" : volunteerDraftOptions.value.length },
]);
const formInteractionDisabled = computed(() => optionsLoading.value || exporting.value);
const loadErrorItems = computed(() => [
  { label: "报表选项", message: optionsLoadError.value },
  { label: "导出记录", message: recordsLoadError.value },
].filter((item) => item.message));
const missingRequiredFields = computed(() => getMissingRequiredReportFields(form));
const missingRequiredFieldsMessage = computed(() => getMissingRequiredReportFieldsMessage(form));
const printPreviewDisabled = computed(
  () => formInteractionDisabled.value || Boolean(missingRequiredFields.value.length) || !printPreviewPath.value,
);
const exportRecordsEmptyDescription = computed(() =>
  recordsLoadError.value
    ? "导出记录加载失败，请重试。"
    : "暂无导出记录。请先在上方选择报表类型并补齐参数，再点击“生成报表”。",
);
const scoreReportGuardMessages = computed(() =>
  buildScoreReportGuardMessages(form.report_type, {
    examCount: examOptions.value.length,
    scoreRecordTotal: scoreRecordTotal.value,
  }),
);
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

function selectReportType(reportType: string): void {
  form.report_type = reportType;
  exportActionError.value = "";
}

function clearReportOptions(): void {
  examOptions.value = [];
  studentOptions.value = [];
  teacherOptions.value = [];
  ruleVersions.value = [];
  adviserRuleVersions.value = [];
  recommendationOptions.value = [];
  volunteerDraftOptions.value = [];
  evaluationBatchOptions.value = [];
  scoreRecordTotal.value = 0;
}

async function loadOptions(showToast = false): Promise<void> {
  optionsLoading.value = true;
  optionsLoadError.value = "";
  exportActionError.value = "";
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
    clearReportOptions();
    optionsLoadError.value = formatUserActionError("刷新报表选项", error, "确认考试、学生、教师或推荐数据接口可用后重试。");
    if (showToast) ElMessage.error(optionsLoadError.value);
  } finally {
    optionsLoading.value = false;
  }
}

async function loadExportRecords(showToast = false): Promise<void> {
  recordsLoading.value = true;
  recordsLoadError.value = "";
  try {
    exportRecords.value = await apiRequest<ExportRecord[]>("/api/reports/exports");
  } catch (error) {
    exportRecords.value = [];
    recordsLoadError.value = formatUserActionError("刷新导出记录", error, "确认本地服务已启动后重试；不影响你重新生成报表。");
    if (showToast) ElMessage.error(recordsLoadError.value);
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
    exportActionError.value = "";
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
    exportActionError.value = formatUserActionError("生成报表", error, "先确认报表参数完整；如果仍失败，请回到对应业务页复核源数据。");
    ElMessage.error(exportActionError.value);
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
  () => form.report_type,
  (reportType) => {
    const domain = getReportDomainForType(reportType);
    if (domain) selectedCatalogDomain.value = domain;
  },
);

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
    exportActionError.value = "";
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
  applyRoutePrefill();
  await Promise.all([loadOptions(), loadExportRecords()]);
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

.load-error-list {
  display: grid;
  gap: 8px;
  margin: 0 0 12px;
  padding: 0;
  list-style: none;
}

.load-error-list li {
  display: grid;
  gap: 4px;
}

.load-error-list strong {
  color: #7f1d1d;
}

.load-error-list span {
  color: #6b3d3d;
  line-height: 1.55;
}

.report-workspace {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.report-picker {
  position: sticky;
  top: 18px;
  padding: 20px;
}

.domain-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.domain-tab {
  min-height: 32px;
  padding: 7px 11px;
  border: 1px solid #d9e5ef;
  border-radius: 6px;
  background: #fff;
  color: #52677c;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.domain-tab.active {
  border-color: #1f6c98;
  background: #e9f4fb;
  color: #1f6c98;
}

.domain-tab:disabled,
.report-list-item:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.active-domain-copy {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #e4edf5;
}

.active-domain-copy strong {
  color: #1f3448;
  font-size: 15px;
}

.active-domain-copy p {
  margin: 5px 0 0;
  color: #667b8f;
  line-height: 1.55;
  font-size: 13px;
}

.report-list {
  display: grid;
  gap: 8px;
  margin-top: 14px;
}

.report-list-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  min-height: 72px;
  padding: 11px 12px;
  border: 1px solid #dce7f1;
  border-radius: 8px;
  background: #fff;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.report-list-item.selected {
  border-color: #1f6c98;
  box-shadow: inset 3px 0 0 rgba(31, 108, 152, 0.86);
}

.report-list-item strong {
  display: block;
  color: #24384b;
  font-size: 14px;
}

.report-list-item span {
  display: block;
  margin-top: 4px;
  color: #65798d;
  line-height: 1.45;
  font-size: 12px;
}

.report-list-item small {
  flex: 0 0 auto;
  max-width: 92px;
  color: #1f6c98;
  line-height: 1.45;
  text-align: right;
  font-size: 12px;
}

.report-form-panel {
  min-width: 0;
}

.current-report-strip {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(260px, 1.1fr);
  gap: 14px 18px;
  margin-bottom: 16px;
  padding: 0 0 16px;
  border-bottom: 1px solid #e5edf4;
}

.current-report-strip span {
  color: #1f6c98;
  font-size: 12px;
  font-weight: 740;
}

.current-report-strip strong {
  display: block;
  margin-top: 5px;
  color: #1f3448;
  font-size: 20px;
}

.current-report-strip p {
  margin: 7px 0 0;
  color: #60748a;
  line-height: 1.6;
}

.current-report-strip dl {
  display: grid;
  gap: 8px;
  margin: 0;
}

.current-report-strip dl div {
  display: grid;
  grid-template-columns: 70px minmax(0, 1fr);
  gap: 10px;
}

.current-report-strip dt {
  color: #7a8ea2;
  font-size: 12px;
}

.current-report-strip dd {
  margin: 0;
  color: #2d4052;
  line-height: 1.45;
  font-size: 13px;
}

.current-report-strip .risk-tag-row {
  grid-column: 1 / -1;
}

.toolbar-row {
  margin-top: 14px;
}

.report-alert {
  margin-top: 14px;
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
  .report-workspace,
  .current-report-strip {
    grid-template-columns: 1fr;
  }

  .report-picker {
    position: static;
  }
}
</style>
