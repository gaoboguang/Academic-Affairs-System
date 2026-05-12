<template>
  <AppPage
    :title="detail?.college.name ?? '院校详情'"
    eyebrow="升学数据 / 院校画像"
    description="查看院校基本信息、联系方式、山东近年录取和计划表现，以及本地来源证据。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button @click="router.push('/colleges')">返回院校库</el-button>
      <el-button @click="router.push('/recommendations')">志愿工作台</el-button>
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

      <AppTableShell title="招生数据" description="按院校查看完整招生计划和录取/投档历史，支持筛选后分页浏览。">
        <el-tabs v-model="activeAdmissionTab">
          <el-tab-pane label="录取/投档">
            <div class="detail-filter-grid">
              <el-input v-model.number="admissionFilters.year" clearable placeholder="年份" />
              <el-input v-model="admissionFilters.province" clearable placeholder="省份" />
              <el-input v-model="admissionFilters.batch" clearable placeholder="批次" />
              <el-input v-model="admissionFilters.student_type" clearable placeholder="考生类型" />
              <el-button type="primary" @click="loadAdmissions({ resetPage: true })">查询</el-button>
              <el-button @click="resetAdmissionFilters()">重置</el-button>
            </div>
            <el-table v-loading="admissionsLoading" :data="admissions" stripe>
              <el-table-column label="年份" prop="year" width="90" />
              <el-table-column label="省份" prop="province" width="100" />
              <el-table-column label="批次" prop="batch" min-width="120" />
              <el-table-column label="专业" min-width="180">
                <template #default="{ row }">
                  <el-button v-if="row.major_id" link type="primary" @click="router.push(`/majors/${row.major_id}`)">{{ row.major_name || '-' }}</el-button>
                  <span v-else>{{ row.major_name || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="类型" prop="student_type" width="110" />
              <el-table-column label="最低分" prop="min_score" width="100" />
              <el-table-column label="最低位次" prop="min_rank" width="120" />
              <el-table-column label="计划/录取数" prop="plan_count" width="120" />
            </el-table>
            <el-pagination
              v-if="admissionPagination.total"
              class="table-pagination"
              background
              layout="total, sizes, prev, pager, next"
              :current-page="admissionPagination.page"
              :page-size="admissionPagination.page_size"
              :page-sizes="[50, 100, 200]"
              :total="admissionPagination.total"
              @current-change="handleAdmissionPageChange"
              @size-change="handleAdmissionPageSizeChange"
            />
          </el-tab-pane>
          <el-tab-pane label="招生计划">
            <div class="detail-filter-grid">
              <el-input v-model.number="planFilters.year" clearable placeholder="年份" />
              <el-input v-model="planFilters.province" clearable placeholder="省份" />
              <el-input v-model="planFilters.batch" clearable placeholder="批次" />
              <el-input v-model="planFilters.student_type" clearable placeholder="考生类型" />
              <el-input v-model="planFilters.keyword" clearable placeholder="专业关键词" />
              <el-button type="primary" @click="loadPlans({ resetPage: true })">查询</el-button>
              <el-button @click="resetPlanFilters()">重置</el-button>
            </div>
            <el-table v-loading="plansLoading" :data="plans" stripe>
              <el-table-column label="年份" prop="year" width="90" />
              <el-table-column label="省份" prop="province" width="100" />
              <el-table-column label="批次" prop="batch" min-width="120" />
              <el-table-column label="专业" min-width="180">
                <template #default="{ row }">
                  <el-button v-if="row.major_id" link type="primary" @click="router.push(`/majors/${row.major_id}`)">{{ row.major_name || '-' }}</el-button>
                  <span v-else>{{ row.major_name || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="专业组" prop="major_group_code" width="110" />
              <el-table-column label="计划数" prop="plan_count" width="100" />
              <el-table-column label="类型" prop="student_type" width="110" />
              <el-table-column label="选科要求" prop="subject_requirement" min-width="140" />
            </el-table>
            <el-pagination
              v-if="planPagination.total"
              class="table-pagination"
              background
              layout="total, sizes, prev, pager, next"
              :current-page="planPagination.page"
              :page-size="planPagination.page_size"
              :page-sizes="[50, 100, 200]"
              :total="planPagination.total"
              @current-change="handlePlanPageChange"
              @size-change="handlePlanPageSizeChange"
            />
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
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import { apiRequest } from "../api/client";
import AppPage from "../components/ui/AppPage.vue";
import AppSectionCard from "../components/ui/AppSectionCard.vue";
import AppStatGrid from "../components/ui/AppStatGrid.vue";
import AppTableShell from "../components/ui/AppTableShell.vue";
import type { CollegeDetail } from "../components/recommendations/detailTypes";
import type { AdmissionRecord, EnrollmentPlanItem, PaginatedResponse, PaginationState } from "../components/recommendations/types";

const route = useRoute();
const router = useRouter();
const detail = ref<CollegeDetail | null>(null);
const loading = ref(false);
const error = ref("");
const activeAdmissionTab = ref("0");
const admissions = ref<AdmissionRecord[]>([]);
const plans = ref<EnrollmentPlanItem[]>([]);
const admissionsLoading = ref(false);
const plansLoading = ref(false);
const admissionPagination = reactive<PaginationState>({ page: 1, page_size: 50, total: 0 });
const planPagination = reactive<PaginationState>({ page: 1, page_size: 50, total: 0 });
const admissionFilters = reactive({
  year: undefined as number | undefined,
  province: "山东",
  batch: "",
  student_type: "",
});
const planFilters = reactive({
  year: undefined as number | undefined,
  province: "山东",
  batch: "",
  student_type: "",
  keyword: "",
});

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

async function loadAdmissions(options: { resetPage?: boolean } = {}): Promise<void> {
  if (options.resetPage) admissionPagination.page = 1;
  const query = new URLSearchParams();
  query.set("college_id", String(collegeId.value));
  if (admissionFilters.year) query.set("year", String(admissionFilters.year));
  if (admissionFilters.province) query.set("province", admissionFilters.province);
  if (admissionFilters.batch) query.set("batch", admissionFilters.batch);
  if (admissionFilters.student_type) query.set("student_type", admissionFilters.student_type);
  query.set("page", String(admissionPagination.page));
  query.set("page_size", String(admissionPagination.page_size));
  admissionsLoading.value = true;
  try {
    const response = await apiRequest<PaginatedResponse<AdmissionRecord>>(`/api/admissions/page?${query.toString()}`);
    admissions.value = response.items;
    admissionPagination.total = response.total;
    admissionPagination.page = response.page;
    admissionPagination.page_size = response.page_size;
  } finally {
    admissionsLoading.value = false;
  }
}

async function loadPlans(options: { resetPage?: boolean } = {}): Promise<void> {
  if (options.resetPage) planPagination.page = 1;
  const query = new URLSearchParams();
  query.set("college_id", String(collegeId.value));
  if (planFilters.year) query.set("year", String(planFilters.year));
  if (planFilters.province) query.set("province", planFilters.province);
  if (planFilters.batch) query.set("batch", planFilters.batch);
  if (planFilters.student_type) query.set("student_type", planFilters.student_type);
  if (planFilters.keyword) query.set("keyword", planFilters.keyword);
  query.set("page", String(planPagination.page));
  query.set("page_size", String(planPagination.page_size));
  plansLoading.value = true;
  try {
    const response = await apiRequest<PaginatedResponse<EnrollmentPlanItem>>(`/api/enrollment-plans/page?${query.toString()}`);
    plans.value = response.items;
    planPagination.total = response.total;
    planPagination.page = response.page;
    planPagination.page_size = response.page_size;
  } finally {
    plansLoading.value = false;
  }
}

function handleAdmissionPageChange(page: number): void {
  admissionPagination.page = page;
  void loadAdmissions();
}

function handleAdmissionPageSizeChange(pageSize: number): void {
  admissionPagination.page_size = pageSize;
  admissionPagination.page = 1;
  void loadAdmissions();
}

function handlePlanPageChange(page: number): void {
  planPagination.page = page;
  void loadPlans();
}

function handlePlanPageSizeChange(pageSize: number): void {
  planPagination.page_size = pageSize;
  planPagination.page = 1;
  void loadPlans();
}

function resetAdmissionFilters(): void {
  admissionFilters.year = undefined;
  admissionFilters.province = "山东";
  admissionFilters.batch = "";
  admissionFilters.student_type = "";
  void loadAdmissions({ resetPage: true });
}

function resetPlanFilters(): void {
  planFilters.year = undefined;
  planFilters.province = "山东";
  planFilters.batch = "";
  planFilters.student_type = "";
  planFilters.keyword = "";
  void loadPlans({ resetPage: true });
}

onMounted(() => {
  void loadDetail();
  void loadAdmissions();
  void loadPlans();
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

.detail-filter-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) repeat(2, auto);
  gap: 10px;
  align-items: center;
  margin-bottom: 14px;
}

.table-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

@media (max-width: 960px) {
  .detail-grid,
  .contact-list,
  .detail-filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
