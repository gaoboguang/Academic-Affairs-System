<template>
  <div class="page-shell">
    <section
      v-if="evaluationOverview || loadingEvaluationOverview || evaluationOverviewError"
      class="soft-card panel-block"
      v-loading="loadingEvaluationOverview"
    >
      <el-alert
        v-if="evaluationOverviewError"
        class="panel-alert"
        type="error"
        show-icon
        :closable="false"
        title="评教批次总览加载失败"
      >
        <template #default>{{ evaluationOverviewError }}</template>
      </el-alert>

      <el-empty
        v-if="!evaluationOverview && !loadingEvaluationOverview"
        :description="evaluationOverviewError ? '当前批次总览暂时加载失败。' : '请选择一个评教批次查看总览。'"
      />

      <template v-if="evaluationOverview">
      <div class="section-head">
        <div>
          <h3>批次总览</h3>
          <p>{{ evaluationOverview.template_name }} · {{ evaluationOverview.semester_name }}</p>
        </div>
      </div>

      <section class="metric-grid compact-metrics">
        <div class="soft-card stat-card">
          <div class="metric-label">教师数</div>
          <div class="metric-value">{{ evaluationOverview.teacher_count }}</div>
        </div>
        <div class="soft-card stat-card">
          <div class="metric-label">最高综合分</div>
          <div class="metric-value">{{ evaluationOverview.teacher_summaries[0]?.overall_avg_score ?? "-" }}</div>
        </div>
      </section>

      <div class="compare-toolbar">
        <div>
          <h4>批次对比</h4>
          <p>把当前批次和历史批次放在同一张表里，看教师整体是提升、回落还是持平。</p>
        </div>
        <div class="compare-selector">
          <el-select
            :model-value="selectedCompareBatchId ?? undefined"
            clearable
            filterable
            :disabled="controlsDisabled || loadingEvaluationComparison"
            placeholder="选择对比批次"
            @change="emit('change-compare-batch', $event)"
          >
            <el-option
              v-for="item in compareBatchOptions"
              :key="item.id"
              :label="`${item.template_name} · ${item.semester_name} · ${item.import_time}`"
              :value="item.id"
            />
          </el-select>
        </div>
      </div>

      <el-alert
        v-if="evaluationComparisonError"
        class="panel-alert"
        type="error"
        show-icon
        :closable="false"
        title="批次对比加载失败"
      >
        <template #default>{{ evaluationComparisonError }}</template>
      </el-alert>

      <section v-if="evaluationComparison" class="comparison-metric-grid">
        <div class="soft-card stat-card">
          <div class="metric-label">共同教师</div>
          <div class="metric-value">{{ evaluationComparison.overlap_teacher_count }}</div>
        </div>
        <div class="soft-card stat-card">
          <div class="metric-label">提升人数</div>
          <div class="metric-value comparison-up">{{ evaluationComparison.improved_count }}</div>
        </div>
        <div class="soft-card stat-card">
          <div class="metric-label">回落人数</div>
          <div class="metric-value comparison-down">{{ evaluationComparison.declined_count }}</div>
        </div>
        <div class="soft-card stat-card">
          <div class="metric-label">仅当前 / 仅历史</div>
          <div class="metric-value">
            {{ evaluationComparison.only_current_count }} / {{ evaluationComparison.only_compare_count }}
          </div>
        </div>
      </section>

      <el-table
        v-if="evaluationComparison"
        :data="evaluationComparison.teacher_deltas"
        stripe
        v-loading="loadingEvaluationComparison"
        style="margin-bottom: 16px"
      >
        <el-table-column label="教师" prop="teacher_name" min-width="120" />
        <el-table-column label="当前分" prop="current_score" width="100" />
        <el-table-column label="对比分" prop="compare_score" width="100" />
        <el-table-column label="分数变化" min-width="110">
          <template #default="{ row }">
            <span :class="deltaClass(row.score_delta)">{{ formatSignedValue(row.score_delta) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="名次变化" min-width="110">
          <template #default="{ row }">
            <span :class="deltaClass(row.rank_delta)">
              {{ formatRankDelta(row.rank_delta) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="样本变化" min-width="100">
          <template #default="{ row }">
            {{ formatSignedValue(row.response_count_delta, 0) }}
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="当前两个批次没有可对比的共同教师。" />
        </template>
      </el-table>

      <el-table :data="evaluationOverview.teacher_summaries" stripe>
        <el-table-column label="名次" prop="rank" width="80" />
        <el-table-column label="教师" prop="teacher_name" min-width="120" />
        <el-table-column label="综合得分" prop="overall_avg_score" width="110" />
        <el-table-column label="样本数" prop="response_count" width="90" />
        <el-table-column label="维度得分" min-width="260">
          <template #default="{ row }">
            {{ formatWeight(row.dimension_scores_json) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="controlsDisabled" @click="emit('load-teacher-detail', row.teacher_id)">查看</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="当前批次暂无教师评教汇总。请检查导入数据是否包含可匹配教师。" />
        </template>
      </el-table>
      </template>
    </section>

    <section
      v-if="evaluationDetail || loadingTeacherDetail || teacherDetailError"
      class="soft-card panel-block"
      v-loading="loadingTeacherDetail"
    >
      <el-alert
        v-if="teacherDetailError"
        class="panel-alert"
        type="error"
        show-icon
        :closable="false"
        title="教师评教详情加载失败"
      >
        <template #default>{{ teacherDetailError }}</template>
      </el-alert>

      <template v-if="evaluationDetail">
      <div class="section-head">
        <div>
          <h3>教师评教详情</h3>
          <p>{{ evaluationDetail.teacher_name }} · 综合得分 {{ evaluationDetail.overall_avg_score }}</p>
        </div>
      </div>

      <section v-if="evaluationTeacherTrend?.points.length" class="trend-panel">
        <div class="section-head compact">
          <div>
            <h4>历史趋势</h4>
            <p>按同模板历史批次回看这位教师的综合得分和名次变化。</p>
          </div>
        </div>

        <div class="trend-metric-grid">
          <div class="soft-card stat-card">
            <div class="metric-label">历史批次</div>
            <div class="metric-value">{{ evaluationTeacherTrend.points.length }}</div>
          </div>
          <div class="soft-card stat-card">
            <div class="metric-label">当前批次变化</div>
            <div class="metric-value" :class="deltaClass(trendDeltaScore)">
              {{ trendDeltaScore === null ? "-" : formatSignedValue(trendDeltaScore) }}
            </div>
          </div>
          <div class="soft-card stat-card">
            <div class="metric-label">历史最高分</div>
            <div class="metric-value">{{ trendPeakScore }}</div>
          </div>
          <div class="soft-card stat-card">
            <div class="metric-label">当前名次变化</div>
            <div class="metric-value" :class="deltaClass(trendRankDelta)">
              {{ formatRankDelta(trendRankDelta) }}
            </div>
          </div>
        </div>

        <el-table :data="evaluationTeacherTrend.points" stripe style="margin-top: 16px">
          <el-table-column label="批次" min-width="220">
            <template #default="{ row }">
              {{ row.template_name }} · {{ row.semester_name || "-" }}
            </template>
          </el-table-column>
          <el-table-column label="综合得分" prop="overall_avg_score" width="110" />
          <el-table-column label="名次" prop="rank" width="90" />
          <el-table-column label="样本数" prop="response_count" width="90" />
          <el-table-column label="导入时间" prop="import_time" min-width="170" />
        </el-table>
      </section>

      <div class="detail-grid-box">
        <div class="soft-card inner-card">
          <h4>维度得分</h4>
          <el-table :data="evaluationDetail.dimension_summaries" stripe>
            <el-table-column label="维度" prop="dimension_name" min-width="140" />
            <el-table-column label="平均分" prop="avg_score" width="100" />
            <el-table-column label="样本数" prop="response_count" width="90" />
            <template #empty>
              <el-empty description="当前教师暂无维度得分。"/>
            </template>
          </el-table>
        </div>
        <div class="soft-card inner-card">
          <h4>题目明细</h4>
          <el-table :data="evaluationDetail.question_stats" stripe>
            <el-table-column label="维度" prop="dimension_name" width="120" />
            <el-table-column label="题目" prop="question_text" min-width="220" />
            <el-table-column label="平均分" prop="avg_score" width="100" />
            <el-table-column label="样本数" prop="response_count" width="90" />
            <template #empty>
              <el-empty description="当前教师暂无题目明细。"/>
            </template>
          </el-table>
        </div>
      </div>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { deltaClass, formatRankDelta, formatSignedValue, formatWeight } from "./helpers";
import type {
  EvaluationBatch,
  EvaluationBatchCompare,
  EvaluationOverview,
  EvaluationTeacherDetail,
  EvaluationTeacherTrend,
} from "./types";

defineProps<{
  evaluationOverview: EvaluationOverview | null;
  selectedCompareBatchId: number | null;
  compareBatchOptions: EvaluationBatch[];
  evaluationComparison: EvaluationBatchCompare | null;
  evaluationDetail: EvaluationTeacherDetail | null;
  evaluationTeacherTrend: EvaluationTeacherTrend | null;
  trendDeltaScore: number | null;
  trendRankDelta: number | null;
  trendPeakScore: string;
  loadingEvaluationOverview: boolean;
  evaluationOverviewError: string;
  loadingEvaluationComparison: boolean;
  evaluationComparisonError: string;
  loadingTeacherDetail: boolean;
  teacherDetailError: string;
  controlsDisabled: boolean;
}>();

const emit = defineEmits<{
  "change-compare-batch": [value: number | string | undefined | null];
  "load-teacher-detail": [teacherId: number];
}>();
</script>

<style scoped>
.stat-card {
  padding: 18px 20px;
}

.panel-alert {
  margin-bottom: 14px;
}

.metric-label {
  color: #61778b;
  font-size: 13px;
}

.metric-value {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 760;
  color: #21374b;
}

.compact-metrics {
  margin-bottom: 16px;
}

.compare-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(247, 251, 254, 0.92);
  border: 1px solid rgba(117, 134, 152, 0.14);
}

.compare-toolbar h4 {
  margin: 0;
  color: #22384c;
}

.compare-toolbar p {
  margin: 6px 0 0;
  color: #657b8f;
  line-height: 1.6;
}

.compare-selector {
  width: min(320px, 100%);
}

.comparison-metric-grid,
.trend-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.trend-panel {
  margin-bottom: 16px;
  padding: 18px;
  border-radius: 20px;
  background: rgba(246, 250, 253, 0.9);
  border: 1px solid rgba(116, 133, 151, 0.12);
}

.comparison-up {
  color: #1d7b4d;
}

.comparison-down {
  color: #ba5c43;
}

.comparison-flat {
  color: #72869a;
}

.detail-grid-box {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.inner-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(116, 133, 151, 0.14);
  background: rgba(248, 252, 255, 0.92);
}

.inner-card h4 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #22384b;
}

@media (max-width: 1080px) {
  .detail-grid-box,
  .comparison-metric-grid,
  .trend-metric-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .compare-toolbar {
    flex-direction: column;
  }

  .compare-selector {
    width: 100%;
  }
}
</style>
