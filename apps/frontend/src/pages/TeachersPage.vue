<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">基础台账 / 教师中心</div>
        <h2 class="page-title">教师中心</h2>
        <p class="page-subtitle">
          当前支持教师列表、详情页、导入导出和任教关系维护，为教学分析、职称历史和工作量计算做数据底座。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>教师总数</strong>{{ teachers.total }}</span>
          <span class="page-chip"><strong>当前页记录</strong>{{ teachers.items.length }}</span>
          <span class="page-chip"><strong>任教关系</strong>{{ assignments.length }}</span>
          <span class="page-chip"><strong>导入策略</strong>{{ importStrategyLabel }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="openFile('/api/teachers/template')">模板下载</el-button>
        <el-button @click="openFile('/api/teachers/export')">导出列表</el-button>
        <el-button type="primary" @click="openCreate">新增教师</el-button>
      </div>
    </header>

    <section class="overview-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">教学台账</div>
        <h3>教师信息、任教关系和后续分析保持同一条数据链</h3>
        <p>
          列表页先确认教师基础信息和当前任教范围，再进入详情维护职称历史、考试趋势和同科对比，避免信息断层。
        </p>
      </article>
      <article v-for="item in overviewCards" :key="item.label" class="soft-card overview-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head compact">
        <div>
          <h3>筛选与导入</h3>
          <p>先按工号、姓名或学科缩小范围，再处理批量导入和任教关系维护。</p>
        </div>
      </div>
      <div class="filter-grid">
        <el-input v-model="filters.teacher_no" placeholder="按工号筛选" />
        <el-input v-model="filters.name" placeholder="按姓名筛选" />
        <el-select v-model="filters.subject_id" clearable placeholder="选择学科">
          <el-option
            v-for="subject in referenceStore.subjects"
            :key="subject.id"
            :label="subject.name"
            :value="subject.id"
          />
        </el-select>
      </div>
      <div class="action-row import-row">
        <el-button type="primary" @click="loadTeachers">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
        <el-select v-model="importStrategy" style="width: 180px">
          <el-option label="跳过已存在" value="skip_existing" />
          <el-option label="更新已有记录" value="update" />
          <el-option label="仅新增" value="create" />
        </el-select>
        <el-upload
          :show-file-list="false"
          :auto-upload="false"
          :on-change="handleImport"
        >
          <el-button>导入教师</el-button>
        </el-upload>
        <el-button @click="openAssignmentDialog">维护任教关系</el-button>
      </div>
      <el-alert
        v-if="importResult"
        :title="importResult.message"
        type="success"
        show-icon
        :closable="false"
      />
    </section>

    <section class="soft-card panel-block">
      <div class="section-head compact">
        <div>
          <h3>教师列表</h3>
          <p>列表先给出身份、学科和岗位视图，详情页再承接职称历史与考试表现。</p>
        </div>
        <span class="panel-caption">共 {{ teachers.total }} 条</span>
      </div>
      <div class="table-shell">
        <el-table :data="teachers.items" stripe>
          <el-table-column label="工号" prop="teacher_no" min-width="110" />
          <el-table-column label="姓名" prop="name" min-width="100" />
          <el-table-column label="性别" prop="gender" width="80" />
          <el-table-column label="学科" prop="subject_name" width="100" />
          <el-table-column label="职称" width="120">
            <template #default="{ row }">
              {{ resolveDictName("teacher_title", row.title_code) }}
            </template>
          </el-table-column>
          <el-table-column label="岗位" width="120">
            <template #default="{ row }">
              {{ resolveDictName("teacher_position", row.position_code) }}
            </template>
          </el-table-column>
          <el-table-column label="班主任" width="90">
            <template #default="{ row }">
              <el-tag :type="row.is_head_teacher ? 'success' : 'info'" effect="light">
                {{ row.is_head_teacher ? "是" : "否" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="联系电话" prop="phone" min-width="130" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link @click="openDetail(row)">详情</el-button>
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="760px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleTeacherDialogClosed"
    >
      <el-form label-width="110px">
        <div class="form-grid">
          <el-form-item label="工号">
            <el-input v-model="formState.teacher_no" />
          </el-form-item>
          <el-form-item label="姓名">
            <el-input v-model="formState.name" />
          </el-form-item>
          <el-form-item label="性别">
            <el-select v-model="formState.gender" clearable>
              <el-option label="男" value="男" />
              <el-option label="女" value="女" />
            </el-select>
          </el-form-item>
          <el-form-item label="学科">
            <el-select v-model="formState.subject_id" clearable filterable>
              <el-option
                v-for="subject in referenceStore.subjects"
                :key="subject.id"
                :label="subject.name"
                :value="subject.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="职称">
            <el-select v-model="formState.title_code" clearable filterable>
              <el-option
                v-for="item in referenceStore.dicts.teacher_title ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="岗位">
            <el-select v-model="formState.position_code" clearable filterable>
              <el-option
                v-for="item in referenceStore.dicts.teacher_position ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="任教状态">
            <el-select v-model="formState.employment_status" clearable filterable>
              <el-option
                v-for="item in referenceStore.dicts.teacher_status ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="formState.phone" />
          </el-form-item>
          <el-form-item label="入职日期">
            <el-date-picker
              v-model="formState.entry_date"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="是否班主任">
            <el-switch v-model="formState.is_head_teacher" />
          </el-form-item>
        </div>
        <el-form-item label="备注">
          <el-input v-model="formState.note" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="assignmentDialogVisible"
      title="任教关系维护"
      width="880px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleAssignmentDialogClosed"
    >
      <div class="section-head compact">
        <div>
          <h3>任教关系维护</h3>
          <p>把学期、班级、学科和课程类型放到统一关系表里，供分析与工作量复用。</p>
        </div>
        <div class="assignment-toolbar">
          <el-button type="primary" @click="openAssignmentCreate">新增任教关系</el-button>
        </div>
      </div>
      <div class="table-shell">
        <el-table :data="assignments" stripe>
          <el-table-column label="教师" prop="teacher_name" min-width="100" />
          <el-table-column label="学期" prop="semester_name" min-width="160" />
          <el-table-column label="年级" prop="grade_name" width="90" />
          <el-table-column label="班级" prop="class_name" width="90" />
          <el-table-column label="学科" prop="subject_name" width="100" />
          <el-table-column label="课程类型" prop="course_type" width="110" />
          <el-table-column label="周课时" prop="weekly_periods_manual" width="100" />
        </el-table>
      </div>

      <el-dialog
        v-model="assignmentFormVisible"
        title="新增任教关系"
        width="620px"
        append-to-body
        destroy-on-close
        :close-on-click-modal="false"
        @closed="resetAssignmentForm"
      >
        <el-form label-width="110px">
          <el-form-item label="教师">
            <el-select v-model="assignmentForm.teacher_id" filterable style="width: 100%">
              <el-option
                v-for="teacher in teachers.items"
                :key="teacher.id"
                :label="teacher.name"
                :value="teacher.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="学期">
            <el-select v-model="assignmentForm.semester_id" filterable style="width: 100%">
              <el-option
                v-for="semester in referenceStore.semesters"
                :key="semester.id"
                :label="`${semester.academic_year_name ?? ''} ${semester.name}`"
                :value="semester.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="年级">
            <el-select v-model="assignmentForm.grade_id" clearable style="width: 100%">
              <el-option
                v-for="grade in referenceStore.grades"
                :key="grade.id"
                :label="grade.name"
                :value="grade.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="班级">
            <el-select v-model="assignmentForm.class_id" clearable style="width: 100%">
              <el-option
                v-for="schoolClass in referenceStore.classes"
                :key="schoolClass.id"
                :label="schoolClass.name"
                :value="schoolClass.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="学科">
            <el-select v-model="assignmentForm.subject_id" clearable style="width: 100%">
              <el-option
                v-for="subject in referenceStore.subjects"
                :key="subject.id"
                :label="subject.name"
                :value="subject.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="课程类型">
            <el-select v-model="assignmentForm.course_type" clearable style="width: 100%">
              <el-option
                v-for="item in referenceStore.dicts.course_type ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="周课时">
            <el-input-number v-model="assignmentForm.weekly_periods_manual" :min="0" :max="40" style="width: 100%" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="assignmentFormVisible = false">取消</el-button>
          <el-button type="primary" @click="submitAssignment">保存</el-button>
        </template>
      </el-dialog>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import type { UploadFile } from "element-plus";
import { useRouter } from "vue-router";

import { apiRequest, openFile, uploadFile } from "../api/client";
import { useReferenceStore } from "../stores/reference";

interface TeacherItem {
  id: number;
  teacher_no: string;
  name: string;
  gender?: string;
  subject_name?: string;
  title_code?: string;
  position_code?: string;
  is_head_teacher: boolean;
  phone?: string;
}

interface TeacherListResponse {
  items: TeacherItem[];
  total: number;
  page: number;
  page_size: number;
}

interface AssignmentItem {
  id: number;
  teacher_name?: string;
  semester_name?: string;
  grade_name?: string;
  class_name?: string;
  subject_name?: string;
  course_type?: string;
  weekly_periods_manual?: number;
}

interface ImportResult {
  message: string;
  error_report_path?: string;
}

const referenceStore = useReferenceStore();
const router = useRouter();
const importStrategy = ref("skip_existing");
const dialogVisible = ref(false);
const assignmentDialogVisible = ref(false);
const assignmentFormVisible = ref(false);
const editingId = ref<number | null>(null);
const submitting = ref(false);
const importResult = ref<ImportResult | null>(null);

const filters = reactive({
  teacher_no: "",
  name: "",
  subject_id: undefined as number | undefined,
});

const teachers = reactive<TeacherListResponse>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
});

const assignments = ref<AssignmentItem[]>([]);

const formState = reactive<Record<string, unknown>>({
  teacher_no: "",
  name: "",
  gender: null,
  subject_id: null,
  phone: "",
  title_code: null,
  position_code: null,
  is_head_teacher: false,
  employment_status: null,
  entry_date: null,
  note: "",
  is_active: true,
});

const assignmentForm = reactive<Record<string, unknown>>({
  teacher_id: null,
  semester_id: null,
  grade_id: null,
  class_id: null,
  subject_id: null,
  course_type: null,
  weekly_periods_manual: 0,
  is_active: true,
});

const dialogTitle = computed(() => (editingId.value ? "编辑教师" : "新增教师"));
const importStrategyLabel = computed(() => {
  const mapping: Record<string, string> = {
    skip_existing: "跳过已存在",
    update: "更新已有记录",
    create: "仅新增",
  };
  return mapping[importStrategy.value] ?? importStrategy.value;
});
const overviewCards = computed(() => [
  {
    label: "学科覆盖",
    value: new Set(teachers.items.map((item) => item.subject_name).filter(Boolean)).size,
    help: "当前结果页覆盖的学科数量。",
    tone: "tone-blue",
  },
  {
    label: "班主任",
    value: teachers.items.filter((item) => item.is_head_teacher).length,
    help: "当前结果页里标记为班主任的教师。",
    tone: "tone-green",
  },
  {
    label: "联系电话",
    value: teachers.items.filter((item) => item.phone).length,
    help: "当前结果页里已填写联系电话的教师。",
    tone: "tone-slate",
  },
]);

function resolveDictName(dictCode: string, code?: string | null): string {
  if (!code) return "-";
  return (
    referenceStore.dicts[dictCode]?.find((item) => String(item.code) === String(code))?.name ?? code
  );
}

function resetForm(): void {
  Object.assign(formState, {
    teacher_no: "",
    name: "",
    gender: null,
    subject_id: null,
    phone: "",
    title_code: null,
    position_code: null,
    is_head_teacher: false,
    employment_status: null,
    entry_date: null,
    note: "",
    is_active: true,
  });
}

async function loadTeachers(): Promise<void> {
  try {
    const query = new URLSearchParams({
      page: "1",
      page_size: "100",
    });
    if (filters.teacher_no) query.set("teacher_no", filters.teacher_no);
    if (filters.name) query.set("name", filters.name);
    if (filters.subject_id) query.set("subject_id", String(filters.subject_id));

    Object.assign(
      teachers,
      await apiRequest<TeacherListResponse>(`/api/teachers?${query.toString()}`),
    );
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadAssignments(): Promise<void> {
  try {
    assignments.value = await apiRequest<AssignmentItem[]>("/api/teachers/assignments");
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function resetFilters(): void {
  filters.teacher_no = "";
  filters.name = "";
  filters.subject_id = undefined;
  void loadTeachers();
}

function openCreate(): void {
  editingId.value = null;
  resetForm();
  dialogVisible.value = true;
}

async function openAssignmentDialog(): Promise<void> {
  await loadAssignments();
  assignmentDialogVisible.value = true;
}

async function openEdit(row: TeacherItem): Promise<void> {
  try {
    const detail = await apiRequest<Record<string, unknown>>(`/api/teachers/${row.id}`);
    editingId.value = row.id;
    resetForm();
    Object.assign(formState, detail);
    dialogVisible.value = true;
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function openDetail(row: TeacherItem): void {
  router.push(`/teachers/${row.id}`);
}

async function submitForm(): Promise<void> {
  if (!String(formState.teacher_no ?? "").trim() || !String(formState.name ?? "").trim()) {
    ElMessage.warning("工号和姓名不能为空");
    return;
  }
  try {
    submitting.value = true;
    const method = editingId.value ? "PUT" : "POST";
    const path = editingId.value ? `/api/teachers/${editingId.value}` : "/api/teachers";
    await apiRequest(path, {
      method,
      body: JSON.stringify(formState),
    });
    ElMessage.success("教师保存成功");
    dialogVisible.value = false;
    await loadTeachers();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    submitting.value = false;
  }
}

async function handleImport(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw) {
    return;
  }
  try {
    importResult.value = await uploadFile<ImportResult>("/api/teachers/import", uploadFileItem.raw, {
      strategy: importStrategy.value,
    });
    ElMessage.success(importResult.value.message);
    await Promise.all([loadTeachers(), loadAssignments()]);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function openAssignmentCreate(): void {
  if (!teachers.items.length || !referenceStore.semesters.length) {
    ElMessage.warning("请先加载教师和学期数据");
    return;
  }
  resetAssignmentForm();
  assignmentFormVisible.value = true;
}

function resetAssignmentForm(): void {
  Object.assign(assignmentForm, {
    teacher_id: null,
    semester_id: null,
    grade_id: null,
    class_id: null,
    subject_id: null,
    course_type: null,
    weekly_periods_manual: 0,
    is_active: true,
  });
}

async function submitAssignment(): Promise<void> {
  if (!assignmentForm.teacher_id || !assignmentForm.semester_id) {
    ElMessage.warning("教师和学期不能为空");
    return;
  }
  try {
    await apiRequest("/api/teachers/assignments", {
      method: "POST",
      body: JSON.stringify(assignmentForm),
    });
    ElMessage.success("任教关系保存成功");
    assignmentFormVisible.value = false;
    await loadAssignments();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function handleTeacherDialogClosed(): void {
  editingId.value = null;
  resetForm();
}

function handleAssignmentDialogClosed(): void {
  assignmentFormVisible.value = false;
  resetAssignmentForm();
}

onMounted(async () => {
  await referenceStore.loadAll();
  await Promise.all([loadTeachers(), loadAssignments()]);
});
</script>

<style scoped>
.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) repeat(3, minmax(0, 0.75fr));
  gap: 16px;
}

.overview-panel,
.overview-card {
  padding: 24px;
}

.overview-panel {
  background:
    radial-gradient(circle at top left, rgba(180, 219, 243, 0.32), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(244, 248, 252, 0.94));
}

.overview-kicker {
  display: inline-flex;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f6c98;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.overview-panel h3 {
  margin: 14px 0 0;
  color: #1f3448;
  font-size: 28px;
  line-height: 1.25;
}

.overview-panel p {
  margin: 12px 0 0;
  color: #62788c;
  line-height: 1.7;
}

.overview-card {
  display: grid;
  align-content: end;
  gap: 10px;
}

.overview-card span {
  color: #6d8194;
  font-size: 13px;
}

.overview-card strong {
  color: #1f3245;
  font-size: 30px;
  font-weight: 760;
}

.overview-card p {
  margin: 0;
  color: #73879b;
  line-height: 1.55;
  font-size: 13px;
}

.tone-blue {
  box-shadow: inset 0 4px 0 rgba(31, 108, 152, 0.78);
}

.tone-green {
  box-shadow: inset 0 4px 0 rgba(69, 141, 105, 0.8);
}

.tone-slate {
  box-shadow: inset 0 4px 0 rgba(92, 111, 129, 0.74);
}

.import-row {
  margin-top: 14px;
  align-items: center;
}

.panel-caption {
  color: #6d8194;
  font-size: 13px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.assignment-toolbar {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 1180px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
