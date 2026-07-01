<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="880px"
    destroy-on-close
    :close-on-click-modal="false"
    :close-on-press-escape="!saving"
    @closed="emit('closed')"
  >
    <el-form label-width="92px" :disabled="controlsDisabled">
      <div class="form-grid">
        <el-form-item label="模板名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="对象类型">
          <el-select v-model="form.target_type" style="width: 100%">
            <el-option
              v-for="option in templateTargetTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
      </div>
    </el-form>

    <div class="section-head compact">
      <div>
        <h4>题目列表</h4>
        <p>维度权重会按题目权重自动汇总。</p>
      </div>
      <el-button :disabled="controlsDisabled" @click="emit('add-question')">新增题目</el-button>
    </div>

    <el-table :data="questions" stripe>
      <el-table-column label="维度" min-width="130">
        <template #default="{ row }">
          <el-input v-model="row.dimension_name" :disabled="controlsDisabled" />
        </template>
      </el-table-column>
      <el-table-column label="题目" min-width="240">
        <template #default="{ row }">
          <el-input v-model="row.question_text" :disabled="controlsDisabled" />
        </template>
      </el-table-column>
      <el-table-column label="满分" width="100">
        <template #default="{ row }">
          <el-input-number v-model="row.score_max" :min="1" :max="100" :disabled="controlsDisabled" />
        </template>
      </el-table-column>
      <el-table-column label="权重" width="100">
        <template #default="{ row }">
          <el-input-number v-model="row.weight" :min="0" :step="0.1" :disabled="controlsDisabled" />
        </template>
      </el-table-column>
      <el-table-column label="排序" width="90">
        <template #default="{ row }">
          <el-input-number v-model="row.sort_order" :min="0" :disabled="controlsDisabled" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90">
        <template #default="{ $index }">
          <el-button link type="danger" :disabled="controlsDisabled" @click="emit('remove-question', $index)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button :disabled="controlsDisabled" @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" :disabled="controlsDisabled" @click="emit('save')">保存模板</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { templateTargetTypeOptions } from "./helpers";
import type { EvaluationQuestion, TemplateFormState } from "./types";

const props = defineProps<{
  visible: boolean;
  title: string;
  saving: boolean;
  controlsDisabled: boolean;
  form: TemplateFormState;
  questions: EvaluationQuestion[];
}>();

const emit = defineEmits<{
  "update:visible": [value: boolean];
  closed: [];
  "add-question": [];
  "remove-question": [index: number];
  save: [];
}>();

const dialogVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit("update:visible", value),
});
</script>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
