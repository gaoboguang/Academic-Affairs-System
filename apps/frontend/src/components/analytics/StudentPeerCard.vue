<template>
  <article class="soft-card inner-panel peer-card">
    <header class="card-head">
      <h4>同分段对比</h4>
      <span class="muted">{{ headline }}</span>
    </header>
    <p v-if="peer.peer_sample_note" class="muted note">{{ peer.peer_sample_note }}</p>
    <EChartHost v-if="hasRows" :option="chartOption" height="260px" />
    <p v-else class="hint">同分段样本不足，无法生成对比。建议在年级数据齐备后再来查看。</p>
    <div v-if="peer.laggard_subjects?.length" class="laggard-row">
      <el-tag v-for="name in peer.laggard_subjects" :key="name" effect="light" type="danger">同档相对落后 · {{ name }}</el-tag>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

import EChartHost from "./EChartHost.vue";
import { buildPeerCompareOption, type PeerCompareRow } from "./chartOptions";

interface PeerSubjectGap {
  subject_id: number;
  subject_name: string;
  student_score?: number | null;
  peer_average?: number | null;
  gap?: number | null;
}

interface Props {
  peer: {
    peer_count: number;
    peer_radius: number;
    peer_total_average?: number | null;
    peer_sample_note?: string | null;
    subject_gaps: PeerSubjectGap[];
    laggard_subjects?: string[];
  };
}

const props = defineProps<Props>();

const headline = computed(() => {
  if (!props.peer.peer_count) {
    return "同分段样本暂未生成";
  }
  const avg = props.peer.peer_total_average != null ? `平均 ${props.peer.peer_total_average} 分` : "";
  return `命中 ${props.peer.peer_count} 名同分段同学（±${props.peer.peer_radius} 名）${avg}`;
});

const validRows = computed<PeerCompareRow[]>(() =>
  props.peer.subject_gaps
    .filter((row) => row.student_score != null || row.peer_average != null)
    .map((row) => ({
      subjectName: row.subject_name,
      studentScore: row.student_score ?? null,
      peerAverage: row.peer_average ?? null,
    })),
);

const hasRows = computed(() => validRows.value.length >= 1);

const chartOption = computed(() => buildPeerCompareOption(validRows.value));
</script>

<style scoped>
.peer-card {
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

.note {
  margin: 0;
}

.laggard-row {
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
