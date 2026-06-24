<template>
  <div class="print-shell app-print-shell">
    <div class="print-toolbar app-print-toolbar">
      <div>
        <strong>{{ toolbarTitle || title }}</strong>
        <p>{{ toolbarDescription || "确认版式后可使用浏览器打印或导出 PDF。" }}</p>
      </div>
      <el-button type="primary" @click="printPage">打印</el-button>
    </div>

    <div v-if="loading" class="print-placeholder">{{ loadingText }}</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else class="print-page app-print-page">
      <header class="print-header">
        <div>
          <div v-if="eyebrow" class="print-eyebrow">{{ eyebrow }}</div>
          <h1>{{ title }}</h1>
          <p v-if="description">{{ description }}</p>
        </div>
        <div v-if="summaryCards?.length" class="print-summary-grid">
          <div
            v-for="card in summaryCards"
            :key="card.title"
            class="print-summary-item"
            :class="`tone-${card.tone ?? 'neutral'}`"
          >
            <span>{{ card.title }}</span>
            <strong>{{ card.value }}</strong>
            <p v-if="card.description">{{ card.description }}</p>
          </div>
        </div>
      </header>
      <slot />
    </article>
  </div>
</template>

<script setup lang="ts">
import type { PrintSummaryCard } from "./types";

withDefaults(
  defineProps<{
    title: string;
    eyebrow?: string;
    description?: string;
    toolbarTitle?: string;
    toolbarDescription?: string;
    loading?: boolean;
    loadingText?: string;
    errorMessage?: string;
    summaryCards?: PrintSummaryCard[];
  }>(),
  {
    loading: false,
    loadingText: "正在加载打印内容...",
  },
);

function printPage(): void {
  window.print();
}
</script>
