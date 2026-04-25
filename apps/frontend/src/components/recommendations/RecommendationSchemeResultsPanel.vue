<template>
  <section v-if="schemeMeta" class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>方案结果</h3>
        <p>
          {{ schemeMeta.scheme_name }} · {{ schemeMeta.student_name }} ·
          {{ formatStudentType(schemeMeta.student_type) }} · {{ schemeMeta.province }}
        </p>
      </div>
      <div class="action-row">
        <el-tag type="danger" effect="light">冲 {{ groupedResults.challenge.length }}</el-tag>
        <el-tag type="warning" effect="light">稳 {{ groupedResults.steady.length }}</el-tag>
        <el-tag type="success" effect="light">保 {{ groupedResults.safe.length }}</el-tag>
        <el-button
          type="primary"
          plain
          :loading="exportingScheme === schemeMeta.scheme_id"
          @click="emit('export-scheme', schemeMeta)"
        >
          导出推荐单
        </el-button>
        <el-button plain @click="emit('print-preview', schemeMeta)">打印预览</el-button>
      </div>
    </div>

    <div class="comparison-toolbar">
      <div class="comparison-copy">
        <strong>方案对比</strong>
        <p>
          和同一学生的历史方案做差异对比，直接看新增、移除和冲稳保分组变化。
        </p>
      </div>
      <div class="comparison-controls">
        <el-select
          v-model="compareSchemeIdModel"
          clearable
          filterable
          placeholder="选择历史方案对比"
        >
          <el-option
            v-for="item in compareHistoryOptions"
            :key="item.scheme_id"
            :label="`${item.scheme_name} · ${item.generated_at}`"
            :value="item.scheme_id"
          />
        </el-select>
      </div>
    </div>

    <div v-if="loadingScheme" class="comparison-placeholder">
      正在加载当前方案结果...
    </div>
    <div v-else-if="selectedSchemeError" class="comparison-state-card tone-danger">
      <strong>当前方案结果读取失败</strong>
      <p>{{ selectedSchemeError }}</p>
      <el-button type="danger" plain @click="emit('reload-scheme', schemeMeta)">重试读取</el-button>
    </div>
    <div v-else class="result-board-grid">
      <article
        v-for="column in resultColumns"
        :key="column.key"
        class="result-column"
        :class="column.key"
      >
        <header class="result-column-head">
          <div>
            <span class="result-pill">{{ column.label }}</span>
            <h4>{{ groupedResults[column.key].length }} 条结果</h4>
          </div>
          <span class="result-tip">{{ column.tip }}</span>
        </header>

        <div v-if="groupedResults[column.key].length" class="result-card-list">
          <article v-for="item in groupedResults[column.key]" :key="item.id" class="result-card">
            <div class="result-card-head">
              <div>
                <h5>{{ item.college_name }}</h5>
                <p>{{ item.major_name || "院校级推荐" }}</p>
              </div>
              <span class="ratio-badge">
                {{ item.ratio !== null && item.ratio !== undefined ? `比值 ${item.ratio}` : formatScoreBasis(item.score_basis) }}
              </span>
            </div>
            <dl class="detail-grid">
              <div>
                <dt>参考位次</dt>
                <dd>{{ item.reference_rank ?? "-" }}</dd>
              </div>
              <div>
                <dt>学生位次</dt>
                <dd>{{ item.student_rank ?? "-" }}</dd>
              </div>
              <div>
                <dt>依据</dt>
                <dd>{{ formatScoreBasis(item.score_basis) }}</dd>
              </div>
              <div>
                <dt>近年数据</dt>
                <dd>{{ formatReferenceYears(item.snapshot_json) }}</dd>
              </div>
              <div>
                <dt>参考口径</dt>
                <dd>{{ formatReferenceCopy(item) }}</dd>
              </div>
            </dl>
            <div v-if="hasCareerMatch(item)" class="career-match-card">
              <div class="career-match-head">
                <span class="career-match-label">职业匹配</span>
                <el-tag
                  size="small"
                  :type="careerMatchTagType(item.career_match_strength)"
                  effect="plain"
                >
                  {{ formatCareerMatchStrength(item.career_match_strength) }}
                </el-tag>
                <span v-if="item.career_match_score !== null && item.career_match_score !== undefined" class="career-match-score">
                  {{ item.career_match_score.toFixed(1) }}
                </span>
              </div>
              <p v-if="(item.matched_direction_names_json ?? []).length" class="career-match-copy">
                对应方向：{{ (item.matched_direction_names_json ?? []).join(" / ") }}
              </p>
              <p v-if="item.career_match_summary" class="career-match-copy">{{ item.career_match_summary }}</p>
              <div class="tag-cluster">
                <el-tag
                  v-if="item.requires_postgraduate_path"
                  size="small"
                  type="info"
                  effect="light"
                >
                  需关注读研路径
                </el-tag>
                <el-tag
                  v-if="item.requires_certificate_path"
                  size="small"
                  type="info"
                  effect="light"
                >
                  需关注资格证
                </el-tag>
                <el-tag
                  v-if="item.requires_long_training_path"
                  size="small"
                  type="info"
                  effect="light"
                >
                  需关注长培养周期
                </el-tag>
              </div>
            </div>
            <p v-if="formatBoundaryNotes(item).length" class="reference-copy">
              {{ formatBoundaryNotes(item).join(" ") }}
            </p>
            <p class="reason-copy">{{ formatRecommendationReason(item) }}</p>
            <div class="tag-cluster">
              <el-tag
                v-for="flag in item.risk_flags_json ?? []"
                :key="flag"
                size="small"
                type="warning"
                effect="light"
              >
                {{ riskFlagText(flag) }}
              </el-tag>
              <span v-if="!(item.risk_flags_json ?? []).length" class="muted-copy">无额外风险提示</span>
            </div>
          </article>
        </div>
        <el-empty
          v-else
          :description="`当前${column.label}分组暂无结果。可检查招生计划、录取数据和冲稳保阈值是否覆盖该学生。`"
        />
      </article>
    </div>

    <section v-if="!selectedSchemeError" class="comparison-panel">
      <div v-if="comparingScheme" class="comparison-placeholder">
        正在加载对比方案...
      </div>
      <div v-else-if="compareSchemeError" class="comparison-state-card tone-warning">
        <strong>历史方案对比读取失败</strong>
        <p>{{ compareSchemeError }}</p>
        <el-button
          v-if="compareSchemeId !== undefined"
          type="warning"
          plain
          @click="emit('compare-scheme-change', compareSchemeId)"
        >
          重试对比
        </el-button>
      </div>
      <template v-else-if="selectedCompareSchemeMeta && schemeComparison">
        <div class="comparison-summary-grid">
          <article class="comparison-summary-card tone-blue">
            <span>新增志愿</span>
            <strong>{{ schemeComparison.added.length }}</strong>
            <p>当前方案新增但旧方案没有的院校/专业。</p>
          </article>
          <article class="comparison-summary-card tone-slate">
            <span>移除志愿</span>
            <strong>{{ schemeComparison.removed.length }}</strong>
            <p>旧方案存在但当前方案已经移除的院校/专业。</p>
          </article>
          <article class="comparison-summary-card tone-amber">
            <span>分组变化</span>
            <strong>{{ schemeComparison.changed.length }}</strong>
            <p>同一院校/专业仍在，但冲稳保分组已变化。</p>
          </article>
          <article class="comparison-summary-card tone-green">
            <span>稳定保留</span>
            <strong>{{ schemeComparison.commonCount }}</strong>
            <p>院校/专业及分组均保持一致。</p>
          </article>
          <article v-if="schemeComparison.referenceSummary" class="comparison-summary-card tone-purple">
            <span>参考口径变化</span>
            <strong>{{ schemeComparison.referenceSummary.affectedCount }}</strong>
            <p>{{ schemeComparison.referenceSummary.summary }}</p>
          </article>
        </div>

        <div v-if="schemeComparison.referenceSummary" class="comparison-reference-note">
          {{ schemeComparison.referenceSummary.detail }}
        </div>

        <div class="comparison-delta-grid">
          <article
            v-for="item in schemeComparison.deltaByGroup"
            :key="item.key"
            class="comparison-delta-card"
          >
            <div>
              <span>{{ item.label }}</span>
              <strong>{{ item.current }}</strong>
            </div>
            <p>
              对比 {{ item.compare }} 条，
              <span :class="item.delta > 0 ? 'delta-up' : item.delta < 0 ? 'delta-down' : 'delta-flat'">
                {{ formatSignedDelta(item.delta) }}
              </span>
            </p>
          </article>
        </div>

        <div class="comparison-column-grid">
          <article class="comparison-column">
            <header>
              <h4>新增</h4>
              <span>{{ schemeComparison.added.length }} 条</span>
            </header>
            <div v-if="schemeComparison.added.length" class="comparison-item-list">
              <div v-for="item in schemeComparison.added" :key="item.key" class="comparison-item">
                <strong>{{ item.label }}</strong>
                <span>{{ resultGroupLabel(item.currentType) }}</span>
              </div>
            </div>
            <div v-else class="comparison-empty">当前方案没有新增志愿。</div>
          </article>

          <article class="comparison-column">
            <header>
              <h4>移除</h4>
              <span>{{ schemeComparison.removed.length }} 条</span>
            </header>
            <div v-if="schemeComparison.removed.length" class="comparison-item-list">
              <div v-for="item in schemeComparison.removed" :key="item.key" class="comparison-item">
                <strong>{{ item.label }}</strong>
                <span>{{ resultGroupLabel(item.compareType) }}</span>
              </div>
            </div>
            <div v-else class="comparison-empty">当前方案没有移除旧志愿。</div>
          </article>

          <article class="comparison-column">
            <header>
              <h4>分组变化</h4>
              <span>{{ schemeComparison.changed.length }} 条</span>
            </header>
            <div v-if="schemeComparison.changed.length" class="comparison-item-list">
              <div v-for="item in schemeComparison.changed" :key="item.key" class="comparison-item">
                <strong>{{ item.label }}</strong>
                <span>{{ resultGroupLabel(item.compareType) }} → {{ resultGroupLabel(item.currentType) }}</span>
              </div>
            </div>
            <div v-else class="comparison-empty">当前方案的分组结构没有变化。</div>
          </article>
        </div>
      </template>
      <div v-else class="comparison-placeholder">
        {{ compareHistoryOptions.length ? "选择同一学生的历史方案即可查看差异。" : "当前学生暂无可对比的历史方案。" }}
      </div>

      <div class="comparison-divider"></div>

      <div class="comparison-toolbar">
        <div class="comparison-copy">
          <strong>批量对照</strong>
          <p>
            一次选择多份历史方案，快速看每一版与当前方案之间的新增、移除和分组变化。
          </p>
        </div>
        <div class="comparison-controls">
          <el-select
            v-model="multiCompareSchemeIdsModel"
            multiple
            collapse-tags
            clearable
            filterable
            placeholder="选择多个历史方案"
          >
            <el-option
              v-for="item in compareHistoryOptions"
              :key="item.scheme_id"
              :label="`${item.scheme_name} · ${item.generated_at}`"
              :value="item.scheme_id"
            />
          </el-select>
        </div>
      </div>

      <div v-if="multiCompareError" class="comparison-state-card tone-warning top-spaced">
        <strong>批量对照有部分方案读取失败</strong>
        <p>{{ multiCompareError }}</p>
        <el-button
          v-if="multiCompareSchemeIds.length"
          type="warning"
          plain
          @click="emit('multi-compare-change', multiCompareSchemeIds)"
        >
          重试批量对照
        </el-button>
      </div>

      <el-table v-if="multiSchemeComparisonRows.length" :data="multiSchemeComparisonRows" stripe style="margin-top: 16px">
        <el-table-column label="方案" prop="scheme_name" min-width="180" />
        <el-table-column label="生成时间" prop="generated_at" min-width="170" />
        <el-table-column label="结果数" prop="result_count" width="80" />
        <el-table-column label="冲/稳/保" min-width="120">
          <template #default="{ row }">
            {{ row.challenge_count }} / {{ row.steady_count }} / {{ row.safe_count }}
          </template>
        </el-table-column>
        <el-table-column label="新增" prop="added_count" width="80" />
        <el-table-column label="移除" prop="removed_count" width="80" />
        <el-table-column label="变化" prop="changed_count" width="80" />
        <el-table-column label="参考口径变化" prop="reference_change_affected_count" width="108" />
        <el-table-column label="参考年变化" prop="reference_year_changed_count" width="100" />
        <el-table-column label="偏旧状态变化" prop="stale_reference_shift_count" width="116" />
        <el-table-column label="年变伴随分组变" prop="reference_year_group_shift_count" width="128" />
        <el-table-column label="稳定保留" prop="common_count" width="90" />
        <el-table-column label="差异总量" width="100">
          <template #default="{ row }">
            {{ row.added_count + row.removed_count + row.changed_count + row.reference_change_affected_count }}
          </template>
        </el-table-column>
      </el-table>
      <div v-else class="comparison-placeholder">
        {{ multiCompareSchemeIds.length ? (multiComparingSchemes ? "正在整理多方案差异..." : "当前所选方案暂无可展示差异。") : "选择多个历史方案后，这里会出现批量对照表。" }}
      </div>
    </section>

    <el-table v-if="!loadingScheme && !selectedSchemeError" :data="selectedSchemeResults" stripe style="margin-top: 18px">
      <el-table-column label="分组" width="90">
        <template #default="{ row }">
          {{ resultGroupLabel(row.result_type) }}
        </template>
      </el-table-column>
      <el-table-column label="院校" prop="college_name" min-width="180" />
      <el-table-column label="专业" prop="major_name" min-width="180" />
      <el-table-column label="参考位次" prop="reference_rank" width="100" />
      <el-table-column label="学生位次" prop="student_rank" width="100" />
      <el-table-column label="依据" width="120">
        <template #default="{ row }">
          {{ formatScoreBasis(row.score_basis) }}
        </template>
      </el-table-column>
      <el-table-column label="参考口径" min-width="220">
        <template #default="{ row }">
          {{ formatReferenceCopy(row) }}
        </template>
      </el-table-column>
      <el-table-column label="理由" min-width="320">
        <template #default="{ row }">
          {{ [formatRecommendationReason(row), ...formatBoundaryNotes(row)].filter(Boolean).join(" ") }}
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import {
  buildRecommendationSchemeComparison,
  type RecommendationSchemeComparisonSummary,
} from "./recommendationComparison";
import {
  buildRecommendationBoundaryNotes,
  buildRecommendationReferenceCopy,
  getRecommendationRiskFlagText,
} from "./recommendationCopy";
import type { RecommendationHistoryItem, RecommendationResult, ResultGroupKey } from "./types";

