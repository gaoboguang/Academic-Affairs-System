<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="620px"
    destroy-on-close
    :close-on-click-modal="false"
    @closed="emit('closed')"
  >
    <el-form label-width="92px">
      <div class="form-grid">
        <el-form-item label="版本名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="学期">
          <el-select v-model="form.semester_id" clearable filterable style="width: 100%">
            <el-option
              v-for="item in semesters"
              :key="item.id"
              :label="semesterLabel(item)"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="默认版本">
          <el-switch v-model="form.is_default" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option
              v-for="option in ruleVersionStatusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
      </div>
      <el-form-item label="备注">
        <el-input v-model="form.note" type="textarea" :rows="3" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="emit('save')">保存版本</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { OptionItem } from "../../stores/reference";
import { ruleVersionStatusOptions, semesterLabel } from "./helpers";
import type { RuleVersionFormState } from "./types";

const props = defineProps<{
  visible: boolean;
  title: string;
  saving: boolean;
  form: RuleVersionFormState;
  semesters: OptionItem[];
}>();

const emit = defineEmits<{
  "update:visible": [value: boolean];
  closed: [];
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
