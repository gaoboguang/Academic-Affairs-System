<template>
  <AppPage
    :title="detail?.major.name ?? '专业详情'"
    eyebrow="升学数据 / 专业画像"
    description="查看专业基本信息、开设院校、山东近年录取表现、选科要求样例和就业映射。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button @click="router.push('/recommendations')">返回志愿工作台</el-button>
      <el-button type="primary" :loading="loading" @click="reloadMajorDetail">刷新专业</el-button>
    </template>

    <el-alert
      v-if="detailLoadError"
      class="detail-alert"
      type="error"
      show-icon
      :closable="false"
      title="专业详情加载失败"
      :description="detailLoadError"
    >
      <template #default>
        <el-button size="small" type="primary" plain :loading="loading" @click="reloadMajorDetail">
          重新加载专业详情
        </el-button>
      </template>
    </el-alert>

    <div v-loading="loading" class="major-detail-body">
      <AppStatGrid :items="statCards" :columns="4" />

      <template v-if="detail">
        <AppSectionCard title="专业概览" description="通用专业画像和可用标签。">
          <div class="detail-grid">
            <article class="summary-panel">
              <span>专业代码</span>
              <strong>{{ detail.profile?.major_code || detail.major.major_code || "-" }}</strong>
              <p>{{ detail.major.category || "门类未维护" }}</p>
            </article>
            <article class="summary-panel">
              <span>层次 / 学制</span>
              <strong>{{ detail.profile?.education_level || "-" }}</strong>
              <p>{{ detail.profile?.schooling_years || detail.major.direction || "-" }}</p>
            </article>
            <article class="summary-panel">
              <span>选科要求样例</span>
              <strong>{{ detail.subject_requirement_samples[0] || "暂无" }}</strong>
              <p>{{ detail.subject_requirement_samples.slice(1).join("、") || "来自招生计划样本" }}</p>
            </article>
          </div>
          <div class="tag-cluster tag-row">
            <el-tag v-for="tag in detail.profile?.tags_json ?? []" :key="tag" effect="plain">{{ tag }}</el-tag>
            <span v-if="!(detail.profile?.tags_json ?? []).length" class="muted-copy">暂无专业标签</span>
          </div>
          <p class="body-copy">{{ detail.profile?.summary || detail.major.note || "暂无专业简介。" }}</p>
        </AppSectionCard>

        <AppTableShell title="开设院校" description="学校内专业特色和院校详情入口。">
          <el-table :data="detail.college_profiles" stripe>
            <el-table-column label="院校" min-width="180">
              <template #default="{ row }">
                <el-button link type="primary" @click="router.push(`/colleges/${row.college_id}`)">
                  {{ row.college_name || "-" }}
                </el-button>
              </template>
            </el-table-column>
            <el-table-column label="层次" prop="education_level" width="110" />
            <el-table-column label="学制" prop="schooling_years" width="100" />
            <el-table-column label="特色" min-width="240">
              <template #default="{ row }">
                <div class="tag-cluster">
                  <el-tag v-if="row.is_national_feature" size="small">国家特色</el-tag>
                  <el-tag v-if="row.is_provincial_feature" size="small" type="success">省级特色</el-tag>
                  <el-tag v-if="row.is_key_major" size="small" type="warning">重点专业</el-tag>
                  <span>{{ row.school_major_feature || "-" }}</span>
                </div>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="暂无开设院校画像" />
            </template>
          </el-table>
        </AppTableShell>

        <AppTableShell title="山东近年录取表现" description="展示该专业近年录取/投档和招生计划样本。">
          <el-tabs>
            <el-tab-pane label="录取/投档">
              <el-table :data="detail.recent_admissions" stripe>
                <el-table-column label="年份" prop="year" width="90" />
                <el-table-column label="院校" min-width="180">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="router.push(`/colleges/${row.college_id}`)">
                      {{ row.college_name || "-" }}
                    </el-button>
                  </template>
                </el-table-column>
                <el-table-column label="批次" prop="batch" min-width="120" />
                <el-table-column label="最低分" prop="min_score" width="100" />
                <el-table-column label="最低位次" prop="min_rank" width="120" />
                <template #empty>
                  <el-empty description="暂无近年录取/投档样本" />
                </template>
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="招生计划">
              <el-table :data="detail.recent_plans" stripe>
                <el-table-column label="年份" prop="year" width="90" />
                <el-table-column label="院校" min-width="180">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="router.push(`/colleges/${row.college_id}`)">
                      {{ row.college_name || "-" }}
                    </el-button>
                  </template>
                </el-table-column>
                <el-table-column label="批次" prop="batch" min-width="120" />
                <el-table-column label="计划数" prop="plan_count" width="100" />
                <el-table-column label="选科要求" prop="subject_requirement" min-width="140" />
                <template #empty>
                  <el-empty description="暂无近年招生计划样本" />
                </template>
              </el-table>
            </el-tab-pane>
          </el-tabs>
        </AppTableShell>

        <AppTableShell title="就业映射" description="当前专业到职业方向的本地映射。">
          <el-table :data="detail.employment_mappings" stripe>
            <el-table-column label="方向" prop="direction_name" min-width="180" />
            <el-table-column label="类别" prop="direction_category" min-width="140" />
            <el-table-column label="匹配强度" prop="strength" width="120" />
            <el-table-column label="说明" prop="recommendation_note" min-width="260" />
            <template #empty>
              <el-empty description="暂无就业映射" />
            </template>
          </el-table>
        </AppTableShell>

        <AppTableShell title="来源证据" description="本地 scraper 文件、官方页面或结构化来源记录。">
          <el-table :data="detail.source_documents" stripe>
            <el-table-column label="类型" prop="source_type" width="160" />
            <el-table-column label="标题" prop="title" min-width="180" />
            <el-table-column label="路径" prop="source_path" min-width="260" />
            <el-table-column label="SHA256" prop="source_sha256" min-width="220" show-overflow-tooltip />
            <template #empty>
              <el-empty description="暂无来源证据" />
            </template>
          </el-table>
        </AppTableShell>
      </template>

      <el-empty v-else :description="majorDetailEmptyDescription">
        <el-button v-if="detailLoadError" type="primary" :loading="loading" @click="reloadMajorDetail">
          重新加载专业详情
        </el-button>
      </el-empty>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { ElMessage } from "element-plus";
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { apiRequest } from "../api/client";
import type { MajorDetail } from "../components/recommendations/detailTypes";
import {
  AppPage,
  AppSectionCard,
  AppStatGrid,
  AppTableShell,
  type PageMetaItem,
  type StatCardItem,
} from "../components/ui";
import { formatUserActionError, getErrorMessage } from "../utils/userFeedback";

