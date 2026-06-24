<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>专业就业映射</h3>
        <p>把专业和标准化就业方向做成可维护映射，为工作台职业意向和推荐排序增强做底座。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('load')">刷新</el-button>
        <el-button type="primary" @click="emit('create')">新增映射</el-button>
      </div>
    </div>

    <div class="filter-grid">
      <el-input v-model="filters.keyword" placeholder="按专业或就业方向筛选" />
      <el-select v-model="filters.major_id" clearable filterable placeholder="专业">
        <el-option v-for="item in majorOptions" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="filters.direction_id" clearable filterable placeholder="就业方向">
        <el-option v-for="item in directionOptions" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="filters.strength" clearable placeholder="映射强度">
        <el-option v-for="item in strengthOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" @click="emit('load')">查询</el-button>
      <el-button @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="mappings" stripe>
      <el-table-column label="专业" min-width="180" prop="major_name" />
      <el-table-column label="就业方向" min-width="220">
        <template #default="{ row }">
          <div class="name-stack">
            <strong>{{ row.direction_name }}</strong>
            <span v-if="row.direction_category">{{ row.direction_category }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="强度" width="120">
        <template #default="{ row }">
          <el-tag :type="strengthTagType(row.strength)" effect="plain">{{ strengthLabel(row.strength) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="路径要求" min-width="220">
        <template #default="{ row }">
          <div class="tag-row">
            <el-tag v-if="row.requires_postgraduate" type="warning" effect="plain">需读研增强</el-tag>
            <el-tag v-if="row.requires_certificate" type="danger" effect="plain">需资格证</el-tag>
            <el-tag v-if="row.supports_art" type="success" effect="plain">适合艺体</el-tag>
            <el-tag v-for="item in row.supported_student_types_json || []" :key="`${row.id}-${item}`" effect="plain">
              {{ studentTypeLabel(item) }}
            </el-tag>
            <span
              v-if="!row.requires_postgraduate && !row.requires_certificate && !row.supports_art && !(row.supported_student_types_json || []).length"
            >
              -
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="说明" min-width="220">
        <template #default="{ row }">
          {{ row.recommendation_note || row.note || "-" }}
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
    <el-empty v-if="!mappings.length" description="暂无专业就业映射" />
  </section>
</template>

<script setup lang="ts">
import { recommendationStudentTypeOptions } from "./helpers";

import type { EmploymentDirectionItem, MajorEmploymentMappingItem, MajorItem, PaginationState } from "./types";

interface MajorEmploymentMappingFiltersState {
  keyword: string;
  major_id?: number;
  direction_id?: number;
  strength: string;
}

defineProps<{
  mappings: MajorEmploymentMappingItem[];
  filters: MajorEmploymentMappingFiltersState;
  pagination: PaginationState;
  majorOptions: MajorItem[];
  directionOptions: EmploymentDirectionItem[];
  strengthOptions: Array<{ value: string; label: string }>;
}>();

const emit = defineEmits<{
  load: [];
  reset: [];
  "page-change": [value: number];
  "page-size-change": [value: number];
  create: [];
  edit: [value: MajorEmploymentMappingItem];
}>();

function strengthLabel(value: string): string {
  return {
    core: "核心相关",
    high: "强相关",
    medium: "一般相关",
    transferable: "可转化",
  }[value] ?? value;
}

function strengthTagType(value: string): "success" | "warning" | "info" {
  const typeMap = {
    core: "success",
    high: "warning",
    medium: "info",
    transferable: "info",
  } as const;
  return typeMap[value as keyof typeof typeMap] ?? "info";
}

function studentTypeLabel(value: string): string {
  return recommendationStudentTypeOptions.find((item) => item.value === value)?.label ?? value;
}
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.toolbar-row {
  margin-bottom: 16px;
}

.table-pagination {
  margin-top: 16px;
  justify-content: flex-end;
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
