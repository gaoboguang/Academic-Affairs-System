<template>
  <AppPage
    title="工作台"
    eyebrow="本地教务工具 / 今日概览"
    description="汇总学生、教师、考试、导入、数据质量和待处理事项，进入系统后先确认这里的关键状态。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button type="primary" plain :loading="loading" @click="reload">刷新工作台</el-button>
    </template>

    <div v-if="loadError" class="dashboard-alert">
      <el-alert
        type="error"
        show-icon
        :closable="false"
        title="工作台数据加载失败"
        :description="loadError"
      />
      <el-button type="primary" :loading="loading" @click="reload">重新加载</el-button>
    </div>

    <div v-if="hasDashboardShell" v-loading="loading" class="dashboard-body">
      <section class="status-card-grid" aria-label="工作台关键指标">
        <button
          v-for="card in statusCards"
          :key="card.label"
          type="button"
          class="status-card-button"
          :disabled="dashboardActionsDisabled"
          @click="router.push(card.path)"
        >
          <AppStatCard
            :label="card.label"
            :value="card.value"
            :help="card.help"
            :tone="card.tone"
            :loading="card.loading"
          />
        </button>
      </section>

      <template v-if="hasLoaded">
      <AppSectionCard
        title="待处理事项"
        description="根据当前学生、教师、考试和升学任务整理优先动作，点进对应页面继续处理。"
      >
        <div v-if="nextSteps.length" class="next-step-grid">
          <article v-for="step in nextSteps" :key="step.code" class="next-step-card">
            <div class="next-step-head">
              <el-tag :type="step.severity" effect="light">{{ severityLabel(step.severity) }}</el-tag>
              <el-button link type="primary" :disabled="dashboardActionsDisabled" @click="router.push(step.path)">
                {{ step.actionLabel }}
              </el-button>
            </div>
            <h3>{{ step.title }}</h3>
            <p>{{ step.detail }}</p>
          </article>
        </div>
        <el-empty v-else description="当前没有需要优先处理的事项" />
      </AppSectionCard>

      <section class="dashboard-grid">
        <AppSectionCard
          title="最近考试与成绩状态"
          description="查看最近一次考试是否已有成绩，便于继续做分析和报表。"
        >
          <template #actions>
            <el-button v-if="summary.recent_exam" type="primary" plain :disabled="dashboardActionsDisabled" @click="openAnalytics">
              进入分析中心
            </el-button>
          </template>

          <div v-if="summary.recent_exam" class="exam-summary">
            <div class="exam-summary-main">
              <strong>{{ summary.recent_exam.exam_name }}</strong>
              <span>{{ summary.recent_exam.exam_date }}</span>
              <p v-if="summary.recent_exam.participant_count > 0">
                已形成成绩快照，可进入分析中心查看学生、班级、年级和教师分析结果。
              </p>
              <p v-else>
                这场考试还没有可用成绩记录，请先在考试成绩页导入成绩，再查看分析和报表。
              </p>
            </div>
            <div class="exam-summary-metrics">
              <div class="exam-metric">
                <span>参与人数</span>
                <strong>{{ summary.recent_exam.participant_count }}</strong>
              </div>
              <div class="exam-metric">
                <span>总分均分</span>
                <strong>{{ formatNumber(summary.recent_exam.average_score) }}</strong>
              </div>
              <div class="exam-metric">
                <span>优秀率</span>
                <strong>{{ formatPercent(summary.recent_exam.excellent_rate) }}</strong>
              </div>
            </div>
          </div>
          <div v-else class="empty-action">
            <el-empty description="暂无可用考试数据" />
            <p>先创建考试并配置科目，再导入成绩，后续分析中心和报表中心才有可靠数据。</p>
            <el-button type="primary" :disabled="dashboardActionsDisabled" @click="router.push('/exams')">创建考试</el-button>
          </div>
        </AppSectionCard>

        <AppSectionCard title="快捷入口" description="入口全部指向现有业务页面，避免重复创建孤立流程。">
          <div class="quick-grid">
            <button
              v-for="item in quickActions"
              :key="item.label"
              type="button"
              class="quick-action"
              :disabled="dashboardActionsDisabled"
              @click="router.push(item.path)"
            >
              <strong>{{ item.label }}</strong>
              <span>{{ item.help }}</span>
            </button>
          </div>
        </AppSectionCard>
      </section>

      <AppSectionCard
        title="基础数据修复提醒"
        description="展示学生、班级、成绩等日常数据里需要补齐或修正的事项。"
      >
        <template #actions>
          <el-button link type="primary" :disabled="dashboardActionsDisabled" @click="router.push('/system-tools')">
            处理数据问题
          </el-button>
        </template>

        <div v-if="summary.data_quality_issues.length" class="quality-grid">
          <article v-for="issue in summary.data_quality_issues" :key="issue.code" class="quality-card">
            <div class="quality-head">
              <el-tag :type="issue.severity === 'error' ? 'danger' : 'warning'" effect="light">
                {{ issue.severity === "error" ? "高风险" : "提醒" }}
              </el-tag>
              <strong>{{ issue.count }}</strong>
            </div>
            <h3>{{ issue.title }}</h3>
            <p>{{ issue.summary }}</p>
            <div v-if="issue.samples.length" class="quality-samples">
              <span v-for="sample in issue.samples" :key="sample">{{ sample }}</span>
            </div>
          </article>
        </div>
        <el-empty v-else description="当前没有需要提醒的基础数据修复问题" />
      </AppSectionCard>

      <AppSectionCard
        title="最近导入"
        description="展示最近几次导入的类型、状态和来源文件，便于回看最近操作。"
      >
        <template #actions>
          <el-button link type="primary" :disabled="dashboardActionsDisabled" @click="router.push('/import-center')">
            查看导入中心
          </el-button>
        </template>

        <div class="table-shell">
          <el-table :data="recentImportRows" stripe v-loading="loading">
            <el-table-column label="批次 ID" prop="id" width="90" />
            <el-table-column label="类型" min-width="140">
              <template #default="{ row }">
                {{ row.job_type_label }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="row.status_type" effect="light">{{ row.status_label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="来源文件" prop="source_filename" min-width="180" />
            <el-table-column label="开始时间" prop="started_at" min-width="180" />
            <el-table-column label="结束时间" prop="finished_at" min-width="180" />
            <template #empty>
              <el-empty :description="loading ? '正在加载最近导入记录' : '暂无导入记录'" />
            </template>
          </el-table>
        </div>
      </AppSectionCard>
      </template>

      <el-empty v-else class="dashboard-shell-empty" :description="dashboardBodyEmptyDescription">
        <el-button v-if="loadError" type="primary" :loading="loading" @click="reload">重新加载工作台数据</el-button>
      </el-empty>
    </div>

    <el-empty
      v-else
      class="dashboard-empty"
      :description="loading ? '正在加载工作台数据' : '工作台数据暂未加载'"
    >
      <el-button v-if="!loading" type="primary" @click="reload">重新加载</el-button>
    </el-empty>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import { useRouter } from "vue-router";

import { apiRequest } from "../api/client";
import {
  buildDashboardNextSteps,
  formatDashboardBackupLabel,
  formatDataHealthCardValue,
  type DashboardBackupSummary,
  type DashboardDataHealthSummary,
  type DashboardNextStep,
} from "../components/dashboard/dashboardDecisions";
import { AppPage, AppSectionCard, AppStatCard, type PageMetaItem, type StatCardItem } from "../components/ui";
import { formatImportStatus as formatUnifiedImportStatus, importStatusTagType } from "../utils/importFeedback";
import { formatUserActionError } from "../utils/userFeedback";

interface ImportJob {
  id: number;
  job_type: string;
  source_filename?: string;
  status: string;
  started_at?: string;
  finished_at?: string;
}

interface RecentExam {
  exam_id: number;
  exam_name: string;
  exam_date: string;
  participant_count: number;
  average_score?: number | null;
  excellent_rate?: number | null;
}

interface DataQualityIssue {
  code: string;
  title: string;
  severity: string;
  count: number;
  summary: string;
  samples: string[];
}

interface DashboardSummary {
  student_total: number;
  teacher_total: number;
  exam_total: number;
  score_record_total: number;
  grade_total: number;
  class_total: number;
  recent_imports: ImportJob[];
  latest_backup_time?: string | null;
  latest_backup?: DashboardBackupSummary | null;
  recent_exam?: RecentExam | null;
  data_health?: DashboardDataHealthSummary | null;
  data_quality_issues: DataQualityIssue[];
  planning_summary?: {
    open_task_count: number;
    overdue_task_count: number;
    due_soon_task_count: number;
    students_without_goal_count: number;
    volunteer_draft_without_review_count: number;
    material_gap_without_due_count: number;
  } | null;
}

interface DashboardStatusCard extends StatCardItem {
  path: string;
}

const router = useRouter();

const loading = ref(false);
const hasLoaded = ref(false);
const loadError = ref("");
const dashboardLoadFailed = computed(() => Boolean(loadError.value && !hasLoaded.value));
const hasDashboardShell = computed(() => hasLoaded.value || loading.value || dashboardLoadFailed.value);
const dashboardBodyEmptyDescription = computed(() => {
  if (loading.value) return "正在加载工作台数据";
  if (dashboardLoadFailed.value) return "工作台数据加载失败，请重新加载。";
  return "工作台数据暂未加载";
});

const quickActions = [
  { label: "学生导入", help: "补齐学生主档和班级信息。", path: "/students" },
  { label: "教师维护", help: "维护教师台账和任教关系。", path: "/teachers" },
  { label: "考试成绩导入", help: "创建考试、配置科目并导入成绩。", path: "/exams" },
  { label: "分析中心", help: "查看学生、班级、年级和教师分析。", path: "/analytics" },
  { label: "报表中心", help: "导出打印可交接的汇总材料。", path: "/reports" },
  { label: "高考志愿工作台", help: "进入推荐和志愿草稿流程。", path: "/recommendations" },
];

const importJobTypeLabels: Record<string, string> = {
  student_import: "学生导入",
  students: "学生导入",
  teacher_import: "教师导入",
  teachers: "教师导入",
  exam_score_import: "成绩导入",
  score_import: "成绩导入",
  scores: "成绩导入",
  timetable_import: "课表导入",
  timetable: "课表导入",
  admission_import: "录取数据导入",
  admissions: "录取数据导入",
  enrollment_plans: "招生计划导入",
  evaluation_import: "评教导入",
  evaluation: "评教导入",
  archive_import: "档案导入",
};

const importStatusLabels: Record<string, string> = {
  pending: "待处理",
  running: "处理中",
  processing: "处理中",
  success: "成功",
  partially_failed: "部分成功",
  partial_success: "部分成功",
  completed: "已完成",
  completed_with_unresolved: "待修正",
  failed: "失败",
  rolled_back: "已回滚",
};

const summary = reactive<DashboardSummary>(createEmptyDashboardSummary());

const latestImport = computed(() => summary.recent_imports[0] ?? null);
const latestImportLabel = computed(() =>
  latestImport.value ? formatImportJobType(latestImport.value.job_type) : "暂无",
);
const backupLabel = computed(() => formatDashboardBackupLabel(summary.latest_backup));

const pageMeta = computed<PageMetaItem[]>(() => {
  if (dashboardLoadFailed.value) {
    return [
      { label: "数据状态", value: "加载失败" },
      { label: "最近考试", value: "加载失败" },
      { label: "最近导入", value: "加载失败" },
      { label: "最近备份", value: "加载失败" },
    ];
  }

  return [
    { label: "数据状态", value: hasLoaded.value ? "已加载" : "待加载" },
    { label: "最近考试", value: summary.recent_exam?.exam_name ?? "暂无" },
    { label: "最近导入", value: latestImportLabel.value },
    { label: "最近备份", value: backupLabel.value },
  ];
});
const dashboardActionsDisabled = computed(() => loading.value || dashboardLoadFailed.value);

const failedStatusCards: DashboardStatusCard[] = [
  {
    label: "学生总数",
    value: "加载失败",
    help: "工作台概览暂时无法读取，请重新加载。",
    path: "/students",
    tone: "danger",
  },
  {
    label: "教师总数",
    value: "加载失败",
    help: "工作台概览暂时无法读取，请重新加载。",
    path: "/teachers",
    tone: "danger",
  },
  {
    label: "考试数量",
    value: "加载失败",
    help: "工作台概览暂时无法读取，请重新加载。",
    path: "/exams",
    tone: "danger",
  },
  {
    label: "成绩记录",
    value: "加载失败",
    help: "工作台概览暂时无法读取，请重新加载。",
    path: "/exams",
    tone: "danger",
  },
  {
    label: "数据健康",
    value: "加载失败",
    help: "工作台概览暂时无法读取，请重新加载。",
    path: "/gaokao-data",
    tone: "danger",
  },
  {
    label: "最近备份",
    value: "加载失败",
    help: "工作台概览暂时无法读取，请重新加载。",
    path: "/system-tools",
    tone: "danger",
  },
  {
    label: "最近导入",
    value: "加载失败",
    help: "工作台概览暂时无法读取，请重新加载。",
    path: "/import-center",
    tone: "danger",
  },
];

const statusCards = computed<DashboardStatusCard[]>(() => {
  if (dashboardLoadFailed.value) {
    return failedStatusCards.map((card) => ({ ...card, loading: loading.value }));
  }

  return [
    {
      label: "学生总数",
      value: summary.student_total,
      help: "查看学生名单、画像和详情。",
      path: "/students",
      tone: "primary",
      loading: loading.value,
    },
    {
      label: "教师总数",
      value: summary.teacher_total,
      help: "维护教师台账和任教关系。",
      path: "/teachers",
      tone: "info",
      loading: loading.value,
    },
    {
      label: "考试数量",
      value: summary.exam_total,
      help: "进入考试成绩页继续处理。",
      path: "/exams",
      tone: "warning",
      loading: loading.value,
    },
    {
      label: "成绩记录",
      value: summary.score_record_total,
      help: "查看已导入的成绩明细。",
      path: "/exams",
      tone: "success",
      loading: loading.value,
    },
    {
      label: "数据健康",
      value: formatDataHealthCardValue(summary.data_health),
      help: "查看基础数据和高考数据缺口。",
      path: "/gaokao-data",
      tone: summary.data_health?.p0_gap_count ? "danger" : "neutral",
      loading: loading.value,
    },
    {
      label: "最近备份",
      value: backupLabel.value,
      help: "进入系统工具查看备份与恢复。",
      path: "/system-tools",
      tone: "neutral",
      loading: loading.value,
    },
    {
      label: "最近导入",
      value: latestImportLabel.value,
      help: "查看最近导入批次和错误报告。",
      path: "/import-center",
      tone: "neutral",
      loading: loading.value,
    },
  ];
});

const nextSteps = computed(() => buildDashboardNextSteps(summary));

const recentImportRows = computed(() =>
  summary.recent_imports.map((item) => ({
    ...item,
    job_type_label: formatImportJobType(item.job_type),
    status_label: formatImportStatus(item.status),
    status_type: formatImportStatusType(item.status),
  })),
);

function formatNumber(value?: number | null): string {
  if (value === null || value === undefined) return "-";
  return value.toFixed(2);
}

function formatPercent(value?: number | null): string {
  if (value === null || value === undefined) return "-";
  return `${value.toFixed(2)}%`;
}

function formatImportJobType(jobType: string): string {
  return importJobTypeLabels[jobType] ?? jobType.replace(/_/g, " ");
}

function formatImportStatus(status: string): string {
  return importStatusLabels[status] ?? formatUnifiedImportStatus(status);
}

function formatImportStatusType(status: string): "success" | "warning" | "danger" | "info" {
  return importStatusTagType(status);
}

function createEmptyDashboardSummary(): DashboardSummary {
  return {
    student_total: 0,
    teacher_total: 0,
    exam_total: 0,
    score_record_total: 0,
    grade_total: 0,
    class_total: 0,
    recent_imports: [],
    latest_backup_time: null,
    latest_backup: null,
    recent_exam: null,
    data_health: null,
    data_quality_issues: [],
    planning_summary: null,
  };
}

function resetSummary(): void {
  Object.assign(summary, createEmptyDashboardSummary());
}

async function reload(): Promise<void> {
  loading.value = true;
  loadError.value = "";
  try {
    const payload = await apiRequest<DashboardSummary>("/api/dashboard/summary");
    Object.assign(summary, {
      ...payload,
      recent_imports: payload.recent_imports ?? [],
      data_quality_issues: payload.data_quality_issues ?? [],
    });
    hasLoaded.value = true;
  } catch (error) {
    resetSummary();
    hasLoaded.value = false;
    loadError.value = formatUserActionError("加载工作台数据", error, "确认本地后端服务正常后重试");
    ElMessage.error(loadError.value);
  } finally {
    loading.value = false;
  }
}

function openAnalytics(): void {
  void router.push("/analytics");
}

function severityLabel(severity: DashboardNextStep["severity"]): string {
  if (severity === "danger") return "高风险";
  if (severity === "warning") return "建议处理";
  return "提醒";
}

onMounted(() => {
  void reload();
});
</script>

<style scoped>
.dashboard-alert {
  display: flex;
  align-items: stretch;
  gap: 12px;
  margin-bottom: 16px;
}

.dashboard-alert .el-alert {
  flex: 1;
}

.dashboard-body {
  display: grid;
  gap: 18px;
  min-height: 360px;
}

.dashboard-empty {
  padding: 72px 0;
}

.dashboard-shell-empty {
  padding: 40px 0 32px;
}

.status-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.status-card-button {
  display: block;
  min-width: 0;
  width: 100%;
  height: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.status-card-button:disabled,
.quick-action:disabled {
  cursor: not-allowed;
  opacity: 0.62;
}

.status-card-button:focus-visible {
  outline: 2px solid rgba(31, 108, 152, 0.55);
  outline-offset: 4px;
}

.status-card-button :deep(.app-stat-card) {
  height: 100%;
}

.status-card-button :deep(.app-stat-value strong) {
  overflow-wrap: anywhere;
  line-height: 1.18;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 18px;
}

.next-step-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}

.next-step-card {
  display: grid;
  gap: 10px;
  padding: 16px;
  border: 1px solid rgba(120, 138, 156, 0.14);
  border-radius: 8px;
  background: rgba(250, 252, 255, 0.92);
}

.next-step-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.next-step-card h3,
.quality-card h3 {
  margin: 0;
  color: #1f3346;
  font-size: 16px;
  letter-spacing: 0;
}

.next-step-card p,
.quality-card p {
  margin: 0;
  color: #647789;
  line-height: 1.6;
}

.exam-summary {
  display: grid;
  gap: 18px;
}

.exam-summary-main {
  display: grid;
  gap: 8px;
}

.exam-summary-main strong {
  color: #1e3448;
  font-size: 24px;
}

.exam-summary-main span {
  color: #6c8194;
  font-size: 13px;
}

.exam-summary-main p {
  margin: 0;
  color: #60758a;
  line-height: 1.6;
}

.exam-summary-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.exam-metric {
  padding: 18px;
  border-radius: 8px;
  background: rgba(245, 249, 252, 0.84);
  border: 1px solid rgba(120, 138, 156, 0.12);
}

.exam-metric span {
  display: block;
  color: #6b7f92;
  font-size: 13px;
}

.exam-metric strong {
  display: block;
  margin-top: 10px;
  font-size: 28px;
  color: #1d3147;
}

.empty-action {
  display: grid;
  justify-items: center;
  gap: 12px;
  padding: 12px 0 4px;
  text-align: center;
}

.empty-action p {
  max-width: 520px;
  margin: 0;
  color: #647789;
  line-height: 1.6;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.quick-action {
  padding: 18px;
  border: 1px solid rgba(114, 132, 150, 0.14);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.quick-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px rgba(37, 57, 81, 0.08);
  border-color: rgba(31, 108, 152, 0.24);
}

.quick-action:disabled:hover {
  transform: none;
  box-shadow: none;
  border-color: rgba(114, 132, 150, 0.14);
}

.quick-action strong {
  display: block;
  color: #213344;
  font-size: 16px;
}

.quick-action span {
  display: block;
  margin-top: 8px;
  color: #667a8d;
  line-height: 1.5;
}

.quality-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.quality-card {
  padding: 18px;
  border-radius: 8px;
  background: rgba(250, 252, 255, 0.92);
  border: 1px solid rgba(120, 138, 156, 0.14);
}

.quality-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.quality-card h3 {
  margin-top: 14px;
  margin-bottom: 8px;
}

.quality-samples {
  display: grid;
  gap: 6px;
  margin-top: 12px;
}

.quality-samples span {
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(242, 247, 252, 0.82);
  color: #5f7385;
  font-size: 12px;
}

@media (max-width: 1100px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .dashboard-alert {
    display: grid;
  }

  .exam-summary-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
