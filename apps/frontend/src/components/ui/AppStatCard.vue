<template>
  <el-card class="app-stat-card stat-card" :class="`tone-${tone ?? 'neutral'}`" shadow="never">
    <div class="app-stat-label">{{ label }}</div>
    <div class="app-stat-value">
      <span v-if="loading">...</span>
      <strong v-else>{{ value }}</strong>
      <em v-if="suffix">{{ suffix }}</em>
    </div>
    <p v-if="help" class="app-stat-help">{{ help }}</p>
  </el-card>
</template>

<script setup lang="ts">
import type { UiTone } from "./types";

withDefaults(
  defineProps<{
    label: string;
    value: string | number;
    help?: string;
    suffix?: string;
    tone?: UiTone;
    loading?: boolean;
  }>(),
  {
    tone: "neutral",
    loading: false,
  },
);
</script>
