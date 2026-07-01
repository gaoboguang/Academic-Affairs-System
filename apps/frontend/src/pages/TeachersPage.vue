<template>
  <AppPage
    title="教师中心"
    eyebrow="基础台账 / 教师中心"
    description="维护教师基础信息、导入导出和任教关系，为教学分析、职称历史和工作量计算提供同一条数据链。"
    :meta="teacherPageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button @click="openFile('/api/teachers/template')">模板下载</el-button>
        <el-button @click="openFile('/api/teachers/export')">导出列表</el-button>
        <el-button type="primary" @click="openCreate">新增教师</el-button>
      </div>
    </template>

    <AppStatGrid :items="overviewCards" :columns="4" />

    <section v-if="referenceLoadError || teacherActionError" class="teacher-status-stack">
      <el-alert
        v-if="referenceLoadError"
        type="warning"
        title="教师中心基础选项加载失败"
        show-icon
        :closable="false"
      >
        <template #default>
          <div class="teacher-alert-body">
            <span>{{ referenceLoadError }}</span>
            <el-button link type="primary" :loading="referenceLoading" @click="loadReferenceOptions">
              重新加载基础选项
            </el-button>
          </div>
        </template>
      </el-alert>
      <el-alert
        v-if="teacherActionError"
        type="error"
        title="教师操作失败"
        show-icon
        :closable="false"
      >
        <template #default>
          <div class="teacher-alert-body">
            <span>{{ teacherActionError }}</span>
            <el-button link type="primary" :loading="teachersLoading" @click="loadTeachers">
              重新加载教师列表
            </el-button>
          </div>
        </template>
      </el-alert>
    </section>

    <AppFilterBar
      title="筛选与导入"
      description="先按工号、姓名或学科缩小范围，再处理批量导入和任教关系维护。"
      sticky
    >
      <div class="filter-grid">
        <el-input v-model="filters.teacher_no" placeholder="按工号筛选" :disabled="filterControlsDisabled" />
        <el-input v-model="filters.name" placeholder="按姓名筛选" :disabled="filterControlsDisabled" />
        <el-select
          v-model="filters.subject_id"
          clearable
          placeholder="选择学科"
          :loading="referenceLoading"
          :disabled="filterControlsDisabled || referenceLoading"
        >
          <el-option
            v-for="subject in referenceStore.subjects"
            :key="subject.id"
            :label="subject.name"
            :value="subject.id"
          />
        </el-select>
      </div>
      <template #actions>
        <el-button type="primary" :loading="teachersLoading" :disabled="filterControlsDisabled" @click="loadTeachers">查询</el-button>
        <el-button :disabled="filterControlsDisabled" @click="resetFilters">重置</el-button>
        <el-select v-model="importStrategy" style="width: 180px" :disabled="importingTeachers || teachersLoading">
          <el-option label="跳过已存在" value="skip_existing" />
          <el-option label="更新已有记录" value="update" />
          <el-option label="仅新增" value="create" />
        </el-select>
        <el-upload
          :show-file-list="false"
          :auto-upload="false"
          :disabled="importingTeachers || teachersLoading"
          :on-change="handleImport"
          accept=".xlsx,.xls"
        >
          <el-button :loading="importingTeachers">导入教师</el-button>
        </el-upload>
        <el-button
          :loading="assignmentsLoading"
          :disabled="assignmentDialogActionDisabled"
          @click="openAssignmentDialog"
        >
          维护任教关系
        </el-button>
      </template>
      <el-alert
        v-if="importActionError"
        class="teacher-page-alert"
        type="error"
        :title="importActionError"
        show-icon
        :closable="false"
      >
        <template #default>
          <el-button link type="primary" @click="openFile('/api/teachers/template')">
            重新下载导入模板
          </el-button>
        </template>
      </el-alert>
      <ImportFeedbackPanel :result="importResult" />
    </AppFilterBar>

    <AppTableShell
      title="教师列表"
      description="列表先给出身份、学科和岗位视图，详情页再承接职称历史与考试表现。"
    >
      <template #actions>
        <span class="panel-caption">共 {{ teachers.total }} 条</span>
      </template>
      <el-alert
        v-if="teachersLoadError"
        class="teacher-page-alert"
        type="error"
        :title="teachersLoadError"
        show-icon
        :closable="false"
      >
        <template #default>
          <el-button size="small" @click="loadTeachers">重新加载</el-button>
        </template>
      </el-alert>
      <div v-loading="teachersLoading" class="teacher-table-body">
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
              <el-button link :disabled="teachersLoading" @click="openDetail(row)">详情</el-button>
              <el-button
                link
                type="primary"
                :loading="editingTeacherId === row.id"
                :disabled="teachersLoading"
                @click="openEdit(row)"
              >
                编辑
              </el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="teacherEmptyDescription">
              <el-button v-if="teachersLoadError" type="primary" plain :loading="teachersLoading" @click="loadTeachers">
                重新加载教师列表
              </el-button>
            </el-empty>
          </template>
        </el-table>
      </div>
    </AppTableShell>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="760px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleTeacherDialogClosed"
    >
      <el-form label-width="110px" :disabled="teacherFormDisabled">
        <el-alert
          v-if="referenceLoadError"
          class="teacher-page-alert"
          type="warning"
          show-icon
          :closable="false"
          title="基础选项加载失败，学科、职称、岗位等下拉项可能不完整。"
        >
          <template #default>
            <el-button link type="primary" :loading="referenceLoading" @click="loadReferenceOptions">
              重新加载基础选项
            </el-button>
          </template>
        </el-alert>
        <el-alert
          v-if="teacherFormActionError"
          class="teacher-page-alert"
          type="error"
          :title="teacherFormActionError"
          show-icon
          :closable="false"
        />
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
            <el-select
              v-model="formState.subject_id"
              clearable
              filterable
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
              <el-option
                v-for="subject in referenceStore.subjects"
                :key="subject.id"
                :label="subject.name"
                :value="subject.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="职称">
            <el-select
              v-model="formState.title_code"
              clearable
              filterable
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
              <el-option
                v-for="item in referenceStore.dicts.teacher_title ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="岗位">
            <el-select
              v-model="formState.position_code"
              clearable
              filterable
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
              <el-option
                v-for="item in referenceStore.dicts.teacher_position ?? []"
                :key="String(item.code)"
                :label="item.name"
                :value="item.code"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="任教状态">
            <el-select
              v-model="formState.employment_status"
              clearable
              filterable
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
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
        <el-button :disabled="submitting" @click="dialogVisible = false">取消</el-button>
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
          <el-button type="primary" :disabled="assignmentCreateDisabled" @click="openAssignmentCreate">
            新增任教关系
          </el-button>
        </div>
      </div>
      <el-alert
        v-if="assignmentsLoadError"
        class="teacher-page-alert"
        type="error"
        :title="assignmentsLoadError"
        show-icon
        :closable="false"
      >
        <template #default>
          <el-button size="small" @click="loadAssignments">重新加载</el-button>
        </template>
      </el-alert>
      <div v-loading="assignmentsLoading" class="table-shell assignment-table-body">
        <el-table :data="assignments" stripe>
          <el-table-column label="教师" prop="teacher_name" min-width="100" />
          <el-table-column label="学期" prop="semester_name" min-width="160" />
          <el-table-column label="年级" prop="grade_name" width="90" />
          <el-table-column label="班级" prop="class_name" width="90" />
          <el-table-column label="学科" prop="subject_name" width="100" />
          <el-table-column label="课程类型" prop="course_type" width="110" />
          <el-table-column label="周课时" prop="weekly_periods_manual" width="100" />
          <template #empty>
            <el-empty :description="assignmentEmptyDescription">
              <el-button
                v-if="assignmentsLoadError"
                type="primary"
                plain
                :loading="assignmentsLoading"
                @click="loadAssignments"
              >
                重新加载任教关系
              </el-button>
            </el-empty>
          </template>
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
        <el-form label-width="110px" :disabled="assignmentFormDisabled">
          <el-alert
            v-if="referenceLoadError"
            class="teacher-page-alert"
            type="warning"
            show-icon
            :closable="false"
            title="基础选项加载失败，学期、班级、学科或课程类型可能不完整。"
          >
            <template #default>
              <el-button link type="primary" :loading="referenceLoading" @click="loadReferenceOptions">
                重新加载基础选项
              </el-button>
            </template>
          </el-alert>
          <el-alert
            v-if="assignmentFormActionError"
            class="teacher-page-alert"
            type="error"
            :title="assignmentFormActionError"
            show-icon
            :closable="false"
          />
          <el-form-item label="教师">
            <el-select
              v-model="assignmentForm.teacher_id"
              filterable
              style="width: 100%"
              :loading="teachersLoading"
              :disabled="teachersLoading || !teachers.items.length"
            >
              <el-option
                v-for="teacher in teachers.items"
                :key="teacher.id"
                :label="teacher.name"
                :value="teacher.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="学期">
            <el-select
              v-model="assignmentForm.semester_id"
              filterable
              style="width: 100%"
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
              <el-option
                v-for="semester in referenceStore.semesters"
                :key="semester.id"
                :label="`${semester.academic_year_name ?? ''} ${semester.name}`"
                :value="semester.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="年级">
            <el-select
              v-model="assignmentForm.grade_id"
              clearable
              style="width: 100%"
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
              v-model="assignmentForm.class_id"
              clearable
              style="width: 100%"
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
          <el-form-item label="学科">
            <el-select
              v-model="assignmentForm.subject_id"
              clearable
              style="width: 100%"
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
              <el-option
                v-for="subject in referenceStore.subjects"
                :key="subject.id"
                :label="subject.name"
                :value="subject.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="课程类型">
            <el-select
              v-model="assignmentForm.course_type"
              clearable
              style="width: 100%"
              :loading="referenceLoading"
              :disabled="referenceLoading"
            >
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
          <el-button :disabled="assignmentSubmitting" @click="assignmentFormVisible = false">取消</el-button>
          <el-button type="primary" :loading="assignmentSubmitting" @click="submitAssignment">保存</el-button>
        </template>
      </el-dialog>
    </el-dialog>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import type { UploadFile } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { apiRequest, openFile, uploadFile } from "../api/client";
