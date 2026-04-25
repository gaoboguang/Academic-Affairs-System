<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>招生计划库</h3>
        <p>按年份、省份、批次和院校专业组维护当年招生计划，为志愿筛选和风险校验提供当前基线。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('download-template')">模板下载</el-button>
        <el-upload :show-file-list="false" :auto-upload="false" :on-change="handleImport">
          <el-button type="primary">导入招生计划</el-button>
        </el-upload>
      </div>
    </div>

    <ImportFeedbackPanel :result="enrollmentPlanImportResult" />

    <div class="filter-grid">
      <el-select v-model="filters.year" clearable placeholder="年份">
        <el-option v-for="year in yearOptions" :key="year" :label="String(year)" :value="year" />
      </el-select>
      <el-select v-model="filters.province" clearable filterable placeholder="省份">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-select v-model="filters.batch" clearable filterable placeholder="批次">
        <el-option v-for="item in batchOptions" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="filters.college_id" clearable filterable placeholder="院校">
        <el-option v-for="college in collegeOptions" :key="college.id" :label="college.name" :value="college.id" />
      </el-select>
      <el-select v-model="filters.student_type" clearable filterable placeholder="学生类别">
        <el-option v-for="item in studentTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-input v-model="filters.keyword" placeholder="按院校 / 专业 / 专业组筛选" />
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" @click="emit('load')">查询</el-button>
      <el-button @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="enrollmentPlans" stripe>
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
    <el-empty v-if="!enrollmentPlans.length" description="暂无招生计划数据" />
  </section>
</template>

<script setup lang="ts">
import type { UploadFile } from "element-plus";

import ImportFeedbackPanel from "../common/ImportFeedbackPanel.vue";
import type { CollegeItem, EnrollmentPlanItem, EnrollmentPlanImportResponse } from "./types";

interface EnrollmentPlanFiltersState {
  year?: number;
  province: string;
  batch: string;
  college_id?: number;
  student_type: string;
  keyword: string;
}

defineProps<{
  enrollmentPlans: EnrollmentPlanItem[];
  filters: EnrollmentPlanFiltersState;
  yearOptions: number[];
  provinceOptions: string[];
  batchOptions: string[];
  collegeOptions: CollegeItem[];
  studentTypeOptions: Array<{ value: string; label: string }>;
  enrollmentPlanImportResult: EnrollmentPlanImportResponse | null;
}>();

const emit = defineEmits<{
  load: [];
  reset: [];
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
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.toolbar-row {
  margin-bottom: 16px;
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
