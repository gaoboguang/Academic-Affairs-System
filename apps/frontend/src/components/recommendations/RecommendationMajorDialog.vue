<template>
  <el-dialog
    v-model="visibleModel"
    :title="title"
    width="720px"
    destroy-on-close
    :close-on-click-modal="false"
    @closed="emit('closed')"
  >
    <el-form label-width="92px">
      <div class="form-grid">
        <el-form-item label="专业名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="专业代码">
          <el-input v-model="form.major_code" />
        </el-form-item>
        <el-form-item label="专业门类">
          <el-input v-model="form.category" />
        </el-form-item>
        <el-form-item label="专业方向">
          <el-input v-model="form.direction" />
        </el-form-item>
        <el-form-item label="就业去向" class="span-two">
          <el-input v-model="form.career_path" />
        </el-form-item>
        <el-form-item label="艺体相关">
          <el-switch v-model="form.is_art_related" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="备注" class="span-two">
          <el-input v-model="form.note" type="textarea" :rows="3" />
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

import type { MajorPayload } from "./types";

const props = defineProps<{
  visible: boolean;
  title: string;
  form: MajorPayload;
  saving: boolean;
}>();

const emit = defineEmits<{
  "update:visible": [value: boolean];
  submit: [];
  closed: [];
}>();

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
