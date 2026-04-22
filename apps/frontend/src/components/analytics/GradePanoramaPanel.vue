<template>
  <section class="soft-card panel-block">
    <div class="section-head compact">
      <div>
        <h3>多学年全景对比</h3>
        <p>按年级查看跨学年、跨考试的整体趋势、学年摘要和学科演进，避免只盯单次考试。</p>
      </div>
    </div>

    <div class="filter-grid">
      <el-select v-model="selectedGradeIdModel" filterable placeholder="选择年级">
        <el-option v-for="grade in grades" :key="grade.id" :label="grade.name" :value="grade.id" />
      </el-select>
      <el-select
        v-model="selectedAcademicYearIdsModel"
        multiple
        collapse-tags
        clearable
        filterable
        placeholder="筛选学年，可多选"
      >
        <el-option
          v-for="year in academicYears"
          :key="year.id"
          :label="year.name"
          :value="year.id"
        />
      </el-select>
      <div class="action-row">
        <el-button type="primary" :loading="loading" @click="emit('load')">查询</el-button>
        <el-button @click="emit('reset')">重置</el-button>
      </div>
    </div>

    <el-empty v-if="!selectedGradeId" description="请先选择年级" />
    <el-empty v-else-if="!panorama" description="当前还没有加载全景对比数据" />
    <template v-else>
      <div class="metric-grid analytics-grid">
        <div
          v-for="item in metricCards"
          :key="item.label"
          class="soft-card stat-card"
          :class="item.tone"
        >
          <div class="metric-label">{{ item.label }}</div>
          <div class="metric-value">{{ item.value }}</div>
          <div class="metric-help">{{ item.help }}</div>
        </div>
      </div>

      <section class="insight-grid">
        <article
          v-for="item in insightCards"
          :key="item.label"
          class="soft-card insight-card"
          :class="item.tone"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.help }}</p>
        </article>
      </section>

      <div class="split-grid">
        <section class="soft-card inner-panel">
          <div class="inner-head">
            <h4>学年对抗看板</h4>
          </div>
          <div class="table-shell">
            <el-table :data="yearCompetitionRows" stripe>
              <el-table-column label="学年" prop="academic_year_name" min-width="140" />
              <el-table-column label="场次" prop="exam_count" width="80" />
              <el-table-column label="平均均分" prop="average_score" width="110" />
              <el-table-column label="平均优秀率" width="120">
                <template #default="{ row }">
                  {{ row.average_excellent_rate ?? "-" }}
                </template>
              </el-table-column>
              <el-table-column label="最佳场次" prop="best_exam_name" min-width="180" />
              <el-table-column label="最近场次" prop="latest_exam_name" min-width="180" />
              <el-table-column label="状态" prop="leadLabel" width="100" />
            </el-table>
          </div>
        </section>

        <section class="soft-card inner-panel">
          <div class="inner-head">
            <h4>考试趋势摘要</h4>
          </div>
          <div class="table-shell">
            <el-table :data="examTimelineRows" stripe>
              <el-table-column label="学年" prop="academic_year_name" width="120" />
              <el-table-column label="学期" prop="semester_name" width="100" />
              <el-table-column label="考试" prop="exam_name" min-width="180" />
              <el-table-column label="日期" prop="exam_date" width="110" />
              <el-table-column label="均分" prop="total_average" width="90" />
              <el-table-column label="中位数" prop="total_median" width="90" />
              <el-table-column label="优秀率" width="100">
                <template #default="{ row }">
                  {{ row.excellent_rate ?? "-" }}
                </template>
              </el-table-column>
              <el-table-column label="前10名" prop="top10_count" width="90" />
              <el-table-column label="前30名" prop="top30_count" width="90" />
              <el-table-column label="均分变化" prop="delta_average" width="100" />
              <el-table-column label="前30变化" prop="delta_top30" width="100" />
            </el-table>
          </div>
        </section>
      </div>

      <div class="split-grid panorama-battle-grid">
        <section class="soft-card inner-panel">
          <div class="inner-head">
            <h4>学科攻坚优先级</h4>
          </div>
          <div class="table-shell">
            <el-table :data="subjectAttackRows" stripe>
              <el-table-column label="学科" prop="subject_name" min-width="120" />
              <el-table-column label="最近均分" prop="latest_average" width="100" />
              <el-table-column label="均分变化" width="100">
                <template #default="{ row }">
                  {{ formatSignedValue(row.delta_average) }}
                </template>
              </el-table-column>
              <el-table-column label="优秀率变化" width="110">
                <template #default="{ row }">
                  {{ formatSignedValue(row.delta_excellent_rate) }}
                </template>
              </el-table-column>
              <el-table-column label="趋势" prop="trendLabel" width="110" />
              <el-table-column label="当前重点" width="120">
                <template #default="{ row }">
                  <el-tag :type="focusTagType(row.focusLabel)" size="small">{{ row.focusLabel }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>

        <section class="soft-card inner-panel">
          <div class="inner-head">
            <h4>学科风险预警</h4>
          </div>
          <div class="table-shell">
            <el-table :data="subjectRiskRows" stripe>
              <el-table-column label="学科" prop="subject_name" min-width="120" />
              <el-table-column label="波动幅度" prop="swing" width="100" />
              <el-table-column label="均分变化" width="100">
                <template #default="{ row }">
                  {{ formatSignedValue(row.delta_average) }}
                </template>
              </el-table-column>
              <el-table-column label="最近优秀率" prop="latest_excellent_rate" width="110" />
              <el-table-column label="趋势" prop="trendLabel" width="110" />
              <el-table-column label="关注级别" width="110">
                <template #default="{ row }">
                  <el-tag :type="alertTagType(row.alertLevel)" size="small">{{ row.alertLevel }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>
      </div>

      <section class="soft-card inner-panel panorama-subject-panel">
        <div class="inner-head">
          <h4>全量学科趋势看板</h4>
        </div>
        <div class="table-shell">
          <el-table :data="subjectTrendRows" stripe>
            <el-table-column label="学科" prop="subject_name" min-width="120" />
            <el-table-column label="覆盖场次" prop="exam_count" width="90" />
            <el-table-column label="首场均分" prop="first_average" width="100" />
            <el-table-column label="最近均分" prop="latest_average" width="100" />
            <el-table-column label="均分变化" prop="delta_average" width="100" />
            <el-table-column label="最近优秀率" prop="latest_excellent_rate" width="110" />
          </el-table>
        </div>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import {
  buildPanoramaExamTimelineRows,
  buildPanoramaInsightCards,
  buildPanoramaMetricCards,
  buildPanoramaSubjectPriorityRows,
  buildPanoramaSubjectTrendRows,
  buildPanoramaYearCompetitionRows,
} from "./helpers";
import type { GradePanoramaResponse } from "./types";
import type { OptionItem } from "../../stores/reference";

const props = defineProps<{
  grades: OptionItem[];
  academicYears: OptionItem[];
  selectedGradeId: number | null;
  selectedAcademicYearIds: number[];
  panorama: GradePanoramaResponse | null;
  loading: boolean;
}>();

const emit = defineEmits<{
  "update:selectedGradeId": [value: number | null];
  "update:selectedAcademicYearIds": [value: number[]];
  load: [];
  reset: [];
}>();

const selectedGradeIdModel = computed({
  get: () => props.selectedGradeId,
  set: (value: number | null) => emit("update:selectedGradeId", value),
});

const selectedAcademicYearIdsModel = computed({
  get: () => props.selectedAcademicYearIds,
  set: (value: number[]) => emit("update:selectedAcademicYearIds", value.map((item) => Number(item))),
});

const metricCards = computed(() => buildPanoramaMetricCards(props.panorama));
const insightCards = computed(() => buildPanoramaInsightCards(props.panorama));
const yearCompetitionRows = computed(() => buildPanoramaYearCompetitionRows(props.panorama));
const examTimelineRows = computed(() => buildPanoramaExamTimelineRows(props.panorama));
const subjectPriorityRows = computed(() => buildPanoramaSubjectPriorityRows(props.panorama));
const subjectAttackRows = computed(() =>
  [...subjectPriorityRows.value]
    .filter((item) => item.focusLabel !== "风险预警")
    .sort((left, right) => right.momentumScore - left.momentumScore)
    .slice(0, 5),
);
const subjectRiskRows = computed(() =>
  [...subjectPriorityRows.value]
    .sort((left, right) => right.riskScore - left.riskScore || Number(left.delta_average) - Number(right.delta_average))
    .slice(0, 5),
);
const subjectTrendRows = computed(() => buildPanoramaSubjectTrendRows(props.panorama));

function formatSignedValue(value: number | string): string | number {
  if (typeof value !== "number") return value;
  return value > 0 ? `+${value}` : value;
}

function focusTagType(label: string): "success" | "warning" | "info" {
  if (label === "优势巩固") return "success";
  if (label === "重点拉升" || label === "保持观察") return "warning";
  return "info";
}

function alertTagType(label: string): "danger" | "warning" | "info" {
  if (label === "高关注") return "danger";
  if (label === "中关注") return "warning";
  return "info";
}
</script>

<style scoped>
.insight-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-top: 16px;
}

.insight-card {
  padding: 18px 20px;
}

.insight-card span {
  color: #6d8194;
  font-size: 13px;
}

.insight-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3245;
  font-size: 24px;
  font-weight: 760;
}

.insight-card p {
  margin: 8px 0 0;
  color: #73879b;
  line-height: 1.55;
  font-size: 13px;
}

.panorama-subject-panel {
  margin-top: 16px;
}

.panorama-battle-grid {
  margin-top: 16px;
}

.metric-help {
  margin-top: 8px;
  color: #6d8194;
  font-size: 12px;
  line-height: 1.55;
}

@media (max-width: 1180px) {
  .insight-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 780px) {
  .insight-grid {
    grid-template-columns: 1fr;
  }
}
</style>
