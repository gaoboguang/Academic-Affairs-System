<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>教师任教分析报表打印预览</strong>
        <p>建议在浏览器中选择“打印”或“另存为 PDF”。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载教师分析报表...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="analytics" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">教师任教分析报表 / 打印预览</div>
          <h1>{{ analytics.teacher_name }}</h1>
          <p>{{ analytics.exam_name }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item"><span>教师均分</span><strong>{{ analytics.overall_average ?? "-" }}</strong></div>
          <div class="print-summary-item"><span>任教拆分</span><strong>{{ analytics.assignment_breakdown.length }}</strong></div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head"><h2>摘要概览</h2></div>
        <PrintInsightCards :cards="insightCards" />
      </section>

      <section class="print-section">
        <div class="print-section-head"><h2>任教拆分</h2><span>{{ analytics.assignment_breakdown.length }} 条</span></div>
        <table class="print-table">
          <thead><tr><th>班级</th><th>学科</th><th>均分</th><th>优秀率</th><th>及格率</th><th>有效人数</th></tr></thead>
          <tbody>
            <tr v-for="item in analytics.assignment_breakdown" :key="item.assignment_id">
              <td>{{ item.class_name ?? "-" }}</td><td>{{ item.subject_name ?? "-" }}</td><td>{{ item.average_score }}</td><td>{{ item.excellent_rate }}</td><td>{{ item.pass_rate }}</td><td>{{ item.valid_count }}</td>
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
import { buildTeacherAnalysisInsightCards } from "../components/reports/reportInsights";

interface TeacherAssignmentAnalytics { assignment_id: number; class_name: string | null; subject_name: string | null; average_score: number; excellent_rate: number; pass_rate: number; valid_count: number; }
interface TeacherAnalyticsResponse { exam_name: string; teacher_name: string; overall_average: number | null; assignment_breakdown: TeacherAssignmentAnalytics[]; }

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const analytics = ref<TeacherAnalyticsResponse | null>(null);
const insightCards = computed(() => (analytics.value ? buildTeacherAnalysisInsightCards(analytics.value) : []));

function goBack(): void { window.history.back(); }
function printPage(): void { window.print(); }

async function loadPrintData(): Promise<void> {
  const teacherId = Number(route.params.teacherId);
  const examId = Number(route.params.examId);
  if (!teacherId || !examId) {
    errorMessage.value = "打印参数无效";
    return;
  }
  analytics.value = await apiRequest<TeacherAnalyticsResponse>(`/api/analytics/teachers/${teacherId}?exam_id=${examId}`);
}

onMounted(async () => {
  try { await loadPrintData(); } catch (error) { errorMessage.value = (error as Error).message; } finally { loading.value = false; }
});
</script>

<style scoped>
.print-shell { min-height: 100vh; padding: 24px; background: #eef3f7; color: #1f3348; }
.print-toolbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; max-width: 1080px; margin: 0 auto 20px; padding: 16px 18px; border-radius: 18px; background: rgba(255,255,255,.92); border: 1px solid rgba(123,141,158,.14); }
.print-toolbar p { margin: 6px 0 0; color: #6d8194; }
.print-page { max-width: 1080px; margin: 0 auto; padding: 28px; background: #fff; border-radius: 24px; box-shadow: 0 18px 40px rgba(31,51,72,.08); }
.print-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid rgba(124,141,156,.16); }
.print-eyebrow { color: #6b8093; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; }
.print-header h1 { margin: 10px 0 0; font-size: 32px; }
.print-header p { margin: 8px 0 0; color: #62778a; }
.print-summary-grid { display: grid; gap: 12px; min-width: 220px; }
.print-summary-item { padding: 14px 16px; border-radius: 16px; background: rgba(245,249,252,.92); border: 1px solid rgba(123,141,158,.12); }
.print-summary-item span { color: #6e8397; font-size: 12px; }
.print-summary-item strong { display: block; margin-top: 8px; font-size: 18px; }
.print-section { margin-top: 24px; }
.print-section-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.print-section-head h2 { margin: 0; font-size: 20px; }
.print-section-head span { color: #6d8194; font-size: 13px; }
.print-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.print-table th, .print-table td { padding: 10px 12px; border: 1px solid rgba(123,141,158,.2); text-align: left; vertical-align: top; line-height: 1.55; }
.print-table th { background: rgba(243,247,250,.96); }
.print-placeholder { max-width: 1080px; margin: 0 auto; color: #6d8194; line-height: 1.7; }
.print-placeholder.danger { color: #b24b3b; }
@media print { .print-shell { padding: 0; background: #fff; } .print-toolbar { display: none; } .print-page { max-width: none; margin: 0; padding: 0; border-radius: 0; box-shadow: none; } }
</style>