interface MultiSchemeComparisonRow {
  scheme_id: number;
  scheme_name: string;
  generated_at: string;
  result_count: number;
  challenge_count: number;
  steady_count: number;
  safe_count: number;
  added_count: number;
  removed_count: number;
  changed_count: number;
  reference_change_affected_count: number;
  reference_year_changed_count: number;
  stale_reference_shift_count: number;
  reference_year_group_shift_count: number;
  common_count: number;
}

const props = defineProps<{
  schemeMeta: RecommendationHistoryItem | null;
  compareHistoryOptions: RecommendationHistoryItem[];
  selectedSchemeResults: RecommendationResult[];
  loadingScheme: boolean;
  selectedSchemeError?: string | null;
  compareSchemeId?: number;
  comparingScheme: boolean;
  compareSchemeError?: string | null;
  compareSchemeResults: RecommendationResult[];
  multiCompareSchemeIds: number[];
  multiCompareError?: string | null;
  multiCompareSchemeResults: Record<number, RecommendationResult[]>;
  multiComparingSchemes: boolean;
  exportingScheme: number | null;
}>();

const emit = defineEmits<{
  "update:compareSchemeId": [value: number | undefined];
  "compare-scheme-change": [value: number | undefined];
  "update:multiCompareSchemeIds": [value: number[]];
  "multi-compare-change": [value: number[]];
  "export-scheme": [value: RecommendationHistoryItem];
  "print-preview": [value: RecommendationHistoryItem];
  "reload-scheme": [value: RecommendationHistoryItem];
}>();

