<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>省份规则配置</h3>
        <p>按省份、年份和批次维护志愿数上限、单位类型与调剂规则，避免把志愿模式写死在页面里。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('load')">刷新</el-button>
        <el-button :loading="bootstrapping" @click="emit('bootstrap')">装载全国基线</el-button>
        <el-button type="primary" @click="emit('create')">新增规则</el-button>
      </div>
    </div>

    <div class="filter-grid">
      <el-select v-model="filters.year" clearable placeholder="年份">
        <el-option v-for="year in yearOptions" :key="year" :label="String(year)" :value="year" />
      </el-select>
      <el-select v-model="filters.province" clearable filterable placeholder="省份">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-select v-model="filters.exam_mode" clearable filterable placeholder="高考模式">
        <el-option v-for="item in examModeOptions" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="filters.candidate_type" clearable filterable placeholder="考生类别">
        <el-option label="通用 / 不区分类别" value="" />
        <el-option v-for="item in candidateTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" @click="emit('load')">查询</el-button>
      <el-button @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="rules" stripe>
      <el-table-column label="省份" prop="province" width="100" />
      <el-table-column label="年份" prop="year" width="90" />
      <el-table-column label="模式" prop="exam_mode" width="120" />
      <el-table-column label="类别" width="120">
        <template #default="{ row }">
          {{ formatCandidateType(row.candidate_type) }}
        </template>
      </el-table-column>
      <el-table-column label="批次" min-width="150">
        <template #default="{ row }">
          {{ row.batch_order ? `${row.batch_order}. ${row.batch}` : row.batch }}
        </template>
      </el-table-column>
      <el-table-column label="总分" prop="total_score" width="90" />
      <el-table-column label="志愿上限" prop="volunteer_limit" width="100" />
      <el-table-column label="单位类型" prop="volunteer_unit_type" width="120" />
      <el-table-column label="选科模式" min-width="150">
        <template #default="{ row }">
          {{ row.subject_requirement_mode || "未设" }}
        </template>
      </el-table-column>
      <el-table-column label="同单位专业上限" width="130">
        <template #default="{ row }">
          {{ row.max_major_per_unit ?? "未设" }}
        </template>
      </el-table-column>
      <el-table-column label="平行志愿" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_parallel ? 'success' : 'info'" effect="light">
            {{ row.is_parallel ? "是" : "否" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="服从调剂" width="100">
        <template #default="{ row }">
          <el-tag :type="row.allow_adjustment ? 'warning' : 'info'" effect="light">
            {{ row.allow_adjustment ? "允许" : "不允许" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="征集志愿" width="100">
        <template #default="{ row }">
          <el-tag :type="row.support_collect_round ? 'success' : 'info'" effect="light">
            {{ row.support_collect_round ? "支持" : "不支持" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="特殊规则" min-width="220">
        <template #default="{ row }">
          <div class="tag-cluster">
            <el-tag v-for="item in row.special_rules_json" :key="item" size="small" effect="plain">{{ item }}</el-tag>
            <span v-if="!row.special_rules_json.length" class="muted-copy">无</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="赋分摘要" prop="score_rule_summary" min-width="220" />
      <el-table-column label="备注" prop="note" min-width="180" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="emit('edit', row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!rules.length" description="暂无省份规则" />
  </section>
</template>

<script setup lang="ts">
import type { ProvinceVolunteerRule } from "./types";

interface ProvinceVolunteerRuleFiltersState {
  year?: number;
  province: string;
  exam_mode: string;
  candidate_type: string;
}

defineProps<{
  rules: ProvinceVolunteerRule[];
  filters: ProvinceVolunteerRuleFiltersState;
  bootstrapping: boolean;
  yearOptions: number[];
  provinceOptions: string[];
  examModeOptions: string[];
  candidateTypeOptions: Array<{ value: string; label: string }>;
}>();

const emit = defineEmits<{
  load: [];
  bootstrap: [];
  reset: [];
  create: [];
  edit: [value: ProvinceVolunteerRule];
}>();

function formatCandidateType(value: string): string {
  if (!value) return "通用";
  const labels: Record<string, string> = {
    general: "普通类",
    art: "艺体类",
    sports: "体育类",
    fine_art: "美术类",
    music: "音乐类",
    dance: "舞蹈类",
    media: "传媒类",
  };
  return labels[value] ?? value;
}
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.toolbar-row {
  margin-bottom: 16px;
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
</style>
