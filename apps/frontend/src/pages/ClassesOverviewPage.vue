<template>
  <AppPage
    title="年级班级"
    eyebrow="基础台账 / 年级班级"
    description="以年级和班级为对象入口，集中查看班主任、任课教师、班级荣誉、学生与最近分析信号。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button :loading="loading" @click="reloadAll">刷新速览</el-button>
      <el-button type="primary" @click="router.push('/base-data')">维护主数据</el-button>
    </template>

    <AppStatGrid :items="overviewCards" :columns="5" />

    <AppFilterBar title="筛选班级" description="按年级、班型、班主任覆盖、任课完整度和荣誉记录快速缩小范围。" sticky>
      <div class="filter-grid class-filter-grid">
        <el-input v-model="filters.keyword" clearable placeholder="搜索班级、教师或荣誉" />
        <el-select v-model="filters.gradeId" clearable placeholder="年级">
          <el-option
            v-for="grade in referenceStore.grades"
            :key="grade.id"
            :label="grade.name"
            :value="grade.id"
          />
        </el-select>
        <el-select v-model="filters.classType" clearable placeholder="班型">
          <el-option
            v-for="item in referenceStore.dicts.class_type ?? []"
            :key="String(item.code)"
            :label="item.name"
            :value="item.code"
          />
        </el-select>
        <el-select v-model="filters.headTeacher" placeholder="班主任">
          <el-option label="全部" value="all" />
          <el-option label="已维护" value="assigned" />
          <el-option label="未维护" value="missing" />
        </el-select>
        <el-select v-model="filters.teaching" placeholder="任课">
          <el-option label="全部" value="all" />
          <el-option label="有任课" value="complete" />
          <el-option label="缺任课" value="missing" />
        </el-select>
        <el-select v-model="filters.honor" placeholder="荣誉">
          <el-option label="全部" value="all" />
          <el-option label="有荣誉" value="has" />
          <el-option label="无荣誉" value="none" />
        </el-select>
        <el-select v-model="selectedSemesterId" clearable placeholder="任教学期">
          <el-option
            v-for="semester in referenceStore.semesters"
            :key="semester.id"
            :label="formatSemesterName(semester)"
            :value="semester.id"
          />
        </el-select>
        <el-select v-model="selectedExamId" clearable placeholder="成绩考试">
          <el-option
            v-for="exam in examOptions"
            :key="exam.id"
            :label="exam.name"
            :value="exam.id"
          />
        </el-select>
      </div>
      <template #actions>
        <el-segmented v-model="viewMode" :options="viewModeOptions" />
        <el-button @click="resetFilters">重置</el-button>
      </template>
    </AppFilterBar>

    <div v-if="loading" class="loading-panel">正在加载年级班级速览...</div>
    <template v-else>
      <AppSectionCard
        v-for="group in visibleGradeGroups"
        :key="group.grade_id"
        :title="group.grade_name"
        :description="`${group.class_count} 个班级，${group.active_student_count} 名在读学生，班主任覆盖 ${formatPercent(group.head_teacher_coverage)}`"
      >
        <template #actions>
          <el-button link type="primary" @click="router.push(`/grades/${group.grade_id}`)">年级详情</el-button>
        </template>

        <div v-if="viewMode === 'cards'" class="class-card-grid">
          <article v-for="item in group.classes" :key="item.class_id" class="class-card">
            <div class="class-card-head">
              <div>
                <span>{{ item.grade_name }}</span>
                <h3>{{ item.class_name }}</h3>
              </div>
              <el-tag :type="item.teaching_complete ? 'success' : 'warning'" effect="light">
                {{ item.teaching_complete ? "任课已维护" : "缺任课" }}
              </el-tag>
            </div>
            <div class="class-meta-grid">
              <div>
                <span>班主任</span>
                <strong>{{ item.head_teacher_name ?? "未维护" }}</strong>
              </div>
              <div>
                <span>学生</span>
                <strong>{{ item.active_student_count }}</strong>
              </div>
              <div>
                <span>任课教师</span>
                <strong>{{ item.teacher_count }}</strong>
              </div>
              <div>
                <span>均分</span>
                <strong>{{ formatScore(item.score_summary.average_score) }}</strong>
              </div>
            </div>
            <p class="class-teachers">{{ formatClassTeachers(item.teacher_summary) }}</p>
            <div class="class-card-foot">
              <span>{{ item.latest_honor?.title ?? "暂无班级荣誉" }}</span>
              <el-button type="primary" plain @click="router.push(`/classes/${item.class_id}`)">详情</el-button>
            </div>
          </article>
        </div>

        <AppTableShell v-else>
          <el-table :data="group.classes" stripe>
            <el-table-column label="班级" min-width="120">
              <template #default="{ row }">
                <el-button link type="primary" @click="router.push(`/classes/${row.class_id}`)">
                  {{ row.class_name }}
                </el-button>
              </template>
            </el-table-column>
            <el-table-column label="班型" min-width="100">
              <template #default="{ row }">{{ resolveClassType(row.class_type) }}</template>
            </el-table-column>
            <el-table-column label="班主任" prop="head_teacher_name" min-width="120" />
            <el-table-column label="学生" prop="active_student_count" width="90" />
            <el-table-column label="任课教师" prop="teacher_count" width="100" />
            <el-table-column label="最近均分" width="100">
              <template #default="{ row }">{{ formatScore(row.score_summary.average_score) }}</template>
            </el-table-column>
            <el-table-column label="风险跟进" width="100">
              <template #default="{ row }">{{ row.risk_summary.follow_up_count }}</template>
            </el-table-column>
            <el-table-column label="荣誉" min-width="180">
              <template #default="{ row }">{{ row.latest_honor?.title ?? "暂无" }}</template>
            </el-table-column>
          </el-table>
        </AppTableShell>
      </AppSectionCard>

      <el-empty v-if="!visibleGradeGroups.length" description="没有符合筛选条件的班级。" />
    </template>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import { useRouter } from "vue-router";

