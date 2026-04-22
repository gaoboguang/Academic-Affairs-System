<template>
  <div class="page-shell">
    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>评教模板</h3>
          <p>模板定义维度、题目、分值和题目权重。已有导入历史的模板不再原地改题，改版请新建模板。</p>
        </div>
        <div class="action-row">
          <el-button @click="emit('reload-templates')">刷新</el-button>
          <el-button type="primary" @click="emit('open-create-template')">新增模板</el-button>
        </div>
      </div>

      <el-table :data="templates" stripe>
        <el-table-column label="模板名称" prop="name" min-width="200" />
        <el-table-column label="对象" width="120">
          <template #default="{ row }">
            {{ formatTemplateTargetType(row.target_type) }}
          </template>
        </el-table-column>
        <el-table-column label="题目数" width="90">
          <template #default="{ row }">
            {{ row.questions.length }}
          </template>
        </el-table-column>
        <el-table-column label="维度权重" min-width="220">
          <template #default="{ row }">
            {{ formatWeight(row.weight_json) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" effect="light">
              {{ row.is_active ? "启用" : "停用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="emit('edit-template', row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>导入与分析</h3>
          <p>导入 Excel 或 CSV 原始评教数据，按教师汇总综合得分、维度得分和题目表现。</p>
        </div>
      </div>

      <div class="filter-grid">
        <el-select v-model="evaluationImportForm.template_id" filterable placeholder="选择评教模板">
          <el-option v-for="item in templates" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="evaluationImportForm.semester_id" filterable placeholder="选择学期">
          <el-option
            v-for="item in semesters"
            :key="item.id"
            :label="semesterLabel(item)"
            :value="item.id"
          />
        </el-select>
        <el-upload :show-file-list="false" :auto-upload="false" :on-change="handleImportChange">
          <el-button type="primary">导入评教数据</el-button>
        </el-upload>
        <el-button @click="emit('reload-batches')">刷新批次</el-button>
      </div>

      <el-alert
        v-if="evaluationImportResult"
        class="result-alert"
        :title="evaluationImportResult.message"
        type="success"
        show-icon
        :closable="false"
      />

      <el-table :data="batches" stripe style="margin-top: 16px">
        <el-table-column label="模板" prop="template_name" min-width="180" />
        <el-table-column label="学期" prop="semester_name" min-width="160" />
        <el-table-column label="来源文件" prop="source_filename" min-width="180" />
        <el-table-column label="响应数" prop="response_count" width="90" />
        <el-table-column label="教师数" prop="teacher_count" width="90" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="evaluationBatchStatusType(row.status)" effect="light">
              {{ formatEvaluationBatchStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="emit('select-batch', row.id)">分析</el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { UploadFile } from "element-plus";

import type { OptionItem } from "../../stores/reference";
import { evaluationBatchStatusType, formatEvaluationBatchStatus, formatTemplateTargetType, formatWeight, semesterLabel } from "./helpers";
import type { EvaluationBatch, EvaluationImportFormState, EvaluationImportResponse, EvaluationTemplate } from "./types";

defineProps<{
  templates: EvaluationTemplate[];
  batches: EvaluationBatch[];
  evaluationImportResult: EvaluationImportResponse | null;
  evaluationImportForm: EvaluationImportFormState;
  semesters: OptionItem[];
}>();

const emit = defineEmits<{
  "reload-templates": [];
  "open-create-template": [];
  "edit-template": [item: EvaluationTemplate];
  "import-file": [file: UploadFile];
  "reload-batches": [];
  "select-batch": [batchId: number];
}>();

function handleImportChange(file: UploadFile): void {
  emit("import-file", file);
}
</script>

<style scoped>
.result-alert {
  margin-top: 16px;
}
</style>
