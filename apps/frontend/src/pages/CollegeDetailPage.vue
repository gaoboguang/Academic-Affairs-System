<template>
  <AppPage
    :title="detail?.college.name ?? '院校详情'"
    eyebrow="升学数据 / 院校画像"
    description="查看院校基本信息、联系方式、山东近年录取和计划表现，以及本地来源证据。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button @click="router.push('/recommendations')">返回志愿工作台</el-button>
    </template>

    <div v-if="loading" class="loading-panel">正在加载院校详情...</div>
    <el-empty v-else-if="error" :description="error" />
    <template v-else-if="detail">
      <AppStatGrid :items="statCards" :columns="4" />

      <AppSectionCard title="院校概览" description="院校基础台账和招生画像。">
        <div class="detail-grid">
          <article class="summary-panel">
            <span>院校代码</span>
            <strong>{{ detail.college.college_code || detail.profile?.enrollment_code || '-' }}</strong>
            <p>{{ [detail.college.province, detail.college.city, detail.college.school_type].filter(Boolean).join(' / ') || '-' }}</p>
          </article>
          <article class="summary-panel">
            <span>办学层次</span>
            <strong>{{ detail.profile?.education_level || '未维护' }}</strong>
            <p>{{ levelTags.join('、') || '暂无层级标签' }}</p>
          </article>
          <article class="summary-panel">
            <span>主管部门</span>
            <strong>{{ detail.profile?.authority_department || '-' }}</strong>
            <p>{{ detail.profile?.address || '暂无地址' }}</p>
          </article>
        </div>
        <p class="body-copy">{{ detail.profile?.summary || detail.college.intro || '暂无院校简介。' }}</p>
      </AppSectionCard>

      <AppSectionCard title="联系方式" description="官网、招生网、电话和邮箱。">
        <div class="contact-list">
          <span>官网：{{ detail.profile?.official_website || detail.college.website || '-' }}</span>
          <span>招生网：{{ detail.profile?.admission_website || '-' }}</span>
          <span>电话：{{ detail.profile?.phone || '-' }}</span>
          <span>邮箱：{{ detail.profile?.email || '-' }}</span>
        </div>
      </AppSectionCard>

      <AppTableShell title="山东近年趋势" description="按年份展示计划、专业数、最低位次和估算最低分。">
        <el-table :data="detail.year_summaries" stripe>
          <el-table-column label="年份" prop="year" width="90" />
          <el-table-column label="计划数" prop="total_plan_count" width="100" />
          <el-table-column label="专业数" prop="specialty_count" width="100" />
          <el-table-column label="最低位次" prop="min_rank" width="120" />
          <el-table-column label="估算最低分" prop="estimated_min_score" width="120" />
          <el-table-column label="说明" prop="source_note" min-width="220" />
        </el-table>
      </AppTableShell>

      <AppTableShell title="开设专业画像" description="学校-专业关系、特色标签和来源。">
        <el-table :data="detail.major_profiles" stripe>
          <el-table-column label="专业" min-width="180">
            <template #default="{ row }">
              <el-button link type="primary" @click="router.push(`/majors/${row.major_id}`)">{{ row.major_name || '-' }}</el-button>
            </template>
          </el-table-column>
          <el-table-column label="层次" prop="education_level" width="110" />
          <el-table-column label="学制" prop="schooling_years" width="100" />
          <el-table-column label="特色" min-width="220">
            <template #default="{ row }">
              <div class="tag-cluster">
                <el-tag v-if="row.is_national_feature" size="small">国家特色</el-tag>
                <el-tag v-if="row.is_provincial_feature" size="small" type="success">省级特色</el-tag>
                <el-tag v-if="row.is_key_major" size="small" type="warning">重点专业</el-tag>
                <span>{{ row.school_major_feature || '-' }}</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </AppTableShell>

      <AppTableShell title="专业录取与计划样本" description="优先展示最近导入的录取结果和招生计划。">
        <el-tabs>
          <el-tab-pane label="录取/投档">
            <el-table :data="detail.recent_admissions" stripe>
              <el-table-column label="年份" prop="year" width="90" />
              <el-table-column label="批次" prop="batch" min-width="120" />
              <el-table-column label="专业" min-width="180">
                <template #default="{ row }">
                  <el-button v-if="row.major_id" link type="primary" @click="router.push(`/majors/${row.major_id}`)">{{ row.major_name || '-' }}</el-button>
                  <span v-else>{{ row.major_name || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="最低分" prop="min_score" width="100" />
              <el-table-column label="最低位次" prop="min_rank" width="120" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="招生计划">
            <el-table :data="detail.recent_plans" stripe>
              <el-table-column label="年份" prop="year" width="90" />
              <el-table-column label="批次" prop="batch" min-width="120" />
              <el-table-column label="专业" min-width="180">
                <template #default="{ row }">
                  <el-button v-if="row.major_id" link type="primary" @click="router.push(`/majors/${row.major_id}`)">{{ row.major_name || '-' }}</el-button>
                  <span v-else>{{ row.major_name || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="计划数" prop="plan_count" width="100" />
              <el-table-column label="选科要求" prop="subject_requirement" min-width="140" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </AppTableShell>

      <AppTableShell title="来源证据" description="本地 scraper 文件、官方页面或结构化来源记录。">
        <el-table :data="detail.source_documents" stripe>
          <el-table-column label="类型" prop="source_type" width="160" />
          <el-table-column label="标题" prop="title" min-width="180" />
          <el-table-column label="路径" prop="source_path" min-width="260" />
          <el-table-column label="SHA256" prop="source_sha256" min-width="220" show-overflow-tooltip />
        </el-table>
      </AppTableShell>
    </template>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { apiRequest } from "../api/client";
import AppPage from "../components/ui/AppPage.vue";
import AppSectionCard from "../components/ui/AppSectionCard.vue";
import AppStatGrid from "../components/ui/AppStatGrid.vue";
import AppTableShell from "../components/ui/AppTableShell.vue";
import type { CollegeDetail } from "../components/recommendations/detailTypes";

const route = useRoute();
const router = useRouter();
const detail = ref<CollegeDetail | null>(null);
const loading = ref(false);
const error = ref("");

const collegeId = computed(() => Number(route.params.collegeId));
const levelTags = computed(() => {
  const tags = [...(detail.value?.college.school_level_tags_json ?? [])];
  if (detail.value?.profile?.is_985) tags.push("985");
  if (detail.value?.profile?.is_211) tags.push("211");
  if (detail.value?.profile?.is_dual_class) tags.push("双一流");
  return Array.from(new Set(tags.filter(Boolean)));
});
const latestSummary = computed(() => detail.value?.year_summaries[0]);
const statCards = computed(() => [
  { label: "近年计划", value: latestSummary.value?.total_plan_count ?? "-", help: "最近年份山东计划数" },
  { label: "专业数", value: latestSummary.value?.specialty_count ?? "-", help: "最近年份招生专业数" },
  { label: "最低位次", value: latestSummary.value?.min_rank ?? "-", help: "山东近年最低位次" },
  { label: "估算最低分", value: latestSummary.value?.estimated_min_score ?? "-", help: "按一分一段估算时展示" },
]);
const pageMeta = computed(() => [
  { label: "地区", value: detail.value?.college.province || "未维护" },
  { label: "类型", value: detail.value?.college.school_type || "未维护" },
  { label: "层级", value: levelTags.value.join("、") || "未维护" },
]);

async function loadDetail(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    detail.value = await apiRequest<CollegeDetail>(`/api/colleges/${collegeId.value}/detail`);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadDetail();
});
</script>

<style scoped>
.loading-panel {
  padding: 28px;
  color: #5d6b7a;
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
.body-copy {
  color: #5e7184;
}

.summary-panel strong {
  color: #1f3448;
  font-size: 17px;
}

.body-copy {
  margin: 16px 0 0;
  line-height: 1.8;
}

.contact-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  color: #33485c;
}

.tag-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
</style>