import ImportFeedbackPanel from "../components/common/ImportFeedbackPanel.vue";
import {
  AppFilterBar,
  AppPage,
  AppStatGrid,
  AppTableShell,
  type PageMetaItem,
  type StatCardItem,
} from "../components/ui";
import { useReferenceStore } from "../stores/reference";
import type { ImportFeedbackResult } from "../utils/importFeedback";

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

const referenceStore = useReferenceStore();
const route = useRoute();
const router = useRouter();
const importStrategy = ref("skip_existing");
const dialogVisible = ref(false);
const assignmentDialogVisible = ref(false);
const assignmentFormVisible = ref(false);
const editingId = ref<number | null>(null);
const submitting = ref(false);
const referenceLoading = ref(false);
const referenceLoadError = ref("");
const teachersLoading = ref(false);
const teachersLoadError = ref("");
const importingTeachers = ref(false);
const assignmentsLoading = ref(false);
const assignmentsLoadError = ref("");
const assignmentSubmitting = ref(false);
const editingTeacherId = ref<number | null>(null);
const importResult = ref<ImportFeedbackResult | null>(null);
const teacherActionError = ref("");
const importActionError = ref("");
const teacherFormActionError = ref("");
const assignmentFormActionError = ref("");

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
const teachersLoadFailed = computed(() => Boolean(teachersLoadError.value && !teachers.items.length));
const assignmentsLoadFailed = computed(() => Boolean(assignmentsLoadError.value && !assignments.value.length));
const filterControlsDisabled = computed(() => teachersLoading.value || importingTeachers.value);
const assignmentDialogActionDisabled = computed(
  () => assignmentsLoading.value || importingTeachers.value || teachersLoading.value,
);
const assignmentCreateDisabled = computed(
  () => assignmentsLoading.value || assignmentSubmitting.value || teachersLoading.value || referenceLoading.value,
);
const teacherFormDisabled = computed(() => submitting.value);
const assignmentFormDisabled = computed(() => assignmentSubmitting.value);
const importStrategyLabel = computed(() => {
  const mapping: Record<string, string> = {
    skip_existing: "跳过已存在",
    update: "更新已有记录",
    create: "仅新增",
  };
  return mapping[importStrategy.value] ?? importStrategy.value;
});
const activeFilterCount = computed(
  () => [filters.teacher_no, filters.name, filters.subject_id].filter(Boolean).length,
);
const teacherPageMeta = computed<PageMetaItem[]>(() => [
  { label: "教师总数", value: teachersLoadFailed.value ? "加载失败" : teachers.total },
  { label: "当前页", value: teachersLoadFailed.value ? "加载失败" : teachers.items.length },
  { label: "任教关系", value: assignmentsLoadFailed.value ? "加载失败" : assignments.value.length },
  { label: "启用筛选", value: activeFilterCount.value },
  { label: "导入策略", value: importStrategyLabel.value },
]);
const teacherEmptyDescription = computed(() => {
  if (teachersLoading.value) return "正在加载教师列表";
  if (teachersLoadError.value) return "教师列表加载失败，请重新加载。";
  return activeFilterCount.value ? "没有找到符合当前筛选条件的教师" : "暂无教师记录，可以先新增或导入教师";
});
const assignmentEmptyDescription = computed(() => {
  if (assignmentsLoading.value) return "正在加载任教关系";
  if (assignmentsLoadError.value) return "任教关系加载失败，请重新加载。";
  return "暂无任教关系，可以先新增任教关系或导入教师数据";
});
const overviewCards = computed<StatCardItem[]>(() => [
  ...(teachersLoadFailed.value
    ? [
        {
          label: "教师总数",
          value: "加载失败",
          help: "教师列表接口失败，请重新加载教师列表。",
          tone: "danger" as const,
        },
        {
          label: "学科覆盖",
          value: "加载失败",
          help: "当前无法统计学科覆盖数量。",
          tone: "danger" as const,
        },
        {
          label: "班主任",
          value: "加载失败",
          help: "当前无法统计班主任人数。",
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
          label: "教师总数",
          value: teachers.total,
          help: "当前筛选条件下的教师记录数量。",
          tone: "primary" as const,
          loading: teachersLoading.value,
        },
        {
          label: "学科覆盖",
          value: new Set(teachers.items.map((item) => item.subject_name).filter(Boolean)).size,
          help: "当前结果页覆盖的学科数量。",
          tone: "info" as const,
          loading: teachersLoading.value,
        },
        {
          label: "班主任",
          value: teachers.items.filter((item) => item.is_head_teacher).length,
          help: "当前结果页里标记为班主任的教师。",
          tone: "success" as const,
          loading: teachersLoading.value,
        },
        {
          label: "联系电话",
          value: teachers.items.filter((item) => item.phone).length,
          help: "当前结果页里已填写联系电话的教师。",
          tone: "neutral" as const,
          loading: teachersLoading.value,
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
  teacherFormActionError.value = "";
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

async function loadTeachers(): Promise<void> {
  teachersLoading.value = true;
  teachersLoadError.value = "";
  teacherActionError.value = "";
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
    const message = (error as Error).message || "教师列表加载失败";
    teachersLoadError.value = message;
    Object.assign(teachers, {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });
    ElMessage.error(message);
  } finally {
    teachersLoading.value = false;
  }
}

async function loadAssignments(): Promise<void> {
  assignmentsLoading.value = true;
  assignmentsLoadError.value = "";
  try {
    assignments.value = await apiRequest<AssignmentItem[]>("/api/teachers/assignments");
  } catch (error) {
    const message = (error as Error).message || "任教关系加载失败";
    assignmentsLoadError.value = message;
    assignments.value = [];
    ElMessage.error(message);
  } finally {
    assignmentsLoading.value = false;
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
  teacherActionError.value = "";
  teacherFormActionError.value = "";
  resetForm();
  dialogVisible.value = true;
}

async function openAssignmentDialog(): Promise<void> {
  assignmentDialogVisible.value = true;
  await loadAssignments();
}

function shouldOpenAssignmentsFromRoute(): boolean {
  const value = route.query.assignments;
  return value === "1" || value === "true";
}

async function applyRouteIntent(): Promise<void> {
  if (!shouldOpenAssignmentsFromRoute() || assignmentDialogVisible.value) return;
  await openAssignmentDialog();
}

async function openEdit(row: TeacherItem): Promise<void> {
  editingTeacherId.value = row.id;
  teacherActionError.value = "";
  teacherFormActionError.value = "";
  try {
    const detail = await apiRequest<Record<string, unknown>>(`/api/teachers/${row.id}`);
    editingId.value = row.id;
    resetForm();
    Object.assign(formState, detail);
    dialogVisible.value = true;
  } catch (error) {
    const message = (error as Error).message || "教师详情加载失败";
    teacherActionError.value = message;
    ElMessage.error(message);
  } finally {
    editingTeacherId.value = null;
  }
}

function openDetail(row: TeacherItem): void {
  router.push(`/teachers/${row.id}`);
}

async function submitForm(): Promise<void> {
  teacherFormActionError.value = "";
  if (!String(formState.teacher_no ?? "").trim() || !String(formState.name ?? "").trim()) {
    teacherFormActionError.value = "工号和姓名不能为空";
    ElMessage.warning(teacherFormActionError.value);
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
    teacherFormActionError.value = (error as Error).message || "教师保存失败";
    ElMessage.error(teacherFormActionError.value);
  } finally {
    submitting.value = false;
  }
}

async function handleImport(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw) {
    return;
  }
  importingTeachers.value = true;
  importActionError.value = "";
  try {
    importResult.value = null;
    importResult.value = await uploadFile<ImportFeedbackResult>("/api/teachers/import", uploadFileItem.raw, {
      strategy: importStrategy.value,
    });
    ElMessage({
      type: importResult.value.failed_rows ? "warning" : "success",
      message: importResult.value.message,
    });
    await Promise.all([loadTeachers(), loadAssignments()]);
  } catch (error) {
    importActionError.value = (error as Error).message || "教师导入失败";
    ElMessage.error(importActionError.value);
  } finally {
    importingTeachers.value = false;
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
  assignmentFormActionError.value = "";
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
  assignmentFormActionError.value = "";
  if (!assignmentForm.teacher_id || !assignmentForm.semester_id) {
    assignmentFormActionError.value = "教师和学期不能为空";
    ElMessage.warning(assignmentFormActionError.value);
    return;
  }
  assignmentSubmitting.value = true;
  try {
    await apiRequest("/api/teachers/assignments", {
      method: "POST",
      body: JSON.stringify(assignmentForm),
    });
    ElMessage.success("任教关系保存成功");
    assignmentFormVisible.value = false;
    await loadAssignments();
  } catch (error) {
    assignmentFormActionError.value = (error as Error).message || "任教关系保存失败";
    ElMessage.error(assignmentFormActionError.value);
  } finally {
    assignmentSubmitting.value = false;
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
  await Promise.all([loadReferenceOptions(), loadTeachers(), loadAssignments()]);
  await applyRouteIntent();
});

watch(
  () => route.query.assignments,
  () => {
    void applyRouteIntent();
  },
);
</script>

<style scoped>
.panel-caption {
  color: #6d8194;
  font-size: 13px;
}

.teacher-page-alert {
  margin-bottom: 14px;
}

.teacher-status-stack {
  display: grid;
  gap: 12px;
}

.teacher-alert-body {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
}

.teacher-table-body,
.assignment-table-body {
  min-height: 220px;
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

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
