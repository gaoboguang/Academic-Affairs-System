<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>就业方向库</h3>
        <p>先维护标准化就业方向对象，供学生职业意向采集、专业映射和推荐解释复用。</p>
      </div>
      <div class="action-row">
        <el-button :loading="loading" @click="emit('load')">刷新</el-button>
        <el-button type="primary" @click="emit('create')">新增方向</el-button>
      </div>
    </div>

    <el-alert v-if="loadError" class="career-panel-alert" type="error" show-icon :closable="false" title="就业方向加载失败">
      <template #default>
        <div class="career-alert-body">
          <span>{{ loadError }}</span>
          <el-button link type="primary" :loading="loading" @click="emit('load')">重新加载就业方向库</el-button>
        </div>
      </template>
    </el-alert>

    <div class="filter-grid">
      <el-input v-model="filters.keyword" :disabled="loading" placeholder="按方向名称筛选" />
      <el-select v-model="filters.category" clearable filterable :disabled="loading" placeholder="方向分类">
        <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
      </el-select>
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" :loading="loading" @click="emit('load')">查询</el-button>
      <el-button :disabled="loading" @click="emit('reset')">重置</el-button>
    </div>

    <section v-if="groupedSections.length && !loadError" v-loading="loading" class="direction-groups-panel">
      <div class="section-head compact">
        <div>
          <h3>分类视图</h3>
          <p>先按方向分类回看结构，再到底部明细列表维护单条方向。</p>
        </div>
        <div class="group-summary-chips">
          <span class="page-chip"><strong>方向</strong>{{ directions.length }}</span>
          <span class="page-chip"><strong>分类</strong>{{ groupedSections.length }}</span>
        </div>
      </div>

      <div class="direction-group-grid">
        <article v-for="section in groupedSections" :key="section.key" class="direction-group-card">
          <header class="direction-group-head">
            <div>
              <h4>{{ section.label }}</h4>
              <p>{{ section.count }} 个方向</p>
            </div>
          </header>

          <div class="direction-item-list">
            <article v-for="item in section.directions" :key="item.id" class="direction-item-card">
              <div class="direction-item-head">
                <div class="name-stack">
                  <strong>{{ item.name }}</strong>
                  <span v-if="item.alias_names_json?.length">别名：{{ item.alias_names_json.join(" / ") }}</span>
                </div>
                <el-button link type="primary" @click="emit('edit', item)">编辑</el-button>
              </div>

              <p v-if="item.description" class="direction-description">{{ item.description }}</p>

              <div class="direction-copy-stack">
                <span v-if="item.common_job_types_json?.length">岗位：{{ item.common_job_types_json.join(" / ") }}</span>
                <span v-if="item.common_industries_json?.length">行业：{{ item.common_industries_json.join(" / ") }}</span>
                <span v-if="!item.common_job_types_json?.length && !item.common_industries_json?.length" class="muted-copy">
                  暂无岗位或行业标签
                </span>
              </div>

              <div class="tag-row">
                <el-tag v-if="item.prefers_postgraduate" type="warning" effect="plain">偏深造</el-tag>
                <el-tag v-if="item.requires_certificate" type="danger" effect="plain">需资格证</el-tag>
                <el-tag v-if="item.requires_long_cycle" type="info" effect="plain">长培养路径</el-tag>
                <el-tag v-if="item.supports_art" type="success" effect="plain">适合艺体</el-tag>
                <span
                  v-if="!item.prefers_postgraduate && !item.requires_certificate && !item.requires_long_cycle && !item.supports_art"
                  class="muted-copy"
                >
                  暂无特殊路径提示
                </span>
              </div>
            </article>
          </div>
        </article>
      </div>
    </section>

    <div v-if="directions.length" class="detail-section-head">
      <div>
        <h3>明细列表</h3>
        <p>保留表格视图，便于核对常见岗位、路径标签和状态字段。</p>
      </div>
    </div>

    <el-table :data="directions" stripe v-loading="loading">
      <template #empty>
        <el-empty :description="directionEmptyDescription">
          <el-button v-if="loadError" type="primary" plain :loading="loading" @click="emit('load')">
            重新加载就业方向库
          </el-button>
          <el-button v-else-if="!hasActiveFilters" type="primary" plain @click="emit('create')">新增就业方向</el-button>
        </el-empty>
      </template>
      <el-table-column label="方向" min-width="220">
        <template #default="{ row }">
          <div class="name-stack">
            <strong>{{ row.name }}</strong>
            <span v-if="row.alias_names_json?.length">别名：{{ row.alias_names_json.join(" / ") }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="分类" prop="category" min-width="160" />
      <el-table-column label="常见岗位" min-width="200">
        <template #default="{ row }">
          {{ row.common_job_types_json?.join(" / ") || "-" }}
        </template>
      </el-table-column>
      <el-table-column label="路径提示" min-width="220">
        <template #default="{ row }">
          <div class="tag-row">
            <el-tag v-if="row.prefers_postgraduate" type="warning" effect="plain">偏深造</el-tag>
            <el-tag v-if="row.requires_certificate" type="danger" effect="plain">需资格证</el-tag>
            <el-tag v-if="row.requires_long_cycle" type="info" effect="plain">长培养路径</el-tag>
            <el-tag v-if="row.supports_art" type="success" effect="plain">适合艺体</el-tag>
            <span v-if="!row.prefers_postgraduate && !row.requires_certificate && !row.requires_long_cycle && !row.supports_art">
              -
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" effect="light">
            {{ row.is_active ? "启用" : "停用" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="emit('edit', row)">编辑</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { buildEmploymentDirectionCategorySections } from "./helpers";
import type { EmploymentDirectionItem } from "./types";

interface EmploymentDirectionFiltersState {
  keyword: string;
  category: string;
}

const props = defineProps<{
  directions: EmploymentDirectionItem[];
  filters: EmploymentDirectionFiltersState;
  categoryOptions: string[];
  loading: boolean;
  loadError: string;
}>();

const emit = defineEmits<{
  load: [];
  reset: [];
  create: [];
  edit: [value: EmploymentDirectionItem];
}>();

const groupedSections = computed(() => buildEmploymentDirectionCategorySections(props.directions));
const hasActiveFilters = computed(() => Boolean(props.filters.keyword || props.filters.category));
const directionEmptyDescription = computed(() => {
  if (props.loadError) return "就业方向加载失败，请重新加载。";
  if (props.loading) return "正在加载就业方向";
  if (hasActiveFilters.value) return "没有符合当前筛选条件的就业方向。";
  return "暂无就业方向数据，可以先新增方向。";
});
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.toolbar-row {
  margin-bottom: 16px;
}

.career-panel-alert {
  margin-bottom: 16px;
}

.career-alert-body {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.direction-groups-panel {
  display: grid;
  gap: 16px;
  margin-bottom: 20px;
}

.group-summary-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.direction-group-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.direction-group-card {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid rgba(98, 126, 164, 0.18);
  border-radius: 18px;
  background:
    linear-gradient(180deg, rgba(243, 247, 252, 0.92), rgba(255, 255, 255, 0.98)),
    rgba(255, 255, 255, 0.98);
}

.direction-group-head h4 {
  margin: 0;
  color: #203449;
  font-size: 16px;
}

.direction-group-head p {
  margin: 6px 0 0;
  color: #7b8d9c;
  font-size: 13px;
}

.direction-item-list {
  display: grid;
  gap: 12px;
}

.direction-item-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: inset 0 0 0 1px rgba(98, 126, 164, 0.14);
}

.direction-item-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
}

.direction-description {
  margin: 0;
  color: #5f7080;
  font-size: 13px;
  line-height: 1.6;
}

.direction-copy-stack {
  display: grid;
  gap: 4px;
  color: #5f7080;
  font-size: 13px;
}

.detail-section-head {
  margin-bottom: 12px;
}

.detail-section-head h3 {
  margin: 0;
  color: #203449;
  font-size: 16px;
}

.detail-section-head p {
  margin: 6px 0 0;
  color: #7b8d9c;
  font-size: 13px;
}

.name-stack {
  display: grid;
  gap: 4px;
}

.name-stack strong {
  color: #203449;
}

.name-stack span {
  color: #7b8d9c;
  font-size: 13px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
