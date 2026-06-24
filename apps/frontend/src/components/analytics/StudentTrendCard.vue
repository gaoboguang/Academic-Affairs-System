<template>
  <article class="soft-card inner-panel trend-card">
    <header class="card-head">
      <h4>趋势与稳定性</h4>
      <div class="badges">
        <el-tag :type="shapeTagType" effect="dark" size="small">{{ trendShape.label }}</el-tag>
        <el-tag :type="stabilityTagType" effect="plain" size="small">{{ stabilityLabel }}</el-tag>
      </div>
    </header>
    <p class="card-summary">{{ trendShape.summary || "尚未收集到足够趋势数据。" }}</p>
    <p class="card-summary muted" v-if="stability.summary">{{ stability.summary }}</p>
    <EChartHost v-if="hasPoints" :option="chartOption" height="240px" />
    <p v-else class="hint">至少累计 3 次考试后才能形成完整趋势曲线。</p>
    <section v-if="subjectShapes.length" class="subject-spark-grid">
      <div v-for="entry in subjectShapes" :key="entry.subject_id" class="subject-spark-cell">
        <div class="spark-head">
          <strong>{{ entry.subject_name }}</strong>
          <span :class="['spark-tag', shapeColorClass(entry.label)]">{{ entry.label }}</span>
        </div>
        <EChartHost
          :option="sparklineOption(entry.sparkline)"
          height="56px"
          v-if="(entry.sparkline ?? []).filter((value) => value != null).length >= 2"
        />
        <p v-else class="hint small">样本不足</p>
      </div>
    </section>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

import EChartHost from "./EChartHost.vue";
import { buildSparklineOption, buildTotalTrendOption, type TrendPoint } from "./chartOptions";

interface TrendPointInput {
  exam_name: string;
  total_score?: number | null;
  grade_rank?: number | null;
}

interface SubjectShape {
  subject_id: number;
  subject_name: string;
  label: string;
  sparkline: Array<number | null>;
}

interface Props {
  trendShape: { label: string; slope?: number | null; summary?: string };
  stability: { level: string; rank_stddev?: number | null; score_cv?: number | null; sample_count?: number; summary?: string };
  trendPoints: TrendPointInput[];
  subjectShapes: SubjectShape[];
}

const props = defineProps<Props>();

const stabilityLabelMap: Record<string, string> = {
  high: "稳定性高",
  medium: "稳定性中等",
  low: "稳定性偏弱",
  unknown: "稳定性未知",
};

const stabilityLabel = computed(() => stabilityLabelMap[props.stability.level] ?? "稳定性未知");

const shapeTagType = computed(() => {
  switch (props.trendShape.label) {
    case "稳步上升":
      return "success";
    case "下滑":
      return "danger";
    case "剧烈波动":
      return "warning";
    case "U型反弹":
      return "primary";
    case "稳定":
      return "info";
    default:
      return "info";
  }
});

const stabilityTagType = computed(() => {
  switch (props.stability.level) {
    case "high":
      return "success";
    case "medium":
      return "warning";
    case "low":
      return "danger";
    default:
      return "info";
  }
});

const hasPoints = computed(
  () => props.trendPoints.filter((point) => point.total_score != null || point.grade_rank != null).length >= 3,
);

const chartPoints = computed<TrendPoint[]>(() =>
  props.trendPoints.map((point) => ({
    label: point.exam_name,
    score: point.total_score ?? null,
    rank: point.grade_rank ?? null,
  })),
);

const chartOption = computed(() => buildTotalTrendOption(chartPoints.value));

function sparklineOption(values: Array<number | null>) {
  return buildSparklineOption(values);
}

function shapeColorClass(label: string): string {
  if (label === "稳步上升") return "good";
  if (label === "下滑") return "warn";
  if (label === "剧烈波动") return "danger";
  if (label === "U型反弹") return "info";
  return "muted";
}
</script>

<style scoped>
.trend-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-head h4 {
  margin: 0;
  font-size: 16px;
  color: #1d3147;
}

.badges {
  display: flex;
  gap: 6px;
}

.card-summary {
  margin: 0;
  color: #4a5b6b;
  font-size: 13px;
  line-height: 1.6;
}

.card-summary.muted {
  color: #7f8f9e;
}

.hint {
  margin: 8px 0;
  color: #7f8f9e;
  font-size: 13px;
}

.hint.small {
  font-size: 12px;
  margin: 0;
}

.subject-spark-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.subject-spark-cell {
  border-radius: 10px;
  padding: 10px 12px;
  background: rgba(31, 108, 152, 0.04);
}

.spark-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.spark-head strong {
  font-size: 13px;
  color: #1d3147;
}

.spark-tag {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 999px;
}

.spark-tag.good {
  color: #1f8a4d;
  background: rgba(31, 138, 77, 0.12);
}

.spark-tag.warn {
  color: #b66019;
  background: rgba(209, 141, 72, 0.18);
}

.spark-tag.danger {
  color: #b03a3a;
  background: rgba(176, 58, 58, 0.14);
}

.spark-tag.info {
  color: #1f6c98;
  background: rgba(31, 108, 152, 0.14);
}

.spark-tag.muted {
  color: #7f8f9e;
  background: rgba(127, 143, 158, 0.12);
}
</style>
