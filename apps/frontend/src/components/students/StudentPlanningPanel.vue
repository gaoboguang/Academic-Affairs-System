<template>
  <section class="student-planning-panel" v-loading="loading">
    <div class="section-head">
      <div>
        <h3>升学规划</h3>
        <p>把目标路径、材料缺口、志愿复核和阶段复盘收成一条可跟进清单。</p>
      </div>
      <div class="action-row">
        <el-button :loading="generatingTasks" @click="generateTasksFromPathway">从升学方案生成任务</el-button>
        <el-button :loading="exporting" @click="exportPlanningFollowup">导出跟进表</el-button>
        <el-button type="primary" @click="reload">刷新规划</el-button>
      </div>
    </div>

    <el-alert
      v-if="errorMessage"
      class="planning-alert"
      type="error"
      show-icon
      :closable="false"
      :title="errorMessage"
    />

    <div class="planning-summary-grid">
      <div class="planning-summary-item">
        <span>目标路径</span>
        <strong>{{ planning?.goals.length ?? 0 }}</strong>
      </div>
      <div class="planning-summary-item">
        <span>进行中任务</span>
        <strong>{{ planning?.summary.open_task_count ?? 0 }}</strong>
      </div>
      <div class="planning-summary-item" :class="{ warning: Boolean(planning?.summary.overdue_task_count) }">
        <span>逾期任务</span>
        <strong>{{ planning?.summary.overdue_task_count ?? 0 }}</strong>
      </div>
      <div class="planning-summary-item">
        <span>材料任务</span>
        <strong>{{ planning?.summary.material_gap_task_count ?? 0 }}</strong>
      </div>
    </div>

    <div class="planning-layout">
      <section class="planning-block">
        <div class="section-head compact">
          <div>
            <h3>目标路径</h3>
            <p>先定路径，再拆任务。一个学生可以保留主路径和备选路径。</p>
          </div>
        </div>
        <div class="planning-form-grid">
          <el-select v-model="goalForm.pathway_code" filterable placeholder="目标路径" @change="syncPathwayName">
            <el-option label="普通类常规批" value="summer_general_regular" />
            <el-option label="春季高考" value="spring_exam" />
            <el-option label="综合评价" value="vocational_comprehensive" />
            <el-option label="高职单招" value="vocational_single_exam" />
            <el-option label="艺体路径" value="art_sports" />
            <el-option label="提前批" value="early_batch" />
          </el-select>
          <el-input-number v-model="goalForm.target_year" :min="2020" :max="2100" />
          <el-input v-model="goalForm.target_college" placeholder="目标院校，可选" />
          <el-input v-model="goalForm.target_major" placeholder="目标专业方向，可选" />
          <el-input-number v-model="goalForm.target_score" :min="0" :max="750" placeholder="目标分数" />
          <el-input-number v-model="goalForm.target_rank" :min="1" placeholder="目标位次" />
          <el-input v-model="goalForm.backup_pathways" placeholder="备选路径，如春考/综评" />
          <el-button type="primary" :loading="savingGoal" @click="saveGoal">保存目标</el-button>
        </div>
        <div class="planning-row-list">
          <article v-for="goal in planning?.goals ?? []" :key="goal.id" class="planning-row">
            <div>
              <strong>{{ goal.pathway_name }}</strong>
              <p>
                {{ goal.target_year }} · {{ goal.target_college || "未设院校" }} ·
                {{ goal.target_major || "未设专业" }}
              </p>
            </div>
            <el-tag effect="light">{{ goal.status_label }}</el-tag>
          </article>
          <el-empty v-if="planning && !planning.goals.length" description="暂无升学目标，请先保存一个目标路径。" />
        </div>
      </section>

      <section class="planning-block">
        <div class="section-head compact">
          <div>
            <h3>新增任务</h3>
            <p>用于手工补充家校沟通、成绩复核、章程核对或阶段复盘。</p>
          </div>
        </div>
        <div class="planning-form-grid task-form">
          <el-select v-model="taskForm.task_type" placeholder="任务类型">
            <el-option label="材料补齐" value="material" />
            <el-option label="成绩复核" value="score_review" />
            <el-option label="志愿草稿" value="volunteer_draft" />
            <el-option label="章程核对" value="chapter_review" />
            <el-option label="家校沟通" value="family_contact" />
            <el-option label="阶段复盘" value="stage_review" />
          </el-select>
          <el-input v-model="taskForm.title" placeholder="任务标题" />
          <el-select v-model="taskForm.priority" placeholder="优先级">
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
          <el-date-picker v-model="taskForm.due_date" value-format="YYYY-MM-DD" placeholder="截止日期，可选" />
          <el-input v-model="taskForm.description" class="wide-field" placeholder="任务说明，可选" />
          <el-button type="primary" :loading="savingTask" @click="saveTask">新增任务</el-button>
        </div>
      </section>
    </div>

    <section class="planning-block">
      <div class="section-head compact">
        <div>
          <h3>任务清单</h3>
          <p>逾期、待复核和高优先级任务会排在前面。</p>
        </div>
      </div>
      <div class="table-shell compact-table">
        <el-table :data="sortedTasks" stripe>
          <el-table-column label="任务" min-width="260">
            <template #default="{ row }">
              <strong>{{ row.title }}</strong>
              <p class="table-subcopy">{{ row.description || "无补充说明" }}</p>
            </template>
          </el-table-column>
          <el-table-column label="类型" prop="task_type_label" width="110" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="taskStatusTagType(row.status)" effect="light">{{ row.status_label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="优先级" prop="priority_label" width="90" />
          <el-table-column label="截止日期" width="120">
            <template #default="{ row }">
              <span :class="{ overdue: row.is_overdue }">{{ row.due_date || "-" }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="210" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.related_route" link type="primary" @click="router.push(row.related_route)">查看</el-button>
              <el-button v-if="row.status !== 'completed'" link type="success" @click="completeTask(row.id)">完成</el-button>
              <el-button v-if="row.status !== 'review'" link @click="markTaskReview(row.id)">待复核</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-if="planning && !planning.tasks.length" description="暂无规划任务，可从升学方案或手工新增。" />
    </section>

    <section class="planning-bottom-grid">
      <div class="planning-block">
        <div class="section-head compact">
          <div>
            <h3>系统建议</h3>
            <p>根据画像、路径缺口和现有任务生成，供你一键转成正式任务。</p>
          </div>
        </div>
        <div class="planning-row-list">
          <article v-for="item in planning?.suggested_tasks ?? []" :key="item.title" class="planning-row">
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.description }}</p>
            </div>
            <el-tag type="warning" effect="light">{{ item.task_type_label }}</el-tag>
          </article>
          <p v-if="planning && !planning.suggested_tasks.length" class="muted-copy">当前暂无新的系统建议。</p>
        </div>
      </div>

      <div class="planning-block">
        <div class="section-head compact">
          <div>
            <h3>复盘记录</h3>
            <p>记录沟通结果、阶段判断和下一次复核点。</p>
          </div>
        </div>
        <div class="note-input-row">
          <el-input v-model="noteText" placeholder="写一条复盘记录" />
          <el-button :loading="savingNote" @click="saveNote">添加</el-button>
        </div>
        <div class="planning-row-list">
          <article v-for="note in planning?.notes ?? []" :key="note.id" class="planning-row">
            <div>
              <strong>{{ note.note_type_label }}</strong>
              <p>{{ note.content }}</p>
            </div>
            <span class="muted-copy">{{ note.created_at || "-" }}</span>
          </article>
          <p v-if="planning && !planning.notes.length" class="muted-copy">暂无复盘记录。</p>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import { useRouter } from "vue-router";

import { apiRequest, openFile } from "../../api/client";
import {
  sortPlanningTasks,
  type PlanningGoal,
  type PlanningSummary,
  type PlanningTask,
} from "../planning/studentPlanning";
import { formatUserActionError } from "../../utils/userFeedback";

interface PlanningNote {
  id: number;
  note_type_label: string;
  content: string;
  created_at?: string | null;
}

interface StudentPlanningResponse {
  goals: PlanningGoal[];
  tasks: PlanningTask[];
  notes: PlanningNote[];
  suggested_tasks: PlanningTask[];
  summary: PlanningSummary;
}

interface ExportRecord {
  download_url: string;
}

const props = defineProps<{
  studentId: number;
  latestExamId?: number | null;
}>();

const router = useRouter();
const loading = ref(false);
const savingGoal = ref(false);
const savingTask = ref(false);
const savingNote = ref(false);
const generatingTasks = ref(false);
const exporting = ref(false);
const errorMessage = ref("");
const planning = ref<StudentPlanningResponse | null>(null);
const noteText = ref("");

const pathwayNameMap: Record<string, string> = {
  summer_general_regular: "普通类常规批",
  spring_exam: "春季高考",
  vocational_comprehensive: "综合评价",
  vocational_single_exam: "高职单招",
  art_sports: "艺体路径",
  early_batch: "提前批",
};

const goalForm = reactive({
  target_year: 2026,
  pathway_code: "summer_general_regular",
  pathway_name: "普通类常规批",
  target_college: "",
  target_major: "",
  target_score: undefined as number | undefined,
  target_rank: undefined as number | undefined,
  backup_pathways: "",
});

const taskForm = reactive({
  task_type: "stage_review",
  title: "",
  description: "",
  priority: "medium",
  due_date: "" as string | undefined,
});

const sortedTasks = computed(() => sortPlanningTasks(planning.value?.tasks ?? []));

function syncPathwayName(): void {
  goalForm.pathway_name = pathwayNameMap[goalForm.pathway_code] ?? goalForm.pathway_code;
}

function taskStatusTagType(status: string): "success" | "warning" | "info" | "danger" {
  if (status === "completed") return "success";
  if (status === "review") return "warning";
  if (status === "paused") return "info";
  return "danger";
}

async function reload(): Promise<void> {
  loading.value = true;
  errorMessage.value = "";
  try {
    planning.value = await apiRequest<StudentPlanningResponse>(`/api/planning/students/${props.studentId}?target_year=2026`);
  } catch (error) {
    errorMessage.value = formatUserActionError("加载升学规划", error, "确认本地服务已启动后重试。");
  } finally {
    loading.value = false;
  }
}

async function saveGoal(): Promise<void> {
  try {
    savingGoal.value = true;
    await apiRequest("/api/planning/goals", {
      method: "POST",
      body: JSON.stringify({
        student_id: props.studentId,
        target_year: goalForm.target_year,
        pathway_code: goalForm.pathway_code,
        pathway_name: goalForm.pathway_name,
        target_college: goalForm.target_college || null,
        target_major: goalForm.target_major || null,
        target_score: goalForm.target_score ?? null,
        target_rank: goalForm.target_rank ?? null,
        backup_pathways: goalForm.backup_pathways || null,
        status: "in_progress",
        priority: "medium",
      }),
    });
    ElMessage.success("升学目标已保存");
    await reload();
  } catch (error) {
    ElMessage.error(formatUserActionError("保存升学目标", error, "同一年同一路径已有目标时，可直接在任务清单继续跟进。"));
  } finally {
    savingGoal.value = false;
  }
}

async function saveTask(): Promise<void> {
  if (!taskForm.title.trim()) {
    ElMessage.warning("请先填写任务标题");
    return;
  }
  try {
    savingTask.value = true;
    await apiRequest("/api/planning/tasks", {
      method: "POST",
      body: JSON.stringify({
        student_id: props.studentId,
        task_type: taskForm.task_type,
        title: taskForm.title,
        description: taskForm.description || null,
        priority: taskForm.priority,
        due_date: taskForm.due_date || null,
        status: "not_started",
      }),
    });
    taskForm.title = "";
    taskForm.description = "";
    taskForm.due_date = undefined;
    ElMessage.success("规划任务已新增");
    await reload();
  } catch (error) {
    ElMessage.error(formatUserActionError("新增规划任务", error, "请检查任务标题和截止日期后重试。"));
  } finally {
    savingTask.value = false;
  }
}

async function completeTask(taskId?: number | null): Promise<void> {
  if (!taskId) return;
  await updateTaskStatus(taskId, "completed", "任务已完成");
}

async function markTaskReview(taskId?: number | null): Promise<void> {
  if (!taskId) return;
  await updateTaskStatus(taskId, "review", "任务已标记为待复核");
}

async function updateTaskStatus(taskId: number, status: string, message: string): Promise<void> {
  try {
    await apiRequest(`/api/planning/tasks/${taskId}`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    });
    ElMessage.success(message);
    await reload();
  } catch (error) {
    ElMessage.error(formatUserActionError("更新规划任务", error, "请刷新后确认任务是否仍存在。"));
  }
}

