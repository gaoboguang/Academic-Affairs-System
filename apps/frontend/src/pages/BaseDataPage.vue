<template>
  <AppPage
    title="基础数据"
    eyebrow="基础台账 / 主数据中心"
    description="集中维护学年、学期、年级、班级、学科和字典配置，保证学生、教师、考试、课表和报表共用同一套主数据。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button :disabled="allLoading" @click="router.push('/classes')">年级班级视图</el-button>
      <el-button type="primary" :loading="allLoading" @click="reloadAll(true)">刷新基础数据</el-button>
    </template>

    <section v-if="loadErrorItems.length" class="base-data-status-stack">
      <el-alert
        type="error"
        show-icon
        :closable="false"
        title="基础数据部分内容加载失败"
      >
        <template #default>
          <ul class="base-data-error-list">
            <li v-for="item in loadErrorItems" :key="item.label">
              <strong>{{ item.label }}</strong>
              <span>{{ item.message }}</span>
            </li>
          </ul>
          <div class="base-data-alert-actions">
            <el-button
              v-if="referenceLoadError"
              size="small"
              type="danger"
              plain
              :loading="referenceStore.loading"
              @click="loadReferenceData(true)"
            >
              重新加载引用数据
            </el-button>
            <el-button
              v-if="dictTypesLoadError"
              size="small"
              type="danger"
              plain
              :loading="dictTypesLoading"
              @click="loadDictTypes(true)"
            >
              重新加载字典类型
            </el-button>
            <el-button
              v-if="teacherOptionsLoadError"
              size="small"
              type="danger"
              plain
              :loading="teacherOptionsLoading"
              @click="loadTeacherOptions(true)"
            >
              重新加载教师选项
            </el-button>
          </div>
        </template>
      </el-alert>
    </section>

    <AppStatGrid :items="overviewCards" :columns="5" />

    <AppSectionCard
      title="主数据维护"
      description="这些数据会被后续导入、分析、报表和账号范围直接引用；修改前请确认名称与导入模板一致。"
    >
      <el-tabs class="base-data-tabs">
        <el-tab-pane label="学年">
          <BaseCrudSection
            title="学年"
            description="维护学年范围和当前学年。"
            endpoint="/api/base/academic-years"
            :columns="[
              { label: '名称', prop: 'name' },
              { label: '开始日期', prop: 'start_date' },
              { label: '结束日期', prop: 'end_date' },
              { label: '当前学年', prop: 'is_current' },
            ]"
            :fields="academicYearFields"
            :disabled="referenceStore.loading"
            :disabled-reason="referenceStore.loading ? '引用数据刷新中，暂不能维护学年。' : ''"
            @saved="reloadAll(false)"
          />
        </el-tab-pane>
        <el-tab-pane label="学期">
          <BaseCrudSection
            title="学期"
            description="学期用于后续考试、任教关系与课表统计。"
            endpoint="/api/base/semesters"
            :columns="[
              { label: '学年', prop: 'academic_year_name' },
              { label: '名称', prop: 'name' },
              { label: '开始日期', prop: 'start_date' },
              { label: '结束日期', prop: 'end_date' },
              { label: '周数', prop: 'week_count' },
            ]"
            :fields="semesterFields"
            :disabled="semesterSectionDisabled"
            :disabled-reason="semesterSectionDisabledReason"
            @saved="reloadAll(false)"
          />
        </el-tab-pane>
        <el-tab-pane label="年级">
          <BaseCrudSection
            title="年级"
            description="用于学生、班级、考试和任教范围。"
            endpoint="/api/base/grades"
            :columns="[
              { label: '名称', prop: 'name' },
              { label: '排序', prop: 'sort_order' },
              { label: '启用', prop: 'is_active' },
            ]"
            :fields="gradeFields"
            :disabled="referenceStore.loading"
            :disabled-reason="referenceStore.loading ? '引用数据刷新中，暂不能维护年级。' : ''"
            @saved="reloadAll(false)"
          />
        </el-tab-pane>
        <el-tab-pane label="班级">
          <BaseCrudSection
            title="班级"
            description="班级关联年级、班型和班主任。"
            endpoint="/api/base/classes"
            :columns="[
              { label: '年级', prop: 'grade_name' },
              { label: '班级名称', prop: 'name' },
              { label: '班型', prop: 'class_type' },
              { label: '班主任', prop: 'head_teacher_name' },
              { label: '班额', prop: 'student_count' },
            ]"
            :fields="classFields"
            :disabled="classSectionDisabled"
            :disabled-reason="classSectionDisabledReason"
            @saved="reloadAll(false)"
          />
        </el-tab-pane>
        <el-tab-pane label="学科">
          <BaseCrudSection
            title="学科"
            description="学科主数据供教师、考试、分析和课表复用。"
            endpoint="/api/base/subjects"
            :columns="[
              { label: '代码', prop: 'code' },
              { label: '名称', prop: 'name' },
              { label: '类别', prop: 'category' },
              { label: '排序', prop: 'sort_order' },
            ]"
            :fields="subjectFields"
            :disabled="referenceStore.loading"
            :disabled-reason="referenceStore.loading ? '引用数据刷新中，暂不能维护学科。' : ''"
            @saved="reloadAll(false)"
          />
        </el-tab-pane>
        <el-tab-pane label="字典">
          <div class="dict-layout">
            <BaseCrudSection
              title="字典类型"
              description="字典项供学生状态、职称、岗位、班型等配置使用。"
              endpoint="/api/base/dict-types"
              :columns="[
                { label: '编码', prop: 'code' },
                { label: '名称', prop: 'name' },
                { label: '启用', prop: 'is_active' },
              ]"
              :fields="dictTypeFields"
              :disabled="dictTypesLoading"
              :disabled-reason="dictTypesLoading ? '字典类型刷新中，暂不能维护字典类型。' : ''"
              @saved="reloadAll(false)"
            />
            <section class="dict-side">
              <div class="dict-side-head">
                <div>
                  <h3>字典项</h3>
                  <p>先选择字典类型，再维护该类型下的具体选项。</p>
                </div>
                <el-select
                  v-model="selectedDictCode"
                  filterable
                  placeholder="选择字典类型"
                  :loading="dictTypesLoading"
                  :disabled="dictTypesLoading || Boolean(dictTypesLoadError) || !dictTypes.length"
                  style="width: 240px"
                >
                  <el-option
                    v-for="dictType in dictTypes"
                    :key="dictType.code"
                    :label="`${dictType.name}（${dictType.code}）`"
                    :value="dictType.code"
                  />
                </el-select>
              </div>
              <BaseCrudSection
                v-if="selectedDictCode"
                title="字典项"
                :description="selectedDictDescription"
                :endpoint="`/api/base/dict-types/${selectedDictCode}/items`"
                update-endpoint="/api/base/dict-items"
                :columns="[
                  { label: '编码', prop: 'code' },
                  { label: '名称', prop: 'name' },
                  { label: '排序', prop: 'sort_order' },
                  { label: '启用', prop: 'is_active' },
                ]"
                :fields="dictItemFields"
                :disabled="dictItemSectionDisabled"
                :disabled-reason="dictItemSectionDisabledReason"
                @saved="reloadAll(false)"
              />
              <el-empty v-else :description="dictItemsEmptyDescription">
                <el-button v-if="dictTypesLoadError" type="primary" plain :loading="dictTypesLoading" @click="loadDictTypes(true)">
                  重新加载字典类型
                </el-button>
              </el-empty>
            </section>
          </div>
        </el-tab-pane>
      </el-tabs>
    </AppSectionCard>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import { useRouter } from "vue-router";

