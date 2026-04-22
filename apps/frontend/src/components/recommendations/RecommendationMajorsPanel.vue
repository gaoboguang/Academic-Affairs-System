<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>专业库</h3>
        <p>维护专业方向、门类、就业去向和艺体相关标记，供录取数据清洗和专业偏好筛选复用。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('load')">刷新</el-button>
        <el-button type="primary" @click="emit('create')">新增专业</el-button>
      </div>
    </div>

    <div class="filter-grid">
      <el-input v-model="filters.keyword" placeholder="按专业名称筛选" />
      <el-select v-model="filters.is_art_related" placeholder="艺体相关">
        <el-option label="全部" value="all" />
        <el-option label="艺体相关" value="true" />
        <el-option label="非艺体" value="false" />
      </el-select>
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" @click="emit('load')">查询</el-button>
      <el-button @click="emit('reset')">重置</el-button>
    </div>

    <el-table :data="majors" stripe>
      <el-table-column label="专业" min-width="220">
        <template #default="{ row }">
          <div class="name-stack">
            <strong>{{ row.name }}</strong>
            <span v-if="row.major_code">{{ row.major_code }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="门类" prop="category" min-width="140" />
      <el-table-column label="方向" prop="direction" min-width="160" />
      <el-table-column label="就业去向" prop="career_path" min-width="200" />
      <el-table-column label="艺体" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_art_related ? 'warning' : 'info'" effect="light">
            {{ row.is_art_related ? "相关" : "否" }}
          </el-tag>
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
    <el-empty v-if="!majors.length" description="暂无专业数据" />
  </section>
</template>

<script setup lang="ts">
import type { MajorItem } from "./types";

interface MajorFiltersState {
  keyword: string;
  is_art_related: "all" | "true" | "false";
}

defineProps<{
  majors: MajorItem[];
  filters: MajorFiltersState;
}>();

const emit = defineEmits<{
  load: [];
  reset: [];
  create: [];
  edit: [value: MajorItem];
}>();
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.toolbar-row {
  margin-bottom: 16px;
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
</style>
