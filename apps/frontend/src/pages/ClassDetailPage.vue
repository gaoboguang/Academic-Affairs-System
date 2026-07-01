<template>
  <AppPage
    :title="profile?.overview.class_name ?? '班级详情'"
    eyebrow="基础台账 / 班级档案"
    description="集中查看班主任、任课教师、学生名单、班级荣誉和可跳转的分析输出。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button @click="router.push('/classes')">返回速览</el-button>
      <el-button :disabled="!profile || profileLoading || savingClass" @click="openClassEdit">编辑班级</el-button>
      <el-button :disabled="!profile || profileLoading || optionsLoading || savingAssignment" @click="openAssignmentDialog">
        设置任课教师
      </el-button>
      <el-button type="primary" :disabled="!profile || profileLoading || savingHonor" @click="openHonorDialog()">新增荣誉</el-button>
    </template>

    <el-alert
      v-if="optionsLoadError"
      class="class-detail-alert"
      type="error"
      :title="optionsLoadError"
      show-icon
      :closable="false"
    >
      <template #default>
        <el-button size="small" :loading="optionsLoading" @click="loadOptionsWithFeedback">重新加载基础选项</el-button>
      </template>
    </el-alert>

    <el-alert
      v-if="profileLoadError"
      class="class-detail-alert"
      type="error"
      :title="profileLoadError"
      show-icon
      :closable="false"
    >
      <template #default>
        <el-button size="small" :loading="profileLoading" @click="loadProfileWithFeedback">重新加载班级档案</el-button>
      </template>
    </el-alert>

    <el-alert
      v-if="classActionError"
      class="class-detail-alert"
      type="error"
      :title="classActionError"
      show-icon
      :closable="false"
    >
      <template #default>
        <el-button size="small" :loading="profileLoading" @click="loadProfileWithFeedback">刷新班级档案</el-button>
      </template>
    </el-alert>

    <div v-loading="loading || profileLoading" class="class-detail-body">
      <template v-if="profile">
      <AppStatGrid :items="profileCards" :columns="5" />

      <AppSectionCard title="班级概览" description="班级对象的核心台账和最近教学信号。">
        <div class="class-summary-grid">
          <article class="summary-panel">
            <span>班主任</span>
            <strong>{{ profile.overview.head_teacher_name ?? '未维护' }}</strong>
            <p>{{ resolveClassType(profile.overview.class_type) }} · {{ profile.overview.grade_name ?? '-' }}</p>
          </article>
          <article class="summary-panel">
            <span>任课教师</span>
            <strong>{{ formatClassTeachers(profile.overview.teacher_summary, 5) }}</strong>
            <p>当前学期 {{ profile.overview.teacher_count }} 位教师。</p>
          </article>
          <article class="summary-panel">
            <span>最近考试</span>
            <strong>{{ profile.overview.score_summary.exam_name ?? '暂无考试样本' }}</strong>
            <p>样本 {{ profile.overview.score_summary.sample_count }}，均分 {{ formatScore(profile.overview.score_summary.average_score) }}</p>
          </article>
        </div>
      </AppSectionCard>

      <el-tabs v-model="activeTab" class="profile-tabs">
        <el-tab-pane label="学生" name="students">
          <AppFilterBar title="学生名单" description="按学生状态和类别筛选，点击姓名进入学生详情。" :sticky="false">
            <div class="filter-grid detail-filter-grid">
              <el-select v-model="studentFilters.status" clearable placeholder="学生状态" :disabled="profileLoading || optionsLoading">
                <el-option
                  v-for="item in referenceStore.dicts.student_status ?? []"
                  :key="String(item.code)"
                  :label="item.name"
                  :value="item.code"
                />
              </el-select>
              <el-select
                v-model="studentFilters.studentType"
                clearable
                placeholder="学生类别"
                :disabled="profileLoading || optionsLoading"
              >
                <el-option
                  v-for="item in referenceStore.dicts.student_type ?? []"
                  :key="String(item.code)"
                  :label="item.name"
                  :value="item.code"
                />
              </el-select>
            </div>
          </AppFilterBar>
          <AppTableShell>
            <el-table v-loading="profileLoading" :data="filteredStudents" stripe>
              <template #empty>
                <el-empty :description="studentEmptyDescription" />
              </template>
              <el-table-column label="学号" prop="student_no" min-width="120" />
              <el-table-column label="姓名" min-width="120">
                <template #default="{ row }">
                  <el-button link type="primary" @click="router.push(`/students/${row.id}`)">{{ row.name }}</el-button>
                </template>
              </el-table-column>
              <el-table-column label="性别" prop="gender" width="80" />
              <el-table-column label="状态" min-width="100">
                <template #default="{ row }">{{ resolveDictName('student_status', row.status) }}</template>
              </el-table-column>
              <el-table-column label="类别" min-width="110">
                <template #default="{ row }">{{ resolveDictName('student_type', row.student_type) }}</template>
              </el-table-column>
              <el-table-column label="艺体方向" prop="art_track" min-width="100" />
              <el-table-column label="电话" prop="phone" min-width="130" />
            </el-table>
          </AppTableShell>
        </el-tab-pane>

        <el-tab-pane label="任课教师" name="teachers">
          <AppTableShell title="任课教师" description="按当前学期展示班级任课关系。">
            <template #actions>
              <el-button
                type="primary"
                plain
                :disabled="profileLoading || optionsLoading || savingAssignment"
                @click="openAssignmentDialog"
              >
                新增任教关系
              </el-button>
            </template>
            <el-table v-loading="profileLoading" :data="profile.assignments" stripe>
              <template #empty>
                <el-empty description="当前学期暂无任课关系。">
                  <el-button
                    type="primary"
                    plain
                    :disabled="profileLoading || optionsLoading || savingAssignment"
                    @click="openAssignmentDialog"
                  >
                    设置任课教师
                  </el-button>
                </el-empty>
              </template>
              <el-table-column label="教师" prop="teacher_name" min-width="120" />
              <el-table-column label="学科" prop="subject_name" min-width="110" />
              <el-table-column label="课程类型" min-width="110">
                <template #default="{ row }">{{ resolveDictName('course_type', row.course_type) }}</template>
              </el-table-column>
              <el-table-column label="周课时" prop="weekly_periods_manual" width="100" />
              <el-table-column label="学期" prop="semester_name" min-width="170" />
            </el-table>
          </AppTableShell>
        </el-tab-pane>

        <el-tab-pane label="荣誉" name="honors">
          <AppTableShell title="班级荣誉" description="结构化记录班级荣誉，便于后续统计、筛选和导出。">
            <template #actions>
              <el-button type="primary" :disabled="profileLoading || savingHonor" @click="openHonorDialog()">新增荣誉</el-button>
            </template>
            <el-table v-loading="profileLoading" :data="profile.honors" stripe>
              <template #empty>
                <el-empty description="暂无班级荣誉。" />
              </template>
              <el-table-column label="荣誉" prop="title" min-width="180" />
              <el-table-column label="级别" prop="honor_level" min-width="100" />
              <el-table-column label="日期" prop="awarded_on" width="120" />
              <el-table-column label="来源" prop="source" min-width="140" />
              <el-table-column label="备注" prop="note" min-width="180" />
              <el-table-column label="操作" width="140" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" :disabled="profileLoading || savingHonor || deletingHonorId !== null" @click="openHonorDialog(row)">
                    编辑
                  </el-button>
                  <el-button
                    link
                    type="danger"
                    :loading="deletingHonorId === row.id"
                    :disabled="profileLoading || savingHonor || (deletingHonorId !== null && deletingHonorId !== row.id)"
                    @click="deleteHonor(row)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </AppTableShell>
        </el-tab-pane>

        <el-tab-pane label="分析与输出" name="outputs">
          <div class="action-card-grid">
            <article class="action-card" @click="router.push(`/analytics?class_id=${classId}`)">
              <strong>班级成绩分析</strong>
              <p>进入分析中心查看当前班级在指定考试下的学科拆分和均分表现。</p>
            </article>
            <article class="action-card" @click="openClassAnalysisPrint">
              <strong>打印班级分析</strong>
              <p>如果当前速览绑定了考试，可直接打开班级分析打印预览。</p>
            </article>
            <article class="action-card" @click="router.push(`/analytics?adviser_class_id=${classId}`)">
              <strong>班主任驾驶舱</strong>
              <p>查看成绩波动、成长档案、规划任务和学生跟进清单。</p>
            </article>
            <article class="action-card" @click="router.push('/reports')">
              <strong>报表中心</strong>
              <p>统一导出班级分析、周报和跟进材料。</p>
            </article>
          </div>
        </el-tab-pane>
      </el-tabs>
      </template>
      <el-empty v-else :description="classDetailEmptyDescription">
        <el-button v-if="profileLoadError" type="primary" plain :loading="profileLoading" @click="loadProfileWithFeedback">
          重新加载班级档案
        </el-button>
      </el-empty>
    </div>

    <el-dialog v-model="classDialogVisible" title="编辑班级" width="620px" destroy-on-close>
      <el-form label-width="100px" :disabled="classFormDisabled">
        <el-form-item label="所属年级">
          <el-select v-model="classForm.grade_id" :loading="optionsLoading" style="width: 100%">
            <el-option v-for="grade in referenceStore.grades" :key="grade.id" :label="grade.name" :value="grade.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级名称">
          <el-input v-model="classForm.name" />
        </el-form-item>
        <el-form-item label="班型">
          <el-select v-model="classForm.class_type" clearable :loading="optionsLoading" style="width: 100%">
            <el-option
              v-for="item in referenceStore.dicts.class_type ?? []"
              :key="String(item.code)"
              :label="item.name"
              :value="item.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="班主任">
          <el-select v-model="classForm.head_teacher_id" clearable filterable :loading="optionsLoading" style="width: 100%">
            <el-option v-for="teacher in teacherOptions" :key="teacher.id" :label="teacher.name" :value="teacher.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班额">
          <el-input-number v-model="classForm.student_count" :min="0" :max="300" style="width: 100%" />
        </el-form-item>
      </el-form>
      <el-alert v-if="classFormError" class="dialog-alert" type="error" :title="classFormError" show-icon :closable="false" />
      <template #footer>
        <el-button :disabled="savingClass" @click="classDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingClass" :disabled="optionsLoading" @click="saveClass">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="honorDialogVisible" :title="editingHonorId ? '编辑荣誉' : '新增荣誉'" width="620px" destroy-on-close>
      <el-form label-width="100px" :disabled="honorFormDisabled">
        <el-form-item label="荣誉标题">
          <el-input v-model="honorForm.title" />
        </el-form-item>
        <el-form-item label="级别">
          <el-input v-model="honorForm.honor_level" placeholder="校级 / 市级 / 省级" />
        </el-form-item>
        <el-form-item label="获奖日期">
          <el-date-picker v-model="honorForm.awarded_on" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="honorForm.source" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="honorForm.note" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <el-alert v-if="honorFormError" class="dialog-alert" type="error" :title="honorFormError" show-icon :closable="false" />
      <template #footer>
        <el-button :disabled="savingHonor" @click="honorDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingHonor" @click="saveHonor">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="assignmentDialogVisible" title="新增任教关系" width="620px" destroy-on-close>
      <el-form label-width="100px" :disabled="assignmentFormDisabled">
        <el-form-item label="教师">
          <el-select v-model="assignmentForm.teacher_id" filterable :loading="optionsLoading" style="width: 100%">
            <el-option v-for="teacher in teacherOptions" :key="teacher.id" :label="teacher.name" :value="teacher.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学期">
          <el-select v-model="assignmentForm.semester_id" filterable :loading="optionsLoading" style="width: 100%">
            <el-option
              v-for="semester in referenceStore.semesters"
              :key="semester.id"
              :label="formatSemesterName(semester)"
              :value="semester.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="学科">
          <el-select v-model="assignmentForm.subject_id" clearable :loading="optionsLoading" style="width: 100%">
            <el-option v-for="subject in referenceStore.subjects" :key="subject.id" :label="subject.name" :value="subject.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程类型">
          <el-select v-model="assignmentForm.course_type" clearable :loading="optionsLoading" style="width: 100%">
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
      <el-alert v-if="assignmentFormError" class="dialog-alert" type="error" :title="assignmentFormError" show-icon :closable="false" />
      <template #footer>
        <el-button :disabled="savingAssignment" @click="assignmentDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingAssignment" :disabled="optionsLoading" @click="saveAssignment">保存</el-button>
      </template>
    </el-dialog>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";
