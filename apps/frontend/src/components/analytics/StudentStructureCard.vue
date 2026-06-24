<template>
  <article class="soft-card inner-panel structure-card">
    <header class="card-head">
      <h4>学科结构与短板</h4>
      <span class="muted">{{ summary }}</span>
    </header>
    <div class="grid">
      <div class="radar-block">
        <EChartHost v-if="hasRadar" :option="radarOption" height="280px" />
        <p v-else class="hint">需要至少 3 科有效分数才能形成雷达图。</p>
        <div class="legend">
          <span><i class="dot strong"></i>本人 T 分</span>
          <span><i class="dot baseline"></i>班级平均（T=50）</span>
        </div>
      </div>
      <div class="loss-block">
        <h5>失分集中度</h5>
        <p v-if="!structure.loss_concentration.length" class="hint">本次考试未导入题分明细，无法分析失分集中度。</p>
        <ul v-else class="loss-list">
          <li v-for="entry in structure.loss_concentration" :key="entry.subject_id">
            <div class="loss-row">
              <strong>{{ entry.subject_name }}</strong>
              <span v-if="entry.loss_share != null">前 3 个知识点占失分 {{ Math.round(entry.loss_share * 100) }}%</span>
              <span v-else class="muted">失分较分散</span>
            </div>
            <p v-if="entry.top_paths.length" class="loss-paths">{{ entry.top_paths.slice(0, 3).join("｜") }}</p>
          </li>
        </ul>
      </div>
    </div>
    <div v-if="structure.strengths.length || structure.weaknesses.length" class="tag-row">
      <el-tag v-for="name in structure.strengths" :key="`s-${name}`" effect="light" type="success">优势 · {{ name }}</el-tag>
      <el-tag v-for="name in structure.weaknesses" :key="`w-${name}`" effect="light" type="danger">短板 · {{ name }}</el-tag>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

import EChartHost from "./EChartHost.vue";
import { buildRadarOption } from "./chartOptions";

interface StructurePoint {
  subject_id: number;
  subject_name: string;
  student_t_score?: number | null;
  class_average_t?: number;
  z_score?: number | null;
}

interface LossEntry {
  subject_id: number;
  subject_name: string;
  top_paths: string[];
  loss_share?: number | null;
}

interface Props {
  structure: {
    radar_points: StructurePoint[];
    strengths: string[];
    weaknesses: string[];
    loss_concentration: LossEntry[];
    summary?: string;
  };
}

const props = defineProps<Props>();

const summary = computed(() => props.structure.summary ?? "");

const hasRadar = computed(() => props.structure.radar_points.filter((point) => point.student_t_score != null).length >= 3);

const radarOption = computed(() => {
  const axes = props.structure.radar_points.map((point) => ({ name: point.subject_name, max: 80 }));
  const studentValues = props.structure.radar_points.map((point) => point.student_t_score ?? null);
  const baseline = props.structure.radar_points.map((point) => point.class_average_t ?? 50);
  return buildRadarOption(axes, [
    { name: "本人 T 分", values: studentValues },
    { name: "班级平均", values: baseline },
  ]);
});
</script>

<style scoped>
.structure-card {
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
  color: #1d3147;
  font-size: 16px;
}

.muted {
  color: #7f8f9e;
  font-size: 13px;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  align-items: start;
}

@media (max-width: 960px) {
  .grid {
    grid-template-columns: 1fr;
  }
}

.legend {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #5b6a76;
  margin-top: 4px;
}

.legend .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

.legend .dot.strong {
  background: #1f6c98;
}

.legend .dot.baseline {
  background: #d18d48;
}

.loss-block h5 {
  margin: 0 0 8px;
  color: #1d3147;
  font-size: 14px;
}

.loss-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.loss-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #2c3e50;
}

.loss-paths {
  margin: 4px 0 0;
  color: #5b6a76;
  font-size: 12px;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.hint {
  margin: 8px 0;
  color: #7f8f9e;
  font-size: 13px;
}
</style>
