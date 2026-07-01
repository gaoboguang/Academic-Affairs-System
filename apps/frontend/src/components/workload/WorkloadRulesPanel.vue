<template>
  <div class="page-shell">
    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>规则版本</h3>
          <p>规则版本计算后会锁定，不允许原地修改，避免历史结果被后续调整覆盖。</p>
        </div>
        <div class="action-row">
          <el-button
            type="primary"
            :disabled="ruleActionsDisabled"
            @click="emit('open-rule-version-dialog')"
          >
            新建规则版本
          </el-button>
          <el-button
            :disabled="ruleItemControlsDisabled || !selectedRuleVersionId"
            :loading="savingRuleItems"
            @click="emit('save-rule-items')"
          >
            保存规则项
          </el-button>
        </div>
      </div>
      <el-alert
        v-if="ruleVersionsError"
        class="panel-alert"
        type="warning"
        show-icon
        :closable="false"
        :title="ruleVersionsError"
      />
      <div class="table-shell" v-loading="loadingRuleVersions">
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
          <template #empty>
            <el-empty :description="ruleVersionsEmptyDescription" />
          </template>
        </el-table>
      </div>

      <div class="section-head sub-head">
        <div>
          <h3>规则项</h3>
          <p>覆盖学科、年级、班型、课程类型、班额和班主任附加量。</p>
        </div>
        <el-button
          :disabled="ruleItemControlsDisabled || !selectedRuleVersionId"
          @click="emit('add-rule-item')"
        >
          新增规则项
        </el-button>
      </div>
      <el-alert
        v-if="ruleItemsError"
        class="panel-alert"
        type="warning"
        show-icon
        :closable="false"
        :title="ruleItemsError"
      />
      <el-empty v-if="!selectedRuleVersionId" description="请选择一个规则版本" />
      <div v-else class="table-shell" v-loading="loadingRuleItems">
        <el-table :data="ruleItems" stripe>
          <el-table-column label="维度" width="140">
            <template #default="{ row }">
              <el-select v-model="row.dimension_type" :disabled="ruleItemControlsDisabled">
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
              <el-input
                v-model="row.match_key"
                placeholder="如 math / 高二 / key / true"
                :disabled="ruleItemControlsDisabled"
              />
            </template>
          </el-table-column>
          <el-table-column label="系数" width="140">
            <template #default="{ row }">
              <el-input-number
                v-model="row.coefficient"
                :precision="2"
                :step="0.05"
                controls-position="right"
                :disabled="ruleItemControlsDisabled"
              />
            </template>
          </el-table-column>
          <el-table-column label="固定量" width="140">
            <template #default="{ row }">
              <el-input-number
                v-model="row.fixed_value"
                :precision="2"
                :step="0.5"
                controls-position="right"
                :disabled="ruleItemControlsDisabled"
              />
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="180">
            <template #default="{ row }">
              <el-input v-model="row.note" placeholder="说明" :disabled="ruleItemControlsDisabled" />
            </template>
          </el-table-column>
          <el-table-column label="启用" width="90">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" :disabled="ruleItemControlsDisabled" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ $index }">
              <el-button
                link
                type="danger"
                :disabled="ruleItemControlsDisabled"
                @click="emit('remove-rule-item', $index)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="ruleItemsEmptyDescription" />
          </template>
        </el-table>
      </div>
    </section>

    <section class="soft-card panel-block" v-loading="loadingExtras || loadingTeacherOptions">
      <div class="section-head">
        <div>
          <h3>附加量化项</h3>
          <p>用于备课组长、公开课、竞赛辅导等手工补录量化项。</p>
        </div>
        <el-button
          type="primary"
          :loading="savingExtra"
          :disabled="extraControlsDisabled"
          @click="emit('create-extra')"
        >
          新增附加项
        </el-button>
      </div>
      <el-alert
        v-if="teacherOptionsError || extrasError"
        class="panel-alert"
        type="warning"
        show-icon
        :closable="false"
        title="附加项数据加载不完整"
      >
        <div class="panel-alert-list">
          <p v-if="teacherOptionsError">{{ teacherOptionsError }}</p>
          <p v-if="extrasError">{{ extrasError }}</p>
        </div>
      </el-alert>
      <div class="filter-grid">
        <el-select
          v-model="extraForm.teacher_id"
          filterable
          placeholder="教师"
          :loading="loadingTeacherOptions"
          :disabled="extraControlsDisabled"
        >
          <el-option v-for="teacher in teacherOptions" :key="teacher.id" :label="teacher.name" :value="teacher.id" />
        </el-select>
        <el-input v-model="extraForm.item_name" placeholder="项目名称" :disabled="extraControlsDisabled" />
        <el-input-number
          v-model="extraForm.quantity"
          :precision="2"
          :step="0.5"
          controls-position="right"
          :disabled="extraControlsDisabled"
        />
        <el-input-number
          v-model="extraForm.coefficient"
          :precision="2"
          :step="0.5"
          controls-position="right"
          :disabled="extraControlsDisabled"
        />
        <el-input-number
          v-model="extraForm.amount"
          :precision="2"
          :step="0.5"
          controls-position="right"
          :disabled="extraControlsDisabled"
        />
        <el-input v-model="extraForm.note" placeholder="备注" :disabled="extraControlsDisabled" />
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
          <template #empty>
            <el-empty :description="extrasEmptyDescription" />
          </template>
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
  loadingRuleVersions: boolean;
  ruleVersionsError: string;
  loadingRuleItems: boolean;
  ruleItemsError: string;
  loadingExtras: boolean;
  extrasError: string;
  loadingTeacherOptions: boolean;
  teacherOptionsError: string;
  ruleActionsDisabled: boolean;
  ruleItemControlsDisabled: boolean;
  extraControlsDisabled: boolean;
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

const ruleVersionsEmptyDescription = computed(() => {
  if (props.ruleVersionsError) return "规则版本加载失败，请使用页面顶部重试入口重新加载。";
  return "当前还没有规则版本，请先新建规则版本。";
});

const ruleItemsEmptyDescription = computed(() => {
  if (props.ruleItemsError) return "规则项加载失败，请使用页面顶部重试入口重新加载。";
  return "当前规则版本还没有规则项。可点击“新增规则项”补齐系数。";
});

const extrasEmptyDescription = computed(() => {
  if (props.extrasError) return "附加项加载失败，请使用页面顶部重试入口重新加载。";
  return "当前学期还没有附加量化项。";
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

.panel-alert {
  margin-bottom: 14px;
}

.panel-alert-list {
  display: grid;
  gap: 6px;
  margin-top: 8px;
}

.panel-alert-list p {
  margin: 0;
}
</style>
