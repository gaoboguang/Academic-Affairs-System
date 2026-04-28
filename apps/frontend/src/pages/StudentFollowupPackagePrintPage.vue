<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>学生跟进包打印预览</strong>
        <p>建议在浏览器中选择“打印”或“另存为 PDF”。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载学生跟进包...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="risk" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">学生跟进包 / 打印预览</div>
          <h1>{{ risk.student_name }}</h1>
          <p>{{ risk.student_no }} · {{ risk.grade_name ?? "未分年级" }} {{ risk.class_name ?? "" }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item"><span>风险等级</span><strong>{{ risk.risk_label }}</strong></div>
          <div class="print-summary-item"><span>考勤记录</span><strong>{{ risk.attendance_summary.total_records }}</strong></div>
          <div class="print-summary-item"><span>行为记录</span><strong>{{ risk.behavior_summary.total_records }}</strong></div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head"><h2>跟进摘要</h2></div>
        <div class="summary-lines">
          <p>主要原因：{{ risk.reasons.join(" / ") }}</p>
          <p>建议行动：{{ risk.suggested_actions.join(" / ") }}</p>
          <p v-if="risk.data_flags.length">缺失数据：{{ risk.data_flags.join(" / ") }}</p>
        </div>
      </section>

      <section class="print-section">
        <div class="print-section-head"><h2>成绩趋势</h2></div>
        <table class="print-table">
          <tbody>
            <tr><th>考试</th><td>{{ risk.score_summary.exam_name ?? "-" }}</td></tr>
            <tr><th>总分</th><td>{{ risk.score_summary.total_score ?? "-" }}</td></tr>
            <tr><th>上次总分</th><td>{{ risk.score_summary.previous_total_score ?? "-" }}</td></tr>
            <tr><th>变化</th><td>{{ risk.score_summary.total_score_delta ?? "-" }}</td></tr>
            <tr><th>班级/年级名次</th><td>{{ risk.score_summary.class_rank ?? "-" }} / {{ risk.score_summary.grade_rank ?? "-" }}</td></tr>
          </tbody>
        </table>
      </section>

      <section class="print-section">
        <div class="print-section-head"><h2>考勤与行为</h2></div>
        <div class="summary-lines">
          <p>考勤：{{ formatAttendanceSummary(risk.attendance_summary) }}</p>
          <p>行为：{{ formatBehaviorSummary(risk.behavior_summary) }}</p>
          <p>成长档案：{{ risk.growth_summary.record_count }} 条，最近记录 {{ risk.growth_summary.latest_record_date ?? "-" }}</p>
        </div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "../api/client";
import {
  formatAttendanceSummary,
  formatBehaviorSummary,
  type AttendanceRiskSummary,
  type BehaviorRiskSummary,
} from "../components/analytics/adviserDashboard";

interface StudentRiskResponse {
  student_name: string;
  student_no?: string | null;
  grade_name?: string | null;
  class_name?: string | null;
  risk_label: string;
  reasons: string[];
  suggested_actions: string[];
  data_flags: string[];
  score_summary: {
    exam_name?: string | null;
    total_score?: number | null;
    previous_total_score?: number | null;
    total_score_delta?: number | null;
    class_rank?: number | null;
    grade_rank?: number | null;
  };
  attendance_summary: AttendanceRiskSummary;
  behavior_summary: BehaviorRiskSummary;
  growth_summary: {
    record_count: number;
    latest_record_date?: string | null;
  };
}

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const risk = ref<StudentRiskResponse | null>(null);

function goBack(): void { window.history.back(); }
function printPage(): void { window.print(); }

async function loadPrintData(): Promise<void> {
  const studentId = Number(route.params.studentId);
  if (!studentId) {
    errorMessage.value = "打印参数无效";
    return;
  }
  const query = new URLSearchParams();
  if (typeof route.query.examId === "string") query.set("exam_id", route.query.examId);
  if (typeof route.query.startDate === "string") query.set("start_date", route.query.startDate);
  if (typeof route.query.endDate === "string") query.set("end_date", route.query.endDate);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  risk.value = await apiRequest<StudentRiskResponse>(`/api/analytics/student-risk/${studentId}${suffix}`);
}

onMounted(async () => {
  try { await loadPrintData(); } catch (error) { errorMessage.value = (error as Error).message; } finally { loading.value = false; }
});
</script>

<style scoped>
.print-shell { min-height: 100vh; padding: 24px; background: #eef3f7; color: #1f3348; }
.print-toolbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; max-width: 960px; margin: 0 auto 20px; padding: 16px 18px; border-radius: 18px; background: rgba(255,255,255,.92); border: 1px solid rgba(123,141,158,.14); }
.print-toolbar p { margin: 6px 0 0; color: #6d8194; }
.print-page { max-width: 960px; margin: 0 auto; padding: 28px; background: #fff; border-radius: 24px; box-shadow: 0 18px 40px rgba(31,51,72,.08); }
.print-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid rgba(124,141,156,.16); }
.print-eyebrow { color: #6b8093; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; }
.print-header h1 { margin: 10px 0 0; font-size: 32px; }
.print-header p, .summary-lines p { color: #62778a; line-height: 1.65; }
.print-summary-grid { display: grid; gap: 12px; min-width: 220px; }
.print-summary-item { padding: 14px 16px; border-radius: 16px; background: rgba(245,249,252,.92); border: 1px solid rgba(123,141,158,.12); }
.print-summary-item span { color: #6e8397; font-size: 12px; }
.print-summary-item strong { display: block; margin-top: 8px; font-size: 18px; }
.print-section { margin-top: 24px; }
.print-section-head { margin-bottom: 12px; }
.print-section-head h2 { margin: 0; font-size: 20px; }
.print-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.print-table th, .print-table td { padding: 10px 12px; border: 1px solid rgba(123,141,158,.2); text-align: left; vertical-align: top; line-height: 1.55; }
.print-table th { width: 160px; background: rgba(243,247,250,.96); }
.print-placeholder { max-width: 960px; margin: 0 auto; color: #6d8194; line-height: 1.7; }
.print-placeholder.danger { color: #b24b3b; }
@media print { .print-shell { padding: 0; background: #fff; } .print-toolbar { display: none; } .print-page { max-width: none; margin: 0; padding: 0; border-radius: 0; box-shadow: none; } }
</style>