const resultColumns: Array<{ key: ResultGroupKey; label: string; tip: string }> = [
  { key: "challenge", label: "冲刺", tip: "略高于当前位次，需接受风险" },
  { key: "steady", label: "稳妥", tip: "与历史基线接近，适合作为主干" },
  { key: "safe", label: "保底", tip: "优于历史基线较多，风险相对更低" },
];

const compareSchemeIdModel = computed<number | undefined>({
  get: () => props.compareSchemeId,
  set: (value) => {
    emit("update:compareSchemeId", value);
    emit("compare-scheme-change", value);
  },
});

const multiCompareSchemeIdsModel = computed<number[]>({
  get: () => props.multiCompareSchemeIds,
  set: (value) => {
    const nextValue = value.map((item) => Number(item));
    emit("update:multiCompareSchemeIds", nextValue);
    emit("multi-compare-change", nextValue);
  },
});

const groupedResults = computed<Record<ResultGroupKey, RecommendationResult[]>>(() => ({
  challenge: props.selectedSchemeResults.filter((item) => item.result_type === "challenge"),
  steady: props.selectedSchemeResults.filter((item) => item.result_type === "steady"),
  safe: props.selectedSchemeResults.filter((item) => item.result_type === "safe"),
}));

const selectedCompareSchemeMeta = computed(
  () => props.compareHistoryOptions.find((item) => item.scheme_id === props.compareSchemeId) ?? null,
);

