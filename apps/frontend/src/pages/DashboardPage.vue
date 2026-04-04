<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">工作台 / 今日概况</div>
        <h2 class="page-title">先处理关键状态，再进入具体模块</h2>
        <p class="page-subtitle">
          先看最近考试、导入和数据质量，再进入成绩、工作量、推荐与备份等高频流程。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>学生</strong>{{ summary.student_total }}</span>
          <span class="page-chip"><strong>教师</strong>{{ summary.teacher_total }}</span>
          <span class="page-chip"><strong>高风险问题</strong>{{ urgentIssueCount }}</span>
          <span class="page-chip"><strong>最近导入</strong>{{ latestImport?.job_type ?? "暂无" }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="router.push('/system-tools')">进入系统设置</el-button>
        <el-button type="primary" @click="reload">刷新概况</el-button>
      </div>
    </header>

    <section class="dashboard-command-grid">
      <article class="soft-card command-panel command-panel-primary">
        <div class="panel-kicker">当前焦点</div>
        <div class="section-head compact">
          <div>
            <h3>最近考试摘要</h3>
            <p v-if="summary.recent_exam">
              {{ summary.recent_exam.exam_date }} · {{ summary.recent_exam.participant_count }} 人参与
            </p>
            <p v-else>暂无已发布考试数据</p>
          </div>
          <el-button v-if="summary.recent_exam" type="primary" plain @click="openAnalytics">
            进入分析中心
          </el-button>
        </div>

        <div v-if="summary.recent_exam" class="exam-hero">
          <div class="exam-hero-copy">
            <h3>{{ summary.recent_exam.exam_name }}</h3>
            <p>工作台优先暴露最近一次有效考试，方便直接进入年级、班级和教师分析。</p>
          </div>
          <div class="exam-metrics">
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
        <div v-else class="empty-hint">
          <strong>还没有可用考试摘要</strong>
          <p>先创建考试并导入成绩，工作台会自动展示最近一次考试的参与人数、均分与优秀率。</p>
        </div>
      </article>

      <article class="soft-card command-panel">
        <div class="section-head compact">
          <div>
            <div class="panel-kicker">状态提醒</div>
            <h3>先修风险，再跑分析</h3>
            <p>避免错误数据一路传到推荐、报表和工作量结果里。</p>
          </div>
        </div>
        <div class="pulse-grid">
          <article
            v-for="item in dashboardPulseCards"
            :key="item.label"
            class="pulse-card"
            :class="item.tone"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <p>{{ item.help }}</p>
          </article>
        </div>
      </article>

      <article class="soft-card command-panel quick-panel">
        <div class="section-head compact">
          <div>
            <div class="panel-kicker">快捷入口</div>
            <h3>高频动作直接到达</h3>
            <p>保留“先维护数据，再跑计算”的路径顺序，不让首页变成纯导航列表。</p>
          </div>
        </div>
        <div class="quick-grid">
          <button
            v-for="item in quickActions"
            :key="item.label"
            type="button"
            class="quick-action"
            :class="item.tone"
            @click="router.push(item.path)"
          >
            <span class="quick-kicker">{{ item.kicker }}</span>
            <strong>{{ item.label }}</strong>
            <span>{{ item.help }}</span>
          </button>
        </div>
      </article>
    </section>

    <section class="metric-grid">
      <MetricCard label="学生总数" :value="summary.student_total" help-text="当前库内学生记录" />
      <MetricCard label="教师总数" :value="summary.teacher_total" help-text="当前库内教师记录" />
      <MetricCard label="年级数量" :value="summary.grade_total" help-text="基础数据中启用的年级" />
      <MetricCard label="班级数量" :value="summary.class_total" help-text="基础数据中启用的班级" />
      <MetricCard label="最近备份" :value="summary.latest_backup_time ?? '-'" help-text="最近一次备份包文件名" />
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>数据质量提醒</h3>
          <p>先修数据，再跑分析和报表，避免错误被扩散到推荐和工作量结果里。</p>
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
          <p>学生、成绩、课表、录取库等导入批次都会汇总到这里。</p>
        </div>
        <span class="panel-caption">最近 {{ summary.recent_imports.length }} 条</span>
      </div>
      <div class="table-shell">
        <el-table :data="summary.recent_imports" stripe>
          <el-table-column label="批次 ID" prop="id" width="90" />
          <el-table-column label="类型" prop="job_type" />
          <el-table-column label="来源文件" prop="source_filename" min-width="180" />
          <el-table-column label="状态" prop="status" />
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
}

const router = useRouter();
const quickActions = [
  { label: "新增考试", help: "进入考试配置与科目维护", path: "/exams", kicker: "考试入口", tone: "tone-blue" },
  { label: "导入成绩", help: "考试建好后直接导入分数", path: "/exams", kicker: "数据导入", tone: "tone-slate" },
  { label: "计算工作量", help: "跳到课表与工作量闭环", path: "/workload", kicker: "教师流程", tone: "tone-amber" },
  { label: "生成推荐", help: "进入升学推荐中心", path: "/recommendations", kicker: "升学决策", tone: "tone-blue" },
  { label: "创建备份", help: "进入系统设置创建本地备份", path: "/system-tools", kicker: "安全操作", tone: "tone-slate" },
];