import { useRoute, useRouter } from "vue-router";

import { apiRequest, openFile } from "../api/client";
import {
  AppFilterBar,
  AppPage,
  AppSectionCard,
  AppStatGrid,
  AppTableShell,
  type PageMetaItem,
  type StatCardItem,
} from "../components/ui";
import {
  buildClassProfileCards,
  formatClassTeachers,
  formatScore,
  type ClassHonorRead,
  type ClassProfileResponse,
  type StudentListItem,
} from "../components/classes/classProfile";
import { useReferenceStore, type OptionItem } from "../stores/reference";
import { formatUserActionError } from "../utils/userFeedback";

interface TeacherOption {
  id: number;
  name: string;
}

const route = useRoute();
const router = useRouter();
const referenceStore = useReferenceStore();
const classId = computed(() => Number(route.params.classId));
const loading = ref(false);
const optionsLoading = ref(false);
const profileLoading = ref(false);
const profile = ref<ClassProfileResponse | null>(null);
const teacherOptions = ref<TeacherOption[]>([]);
const optionsLoadError = ref("");
const profileLoadError = ref("");
const classActionError = ref("");
const activeTab = ref("students");
const classDialogVisible = ref(false);
const honorDialogVisible = ref(false);
const assignmentDialogVisible = ref(false);
const savingClass = ref(false);
const savingHonor = ref(false);
const savingAssignment = ref(false);
const editingHonorId = ref<number | null>(null);
const deletingHonorId = ref<number | null>(null);
const classFormError = ref("");
const honorFormError = ref("");
const assignmentFormError = ref("");
const studentFilters = reactive({
  status: "" as string | undefined,
  studentType: "" as string | undefined,
});
const classForm = reactive({
  grade_id: null as number | null,
  name: "",
  class_type: null as string | null,
  head_teacher_id: null as number | null,
  student_count: 0,
  is_active: true,
});
const honorForm = reactive({
  title: "",
  honor_level: "",
  awarded_on: null as string | null,
  source: "",
  note: "",
  is_active: true,
});
const assignmentForm = reactive({
  teacher_id: null as number | null,
  semester_id: null as number | null,
  grade_id: null as number | null,
  class_id: null as number | null,
  subject_id: null as number | null,
  course_type: null as string | null,
  weekly_periods_manual: 0,
  is_active: true,
});

