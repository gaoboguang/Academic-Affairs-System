<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>班主任周报打印预览</strong>
        <p>建议在浏览器中选择“打印”或“另存为 PDF”。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载班主任周报...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="dashboard" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">班主任周报 / 打印预览</div>
          <h1>{{ dashboard.class_name ?? dashboard.grade_name ?? "班主任周报" }}</h1>
          <p>{{ dashboard.exam_name ?? "未选择考试" }} · {{ dashboard.start_date }} 至 {{ dashboard.end_date }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item"><span>学生数</span><strong>{{ dashboard.overview.student_count }}</strong></div>
          <div class="print-summary-item"><span>成绩样本</span><strong>{{ dashboard.overview.score_sample_count }}</strong></div>
          <div class="print-summary-item"><span>需跟进</span><strong>{{ dashboard.overview.follow_up_count }}</strong></div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head"><h2>数据概况</h2></div>
        <div class="summary-lines">
          <p>考勤：{{ formatAttendanceSummary(dashboard.attendance_summary) }}</p>
          <p>行为：{{ formatBehaviorSummary(dashboard.behavior_summary) }}</p>
          <p v-if="dashboard.data_flags.length">缺失数据：{{ dashboard.data_flags.join(" / ") }}</p>
        </div>
      </section>

      <section class="print-section">
        <div class="print-section-head"><h2>重点学生</h2><span>{{ dashboard.risk_students.length }} 人</span></div>
        <table class="print-table">
          <thead><tr><th>学生</th><th>班级</th><th>风险等级</th><th>主要原因</th><th>建议动作</th></tr></thead>
          <tbody>
            <tr v-for="item in dashboard.risk_students" :key="item.student_id">
              <td>{{ item.student_name }}</td>
              <td>{{ item.class_name ?? "-" }}</td>
              <td>{{ item.risk_label }}</td>
              <td>{{ item.primary_reason }}</td>
              <td>{{ item.suggested_action }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="print-section">
        <div class="print-section-head"><h2>行动清单</h2></div>
        <table class="print-table">
          <thead><tr><th>任务</th><th>数量</th><th>学生 ID</th></tr></thead>
          <tbody>
            <tr v-for="item in dashboard.action_items" :key="item.action_type">
              <td>{{ item.title }}</td>
              <td>{{ item.count }}</td>
              <td>{{ item.student_ids.join(" / ") || "-" }}</td>
            </tr>
          </tbody>
        </table>
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
  type AdviserDashboardResponse,
} from "../components/analytics/adviserDashboard";

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const dashboard = ref<AdviserDashboardResponse | null>(null);

function goBack(): void { window.history.back(); }
function printPage(): void { window.print(); }

async function loadPrintData(): Promise<void> {
  const classId = Number(route.params.classId);
  if (!classId) {
    errorMessage.value = "打印参数无效";
    return;
  }
  const query = new URLSearchParams({ class_id: String(classId) });
  if (typeof route.query.examId === "string") query.set("exam_id", route.query.examId);
  if (typeof route.query.startDate === "string") query.set("start_date", route.query.startDate);
  if (typeof route.query.endDate === "string") query.set("end_date", route.query.endDate);
  dashboard.value = await apiRequest<AdviserDashboardResponse>(`/api/analytics/adviser-dashboard?${query.toString()}`);
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
.print-header p, .summary-lines p { color: #62778a; line-height: 1.65; }
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