async function generateTasksFromPathway(): Promise<void> {
  try {
    generatingTasks.value = true;
    const result = await apiRequest<{ created_count: number; skipped_count: number }>("/api/planning/tasks/bulk-create-from-pathway", {
      method: "POST",
      body: JSON.stringify({
        student_id: props.studentId,
        target_year: 2026,
        include_material_gaps: true,
        include_review_tasks: true,
      }),
    });
    ElMessage.success(`已生成 ${result.created_count} 项任务，跳过 ${result.skipped_count} 项已有任务`);
    await reload();
  } catch (error) {
    ElMessage.error(formatUserActionError("从升学方案生成任务", error, "请先在升学画像中刷新路径评估，再重新生成任务。"));
  } finally {
    generatingTasks.value = false;
  }
}

async function saveNote(): Promise<void> {
  if (!noteText.value.trim()) {
    ElMessage.warning("请先填写复盘内容");
    return;
  }
  try {
    savingNote.value = true;
    await apiRequest("/api/planning/notes", {
      method: "POST",
      body: JSON.stringify({
        student_id: props.studentId,
        note_type: "review",
        content: noteText.value,
      }),
    });
    noteText.value = "";
    ElMessage.success("复盘记录已添加");
    await reload();
  } catch (error) {
    ElMessage.error(formatUserActionError("添加复盘记录", error, "请确认内容不为空后重试。"));
  } finally {
    savingNote.value = false;
  }
}

