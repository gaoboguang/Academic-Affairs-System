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
        <el-form-item label="方向名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="方向分类">
          <el-select v-model="form.category" clearable filterable allow-create default-first-option>
            <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="别名" class="span-two">
          <el-select
            v-model="form.alias_names_json"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            placeholder="支持录入多个别名"
          />
        </el-form-item>
        <el-form-item label="常见岗位" class="span-two">
          <el-select
            v-model="form.common_job_types_json"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            placeholder="支持录入多个岗位类别"
          />
        </el-form-item>
        <el-form-item label="常见行业" class="span-two">
          <el-select
            v-model="form.common_industries_json"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            placeholder="支持录入多个行业"
          />
        </el-form-item>
        <el-form-item label="方向说明" class="span-two">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="偏继续深造">
          <el-switch v-model="form.prefers_postgraduate" />
        </el-form-item>
        <el-form-item label="需资格证">
          <el-switch v-model="form.requires_certificate" />
        </el-form-item>
        <el-form-item label="长培养路径">
          <el-switch v-model="form.requires_long_cycle" />
        </el-form-item>
        <el-form-item label="适合艺体">
          <el-switch v-model="form.supports_art" />
        </el-form-item>
        <el-form-item label="风险提示" class="span-two">
          <el-input v-model="form.risk_note" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="数据来源" class="span-two">
          <el-input v-model="form.source_note" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
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

import type { EmploymentDirectionPayload } from "./types";

const props = defineProps<{
  visible: boolean;
  title: string;
  form: EmploymentDirectionPayload;
  categoryOptions: string[];
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
