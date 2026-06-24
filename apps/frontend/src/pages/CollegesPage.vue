<template>
  <AppPage
    title="院校库"
    eyebrow="升学数据 / 院校浏览"
    description="直接查看本地已收录的院校记录，核对基础信息、画像状态和招生数据覆盖情况。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button @click="loadCatalog()">刷新</el-button>
      <el-button type="primary" @click="router.push('/recommendations')">志愿工作台</el-button>
    </template>

    <AppFilterBar title="筛选院校" description="按名称、代码、地区、类型、层级和数据覆盖情况快速定位院校。">
      <div class="catalog-filter-grid">
        <el-input
          v-model="filters.keyword"
          clearable
          placeholder="院校名称或代码"
          @keyup.enter="loadCatalog({ resetPage: true })"
        />
        <el-select v-model="filters.province" clearable filterable allow-create placeholder="省份">
          <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
        </el-select>
        <el-select v-model="filters.school_type" clearable filterable allow-create placeholder="院校类型">
          <el-option v-for="type in schoolTypeOptions" :key="type" :label="type" :value="type" />
        </el-select>
        <el-select v-model="filters.level_tag" clearable filterable allow-create placeholder="层级标签">
          <el-option v-for="tag in levelTagOptions" :key="tag" :label="tag" :value="tag" />
        </el-select>
        <el-select v-model="filters.has_profile" placeholder="画像状态">
          <el-option label="全部画像状态" value="all" />
          <el-option label="已有画像" value="true" />
          <el-option label="暂无画像" value="false" />
        </el-select>
        <el-select v-model="filters.has_admission_data" placeholder="招生数据">
          <el-option label="全部招生数据" value="all" />
          <el-option label="已有计划或录取" value="true" />
          <el-option label="暂无计划和录取" value="false" />
        </el-select>
      </div>
      <template #actions>
        <el-button type="primary" @click="loadCatalog({ resetPage: true })">查询</el-button>
        <el-button @click="resetFilters()">重置</el-button>
      </template>
    </AppFilterBar>

    <AppTableShell title="院校列表" description="列表只读展示；院校维护仍在高考志愿工作台的数据与规则中心完成。">
      <el-table v-loading="loading" :data="colleges" stripe>
        <el-table-column label="院校" min-width="230">
          <template #default="{ row }">
            <div class="name-stack">
              <el-button link type="primary" class="name-link" @click="openDetail(row.id)">{{ row.name }}</el-button>
              <span>{{ row.college_code || "未维护代码" }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="地区" min-width="140">
          <template #default="{ row }">
            {{ [row.province, row.city].filter(Boolean).join(" / ") || "-" }}
          </template>
        </el-table-column>
        <el-table-column label="类型" prop="school_type" min-width="110" />
        <el-table-column label="层级" min-width="170">
          <template #default="{ row }">
            <div class="tag-cluster">
              <el-tag v-for="tag in row.school_level_tags_json ?? []" :key="tag" size="small">{{ tag }}</el-tag>
              <span v-if="!(row.school_level_tags_json ?? []).length" class="muted-copy">未标注</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="画像" width="100">
          <template #default="{ row }">
            <el-tag :type="row.has_profile ? 'success' : 'info'" effect="light">
              {{ row.has_profile ? "已有" : "暂无" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="计划" width="120">
          <template #default="{ row }">
            <div class="metric-stack">
              <strong>{{ row.plan_count }}</strong>
              <span>{{ row.latest_plan_year ? `${row.latest_plan_year} 最新` : "暂无年份" }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="录取/投档" width="130">
          <template #default="{ row }">
            <div class="metric-stack">
              <strong>{{ row.admission_count }}</strong>
              <span>{{ row.latest_admission_year ? `${row.latest_admission_year} 最新` : "暂无年份" }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="艺体" width="90">
          <template #default="{ row }">
            <el-tag :type="row.supports_art ? 'warning' : 'info'" effect="light">
              {{ row.supports_art ? "支持" : "否" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row.id)">详情</el-button>
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
        @current-change="handlePageChange"
        @size-change="handlePageSizeChange"
      />
      <el-empty v-if="!loading && !colleges.length" description="暂无符合条件的院校" />
    </AppTableShell>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";

import { useCollegeCatalogBrowser } from "../components/colleges/useCollegeCatalogBrowser";
import AppFilterBar from "../components/ui/AppFilterBar.vue";
import AppPage from "../components/ui/AppPage.vue";
import AppTableShell from "../components/ui/AppTableShell.vue";

const router = useRouter();
const {
  colleges,
  filters,
  handlePageChange,
  handlePageSizeChange,
  levelTagOptions,
  loadCatalog,
  loading,
  openDetail,
  pagination,
  provinceOptions,
  resetFilters,
  schoolTypeOptions,
} = useCollegeCatalogBrowser();

const withProfileCount = computed(() => colleges.value.filter((item) => item.has_profile).length);
const withAdmissionDataCount = computed(() => colleges.value.filter((item) => item.plan_count || item.admission_count).length);
const pageMeta = computed(() => [
  { label: "本页院校", value: colleges.value.length ? `${colleges.value.length} 所` : "暂无" },
  { label: "总数", value: pagination.total ? `${pagination.total} 所` : "暂无" },
  { label: "本页有画像", value: `${withProfileCount.value} 所` },
  { label: "本页有招生数据", value: `${withAdmissionDataCount.value} 所` },
]);

onMounted(() => {
  void loadCatalog();
});
</script>

<style scoped>
.catalog-filter-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.name-stack,
.metric-stack {
  display: grid;
  gap: 4px;
}

.name-link {
  justify-content: flex-start;
  padding: 0;
  height: auto;
  font-weight: 650;
}

.name-stack span,
.metric-stack span,
.muted-copy {
  color: #7d8f9d;
  font-size: 13px;
}

.metric-stack strong {
  color: #203449;
}

.tag-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.table-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

@media (max-width: 960px) {
  .catalog-filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
