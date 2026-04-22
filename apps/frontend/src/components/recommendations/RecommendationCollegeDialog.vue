<template>
  <el-dialog
    v-model="visibleModel"
    :title="title"
    width="760px"
    destroy-on-close
    :close-on-click-modal="false"
    @closed="emit('closed')"
  >
    <el-form label-width="92px">
      <div class="form-grid">
        <el-form-item label="院校名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="院校代码">
          <el-input v-model="form.college_code" />
        </el-form-item>
        <el-form-item label="省份">
          <el-select v-model="form.province" clearable filterable style="width: 100%">
            <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
          </el-select>
        </el-form-item>
        <el-form-item label="城市">
          <el-input v-model="form.city" />
        </el-form-item>
        <el-form-item label="院校类型">
          <el-input v-model="form.school_type" />
        </el-form-item>
        <el-form-item label="官网">
          <el-input v-model="form.website" />
        </el-form-item>
        <el-form-item label="层级标签" class="span-two">
          <el-select
            v-model="form.school_level_tags_json"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            style="width: 100%"
          >
            <el-option v-for="item in schoolLevelOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="院校别名" class="span-two">
          <el-select
            v-model="form.alias_names"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="支持艺体">
          <el-switch v-model="form.supports_art" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="简介" class="span-two">
          <el-input v-model="form.intro" type="textarea" :rows="3" />
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

import type { CollegePayload } from "./types";

const props = defineProps<{
  visible: boolean;
  title: string;
  form: CollegePayload;
  provinceOptions: string[];
  schoolLevelOptions: string[];
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
