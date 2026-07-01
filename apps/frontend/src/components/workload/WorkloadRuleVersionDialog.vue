<template>
  <el-dialog
    v-model="dialogVisible"
    title="新建规则版本"
    width="520px"
    destroy-on-close
    :close-on-click-modal="false"
    :close-on-press-escape="!saving"
    @closed="emit('closed')"
  >
    <div class="filter-grid">
      <el-input v-model="form.name" placeholder="规则名称" :disabled="controlsDisabled" />
      <el-select
        v-model="form.semester_id"
        clearable
        filterable
        placeholder="适用学期，可不选"
        :disabled="controlsDisabled"
      >
        <el-option
          v-for="semester in semesterOptions"
          :key="semester.id"
          :label="formatSemesterLabel(semester)"
          :value="semester.id"
        />
      </el-select>
      <el-select v-model="form.status" placeholder="状态" :disabled="controlsDisabled">
        <el-option
          v-for="option in ruleVersionStatusOptions"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </el-select>
      <el-switch
        v-model="form.is_default"
        inline-prompt
        active-text="默认"
        inactive-text="普通"
        :disabled="controlsDisabled"
      />
      <el-input v-model="form.note" placeholder="备注" :disabled="controlsDisabled" />
      <el-switch
        v-model="form.is_active"
        inline-prompt
        active-text="启用"
        inactive-text="停用"
        :disabled="controlsDisabled"
      />
    </div>
    <template #footer>
      <el-button :disabled="saving" @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" :disabled="controlsDisabled" @click="emit('save')">创建</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { OptionItem } from "../../stores/reference";
import { formatSemesterLabel, ruleVersionStatusOptions } from "./helpers";
import type { CreateRuleForm } from "./types";

const props = defineProps<{
  visible: boolean;
  form: CreateRuleForm;
  semesterOptions: OptionItem[];
  saving: boolean;
  controlsDisabled: boolean;
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