async function exportPlanningFollowup(): Promise<void> {
  try {
    exporting.value = true;
    const result = await apiRequest<ExportRecord>("/api/reports/planning-followup/export", {
      method: "POST",
      body: JSON.stringify({
        student_id: props.studentId,
        exam_id: props.latestExamId ?? null,
      }),
    });
    openFile(result.download_url);
    ElMessage.success("升学规划跟进表已生成");
  } catch (error) {
    ElMessage.error(formatUserActionError("导出升学规划跟进表", error, "请先确认学生规划数据已加载。"));
  } finally {
    exporting.value = false;
  }
}

watch(
  () => props.studentId,
  () => {
    void reload();
  },
);

onMounted(reload);
</script>

<style scoped>
.student-planning-panel {
  display: grid;
  gap: 18px;
}

.planning-alert {
  border-radius: 8px;
}

.planning-summary-grid,
.planning-bottom-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.planning-bottom-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.planning-summary-item,
.planning-block,
.planning-row {
  border: 1px solid rgba(121, 139, 156, 0.16);
  border-radius: 8px;
  background: rgba(247, 250, 253, 0.82);
}

.planning-summary-item {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
}

.planning-summary-item.warning {
  border-color: rgba(202, 109, 70, 0.32);
  background: rgba(255, 247, 242, 0.9);
}

