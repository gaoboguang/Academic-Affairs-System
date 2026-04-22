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
            <span>总分变化</span>
            <strong>{{ analytics.total_score_delta ?? "-" }}</strong>
          </div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head">
          <h2>摘要概览</h2>
        </div>
        <PrintInsightCards :cards="insightCards" />
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>分科表现</h2>
          <span>{{ analytics.subjects.length }} 科</span>
        </div>
        <table class="print-table">
          <thead>
            <tr>
              <th>科目</th>
              <th>分数</th>
              <th>班级名次</th>
              <th>年级名次</th>
              <th>班百分位</th>
              <th>年百分位</th>
              <th>分数变化</th>
              <th>名次变化</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in analytics.subjects" :key="item.subject_id">
              <td>{{ item.subject_name }}</td>
              <td>{{ item.score ?? "-" }}</td>
              <td>{{ item.class_rank ?? "-" }}</td>
              <td>{{ item.grade_rank ?? "-" }}</td>
              <td>{{ item.class_percentile ?? "-" }}</td>
              <td>{{ item.grade_percentile ?? "-" }}</td>
              <td>{{ item.score_delta ?? "-" }}</td>
              <td>{{ item.rank_delta ?? "-" }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "../api/client";
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
}

interface StudentAnalyticsResponse {
  exam_id: number;
  exam_name: string;
  student_id: number;
  student_name: string;
  total_score: number;
  class_rank: number | null;
  grade_rank: number | null;
  total_score_delta: number | null;
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
