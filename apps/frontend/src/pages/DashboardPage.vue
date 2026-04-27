<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">工作台 / 今日教务决策台</div>
        <h2 class="page-title">先判断系统能不能试用，再进入具体工作</h2>
        <p class="page-subtitle">
          汇总学生、教师、考试、成绩、导入、备份和高考数据健康状态，把下一步要做的事直接摆在首页。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>学生</strong>{{ summary.student_total }}</span>
          <span class="page-chip"><strong>教师</strong>{{ summary.teacher_total }}</span>
          <span class="page-chip"><strong>成绩记录</strong>{{ summary.score_record_total }}</span>
          <span class="page-chip"><strong>P0 缺口</strong>{{ summary.data_health?.p0_gap_count ?? "-" }}</span>
          <span class="page-chip"><strong>最近导入</strong>{{ latestImport ? formatImportJobType(latestImport.job_type) : "暂无" }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="router.push('/import-center')">导入中心</el-button>
        <el-button @click="router.push('/system-tools')">系统设置</el-button>
        <el-button type="primary" @click="reload">刷新概况</el-button>
      </div>
    </header>

    <section class="metric-grid">
      <button
        v-for="card in statusCards"
        :key="card.label"
        type="button"
        class="metric-button"
        @click="router.push(card.path)"
      >
        <MetricCard :label="card.label" :value="card.value" :help-text="card.helpText" />
      </button>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>下一步建议</h3>
          <p>这些建议只基于当前本地数据状态生成，点击后进入已有页面处理。</p>
        </div>
      </div>
      <div class="next-step-grid">
        <article v-for="step in nextSteps" :key="step.code" class="next-step-card">
          <div class="next-step-head">
            <el-tag :type="step.severity" effect="light">{{ severityLabel(step.severity) }}</el-tag>
            <el-button link type="primary" @click="router.push(step.path)">{{ step.actionLabel }}</el-button>
          </div>
          <h4>{{ step.title }}</h4>
          <p>{{ step.detail }}</p>
        </article>
      </div>
    </section>

    <section class="dashboard-grid">
      <article class="soft-card panel-block">
        <div class="section-head compact">
          <div>
            <h3>最近考试与成绩状态</h3>
            <p>优先确认最近考试是否已有成绩，避免在空成绩库上解读分析图表。</p>
          </div>
          <el-button v-if="summary.recent_exam" type="primary" plain @click="openAnalytics">
            进入分析中心
          </el-button>
        </div>

        <div v-if="summary.recent_exam" class="exam-summary">
          <div class="exam-summary-main">
            <strong>{{ summary.recent_exam.exam_name }}</strong>
            <span>{{ summary.recent_exam.exam_date }}</span>
            <p v-if="summary.recent_exam.participant_count > 0">
              已形成成绩快照，可进入分析中心查看学生、班级、年级和教师分析结果。
            </p>
            <p v-else>
              这场考试还没有可用成绩记录。请先在考试成绩页导入成绩，再查看分析和报表。
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
          <el-button type="primary" @click="router.push('/exams')">创建考试</el-button>
        </div>
      </article>

      <article class="soft-card panel-block">
        <div class="section-head compact">
          <div>
            <h3>快捷入口</h3>
            <p>入口全部指向现有业务页面，不新造孤立流程。</p>
          </div>
        </div>

        <div class="quick-grid">
          <button
            v-for="item in quickActions"
            :key="item.label"
            type="button"
            class="quick-action"
            @click="router.push(item.path)"
          >
            <strong>{{ item.label }}</strong>
            <span>{{ item.help }}</span>
          </button>
        </div>
      </article>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>基础数据修复提醒</h3>
          <p>这些是学生、班级、成绩等业务数据的可修复问题；高考数据缺口请进入高考数据看板复核。</p>
        </div>
        <el-button link type="primary" @click="router.push('/system-tools')">打开修复工具</el-button>
      </div>
      <div v-if="summary.data_quality_issues.length" class="quality-grid">
        <article v-for="issue in summary.data_quality_issues" :key="issue.code" class="quality-card">
          <div class="quality-head">
            <el-tag :type="issue.severity === 'error' ? 'danger' : 'warning'" effect="light">
              {{ issue.severity === "error" ? "高风险" : "提醒" }}
            </el-tag>
            <strong>{{ issue.count }}</strong>
          </div>
          <h4>{{ issue.title }}</h4>
          <p>{{ issue.summary }}</p>
          <div v-if="issue.samples.length" class="quality-samples">
            <span v-for="sample in issue.samples" :key="sample">{{ sample }}</span>
          </div>
        </article>
      </div>
      <el-empty v-else description="当前没有需要提醒的基础数据修复问题" />
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>最近导入</h3>
          <p>展示最近几次导入的类型、状态和来源文件，便于回看最近操作。</p>
        </div>
        <el-button link type="primary" @click="router.push('/import-center')">
          查看导入中心
        </el-button>
      </div>
      <div class="table-shell">
        <el-table :data="recentImportRows" stripe>
          <el-table-column label="批次 ID" prop="id" width="90" />
          <el-table-column label="类型" min-width="140">
            <template #default="{ row }">
              {{ row.job_type_label }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="row.status_type" effect="light">{{ row.status_label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="来源文件" prop="source_filename" min-width="180" />
          <el-table-column label="开始时间" prop="started_at" min-width="180" />
          <el-table-column label="结束时间" prop="finished_at" min-width="180" />
        </el-table>
      </div>
      <el-empty v-if="!summary.recent_imports.length" description="暂无导入记录" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import { useRouter } from "vue-router";

import { apiRequest } from "../api/client";
import {
  buildDashboardNextSteps,
  formatDashboardBackupLabel,
  formatDataHealthCardValue,
  type DashboardBackupSummary,
  type DashboardDataHealthSummary,
} from "../components/dashboard/dashboardDecisions";
import MetricCard from "../components/MetricCard.vue";
import { formatImportStatus as formatUnifiedImportStatus, importStatusTagType } from "../utils/importFeedback";

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
}

const router = useRouter();

const quickActions = [
  { label: "学生导入", help: "补齐学生主档和班级信息。", path: "/students" },
  { label: "教师维护", help: "维护教师台账和任教关系。", path: "/teachers" },
  { label: "考试成绩导入", help: "创建考试、配置科目并导入成绩。", path: "/exams" },
  { label: "分析中心", help: "查看学生、班级、年级和教师分析。", path: "/analytics" },
  { label: "报表中心", help: "导出打印可交接的汇总材料。", path: "/reports" },
  { label: "系统备份", help: "创建备份、查看恢复入口。", path: "/system-tools" },
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

const summary = reactive<DashboardSummary>({
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
});

const latestImport = computed(() => summary.recent_imports[0] ?? null);
const latestBackupLabel = computed(() => formatDashboardBackupLabel(summary.latest_backup));

const statusCards = computed(() => [
  { label: "学生总数", value: summary.student_total, helpText: "当前库内学生记录，点击进入学生中心。", path: "/students" },
  { label: "教师总数", value: summary.teacher_total, helpText: "教师样本偏少会影响工作量和评教对比。", path: "/teachers" },
  { label: "考试数量", value: summary.exam_total, helpText: "已有考试批次，点击进入考试成绩页。", path: "/exams" },
  { label: "成绩记录", value: summary.score_record_total, helpText: "为 0 时不要解读成绩分析图表。", path: "/exams" },
  { label: "最近导入", value: latestImport.value ? formatImportJobType(latestImport.value.job_type) : "暂无", helpText: "查看最近导入批次和错误报告。", path: "/import-center" },
  { label: "最近备份", value: latestBackupLabel.value, helpText: "导入真实数据和恢复前建议先备份。", path: "/system-tools" },
  { label: "数据健康", value: summary.data_health?.label ?? "未检查", helpText: "查看高考数据可用性和发布状态。", path: "/gaokao-data" },
  { label: "P0 缺口", value: formatDataHealthCardValue(summary.data_health), helpText: "缺口存在时，推荐输出必须保留风险提示。", path: "/gaokao-data" },
]);

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

async function reload(): Promise<void> {
  try {
    const payload = await apiRequest<DashboardSummary>("/api/dashboard/summary");
    Object.assign(summary, payload);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function openAnalytics(): void {
  void router.push("/analytics");
}

function severityLabel(severity: "danger" | "warning" | "info"): string {
  if (severity === "danger") return "高风险";
  if (severity === "warning") return "建议处理";
  return "提醒";
}

onMounted(reload);
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 18px;
}

.metric-button {
  display: block;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.metric-button:focus-visible {
  outline: 2px solid rgba(31, 108, 152, 0.55);
  outline-offset: 4px;
}

.metric-button :deep(.metric-value) {
  overflow-wrap: anywhere;
  line-height: 1.18;
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

.next-step-card h4 {
  margin: 0;
  color: #1f3346;
  font-size: 16px;
}

.next-step-card p {
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
  border-radius: 18px;
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
  border-radius: 18px;
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
  border-radius: 18px;
  background: rgba(250, 252, 255, 0.92);
  border: 1px solid rgba(120, 138, 156, 0.14);
}

.quality-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.quality-card h4 {
  margin: 14px 0 8px;
  font-size: 16px;
}

.quality-card p {
  margin: 0;
  color: #647789;
  line-height: 1.6;
}

.quality-samples {
  display: grid;
  gap: 6px;
  margin-top: 12px;
}

.quality-samples span {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(242, 247, 252, 0.82);
  color: #5f7385;
  font-size: 12px;
}

.panel-caption {
  color: #7d8d98;
  font-size: 13px;
}

@media (max-width: 1100px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .exam-summary-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
