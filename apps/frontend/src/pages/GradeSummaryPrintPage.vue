<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>年级汇总表打印预览</strong>
        <p>建议在浏览器中选择“打印”或“另存为 PDF”。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载年级汇总表...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="analytics" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">年级汇总表 / 打印预览</div>
          <h1>{{ analytics.grade_name }}</h1>
          <p>{{ analytics.exam_name }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item"><span>学生数</span><strong>{{ analytics.student_count }}</strong></div>
          <div class="print-summary-item"><span>年级均分</span><strong>{{ analytics.total_average }}</strong></div>
          <div class="print-summary-item"><span>年级中位数</span><strong>{{ analytics.total_median }}</strong></div>
          <div class="print-summary-item"><span>优秀率</span><strong>{{ analytics.excellent_rate ?? "-" }}</strong></div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head"><h2>摘要概览</h2></div>
        <PrintInsightCards :cards="insightCards" />
      </section>

      <section class="print-section">
        <div class="print-section-head"><h2>班级横向对比</h2><span>{{ analytics.class_breakdown.length }} 个班级</span></div>
        <table class="print-table">
          <thead><tr><th>班级</th><th>人数</th><th>均分</th><th>中位数</th><th>最高分</th><th>最低分</th><th>优秀率</th></tr></thead>
          <tbody>
            <tr v-for="item in analytics.class_breakdown" :key="item.class_id ?? item.class_name">
              <td>{{ item.class_name }}</td><td>{{ item.student_count }}</td><td>{{ item.average_score }}</td><td>{{ item.median_score }}</td><td>{{ item.max_score }}</td><td>{{ item.min_score }}</td><td>{{ item.excellent_rate ?? "-" }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="print-section">
        <div class="print-section-head"><h2>学科横向对比</h2><span>{{ analytics.subject_breakdown.length }} 科</span></div>
        <table class="print-table">
          <thead><tr><th>学科</th><th>均分</th><th>优秀率</th><th>及格率</th><th>贡献度</th></tr></thead>
          <tbody>
            <tr v-for="item in analytics.subject_breakdown" :key="item.subject_id">
              <td>{{ item.subject_name }}</td><td>{{ item.average_score }}</td><td>{{ item.excellent_rate }}</td><td>{{ item.pass_rate }}</td><td>{{ item.contribution_rate ?? "-" }}</td>
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
import { buildGradeAnalysisInsightCards } from "../components/reports/reportInsights";

interface GradeClassAnalyticsItem { class_id: number | null; class_name: string; student_count: number; average_score: number; median_score: number; max_score: number; min_score: number; excellent_rate: number | null; }
interface GradeSubjectAnalyticsItem { subject_id: number; subject_name: string; average_score: number; excellent_rate: number; pass_rate: number; contribution_rate: number | null; }
interface GradeAnalyticsResponse { exam_name: string; grade_name: string; student_count: number; total_average: number; total_median: number; excellent_rate: number | null; class_breakdown: GradeClassAnalyticsItem[]; subject_breakdown: GradeSubjectAnalyticsItem[]; }

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const analytics = ref<GradeAnalyticsResponse | null>(null);
const insightCards = computed(() => (analytics.value ? buildGradeAnalysisInsightCards(analytics.value) : []));

function goBack(): void { window.history.back(); }
function printPage(): void { window.print(); }

async function loadPrintData(): Promise<void> {
  const gradeId = Number(route.params.gradeId);
  const examId = Number(route.params.examId);
  if (!gradeId || !examId) {
    errorMessage.value = "打印参数无效";
    return;
  }
  analytics.value = await apiRequest<GradeAnalyticsResponse>(`/api/analytics/grades/${gradeId}?exam_id=${examId}`);
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
