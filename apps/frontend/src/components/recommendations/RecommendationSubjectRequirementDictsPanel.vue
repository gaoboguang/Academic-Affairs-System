<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>选科要求字典</h3>
        <p>核对院校专业选科文本如何标准化为必选、任选、不限等结构化科目要求。</p>
      </div>
      <div class="action-row">
        <el-button :loading="loading" @click="emit('load')">刷新</el-button>
        <el-button :loading="bootstrapping" :disabled="loading" @click="emit('bootstrap')">装载基线</el-button>
      </div>
    </div>

    <el-alert v-if="loadError" class="rule-panel-alert" type="error" show-icon :closable="false" title="选科字典加载失败">
      <template #default>
        <div class="rule-alert-body">
          <span>{{ loadError }}</span>
          <el-button link type="primary" :loading="loading" @click="emit('load')">重新加载选科字典</el-button>
        </div>
      </template>
    </el-alert>

    <div class="rule-summary-grid" v-loading="loading">
      <article class="rule-summary-card">
        <span>字典总数</span>
        <strong>{{ dicts.length }}</strong>
        <p>{{ yearCount }} 个年份，{{ examModeCount }} 种模式</p>
      </article>
      <article class="rule-summary-card">
        <span>匹配模式</span>
        <strong>{{ matchModeCount }}</strong>
        <p>用于把原始选科文本转为结构化要求</p>
      </article>
      <article class="rule-summary-card">
        <span>标准科目组合</span>
        <strong>{{ subjectSetCount }}</strong>
        <p>候选筛选和选科风险提示会消费这些结果</p>
      </article>
    </div>

    <div class="filter-grid">
      <el-select v-model="filters.year" clearable :disabled="loading" placeholder="年份">
        <el-option v-for="year in yearOptions" :key="year" :label="String(year)" :value="year" />
      </el-select>
      <el-select v-model="filters.province" clearable filterable :disabled="loading" placeholder="省份">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-select v-model="filters.exam_mode" clearable filterable :disabled="loading" placeholder="高考模式">
        <el-option v-for="item in examModeOptions" :key="item" :label="item || '通用模式'" :value="item" />
      </el-select>
      <el-input v-model="filters.requirement_code" clearable :disabled="loading" placeholder="要求代码" />
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" :loading="loading" @click="emit('load')">查询</el-button>
      <el-button :disabled="loading" @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="dicts" stripe v-loading="loading">
      <template #empty>
        <el-empty :description="dictEmptyDescription">
          <el-button v-if="loadError" type="primary" plain :loading="loading" @click="emit('load')">
            重新加载选科字典
          </el-button>
        </el-empty>
      </template>
      <el-table-column label="省份" prop="province" width="90" />
      <el-table-column label="年份" prop="year" width="90" />
      <el-table-column label="模式" min-width="130">
        <template #default="{ row }">
          {{ row.exam_mode || "通用" }}
        </template>
      </el-table-column>
      <el-table-column label="代码" prop="requirement_code" min-width="150" />
      <el-table-column label="原始说明" prop="requirement_text" min-width="240" />
      <el-table-column label="匹配模式" prop="match_mode" min-width="120" />
      <el-table-column label="标准科目" min-width="220">
        <template #default="{ row }">
          <div class="tag-cluster">
            <el-tag v-for="item in row.normalized_subjects_json" :key="item" size="small" effect="plain">{{ item }}</el-tag>
            <span v-if="!row.normalized_subjects_json.length" class="muted-copy">不限 / 未设</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="来源" prop="source_note" min-width="200" />
      <el-table-column label="备注" prop="note" min-width="180" />
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { SubjectRequirementDict, SubjectRequirementDictFiltersState } from "./types";

const props = defineProps<{
  dicts: SubjectRequirementDict[];
  filters: SubjectRequirementDictFiltersState;
  bootstrapping: boolean;
  loading: boolean;
  loadError: string;
  yearOptions: number[];
  provinceOptions: string[];
  examModeOptions: string[];
}>();

const emit = defineEmits<{
  load: [];
  bootstrap: [];
  reset: [];
}>();

const yearCount = computed(() => new Set(props.dicts.map((item) => item.year)).size);
const examModeCount = computed(() => new Set(props.dicts.map((item) => item.exam_mode || "通用")).size);
const matchModeCount = computed(() => new Set(props.dicts.map((item) => item.match_mode)).size);
const subjectSetCount = computed(() =>
  new Set(props.dicts.map((item) => item.normalized_subjects_json.join("+") || "不限")).size,
);
const hasActiveFilters = computed(() =>
  Boolean(props.filters.year || props.filters.province || props.filters.exam_mode || props.filters.requirement_code),
);
const dictEmptyDescription = computed(() => {
  if (props.loadError) return "选科要求字典加载失败，请重新加载。";
  if (props.loading) return "正在加载选科要求字典";
  if (hasActiveFilters.value) return "没有符合当前筛选条件的选科要求字典。";
  return "暂无选科要求字典，可以先装载基线。";
});
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.toolbar-row {
  margin-bottom: 16px;
}

.rule-panel-alert {
  margin-bottom: 16px;
}

.rule-alert-body {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
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