const classFormDisabled = computed(() => savingClass.value || optionsLoading.value);
const honorFormDisabled = computed(() => savingHonor.value);
const assignmentFormDisabled = computed(() => savingAssignment.value || optionsLoading.value);
const pageMeta = computed<PageMetaItem[]>(() => [
  { label: "年级", value: profile.value?.overview.grade_name ?? "-" },
  { label: "班主任", value: profile.value?.overview.head_teacher_name ?? "未维护" },
  { label: "学生", value: profile.value?.overview.active_student_count ?? 0 },
  { label: "荣誉", value: profile.value?.overview.honor_count ?? 0 },
]);
const profileCards = computed<StatCardItem[]>(() =>
  buildClassProfileCards(profile.value).map((item) => ({
    ...item,
    loading: profileLoading.value,
  })),
);
const activeStudentFilterCount = computed(() => {
  let count = 0;
  if (studentFilters.status) count += 1;
  if (studentFilters.studentType) count += 1;
  return count;
});
const filteredStudents = computed<StudentListItem[]>(() =>
  (profile.value?.students ?? []).filter((item) => {
    if (studentFilters.status && item.status !== studentFilters.status) return false;
    if (studentFilters.studentType && item.student_type !== studentFilters.studentType) return false;
    return true;
  }),
);
const studentEmptyDescription = computed(() =>
  activeStudentFilterCount.value ? "没有符合筛选条件的学生。" : "当前班级暂无学生。",
);
const classDetailEmptyDescription = computed(() => {
  if (profileLoadError.value) return "班级档案加载失败，请重新加载。";
  if (loading.value || profileLoading.value) return "正在加载班级档案。";
  return "班级不存在或已停用。";
});

