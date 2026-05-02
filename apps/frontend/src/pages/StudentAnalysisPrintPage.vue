<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>学生成绩分析单打印预览</strong>
        <p>建议在浏览器中选择“打印”或“另存为 PDF”。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载学生分析单...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="analytics && studentMeta" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">学生成绩分析单 / 打印预览</div>
          <h1>{{ analytics.student_name }}</h1>
          <p>{{ studentMeta.student_no }} · {{ studentMeta.current_grade_name ?? "未分年级" }} {{ studentMeta.current_class_name ?? "" }}</p>
          <p>{{ analytics.exam_name }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item">
            <span>总分</span>
            <strong>{{ analytics.total_score }}</strong>
          </div>
          <div class="print-summary-item">
            <span>班级名次</span>
            <strong>{{ analytics.class_rank ?? "-" }}</strong>
          </div>
          <div class="print-summary-item">
            <span>年级名次</span>
            <strong>{{ analytics.grade_rank ?? "-" }}</strong>
          </div>
          <div class="print-summary-item">
            <span>校内PR</span>
            <strong>{{ formatPercentValue(analytics.grade_percentile) }}</strong>
          </div>
          <div class="print-summary-item">
            <span>总分变化</span>
            <strong>{{ analytics.total_score_delta ?? "-" }}</strong>
          </div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head">
          <h2>摘要概览</h2>
        </div>
        <p class="print-lead">{{ analytics.overview_sentence }}</p>
        <PrintInsightCards :cards="insightCards" />
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>学科雷达与偏科分析</h2>
          <span>{{ analytics.subjects.length }} 科</span>
        </div>
        <div class="print-radar">
          <div v-for="item in radarRows" :key="item.subject" class="print-radar-row">
            <span>{{ item.subject }}</span>
            <div><i :style="{ width: `${Math.min(100, Math.max(0, item.value))}%` }" /></div>
            <strong>{{ item.label }}</strong>
          </div>
        </div>
        <table class="print-table">
          <thead>
            <tr>
              <th>科目</th>
              <th>分数</th>
              <th>校内名次</th>
              <th>PR</th>
              <th>T分</th>
              <th>排名离差</th>
              <th>同档差距</th>
              <th>有效分差</th>
              <th>诊断</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in analytics.subjects" :key="item.subject_id">
              <td>{{ item.subject_name }}</td>
              <td>{{ item.score ?? "-" }}</td>
              <td>{{ item.grade_rank ?? "-" }}</td>
              <td>{{ formatPercentValue(item.grade_percentile) }}</td>
              <td>{{ item.t_score ?? "-" }}</td>
              <td>{{ item.rank_deviation ?? "-" }}</td>
              <td>{{ formatSignedNumber(item.peer_average_delta, "分") }}</td>
              <td>{{ formatSignedNumber(item.primary_effective_score_gap, "分") }}</td>
              <td>{{ item.diagnosis }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>进退步轨迹</h2>
          <span>近 {{ analytics.trend_points?.length ?? 0 }} 次</span>
        </div>
        <table class="print-table">
          <thead>
            <tr>
              <th>考试</th>
              <th>日期</th>
              <th>总分</th>
              <th>班级名次</th>
              <th>校内名次</th>
              <th>PR</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in analytics.trend_points" :key="item.exam_id">
              <td>{{ item.exam_name }}</td>
              <td>{{ item.exam_date }}</td>
              <td>{{ item.total_score ?? "-" }}</td>
              <td>{{ item.class_rank ?? "-" }}</td>
              <td>{{ item.grade_rank ?? "-" }}</td>
              <td>{{ formatPercentValue(item.grade_percentile) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>行动建议</h2>
        </div>
        <div class="print-action-grid">
          <article v-for="item in analytics.action_suggestions" :key="`${item.category}-${item.title}`">
            <strong>{{ item.title }}</strong>
            <p>{{ item.summary }}</p>
          </article>
        </div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "../api/client";
import {
  buildStudentRadarRows,
  formatPercentValue,
  formatSignedNumber,
} from "../components/analytics/studentReport";
import PrintInsightCards from "../components/reports/PrintInsightCards.vue";
import { buildStudentAnalysisInsightCards } from "../components/reports/reportInsights";

interface StudentSubjectAnalytics {
  subject_id: number;
  subject_name: string;
  score: number | null;
  class_rank: number | null;
  grade_rank: number | null;
  class_percentile: number | null;
  grade_percentile: number | null;
  score_delta: number | null;
  rank_delta: number | null;
  t_score?: number | null;
  rank_deviation?: number | null;
  peer_average_delta?: number | null;
  primary_effective_score_gap?: number | null;
  diagnosis?: string;
}

interface StudentAnalyticsResponse {
  exam_id: number;
  exam_name: string;
  student_id: number;
  student_name: string;
  total_score: number;
  class_rank: number | null;
  grade_rank: number | null;
  grade_percentile?: number | null;
  total_score_delta: number | null;
  overview_sentence?: string;
  trend_points?: Array<{
    exam_id: number;
    exam_name: string;
    exam_date: string;
    total_score?: number | null;
    class_rank?: number | null;
    grade_rank?: number | null;
    grade_percentile?: number | null;
  }>;
  action_suggestions?: Array<{
    category: string;
    title: string;
    summary: string;
  }>;
  subjects: StudentSubjectAnalytics[];
}

interface StudentRead {
  id: number;
  student_no: string;
  name: string;
  current_grade_name?: string | null;
  current_class_name?: string | null;
}

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const analytics = ref<StudentAnalyticsResponse | null>(null);
const studentMeta = ref<StudentRead | null>(null);
const insightCards = computed(() => (analytics.value ? buildStudentAnalysisInsightCards(analytics.value) : []));
const radarRows = computed(() => (analytics.value ? buildStudentRadarRows(analytics.value.subjects, "pr") : []));

function goBack(): void {
  window.history.back();
}

function printPage(): void {
  window.print();
}

async function loadPrintData(): Promise<void> {
  const studentId = Number(route.params.studentId);
  const examId = Number(route.params.examId);
  if (!studentId || !examId) {
    errorMessage.value = "打印参数无效";
    return;
  }

  const [analyticsPayload, studentPayload] = await Promise.all([
    apiRequest<StudentAnalyticsResponse>(`/api/analytics/students/${studentId}?exam_id=${examId}`),
    apiRequest<StudentRead>(`/api/students/${studentId}`),
  ]);
  analytics.value = analyticsPayload;
  studentMeta.value = studentPayload;
}

onMounted(async () => {
  try {
    await loadPrintData();
  } catch (error) {
    errorMessage.value = (error as Error).message;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.print-shell {
  min-height: 100vh;
  padding: 24px;
  background: #eef3f7;
  color: #1f3348;
}

.print-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  max-width: 1080px;
  margin: 0 auto 20px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(123, 141, 158, 0.14);
}

.print-toolbar p {
  margin: 6px 0 0;
  color: #6d8194;
}

.print-page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 28px;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(31, 51, 72, 0.08);
}

.print-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(124, 141, 156, 0.16);
}

.print-eyebrow {
  color: #6b8093;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.print-header h1 {
  margin: 10px 0 0;
  font-size: 32px;
}

.print-header p {
  margin: 8px 0 0;
  color: #62778a;
}

.print-summary-grid {
  display: grid;
  gap: 12px;
  min-width: 220px;
}

.print-summary-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(245, 249, 252, 0.92);
  border: 1px solid rgba(123, 141, 158, 0.12);
}

.print-summary-item span {
  color: #6e8397;
  font-size: 12px;
}

.print-summary-item strong {
  display: block;
  margin-top: 8px;
  font-size: 18px;
}

.print-section {
  margin-top: 24px;
}

.print-section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.print-section-head h2 {
  margin: 0;
  font-size: 20px;
}

.print-section-head span {
  color: #6d8194;
  font-size: 13px;
}

.print-lead {
  margin: 0 0 14px;
  color: #52687e;
  line-height: 1.7;
}

.print-radar {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 16px;
  margin-bottom: 16px;
}

.print-radar-row {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) 48px;
  align-items: center;
  gap: 10px;
  color: #52687e;
  font-size: 13px;
}

.print-radar-row div {
  height: 9px;
  overflow: hidden;
  border-radius: 999px;
  background: #e7eef5;
}

.print-radar-row i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #1f6c98;
}

.print-radar-row strong {
  color: #1f3448;
  text-align: right;
}

.print-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.print-table th,
.print-table td {
  padding: 10px 12px;
  border: 1px solid rgba(123, 141, 158, 0.2);
  text-align: left;
  vertical-align: top;
  line-height: 1.55;
}

.print-table th {
  background: rgba(243, 247, 250, 0.96);
}

.print-action-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.print-action-grid article {
  padding: 14px;
  border-radius: 12px;
  background: #f4f8fb;
  border: 1px solid rgba(123, 141, 158, 0.16);
}

.print-action-grid p {
  margin: 8px 0 0;
  color: #52687e;
  line-height: 1.6;
}

.print-placeholder {
  max-width: 1080px;
  margin: 0 auto;
  color: #6d8194;
  line-height: 1.7;
}

.print-placeholder.danger {
  color: #b24b3b;
}

@media print {
  .print-shell {
    padding: 0;
    background: #ffffff;
  }

  .print-toolbar {
    display: none;
  }

  .print-page {
    max-width: none;
    margin: 0;
    padding: 0;
    border-radius: 0;
    box-shadow: none;
  }
}
</style>
