<template>
  <article class="soft-card inner-panel heatmap-card">
    <header class="card-head">
      <div>
        <h4>知识点热力图</h4>
        <p class="muted">行：知识点（按失分降序），列：学生。颜色越冷代表得分率越高。</p>
      </div>
      <div class="actions">
        <el-button :loading="loading" @click="emit('refresh')">{{ heatmap ? "刷新" : "加载热力图" }}</el-button>
      </div>
    </header>
    <el-alert
      v-if="errorMessage"
      type="error"
      show-icon
      :closable="false"
      :title="errorMessage"
    >
      <template #default>
        <el-button size="small" type="danger" plain :loading="loading" @click="emit('refresh')">重新加载热力图</el-button>
      </template>
    </el-alert>
    <div v-if="!heatmap && !errorMessage" class="hint">点击「加载热力图」从 API 拉取数据。</div>
    <div v-else-if="!heatmap && errorMessage" class="hint">热力图加载失败，请检查题分明细和班级筛选后重试。</div>
    <div v-else-if="heatmap?.notices?.length" class="hint">{{ heatmap.notices[0] }}</div>
    <section
      v-for="group in (heatmap?.subject_groups ?? [])"
      :key="group.subject_id"
      class="subject-block"
    >
      <h5>{{ group.subject_name }}（{{ group.students.length }} 人 × {{ group.knowledge_paths.length }} 知识点）</h5>
      <EChartHost
        v-if="group.knowledge_paths.length && group.students.length"
        :option="buildOption(group)"
        :height="`${Math.max(220, group.knowledge_paths.length * 22 + 80)}px`"
      />
      <p v-else class="hint">该科目暂无足够数据形成矩阵。</p>
    </section>
  </article>
</template>

<script setup lang="ts">
import EChartHost from "./EChartHost.vue";
import { buildHeatmapOption, type HeatmapMatrix } from "./chartOptions";

interface HeatmapStudent {
  student_id: number;
  student_name: string;
  student_no?: string | null;
}

interface HeatmapGroup {
  subject_id: number;
  subject_name: string;
  knowledge_paths: string[];
  students: HeatmapStudent[];
  cells: Array<Array<number | null>>;
}

interface HeatmapPayload {
  subject_groups: HeatmapGroup[];
  notices: string[];
}

defineProps<{
  heatmap: HeatmapPayload | null;
  loading: boolean;
  errorMessage: string;
}>();

const emit = defineEmits<{ (event: "refresh"): void }>();

function buildOption(group: HeatmapGroup) {
  const cells: Array<[number, number, number | null]> = [];
  group.cells.forEach((row, rowIndex) => {
    row.forEach((value, columnIndex) => {
      cells.push([columnIndex, rowIndex, value ?? null]);
    });
  });
  const matrix: HeatmapMatrix = {
    rowLabels: group.knowledge_paths,
    columnLabels: group.students.map((student) => student.student_name),
    cells,
  };
  return buildHeatmapOption(matrix);
}
</script>

<style scoped>
.heatmap-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 16px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-head h4 {
  margin: 0;
  color: #1d3147;
  font-size: 16px;
}

.muted {
  margin: 4px 0 0;
  color: #7f8f9e;
  font-size: 13px;
}

.subject-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.subject-block h5 {
  margin: 0;
  font-size: 14px;
  color: #2c3e50;
}

.hint {
  color: #7f8f9e;
  font-size: 13px;
  margin: 6px 0;
}
</style>
