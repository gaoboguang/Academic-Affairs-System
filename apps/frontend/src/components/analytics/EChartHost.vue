<template>
  <div ref="containerRef" class="echart-host" :style="{ height }"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { EChartsOption } from "echarts";

const props = defineProps<{
  option: EChartsOption;
  height?: string;
}>();

const containerRef = ref<HTMLDivElement | null>(null);
let instance: import("echarts").ECharts | null = null;
let resizeObserver: ResizeObserver | null = null;

async function ensureInstance(): Promise<void> {
  if (!containerRef.value) return;
  if (instance) return;
  const echarts = await import("echarts");
  instance = echarts.init(containerRef.value);
  resizeObserver = new ResizeObserver(() => {
    instance?.resize();
  });
  resizeObserver.observe(containerRef.value);
}

async function applyOption(): Promise<void> {
  await ensureInstance();
  if (!instance) return;
  instance.setOption(props.option, { notMerge: true });
}

onMounted(applyOption);
watch(() => props.option, applyOption, { deep: true });

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  instance?.dispose();
  instance = null;
});
</script>

<style scoped>
.echart-host {
  width: 100%;
  height: 260px;
}
</style>
