<template>
  <div class="page-shell">
    <section class="overview-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">工作量闭环</div>
        <h3>{{ currentSemesterLabel }}</h3>
        <p>先导入课表并修正未匹配项，再确认规则版本和附加项，最后统一计算并导出工作量结果。</p>
      </article>
      <article v-for="item in overviewCards" :key="item.label" class="soft-card overview-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head compact">
        <div>
          <h3>计算上下文</h3>
          <p>工作量结果由学期、规则版本和课表批次共同决定，切换其中任一项后都建议重新确认结果。</p>
        </div>
      </div>
      <div class="process-grid">
        <article v-for="item in processCards" :key="item.label" class="process-card" :class="item.tone">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.help }}</p>
        </article>
      </div>
      <div class="filter-grid">
        <el-select v-model="semesterModel" filterable placeholder="选择学期">
          <el-option
            v-for="semester in semesterOptions"
            :key="semester.id"
            :label="formatSemesterLabel(semester)"
            :value="semester.id"
          />
        </el-select>
        <el-select v-model="ruleVersionModel" filterable placeholder="选择规则版本">
          <el-option
            v-for="rule in ruleVersions"
            :key="rule.id"
            :label="ruleLabel(rule)"
            :value="rule.id"
          />
        </el-select>
        <el-select v-model="batchModel" filterable clearable placeholder="选择课表批次">
          <el-option
            v-for="batch in timetableBatches"
            :key="batch.id"
            :label="batchLabel(batch)"
            :value="batch.id"
          />
        </el-select>
      </div>
      <div v-if="precheckMessages.length" class="precheck-list">
        <el-alert
          v-for="item in precheckMessages"
          :key="item"
          type="warning"
          show-icon
          :closable="false"
          :title="item"
        />
      </div>
      <div class="action-row toolbar-row">
        <el-button type="primary" :loading="calculating" @click="emit('calculate')">
          计算工作量
        </el-button>
        <el-button :disabled="!resultCount" @click="emit('export-results')">
          导出工作量
        </el-button>
      </div>
    </section>

    <section class="metric-grid">
      <div class="soft-card stat-card">
        <div class="metric-label">当前批次未匹配</div>
        <div class="metric-value">{{ currentBatch?.unresolved_count ?? 0 }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">结果教师数</div>
        <div class="metric-value">{{ resultCount }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">学期总工作量</div>
        <div class="metric-value">{{ totalWorkload }}</div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { OptionItem } from "../../stores/reference";
import { batchLabel, formatSemesterLabel, ruleLabel } from "./helpers";
import type { RuleVersionItem, StatusCard, TimetableBatchItem } from "./types";

const props = defineProps<{
  selectedSemesterId: number | null;
  selectedRuleVersionId: number | null;
  selectedBatchId: number | null;
  semesterOptions: OptionItem[];
  ruleVersions: RuleVersionItem[];
  timetableBatches: TimetableBatchItem[];
  currentSemesterLabel: string;
  currentBatch: TimetableBatchItem | null;
  overviewCards: StatusCard[];
  processCards: StatusCard[];
  precheckMessages: string[];
  resultCount: number;
  totalWorkload: string;
  calculating: boolean;
}>();

const emit = defineEmits<{
  "update:selectedSemesterId": [value: number | null];
  "update:selectedRuleVersionId": [value: number | null];
  "update:selectedBatchId": [value: number | null];
  calculate: [];
  "export-results": [];
}>();

const semesterModel = computed<number | undefined>({
  get: () => props.selectedSemesterId ?? undefined,
  set: (value) => emit("update:selectedSemesterId", value ?? null),
});

const ruleVersionModel = computed<number | undefined>({
  get: () => props.selectedRuleVersionId ?? undefined,
  set: (value) => emit("update:selectedRuleVersionId", value ?? null),
});

const batchModel = computed<number | undefined>({
  get: () => props.selectedBatchId ?? undefined,
  set: (value) => emit("update:selectedBatchId", value ?? null),
});
</script>

<style scoped>
.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) repeat(3, minmax(0, 0.75fr));
  gap: 16px;
}

.overview-panel,
.overview-card {
  padding: 24px;
}

.overview-panel {
  background:
    radial-gradient(circle at top left, rgba(180, 219, 243, 0.32), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(244, 248, 252, 0.94));
}

.overview-kicker {
  display: inline-flex;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f6c98;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.overview-panel h3 {
  margin: 14px 0 0;
  color: #1f3448;
  font-size: 28px;
  line-height: 1.25;
}

.overview-panel p {
  margin: 12px 0 0;
  color: #62788c;
  line-height: 1.7;
}

.overview-card {
  display: grid;
  align-content: end;
  gap: 10px;
}

.overview-card span {
  color: #6d8194;
  font-size: 13px;
}

.overview-card strong {
  color: #1f3245;
  font-size: 30px;
  font-weight: 760;
}

.overview-card p {
  margin: 0;
  color: #73879b;
  line-height: 1.55;
  font-size: 13px;
}

.process-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.process-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(248, 251, 254, 0.94);
  border: 1px solid rgba(123, 142, 161, 0.12);
}

.process-card span {
  color: #6d8194;
  font-size: 13px;
}

.process-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3245;
  font-size: 20px;
  font-weight: 760;
  line-height: 1.35;
}

.process-card p {
  margin: 8px 0 0;
  color: #73879b;
  line-height: 1.55;
  font-size: 13px;
}

.stat-card {
  padding: 18px 20px;
}

.metric-label {
  color: #60748a;
  font-size: 13px;
}

.metric-value {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 700;
  color: #244560;
}

.tone-blue {
  box-shadow: inset 0 4px 0 rgba(31, 108, 152, 0.78);
}

.tone-amber {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.84);
}

.tone-slate {
  box-shadow: inset 0 4px 0 rgba(92, 111, 129, 0.74);
}

.tone-green {
  box-shadow: inset 0 4px 0 rgba(66, 145, 102, 0.76);
}

.toolbar-row {
  margin-top: 14px;
}

.precheck-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

@media (max-width: 1180px) {
  .overview-grid,
  .process-grid {
    grid-template-columns: 1fr;
  }
}
</style>
