<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>推荐历史</h3>
        <p>按学生查看历史方案，支持再次查看结果与导出推荐报告。</p>
      </div>
    </div>

    <div class="filter-grid">
      <el-select v-model="historyFilters.student_id" clearable filterable placeholder="按学生筛选历史">
        <el-option
          v-for="student in studentOptions"
          :key="student.id"
          :label="`${student.student_no} - ${student.name}`"
          :value="student.id"
        />
      </el-select>
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" :loading="loadingHistory" @click="emit('load-history')">查询历史</el-button>
      <el-button :disabled="loadingHistory" @click="emit('reset-history')">重置</el-button>
    </div>

    <div v-if="historyLoadError && !loadingHistory" class="history-state-card tone-danger">
      <strong>推荐历史读取失败</strong>
      <p>{{ historyLoadError }}</p>
      <el-button size="small" type="danger" plain @click="emit('load-history')">重试读取</el-button>
    </div>

    <div v-if="loadingHistory" class="history-loading-placeholder">正在读取推荐历史...</div>
    <el-table v-else :data="historyItems" stripe max-height="360">
      <el-table-column label="方案" prop="scheme_name" min-width="180" />
      <el-table-column label="学生" prop="student_name" min-width="110" />
      <el-table-column label="省份" prop="province" width="90" />
      <el-table-column label="目标年" width="90">
        <template #default="{ row }">
          {{ row.target_year ?? "-" }}
        </template>
      </el-table-column>
      <el-table-column label="类别" width="90">
        <template #default="{ row }">
          {{ formatStudentType(row.student_type) }}
        </template>
      </el-table-column>
      <el-table-column label="分数模式" min-width="180">
        <template #default="{ row }">
          <div class="history-mode-cell">
            <span>{{ formatScoreInputLabel(row) }}</span>
            <small>{{ formatSimulationHint(row) }}</small>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="结果数" prop="result_count" width="80" />
      <el-table-column label="生成时间" prop="generated_at" min-width="170" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <div class="action-row compact-actions">
            <el-button link type="primary" @click="emit('view-scheme', row)">查看</el-button>
            <el-button link type="primary" @click="emit('export-scheme', row)">导出</el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!loadingHistory && !historyItems.length" description="暂无推荐历史" />
  </section>
</template>

<script setup lang="ts">
import type { RecommendationHistoryItem, StudentOption } from "./types";

interface HistoryFiltersState {
  student_id?: number;
}

defineProps<{
  historyItems: RecommendationHistoryItem[];
  studentOptions: StudentOption[];
  historyFilters: HistoryFiltersState;
  loadingHistory: boolean;
  historyLoadError?: string | null;
}>();

const emit = defineEmits<{
  "load-history": [];
  "reset-history": [];
  "view-scheme": [value: RecommendationHistoryItem];
  "export-scheme": [value: RecommendationHistoryItem];
}>();

function formatStudentType(value?: string | null): string {
  if (!value) return "-";
  const mapping: Record<string, string> = {
    general: "普通生",
    repeat: "复读生",
  };
  return mapping[value] ?? value;
}

function formatScoreInputLabel(item: RecommendationHistoryItem): string {
  if (item.score_input_label?.trim()) return item.score_input_label;
  const mapping: Record<string, string> = {
    actual_rank: "正式位次",
    actual_score: "正式分数",
    estimated_score: "预估分数",
    estimated_score_and_rank: "预估分数 + 预估位次",
    score_range: "分数区间",
    rank_range: "位次区间",
  };
  return mapping[item.score_input_mode] ?? item.score_input_mode ?? "-";
}

function formatSimulationHint(item: RecommendationHistoryItem): string {
  const hints: string[] = [];
  if (item.reference_exam_name?.trim()) {
    hints.push(`参考 ${item.reference_exam_name.trim()}`);
  }
  if (item.use_historical_mapping) {
    hints.push("历史映射");
  }
  if (!hints.length) {
    if (item.score_confidence === "official") return "正式成绩链路";
    if (item.score_confidence === "estimated" || item.score_confidence === "range_estimated") return "模拟测算链路";
    if (item.score_confidence === "score_only") return "分数测算链路";
    return "默认推荐链路";
  }
  return hints.join(" / ");
}
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.toolbar-row {
  margin-bottom: 16px;
}

.compact-actions {
  gap: 4px;
}

.history-mode-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  line-height: 1.5;
}

.history-mode-cell small {
  color: var(--el-text-color-secondary);
}

.history-loading-placeholder {
  display: grid;
  place-items: center;
  min-height: 180px;
  margin-bottom: 12px;
  color: #73879a;
  border: 1px dashed rgba(115, 135, 154, 0.28);
  border-radius: 16px;
  background: rgba(247, 250, 252, 0.95);
}

.history-state-card {
  margin-bottom: 12px;
  padding: 16px 18px;
  border-radius: 16px;
}

.history-state-card strong {
  display: block;
  color: #1f3245;
}

.history-state-card p {
  margin: 8px 0 12px;
  color: #5f7285;
}

.tone-danger {
  border: 1px solid rgba(210, 63, 63, 0.24);
  background: rgba(255, 245, 245, 0.92);
}
</style>
