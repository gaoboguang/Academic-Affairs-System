<template>
  <div class="print-risk-grid">
    <article
      v-for="card in cards"
      :key="card.key"
      class="print-risk-card"
      :class="`tone-${card.tone}`"
    >
      <strong>{{ card.title }}</strong>
      <p class="print-risk-summary">{{ card.summary }}</p>
      <p class="print-risk-detail">{{ card.detail }}</p>
    </article>
  </div>
</template>

<script setup lang="ts">
import type { ReportInsightCard } from "./reportInsights";

defineProps<{
  cards: ReportInsightCard[];
}>();
</script>

<style scoped>
.print-risk-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.print-risk-card {
  padding: 16px;
  border-radius: 16px;
  border: 1px solid rgba(126, 141, 158, 0.14);
  background: rgba(255, 255, 255, 0.9);
}

.print-risk-card.tone-warning {
  border-color: rgba(189, 123, 36, 0.2);
  background: rgba(255, 249, 240, 0.96);
}

.print-risk-card.tone-info {
  border-color: rgba(74, 111, 165, 0.2);
  background: rgba(245, 249, 255, 0.96);
}

.print-risk-card.tone-success {
  border-color: rgba(60, 138, 88, 0.18);
  background: rgba(244, 251, 246, 0.95);
}

.print-risk-card strong {
  display: block;
  color: #1f3245;
}

.print-risk-summary {
  margin: 8px 0 0;
  color: #34506a;
  font-weight: 600;
  line-height: 1.6;
}

.print-risk-detail {
  margin: 8px 0 0;
  color: #60748a;
  line-height: 1.6;
}
</style>
