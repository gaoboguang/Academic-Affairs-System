<template>
  <AppPage
    title="学生中心"
    eyebrow="基础台账 / 学生中心"
    description="当前支持学生列表、详情页、模板下载、批量导入和 Excel 导出。学生状态、类别、艺体方向和生源地会一起沉到学生主档。"
    :meta="studentPageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button :disabled="studentsLoading || importingStudents" @click="openFile('/api/students/template')">
          模板下载
        </el-button>
        <el-button :disabled="studentsLoading || importingStudents" @click="openFile('/api/students/export')">
          导出列表
        </el-button>
        <el-button type="primary" :disabled="studentsLoading || importingStudents" @click="openCreate">
          新增学生
        </el-button>
      </div>
    </template>

    <AppStatGrid :items="overviewCards" :columns="4" />

    <section v-if="referenceLoadError || studentActionError" class="student-status-stack">
      <el-alert
        v-if="referenceLoadError"
        type="warning"
        title="学生中心基础选项加载失败"
        show-icon
        :closable="false"
      >
        <template #default>
          <div class="student-alert-body">
            <span>{{ referenceLoadError }}</span>
            <el-button link type="primary" :loading="referenceLoading" @click="loadReferenceOptions">
              重新加载基础选项
            </el-button>
          </div>
        </template>
      </el-alert>
      <el-alert
        v-if="studentActionError"
        type="error"
        title="学生操作失败"
        show-icon
        :closable="false"
      >
        <template #default>
          <div class="student-alert-body">
            <span>{{ studentActionError }}</span>
            <el-button link type="primary" :loading="studentsLoading" @click="loadStudents">
              重新加载学生列表
            </el-button>
          </div>
        </template>
      </el-alert>
    </section>

    <AppFilterBar
      title="筛选与导入"
      description="先缩小学生范围，再执行导入或进入详情，避免在过长列表里盲目查找。"
      sticky
    >
      <div class="filter-grid">
        <el-input v-model="filters.student_no" placeholder="按学号筛选" :disabled="filterControlsDisabled" />
        <el-input v-model="filters.name" placeholder="按姓名筛选" :disabled="filterControlsDisabled" />
        <el-select
          v-model="filters.grade_id"
          clearable
          placeholder="选择年级"
          :loading="referenceLoading"
          :disabled="filterControlsDisabled || referenceLoading"
        >
          <el-option
            v-for="grade in referenceStore.grades"
            :key="grade.id"
            :label="grade.name"
            :value="grade.id"
          />
        </el-select>
        <el-select
          v-model="filters.class_id"
          clearable
          placeholder="选择班级"
          :loading="referenceLoading"
          :disabled="filterControlsDisabled || referenceLoading"
        >
          <el-option
            v-for="schoolClass in referenceStore.classes"
            :key="schoolClass.id"
            :label="schoolClass.name"
            :value="schoolClass.id"
          />
        </el-select>
      </div>
      <el-alert
        v-if="importActionError"
        class="student-list-alert"
        type="error"
        :title="importActionError"
        show-icon
        :closable="false"
      >
        <template #default>
          <el-button link type="primary" @click="openFile('/api/students/template')">
            重新下载导入模板
          </el-button>
        </template>
      </el-alert>
      <ImportFeedbackPanel :result="importResult" />
      <template #actions>
        <el-button type="primary" :loading="studentsLoading" :disabled="filterControlsDisabled" @click="searchStudents">
          查询
        </el-button>
        <el-button :disabled="filterControlsDisabled" @click="resetFilters">重置</el-button>
        <el-select v-model="importStrategy" style="width: 180px" :disabled="studentsLoading || importingStudents">
          <el-option label="跳过已存在" value="skip_existing" />
          <el-option label="更新已有记录" value="update" />
          <el-option label="仅新增" value="create" />
        </el-select>
        <el-upload
          :show-file-list="false"
          :auto-upload="false"
          :disabled="studentsLoading || importingStudents"
          :on-change="handleImport"
          accept=".xlsx,.xls"
        >
          <el-button :loading="importingStudents">导入学生</el-button>
        </el-upload>
      </template>
    </AppFilterBar>

    <AppSectionCard
      title="升学画像批量维护"
      description="批量补充选科组合、考生类型、身份意向、目标地区、就业方向等推荐工作台需要的字段。空白单元格会保留系统已有值。"
    >
      <div class="action-row import-row pathway-profile-actions">
        <el-button :disabled="pathwayProfileActionsDisabled" @click="openFile(pathwayProfileBulkEndpoints.template)">
          升学画像模板
        </el-button>
        <el-button :disabled="pathwayProfileActionsDisabled" @click="openFile(pathwayProfileBulkEndpoints.export)">
          下载画像数据
        </el-button>
        <el-upload
          :show-file-list="false"
          :auto-upload="false"
          :disabled="pathwayProfileActionsDisabled"
          :on-change="handlePathwayProfileImport"
          accept=".xlsx,.xls"
        >
          <el-button type="primary" :loading="importingPathwayProfile">上传画像</el-button>
        </el-upload>
      </div>
      <el-alert
        v-if="pathwayProfileImportActionError"
        class="student-list-alert"
        type="error"
        :title="pathwayProfileImportActionError"
        show-icon
        :closable="false"
      >
        <template #default>
          <el-button link type="primary" @click="openFile(pathwayProfileBulkEndpoints.template)">
            重新下载画像模板
          </el-button>
        </template>
      </el-alert>
      <ImportFeedbackPanel :result="pathwayProfileImportResult" />
    </AppSectionCard>

    <AppTableShell
      title="学生列表"
      description="列表保留基础身份、当前班级、生源地和联系方式，详情页承接更深的信息。"
    >
      <template #actions>
        <div class="list-action-stack">
          <span class="panel-caption">共 {{ students.total }} 条</span>
          <div class="bulk-action-controls">
            <span class="bulk-action-label">批量操作</span>
            <span class="bulk-selection-count">已选 {{ selectedRows.length }} 名</span>
            <el-button
              type="primary"
              plain
              :icon="TransferIcon"
              :disabled="bulkActionsDisabled || referenceLoading || !referenceStore.classes.length"
              @click="openClassTransferDialog"
            >
              批量调班
            </el-button>
            <el-button
              type="danger"
              plain
              :icon="DeleteIcon"
              :disabled="bulkActionsDisabled"
              @click="openBulkDeleteDialog"
            >
              批量删除学生
            </el-button>
          </div>
        </div>
      </template>
      <el-alert
        v-if="studentsLoadError"
        class="student-list-alert"
        type="error"
        :title="studentsLoadError"
        show-icon
        :closable="false"
      >
        <template #default>
          <el-button size="small" @click="loadStudents">重新加载</el-button>
        </template>
      </el-alert>
      <div v-loading="studentsLoading" class="student-table-body">
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
              <el-button link :disabled="studentsLoading" @click="openDetail(row)">详情</el-button>
              <el-button
                link
                type="primary"
                :loading="editingStudentId === row.id"
                :disabled="studentsLoading"
                @click="openEdit(row)"
              >
                编辑
              </el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="studentEmptyDescription">
              <el-button v-if="studentsLoadError" type="primary" plain :loading="studentsLoading" @click="loadStudents">
                重新加载学生列表
              </el-button>
            </el-empty>
          </template>
        </el-table>
      </div>
      <div class="pager-row">
        <el-pagination
          background
          layout="prev, pager, next, total"
          :current-page="page"
          :page-size="pageSize"
          :total="students.total"
          :disabled="studentsLoading"
          @current-change="handlePageChange"
        />
      </div>
    </AppTableShell>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="760px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form label-width="110px" :disabled="studentFormDisabled">
        <el-alert
          v-if="referenceLoadError"
          class="student-list-alert"
          type="warning"
          show-icon
          :closable="false"
          title="基础选项加载失败，年级、班级、学生状态、类别等下拉项可能不完整。"
        >
          <template #default>
            <el-button link type="primary" :loading="referenceLoading" @click="loadReferenceOptions">
              重新加载基础选项
            </el-button>
          </template>
        </el-alert>
        <el-alert
          v-if="studentFormActionError"
          class="student-list-alert"
          type="error"
          :title="studentFormActionError"
          show-icon
          :closable="false"
        />
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
            <el-select
              v-model="formState.current_grade_id"
              clearable
              filterable
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
              <el-option
                v-for="grade in referenceStore.grades"
                :key="grade.id"
                :label="grade.name"
                :value="grade.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="班级">
            <el-select
              v-model="formState.current_class_id"
              clearable
              filterable
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
              <el-option
                v-for="schoolClass in referenceStore.classes"
                :key="schoolClass.id"
                :label="schoolClass.name"
                :value="schoolClass.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="学生状态">
            <el-select
              v-model="formState.status"
              clearable
              filterable
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
              <el-option
                v-for="item in referenceStore.dicts.student_status ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="学生类别">
            <el-select
              v-model="formState.student_type"
              clearable
              filterable
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
              <el-option
                v-for="item in referenceStore.dicts.student_type ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="艺体方向">
            <el-select
              v-model="formState.art_track"
              clearable
              filterable
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
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
        <el-button :disabled="submitting" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <StudentBulkDeleteDialog
      v-model="bulkDeleteDialogVisible"
      :student-ids="bulkDeleteStudentIds"
      :student-labels="bulkDeleteStudentLabels"
      @completed="handleBulkDeleteCompleted"
    />
    <StudentClassTransferDialog
      v-model="classTransferDialogVisible"
      :student-ids="classTransferStudentIds"
      :student-labels="classTransferStudentLabels"
      :class-options="referenceStore.classes"
      @completed="handleClassTransferCompleted"
    />
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { Delete as DeleteIcon, Switch as TransferIcon } from "@element-plus/icons-vue";
import ElMessage from "element-plus/es/components/message/index";
import type { UploadFile } from "element-plus";
import type { components as StudentApiSchemas } from "../types/api.generated";

