<template>
  <el-dialog
    v-model="visibleModel"
    :title="title"
    width="760px"
    destroy-on-close
    :close-on-click-modal="false"
    @closed="emit('closed')"
  >
    <el-form label-width="104px">
      <div class="form-grid">
        <el-form-item label="省份">
          <el-select v-model="form.province" filterable allow-create default-first-option style="width: 100%">
            <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
          </el-select>
        </el-form-item>
        <el-form-item label="年份">
          <el-select v-model="form.year" style="width: 100%">
            <el-option v-for="year in yearOptions" :key="year" :label="String(year)" :value="year" />
          </el-select>
        </el-form-item>
        <el-form-item label="高考模式">
          <el-select v-model="form.exam_mode" filterable allow-create default-first-option style="width: 100%">
            <el-option v-for="item in examModeOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="考生类别">
          <el-select v-model="form.candidate_type" clearable filterable style="width: 100%">
            <el-option label="通用 / 不区分类别" value="" />
            <el-option v-for="item in candidateTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="批次">
          <el-input v-model="form.batch" />
        </el-form-item>
        <el-form-item label="批次顺序">
          <el-input-number v-model="form.batch_order" :min="1" :step="1" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="总分口径">
          <el-input-number v-model="form.total_score" :min="1" :step="10" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="志愿上限">
          <el-input-number
            v-model="form.volunteer_limit"
            :min="1"
            :step="1"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="单位类型">
          <el-select v-model="form.volunteer_unit_type" style="width: 100%">
            <el-option v-for="item in unitTypeOptions" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item label="选科模式">
          <el-select v-model="form.subject_requirement_mode" clearable style="width: 100%">
            <el-option v-for="item in subjectRequirementModeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="平行模式">
          <el-select v-model="form.parallel_rule_mode" clearable style="width: 100%">
            <el-option v-for="item in parallelRuleModeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业上限">
          <el-input-number
            v-model="form.max_major_per_unit"
            :min="1"
            :step="1"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item label="平行志愿">
          <el-switch v-model="form.is_parallel" />
        </el-form-item>
        <el-form-item label="服从调剂">
          <el-switch v-model="form.allow_adjustment" />
        </el-form-item>
        <el-form-item label="征集志愿">
          <el-switch v-model="form.support_collect_round" />
        </el-form-item>
        <el-form-item label="统一必选" class="span-two">
          <el-select
            v-model="form.required_subjects_json"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="首选科目" class="span-two">
          <el-select
            v-model="form.first_choice_subjects_json"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="再选科目" class="span-two">
          <el-select
            v-model="form.reselect_subjects_json"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="赋分摘要" class="span-two">
          <el-input v-model="form.score_rule_summary" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="特殊规则" class="span-two">
          <el-select
            v-model="form.special_rules_json"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            style="width: 100%"
          >
            <el-option v-for="item in specialRuleOptions" :key="item" :label="item" :value="item" />
          </el-select>
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

import type { ProvinceVolunteerRulePayload } from "./types";

const props = defineProps<{
  visible: boolean;
  title: string;
  form: ProvinceVolunteerRulePayload;
  saving: boolean;
  yearOptions: number[];
  provinceOptions: string[];
  examModeOptions: string[];
  candidateTypeOptions: ReadonlyArray<{ value: string; label: string }>;
  subjectRequirementModeOptions: ReadonlyArray<{ value: string; label: string }>;
  parallelRuleModeOptions: ReadonlyArray<{ value: string; label: string }>;
  unitTypeOptions: string[];
  specialRuleOptions: string[];
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
