<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>量化规则版本</h3>
        <p>规则版本一旦产生记录就不能原地改规则项，避免历史得分被新规则覆盖。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('reload-rule-versions')">刷新</el-button>
        <el-button type="primary" @click="emit('open-create-rule-version')">新增规则版本</el-button>
      </div>
    </div>

    <div class="quant-shell">
      <div class="soft-card inner-card">
        <el-table :data="ruleVersions" stripe>
          <el-table-column label="规则版本" prop="name" min-width="180" />
          <el-table-column label="学期" prop="semester_name" min-width="160" />
          <el-table-column label="默认" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_default ? 'success' : 'info'" effect="light">
                {{ row.is_default ? "是" : "否" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="ruleVersionStatusType(row.status)" effect="light">
                {{ formatRuleVersionStatus(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="emit('select-rule-version', row.id)">规则项</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="soft-card inner-card">
        <div class="section-head compact">
          <div>
            <h4>规则项</h4>
            <p v-if="selectedRuleVersionMeta">
              当前规则：{{ selectedRuleVersionMeta.name }}
              {{ selectedRuleVersionMeta.semester_name ? ` · ${selectedRuleVersionMeta.semester_name}` : "" }}
            </p>
            <p v-else>先选择一个规则版本</p>
          </div>
          <div class="action-row">
            <el-button :disabled="!selectedRuleVersionId" @click="emit('add-rule-item-row')">新增规则项</el-button>
            <el-button
              type="primary"
              :disabled="!selectedRuleVersionId"
              :loading="savingRuleItems"
              @click="emit('save-rule-items')"
            >
              保存规则项
            </el-button>
          </div>
        </div>

        <el-table :data="ruleItemRows" stripe>
          <el-table-column label="量化项" min-width="160">
            <template #default="{ row }">
              <el-input v-model="row.item_name" />
            </template>
          </el-table-column>
          <el-table-column label="类型" min-width="130">
            <template #default="{ row }">
              <el-input v-model="row.item_type" />
            </template>
          </el-table-column>
          <el-table-column label="默认分值" width="110">
            <template #default="{ row }">
              <el-input-number v-model="row.default_score" :step="0.5" />
            </template>
          </el-table-column>
          <el-table-column label="附件" width="90">
            <template #default="{ row }">
              <el-switch v-model="row.requires_attachment" />
            </template>
          </el-table-column>
          <el-table-column label="排序" width="90">
            <template #default="{ row }">
              <el-input-number v-model="row.sort_order" :min="0" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90">
            <template #default="{ $index }">
              <el-button link type="danger" @click="emit('remove-rule-item-row', $index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { formatRuleVersionStatus, ruleVersionStatusType } from "./helpers";
import type { RuleItem, RuleVersion } from "./types";

defineProps<{
  ruleVersions: RuleVersion[];
  selectedRuleVersionId: number | null;
  selectedRuleVersionMeta: RuleVersion | null;
  ruleItemRows: RuleItem[];
  savingRuleItems: boolean;
}>();

const emit = defineEmits<{
  "reload-rule-versions": [];
  "open-create-rule-version": [];
  "select-rule-version": [ruleVersionId: number];
  "add-rule-item-row": [];
  "save-rule-items": [];
  "remove-rule-item-row": [index: number];
}>();
</script>

<style scoped>
.quant-shell {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 16px;
}

.inner-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(116, 133, 151, 0.14);
  background: rgba(248, 252, 255, 0.92);
}

.inner-card h4 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #22384b;
}

@media (max-width: 1080px) {
  .quant-shell {
    grid-template-columns: 1fr;
  }
}
</style>
