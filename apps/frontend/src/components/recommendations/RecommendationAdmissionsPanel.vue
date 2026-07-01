<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>历年录取数据</h3>
        <p>按年份、省份、院校、专业和学生类别维护录取基线，为推荐引擎提供近三年参考数据。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('download-template')">模板下载</el-button>
        <el-upload
          :show-file-list="false"
          :auto-upload="false"
          :disabled="importing || loading"
          :on-change="handleImport"
        >
          <el-button type="primary" :loading="importing" :disabled="loading || importing">导入录取数据</el-button>
        </el-upload>
      </div>
    </div>

    <el-alert v-if="loadError" class="planning-panel-alert" type="error" show-icon :closable="false" title="录取数据加载失败">
      <template #default>
        <div class="planning-alert-body">
          <span>{{ loadError }}</span>
          <el-button link type="primary" :loading="loading" @click="emit('load')">重新加载录取库</el-button>
        </div>
      </template>
    </el-alert>

    <ImportFeedbackPanel :result="admissionImportResult" />

    <div class="filter-grid">
      <el-select v-model="filters.year" clearable :disabled="loading" placeholder="年份">
        <el-option v-for="year in admissionYearOptions" :key="year" :label="String(year)" :value="year" />
      </el-select>
      <el-select v-model="filters.province" clearable filterable :disabled="loading" placeholder="省份">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-select v-model="filters.college_id" clearable filterable :disabled="loading" placeholder="院校">
        <el-option v-for="college in collegeOptions" :key="college.id" :label="college.name" :value="college.id" />
      </el-select>
      <el-select v-model="filters.student_type" clearable filterable :disabled="loading" placeholder="学生类别">
        <el-option v-for="item in studentTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" :loading="loading" @click="emit('load')">查询</el-button>
      <el-button :disabled="loading" @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="admissions" stripe v-loading="loading">
      <template #empty>
        <el-empty :description="admissionEmptyDescription">
          <el-button v-if="loadError" type="primary" plain :loading="loading" @click="emit('load')">
            重新加载录取库
          </el-button>
        </el-empty>
      </template>
      <el-table-column label="年份" prop="year" width="90" />
      <el-table-column label="省份" prop="province" width="110" />
      <el-table-column label="批次" prop="batch" min-width="110" />
      <el-table-column label="院校" prop="college_name" min-width="180" />
      <el-table-column label="专业" prop="major_name" min-width="180" />
      <el-table-column label="学生类别" width="110">
        <template #default="{ row }">
          {{ formatStudentType(row.student_type) }}
        </template>
      </el-table-column>
      <el-table-column label="最低分" prop="min_score" width="100" />
      <el-table-column label="最低位次" prop="min_rank" width="110" />
      <el-table-column label="选科要求" prop="subject_requirement" min-width="120" />
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
import type { AdmissionImportResponse, AdmissionRecord, CollegeItem, PaginationState } from "./types";

interface AdmissionFiltersState {
  year?: number;
  province: string;
  college_id?: number;
  student_type: string;
}

const props = defineProps<{
  admissions: AdmissionRecord[];
  filters: AdmissionFiltersState;
  admissionYearOptions: number[];
  provinceOptions: string[];
  collegeOptions: CollegeItem[];
  studentTypeOptions: Array<{ value: string; label: string }>;
  admissionImportResult: AdmissionImportResponse | null;
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

function formatStudentType(value?: string | null): string {
  if (!value) return "-";
  const mapping: Record<string, string> = {
    general: "普通生",
    repeat: "复读生",
    art: "艺体生",
    sports: "体育生",
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
      props.filters.college_id ||
      props.filters.student_type,
  ),
);
const admissionEmptyDescription = computed(() => {
  if (props.loadError) return "录取数据加载失败，请重新加载。";
  if (props.loading) return "正在加载录取数据";
  if (hasActiveFilters.value) return "没有符合当前筛选条件的录取数据。";
  return "暂无录取数据，可以先下载模板并导入。";
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
</style>
