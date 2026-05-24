<template>
  <div class="app-page page-shell">
    <h1 v-if="hideHeader" class="app-page-sr-title">{{ title }}</h1>
    <header v-else class="app-page-header page-header">
      <div class="app-page-header-main">
        <div v-if="eyebrow" class="page-eyebrow">{{ eyebrow }}</div>
        <h1 class="page-title">{{ title }}</h1>
        <p v-if="description" class="page-subtitle">{{ description }}</p>
        <div v-if="meta?.length" class="page-chip-row">
          <span v-for="item in meta" :key="item.label" class="page-chip">
            <component v-if="item.icon" :is="item.icon" class="app-page-meta-icon" />
            <strong>{{ item.label }}</strong>{{ item.value }}
          </span>
        </div>
      </div>
      <div v-if="$slots.actions" class="action-row app-page-actions">
        <slot name="actions" />
      </div>
    </header>
    <slot />
  </div>
</template>

<script setup lang="ts">
import type { PageMetaItem } from "./types";

defineProps<{
  title: string;
  eyebrow?: string;
  description?: string;
  meta?: PageMetaItem[];
  hideHeader?: boolean;
}>();
</script>

<style scoped>
.app-page-header-main {
  min-width: 0;
}

.app-page-actions {
  justify-content: flex-end;
}

.app-page-meta-icon {
  width: 14px;
  height: 14px;
  color: var(--accent-primary);
}

.app-page-sr-title {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