const schemeComparison = computed<RecommendationSchemeComparisonSummary | null>(() => {
  if (!selectedCompareSchemeMeta.value) return null;
  return buildRecommendationSchemeComparison(props.selectedSchemeResults, props.compareSchemeResults, {
    currentTargetYear: props.schemeMeta?.target_year,
    compareTargetYear: selectedCompareSchemeMeta.value.target_year,
    currentProvince: props.schemeMeta?.province,
    compareProvince: selectedCompareSchemeMeta.value.province,
  });
});

const multiSchemeComparisonRows = computed<MultiSchemeComparisonRow[]>(() =>
  props.multiCompareSchemeIds
    .map((schemeId) => {
      const meta = props.compareHistoryOptions.find((item) => item.scheme_id === schemeId);
      const results = props.multiCompareSchemeResults[schemeId];
      if (!meta || !results) return null;
      const summary = buildRecommendationSchemeComparison(props.selectedSchemeResults, results, {
        currentTargetYear: props.schemeMeta?.target_year,
        compareTargetYear: meta.target_year,
        currentProvince: props.schemeMeta?.province,
        compareProvince: meta.province,
      });
      return {
        scheme_id: meta.scheme_id,
        scheme_name: meta.scheme_name,
        generated_at: meta.generated_at,
        result_count: meta.result_count,
        challenge_count: meta.challenge_count,
        steady_count: meta.steady_count,
        safe_count: meta.safe_count,
        added_count: summary.added.length,
        removed_count: summary.removed.length,
        changed_count: summary.changed.length,
        reference_change_affected_count: summary.referenceSummary?.affectedCount ?? 0,
        reference_year_changed_count: summary.referenceSummary?.changedCount ?? 0,
        stale_reference_shift_count: summary.referenceSummary?.staleShiftCount ?? 0,
        reference_year_group_shift_count: summary.referenceSummary?.groupShiftCount ?? 0,
        common_count: summary.commonCount,
      };
    })
    .filter((item): item is MultiSchemeComparisonRow => Boolean(item))
    .sort((left, right) => {
      const leftDiff = left.added_count + left.removed_count + left.changed_count + left.reference_change_affected_count;
      const rightDiff = right.added_count + right.removed_count + right.changed_count + right.reference_change_affected_count;
      return leftDiff - rightDiff;
    }),
);

