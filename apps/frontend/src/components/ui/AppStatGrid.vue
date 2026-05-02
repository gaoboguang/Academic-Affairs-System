<template>
  <el-row class="app-stat-grid" :gutter="16">
    <el-col
      v-for="item in items"
      :key="item.label"
      :xs="24"
      :sm="12"
      :md="columnSpan"
      :lg="columnSpan"
    >
      <AppStatCard v-bind="item" />
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { computed } from "vue";

import AppStatCard from "./AppStatCard.vue";
import type { StatCardItem } from "./types";

const props = withDefaults(
  defineProps<{
    items: StatCardItem[];
    columns?: 2 | 3 | 4 | 5 | 6;
  }>(),
  {
    columns: 4,
  },
);

const columnSpan = computed(() => Math.max(4, Math.floor(24 / props.columns)));
</script>