import { apiRequest } from "../api/client";
import {
  AppFilterBar,
  AppPage,
  AppSectionCard,
  AppStatGrid,
  AppTableShell,
  type PageMetaItem,
} from "../components/ui";
import {
  buildClassOverviewCards,
  filterClasses,
  formatClassTeachers,
  formatPercent,
  formatScore,
  type ClassesOverviewResponse,
  type GradeOverviewGroup,
} from "../components/classes/classProfile";
import { useReferenceStore, type OptionItem } from "../stores/reference";

interface ExamOption {
  id: number;
  name: string;
}

const referenceStore = useReferenceStore();
const router = useRouter();
const loading = ref(false);
const overview = ref<ClassesOverviewResponse | null>(null);
const examOptions = ref<ExamOption[]>([]);
const selectedSemesterId = ref<number | null>(null);
const selectedExamId = ref<number | null>(null);
const viewMode = ref<"cards" | "table">("cards");
const viewModeOptions = [
  { label: "卡片", value: "cards" },
  { label: "表格", value: "table" },
];
const filters = reactive({
  keyword: "",
  gradeId: undefined as number | undefined,
  classType: "" as string | undefined,
  headTeacher: "all" as "all" | "assigned" | "missing",
  teaching: "all" as "all" | "complete" | "missing",
  honor: "all" as "all" | "has" | "none",
});

const overviewCards = computed(() => buildClassOverviewCards(overview.value));
const pageMeta = computed<PageMetaItem[]>(() => [
  { label: "任教学期", value: overview.value?.semester_name ?? "当前学期" },
  { label: "成绩考试", value: overview.value?.exam_name ?? "最近考试" },
  { label: "班级", value: overview.value?.total_classes ?? 0 },
  { label: "荣誉", value: overview.value?.total_honors ?? 0 },
]);
const visibleGradeGroups = computed<GradeOverviewGroup[]>(() => {
  const groups = overview.value?.grades ?? [];
  return groups
    .filter((group) => !filters.gradeId || group.grade_id === filters.gradeId)
    .map((group) => ({
      ...group,
      classes: filterClasses(group.classes, {
        keyword: filters.keyword,
        classType: filters.classType,
        headTeacher: filters.headTeacher,
        teaching: filters.teaching,
        honor: filters.honor,
      }),
    }))
    .filter((group) => group.classes.length > 0);
});

function formatSemesterName(item: OptionItem): string {
  return `${item.academic_year_name ?? ""} ${item.name}`.trim();
}

function resolveClassType(code?: string | null): string {
  if (!code) return "-";
  return referenceStore.dicts.class_type?.find((item) => String(item.code) === String(code))?.name ?? code;
}

function resetFilters(): void {
  filters.keyword = "";
  filters.gradeId = undefined;
  filters.classType = "";
  filters.headTeacher = "all";
  filters.teaching = "all";
  filters.honor = "all";
}

async function loadOptions(): Promise<void> {
  await referenceStore.loadAll();
  const exams = await apiRequest<{ items: ExamOption[] }>("/api/exams?page=1&page_size=100");
  examOptions.value = exams.items;
}

async function loadOverview(): Promise<void> {
  const query = new URLSearchParams();
  if (filters.gradeId) query.set("grade_id", String(filters.gradeId));
  if (selectedSemesterId.value) query.set("semester_id", String(selectedSemesterId.value));
  if (selectedExamId.value) query.set("exam_id", String(selectedExamId.value));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  overview.value = await apiRequest<ClassesOverviewResponse>(`/api/classes/overview${suffix}`);
}

async function reloadAll(): Promise<void> {
  try {
    loading.value = true;
    await loadOptions();
    await loadOverview();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    loading.value = false;
  }
}

watch([selectedSemesterId, selectedExamId], () => {
  void loadOverview().catch((error: Error) => ElMessage.error(error.message));
});

watch(
  () => filters.gradeId,
  () => {
    void loadOverview().catch((error: Error) => ElMessage.error(error.message));
  },
);

onMounted(reloadAll);
</script>

<style scoped>
.class-filter-grid {
  grid-template-columns: repeat(4, minmax(160px, 1fr));
}

.class-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}

.class-card {
  display: grid;
  gap: 14px;
  min-height: 250px;
  padding: 18px;
  border: 1px solid var(--border-soft);
  border-radius: 8px;
  background: var(--bg-panel);
  box-shadow: var(--shadow-soft);
}

.class-card-head,
.class-card-foot {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.class-card-head span,
.class-meta-grid span {
  color: var(--text-muted);
  font-size: 12px;
}

.class-card-head h3 {
  margin: 4px 0 0;
  color: var(--text-main);
  font-size: 22px;
}

.class-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.class-meta-grid div {
  display: grid;
  gap: 4px;
  padding: 10px;
  border-radius: 8px;
  background: var(--bg-muted);
}

.class-meta-grid strong {
  color: var(--text-main);
  font-size: 18px;
}

.class-teachers {
  min-height: 44px;
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.class-card-foot {
  align-items: center;
  margin-top: auto;
}

.class-card-foot span {
  min-width: 0;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loading-panel {
  padding: 22px;
  border-radius: 8px;
  border: 1px solid var(--border-soft);
  background: var(--bg-panel);
  color: var(--text-muted);
}

@media (max-width: 980px) {
  .class-filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