function formatReferenceYears(snapshot?: Record<string, unknown> | null): string {
  const years = Array.isArray(snapshot?.reference_years) ? snapshot?.reference_years : [];
  return years.length ? years.join(" / ") : "-";
}

function formatRecommendationReason(item: RecommendationResult): string {
  return item.reason_text?.trim() || "暂无理由说明";
}

function formatReferenceCopy(item: RecommendationResult): string {
  return buildRecommendationReferenceCopy(item) ?? "-";
}

function formatBoundaryNotes(item: RecommendationResult): string[] {
  return buildRecommendationBoundaryNotes(item, props.schemeMeta?.target_year);
}

function resultGroupLabel(resultType?: ResultGroupKey): string {
  if (!resultType) return "-";
  return resultColumns.find((column) => column.key === resultType)?.label ?? resultType;
}

function hasCareerMatch(item: RecommendationResult): boolean {
  return Boolean(
    item.career_match_summary
      || (item.matched_direction_names_json ?? []).length
      || item.career_match_strength
      || item.requires_postgraduate_path
      || item.requires_certificate_path
      || item.requires_long_training_path,
  );
}

function formatScoreBasis(value: string): string {
  const mapping: Record<string, string> = {
    rank: "位次",
    score: "分数",
    comprehensive_score: "综合分",
    culture_score: "文化分",
    plan_only: "计划清单",
  };
  return mapping[value] ?? value;
}

