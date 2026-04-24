<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>特殊类型规则字典</h3>
        <p>查看春考、综评、单招、艺术、体育等特殊类型的细分类别、匹配关键词、核对清单和初筛优先级。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('load')">刷新</el-button>
        <el-button :loading="bootstrapping" @click="emit('bootstrap')">装载山东基线</el-button>
      </div>
    </div>

    <div class="rule-summary-grid">
      <article class="rule-summary-card">
        <span>规则总数</span>
        <strong>{{ rules.length }}</strong>
        <p>{{ yearCount }} 个年份，{{ studentTypeCount }} 类考生</p>
      </article>
      <article class="rule-summary-card">
        <span>最高优先级加成</span>
        <strong>{{ maxPriorityBonus }}</strong>
        <p>仅表示初筛先核看顺序，不表示录取概率</p>
      </article>
      <article class="rule-summary-card">
        <span>待核类别</span>
        <strong>{{ fallbackRuleCount }}</strong>
        <p>未命中细分类别时继续要求人工复核</p>
      </article>
    </div>

    <div class="filter-grid">
      <el-select v-model="filters.year" clearable placeholder="年份">
        <el-option v-for="year in yearOptions" :key="year" :label="String(year)" :value="year" />
      </el-select>
      <el-select v-model="filters.province" clearable filterable placeholder="省份">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-select v-model="filters.student_type" clearable filterable placeholder="考生类型">
        <el-option v-for="item in studentTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" @click="emit('load')">查询</el-button>
      <el-button @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="rules" stripe>
      <el-table-column label="省份" prop="province" width="90" />
      <el-table-column label="年份" prop="year" width="90" />
      <el-table-column label="考生类型" width="130">
        <template #default="{ row }">
          {{ formatStudentType(row.student_type) }}
        </template>
      </el-table-column>
      <el-table-column label="类别" min-width="180">
        <template #default="{ row }">
          <strong>{{ row.category_label }}</strong>
          <div class="muted-copy">{{ row.category_code }}</div>
        </template>
      </el-table-column>
      <el-table-column label="关键词" min-width="240">
        <template #default="{ row }">
          <div class="tag-cluster">
            <el-tag v-for="item in row.match_keywords_json" :key="item" size="small" effect="plain">{{ item }}</el-tag>
            <span v-if="!row.match_keywords_json.length" class="muted-copy">无关键词</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="核对清单" min-width="300">
        <template #default="{ row }">
          <ul class="note-list">
            <li v-for="item in row.review_notes_json" :key="item">{{ item }}</li>
          </ul>
          <span v-if="!row.review_notes_json.length" class="muted-copy">无</span>
        </template>
      </el-table-column>
      <el-table-column label="优先级" width="110">
        <template #default="{ row }">
          <el-tag :type="row.priority_bonus > 0 ? 'warning' : 'info'" effect="light">
            {{ row.priority_bonus > 0 ? `+${row.priority_bonus}` : "0" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="优先级说明" min-width="240">
        <template #default="{ row }">
          <ul class="note-list">
            <li v-for="item in row.priority_notes_json" :key="item">{{ item }}</li>
          </ul>
          <span v-if="!row.priority_notes_json.length" class="muted-copy">无</span>
        </template>
      </el-table-column>
      <el-table-column label="来源" prop="source_note" min-width="180" />
      <el-table-column label="备注" prop="note" min-width="180" />
    </el-table>

    <el-empty v-if="!rules.length" description="暂无特殊类型规则" />
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { SpecialTypeRule, SpecialTypeRuleFiltersState } from "./types";

const props = defineProps<{
  rules: SpecialTypeRule[];
  filters: SpecialTypeRuleFiltersState;
  bootstrapping: boolean;
  yearOptions: number[];
  provinceOptions: string[];
  studentTypeOptions: Array<{ value: string; label: string }>;
}>();

const emit = defineEmits<{
  load: [];
  bootstrap: [];
  reset: [];
}>();

const yearCount = computed(() => new Set(props.rules.map((item) => item.year)).size);
const studentTypeCount = computed(() => new Set(props.rules.map((item) => item.student_type)).size);
const maxPriorityBonus = computed(() => Math.max(0, ...props.rules.map((item) => item.priority_bonus)));
const fallbackRuleCount = computed(() =>
  props.rules.filter((item) => item.category_code.includes("review") || item.category_code.includes("fallback")).length,
);

function formatStudentType(value: string): string {
  const found = props.studentTypeOptions.find((item) => item.value === value);
  return found?.label ?? value;
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

.tag-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.note-list {
  margin: 0;
  padding-left: 18px;
  color: #40566b;
  line-height: 1.55;
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
