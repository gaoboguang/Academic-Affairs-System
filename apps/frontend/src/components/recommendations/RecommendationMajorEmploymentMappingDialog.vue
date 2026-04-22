<template>
  <el-dialog
    v-model="visibleModel"
    :title="title"
    width="760px"
    destroy-on-close
    :close-on-click-modal="false"
    @closed="emit('closed')"
  >
    <el-form label-width="100px">
      <div class="form-grid">
        <el-form-item label="专业">
          <el-select v-model="form.major_id" filterable placeholder="选择专业">
            <el-option v-for="item in majorOptions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="就业方向">
          <el-select v-model="form.direction_id" filterable placeholder="选择就业方向">
            <el-option v-for="item in directionOptions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="映射强度">
          <el-select v-model="form.strength">
            <el-option v-for="item in strengthOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="适合学生">
          <el-select
            v-model="form.supported_student_types_json"
            multiple
            filterable
            collapse-tags
            placeholder="可选"
          >
            <el-option v-for="item in studentTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="需读研增强">
          <el-switch v-model="form.requires_postgraduate" />
        </el-form-item>
        <el-form-item label="需资格证">
          <el-switch v-model="form.requires_certificate" />
        </el-form-item>
        <el-form-item label="适合艺体">
          <el-switch v-model="form.supports_art" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="推荐说明" class="span-two">
          <el-input v-model="form.recommendation_note" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="备注" class="span-two">
          <el-input v-model="form.note" type="textarea" :rows="2" />
        </el-form-item>
      </div>
    </el-form>
    <template #footer>
      <el-button @click="visibleModel = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="emit('submit')">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { recommendationStudentTypeOptions } from "./helpers";

import type { EmploymentDirectionItem, MajorEmploymentMappingPayload, MajorItem } from "./types";

const props = defineProps<{
  visible: boolean;
  title: string;
  form: MajorEmploymentMappingPayload;
  majorOptions: MajorItem[];
  directionOptions: EmploymentDirectionItem[];
  strengthOptions: Array<{ value: string; label: string }>;
  saving: boolean;
}>();

const emit = defineEmits<{
  "update:visible": [value: boolean];
  submit: [];
  closed: [];
}>();

const studentTypeOptions = recommendationStudentTypeOptions;

const visibleModel = computed({
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

.span-two {
  grid-column: span 2;
}

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .span-two {
    grid-column: span 1;
  }
}
</style>