function readQueryValue(value: unknown): string | null {
  if (Array.isArray(value)) return typeof value[0] === "string" ? value[0] : null;
  return typeof value === "string" ? value : null;
}

function applyRouteIntent(): void {
  const tab = readQueryValue(route.query.tab);
  if (tab && ["students", "teachers", "honors", "outputs"].includes(tab)) {
    activeTab.value = tab;
  }
  if (
    readQueryValue(route.query.action) === "assignment"
    && activeTab.value === "teachers"
    && profile.value
    && !assignmentDialogVisible.value
  ) {
    openAssignmentDialog();
  }
}

function formatSemesterName(item: OptionItem): string {
  return `${item.academic_year_name ?? ""} ${item.name}`.trim();
}

function resolveDictName(dictCode: string, code?: string | null): string {
  if (!code) return "-";
  return referenceStore.dicts[dictCode]?.find((item) => String(item.code) === String(code))?.name ?? code;
}

function resolveClassType(code?: string | null): string {
  return resolveDictName("class_type", code);
}

async function loadOptions(): Promise<void> {
  await referenceStore.loadAll();
  const payload = await apiRequest<{ items: TeacherOption[] }>("/api/teachers?page=1&page_size=200");
  teacherOptions.value = payload.items;
}

async function loadProfile(): Promise<void> {
  profile.value = await apiRequest<ClassProfileResponse>(`/api/classes/${classId.value}/profile`);
}