type StudentPayloadSchema = StudentApiSchemas["schemas"]["StudentPayload"];
import { useRouter } from "vue-router";

import { apiRequest, openFile, uploadFile } from "../api/client";
import { api } from "../api/typedClient";
import ImportFeedbackPanel from "../components/common/ImportFeedbackPanel.vue";
import StudentBulkDeleteDialog from "../components/students/StudentBulkDeleteDialog.vue";
import StudentClassTransferDialog from "../components/students/StudentClassTransferDialog.vue";
import { pathwayProfileBulkEndpoints } from "../components/students/pathwayProfileBulk";
import {
  AppFilterBar,
  AppPage,
  AppSectionCard,
  AppStatGrid,
  AppTableShell,
  type PageMetaItem,
  type StatCardItem,
} from "../components/ui";
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
const referenceLoading = ref(false);
const referenceLoadError = ref("");
const studentsLoading = ref(false);
const studentsLoadError = ref("");
const importingStudents = ref(false);
const importingPathwayProfile = ref(false);
const editingStudentId = ref<number | null>(null);
const importResult = ref<ImportFeedbackResult | null>(null);
const pathwayProfileImportResult = ref<ImportFeedbackResult | null>(null);
const studentActionError = ref("");
const importActionError = ref("");
const pathwayProfileImportActionError = ref("");
const studentFormActionError = ref("");
const selectedRows = ref<StudentItem[]>([]);
const studentTableRef = ref<{ clearSelection: () => void } | null>(null);
const bulkDeleteDialogVisible = ref(false);
const bulkDeleteStudentIds = ref<number[]>([]);
const bulkDeleteStudentLabels = ref<string[]>([]);
const classTransferDialogVisible = ref(false);
const classTransferStudentIds = ref<number[]>([]);
const classTransferStudentLabels = ref<string[]>([]);

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
const studentsLoadFailed = computed(() => Boolean(studentsLoadError.value && !students.items.length));
const filterControlsDisabled = computed(() => studentsLoading.value || importingStudents.value);
const bulkActionsDisabled = computed(
  () => selectedRows.value.length === 0 || studentsLoading.value || importingStudents.value,
);
const pathwayProfileActionsDisabled = computed(
  () => studentsLoading.value || importingStudents.value || importingPathwayProfile.value,
);
const studentFormDisabled = computed(() => submitting.value);
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
const studentPageMeta = computed<PageMetaItem[]>(() => [
  { label: "学生总数", value: studentsLoadFailed.value ? "加载失败" : students.total },
  { label: "当前页记录", value: studentsLoadFailed.value ? "加载失败" : students.items.length },
  { label: "已选学生", value: selectedRows.value.length },
  { label: "启用筛选", value: activeFilterCount.value },
  { label: "导入策略", value: importStrategyLabel.value },
]);
const studentEmptyDescription = computed(() => {
  if (studentsLoading.value) return "正在加载学生列表";
  if (studentsLoadError.value) return "学生列表加载失败，请重新加载。";
  return activeFilterCount.value ? "没有找到符合当前筛选条件的学生" : "暂无学生记录，可以先新增或导入学生";
});
const selectedStudentIds = computed(() => selectedRows.value.map((student) => student.id));
const overviewCards = computed<StatCardItem[]>(() => [
  ...(studentsLoadFailed.value
    ? [
        {
          label: "当前页班级",
          value: "加载失败",
          help: "学生列表接口失败，请重新加载学生列表。",
          tone: "danger" as const,
        },
        {
          label: "艺体方向",
          value: "加载失败",
          help: "当前无法统计艺体方向维护情况。",
          tone: "danger" as const,
        },
        {
          label: "生源地",
          value: "加载失败",
          help: "当前无法统计高考生源地维护情况。",
          tone: "danger" as const,
        },
        {
          label: "联系电话",
          value: "加载失败",
          help: "当前无法统计联系电话维护情况。",
          tone: "danger" as const,
        },
      ]
    : [
        {
          label: "当前页班级",
          value: new Set(students.items.map((item) => item.current_class_name).filter(Boolean)).size,
          help: "当前筛选结果页覆盖的班级数量。",
          tone: "primary" as const,
          loading: studentsLoading.value,
        },
        {
          label: "艺体方向",
          value: students.items.filter((item) => item.art_track).length,
          help: "当前结果页里已标记艺体方向的学生。",
          tone: "warning" as const,
          loading: studentsLoading.value,
        },
        {
          label: "生源地",
          value: students.items.filter((item) => item.origin_province).length,
          help: "当前结果页里已维护高考生源地的学生。",
          tone: "success" as const,
          loading: studentsLoading.value,
        },
        {
          label: "联系电话",
          value: students.items.filter((item) => item.phone).length,
          help: "当前结果页里已填写联系电话的学生。",
          tone: "neutral" as const,
          loading: studentsLoading.value,
        },
      ]),
]);

