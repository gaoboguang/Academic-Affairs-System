<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <h2 class="page-title">考试成绩中心</h2>
        <p class="page-subtitle">
          当前支持考试维护、考试科目配置、成绩模板下载、Excel 导入、快照重建和导入批次查看。
        </p>
      </div>
      <div class="action-row">
        <el-button @click="downloadTemplate">成绩模板下载</el-button>
        <el-button type="primary" @click="openCreate">新建考试</el-button>
      </div>
    </header>

    <section class="soft-card panel-block">
      <div class="filter-grid">
        <el-input v-model="filters.name" placeholder="按考试名称筛选" />
        <el-select v-model="filters.semester_id" clearable placeholder="选择学期">
          <el-option
            v-for="semester in referenceStore.semesters"
            :key="semester.id"
            :label="`${semester.academic_year_name ?? ''} ${semester.name}`"
            :value="semester.id"
          />
        </el-select>
      </div>
      <div class="action-row import-row">
        <el-button type="primary" @click="loadExams">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </section>

    <section class="soft-card panel-block">
      <el-table :data="exams.items" stripe>
        <el-table-column label="考试名称" prop="name" min-width="180" />
        <el-table-column label="类型" prop="exam_type" width="100" />
        <el-table-column label="考试日期" prop="exam_date" width="120" />
        <el-table-column label="学期" prop="semester_name" min-width="180" />
        <el-table-column label="年级范围" min-width="140">
          <template #default="{ row }">
            {{ (row.grade_scope_names ?? []).join(" / ") || "未设置" }}
          </template>
        </el-table-column>
        <el-table-column label="科目数" prop="subject_count" width="90" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="examStatusType(row.status)" effect="light">
              {{ formatExamStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="240" fixed="right">
          <template #default="{ row }">
            <div class="action-row compact-actions">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="primary" @click="openSubjects(row)">科目配置</el-button>
              <el-button link type="primary" @click="openImport(row)">导入成绩</el-button>
              <el-button link type="primary" @click="rebuild(row.id)">重建</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="720px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleExamDialogClosed"
    >
      <el-form label-width="110px">
        <div class="form-grid">
          <el-form-item label="考试名称">
            <el-input v-model="examForm.name" />
          </el-form-item>
          <el-form-item label="考试类型">
            <el-input v-model="examForm.exam_type" />
          </el-form-item>
          <el-form-item label="考试日期">
            <el-date-picker
              v-model="examForm.exam_date"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="学期">
            <el-select v-model="examForm.semester_id" filterable style="width: 100%">
              <el-option
                v-for="semester in referenceStore.semesters"
                :key="semester.id"
                :label="`${semester.academic_year_name ?? ''} ${semester.name}`"
                :value="semester.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="examForm.status" style="width: 100%">
              <el-option label="草稿" value="draft" />
              <el-option label="已发布" value="published" />
              <el-option label="已归档" value="archived" />
            </el-select>
          </el-form-item>
          <el-form-item label="趋势分析">
            <el-switch v-model="examForm.is_trend_enabled" />
          </el-form-item>
          <el-form-item label="年级范围" class="span-two">
            <el-select
              v-model="examForm.grade_scope_json"
              multiple
              collapse-tags
              filterable
              style="width: 100%"
            >
              <el-option
                v-for="grade in referenceStore.grades"
                :key="grade.id"
                :label="grade.name"
                :value="grade.id"
              />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="备注">
          <el-input v-model="examForm.note" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingExam" @click="submitExam">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="subjectsDialogVisible"
      :title="subjectsDialogTitle"
      width="920px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleSubjectsDialogClosed"
    >
      <div class="assignment-toolbar">
        <div>
          <strong>勾选本次考试涉及的科目</strong>
          <p class="subject-selector-note">
            语文 / 数学 / 英语 / 日语 / 俄语默认 150 分，政治 / 历史 / 地理 / 物理 / 化学 / 生物默认 100 分；下方仍可逐科改分。
          </p>
        </div>
        <div class="action-row compact-actions">
          <el-button @click="selectStandardSubjects">常规九科</el-button>
          <el-button @click="clearSelectedSubjects">清空</el-button>
        </div>
      </div>
      <el-checkbox-group
        class="subject-selector-group"
        :model-value="selectedSubjectIds"
        @change="handleSubjectSelectionChange"
      >
        <el-checkbox-button
          v-for="subject in subjectOptions"
          :key="subject.id"
          :label="subject.id"
        >
          {{ formatSubjectOptionLabel(subject) }}
        </el-checkbox-button>
      </el-checkbox-group>
      <div v-if="!subjectRows.length" class="subject-empty-state">
        请先勾选本次考试涉及的科目，再在下方调整满分、分数线和是否计入总分。
      </div>
      <el-table v-else :data="subjectRows" stripe>
        <el-table-column label="学科" min-width="160">
          <template #default="{ row }">
            <div class="subject-cell">
              <strong>{{ resolveSubjectName(row.subject_id) }}</strong>
              <span>默认 {{ resolveSubjectDefaultScore(row.subject_id) }} 分</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="满分" width="110">
          <template #default="{ row }">
            <el-input-number v-model="row.full_score" :min="0" :max="300" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="优秀线" width="110">
          <template #default="{ row }">
            <el-input-number v-model="row.excellent_line" :min="0" :max="300" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="及格线" width="110">
          <template #default="{ row }">
            <el-input-number v-model="row.pass_line" :min="0" :max="300" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="总分" width="90">
          <template #default="{ row }">
            <el-switch v-model="row.is_in_total" />
          </template>
        </el-table-column>
        <el-table-column label="排序" width="100">
          <template #default="{ row }">
            <el-input-number v-model="row.sort_order" :min="0" :max="99" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeSelectedSubject(row.subject_id)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="subjectsDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingSubjects" @click="saveSubjects">保存科目配置</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="importDialogVisible"
      :title="importDialogTitle"
      width="900px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleImportDialogClosed"
    >
      <div class="action-row import-row">
        <el-select v-model="importStrategy" style="width: 180px">
          <el-option label="覆盖已有成绩" value="overwrite" />
          <el-option label="跳过已有成绩" value="skip_existing" />
        </el-select>
        <el-upload :show-file-list="false" :auto-upload="false" :on-change="handleImport">
          <el-button type="primary">上传成绩表</el-button>
        </el-upload>
        <el-button @click="reloadBatches">刷新批次</el-button>
      </div>
      <el-alert
        v-if="importResult"
        :title="importResult.message"
        type="success"
        show-icon
        :closable="false"
      />
      <el-table :data="scoreBatches" stripe style="margin-top: 16px">
        <el-table-column label="批次 ID" prop="id" width="90" />
        <el-table-column label="来源文件" prop="source_filename" min-width="180" />
        <el-table-column label="导入时间" prop="import_time" min-width="160" />
        <el-table-column label="成功" prop="success_rows" width="90" />
        <el-table-column label="失败" prop="failed_rows" width="90" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="scoreBatchStatusType(row.status)" effect="light">
              {{ formatScoreBatchStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import type { UploadFile } from "element-plus";

import { apiRequest, openFile, uploadFile } from "../api/client";
import {
  buildExamSubjectOptions,
  getExamSubjectDefaultFullScore,
  getStandardExamSubjectIds,
  syncExamSubjectRows,
  type ExamSubjectDraftRow,
  type ExamSubjectOption,
} from "../components/exams/examSubjectConfig";
import { useReferenceStore } from "../stores/reference";

interface ExamItem {
  id: number;
  name: string;
  exam_type: string;
  exam_date: string;
  semester_id: number;
  semester_name?: string;
  grade_scope_json: number[];
  grade_scope_names?: string[];
  is_trend_enabled: boolean;
  status: string;
  note?: string;
  subject_count: number;
}

interface ExamListResponse {
  items: ExamItem[];
  total: number;
  page: number;
  page_size: number;
}

interface ExamSubjectRow {
  subject_id: number | null;
  subject_name?: string | null;
  full_score: number;
  excellent_line: number | null;
  pass_line: number | null;
  is_in_total: boolean;
  sort_order: number;
  is_active: boolean;
}

interface ScoreBatch {
  id: number;
  source_filename?: string;
  import_time: string;
  success_rows: number;
  failed_rows: number;
  status: string;
}

interface ImportResult {
  message: string;
  batch_id: number;
}

const referenceStore = useReferenceStore();
const dialogVisible = ref(false);
const subjectsDialogVisible = ref(false);
const importDialogVisible = ref(false);
const editingExamId = ref<number | null>(null);
const subjectsExamId = ref<number | null>(null);
const importExamId = ref<number | null>(null);
const savingExam = ref(false);
const savingSubjects = ref(false);
const importStrategy = ref("overwrite");
const importResult = ref<ImportResult | null>(null);

const filters = reactive({
  name: "",
  semester_id: undefined as number | undefined,
});

const exams = reactive<ExamListResponse>({
  items: [],
  total: 0,
  page: 1,
  page_size: 100,
});

const examForm = reactive({
  name: "",
  exam_type: "月考",
  exam_date: "",
  semester_id: null as number | null,
  grade_scope_json: [] as number[],
  is_trend_enabled: true,
  status: "draft",
  note: "",
  is_active: true,
});

const subjectRows = ref<ExamSubjectDraftRow[]>([]);
const scoreBatches = ref<ScoreBatch[]>([]);
const subjectOptions = computed(() => buildExamSubjectOptions(referenceStore.subjects));
const selectedSubjectIds = computed(() =>
  subjectRows.value
    .map((item) => item.subject_id)
    .filter((value): value is number => typeof value === "number"),
);

const dialogTitle = computed(() => (editingExamId.value ? "编辑考试" : "新建考试"));
const subjectsDialogTitle = computed(() => {
  const current = exams.items.find((item) => item.id === subjectsExamId.value);
  return current ? `科目配置 - ${current.name}` : "科目配置";
});
const importDialogTitle = computed(() => {
  const current = exams.items.find((item) => item.id === importExamId.value);
  return current ? `导入成绩 - ${current.name}` : "导入成绩";
});

function formatExamStatus(status: string): string {
  const mapping: Record<string, string> = {
    draft: "草稿",
    published: "已发布",
    archived: "已归档",
  };
  return mapping[status] ?? status;
}

function examStatusType(status: string): "info" | "success" | "warning" {
  if (status === "published") return "success";
  if (status === "archived") return "warning";
  return "info";
}

function formatScoreBatchStatus(status: string): string {
  const mapping: Record<string, string> = {
    processing: "处理中",
    success: "成功",
    partial_success: "部分成功",
    failed: "失败",
  };
  return mapping[status] ?? status;
}

function scoreBatchStatusType(status: string): "info" | "success" | "warning" | "danger" {
  if (status === "success") return "success";
  if (status === "partial_success") return "warning";
  if (status === "failed") return "danger";
  return "info";
}

function resetExamForm(): void {
  Object.assign(examForm, {
    name: "",
    exam_type: "月考",
    exam_date: "",
    semester_id: null,
    grade_scope_json: [],
    is_trend_enabled: true,
    status: "draft",
    note: "",
    is_active: true,
  });
}

async function loadExams(): Promise<void> {
  try {
    const query = new URLSearchParams({ page: "1", page_size: "100" });
    if (filters.name) query.set("name", filters.name);
    if (filters.semester_id) query.set("semester_id", String(filters.semester_id));
    Object.assign(exams, await apiRequest<ExamListResponse>(`/api/exams?${query.toString()}`));
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function resetFilters(): void {
  filters.name = "";
  filters.semester_id = undefined;
  void loadExams();
}

function downloadTemplate(): void {
  openFile(`/api/system/files?path=${encodeURIComponent("data/templates/exam_scores_import_template.xlsx")}`);
}

function openCreate(): void {
  if (!referenceStore.semesters.length) {
    ElMessage.warning("请先维护学期数据");
    return;
  }
  editingExamId.value = null;
  resetExamForm();
  dialogVisible.value = true;
}

async function openEdit(row: ExamItem): Promise<void> {
  try {
    const detail = await apiRequest<ExamItem>(`/api/exams/${row.id}`);
    editingExamId.value = row.id;
    resetExamForm();
    Object.assign(examForm, detail);
    dialogVisible.value = true;
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function submitExam(): Promise<void> {
  if (!examForm.name.trim() || !examForm.exam_date || !examForm.semester_id) {
    ElMessage.warning("考试名称、考试日期和学期不能为空");
    return;
  }
  try {
    savingExam.value = true;
    const method = editingExamId.value ? "PUT" : "POST";
    const path = editingExamId.value ? `/api/exams/${editingExamId.value}` : "/api/exams";
    await apiRequest(path, { method, body: JSON.stringify(examForm) });
    ElMessage.success("考试保存成功");
    dialogVisible.value = false;
    await loadExams();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingExam.value = false;
  }
}

function formatSubjectOptionLabel(subject: ExamSubjectOption): string {
  return `${subject.name}（${subject.defaultFullScore} 分）`;
}

function resolveSubjectName(subjectId: number | null): string {
  return subjectOptions.value.find((item) => item.id === subjectId)?.name ?? "未识别学科";
}

function resolveSubjectDefaultScore(subjectId: number | null): number {
  const subject = subjectOptions.value.find((item) => item.id === subjectId);
  return subject?.defaultFullScore ?? getExamSubjectDefaultFullScore({ code: "", name: "" });
}

function handleSubjectSelectionChange(values: Array<string | number>): void {
  const selectedIds = values
    .map((item) => Number(item))
    .filter((item) => Number.isInteger(item) && item > 0);
  subjectRows.value = syncExamSubjectRows(selectedIds, referenceStore.subjects, subjectRows.value);
}

function selectStandardSubjects(): void {
  handleSubjectSelectionChange(getStandardExamSubjectIds(referenceStore.subjects));
}

function clearSelectedSubjects(): void {
  subjectRows.value = [];
}

function removeSelectedSubject(subjectId: number | null): void {
  if (subjectId == null) {
    return;
  }
  handleSubjectSelectionChange(selectedSubjectIds.value.filter((item) => item !== subjectId));
}

async function openSubjects(row: ExamItem): Promise<void> {
  try {
    subjectsExamId.value = row.id;
    const items = await apiRequest<ExamSubjectRow[]>(`/api/exams/${row.id}/subjects`);
    subjectRows.value = items.map((item, index) => ({
      subject_id: item.subject_id,
      full_score: item.full_score,
      excellent_line: item.excellent_line,
      pass_line: item.pass_line,
      is_in_total: item.is_in_total,
      sort_order: item.sort_order ?? index + 1,
      is_active: true,
    }));
    subjectsDialogVisible.value = true;
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function saveSubjects(): Promise<void> {
  if (!subjectsExamId.value) return;
  if (!subjectRows.value.length) {
    ElMessage.warning("请至少配置一个考试科目");
    return;
  }
  if (subjectRows.value.some((item) => !item.subject_id)) {
    ElMessage.warning("考试科目不能为空");
    return;
  }
  const subjectIds = subjectRows.value.map((item) => item.subject_id);
  if (new Set(subjectIds).size !== subjectIds.length) {
    ElMessage.warning("考试科目不能重复");
    return;
  }
  try {
    savingSubjects.value = true;
    await apiRequest(`/api/exams/${subjectsExamId.value}/subjects`, {
      method: "POST",
      body: JSON.stringify(subjectRows.value),
    });
    ElMessage.success("考试科目保存成功");
    subjectsDialogVisible.value = false;
    await loadExams();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingSubjects.value = false;
  }
}

async function openImport(row: ExamItem): Promise<void> {
  importExamId.value = row.id;
  importResult.value = null;
  scoreBatches.value = [];
  importDialogVisible.value = true;
  await reloadBatches();
}

async function handleImport(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw || !importExamId.value) return;
  try {
    importResult.value = await uploadFile<ImportResult>(
      `/api/exams/${importExamId.value}/scores/import`,
      uploadFileItem.raw,
      {
        strategy: importStrategy.value,
        rebuild: "true",
      },
    );
    ElMessage.success(importResult.value.message);
    await reloadBatches();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function reloadBatches(): Promise<void> {
  if (!importExamId.value) return;
  try {
    scoreBatches.value = await apiRequest<ScoreBatch[]>(`/api/exams/${importExamId.value}/score-batches`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function rebuild(examId: number): Promise<void> {
  try {
    const payload = await apiRequest<{ message: string }>(`/api/exams/${examId}/rebuild`, {
      method: "POST",
    });
    ElMessage.success(payload.message);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function handleExamDialogClosed(): void {
  editingExamId.value = null;
  resetExamForm();
}

function handleSubjectsDialogClosed(): void {
  subjectsExamId.value = null;
  subjectRows.value = [];
}

function handleImportDialogClosed(): void {
  importExamId.value = null;
  importResult.value = null;
  scoreBatches.value = [];
}

onMounted(async () => {
  await referenceStore.loadCore();
  await loadExams();
});
</script>

<style scoped>
.panel-block {
  padding: 18px;
}

.compact-actions {
  gap: 4px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.span-two {
  grid-column: span 2;
}

.assignment-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.subject-selector-note {
  margin: 6px 0 0;
  color: #6d8194;
  line-height: 1.6;
}

.subject-selector-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.subject-empty-state {
  padding: 16px 18px;
  margin-bottom: 14px;
  border: 1px dashed rgba(123, 141, 158, 0.35);
  border-radius: 14px;
  color: #6d8194;
  background: rgba(245, 249, 252, 0.82);
  line-height: 1.7;
}

.subject-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subject-cell strong {
  color: #22384c;
}

.subject-cell span {
  color: #6d8194;
  font-size: 12px;
}

.import-row {
  margin-top: 14px;
  align-items: center;
}

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .span-two {
    grid-column: span 1;
  }

  .assignment-toolbar {
    flex-direction: column;
  }
}
</style>
