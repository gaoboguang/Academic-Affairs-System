<template>
  <article class="soft-card inner-panel target-card">
    <header class="card-head">
      <h4>目标线达成进度</h4>
      <span class="muted">{{ summary }}</span>
    </header>
    <div v-if="!progress.length" class="hint">未配置目标线或暂无总分快照。</div>
    <ul v-else class="progress-list">
      <li v-for="entry in progress" :key="`${entry.line_id ?? entry.line_name}`" class="progress-row">
        <div class="row-head">
          <strong>{{ entry.line_name }}</strong>
          <el-tag size="small" :type="probabilityTagType(entry.reach_probability_level)" effect="dark">
            {{ probabilityLabel(entry.reach_probability_level, entry.reach_probability) }}
          </el-tag>
        </div>
        <div class="bar-row">
          <span class="bar-label">{{ formatScore(entry.current_score) }} → {{ formatScore(entry.target_score) }}</span>
          <div class="bar-track">
            <div
              class="bar-fill"
              :class="{ reached: (entry.gap ?? 0) >= 0 }"
              :style="{ width: progressPercent(entry) + '%' }"
            ></div>
          </div>
          <span class="bar-gap">{{ gapLabel(entry.gap) }}</span>
        </div>
        <p v-if="entry.trend_estimate != null" class="row-note">
          按近期趋势预计每次约 {{ formatTrend(entry.trend_estimate) }}；{{ entry.note }}
        </p>
        <p v-else class="row-note muted">{{ entry.note }}</p>
        <div v-if="entry.required_subject_combos?.length" class="combo-list">
          <span class="combo-title">突破组合建议</span>
          <span
            v-for="combo in entry.required_subject_combos"
            :key="combo.subject_id"
            class="combo-pill"
            :class="`feasibility-${combo.feasibility}`"
          >
            {{ combo.subject_name }} +{{ combo.gain_needed }} 分
            <small v-if="combo.note">（{{ combo.note }}）</small>
          </span>
        </div>
      </li>
    </ul>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface Combo {
  subject_id: number;
  subject_name: string;
  gain_needed: number;
  feasibility: string;
  note?: string;
}

interface ProgressEntry {
  line_id?: number | null;
  line_name: string;
  current_score?: number | null;
  target_score?: number | null;
  gap?: number | null;
  trend_estimate?: number | null;
  reach_probability_level?: string;
  reach_probability?: number | null;
  required_subject_combos?: Combo[];
  note?: string;
}

interface Props {
  progress: ProgressEntry[];
}

const props = defineProps<Props>();

const summary = computed(() => {
  if (!props.progress.length) return "尚未配置目标线";
  const reached = props.progress.filter((entry) => (entry.gap ?? 0) >= 0).length;
  return `已达 ${reached} / 共 ${props.progress.length} 条目标线`;
});

function progressPercent(entry: ProgressEntry): number {
  const current = entry.current_score ?? 0;
  const target = entry.target_score ?? 0;
  if (!target) return 0;
  if (entry.gap != null && entry.gap >= 0) return 100;
  if (current <= 0) return 0;
  return Math.min(100, Math.max(4, (current / target) * 100));
}

function gapLabel(gap?: number | null): string {
  if (gap == null) return "-";
  if (gap >= 0) return `已超线 ${gap.toFixed(1)} 分`;
  return `还差 ${Math.abs(gap).toFixed(1)} 分`;
}

function formatScore(value?: number | null): string {
  if (value == null) return "-";
  return `${value.toFixed(0)} 分`;
}

function formatTrend(value: number): string {
  if (value === 0) return "持平";
  return value > 0 ? `+${value.toFixed(1)} 分` : `${value.toFixed(1)} 分`;
}

function probabilityLabel(level?: string, probability?: number | null): string {
  if (!level || level === "unknown") return "数据不足";
  const map: Record<string, string> = { high: "把握较大", medium: "存在变数", low: "差距较大" };
  if (probability != null) {
    return `${map[level] ?? level} · ${(probability * 100).toFixed(0)}%`;
  }
  return map[level] ?? level;
}

function probabilityTagType(level?: string): "success" | "warning" | "danger" | "info" {
  switch (level) {
    case "high":
      return "success";
    case "medium":
      return "warning";
    case "low":
      return "danger";
    default:
      return "info";
  }
}
</script>

<style scoped>
.target-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-head h4 {
  margin: 0;
  color: #1d3147;
  font-size: 16px;
}

.muted {
  color: #7f8f9e;
  font-size: 13px;
}

.progress-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.progress-row {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(31, 108, 152, 0.04);
}

.row-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.row-head strong {
  color: #1d3147;
}

.bar-row {
  display: grid;
  grid-template-columns: 110px 1fr auto;
  gap: 10px;
  align-items: center;
}

.bar-label {
  font-size: 12px;
  color: #5b6a76;
}

.bar-track {
  height: 8px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.12);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #d18d48, #1f6c98);
  transition: width 200ms ease;
}

.bar-fill.reached {
  background: linear-gradient(90deg, #4caf50, #2e7d32);
}

.bar-gap {
  font-size: 12px;
  color: #2c3e50;
}

.row-note {
  margin: 6px 0 0;
  font-size: 12px;
  color: #4a5b6b;
}

.combo-list {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.combo-title {
  font-size: 12px;
  color: #5b6a76;
  margin-right: 6px;
}

.combo-pill {
  font-size: 12px;
  padding: 3px 9px;
  border-radius: 999px;
}

.combo-pill.feasibility-high {
  background: rgba(76, 175, 80, 0.16);
  color: #1f8a4d;
}

.combo-pill.feasibility-medium {
  background: rgba(209, 141, 72, 0.18);
  color: #b66019;
}

.combo-pill.feasibility-low {
  background: rgba(176, 58, 58, 0.14);
  color: #b03a3a;
}

.combo-pill.feasibility-unknown {
  background: rgba(127, 143, 158, 0.14);
  color: #5b6a76;
}

.hint {
  margin: 8px 0;
  color: #7f8f9e;
  font-size: 13px;
}
</style>