import BaseCrudSection from "../components/BaseCrudSection.vue";
import { apiRequest } from "../api/client";
import { AppPage, AppSectionCard, AppStatGrid, type PageMetaItem, type StatCardItem } from "../components/ui";
import { useReferenceStore } from "../stores/reference";
import { formatUserActionError } from "../utils/userFeedback";

interface DictType {
  id: number;
  code: string;
  name: string;
}

const referenceStore = useReferenceStore();
const router = useRouter();
const dictTypes = ref<DictType[]>([]);
const selectedDictCode = ref("student_status");
const teacherOptions = ref<Array<{ id: number; name: string }>>([]);
const dictTypesLoading = ref(false);
const teacherOptionsLoading = ref(false);
const referenceLoadError = ref("");
const dictTypesLoadError = ref("");
const teacherOptionsLoadError = ref("");
const allLoading = computed(() => referenceStore.loading || dictTypesLoading.value || teacherOptionsLoading.value);
const semesterSectionDisabled = computed(
  () => referenceStore.loading || Boolean(referenceLoadError.value) || !referenceStore.academicYears.length,
);
const semesterSectionDisabledReason = computed(() => {
  if (referenceStore.loading) return "引用数据刷新中，暂不能维护学期。";
  if (referenceLoadError.value) return "学年数据加载失败，学期维护暂不可用。";
  if (!referenceStore.academicYears.length) return "请先维护学年，再新增学期。";
  return "";
});
const classSectionDisabled = computed(
  () =>
    referenceStore.loading ||
    teacherOptionsLoading.value ||
    Boolean(referenceLoadError.value) ||
    !referenceStore.grades.length,
);
const classSectionDisabledReason = computed(() => {
  if (referenceStore.loading || teacherOptionsLoading.value) return "基础选项刷新中，暂不能维护班级。";
  if (referenceLoadError.value) return "年级或班型数据加载失败，班级维护暂不可用。";
  if (!referenceStore.grades.length) return "请先维护年级，再新增班级。";
  return "";
});
const dictItemSectionDisabled = computed(
  () => dictTypesLoading.value || Boolean(dictTypesLoadError.value) || !selectedDictCode.value,
);
const dictItemSectionDisabledReason = computed(() => {
  if (dictTypesLoading.value) return "字典类型刷新中，暂不能维护字典项。";
  if (dictTypesLoadError.value) return "字典类型加载失败，字典项维护暂不可用。";
  if (!selectedDictCode.value) return "请先选择字典类型。";
  return "";
});
const loadErrorItems = computed(() => [
  { label: "引用数据", message: referenceLoadError.value },
  { label: "字典类型", message: dictTypesLoadError.value },
  { label: "教师选项", message: teacherOptionsLoadError.value },
].filter((item) => item.message));

