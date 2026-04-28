<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>学生升学规划跟进表</strong>
        <p>建议在浏览器中选择“打印”或“另存为 PDF”。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载升学规划...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="planning" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">升学规划 / 打印预览</div>
          <h1>{{ planning.student.name }}</h1>
          <p>{{ planning.student.student_no }} · {{ planning.student.grade_name ?? "未分年级" }} {{ planning.student.class_name ?? "" }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item"><span>目标路径</span><strong>{{ planning.goals.length }}</strong></div>
          <div class="print-summary-item"><span>进行中任务</span><strong>{{ planning.summary.open_task_count }}</strong></div>
          <div class="print-summary-item"><span>逾期任务</span><strong>{{ planning.summary.overdue_task_count }}</strong></div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head"><h2>目标路径</h2></div>
        <table class="print-table">
          <thead><tr><th>路径</th><th>目标</th><th>状态</th><th>备注</th></tr></thead>
          <tbody>
            <tr v-for="goal in planning.goals" :key="goal.id">
              <td>{{ goal.pathway_name }}</td>
              <td>{{ goal.target_college || "-" }} / {{ goal.target_major || "-" }}</td>
              <td>{{ goal.status_label }} / {{ goal.priority_label }}</td>
              <td>{{ goal.note || goal.backup_pathways || "-" }}</td>
            </tr>
            <tr v-if="!planning.goals.length"><td colspan="4">暂无目标路径</td></tr>
          </tbody>
        </table>
      </section>

      <section class="print-section">
        <div class="print-section-head"><h2>任务清单</h2></div>
        <table class="print-table">
          <thead><tr><th>任务</th><th>类型</th><th>状态</th><th>截止</th></tr></thead>
          <tbody>
            <tr v-for="task in planning.tasks" :key="task.id ?? task.title">
              <td>{{ task.title }}<br><span>{{ task.description || "" }}</span></td>
              <td>{{ task.task_type_label }}</td>
              <td>{{ task.status_label }} / {{ task.priority_label }}</td>
              <td>{{ task.due_date || "-" }}<span v-if="task.is_overdue">（逾期）</span></td>
            </tr>
            <tr v-if="!planning.tasks.length"><td colspan="4">暂无规划任务</td></tr>
          </tbody>
        </table>
      </section>

      <section class="print-section">
        <div class="print-section-head"><h2>路径初筛与材料缺口</h2></div>
        <div class="summary-lines">
          <p v-for="item in planning.pathway_evaluations.slice(0, 8)" :key="item.pathway_id">
            {{ item.pathway_name }}：{{ item.status_label }}；缺口：
            {{ formatMissingMaterials(item.missing_materials_json) }}
          </p>
          <p v-if="!planning.pathway_evaluations.length">暂无已保存的路径评估，可先在升学画像中刷新评估。</p>
        </div>
      </section>

      <section class="print-section">
        <div class="print-section-head"><h2>复盘记录</h2></div>
        <div class="summary-lines">
          <p v-for="note in planning.notes" :key="note.id">{{ note.created_at || "-" }} · {{ note.note_type_label }}：{{ note.content }}</p>
          <p v-if="!planning.notes.length">暂无复盘记录。</p>
        </div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "../api/client";
import type { PlanningGoal, PlanningSummary, PlanningTask } from "../components/planning/studentPlanning";

interface PlanningStudent {
  id: number;
  student_no: string;
  name: string;
  grade_name?: string | null;
  class_name?: string | null;
}

interface PlanningNote {
  id: number;
  note_type_label: string;
  content: string;
  created_at?: string | null;
}

interface PathwayEvaluation {
  pathway_id: number;
  pathway_name?: string | null;
  status_label: string;
  missing_materials_json: Array<{ material_label?: string; material_key?: string }>;
}

interface StudentPlanningResponse {
  student: PlanningStudent;
  goals: PlanningGoal[];
  tasks: PlanningTask[];
  notes: PlanningNote[];
  pathway_evaluations: PathwayEvaluation[];
  summary: PlanningSummary;
}

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const planning = ref<StudentPlanningResponse | null>(null);

function goBack(): void { window.history.back(); }
function printPage(): void { window.print(); }

function formatMissingMaterials(items: PathwayEvaluation["missing_materials_json"]): string {
  if (!items.length) return "暂无系统识别缺口";
  return items.map((item) => item.material_label || item.material_key || "材料").join(" / ");
}

async function loadPrintData(): Promise<void> {
  const studentId = Number(route.params.studentId);
  if (!studentId) {
    errorMessage.value = "打印参数无效";
    return;
  }
  planning.value = await apiRequest<StudentPlanningResponse>(`/api/planning/students/${studentId}?target_year=2026`);
}

onMounted(async () => {
  try { await loadPrintData(); } catch (error) { errorMessage.value = (error as Error).message; } finally { loading.value = false; }
});
</script>

<style scoped>
.print-shell { min-height: 100vh; padding: 24px; background: #eef3f7; color: #1f3348; }
.print-toolbar { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; max-width: 980px; margin: 0 auto 20px; padding: 16px 18px; border-radius: 18px; background: rgba(255,255,255,.92); border: 1px solid rgba(123,141,158,.14); }
.print-toolbar p { margin: 6px 0 0; color: #6d8194; }
.print-page { max-width: 980px; margin: 0 auto; padding: 28px; background: #fff; border-radius: 24px; box-shadow: 0 18px 40px rgba(31,51,72,.08); }
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
.print-table th { background: rgba(243,247,250,.96); }
.print-table span { color: #6d8194; }
.print-placeholder { max-width: 980px; margin: 0 auto; color: #6d8194; line-height: 1.7; }
.print-placeholder.danger { color: #b24b3b; }
@media print { .print-shell { padding: 0; background: #fff; } .print-toolbar { display: none; } .print-page { max-width: none; margin: 0; padding: 0; border-radius: 0; box-shadow: none; } }
</style>
