<template>
  <AppPage
    :title="profile?.grade.grade_name ?? '年级详情'"
    eyebrow="基础台账 / 年级档案"
    description="聚合一个年级下所有班级的班主任、任课覆盖、成绩样本、风险信号和荣誉记录。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button @click="router.push('/classes')">返回年级班级</el-button>
      <el-button type="primary" @click="reloadAll">刷新年级</el-button>
    </template>

    <div v-if="loading" class="loading-panel">正在加载年级档案...</div>
    <template v-else-if="profile">
      <AppStatGrid :items="gradeCards" :columns="5" />

      <AppSectionCard title="班级横向矩阵" description="用同一口径比较班额、班主任、任课覆盖、成绩样本、风险信号和荣誉记录。">
        <AppTableShell>
          <el-table :data="profile.classes" stripe>
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
            <el-table-column label="班主任" min-width="120">
              <template #default="{ row }">{{ row.head_teacher_name ?? "未维护" }}</template>
            </el-table-column>
            <el-table-column label="学生" prop="active_student_count" width="90" />
            <el-table-column label="任课覆盖" width="110">
              <template #default="{ row }">
                <el-tag :type="row.teaching_complete ? 'success' : 'warning'" effect="light">
                  {{ row.teaching_complete ? "已维护" : "缺任课" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="任课摘要" min-width="240">
              <template #default="{ row }">{{ formatClassTeachers(row.teacher_summary, 4) }}</template>
            </el-table-column>
            <el-table-column label="成绩样本" width="100">
              <template #default="{ row }">{{ row.score_summary.sample_count }}</template>
            </el-table-column>
            <el-table-column label="均分" width="90">
              <template #default="{ row }">{{ formatScore(row.score_summary.average_score) }}</template>
            </el-table-column>
            <el-table-column label="需跟进" width="90">
              <template #default="{ row }">{{ row.risk_summary.follow_up_count }}</template>
            </el-table-column>
            <el-table-column label="荣誉" width="90" prop="honor_count" />
            <el-table-column label="最近荣誉" min-width="180">
              <template #default="{ row }">{{ row.latest_honor?.title ?? "暂无" }}</template>
            </el-table-column>
          </el-table>
        </AppTableShell>
      </AppSectionCard>
    </template>
    <el-empty v-else description="年级不存在或已停用。" />
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import { useRoute, useRouter } from "vue-router";

import { apiRequest } from "../api/client";
import {
  AppPage,
  AppSectionCard,
  AppStatGrid,
  AppTableShell,
  type PageMetaItem,
  type StatCardItem,
} from "../components/ui";
import {
  formatClassTeachers,
  formatPercent,
  formatScore,
  type GradeProfileResponse,
} from "../components/classes/classProfile";
import { useReferenceStore } from "../stores/reference";

const route = useRoute();
const router = useRouter();
const referenceStore = useReferenceStore();
const gradeId = computed(() => Number(route.params.gradeId));
const loading = ref(false);
const profile = ref<GradeProfileResponse | null>(null);

const pageMeta = computed<PageMetaItem[]>(() => [
  { label: "班级", value: profile.value?.grade.class_count ?? 0 },
  { label: "学生", value: profile.value?.grade.active_student_count ?? 0 },
  { label: "班主任覆盖", value: formatPercent(profile.value?.grade.head_teacher_coverage) },
  { label: "任课覆盖", value: formatPercent(profile.value?.grade.teaching_complete_rate) },
]);
const gradeCards = computed<StatCardItem[]>(() => [
  { label: "班级", value: profile.value?.grade.class_count ?? 0, help: "当前年级的班级数量。", tone: "primary" },
  { label: "学生", value: profile.value?.grade.active_student_count ?? 0, help: "当前年级在读学生数。", tone: "success" },
  {
    label: "班主任覆盖",
    value: formatPercent(profile.value?.grade.head_teacher_coverage),
    help: "已维护班主任的班级比例。",
    tone: "warning",
  },
  {
    label: "任课覆盖",
    value: formatPercent(profile.value?.grade.teaching_complete_rate),
    help: "当前学期已维护任课关系的班级比例。",
    tone: "neutral",
  },
  { label: "班级荣誉", value: profile.value?.grade.honor_count ?? 0, help: "当前年级班级荣誉总数。", tone: "neutral" },
]);

function resolveClassType(code?: string | null): string {
  if (!code) return "-";
  return referenceStore.dicts.class_type?.find((item) => String(item.code) === String(code))?.name ?? code;
}

async function reloadAll(): Promise<void> {
  try {
    loading.value = true;
    await referenceStore.loadAll();
    profile.value = await apiRequest<GradeProfileResponse>(`/api/grades/${gradeId.value}/profile`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    loading.value = false;
  }
}

onMounted(reloadAll);
</script>

<style scoped>
.loading-panel {
  padding: 22px;
  border-radius: 8px;
  border: 1px solid var(--border-soft);
  background: var(--bg-panel);
  color: var(--text-muted);
}
</style>