const pageMeta = computed<PageMetaItem[]>(() => [
  { label: "学年", value: referenceLoadError.value ? "加载失败" : referenceStore.academicYears.length },
  { label: "学期", value: referenceLoadError.value ? "加载失败" : referenceStore.semesters.length },
  {
    label: "年级/班级",
    value: referenceLoadError.value ? "加载失败" : `${referenceStore.grades.length} / ${referenceStore.classes.length}`,
  },
  { label: "字典类型", value: dictTypesLoadError.value ? "加载失败" : dictTypes.value.length },
]);
const overviewCards = computed<StatCardItem[]>(() => [
  {
    label: "学年学期",
    value: referenceLoadError.value
      ? "加载失败"
      : `${referenceStore.academicYears.length} / ${referenceStore.semesters.length}`,
    help: "考试、任教关系、课表和报表都会按学年学期归档。",
    tone: referenceLoadError.value ? "danger" : "primary",
    loading: referenceStore.loading,
  },
  {
    label: "班级主数据",
    value: referenceLoadError.value ? "加载失败" : referenceStore.classes.length,
    help: "学生、考试和任教关系都会复用班级主数据。",
    tone: referenceLoadError.value ? "danger" : "success",
    loading: referenceStore.loading,
  },
  {
    label: "学科主数据",
    value: referenceLoadError.value ? "加载失败" : referenceStore.subjects.length,
    help: "考试、分析、课表和工作量共享同一套学科定义。",
    tone: referenceLoadError.value ? "danger" : "warning",
    loading: referenceStore.loading,
  },
  {
    label: "教师选项",
    value: teacherOptionsLoadError.value ? "加载失败" : teacherOptions.value.length,
    help: "班主任、任教关系等关联项从教师主数据读取。",
    tone: teacherOptionsLoadError.value ? "danger" : "info",
    loading: teacherOptionsLoading.value,
  },
  {
    label: "字典类型",
    value: dictTypesLoadError.value ? "加载失败" : dictTypes.value.length,
    help: "学生状态、班型、职称、岗位等选项集中维护。",
    tone: dictTypesLoadError.value ? "danger" : "neutral",
    loading: dictTypesLoading.value,
  },
]);
const selectedDictDescription = computed(() => {
  const selected = dictTypes.value.find((item) => item.code === selectedDictCode.value);
  return selected ? `当前字典：${selected.name}（${selected.code}）` : `当前字典：${selectedDictCode.value}`;
});
const dictItemsEmptyDescription = computed(() => {
  if (dictTypesLoading.value) return "正在加载字典类型";
  if (dictTypesLoadError.value) return "字典类型加载失败，请重新加载。";
  return "请选择字典类型";
});

