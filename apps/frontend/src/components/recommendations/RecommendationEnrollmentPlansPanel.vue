<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>招生计划库</h3>
        <p>按年份、省份、批次和院校专业组维护当年招生计划，为志愿筛选和风险校验提供当前基线。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('download-template')">模板下载</el-button>
        <el-upload
          :show-file-list="false"
          :auto-upload="false"
          :disabled="importing || loading"
          :on-change="handleImport"
        >
          <el-button type="primary" :loading="importing" :disabled="loading || importing">导入招生计划</el-button>
        </el-upload>
      </div>
    </div>

    <el-alert v-if="loadError" class="planning-panel-alert" type="error" show-icon :closable="false" title="招生计划加载失败">
      <template #default>
        <div class="planning-alert-body">
          <span>{{ loadError }}</span>
          <el-button link type="primary" :loading="loading" @click="emit('load')">重新加载招生计划库</el-button>
        </div>
      </template>
    </el-alert>

    <ImportFeedbackPanel :result="enrollmentPlanImportResult" />

    <div class="filter-grid">
      <el-select v-model="filters.year" clearable :disabled="loading" placeholder="年份">
        <el-option v-for="year in yearOptions" :key="year" :label="String(year)" :value="year" />
      </el-select>
      <el-select v-model="filters.province" clearable filterable :disabled="loading" placeholder="省份">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-select v-model="filters.batch" clearable filterable :disabled="loading" placeholder="批次">
        <el-option v-for="item in batchOptions" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="filters.college_id" clearable filterable :disabled="loading" placeholder="院校">
        <el-option v-for="college in collegeOptions" :key="college.id" :label="college.name" :value="college.id" />
      </el-select>
      <el-select v-model="filters.student_type" clearable filterable :disabled="loading" placeholder="学生类别">
        <el-option v-for="item in studentTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-input v-model="filters.keyword" :disabled="loading" placeholder="按院校 / 专业 / 专业组筛选" />
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" :loading="loading" @click="emit('load')">查询</el-button>
      <el-button :disabled="loading" @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="enrollmentPlans" stripe v-loading="loading">
      <template #empty>
        <el-empty :description="enrollmentPlanEmptyDescription">
          <el-button v-if="loadError" type="primary" plain :loading="loading" @click="emit('load')">
            重新加载招生计划库
          </el-button>
        </el-empty>
      </template>
      <el-table-column label="年份" prop="year" width="90" />
      <el-table-column label="省份" prop="province" width="110" />
      <el-table-column label="批次" prop="batch" min-width="110" />
      <el-table-column label="模式" prop="exam_mode" width="120" />
      <el-table-column label="院校 / 专业" min-width="260">
        <template #default="{ row }">
          <div class="name-stack">
            <strong>{{ row.college_name || "-" }}</strong>
            <span>{{ formatPlanTarget(row) }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="计划人数" prop="plan_count" width="100" />
      <el-table-column label="选科要求" prop="subject_requirement" min-width="140" />
      <el-table-column label="学费 / 学制" min-width="150">
        <template #default="{ row }">
          {{ [row.tuition_fee, row.schooling_years].filter(Boolean).join(" / ") || "-" }}
        </template>
      </el-table-column>
      <el-table-column label="培养地点" prop="training_location" min-width="130" />
      <el-table-column label="学生类别" width="100">
        <template #default="{ row }">
          {{ formatStudentType(row.student_type) }}
        </template>
      </el-table-column>
      <el-table-column label="导入批次" prop="import_batch_name" min-width="140" />
      <el-table-column label="数据来源" prop="source_note" min-width="180" />
    </el-table>
    <el-pagination
      v-if="pagination.total"
      class="table-pagination"
      background
      layout="total, sizes, prev, pager, next"
      :current-page="pagination.page"
      :page-size="pagination.page_size"
      :page-sizes="[50, 100, 200]"
      :total="pagination.total"
      @current-change="emit('page-change', $event)"
      @size-change="emit('page-size-change', $event)"
    />
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { UploadFile } from "element-plus";

import ImportFeedbackPanel from "../common/ImportFeedbackPanel.vue";
import type { CollegeItem, EnrollmentPlanItem, EnrollmentPlanImportResponse, PaginationState } from "./types";

interface EnrollmentPlanFiltersState {
  year?: number;
  province: string;
  batch: string;
  college_id?: number;
  student_type: string;
  keyword: string;
}

const props = defineProps<{
  enrollmentPlans: EnrollmentPlanItem[];
  filters: EnrollmentPlanFiltersState;
  yearOptions: number[];
  provinceOptions: string[];
  batchOptions: string[];
  collegeOptions: CollegeItem[];
  studentTypeOptions: Array<{ value: string; label: string }>;
  enrollmentPlanImportResult: EnrollmentPlanImportResponse | null;
  pagination: PaginationState;
  loading: boolean;
  loadError: string;
  importing: boolean;
}>();

const emit = defineEmits<{
  load: [];
  reset: [];
  "page-change": [value: number];
  "page-size-change": [value: number];
  "download-template": [];
  import: [value: UploadFile];
}>();

function handleImport(file: UploadFile): void {
  emit("import", file);
}

function formatPlanTarget(row: EnrollmentPlanItem): string {
  const target = row.major_name || "未填写专业";
  if (row.major_group_code) {
    return `${row.major_group_code}组 / ${target}`;
  }
  return target;
}

function formatStudentType(value?: string | null): string {
  if (!value) return "-";
  const mapping: Record<string, string> = {
    general: "普通生",
    art: "艺体生",
    sports: "体育生",
    repeat: "复读生",
    spring_exam: "春季高考",
    independent_recruitment: "单独招生",
    comprehensive_evaluation: "综合评价招生",
  };
  return mapping[value] ?? value;
}

const hasActiveFilters = computed(() =>
  Boolean(
    props.filters.year ||
      props.filters.province !== "山东" ||
      props.filters.batch ||
      props.filters.college_id ||
      props.filters.student_type ||
      props.filters.keyword,
  ),
);
const enrollmentPlanEmptyDescription = computed(() => {
  if (props.loadError) return "招生计划加载失败，请重新加载。";
  if (props.loading) return "正在加载招生计划";
  if (hasActiveFilters.value) return "没有符合当前筛选条件的招生计划。";
  return "暂无招生计划数据，可以先下载模板并导入。";
});
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.toolbar-row {
  margin-bottom: 16px;
}

.planning-panel-alert {
  margin-bottom: 16px;
}

.planning-alert-body {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.table-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.result-alert {
  margin-top: 16px;
}

.name-stack {
  display: grid;
  gap: 4px;
}

.name-stack strong {
  color: #203449;
}

.name-stack span {
  color: #7b8d9c;
  font-size: 13px;
}
</style>
