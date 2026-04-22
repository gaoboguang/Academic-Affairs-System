<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">工作台 / 今日概况</div>
        <h2 class="page-title">先确认最近状态，再进入具体模块</h2>
        <p class="page-subtitle">
          查看最近考试、导入记录、备份状态和数据质量提醒，避免带着问题继续做分析、推荐或报表。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>学生</strong>{{ summary.student_total }}</span>
          <span class="page-chip"><strong>教师</strong>{{ summary.teacher_total }}</span>
          <span class="page-chip"><strong>高风险问题</strong>{{ urgentIssueCount }}</span>
          <span class="page-chip"><strong>最近导入</strong>{{ latestImport ? formatImportJobType(latestImport.job_type) : "暂无" }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="router.push('/system-tools')">系统设置</el-button>
        <el-button type="primary" @click="reload">刷新概况</el-button>
      </div>
    </header>

    <section class="metric-grid">
      <MetricCard label="学生总数" :value="summary.student_total" help-text="当前库内学生记录" />
      <MetricCard label="教师总数" :value="summary.teacher_total" help-text="当前库内教师记录" />
      <MetricCard label="年级数量" :value="summary.grade_total" help-text="基础数据中启用的年级" />
      <MetricCard label="班级数量" :value="summary.class_total" help-text="基础数据中启用的班级" />
      <MetricCard label="最近备份" :value="summary.latestBackupLabel" help-text="建议在修复和恢复前先创建备份" />
    </section>

    <section class="dashboard-grid">
      <article class="soft-card panel-block">
        <div class="section-head compact">
          <div>
            <h3>最近考试</h3>
            <p>优先暴露最近一次可用考试，方便直接进入分析流程。</p>
          </div>
          <el-button v-if="summary.recent_exam" type="primary" plain @click="openAnalytics">
            进入分析中心
          </el-button>
        </div>

        <div v-if="summary.recent_exam" class="exam-summary">
          <div class="exam-summary-main">
            <strong>{{ summary.recent_exam.exam_name }}</strong>
            <span>{{ summary.recent_exam.exam_date }}</span>
            <p>建议先查看最近考试的学生、班级和教师分析结果，再决定是否进入推荐或报表。</p>
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
        <el-empty v-else description="暂无可用考试数据" />
      </article>

      <article class="soft-card panel-block">
        <div class="section-head compact">
          <div>
            <h3>快捷入口</h3>
            <p>保留常用流程入口，但不替代各页面本身的业务逻辑。</p>
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
          <h3>数据质量提醒</h3>
          <p>先修复高风险问题，再继续做分析、推荐和报表输出。</p>
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
      <el-empty v-else description="当前没有需要提醒的数据质量问题" />
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>最近导入</h3>
          <p>展示最近几次导入的类型、状态和来源文件，便于回看最近操作。</p>
        </div>
        <span class="panel-caption">最近 {{ summary.recent_imports.length }} 条</span>
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
import MetricCard from "../components/MetricCard.vue";

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
  grade_total: number;
  class_total: number;
  recent_imports: ImportJob[];
  latest_backup_time?: string | null;
  recent_exam?: RecentExam | null;
  data_quality_issues: DataQualityIssue[];
  latestBackupLabel: string;
}

const router = useRouter();

const quickActions = [
  { label: "基础数据", help: "维护学年、班级、字典和主数据。", path: "/base-data" },
  { label: "学生中心", help: "维护学生台账、导入导出和详情。", path: "/students" },
  { label: "考试成绩", help: "创建考试并导入成绩数据。", path: "/exams" },
  { label: "分析中心", help: "查看学生、班级和教师分析结果。", path: "/analytics" },
  { label: "课表工作量", help: "处理课表导入、修正和工作量计算。", path: "/workload" },
  { label: "升学推荐", help: "维护录取库并生成推荐方案。", path: "/recommendations" },
];

const importJobTypeLabels: Record<string, string> = {
  student_import: "学生导入",
  teacher_import: "教师导入",
  exam_score_import: "成绩导入",
  score_import: "成绩导入",
  timetable_import: "课表导入",
  admission_import: "录取数据导入",
  evaluation_import: "评教导入",
  archive_import: "档案导入",
};

const importStatusLabels: Record<string, string> = {
  pending: "待处理",
  processing: "处理中",
  success: "成功",
  partial_success: "部分成功",
  completed: "已完成",
  completed_with_unresolved: "待修正",
  failed: "失败",
};

const summary = reactive<DashboardSummary>({
  student_total: 0,
  teacher_total: 0,
  grade_total: 0,
  class_total: 0,
  recent_imports: [],
  latest_backup_time: null,
  recent_exam: null,
  data_quality_issues: [],
  latestBackupLabel: "未创建",
});

const latestImport = computed(() => summary.recent_imports[0] ?? null);
const urgentIssueCount = computed(
  () => summary.data_quality_issues.filter((issue) => issue.severity === "error").length,
);

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
  return importStatusLabels[status] ?? status.replace(/_/g, " ");
}

function formatImportStatusType(status: string): "success" | "warning" | "danger" | "info" {
  if (status === "success" || status === "completed") return "success";
  if (status === "partial_success" || status === "completed_with_unresolved") return "warning";
  if (status === "failed") return "danger";
  return "info";
}

async function reload(): Promise<void> {
  try {
    const payload = await apiRequest<Omit<DashboardSummary, "latestBackupLabel">>("/api/dashboard/summary");
    Object.assign(summary, payload, {
      latestBackupLabel: payload.latest_backup_time ?? "未创建",
    });
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function openAnalytics(): void {
  void router.push("/analytics");
}

onMounted(reload);
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 18px;
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