const summary = reactive<DashboardSummary>({
  student_total: 0,
  teacher_total: 0,
  grade_total: 0,
  class_total: 0,
  recent_imports: [],
  latest_backup_time: null,
  recent_exam: null,
  data_quality_issues: [],
});

const latestImport = computed(() => summary.recent_imports[0] ?? null);
const urgentIssueCount = computed(
  () => summary.data_quality_issues.filter((issue) => issue.severity === "error").length,
);
const warningIssueCount = computed(
  () => summary.data_quality_issues.filter((issue) => issue.severity !== "error").length,
);

const dashboardPulseCards = computed(() => [
  {
    label: "高风险问题",
    value: urgentIssueCount.value,
    help: urgentIssueCount.value ? "建议先在系统设置里修复，再继续分析。" : "当前没有高风险数据问题。",
    tone: "tone-danger",
  },
  {
    label: "一般提醒",
    value: warningIssueCount.value,
    help: warningIssueCount.value ? "这些问题不会阻塞流程，但会影响结果解释。" : "当前没有需要补看的提醒。",
    tone: "tone-slate",
  },
  {
    label: "最近导入",
    value: latestImport.value?.job_type ?? "暂无",
    help: latestImport.value
      ? `${latestImport.value.status} · ${latestImport.value.source_filename ?? "未记录来源文件"}`
      : "还没有导入批次记录。",
    tone: "tone-blue",
  },
]);

function formatNumber(value?: number | null): string {
  if (value === null || value === undefined) return "-";
  return value.toFixed(2);
}

function formatPercent(value?: number | null): string {
  if (value === null || value === undefined) return "-";
  return `${value.toFixed(2)}%`;
}

async function reload(): Promise<void> {
  try {
    Object.assign(summary, await apiRequest<DashboardSummary>("/api/dashboard/summary"));
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function openAnalytics(): void {
  router.push("/analytics");
}

onMounted(reload);
</script>

<style scoped>
.dashboard-command-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 18px;
}

.command-panel {
  padding: 24px;
}

.command-panel-primary {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(180, 219, 243, 0.34), transparent 30%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(244, 248, 252, 0.94));
}

.command-panel-primary::after {
  content: "";
  position: absolute;
  inset: auto 24px 0;
  height: 1px;
  background: linear-gradient(90deg, rgba(31, 108, 152, 0.18), rgba(209, 141, 72, 0.18), transparent);
}

.quick-panel {
  grid-column: 1 / -1;
}

.panel-kicker {
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

.exam-hero {
  display: grid;
  gap: 20px;
}

.exam-hero-copy h3 {
  margin: 0;
  color: #1d3347;
  font-size: 28px;
}

.exam-hero-copy p {
  margin: 10px 0 0;
  color: #5f768a;
  line-height: 1.7;
}

.exam-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.exam-metric {
  padding: 18px;
  border-radius: 20px;
  background: rgba(244, 248, 252, 0.8);
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

.empty-hint {
  padding: 20px;
  border-radius: 22px;
  border: 1px dashed rgba(123, 142, 161, 0.26);
  background: rgba(247, 250, 253, 0.88);
}

.empty-hint strong {
  display: block;
  color: #20364b;
}

.empty-hint p {
  margin: 8px 0 0;
  color: #687f93;
  line-height: 1.6;
}

.pulse-grid {
  display: grid;
  gap: 12px;
}

.pulse-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(248, 251, 254, 0.94);
  border: 1px solid rgba(123, 142, 161, 0.12);
}

.pulse-card span {
  color: #698095;
  font-size: 13px;
}

.pulse-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3448;
  font-size: 26px;
  font-weight: 760;
}

.pulse-card p {
  margin: 8px 0 0;
  color: #71869a;
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

.tone-danger {
  box-shadow: inset 0 4px 0 rgba(196, 87, 70, 0.82);
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 12px;
}

.quick-action {
  padding: 18px;
  border: 1px solid rgba(114, 132, 150, 0.14);
  border-radius: 20px;
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

.quick-kicker {
  display: inline-flex;
  margin-bottom: 10px;
  color: #6c8296;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.quick-action strong {
  display: block;
  color: #213344;
  font-size: 16px;
}

.quick-action span:last-child {
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
  border-radius: 20px;
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
  margin-top: 14px;
}

.quality-samples span {
  color: #53677b;
  font-size: 13px;
}

.panel-caption {
  color: #6c8094;
  font-size: 13px;
}

@media (max-width: 1080px) {
  .dashboard-command-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .exam-metrics,
  .quick-grid {
    grid-template-columns: 1fr;
  }
}
</style>