function formatStudentType(value?: string | null): string {
  if (!value) return "-";
  const mapping: Record<string, string> = {
    general: "普通生",
    repeat: "复读生",
  };
  return mapping[value] ?? value;
}

function formatSignedDelta(value: number): string {
  if (value > 0) return `+${value}`;
  return String(value);
}

function formatCareerMatchStrength(value?: string | null): string {
  const mapping: Record<string, string> = {
    core: "核心相关",
    high: "强相关",
    medium: "一般相关",
    transferable: "可转化",
    pending: "待维护",
  };
  return value ? (mapping[value] ?? value) : "待维护";
}

function careerMatchTagType(value?: string | null): "success" | "warning" | "info" {
  if (value === "core" || value === "high") {
    return "success";
  }
  if (value === "medium" || value === "transferable") {
    return "warning";
  }
  return "info";
}

function riskFlagText(flag: string): string {
  return getRecommendationRiskFlagText(flag);
}
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.comparison-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin: 20px 0 0;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(247, 250, 253, 0.92);
  border: 1px solid rgba(124, 139, 154, 0.12);
}

.comparison-copy strong {
  color: #20364b;
  font-size: 15px;
}

.comparison-copy p {
  margin: 6px 0 0;
  color: #6a8094;
  line-height: 1.6;
}

.comparison-controls {
  width: min(320px, 100%);
}

.comparison-panel {
  margin-top: 18px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(245, 249, 252, 0.88);
  border: 1px solid rgba(126, 143, 158, 0.12);
}

.comparison-state-card {
  margin-top: 16px;
  padding: 18px 20px;
  border-radius: 18px;
}

.comparison-state-card strong {
  display: block;
  color: #1f3245;
}

.comparison-state-card p {
  margin: 8px 0 12px;
  color: #607385;
}

.top-spaced {
  margin-top: 16px;
}

.career-match-card {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(243, 248, 251, 0.92);
  border: 1px solid rgba(126, 143, 158, 0.12);
}

.career-match-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.career-match-label {
  font-size: 13px;
  font-weight: 700;
  color: #24384c;
}

.career-match-score {
  font-size: 12px;
  color: #6a8094;
}

.career-match-copy {
  margin: 8px 0 0;
  color: #496176;
  line-height: 1.6;
}

.comparison-divider {
  height: 1px;
  margin: 20px 0;
  background: rgba(126, 143, 158, 0.12);
}

.comparison-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.comparison-summary-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(123, 142, 161, 0.1);
}

.comparison-summary-card span {
  color: #6d8194;
  font-size: 13px;
}

.comparison-summary-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3348;
  font-size: 24px;
  font-weight: 760;
}

.comparison-summary-card p {
  margin: 8px 0 0;
  color: #73879b;
  font-size: 13px;
  line-height: 1.5;
}

.comparison-reference-note {
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(118, 136, 154, 0.12);
  background: rgba(255, 255, 255, 0.9);
  color: #5d7388;
  line-height: 1.6;
}

