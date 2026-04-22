<template>
  <div class="page-shell">
    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>规则版本</h3>
          <p>规则版本计算后会锁定，不允许原地修改，避免历史结果被后续调整覆盖。</p>
        </div>
        <div class="action-row">
          <el-button type="primary" @click="emit('open-rule-version-dialog')">新建规则版本</el-button>
          <el-button :disabled="!selectedRuleVersionId" :loading="savingRuleItems" @click="emit('save-rule-items')">
            保存规则项
          </el-button>
        </div>
      </div>
      <div class="table-shell">
        <el-table :data="ruleVersions" stripe>
          <el-table-column label="名称" min-width="180">
            <template #default="{ row }">
              <span class="row-link" @click="ruleVersionModel = row.id">
                {{ row.name }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="适用学期" min-width="140">
            <template #default="{ row }">
              {{ row.semester_name ?? "通用规则" }}
            </template>
          </el-table-column>
          <el-table-column label="默认" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.is_default" type="success">默认</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="ruleStatusTagType(row.status)" effect="light">
                {{ formatRuleVersionStatus(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="备注" prop="note" min-width="150" />
        </el-table>
      </div>

      <div class="section-head sub-head">
        <div>
          <h3>规则项</h3>
          <p>覆盖学科、年级、班型、课程类型、班额和班主任附加量。</p>
        </div>
        <el-button :disabled="!selectedRuleVersionId" @click="emit('add-rule-item')">新增规则项</el-button>
      </div>
      <el-empty v-if="!selectedRuleVersionId" description="请选择一个规则版本" />
      <div v-else class="table-shell">
        <el-table :data="ruleItems" stripe>
          <el-table-column label="维度" width="140">
            <template #default="{ row }">
              <el-select v-model="row.dimension_type">
                <el-option
                  v-for="option in dimensionOptions"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="匹配值" min-width="160">
            <template #default="{ row }">
              <el-input v-model="row.match_key" placeholder="如 math / 高二 / key / true" />
            </template>
          </el-table-column>
          <el-table-column label="系数" width="140">
            <template #default="{ row }">
              <el-input-number v-model="row.coefficient" :precision="2" :step="0.05" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="固定量" width="140">
            <template #default="{ row }">
              <el-input-number v-model="row.fixed_value" :precision="2" :step="0.5" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="180">
            <template #default="{ row }">
              <el-input v-model="row.note" placeholder="说明" />
            </template>
          </el-table-column>
          <el-table-column label="启用" width="90">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ $index }">
              <el-button link type="danger" @click="emit('remove-rule-item', $index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>附加量化项</h3>
          <p>用于备课组长、公开课、竞赛辅导等手工补录量化项。</p>
        </div>
        <el-button type="primary" :loading="savingExtra" @click="emit('create-extra')">新增附加项</el-button>
      </div>
      <div class="filter-grid">
        <el-select v-model="extraForm.teacher_id" filterable placeholder="教师">
          <el-option v-for="teacher in teacherOptions" :key="teacher.id" :label="teacher.name" :value="teacher.id" />
        </el-select>
        <el-input v-model="extraForm.item_name" placeholder="项目名称" />
        <el-input-number v-model="extraForm.quantity" :precision="2" :step="0.5" controls-position="right" />
        <el-input-number v-model="extraForm.coefficient" :precision="2" :step="0.5" controls-position="right" />
        <el-input-number v-model="extraForm.amount" :precision="2" :step="0.5" controls-position="right" />
        <el-input v-model="extraForm.note" placeholder="备注" />
      </div>
      <div class="hint-text">
        如填写“固定量”，系统优先使用固定量；否则按数量 × 系数计算。
      </div>
      <div class="table-shell table-gap">
        <el-table :data="extras" stripe>
          <el-table-column label="教师" prop="teacher_name" min-width="120" />
          <el-table-column label="项目" prop="item_name" min-width="140" />
          <el-table-column label="数量" prop="quantity" width="90" />
          <el-table-column label="系数" prop="coefficient" width="90" />
          <el-table-column label="固定量" prop="amount" width="90" />
          <el-table-column label="备注" prop="note" min-width="150" />
        </el-table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { dimensionOptions, formatRuleVersionStatus, ruleStatusTagType } from "./helpers";
import type { ExtraFormState, ExtraItem, RuleItem, RuleVersionItem, TeacherOption } from "./types";

const props = defineProps<{
  ruleVersions: RuleVersionItem[];
  selectedRuleVersionId: number | null;
  ruleItems: RuleItem[];
  savingRuleItems: boolean;
  extras: ExtraItem[];
  extraForm: ExtraFormState;
  teacherOptions: TeacherOption[];
  savingExtra: boolean;
}>();

const emit = defineEmits<{
  "update:selectedRuleVersionId": [value: number | null];
  "open-rule-version-dialog": [];
  "save-rule-items": [];
  "add-rule-item": [];
  "remove-rule-item": [index: number];
  "create-extra": [];
}>();

const ruleVersionModel = computed<number | null>({
  get: () => props.selectedRuleVersionId,
  set: (value) => emit("update:selectedRuleVersionId", value),
});
</script>

<style scoped>
.sub-head {
  margin-top: 22px;
}

.row-link {
  color: #2d5883;
  cursor: pointer;
}
</style>