const academicYearFields = computed(() => [
  { label: "名称", prop: "name", type: "text" as const, required: true },
  { label: "开始日期", prop: "start_date", type: "date" as const, required: true },
  { label: "结束日期", prop: "end_date", type: "date" as const, required: true },
  { label: "当前学年", prop: "is_current", type: "switch" as const, defaultValue: false },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
]);

const semesterFields = computed(() => [
  {
    label: "所属学年",
    prop: "academic_year_id",
    type: "select" as const,
    options: referenceStore.academicYears.map((item) => ({ label: item.name, value: item.id })),
    required: true,
  },
  { label: "名称", prop: "name", type: "text" as const, required: true },
  { label: "开始日期", prop: "start_date", type: "date" as const, required: true },
  { label: "结束日期", prop: "end_date", type: "date" as const, required: true },
  { label: "周数", prop: "week_count", type: "number" as const, min: 1, max: 40, defaultValue: 20, required: true },
  { label: "当前学期", prop: "is_current", type: "switch" as const, defaultValue: false },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
]);

const gradeFields = [
  { label: "名称", prop: "name", type: "text" as const, required: true },
  { label: "排序", prop: "sort_order", type: "number" as const, min: 0, max: 99, defaultValue: 0 },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
];

const classFields = computed(() => [
  {
    label: "所属年级",
    prop: "grade_id",
    type: "select" as const,
    options: referenceStore.grades.map((item) => ({ label: item.name, value: item.id })),
    required: true,
  },
  { label: "班级名称", prop: "name", type: "text" as const, required: true },
  {
    label: "班型",
    prop: "class_type",
    type: "select" as const,
    options: (referenceStore.dicts.class_type ?? []).map((item) => ({
      label: item.name,
      value: item.code as string,
    })),
  },
  {
    label: "班主任",
    prop: "head_teacher_id",
    type: "select" as const,
    options: teacherOptions.value.map((item) => ({ label: item.name, value: item.id })),
  },
  { label: "班额", prop: "student_count", type: "number" as const, min: 0, max: 300, defaultValue: 0 },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
]);

const subjectFields = [
  { label: "编码", prop: "code", type: "text" as const, required: true },
  { label: "名称", prop: "name", type: "text" as const, required: true },
  { label: "类别", prop: "category", type: "text" as const },
  { label: "排序", prop: "sort_order", type: "number" as const, min: 0, max: 99, defaultValue: 0 },
  { label: "计入总分", prop: "is_in_total_default", type: "switch" as const, defaultValue: true },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
];

