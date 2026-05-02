<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>学生知识点补弱报告</strong>
        <p>包含本次知识点诊断、连续趋势、错因分布和任务建议。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载知识点报告...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="analytics" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">知识点补弱报告 / 学生个人</div>
          <h1>{{ analytics.student_name }}</h1>
          <p>{{ analytics.exam_name }}</p>
          <p>{{ analytics.overview_sentence }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item"><span>总分</span><strong>{{ analytics.total_score }}</strong></div>
          <div class="print-summary-item"><span>校内名次</span><strong>{{ analytics.grade_rank ?? "-" }}</strong></div>
          <div class="print-summary-item"><span>知识点</span><strong>{{ analytics.knowledge_points?.length ?? 0 }}</strong></div>
          <div class="print-summary-item"><span>连续趋势</span><strong>{{ analytics.knowledge_trends?.length ?? 0 }}</strong></div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head">
          <h2>本次薄弱知识点 Top 10</h2>
        </div>
        <table class="print-table">
          <thead>
            <tr>
              <th>科目</th>
              <th>知识路径</th>
              <th>得分率</th>
              <th>失分</th>
              <th>主错因</th>
              <th>题号</th>
              <th>建议</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in analytics.knowledge_points" :key="item.knowledge_point_id">
              <td>{{ item.subject_name }}</td>
              <td>{{ knowledgeDisplayName(item) }}</td>
              <td>{{ formatPercentValue(item.score_rate) }}</td>
              <td>{{ item.lost_score }}</td>
              <td>{{ item.dominant_error_tag || formatErrorTagStats(item.error_tag_stats) }}</td>
              <td>{{ formatQuestionNumbers(item.question_numbers) }}</td>
              <td>{{ item.suggestion }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>连续知识点趋势</h2>
        </div>
        <table class="print-table">
          <thead>
            <tr>
              <th>科目</th>
              <th>知识路径</th>
              <th>趋势标签</th>
              <th>薄弱次数</th>
              <th>最近得分率</th>
              <th>主错因</th>
              <th>轨迹</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in analytics.knowledge_trends" :key="`${item.subject_id}-${item.knowledge_point_id}`">
              <td>{{ item.subject_name }}</td>
              <td>{{ knowledgeDisplayName(item) }}</td>
              <td>{{ item.trend_label }}</td>
              <td>{{ item.weak_exam_count }} / {{ item.trend_exam_count }}</td>
              <td>{{ formatPercentValue(item.latest_score_rate) }}</td>
              <td>{{ item.dominant_error_tag || formatErrorTagStats(item.error_tag_stats) }}</td>
              <td>{{ formatKnowledgeTrendTrack(item.points) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>任务清单建议</h2>
        </div>
        <div class="print-action-grid">
          <article v-for="item in knowledgeSuggestions" :key="`${item.category}-${item.title}`">
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
  formatErrorTagStats,
  formatKnowledgeTrendTrack,
  formatPercentValue,
  formatQuestionNumbers,
  knowledgeDisplayName,
  type StudentAnalyticsReportV1,
} from "../components/analytics/studentReport";

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const analytics = ref<StudentAnalyticsReportV1 | null>(null);
const knowledgeSuggestions = computed(() =>
  (analytics.value?.action_suggestions ?? []).filter((item) =>
    ["knowledge_focus", "knowledge_trend_focus", "fix_weakness", "target_warning"].includes(item.category),
  ),
);

function goBack(): void {
  window.history.back();
}

function printPage(): void {
  window.print();
}

onMounted(async () => {
  try {
    const studentId = Number(route.params.studentId);
    const examId = Number(route.params.examId);
    if (!studentId || !examId) {
      errorMessage.value = "打印参数无效";
      return;
    }
    analytics.value = await apiRequest<StudentAnalyticsReportV1>(`/api/analytics/students/${studentId}?exam_id=${examId}`);
  } catch (error) {
    errorMessage.value = (error as Error).message;
  } finally {
    loading.value = false;
  }
});
</script>
