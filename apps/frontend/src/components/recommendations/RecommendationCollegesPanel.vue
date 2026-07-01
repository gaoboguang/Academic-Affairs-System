<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>院校库</h3>
        <p>维护基础院校信息、层级标签、艺体招生标记和别名，为录取清洗与推荐筛选提供基底。</p>
      </div>
      <div class="action-row">
        <el-button :loading="loading" @click="emit('load')">刷新</el-button>
        <el-button type="primary" @click="emit('create')">新增院校</el-button>
      </div>
    </div>

    <el-alert v-if="loadError" class="catalog-panel-alert" type="error" show-icon :closable="false" title="院校库加载失败">
      <template #default>
        <div class="catalog-alert-body">
          <span>{{ loadError }}</span>
          <el-button link type="primary" :loading="loading" @click="emit('load')">重新加载院校库</el-button>
        </div>
      </template>
    </el-alert>

    <div class="filter-grid">
      <el-input v-model="filters.keyword" :disabled="loading" placeholder="按院校名称或别名筛选" />
      <el-select v-model="filters.province" clearable filterable :disabled="loading" placeholder="省份">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-select v-model="filters.supports_art" :disabled="loading" placeholder="艺体招生">
        <el-option label="全部" value="all" />
        <el-option label="支持艺体" value="true" />
        <el-option label="仅普通招生" value="false" />
      </el-select>
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" :loading="loading" @click="emit('load')">查询</el-button>
      <el-button :disabled="loading" @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="colleges" stripe v-loading="loading">
      <template #empty>
        <el-empty :description="collegeEmptyDescription">
          <el-button v-if="loadError" type="primary" plain :loading="loading" @click="emit('load')">
            重新加载院校库
          </el-button>
          <el-button v-else-if="!hasActiveFilters" type="primary" plain @click="emit('create')">新增院校</el-button>
        </el-empty>
      </template>
      <el-table-column label="院校" min-width="220">
        <template #default="{ row }">
          <div class="name-stack">
            <el-button link type="primary" class="name-link" @click="emit('open-detail', row.id)">{{ row.name }}</el-button>
            <span v-if="row.college_code">{{ row.college_code }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="地区" min-width="130">
        <template #default="{ row }">
          {{ [row.province, row.city].filter(Boolean).join(" / ") || "-" }}
        </template>
      </el-table-column>
      <el-table-column label="类型" prop="school_type" min-width="110" />
      <el-table-column label="层级标签" min-width="180">
        <template #default="{ row }">
          <div class="tag-cluster">
            <el-tag v-for="tag in row.school_level_tags_json ?? []" :key="tag" size="small">{{ tag }}</el-tag>
            <span v-if="!(row.school_level_tags_json ?? []).length" class="muted-copy">未标注</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="艺体" width="100">
        <template #default="{ row }">
          <el-tag :type="row.supports_art ? 'warning' : 'info'" effect="light">
            {{ row.supports_art ? "支持" : "否" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="别名" min-width="180">
        <template #default="{ row }">
          <div class="tag-cluster">
            <el-tag v-for="item in row.alias_names ?? []" :key="item" size="small" effect="plain">
              {{ item }}
            </el-tag>
            <span v-if="!(row.alias_names ?? []).length" class="muted-copy">无</span>
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
    <el-pagination
      v-if="pagination.total"
      class="table-pagination"
      background
      layout="total, sizes, prev, pager, next"
      :current-page="pagination.page"
      :page-size="pagination.page_size"
      :page-sizes="[50, 100, 200]"
      :total="pagination.total"
      @current-change="emit('page-change', $event)"
      @size-change="emit('page-size-change', $event)"
    />
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { CollegeItem, PaginationState } from "./types";

interface CollegeFiltersState {
  keyword: string;
  province: string;
  supports_art: "all" | "true" | "false";
}

const props = defineProps<{
  colleges: CollegeItem[];
  filters: CollegeFiltersState;
  pagination: PaginationState;
  provinceOptions: string[];
  loading: boolean;
  loadError: string;
}>();

const emit = defineEmits<{
  load: [];
  reset: [];
  "page-change": [value: number];
  "page-size-change": [value: number];
  create: [];
  edit: [value: CollegeItem];
  "open-detail": [collegeId: number];
}>();

const hasActiveFilters = computed(() =>
  Boolean(props.filters.keyword || props.filters.province || props.filters.supports_art !== "all"),
);
const collegeEmptyDescription = computed(() => {
  if (props.loadError) return "院校库加载失败，请重新加载。";
  if (props.loading) return "正在加载院校库";
  if (hasActiveFilters.value) return "没有符合当前筛选条件的院校。";
  return "暂无院校数据，可以先新增院校。";
});
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.toolbar-row {
  margin-bottom: 16px;
}

.catalog-panel-alert {
  margin-bottom: 16px;
}

.catalog-alert-body {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.table-pagination {
  margin-top: 16px;
  justify-content: flex-end;
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

.name-stack {
  display: grid;
  gap: 4px;
}

.name-stack .name-link {
  justify-content: flex-start;
  padding: 0;
  height: auto;
  font-weight: 650;
  color: #203449;
}

.name-stack span {
  color: #7b8d9c;
  font-size: 13px;
}
</style>