const dictTypeFields = [
  { label: "编码", prop: "code", type: "text" as const, required: true },
  { label: "名称", prop: "name", type: "text" as const, required: true },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
];

const dictItemFields = [
  { label: "编码", prop: "code", type: "text" as const, required: true },
  { label: "名称", prop: "name", type: "text" as const, required: true },
  { label: "排序", prop: "sort_order", type: "number" as const, min: 0, max: 999, defaultValue: 0 },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
];

function clearReferenceData(): void {
  referenceStore.academicYears = [];
  referenceStore.semesters = [];
  referenceStore.grades = [];
  referenceStore.classes = [];
  referenceStore.subjects = [];
  referenceStore.dicts = {};
  referenceStore.coreLoaded = false;
}

async function loadReferenceData(showToast = false): Promise<void> {
  referenceLoadError.value = "";
  try {
    await referenceStore.loadAll({ force: true });
  } catch (error) {
    clearReferenceData();
    referenceLoadError.value = formatUserActionError("加载引用数据", error, "确认本地服务可用后重新加载基础数据");
    if (showToast) {
      ElMessage.error(referenceLoadError.value);
    }
  }
}

async function loadDictTypes(showToast = false): Promise<void> {
  dictTypesLoading.value = true;
  dictTypesLoadError.value = "";
  try {
    dictTypes.value = await apiRequest<DictType[]>("/api/base/dict-types");
    if (!dictTypes.value.some((item) => item.code === selectedDictCode.value)) {
      selectedDictCode.value = dictTypes.value[0]?.code ?? "";
    }
  } catch (error) {
    dictTypes.value = [];
    selectedDictCode.value = "";
    dictTypesLoadError.value = formatUserActionError("加载字典类型", error, "确认基础字典接口可用后重新加载");
    if (showToast) {
      ElMessage.error(dictTypesLoadError.value);
    }
  } finally {
    dictTypesLoading.value = false;
  }
}

async function loadTeacherOptions(showToast = false): Promise<void> {
  teacherOptionsLoading.value = true;
  teacherOptionsLoadError.value = "";
  try {
    const payload = await apiRequest<{ items: Array<{ id: number; name: string }> }>("/api/teachers?page=1&page_size=200");
    teacherOptions.value = payload.items;
  } catch (error) {
    teacherOptions.value = [];
    teacherOptionsLoadError.value = formatUserActionError("加载教师选项", error, "确认教师主数据接口可用后重新加载");
    if (showToast) {
      ElMessage.error(teacherOptionsLoadError.value);
    }
  } finally {
    teacherOptionsLoading.value = false;
  }
}

async function reloadAll(showToast = false): Promise<void> {
  await Promise.all([
    loadReferenceData(showToast),
    loadDictTypes(showToast),
    loadTeacherOptions(showToast),
  ]);
}

onMounted(() => reloadAll(false));
</script>

<style scoped>
.base-data-status-stack {
  display: grid;
  gap: 10px;
}

.base-data-tabs {
  margin-top: 6px;
}

.base-data-error-list {
  display: grid;
  gap: 6px;
  padding-left: 18px;
  margin: 0 0 10px;
}

.base-data-error-list li {
  line-height: 1.55;
}

.base-data-error-list strong {
  margin-right: 8px;
}

.base-data-alert-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dict-layout {
  display: grid;
  grid-template-columns: minmax(360px, 0.86fr) minmax(0, 1.14fr);
  gap: 16px;
  align-items: start;
}

.dict-side {
  min-width: 0;
  padding: 18px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: var(--bg-panel);
}

.dict-side-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.dict-side-head h3 {
  margin: 0;
  color: var(--text-main);
}

.dict-side-head p {
  margin: 8px 0 0;
  color: var(--text-muted);
  line-height: 1.6;
}

@media (max-width: 1180px) {
  .dict-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .dict-side-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