function resolveDictName(dictCode: string, code?: string | null): string {
  if (!code) return "-";
  return (
    referenceStore.dicts[dictCode]?.find((item) => String(item.code) === String(code))?.name ?? code
  );
}

function resetForm(): void {
  studentFormActionError.value = "";
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

async function loadReferenceOptions(): Promise<void> {
  referenceLoading.value = true;
  referenceLoadError.value = "";
  try {
    await referenceStore.loadAll();
  } catch (error) {
    referenceLoadError.value = (error as Error).message || "基础选项加载失败";
  } finally {
    referenceLoading.value = false;
  }
}

async function loadStudents(): Promise<void> {
  studentsLoading.value = true;
  studentsLoadError.value = "";
  studentActionError.value = "";
  try {
    const payload = await api.get("/api/students", {
      query: {
        page: page.value,
        page_size: pageSize.value,
        student_no: filters.student_no || null,
        name: filters.name || null,
        grade_id: filters.grade_id ?? null,
        class_id: filters.class_id ?? null,
      },
    });
    Object.assign(students, payload);
    clearSelectedStudents();
  } catch (error) {
    const message = (error as Error).message || "学生列表加载失败";
    studentsLoadError.value = message;
    Object.assign(students, {
      items: [],
      total: 0,
      page: page.value,
      page_size: pageSize.value,
    });
    clearSelectedStudents();
    ElMessage.error(message);
  } finally {
    studentsLoading.value = false;
  }
}

function searchStudents(): void {
  page.value = 1;
  void loadStudents();
}

function resetFilters(): void {
  void resetFiltersAndReload();
}

async function resetFiltersAndReload(): Promise<void> {
  filters.student_no = "";
  filters.name = "";
  filters.grade_id = undefined;
  filters.class_id = undefined;
  page.value = 1;
  try {
    await loadStudents();
  } catch (error) {
    ElMessage.error((error as Error).message || "重置筛选后刷新学生列表失败");
  }
}

function openCreate(): void {
  editingId.value = null;
  studentActionError.value = "";
  studentFormActionError.value = "";
  resetForm();
  dialogVisible.value = true;
}

async function openEdit(row: StudentItem): Promise<void> {
  editingStudentId.value = row.id;
  studentActionError.value = "";
  studentFormActionError.value = "";
  try {
    const detail = await apiRequest<Record<string, unknown>>(`/api/students/${row.id}`);
    editingId.value = row.id;
    resetForm();
    Object.assign(formState, detail);
    dialogVisible.value = true;
  } catch (error) {
    studentActionError.value = (error as Error).message || "学生详情加载失败";
    ElMessage.error(studentActionError.value);
  } finally {
    editingStudentId.value = null;
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

function openClassTransferDialog(): void {
  if (!selectedRows.value.length) {
    ElMessage.warning("请先勾选需要调班的学生");
    return;
  }
  classTransferStudentIds.value = selectedStudentIds.value;
  classTransferStudentLabels.value = selectedRows.value.map(formatStudentLabel);
  classTransferDialogVisible.value = true;
}

async function handleClassTransferCompleted(): Promise<void> {
  try {
    await Promise.all([loadReferenceOptions(), loadStudents()]);
  } catch (error) {
    ElMessage.error((error as Error).message || "调班完成后刷新数据失败");
  }
}

async function submitForm(): Promise<void> {
  studentFormActionError.value = "";
  if (!String(formState.student_no ?? "").trim() || !String(formState.name ?? "").trim()) {
    studentFormActionError.value = "学号和姓名不能为空";
    ElMessage.warning(studentFormActionError.value);
    return;
  }
  try {
    submitting.value = true;
    if (editingId.value) {
      await api.put("/api/students/{student_id}", {
        path: { student_id: editingId.value },
        body: formState as unknown as StudentPayloadSchema,
      });
    } else {
      await api.post("/api/students", { body: formState as unknown as StudentPayloadSchema });
    }
    ElMessage.success("学生保存成功");
    dialogVisible.value = false;
    await Promise.all([loadReferenceOptions(), loadStudents()]);
  } catch (error) {
    studentFormActionError.value = (error as Error).message || "学生保存失败";
    ElMessage.error(studentFormActionError.value);
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
  importingStudents.value = true;
  importActionError.value = "";
  try {
    importResult.value = null;
    importResult.value = await uploadFile<ImportFeedbackResult>("/api/students/import", uploadFileItem.raw, {
      strategy: importStrategy.value,
    });
    ElMessage({
      type: importResult.value.failed_rows ? "warning" : "success",
      message: importResult.value.message,
    });
    await Promise.all([loadReferenceOptions(), loadStudents()]);
  } catch (error) {
    importActionError.value = (error as Error).message || "学生导入失败";
    ElMessage.error(importActionError.value);
  } finally {
    importingStudents.value = false;
  }
}

async function handlePathwayProfileImport(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw) {
    return;
  }
  importingPathwayProfile.value = true;
  pathwayProfileImportActionError.value = "";
  try {
    pathwayProfileImportResult.value = null;
    pathwayProfileImportResult.value = await uploadFile<ImportFeedbackResult>(
      pathwayProfileBulkEndpoints.import,
      uploadFileItem.raw,
    );
    ElMessage({
      type: pathwayProfileImportResult.value.failed_rows ? "warning" : "success",
      message: pathwayProfileImportResult.value.message,
    });
    await loadStudents();
  } catch (error) {
    pathwayProfileImportActionError.value = (error as Error).message || "升学画像导入失败";
    ElMessage.error(pathwayProfileImportActionError.value);
  } finally {
    importingPathwayProfile.value = false;
  }
}

function handlePageChange(nextPage: number): void {
  page.value = nextPage;
  void loadStudents();
}

onMounted(async () => {
  await Promise.all([loadReferenceOptions(), loadStudents()]);
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
.import-row {
  margin-top: 14px;
  align-items: center;
}

.pathway-profile-actions {
  justify-content: flex-start;
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

.student-list-alert {
  margin-bottom: 14px;
}

.student-status-stack {
  display: grid;
  gap: 12px;
}

.student-alert-body {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
}

.student-table-body {
  min-height: 220px;
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

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .list-action-stack {
    justify-content: flex-start;
  }
}
</style>
