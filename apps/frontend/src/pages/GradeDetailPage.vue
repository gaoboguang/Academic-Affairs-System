<template>
  <AppPage
    :title="profile?.grade.grade_name ?? '年级详情'"
    eyebrow="基础台账 / 年级档案"
    description="聚合一个年级下所有班级的班主任、任课覆盖、成绩样本、风险信号和荣誉记录。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button @click="router.push('/classes')">返回年级班级</el-button>
      <el-button type="primary" :loading="pageBusy" @click="reloadAll">刷新年级</el-button>
    </template>

    <el-alert
      v-if="loadError"
      class="grade-detail-alert"
      type="error"
      show-icon
      :closable="false"
      title="年级档案加载失败"
      :description="loadError"
    >
      <template #default>
        <el-button size="small" type="primary" plain :loading="loading" @click="reloadAll">重新加载年级档案</el-button>
      </template>
    </el-alert>

    <el-alert
      v-if="referenceLoadError"
      class="grade-detail-alert"
      type="warning"
      show-icon
      :closable="false"
      title="基础选项加载失败"
      :description="referenceLoadError"
    >
      <template #default>
        <el-button size="small" plain :loading="referenceLoading" @click="loadReferenceOptions">重新加载基础选项</el-button>
      </template>
    </el-alert>

    <div v-loading="loading" class="grade-detail-body">
    <AppStatGrid :items="gradeCards" :columns="5" />

    <template v-if="profile">
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
            <template #empty>
              <el-empty description="当前年级暂无班级数据" />
            </template>
          </el-table>
        </AppTableShell>
      </AppSectionCard>
    </template>
    <el-empty v-else :description="gradeDetailEmptyDescription">
      <el-button v-if="loadError" type="primary" :loading="loading" @click="reloadAll">重新加载年级档案</el-button>
    </el-empty>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
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
import { formatUserActionError, getErrorMessage } from "../utils/userFeedback";

const route = useRoute();
const router = useRouter();
const referenceStore = useReferenceStore();
const gradeId = computed(() => Number(route.params.gradeId));
const loading = ref(false);
const referenceLoading = ref(false);
const loadError = ref("");
const referenceLoadError = ref("");
const profile = ref<GradeProfileResponse | null>(null);
const pageBusy = computed(() => loading.value || referenceLoading.value);
const profileLoadFailed = computed(() => Boolean(loadError.value && !profile.value));

const pageMeta = computed<PageMetaItem[]>(() => {
  if (profileLoadFailed.value) {
    return [
      { label: "年级档案", value: "加载失败" },
      { label: "年级 ID", value: Number.isFinite(gradeId.value) ? gradeId.value : "-" },
      { label: "基础选项", value: referenceLoadError.value ? "加载失败" : "可用" },
    ];
  }
  if (!profile.value) {
    return [{ label: "年级 ID", value: Number.isFinite(gradeId.value) ? gradeId.value : "-" }];
  }
  return [
    { label: "班级", value: profile.value.grade.class_count },
    { label: "学生", value: profile.value.grade.active_student_count },
    { label: "班主任覆盖", value: formatPercent(profile.value.grade.head_teacher_coverage) },
    { label: "任课覆盖", value: formatPercent(profile.value.grade.teaching_complete_rate) },
  ];
});

const failedGradeCards: StatCardItem[] = [
  { label: "班级", value: "加载失败", help: "请重新加载年级档案。", tone: "danger" },
  { label: "学生", value: "加载失败", help: "请重新加载年级档案。", tone: "danger" },
  { label: "班主任覆盖", value: "加载失败", help: "请重新加载年级档案。", tone: "danger" },
  { label: "任课覆盖", value: "加载失败", help: "请重新加载年级档案。", tone: "danger" },
  { label: "班级荣誉", value: "加载失败", help: "请重新加载年级档案。", tone: "danger" },
];
const gradeCards = computed<StatCardItem[]>(() => {
  if (profileLoadFailed.value) {
    return failedGradeCards.map((item) => ({ ...item, loading: pageBusy.value }));
  }
  const normalCards: StatCardItem[] = [
    { label: "班级", value: profile.value?.grade.class_count ?? "-", help: "当前年级的班级数量。", tone: "primary" },
    { label: "学生", value: profile.value?.grade.active_student_count ?? "-", help: "当前年级在读学生数。", tone: "success" },
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
    { label: "班级荣誉", value: profile.value?.grade.honor_count ?? "-", help: "当前年级班级荣誉总数。", tone: "neutral" },
  ];
  return normalCards.map((item) => ({ ...item, loading: pageBusy.value }));
});

const gradeDetailEmptyDescription = computed(() => {
  if (loading.value) return "正在加载年级档案";
  if (loadError.value) return "年级档案加载失败，请检查本地服务或年级记录后重试";
  return "年级不存在或已停用";
});

function resolveClassType(code?: string | null): string {
  if (!code) return "-";
  return referenceStore.dicts.class_type?.find((item) => String(item.code) === String(code))?.name ?? code;
}

async function loadReferenceOptions(): Promise<void> {
  referenceLoadError.value = "";
  referenceLoading.value = true;
  try {
    await referenceStore.loadAll();
  } catch (error) {
    referenceLoadError.value = getErrorMessage(error);
    ElMessage.error(formatUserActionError("加载基础选项", error, "年级档案仍可查看，班型名称可稍后重新加载"));
  } finally {
    referenceLoading.value = false;
  }
}

async function reloadAll(): Promise<void> {
  if (!Number.isFinite(gradeId.value)) {
    profile.value = null;
    loadError.value = "年级 ID 无效，请从年级班级页面重新进入。";
    return;
  }
  loading.value = true;
  loadError.value = "";
  const [, profileResult] = await Promise.allSettled([
    loadReferenceOptions(),
    apiRequest<GradeProfileResponse>(`/api/grades/${gradeId.value}/profile`),
  ]);
  if (profileResult.status === "fulfilled") {
    profile.value = profileResult.value;
  } else {
    profile.value = null;
    loadError.value = formatUserActionError(
      "加载年级档案",
      profileResult.reason,
      "请确认年级是否存在，或稍后重新加载。",
    );
    ElMessage.error(loadError.value);
  }
  loading.value = false;
}

watch(gradeId, () => {
  profile.value = null;
  void reloadAll();
});

onMounted(reloadAll);
</script>

<style scoped>
.grade-detail-alert {
  margin-bottom: 16px;
}

.grade-detail-body {
  min-height: 260px;
  display: grid;
  gap: 16px;
}
</style>
