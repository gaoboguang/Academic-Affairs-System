<template>
  <section class="report-insight-section">
    <div class="section-head compact">
      <div>
        <h3>导出前摘要</h3>
        <p>{{ description }}</p>
      </div>
    </div>
    <div v-if="loading" class="report-insight-placeholder">正在加载当前报表的导出前摘要...</div>
    <div v-else-if="error" class="report-insight-error">
      <el-alert type="error" show-icon :closable="false" :title="error" />
      <div class="action-row toolbar-row">
        <el-button plain @click="$emit('retry')">重试摘要加载</el-button>
      </div>
    </div>
    <div v-else-if="loaded && !cards.length" class="report-insight-placeholder">
      当前报表在所选参数下暂无额外摘要提示，可直接导出或打印。
    </div>
    <div v-if="groups?.length" class="report-insight-group-list">
      <section v-for="group in groups" :key="group.key" class="report-insight-group">
        <div class="report-insight-group-head">
          <h4>{{ group.title }}</h4>
        </div>
        <div class="report-insight-grid">
          <article
            v-for="card in group.cards"
            :key="card.key"
            class="report-insight-card"
            :class="`tone-${card.tone}`"
          >
            <strong>{{ card.title }}</strong>
            <p class="report-insight-summary">{{ card.summary }}</p>
            <p class="report-insight-detail">{{ card.detail }}</p>
          </article>
        </div>
      </section>
    </div>
    <div v-else class="report-insight-grid">
      <article
        v-for="card in cards"
        :key="card.key"
        class="report-insight-card"
        :class="`tone-${card.tone}`"
      >
        <strong>{{ card.title }}</strong>
        <p class="report-insight-summary">{{ card.summary }}</p>
        <p class="report-insight-detail">{{ card.detail }}</p>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { ReportInsightCard, ReportInsightCardGroup } from "./reportInsights";

defineProps<{
  description: string;
  loading: boolean;
  error: string;
  loaded: boolean;
  cards: ReportInsightCard[];
  groups?: ReportInsightCardGroup[];
}>();

defineEmits<{
  retry: [];
}>();
</script>

<style scoped>
.report-insight-section {
  margin-top: 18px;
}

.report-insight-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.report-insight-group-list {
  display: grid;
  gap: 16px;
}

.report-insight-group-head h4 {
  margin: 0 0 10px;
  color: #1f3245;
  font-size: 15px;
}

.report-insight-placeholder {
  padding: 18px 16px;
  border-radius: 16px;
  border: 1px dashed rgba(126, 143, 158, 0.22);
  background: rgba(248, 251, 253, 0.92);
  color: #60748a;
  line-height: 1.6;
}

.report-insight-error {
  display: grid;
  gap: 12px;
  margin-bottom: 14px;
}

.toolbar-row {
  margin-top: 14px;
}

.report-insight-card {
  padding: 16px;
  border-radius: 16px;
  border: 1px solid rgba(126, 143, 158, 0.14);
  background: rgba(255, 255, 255, 0.9);
}

.report-insight-card.tone-warning {
  border-color: rgba(189, 123, 36, 0.2);
  background: rgba(255, 249, 240, 0.96);
}

.report-insight-card.tone-info {
  border-color: rgba(74, 111, 165, 0.2);
  background: rgba(245, 249, 255, 0.96);
}

.report-insight-card.tone-success {
  border-color: rgba(60, 138, 88, 0.18);
  background: rgba(244, 251, 246, 0.95);
}

.report-insight-card strong {
  display: block;
  color: #1f3245;
}

.report-insight-summary {
  margin: 8px 0 0;
  color: #34506a;
  font-weight: 600;
  line-height: 1.6;
}

.report-insight-detail {
  margin: 8px 0 0;
  color: #60748a;
  line-height: 1.6;
}

.section-head {
  margin-bottom: 16px;
}

.section-head h3 {
  margin: 0;
  font-size: 18px;
}

.section-head p {
  margin: 6px 0 0;
  color: #60748a;
  line-height: 1.6;
}
</style>
