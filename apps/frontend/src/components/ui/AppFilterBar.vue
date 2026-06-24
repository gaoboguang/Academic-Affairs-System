<template>
  <section class="app-filter-bar panel-block" :class="{ 'is-sticky': sticky }">
    <div v-if="title || description" class="app-filter-copy">
      <h2 v-if="title">{{ title }}</h2>
      <p v-if="description">{{ description }}</p>
    </div>
    <div class="app-filter-content">
      <slot />
    </div>
    <div v-if="actions?.length || $slots.actions" class="app-filter-actions">
      <slot name="actions">
        <el-button
          v-for="action in actions"
          :key="action.label"
          :type="action.type"
          :plain="action.plain"
          :disabled="action.disabled"
          :loading="action.loading"
          @click="action.handler"
        >
          {{ action.label }}
        </el-button>
      </slot>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { FilterAction } from "./types";

withDefaults(
  defineProps<{
    title?: string;
    description?: string;
    sticky?: boolean;
    actions?: FilterAction[];
  }>(),
  {
    sticky: true,
  },
);
</script>
