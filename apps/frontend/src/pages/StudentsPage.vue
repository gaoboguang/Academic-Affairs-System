<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">基础台账 / 学生中心</div>
        <h2 class="page-title">学生中心</h2>
        <p class="page-subtitle">
          当前支持学生列表、详情页、模板下载、批量导入和 Excel 导出。学生状态、类别、艺体方向和生源地会一起沉到学生主档。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>学生总数</strong>{{ students.total }}</span>
          <span class="page-chip"><strong>当前页记录</strong>{{ students.items.length }}</span>
          <span class="page-chip"><strong>已选学生</strong>{{ selectedRows.length }}</span>
          <span class="page-chip"><strong>启用筛选</strong>{{ activeFilterCount }}</span>
          <span class="page-chip"><strong>导入策略</strong>{{ importStrategyLabel }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="openFile('/api/students/template')">模板下载</el-button>
        <el-button @click="openFile('/api/students/export')">导出列表</el-button>
        <el-button type="primary" @click="openCreate">新增学生</el-button>
      </div>
    </header>

    <section class="overview-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">管理视图</div>
        <h3>学生台账、导入和详情入口放在一条连续路径里</h3>
        <p>
          先筛选并确认学生范围，再进入详情补充家庭联系人、成长档案、成绩画像和附件，不把高频信息拆到多个页面里。
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
          <p>先缩小学生范围，再执行导入或进入详情，避免在过长列表里盲目查找。</p>
        </div>
      </div>
      <div class="filter-grid">
        <el-input v-model="filters.student_no" placeholder="按学号筛选" />
        <el-input v-model="filters.name" placeholder="按姓名筛选" />
        <el-select v-model="filters.grade_id" clearable placeholder="选择年级">
          <el-option
            v-for="grade in referenceStore.grades"
            :key="grade.id"
            :label="grade.name"
            :value="grade.id"
          />
        </el-select>
        <el-select v-model="filters.class_id" clearable placeholder="选择班级">
          <el-option
            v-for="schoolClass in referenceStore.classes"
            :key="schoolClass.id"
            :label="schoolClass.name"
            :value="schoolClass.id"
          />
        </el-select>
      </div>
      <div class="action-row import-row">
        <el-button type="primary" @click="loadStudents">查询</el-button>
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
          <el-button>导入学生</el-button>
        </el-upload>
      </div>
      <ImportFeedbackPanel :result="importResult" />
    </section>

    <section class="soft-card panel-block">
      <div class="section-head compact">
        <div>
          <h3>学生列表</h3>
          <p>列表保留基础身份、当前班级、生源地和联系方式，详情页承接更深的信息。</p>
        </div>
        <div class="list-action-stack">
          <span class="panel-caption">共 {{ students.total }} 条</span>
          <div class="bulk-action-controls">
            <span class="bulk-action-label">批量操作</span>
            <span class="bulk-selection-count">已选 {{ selectedRows.length }} 名</span>
            <el-button
              type="danger"
              plain
              :icon="DeleteIcon"
              :disabled="selectedRows.length === 0"
              @click="openBulkDeleteDialog"
            >
              批量删除学生
            </el-button>
          </div>
        </div>
      </div>
      <div class="table-shell">
        <el-table
          ref="studentTableRef"
          :data="students.items"
          stripe
          row-key="id"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="48" />
          <el-table-column label="学号" prop="student_no" min-width="120" />
          <el-table-column label="姓名" prop="name" min-width="100" />
          <el-table-column label="性别" prop="gender" width="80" />
          <el-table-column label="年级" prop="current_grade_name" width="100" />
          <el-table-column label="班级" prop="current_class_name" width="100" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag effect="light">{{ resolveDictName("student_status", row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="类别" width="110">
            <template #default="{ row }">
              {{ resolveDictName("student_type", row.student_type) }}
            </template>
          </el-table-column>
          <el-table-column label="艺体方向" width="120">
            <template #default="{ row }">
              {{ resolveDictName("art_track", row.art_track) }}
            </template>
          </el-table-column>
          <el-table-column label="生源地" prop="origin_province" width="100" />
          <el-table-column label="联系电话" prop="phone" min-width="130" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link @click="openDetail(row)">详情</el-button>
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="pager-row">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :current-page="page"
          :page-size="pageSize"
          :total="students.total"
          @current-change="handlePageChange"
        />
      </div>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="760px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form label-width="110px">
        <div class="form-grid">
          <el-form-item label="学号">
            <el-input v-model="formState.student_no" />
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
          <el-form-item label="出生日期">
            <el-date-picker
              v-model="formState.birth_date"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="入学年份">
            <el-input-number v-model="formState.admission_year" :min="2010" :max="2100" style="width: 100%" />
          </el-form-item>
          <el-form-item label="年级">
            <el-select v-model="formState.current_grade_id" clearable filterable>
              <el-option
                v-for="grade in referenceStore.grades"
                :key="grade.id"
                :label="grade.name"
                :value="grade.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="班级">
            <el-select v-model="formState.current_class_id" clearable filterable>
              <el-option
                v-for="schoolClass in referenceStore.classes"
                :key="schoolClass.id"
                :label="schoolClass.name"
                :value="schoolClass.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="学生状态">
            <el-select v-model="formState.status" clearable filterable>
              <el-option
                v-for="item in referenceStore.dicts.student_status ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="学生类别">
            <el-select v-model="formState.student_type" clearable filterable>
              <el-option
                v-for="item in referenceStore.dicts.student_type ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="艺体方向">
            <el-select v-model="formState.art_track" clearable filterable>
              <el-option
                v-for="item in referenceStore.dicts.art_track ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="生源地">
            <el-select v-model="formState.origin_province" clearable filterable allow-create default-first-option>
              <el-option
                v-for="province in provinceOptions"
                :key="province"
                :label="province"
                :value="province"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="formState.phone" />
          </el-form-item>
          <el-form-item label="家庭住址">
            <el-input v-model="formState.address" />
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

    <StudentBulkDeleteDialog
      v-model="bulkDeleteDialogVisible"
      :student-ids="bulkDeleteStudentIds"
      :student-labels="bulkDeleteStudentLabels"
      @completed="handleBulkDeleteCompleted"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { Delete as DeleteIcon } from "@element-plus/icons-vue";
import ElMessage from "element-plus/es/components/message/index";
import type { UploadFile } from "element-plus";
import { useRouter } from "vue-router";

import { apiRequest, openFile, uploadFile } from "../api/client";
import ImportFeedbackPanel from "../components/common/ImportFeedbackPanel.vue";
import StudentBulkDeleteDialog from "../components/students/StudentBulkDeleteDialog.vue";
import { useReferenceStore } from "../stores/reference";
import type { ImportFeedbackResult } from "../utils/importFeedback";

interface StudentItem {
  id: number;
  student_no: string;
  name: string;
  gender?: string;
  current_grade_name?: string;
  current_class_name?: string;
  status?: string;
  student_type?: string;
  art_track?: string;
  origin_province?: string | null;
  phone?: string;
  note?: string;
}

interface StudentListResponse {
  items: StudentItem[];
  total: number;
  page: number;
  page_size: number;
}

const referenceStore = useReferenceStore();
const router = useRouter();
const page = ref(1);
const pageSize = ref(10);
const importStrategy = ref("skip_existing");
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const submitting = ref(false);
const importResult = ref<ImportFeedbackResult | null>(null);
const selectedRows = ref<StudentItem[]>([]);
const studentTableRef = ref<{ clearSelection: () => void } | null>(null);
const bulkDeleteDialogVisible = ref(false);
const bulkDeleteStudentIds = ref<number[]>([]);
const bulkDeleteStudentLabels = ref<string[]>([]);

const filters = reactive({
  student_no: "",
  name: "",
  grade_id: undefined as number | undefined,
  class_id: undefined as number | undefined,
});

const students = reactive<StudentListResponse>({
  items: [],
  total: 0,
  page: 1,
  page_size: 10,
});

const formState = reactive<Record<string, unknown>>({
  student_no: "",
  name: "",
  gender: null,
  birth_date: null,
  admission_year: null,
  current_grade_id: null,
  current_class_id: null,
  status: null,
  student_type: null,
  art_track: null,
  origin_province: null,
  phone: "",
  address: "",
  note: "",
  guardians: [],
  is_active: true,
});

const dialogTitle = computed(() => (editingId.value ? "编辑学生" : "新增学生"));
const activeFilterCount = computed(
  () => [filters.student_no, filters.name, filters.grade_id, filters.class_id].filter(Boolean).length,
);
const importStrategyLabel = computed(() => {
  const mapping: Record<string, string> = {
    skip_existing: "跳过已存在",
    update: "更新已有记录",
    create: "仅新增",
  };
  return mapping[importStrategy.value] ?? importStrategy.value;
});
const selectedStudentIds = computed(() => selectedRows.value.map((student) => student.id));
const overviewCards = computed(() => [
  {
    label: "当前页班级",
    value: new Set(students.items.map((item) => item.current_class_name).filter(Boolean)).size,
    help: "当前筛选结果页覆盖的班级数量。",
    tone: "tone-blue",
  },
  {
    label: "艺体方向",
    value: students.items.filter((item) => item.art_track).length,
    help: "当前结果页里已标记艺体方向的学生。",
    tone: "tone-amber",
  },
  {
    label: "生源地",
    value: students.items.filter((item) => item.origin_province).length,
    help: "当前结果页里已维护高考生源地的学生。",
    tone: "tone-green",
  },
  {
    label: "联系电话",
    value: students.items.filter((item) => item.phone).length,
    help: "当前结果页里已填写联系电话的学生。",
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
    student_no: "",
    name: "",
    gender: null,
    birth_date: null,
    admission_year: null,
    current_grade_id: null,
    current_class_id: null,
    status: null,
    student_type: null,
    art_track: null,
    origin_province: null,
    phone: "",
    address: "",
    note: "",
    guardians: [],
    is_active: true,
  });
}

async function loadStudents(): Promise<void> {
  try {
    const query = new URLSearchParams({
      page: String(page.value),
      page_size: String(pageSize.value),
    });
    if (filters.student_no) query.set("student_no", filters.student_no);
    if (filters.name) query.set("name", filters.name);
    if (filters.grade_id) query.set("grade_id", String(filters.grade_id));
    if (filters.class_id) query.set("class_id", String(filters.class_id));
    Object.assign(
      students,
      await apiRequest<StudentListResponse>(`/api/students?${query.toString()}`),
    );
    clearSelectedStudents();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function resetFilters(): void {
  filters.student_no = "";
  filters.name = "";
  filters.grade_id = undefined;
  filters.class_id = undefined;
  page.value = 1;
  void loadStudents();
}

function openCreate(): void {
  editingId.value = null;
  resetForm();
  dialogVisible.value = true;
}

async function openEdit(row: StudentItem): Promise<void> {
  try {
    const detail = await apiRequest<Record<string, unknown>>(`/api/students/${row.id}`);
    editingId.value = row.id;
    resetForm();
    Object.assign(formState, detail);
    dialogVisible.value = true;
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function openDetail(row: StudentItem): void {
  router.push(`/students/${row.id}`);
}

function formatStudentLabel(student: StudentItem): string {
  return `${student.name}（${student.student_no}）`;
}

function handleSelectionChange(rows: StudentItem[]): void {
  selectedRows.value = rows;
}

function clearSelectedStudents(): void {
  selectedRows.value = [];
  studentTableRef.value?.clearSelection();
}

function openBulkDeleteDialog(): void {
  if (!selectedRows.value.length) {
    ElMessage.warning("请先勾选需要批量删除的学生");
    return;
  }
  bulkDeleteStudentIds.value = selectedStudentIds.value;
  bulkDeleteStudentLabels.value = selectedRows.value.map(formatStudentLabel);
  bulkDeleteDialogVisible.value = true;
}

function handleBulkDeleteCompleted(): void {
  void loadStudents();
}

async function submitForm(): Promise<void> {
  if (!String(formState.student_no ?? "").trim() || !String(formState.name ?? "").trim()) {
    ElMessage.warning("学号和姓名不能为空");
    return;
  }
  try {
    submitting.value = true;
    const method = editingId.value ? "PUT" : "POST";
    const path = editingId.value ? `/api/students/${editingId.value}` : "/api/students";
    await apiRequest(path, {
      method,
      body: JSON.stringify(formState),
    });
    ElMessage.success("学生保存成功");
    dialogVisible.value = false;
    await Promise.all([referenceStore.loadCore(), loadStudents()]);
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    submitting.value = false;
  }
}

function handleDialogClosed(): void {
  editingId.value = null;
  resetForm();
}

async function handleImport(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw) {
    return;
  }
  try {
    importResult.value = null;
    importResult.value = await uploadFile<ImportFeedbackResult>("/api/students/import", uploadFileItem.raw, {
      strategy: importStrategy.value,
    });
    ElMessage({
      type: importResult.value.failed_rows ? "warning" : "success",
      message: importResult.value.message,
    });
    await Promise.all([referenceStore.loadCore(), loadStudents()]);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function handlePageChange(nextPage: number): void {
  page.value = nextPage;
  void loadStudents();
}

onMounted(async () => {
  await referenceStore.loadAll();
  await loadStudents();
});

const provinceOptions = [
  "北京",
  "天津",
  "河北",
  "山西",
  "内蒙古",
  "辽宁",
  "吉林",
  "黑龙江",
  "上海",
  "江苏",
  "浙江",
  "安徽",
  "福建",
  "江西",
  "山东",
  "河南",
  "湖北",
  "湖南",
  "广东",
  "广西",
  "海南",
  "重庆",
  "四川",
  "贵州",
  "云南",
  "西藏",
  "陕西",
  "甘肃",
  "青海",
  "宁夏",
  "新疆",
];
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

.import-feedback {
  margin-top: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: rgba(244, 248, 252, 0.9);
  border: 1px solid rgba(145, 163, 176, 0.22);
}

.import-feedback-summary {
  margin: 0;
  color: var(--text-secondary);
}

.import-feedback-title {
  margin: 10px 0 0;
  color: #1f3448;
  font-size: 13px;
  font-weight: 600;
}

.import-feedback-list {
  margin: 10px 0 0;
  padding-left: 20px;
  color: var(--text-primary);
}

.import-feedback-list-notice {
  color: #335d78;
}

.import-feedback-list li + li {
  margin-top: 6px;
}

.import-feedback-actions {
  margin-top: 8px;
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

.tone-amber {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.84);
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

.list-action-stack {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.bulk-action-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 10px;
  border: 1px solid rgba(145, 163, 176, 0.24);
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.92);
}

.bulk-action-label {
  color: #1f3448;
  font-size: 13px;
  font-weight: 700;
}

.bulk-selection-count {
  color: #6d8194;
  font-size: 13px;
}

.pager-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
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

  .list-action-stack {
    justify-content: flex-start;
  }
}
</style>
