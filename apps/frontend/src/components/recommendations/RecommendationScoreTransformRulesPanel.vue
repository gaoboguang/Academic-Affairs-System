<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>赋分/成绩转换规则</h3>
        <p>核对不同省份、年份和高考模式下的赋分科目、等级表、折算公式和来源说明。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('load')">刷新</el-button>
        <el-button :loading="bootstrapping" @click="emit('bootstrap')">装载基线</el-button>
      </div>
    </div>

    <div class="rule-summary-grid">
      <article class="rule-summary-card">
        <span>规则总数</span>
        <strong>{{ rules.length }}</strong>
        <p>{{ yearCount }} 个年份，{{ subjectCount }} 个科目</p>
      </article>
      <article class="rule-summary-card">
        <span>成绩模式</span>
        <strong>{{ scoreModeCount }}</strong>
        <p>用于解释原始分、等级赋分或固定总分口径</p>
      </article>
      <article class="rule-summary-card">
        <span>带等级表</span>
        <strong>{{ gradeTableRuleCount }}</strong>
        <p>这类规则可继续核对等级区间和赋分区间</p>
      </article>
    </div>

    <div class="filter-grid">
      <el-select v-model="filters.year" clearable placeholder="年份">
        <el-option v-for="year in yearOptions" :key="year" :label="String(year)" :value="year" />
      </el-select>
      <el-select v-model="filters.province" clearable filterable placeholder="省份">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-select v-model="filters.exam_mode" clearable filterable placeholder="高考模式">
        <el-option v-for="item in examModeOptions" :key="item" :label="item || '通用模式'" :value="item" />
      </el-select>
      <el-input v-model="filters.subject_name" clearable placeholder="科目" />
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" @click="emit('load')">查询</el-button>
      <el-button @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="rules" stripe>
      <el-table-column label="省份" prop="province" width="90" />
      <el-table-column label="年份" prop="year" width="90" />
      <el-table-column label="模式" min-width="130">
        <template #default="{ row }">
          {{ row.exam_mode || "通用" }}
        </template>
      </el-table-column>
      <el-table-column label="科目" min-width="150">
        <template #default="{ row }">
          <strong>{{ row.subject_name }}</strong>
          <div v-if="row.subject_code" class="muted-copy">{{ row.subject_code }}</div>
        </template>
      </el-table-column>
      <el-table-column label="成绩模式" prop="score_mode" min-width="130" />
      <el-table-column label="等级表" min-width="260">
        <template #default="{ row }">
          <div v-if="row.grade_table_json.length" class="rule-readable-list">
            <span v-for="item in formatRuleObjectList(row.grade_table_json)" :key="item">{{ item }}</span>
          </div>
          <span v-else class="muted-copy">无</span>
        </template>
      </el-table-column>
      <el-table-column label="公式" min-width="220">
        <template #default="{ row }">
          <div v-if="Object.keys(row.formula_json).length" class="rule-readable-list">
            <span v-for="item in formatRuleObject(row.formula_json)" :key="item">{{ item }}</span>
          </div>
          <span v-else class="muted-copy">无</span>
        </template>
      </el-table-column>
      <el-table-column label="来源" prop="source_note" min-width="200" />
      <el-table-column label="备注" prop="note" min-width="180" />
    </el-table>

    <el-empty v-if="!rules.length" description="暂无赋分/成绩转换规则" />
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ProvinceScoreTransformRule, ProvinceScoreTransformRuleFiltersState } from "./types";

const props = defineProps<{
  rules: ProvinceScoreTransformRule[];
  filters: ProvinceScoreTransformRuleFiltersState;
  bootstrapping: boolean;
  yearOptions: number[];
  provinceOptions: string[];
  examModeOptions: string[];
}>();

const emit = defineEmits<{
  load: [];
  bootstrap: [];
  reset: [];
}>();

const yearCount = computed(() => new Set(props.rules.map((item) => item.year)).size);
const subjectCount = computed(() => new Set(props.rules.map((item) => item.subject_name)).size);
const scoreModeCount = computed(() => new Set(props.rules.map((item) => item.score_mode)).size);
const gradeTableRuleCount = computed(() => props.rules.filter((item) => item.grade_table_json.length).length);

const ruleFieldLabels: Record<string, string> = {
  grade: "等级",
  level: "等级",
  min: "下限",
  max: "上限",
  score: "分值",
  assigned_score: "赋分",
  raw_min: "原始分下限",
  raw_max: "原始分上限",
  converted_min: "转换分下限",
  converted_max: "转换分上限",
  formula: "公式",
  method: "方法",
  description: "说明",
};

function formatRuleObjectList(value: Array<Record<string, unknown>>): string[] {
  return value.slice(0, 4).map((item) => formatRuleObject(item).join("，"));
}

function formatRuleObject(value: Record<string, unknown>): string[] {
  return Object.entries(value).map(([key, item]) => `${ruleFieldLabels[key] ?? key}：${formatRuleValue(item)}`);
}

function formatRuleValue(value: unknown): string {
  if (Array.isArray(value)) return value.join("、");
  if (value && typeof value === "object") {
    return formatRuleObject(value as Record<string, unknown>).join("，");
  }
  return value === null || value === undefined || value === "" ? "未填写" : String(value);
}
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.toolbar-row {
  margin-bottom: 16px;
}

.rule-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.rule-summary-card {
  padding: 16px;
  border-radius: 8px;
  border: 1px solid rgba(121, 138, 154, 0.14);
  background: rgba(248, 251, 254, 0.9);
}

.rule-summary-card span {
  color: #6d8194;
  font-size: 13px;
}

.rule-summary-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3245;
  font-size: 24px;
}

.rule-summary-card p {
  margin: 6px 0 0;
  color: #73879b;
  font-size: 13px;
  line-height: 1.5;
}

.rule-readable-list {
  display: grid;
  gap: 4px;
  color: #40566b;
  font-size: 13px;
  line-height: 1.5;
}

.muted-copy {
  color: #7d8f9d;
  font-size: 13px;
}

@media (max-width: 960px) {
  .rule-summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