const route = useRoute();
const router = useRouter();
const detail = ref<MajorDetail | null>(null);
const loading = ref(false);
const detailLoadError = ref("");

const majorId = computed(() => Number(route.params.majorId));
const detailLoadFailed = computed(() => Boolean(detailLoadError.value && !detail.value));
const failedStatCards: StatCardItem[] = [
  { label: "开设院校", value: "加载失败", help: "请重新加载专业详情。", tone: "danger" },
  { label: "录取样本", value: "加载失败", help: "请重新加载专业详情。", tone: "danger" },
  { label: "计划样本", value: "加载失败", help: "请重新加载专业详情。", tone: "danger" },
  { label: "就业映射", value: "加载失败", help: "请重新加载专业详情。", tone: "danger" },
];
const statCards = computed<StatCardItem[]>(() => {
  if (detailLoadFailed.value) {
    return failedStatCards.map((item) => ({ ...item, loading: loading.value }));
  }
  const normalCards: StatCardItem[] = [
    { label: "开设院校", value: detail.value?.college_profiles.length ?? "-", help: "已有学校-专业画像数量", tone: "primary" },
    { label: "录取样本", value: detail.value?.recent_admissions.length ?? "-", help: "最近录取/投档记录", tone: "success" },
    { label: "计划样本", value: detail.value?.recent_plans.length ?? "-", help: "最近招生计划记录", tone: "warning" },
    { label: "就业映射", value: detail.value?.employment_mappings.length ?? "-", help: "专业到职业方向映射", tone: "neutral" },
  ];
  return normalCards.map((item) => ({ ...item, loading: loading.value }));
});
const pageMeta = computed<PageMetaItem[]>(() => {
  if (detailLoadFailed.value) {
    return [
      { label: "专业详情", value: "加载失败" },
      { label: "专业 ID", value: Number.isFinite(majorId.value) ? String(majorId.value) : "-" },
    ];
  }
  if (!detail.value) {
    return [{ label: "专业 ID", value: Number.isFinite(majorId.value) ? String(majorId.value) : "-" }];
  }
  return [
    { label: "代码", value: detail.value.major.major_code || "未维护" },
    { label: "门类", value: detail.value.major.category || "未维护" },
    { label: "层次", value: detail.value.profile?.education_level || "未维护" },
    { label: "专业 ID", value: Number.isFinite(majorId.value) ? String(majorId.value) : "-" },
  ];
});
const majorDetailEmptyDescription = computed(() => {
  if (loading.value) return "正在加载专业详情";
  if (detailLoadError.value) return "专业详情加载失败，请检查本地服务或专业记录后重试。";
  return "暂无专业详情数据。";
});

async function loadDetail(): Promise<void> {
  if (!Number.isFinite(majorId.value)) {
    detail.value = null;
    detailLoadError.value = "专业 ID 无效，请从志愿工作台重新进入。";
    return;
  }
  loading.value = true;
  detailLoadError.value = "";
  try {
    detail.value = await apiRequest<MajorDetail>(`/api/majors/${majorId.value}/detail`);
  } catch (error) {
    detail.value = null;
    detailLoadError.value = getErrorMessage(error);
    ElMessage.error(formatUserActionError("加载专业详情", error, "请检查专业是否存在或稍后重试。"));
  } finally {
    loading.value = false;
  }
}

async function reloadMajorDetail(): Promise<void> {
  detail.value = null;
  await loadDetail();
}

onMounted(() => {
  void reloadMajorDetail();
});

watch(majorId, () => {
  void reloadMajorDetail();
});
</script>

<style scoped>
.detail-alert {
  margin-bottom: 16px;
}

.major-detail-body {
  min-height: 260px;
  display: grid;
  gap: 16px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.summary-panel {
  display: grid;
  gap: 6px;
  padding: 14px;
  border: 1px solid #e3eaf3;
  border-radius: 6px;
  background: #f8fbff;
}

.summary-panel span,
.summary-panel p,
.body-copy,
.muted-copy {
  color: #5e7184;
}

.summary-panel strong {
  color: #1f3448;
  font-size: 17px;
}

.tag-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.tag-row {
  margin-top: 16px;
}

.body-copy {
  margin: 16px 0 0;
  line-height: 1.8;
}

@media (max-width: 960px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