async function loadOptionsWithFeedback(): Promise<void> {
  try {
    optionsLoading.value = true;
    optionsLoadError.value = "";
    await loadOptions();
  } catch (error) {
    teacherOptions.value = [];
    optionsLoadError.value = formatUserActionError(
      "加载班级基础选项",
      error,
      "确认本地后端服务正常运行后，点击重新加载基础选项。",
    );
    ElMessage.error(optionsLoadError.value);
  } finally {
    optionsLoading.value = false;
  }
}

async function loadProfileWithFeedback(): Promise<void> {
  try {
    profileLoading.value = true;
    profileLoadError.value = "";
    await loadProfile();
    classActionError.value = "";
    applyRouteIntent();
  } catch (error) {
    profile.value = null;
    profileLoadError.value = formatUserActionError(
      "加载班级档案",
      error,
      "确认班级仍然启用且本地后端服务正常运行后，点击重新加载班级档案。",
    );
    ElMessage.error(profileLoadError.value);
  } finally {
    profileLoading.value = false;
  }
}

async function reloadAll(): Promise<void> {
  loading.value = true;
  await Promise.all([loadOptionsWithFeedback(), loadProfileWithFeedback()]);
  loading.value = false;
}

function openClassEdit(): void {
  if (!profile.value) return;
  classFormError.value = "";
  Object.assign(classForm, {
    grade_id: profile.value.overview.grade_id,
    name: profile.value.overview.class_name,
    class_type: profile.value.overview.class_type,
    head_teacher_id: profile.value.overview.head_teacher_id,
    student_count: profile.value.overview.student_count,
    is_active: true,
  });
  classDialogVisible.value = true;
}

async function saveClass(): Promise<void> {
  if (!classForm.grade_id || !classForm.name.trim()) {
    classFormError.value = "年级和班级名称不能为空";
    ElMessage.warning(classFormError.value);
    return;
  }
  try {
    savingClass.value = true;
    classFormError.value = "";
    await apiRequest(`/api/base/classes/${classId.value}`, {
      method: "PUT",
      body: JSON.stringify(classForm),
    });
    ElMessage.success("班级保存成功");
    classDialogVisible.value = false;
    await loadProfileWithFeedback();
  } catch (error) {
    classFormError.value = formatUserActionError("保存班级", error, "检查年级、班级名称和班主任后重试。");
    ElMessage.error(classFormError.value);
  } finally {
    savingClass.value = false;
  }
}

function resetHonorForm(): void {
  editingHonorId.value = null;
  honorFormError.value = "";
  Object.assign(honorForm, {
    title: "",
    honor_level: "",
    awarded_on: null,
    source: "",
    note: "",
    is_active: true,
  });
}

function openHonorDialog(row?: ClassHonorRead): void {
  resetHonorForm();
  if (row) {
    editingHonorId.value = row.id;
    Object.assign(honorForm, {
      title: row.title,
      honor_level: row.honor_level ?? "",
      awarded_on: row.awarded_on ?? null,
      source: row.source ?? "",
      note: row.note ?? "",
      is_active: row.is_active,
    });
  }
  honorDialogVisible.value = true;
}

