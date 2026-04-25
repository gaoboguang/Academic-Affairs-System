<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>历年录取数据</h3>
        <p>按年份、省份、院校、专业和学生类别维护录取基线，为推荐引擎提供近三年参考数据。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('download-template')">模板下载</el-button>
        <el-upload :show-file-list="false" :auto-upload="false" :on-change="handleImport">
          <el-button type="primary">导入录取数据</el-button>
        </el-upload>
      </div>
    </div>

    <ImportFeedbackPanel :result="admissionImportResult" />

    <div class="filter-grid">
      <el-select v-model="filters.year" clearable placeholder="年份">
        <el-option v-for="year in admissionYearOptions" :key="year" :label="String(year)" :value="year" />
      </el-select>
      <el-select v-model="filters.province" clearable filterable placeholder="省份">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-select v-model="filters.college_id" clearable filterable placeholder="院校">
        <el-option v-for="college in collegeOptions" :key="college.id" :label="college.name" :value="college.id" />
      </el-select>
      <el-select v-model="filters.student_type" clearable filterable placeholder="学生类别">
        <el-option v-for="item in studentTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" @click="emit('load')">查询</el-button>
      <el-button @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="admissions" stripe>
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
    <el-empty v-if="!admissions.length" description="暂无录取数据" />
  </section>
</template>

<script setup lang="ts">
import type { UploadFile } from "element-plus";

import ImportFeedbackPanel from "../common/ImportFeedbackPanel.vue";
import type { AdmissionImportResponse, AdmissionRecord, CollegeItem } from "./types";

interface AdmissionFiltersState {
  year?: number;
  province: string;
  college_id?: number;
  student_type: string;
}

defineProps<{
  admissions: AdmissionRecord[];
  filters: AdmissionFiltersState;
  admissionYearOptions: number[];
  provinceOptions: string[];
  collegeOptions: CollegeItem[];
  studentTypeOptions: Array<{ value: string; label: string }>;
  admissionImportResult: AdmissionImportResponse | null;
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
</style>
