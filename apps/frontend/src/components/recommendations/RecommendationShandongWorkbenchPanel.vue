<template>
  <section class="shandong-workbench panel-block">
    <div class="section-head">
      <div>
        <h3>山东普通类推荐工作台</h3>
        <p>选择学生和位次来源后生成“冲 / 稳 / 保 / 仅关注”，并同步查看数据覆盖和发布状态。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('sync-from-recommendation')">沿用推荐条件</el-button>
        <el-button @click="emit('load-data-health')">刷新数据看板</el-button>
        <el-button :disabled="!result" @click="emit('print-report')">打印报告</el-button>
        <el-button :disabled="!result" :loading="exportingReport" @click="emit('export-report')">导出 Excel</el-button>
        <el-button @click="emit('reset')">清空</el-button>
        <el-button type="primary" :loading="loading" @click="emit('generate')">生成山东推荐</el-button>
      </div>
    </div>

    <section class="shandong-workbench-layout">
      <div class="shandong-input-panel">
        <div class="section-head compact">
          <div>
            <h3>推荐输入</h3>
            <p>默认按 2026 山东普通类常规批预览；分数和位次都只在本机使用。</p>
          </div>
        </div>

        <div class="source-mode-block">
          <el-radio-group v-model="form.source_mode">
            <el-radio-button v-for="item in shandongSourceModeOptions" :key="item.value" :label="item.value">
              {{ item.label }}
            </el-radio-button>
          </el-radio-group>
          <p class="mode-help">{{ currentSourceModeHelp }}</p>
        </div>

        <div class="filter-grid shandong-filter-grid">
          <el-select v-model="form.student_id" filterable placeholder="选择学生">
            <el-option
              v-for="student in studentOptions"
              :key="student.id"
              :label="`${student.student_no} - ${student.name}`"
              :value="student.id"
            />
          </el-select>
          <el-select
            v-if="form.source_mode === 'exam_projection'"
            v-model="form.exam_id"
            filterable
            placeholder="选择参考考试"
          >
            <el-option v-for="exam in examOptions" :key="exam.id" :label="exam.name" :value="exam.id" />
          </el-select>
          <el-input-number
            v-if="form.source_mode === 'manual_score'"
            v-model="form.manual_score"
            :min="0"
            :max="750"
            controls-position="right"
            style="width: 100%"
            placeholder="预估高考分数"
          />
          <el-input-number
            v-if="form.source_mode === 'manual_rank'"
            v-model="form.manual_rank"
            :min="1"
            :max="999999"
            controls-position="right"
            style="width: 100%"
            placeholder="山东全省位次"
          />
          <el-select v-model="form.target_year" filterable placeholder="目标年份">
            <el-option v-for="year in yearOptions" :key="year" :label="String(year)" :value="year" />
          </el-select>
          <el-input v-model="form.batch" placeholder="批次，例如：常规批" />
          <el-select v-model="form.risk_preference" placeholder="风险偏好">
            <el-option
              v-for="item in shandongRiskPreferenceOptions"
              :key="item.value"
              :label="`${item.label}：${item.help}`"
              :value="item.value"
            />
          </el-select>
          <el-input v-model="form.major_keyword" clearable placeholder="专业关键词，可选" />
          <el-select
            v-model="form.target_regions_json"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            placeholder="目标地区，可选"
          >
            <el-option v-for="item in targetRegionOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-select
            v-model="form.school_level_tags_json"
            multiple
            filterable
            allow-create
            default-first-option
            collapse-tags
            placeholder="院校层级，可选"
          >
            <el-option v-for="item in schoolLevelOptions" :key="item" :label="item" :value="item" />
          </el-select>
          <el-input-number
            v-model="form.limit"
            :min="1"
            :max="300"
            controls-position="right"
            style="width: 100%"
            placeholder="每组最多展示"
          />
        </div>

        <div class="subject-picker">
          <span>选科组合</span>
          <el-checkbox-group v-model="form.selected_subjects_json">
            <el-checkbox-button v-for="subject in shandongSubjectOptions" :key="subject" :label="subject">
              {{ subject }}
            </el-checkbox-button>
          </el-checkbox-group>
        </div>

        <el-alert
          v-if="form.source_mode === 'exam_projection'"
          title="校内考试估算会自动保存一条预估快照，并在结果中标记“校内估算”。正式填报前仍需用全省位次复核。"
          type="warning"
          show-icon
          :closable="false"
        />
      </div>

      <div class="shandong-quality-panel">
        <div class="section-head compact">
          <div>
            <h3>数据质量看板</h3>
            <p>重点看最近三年数据、2026 发布状态和 P0 缺口。</p>
          </div>
          <el-button size="small" :loading="loadingDataHealth" @click="emit('load-data-health')">刷新</el-button>
        </div>

        <div class="quality-summary-grid">
          <article class="quality-summary-item">
            <span>健康摘要</span>
            <strong>{{ dataHealth?.summary || "待加载" }}</strong>
          </article>
          <article class="quality-summary-item">
            <span>P0 缺口</span>
            <strong>{{ dataHealth?.gaps.length ?? 0 }}</strong>
          </article>
          <article class="quality-summary-item">
            <span>2026 数据项</span>
            <strong>{{ dataHealth?.publication_status.length ?? 0 }}</strong>
          </article>
        </div>

        <div class="quality-table-block">
          <div class="block-title">2023-2025 覆盖矩阵</div>
          <el-table :data="coverageRows" size="small" stripe>
            <el-table-column label="数据域" prop="label" min-width="150" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="shandongStatusTagType(row.status)" effect="light">{{ row.statusLabel }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="已覆盖" width="140">
              <template #default="{ row }">{{ formatYearList(row.coveredYears) }}</template>
            </el-table-column>
            <el-table-column label="缺口" width="140">
              <template #default="{ row }">{{ formatYearList(row.missingYears) }}</template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!coverageRows.length" description="暂无覆盖矩阵，请刷新数据看板" />
        </div>

        <div class="quality-table-block">
          <div class="block-title">2026 发布状态</div>
          <el-table :data="dataHealth?.publication_status ?? []" size="small" stripe>
            <el-table-column label="数据项" prop="label" min-width="170" />
            <el-table-column label="状态" width="130">
              <template #default="{ row }">
                <el-tag :type="shandongStatusTagType(row.status)" effect="light">{{ row.status_label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="下一步" min-width="220">
              <template #default="{ row }">
                <span class="table-muted">{{ row.action_label }}</span>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!dataHealth?.publication_status.length" description="暂无 2026 发布状态" />
        </div>

        <div class="gap-list">
          <strong>P0 缺口</strong>
          <ul v-if="dataHealth?.gaps.length">
            <li v-for="gap in dataHealth.gaps" :key="gap">{{ gap }}</li>
          </ul>
          <p v-else class="table-muted">当前未加载缺口，或 P0 规则内未发现明显缺口。</p>
        </div>
      </div>
    </section>

    <section v-if="projection" class="projection-strip">
      <strong>本次考试预估</strong>
      <span>预估分 {{ formatNullableNumber(projection.predicted_score) }}</span>
      <span>预估位次 {{ formatNullableNumber(projection.predicted_rank) }}</span>
      <span>置信度 {{ formatShandongConfidence(projection.confidence_level) }}</span>
      <span v-if="savingProjection">正在保存预估快照...</span>
    </section>

    <section v-if="result" class="result-overview">
      <article class="result-overview-item">
        <span>学生</span>
        <strong>{{ result.student_name || "未命名学生" }}</strong>
      </article>
      <article class="result-overview-item">
        <span>输入来源</span>
        <strong>{{ formatShandongSourceMode(result.source_mode) }}</strong>
      </article>
      <article class="result-overview-item">
        <span>预估位次</span>
        <strong>{{ formatNullableNumber(result.predicted_rank) }}</strong>
      </article>
      <article class="result-overview-item">
        <span>风险偏好</span>
        <strong>{{ formatShandongRiskPreference(result.risk_preference) }}</strong>
      </article>
      <article class="result-overview-item">
        <span>选科不符已排除</span>
        <strong>{{ result.summary.excluded_subject_mismatch_count }}</strong>
      </article>
    </section>

    <el-alert
      v-if="result?.input_notes.length"
      :title="result.input_notes.join('；')"
      type="info"
      show-icon
      :closable="false"
    />

    <section v-if="result" class="result-group-stack">
      <div v-for="group in resultGroups" :key="group.key" class="result-group">
        <div class="result-group-head">
          <div>
            <h3>{{ group.label }} <span>{{ group.items.length }} 条</span></h3>
            <p>{{ group.description }}</p>
          </div>
          <el-tag :type="group.tagType" effect="light">{{ group.label }}</el-tag>
        </div>
        <el-table :data="group.items" stripe>
          <el-table-column type="expand" width="44">
            <template #default="{ row }">
              <div class="candidate-detail">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="专业（专业类）+ 学校">
                    {{ row.major_name || "院校级计划" }} / {{ row.college_name }}
                  </el-descriptions-item>
                  <el-descriptions-item label="位次差距">
                    {{ formatNullableNumber(row.rank_margin) }} 位，边际 {{ formatPercent(row.rank_margin_ratio) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="计划数变化">
                    {{ getShandongPlanChangeSummary(row) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="选科要求">
                    {{ row.subject_requirement || "不限或待补" }}
                  </el-descriptions-item>
                  <el-descriptions-item label="章程限制">
                    当前推荐未直接纳入学校章程限制，填报前请复核语言、体检、单科和校区要求。
                  </el-descriptions-item>
                  <el-descriptions-item label="数据来源">
                    {{ formatShandongSourceDocumentIds(row.source_document_ids) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="推荐理由" :span="2">
                    {{ row.explanation_text }}
                  </el-descriptions-item>
                </el-descriptions>
                <div class="detail-subsection">
                  <strong>历年最低分 / 位次</strong>
                  <el-table :data="getShandongHistoricalRankRows(row)" size="small" stripe>
                    <el-table-column label="年份" prop="year" width="90" />
                    <el-table-column label="最低分" width="110">
                      <template #default="{ row: historyRow }">{{ formatNullableNumber(historyRow.min_score) }}</template>
                    </el-table-column>
                    <el-table-column label="最低位次" width="130">
                      <template #default="{ row: historyRow }">{{ formatNullableNumber(historyRow.min_rank) }}</template>
                    </el-table-column>
                    <el-table-column label="计划数" width="110">
                      <template #default="{ row: historyRow }">{{ formatNullableNumber(historyRow.plan_count) }}</template>
                    </el-table-column>
                    <el-table-column label="来源说明" prop="source_note" min-width="220" />
                  </el-table>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="学校 / 专业" min-width="260">
            <template #default="{ row }">
              <div class="table-strong">{{ row.college_name }}</div>
              <div class="table-muted">{{ row.major_name || "院校级计划" }}</div>
            </template>
          </el-table-column>
          <el-table-column label="分层" width="90">
            <template #default="{ row }">
              <el-tag :type="group.tagType" effect="light">{{ row.bucket_label }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="参考位次" width="130">
            <template #default="{ row }">{{ formatNullableNumber(getShandongReferenceRank(row)) }}</template>
          </el-table-column>
          <el-table-column label="最近分 / 位次" width="160">
            <template #default="{ row }">
              {{ formatNullableNumber(getShandongLatestMinScore(row)) }} /
              {{ formatNullableNumber(getShandongLatestMinRank(row)) }}
            </template>
          </el-table-column>
          <el-table-column label="位次差" width="120">
            <template #default="{ row }">{{ formatNullableNumber(row.rank_margin) }}</template>
          </el-table-column>
          <el-table-column label="计划数" width="100">
            <template #default="{ row }">{{ formatNullableNumber(row.plan_count) }}</template>
          </el-table-column>
          <el-table-column label="风险" min-width="220">
            <template #default="{ row }">
              <div class="risk-tag-row">
                <el-tag :type="shandongConfidenceTagType(row.data_confidence)" effect="light">
                  置信度 {{ formatShandongConfidence(row.data_confidence) }}
                </el-tag>
                <el-tag v-for="flag in row.risk_flags" :key="flag" type="warning" effect="light">
                  {{ formatShandongRiskFlag(flag) }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!group.items.length" :description="`${group.label} 暂无结果`" />
      </div>
    </section>

    <el-empty v-else description="填写条件后点击“生成山东推荐”，这里会展示冲稳保结果和展开说明。" />
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import {
  formatNullableNumber,
  formatPercent,
  formatShandongConfidence,
  formatShandongRiskFlag,
  formatShandongRiskPreference,
  formatShandongSourceDocumentIds,
  formatShandongSourceMode,
  formatYearList,
  getShandongHistoricalRankRows,
  getShandongLatestMinRank,
  getShandongLatestMinScore,
  getShandongPlanChangeSummary,
  getShandongReferenceRank,
  shandongConfidenceTagType,
  shandongRiskPreferenceOptions,
  shandongSourceModeOptions,
  shandongStatusTagType,
  shandongSubjectOptions,
  type ShandongCoverageRow,
  type ShandongResultGroup,
} from "./shandongRecommendationWorkbench";
import type {
  ExamOption,
  ShandongRecommendationDataHealth,
  ShandongRecommendationFormState,
  ShandongRushStableSafeRecommendationResponse,
  StudentGaokaoScoreProjectionRead,
  StudentOption,
} from "./types";

const props = defineProps<{
  form: ShandongRecommendationFormState;
  studentOptions: StudentOption[];
  examOptions: ExamOption[];
  yearOptions: number[];
  targetRegionOptions: string[];
  schoolLevelOptions: string[];
  result: ShandongRushStableSafeRecommendationResponse | null;
  resultGroups: ShandongResultGroup[];
  projection: StudentGaokaoScoreProjectionRead | null;
  dataHealth: ShandongRecommendationDataHealth | null;
  coverageRows: ShandongCoverageRow[];
  loading: boolean;
  loadingDataHealth: boolean;
  savingProjection: boolean;
  exportingReport: boolean;
}>();

const emit = defineEmits<{
  generate: [];
  reset: [];
  "load-data-health": [];
  "sync-from-recommendation": [];
  "print-report": [];
  "export-report": [];
}>();

const currentSourceModeHelp = computed(() => {
  return shandongSourceModeOptions.find((item) => item.value === props.form.source_mode)?.help ?? "";
});
</script>

<style scoped>
.shandong-workbench {
  padding: 24px;
}

.shandong-workbench-layout {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(360px, 1.05fr);
  gap: 20px;
  align-items: start;
}

.shandong-input-panel,
.shandong-quality-panel {
  display: grid;
  gap: 16px;
  min-width: 0;
}

.source-mode-block {
  display: grid;
  gap: 10px;
}

.source-mode-block :deep(.el-radio-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.source-mode-block :deep(.el-radio-button__inner) {
  border-radius: 8px;
  border-left: var(--el-border);
}

.mode-help,
.table-muted {
  margin: 0;
  color: #6b7f92;
  font-size: 13px;
  line-height: 1.55;
}

.shandong-filter-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.subject-picker {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid rgba(128, 148, 167, 0.18);
  border-radius: 8px;
  background: rgba(248, 251, 254, 0.88);
}

.subject-picker > span,
.block-title {
  color: #2e4358;
  font-size: 13px;
  font-weight: 700;
}

.quality-summary-grid,
.result-overview {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.quality-summary-item,
.result-overview-item {
  padding: 14px;
  border: 1px solid rgba(128, 148, 167, 0.16);
  border-radius: 8px;
  background: #f9fbfd;
}

.quality-summary-item span,
.result-overview-item span {
  display: block;
  color: #6b7f92;
  font-size: 12px;
}

.quality-summary-item strong,
.result-overview-item strong {
  display: block;
  margin-top: 6px;
  color: #203549;
  font-size: 18px;
  line-height: 1.35;
}

.quality-table-block,
.gap-list,
.projection-strip,
.result-group {
  padding: 16px;
  border: 1px solid rgba(128, 148, 167, 0.16);
  border-radius: 8px;
  background: #fff;
}

.quality-table-block {
  display: grid;
  gap: 10px;
}

.gap-list ul {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #5f7387;
  line-height: 1.65;
}

.projection-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-top: 18px;
  color: #40566b;
}

.projection-strip strong {
  color: #203549;
}

.result-overview {
  margin-top: 18px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.result-group-stack {
  display: grid;
  gap: 18px;
  margin-top: 18px;
}

.result-group-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.result-group-head h3 {
  margin: 0;
  color: #203549;
  font-size: 18px;
}

.result-group-head h3 span {
  color: #6b7f92;
  font-size: 14px;
  font-weight: 600;
}

.result-group-head p {
  margin: 6px 0 0;
  color: #6b7f92;
  font-size: 13px;
}

.table-strong {
  color: #24384d;
  font-weight: 700;
}

.risk-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.candidate-detail {
  display: grid;
  gap: 14px;
  padding: 14px 8px;
}

.detail-subsection {
  display: grid;
  gap: 10px;
}

.detail-subsection strong {
  color: #203549;
}

@media (max-width: 1180px) {
  .shandong-workbench-layout {
    grid-template-columns: 1fr;
  }

  .result-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .shandong-filter-grid,
  .quality-summary-grid,
  .result-overview {
    grid-template-columns: 1fr;
  }
}
</style>