async function saveHonor(): Promise<void> {
  if (!honorForm.title.trim()) {
    honorFormError.value = "荣誉标题不能为空";
    ElMessage.warning(honorFormError.value);
    return;
  }
  try {
    savingHonor.value = true;
    honorFormError.value = "";
    const path = editingHonorId.value
      ? `/api/classes/${classId.value}/honors/${editingHonorId.value}`
      : `/api/classes/${classId.value}/honors`;
    await apiRequest(path, {
      method: editingHonorId.value ? "PUT" : "POST",
      body: JSON.stringify(honorForm),
    });
    ElMessage.success("班级荣誉保存成功");
    honorDialogVisible.value = false;
    await loadProfileWithFeedback();
  } catch (error) {
    honorFormError.value = formatUserActionError("保存班级荣誉", error, "检查荣誉标题和日期格式后重试。");
    ElMessage.error(honorFormError.value);
  } finally {
    savingHonor.value = false;
  }
}

async function deleteHonor(row: ClassHonorRead): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认删除“${row.title}”？`, "删除班级荣誉", { type: "warning" });
    deletingHonorId.value = row.id;
    classActionError.value = "";
    await apiRequest(`/api/classes/${classId.value}/honors/${row.id}`, { method: "DELETE" });
    ElMessage.success("班级荣誉已删除");
    await loadProfileWithFeedback();
  } catch (error) {
    if (error instanceof Error) {
      classActionError.value = formatUserActionError("删除班级荣誉", error, "确认该荣誉仍可操作后重试。");
      ElMessage.error(classActionError.value);
    }
  } finally {
    if (deletingHonorId.value === row.id) {
      deletingHonorId.value = null;
    }
  }
}

function openAssignmentDialog(): void {
  if (!profile.value) return;
  activeTab.value = "teachers";
  assignmentFormError.value = "";
  assignmentForm.teacher_id = null;
  assignmentForm.semester_id = referenceStore.semesters.find((item) => item.is_current)?.id ?? referenceStore.semesters[0]?.id ?? null;
  assignmentForm.grade_id = profile.value?.overview.grade_id ?? null;
  assignmentForm.class_id = classId.value;
  assignmentForm.subject_id = null;
  assignmentForm.course_type = null;
  assignmentForm.weekly_periods_manual = 0;
  assignmentDialogVisible.value = true;
}

async function saveAssignment(): Promise<void> {
  if (!assignmentForm.teacher_id || !assignmentForm.semester_id) {
    assignmentFormError.value = "教师和学期不能为空";
    ElMessage.warning(assignmentFormError.value);
    return;
  }
  try {
    savingAssignment.value = true;
    assignmentFormError.value = "";
    await apiRequest("/api/teachers/assignments", {
      method: "POST",
      body: JSON.stringify(assignmentForm),
    });
    ElMessage.success("任教关系保存成功");
    assignmentDialogVisible.value = false;
    await loadProfileWithFeedback();
  } catch (error) {
    assignmentFormError.value = formatUserActionError("保存任教关系", error, "检查教师、学期、学科和课程类型后重试。");
    ElMessage.error(assignmentFormError.value);
  } finally {
    savingAssignment.value = false;
  }
}

function openClassAnalysisPrint(): void {
  const examId = profile.value?.overview.score_summary.exam_id;
  if (!examId) {
    ElMessage.warning("当前班级暂无可打印的考试样本");
    return;
  }
  openFile(`/print/class-analysis/${classId.value}/${examId}`);
}

watch(
  () => route.query,
  () => applyRouteIntent(),
);

watch(classId, () => {
  profile.value = null;
  void reloadAll();
});

onMounted(reloadAll);
</script>

<style scoped>
.class-detail-alert {
  margin-top: -4px;
}

.dialog-alert {
  margin-top: 12px;
}

.class-detail-body {
  display: grid;
  gap: 16px;
  min-height: 320px;
}

.class-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.summary-panel {
  display: grid;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: var(--bg-muted);
}

.summary-panel span {
  color: var(--text-muted);
  font-size: 12px;
}

.summary-panel strong {
  color: var(--text-main);
  font-size: 20px;
}

.summary-panel p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.detail-filter-grid {
  grid-template-columns: repeat(2, minmax(160px, 1fr));
}

.action-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.action-card {
  min-height: 130px;
  padding: 18px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: var(--bg-panel);
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

.action-card:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-soft);
}

.action-card strong {
  color: var(--text-main);
  font-size: 17px;
}

.action-card p {
  margin: 10px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}

@media (max-width: 900px) {
  .class-summary-grid,
  .detail-filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
