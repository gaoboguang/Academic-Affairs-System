<template>
  <div class="metric-card soft-card">
    <div class="metric-topline"></div>
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value">{{ value }}</div>
    <div class="metric-help">{{ helpText }}</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  value: string | number;
  helpText: string;
}>();
</script>

<style scoped>
.metric-card {
  position: relative;
  padding: 20px 22px 22px;
  overflow: hidden;
}

.metric-label {
  color: #678096;
  font-size: 13px;
  letter-spacing: 0.08em;
}

.metric-value {
  margin-top: 10px;
  font-size: 32px;
  font-weight: 760;
  color: #1d3147;
}

.metric-help {
  margin-top: 12px;
  color: #7f8f9e;
  font-size: 13px;
  line-height: 1.5;
}

.metric-topline {
  width: 60px;
  height: 6px;
  margin-bottom: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(31, 108, 152, 0.94), rgba(209, 141, 72, 0.88));
}
</style>
