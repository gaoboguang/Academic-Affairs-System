<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">基础台账 / 主数据中心</div>
        <h2 class="page-title">基础数据</h2>
        <p class="page-subtitle">
          主数据全部从后端字典表和主数据表读取，集中维护学年、学期、年级、班级、学科和字典配置。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>学年</strong>{{ referenceStore.academicYears.length }}</span>
          <span class="page-chip"><strong>学期</strong>{{ referenceStore.semesters.length }}</span>
          <span class="page-chip"><strong>年级/班级</strong>{{ referenceStore.grades.length }} / {{ referenceStore.classes.length }}</span>
          <span class="page-chip"><strong>字典类型</strong>{{ dictTypes.length }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button :loading="referenceStore.loading" @click="reloadAll">刷新基础数据</el-button>
      </div>
    </header>

    <section class="overview-grid">
      <article v-for="item in overviewCards" :key="item.label" class="soft-card overview-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </section>

    <el-tabs>
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
          @saved="reloadAll"
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
          @saved="reloadAll"
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
          @saved="reloadAll"
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
          @saved="reloadAll"
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
          @saved="reloadAll"
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
            @saved="reloadAll"
          />
          <section class="soft-card dict-side">
            <div class="dict-side-head">
              <div>
                <h3>字典项</h3>
                <p>先选择左侧字典编码，再维护具体项。</p>
              </div>
              <el-select
                v-model="selectedDictCode"
                placeholder="选择字典类型"
                style="width: 220px"
              >
                <el-option
                  v-for="dictType in dictTypes"
                  :key="dictType.code"
                  :label="dictType.name"
                  :value="dictType.code"
                />
              </el-select>
            </div>
            <BaseCrudSection
              v-if="selectedDictCode"
              title="字典项"
              :description="`当前字典：${selectedDictCode}`"
              :endpoint="`/api/base/dict-types/${selectedDictCode}/items`"
              update-endpoint="/api/base/dict-items"
              :columns="[
                { label: '编码', prop: 'code' },
                { label: '名称', prop: 'name' },
                { label: '排序', prop: 'sort_order' },
                { label: '启用', prop: 'is_active' },
              ]"
              :fields="dictItemFields"
              @saved="reloadAll"
            />
            <el-empty v-else description="请选择字典类型" />
          </section>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import BaseCrudSection from "../components/BaseCrudSection.vue";
import { apiRequest } from "../api/client";
import { useReferenceStore } from "../stores/reference";

interface DictType {
  id: number;
  code: string;
  name: string;
}

const referenceStore = useReferenceStore();
const dictTypes = ref<DictType[]>([]);
const selectedDictCode = ref("student_status");
const teacherOptions = ref<Array<{ id: number; name: string }>>([]);
const overviewCards = computed(() => [
  {
    label: "班级主数据",
    value: referenceStore.classes.length,
    help: "学生、考试和任教关系都会复用班级主数据。",
    tone: "tone-blue",
  },
  {
    label: "学科主数据",
    value: referenceStore.subjects.length,
    help: "考试、分析、课表和工作量共享同一套学科定义。",
    tone: "tone-amber",
  },
  {
    label: "教师选项",
    value: teacherOptions.value.length,
    help: "班主任、任教关系等关联项从教师主数据读取。",
    tone: "tone-slate",
  },
]);

const academicYearFields = computed(() => [
  { label: "名称", prop: "name", type: "text" as const },
  { label: "开始日期", prop: "start_date", type: "date" as const },
  { label: "结束日期", prop: "end_date", type: "date" as const },
  { label: "当前学年", prop: "is_current", type: "switch" as const, defaultValue: false },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
]);

const semesterFields = computed(() => [
  {
    label: "所属学年",
    prop: "academic_year_id",
    type: "select" as const,
    options: referenceStore.academicYears.map((item) => ({ label: item.name, value: item.id })),
  },
  { label: "名称", prop: "name", type: "text" as const },
  { label: "开始日期", prop: "start_date", type: "date" as const },
  { label: "结束日期", prop: "end_date", type: "date" as const },
  { label: "周数", prop: "week_count", type: "number" as const, min: 1, max: 40, defaultValue: 20 },
  { label: "当前学期", prop: "is_current", type: "switch" as const, defaultValue: false },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
]);

const gradeFields = [
  { label: "名称", prop: "name", type: "text" as const },
  { label: "排序", prop: "sort_order", type: "number" as const, min: 0, max: 99, defaultValue: 0 },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
];

const classFields = computed(() => [
  {
    label: "所属年级",
    prop: "grade_id",
    type: "select" as const,
    options: referenceStore.grades.map((item) => ({ label: item.name, value: item.id })),
  },
  { label: "班级名称", prop: "name", type: "text" as const },
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
  { label: "编码", prop: "code", type: "text" as const },
  { label: "名称", prop: "name", type: "text" as const },
  { label: "类别", prop: "category", type: "text" as const },
  { label: "排序", prop: "sort_order", type: "number" as const, min: 0, max: 99, defaultValue: 0 },
  { label: "计入总分", prop: "is_in_total_default", type: "switch" as const, defaultValue: true },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
];

const dictTypeFields = [
  { label: "编码", prop: "code", type: "text" as const },
  { label: "名称", prop: "name", type: "text" as const },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
];

const dictItemFields = [
  { label: "编码", prop: "code", type: "text" as const },
  { label: "名称", prop: "name", type: "text" as const },
  { label: "排序", prop: "sort_order", type: "number" as const, min: 0, max: 999, defaultValue: 0 },
  { label: "启用", prop: "is_active", type: "switch" as const, defaultValue: true },
];

async function loadDictTypes(): Promise<void> {
  dictTypes.value = await apiRequest<DictType[]>("/api/base/dict-types");
}

async function loadTeachers(): Promise<void> {
  const payload = await apiRequest<{ items: Array<{ id: number; name: string }> }>("/api/teachers?page=1&page_size=200");
  teacherOptions.value = payload.items;
}

async function reloadAll(): Promise<void> {
  try {
    await Promise.all([referenceStore.loadAll({ force: true }), loadDictTypes(), loadTeachers()]);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

onMounted(reloadAll);
</script>

<style scoped>
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.overview-card {
  padding: 24px;
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

.dict-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
}

.dict-side {
  padding: 22px;
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
}

.dict-side-head p {
  margin: 8px 0 0;
  color: #6d8093;
  line-height: 1.6;
}

@media (max-width: 1180px) {
  .overview-grid {
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