.planning-summary-item span {
  color: var(--text-soft);
  font-size: 13px;
}

.planning-summary-item strong {
  color: #21364a;
  font-size: 24px;
}

.planning-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(360px, 0.9fr);
  gap: 16px;
}

.planning-block {
  display: grid;
  gap: 14px;
  padding: 16px;
}

.planning-form-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  align-items: center;
}

.task-form {
  grid-template-columns: 160px minmax(220px, 1fr) 110px 180px;
}

.wide-field {
  grid-column: span 3;
}

.planning-row-list {
  display: grid;
  gap: 10px;
}

.planning-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 14px;
}

.planning-row strong {
  color: #22374b;
}

.planning-row p,
.table-subcopy {
  margin: 4px 0 0;
  color: var(--text-muted);
  line-height: 1.55;
}

.compact-table {
  padding: 8px;
}

.overdue {
  color: #b84f30;
  font-weight: 700;
}

.note-input-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.muted-copy {
  color: var(--text-muted);
  font-size: 13px;
}

@media (max-width: 1080px) {
  .planning-summary-grid,
  .planning-layout,
  .planning-bottom-grid,
  .planning-form-grid,
  .task-form {
    grid-template-columns: 1fr;
  }

  .wide-field {
    grid-column: auto;
  }
}
</style>