.comparison-delta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.comparison-delta-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(124, 140, 155, 0.12);
}

.comparison-delta-card div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.comparison-delta-card span {
  color: #6b8093;
  font-size: 13px;
}

.comparison-delta-card strong {
  color: #21364a;
  font-size: 24px;
}

.comparison-delta-card p {
  margin: 8px 0 0;
  color: #6d8195;
}

.comparison-column-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 16px;
}

.comparison-column {
  padding: 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(125, 141, 156, 0.12);
}

.comparison-column header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.comparison-column h4 {
  margin: 0;
  color: #1f3448;
  font-size: 16px;
}

.comparison-column header span {
  color: #6f8397;
  font-size: 13px;
}

.comparison-item-list {
  display: grid;
  gap: 10px;
}

.comparison-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 12px;
  border-radius: 16px;
  background: rgba(247, 250, 253, 0.96);
}

.comparison-item strong {
  color: #23374b;
  line-height: 1.5;
}

.comparison-item span {
  color: #688095;
  font-size: 13px;
  white-space: nowrap;
}

.comparison-empty,
.comparison-placeholder {
  color: #72869a;
  line-height: 1.7;
}

.tone-danger {
  border: 1px solid rgba(210, 63, 63, 0.22);
  background: rgba(255, 245, 245, 0.94);
}

.tone-warning {
  border: 1px solid rgba(201, 134, 32, 0.22);
  background: rgba(255, 250, 239, 0.95);
}

.tone-purple {
  border: 1px solid rgba(92, 107, 192, 0.18);
  background: rgba(244, 246, 255, 0.96);
}

.delta-up {
  color: #1f7a4b;
  font-weight: 700;
}

.delta-down {
  color: #b4523f;
  font-weight: 700;
}

.delta-flat {
  color: #6d8295;
  font-weight: 700;
}

.result-board-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.result-column {
  padding: 16px;
  border-radius: 22px;
  border: 1px solid rgba(118, 136, 154, 0.14);
  background: rgba(249, 252, 255, 0.92);
}

.result-column.challenge {
  box-shadow: inset 0 4px 0 rgba(210, 92, 73, 0.82);
}

.result-column.steady {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.88);
}

.result-column.safe {
  box-shadow: inset 0 4px 0 rgba(69, 141, 105, 0.8);
}

.result-column-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.result-column-head h4 {
  margin: 8px 0 0;
  font-size: 20px;
  color: #20364b;
}

.result-tip {
  color: #7a8d9d;
  font-size: 12px;
  line-height: 1.5;
  text-align: right;
}

.result-pill {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f6c98;
  font-size: 12px;
  font-weight: 700;
}

.result-card-list {
  display: grid;
  gap: 12px;
}

.result-card {
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(126, 142, 158, 0.12);
}

.result-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.result-card-head h5 {
  margin: 0;
  font-size: 16px;
  color: #21364a;
}

.result-card-head p {
  margin: 4px 0 0;
  color: #70859a;
  line-height: 1.5;
}

.ratio-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(237, 243, 248, 0.95);
  color: #52697f;
  font-size: 12px;
  white-space: nowrap;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
  margin: 14px 0 0;
}

.detail-grid dt {
  color: #7b8f9f;
  font-size: 12px;
}

.detail-grid dd {
  margin: 4px 0 0;
  color: #24384d;
  font-weight: 600;
}

.reason-copy {
  margin: 14px 0 12px;
  color: #5f768a;
  line-height: 1.6;
}

.tag-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.muted-copy {
  color: #7d8f9d;
  font-size: 13px;
}

@media (max-width: 1280px) {
  .result-board-grid,
  .comparison-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1080px) {
  .result-board-grid,
  .comparison-column-grid,
  .comparison-delta-grid,
  .comparison-summary-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .result-card-head,
  .result-column-head,
  .comparison-toolbar,
  .comparison-column header,
  .comparison-item,
  .comparison-delta-card div {
    flex-direction: column;
  }

  .result-tip {
    text-align: left;
  }

  .comparison-controls {
    width: 100%;
  }

  .comparison-item span {
    white-space: normal;
  }
}
</style>
