<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>推荐报告打印预览</strong>
        <p>建议在浏览器中选择“打印”或“另存为 PDF”。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载推荐报告...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="schemeMeta" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">高考志愿 / 推荐报告</div>
          <h1>{{ schemeMeta.scheme_name }}</h1>
          <p>{{ schemeMeta.student_name }} · {{ formatStudentType(schemeMeta.student_type) }} · {{ schemeMeta.province }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item">
            <span>方案生成</span>
            <strong>{{ schemeMeta.generated_at }}</strong>
          </div>
          <div class="print-summary-item">
            <span>结果总数</span>
            <strong>{{ results.length }}</strong>
          </div>
          <div class="print-summary-item">
            <span>冲 / 稳 / 保 / 关注</span>
            <strong>{{ groupedResults.challenge.length }} / {{ groupedResults.steady.length }} / {{ groupedResults.safe.length }} / {{ groupedResults.watch.length }}</strong>
          </div>
          <div class="print-summary-item">
            <span>目标年份</span>
            <strong>{{ schemeMeta.target_year ?? "-" }}</strong>
          </div>
          <div class="print-summary-item">
            <span>分数模式</span>
            <strong>{{ scoreInputSummary }}</strong>
          </div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head">
          <h2>职业意向摘要</h2>
        </div>
        <div class="print-meta-grid">
          <div class="print-meta-item">
            <span>目标方向</span>
            <strong>{{ targetDirectionSummary }}</strong>
          </div>
          <div class="print-meta-item">
            <span>可接受路径</span>
            <strong>{{ acceptedPathSummary }}</strong>
          </div>
        </div>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>分数输入摘要</h2>
        </div>
        <div class="print-meta-grid">
          <div class="print-meta-item">
            <span>模式</span>
            <strong>{{ scoreInputSummary }}</strong>
          </div>
          <div class="print-meta-item">
            <span>说明</span>
            <strong>{{ simulationNote }}</strong>
          </div>
        </div>
      </section>

      <section v-for="group in riskOverviewGroups" :key="group.key" class="print-section">
        <div class="print-section-head">
          <h2>{{ group.title }}</h2>
        </div>
        <PrintInsightCards :cards="group.cards" />
      </section>

      <section v-for="group in groupSections" :key="group.key" class="print-section">
        <div class="print-section-head">
          <h2>{{ group.label }}</h2>
          <span>{{ groupedResults[group.key].length }} 条</span>
        </div>
        <table v-if="groupedResults[group.key].length" class="print-table">
          <thead>
            <tr>
              <th>院校</th>
              <th>专业</th>
              <th>参考位次</th>
              <th>学生位次</th>
              <th>依据</th>
              <th>参考口径</th>
              <th>职业匹配</th>
              <th>对应方向</th>
              <th>路径提示</th>
              <th>职业说明</th>
              <th>理由</th>
              <th>风险提示</th>
              <th>章程/备注</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in groupedResults[group.key]" :key="item.id">
              <td>{{ item.college_name ?? "-" }}</td>
              <td>{{ item.major_name ?? "院校级推荐" }}</td>
              <td>{{ item.reference_rank ?? "-" }}</td>
              <td>{{ item.student_rank ?? "-" }}</td>
              <td>{{ item.ratio !== null && item.ratio !== undefined ? `比值 ${item.ratio}` : formatScoreBasis(item.score_basis) }}</td>
              <td>{{ formatReferenceCopy(item) }}</td>
              <td>{{ formatCareerMatch(item) }}</td>
              <td>{{ formatMatchedDirections(item) }}</td>
              <td>{{ formatPathHints(item) }}</td>
              <td>{{ item.career_match_summary || "-" }}</td>
              <td>{{ [formatRecommendationReason(item), ...formatBoundaryNotes(item)].filter(Boolean).join(" ") }}</td>
              <td>{{ formatRiskFlags(item.risk_flags_json) }}</td>
              <td>{{ formatChapterNotes(item.snapshot_json) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="print-empty">当前分组暂无结果。</div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "../api/client";
import {
  buildRecommendationBoundaryNotes,
  buildRecommendationReferenceCopy,
  buildRecommendationStaleReferenceNote,
  buildRecommendationSimulationNote,
  formatRecommendationRiskFlags,
} from "../components/recommendations/recommendationCopy";
import PrintInsightCards from "../components/reports/PrintInsightCards.vue";
import {
  buildRecommendationReportInsightCards,
  resolveRecommendationReportInsightContext,
} from "../components/reports/reportInsightRecommendation";
import { buildReportInsightGroups } from "../components/reports/reportInsightPresenter";
import type {
  RecommendationHistoryItem,
  RecommendationResult,
  ResultGroupKey,
  StudentCareerPreference,
} from "../components/recommendations/types";

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const schemeMeta = ref<RecommendationHistoryItem | null>(null);
const compareSchemeMeta = ref<RecommendationHistoryItem | null>(null);
const results = ref<RecommendationResult[]>([]);
const compareResults = ref<RecommendationResult[]>([]);
const studentCareerPreference = ref<StudentCareerPreference | null>(null);

const groupSections: Array<{ key: ResultGroupKey; label: string }> = [
  { key: "challenge", label: "冲刺志愿" },
  { key: "steady", label: "稳妥志愿" },
  { key: "safe", label: "保底志愿" },
  { key: "watch", label: "仅关注" },
];

const groupedResults = computed<Record<ResultGroupKey, RecommendationResult[]>>(() => ({
  challenge: results.value.filter((item) => item.result_type === "challenge"),
  steady: results.value.filter((item) => item.result_type === "steady"),
  safe: results.value.filter((item) => item.result_type === "safe"),
  watch: results.value.filter((item) => item.result_type === "watch"),
}));

const targetDirectionSummary = computed(() => {
  const segments: string[] = [];
  if (studentCareerPreference.value?.primary_direction_name) {
    segments.push(`首选：${studentCareerPreference.value.primary_direction_name}`);
  }
  if (studentCareerPreference.value?.secondary_direction_name) {
    segments.push(`次选：${studentCareerPreference.value.secondary_direction_name}`);
  }
  if (studentCareerPreference.value?.alternative_direction_name) {
    segments.push(`替代：${studentCareerPreference.value.alternative_direction_name}`);
  }
  if (segments.length) {
    return segments.join(" / ");
  }
  const matchedDirections: string[] = [];
  for (const item of results.value) {
    for (const direction of item.matched_direction_names_json ?? []) {
      if (direction && !matchedDirections.includes(direction)) {
        matchedDirections.push(direction);
      }
    }
  }
  return matchedDirections.join(" / ") || "未维护";
});

const acceptedPathSummary = computed(() => {
  const segments: string[] = [];
  if (studentCareerPreference.value?.accepts_postgraduate) {
    segments.push("接受读研路径");
  }
  if (studentCareerPreference.value?.accepts_public_service) {
    segments.push("接受考公/考编路径");
  }
  if (studentCareerPreference.value?.accepts_certificate) {
    segments.push("接受资格证路径");
  }
  if (studentCareerPreference.value?.accepts_long_training) {
    segments.push("接受长培养周期");
  }
  return segments.join(" / ") || "未维护";
});

const scoreInputSummary = computed(() => {
  if (schemeMeta.value?.score_input_label?.trim()) {
    return schemeMeta.value.score_input_label.trim();
  }
  const mapping: Record<string, string> = {
    actual_rank: "正式位次",
    actual_score: "正式分数",
    estimated_score: "预估分数",
    estimated_score_and_rank: "预估分数 + 预估位次",
    score_range: "分数区间",
    rank_range: "位次区间",
  };
  const key = schemeMeta.value?.score_input_mode;
  return (key ? mapping[key] : null) ?? "默认推荐链路";
});

const recommendationInsightContext = computed(() =>
  resolveRecommendationReportInsightContext(
    schemeMeta.value ? [schemeMeta.value, ...(compareSchemeMeta.value ? [compareSchemeMeta.value] : [])] : [],
    schemeMeta.value,
  ),
);

const simulationNote = computed(() =>
  buildRecommendationSimulationNote(recommendationInsightContext.value.currentOption),
);

const riskOverviewCards = computed(() =>
  buildRecommendationReportInsightCards(
    results.value,
    recommendationInsightContext.value.currentOption,
    compareResults.value,
    recommendationInsightContext.value.compareOption,
  ),
);
const riskOverviewGroups = computed(() =>
  buildReportInsightGroups("recommendation_summary", riskOverviewCards.value),
);

function formatStudentType(value?: string | null): string {
  if (!value) return "-";
  const mapping: Record<string, string> = {
    general: "普通生",
    repeat: "复读生",
  };
  return mapping[value] ?? value;
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

function formatRiskFlags(flags?: string[] | null): string {
  return formatRecommendationRiskFlags(flags);
}

function formatRecommendationReason(item: RecommendationResult): string {
  const segments = [item.reason_text || "-"];
  const staleReferenceNote = buildRecommendationStaleReferenceNote(item.snapshot_json ?? null, schemeMeta.value?.target_year);
  if (staleReferenceNote) {
    segments.push(staleReferenceNote);
  }
  return segments.join(" ");
}

function formatReferenceCopy(item: RecommendationResult): string {
  return buildRecommendationReferenceCopy(item) ?? "-";
}

function formatBoundaryNotes(item: RecommendationResult): string[] {
  return buildRecommendationBoundaryNotes(item, schemeMeta.value?.target_year);
}

function formatChapterNotes(snapshot?: Record<string, unknown> | null): string {
  if (!snapshot) return "-";
  const segments: string[] = [];
  if (typeof snapshot.chapter_url === "string" && snapshot.chapter_url.trim()) {
    segments.push(`章程：${snapshot.chapter_url.trim()}`);
  }
  if (typeof snapshot.chapter_campus_note === "string" && snapshot.chapter_campus_note.trim()) {
    segments.push(`校区：${snapshot.chapter_campus_note.trim()}`);
  }
  if (typeof snapshot.chapter_other_risk_note === "string" && snapshot.chapter_other_risk_note.trim()) {
    segments.push(`备注：${snapshot.chapter_other_risk_note.trim()}`);
  }
  if (typeof snapshot.chapter_language_requirement === "string" && snapshot.chapter_language_requirement.trim()) {
    segments.push(`语言：${snapshot.chapter_language_requirement.trim()}`);
  }
  if (typeof snapshot.chapter_single_subject_requirement === "string" && snapshot.chapter_single_subject_requirement.trim()) {
    segments.push(`单科：${snapshot.chapter_single_subject_requirement.trim()}`);
  }
  if (typeof snapshot.chapter_gender_requirement === "string" && snapshot.chapter_gender_requirement.trim()) {
    segments.push(`性别：${snapshot.chapter_gender_requirement.trim()}`);
  }
  if (typeof snapshot.chapter_height_requirement === "string" && snapshot.chapter_height_requirement.trim()) {
    segments.push(`身高：${snapshot.chapter_height_requirement.trim()}`);
  }
  if (typeof snapshot.chapter_vision_requirement === "string" && snapshot.chapter_vision_requirement.trim()) {
    segments.push(`视力：${snapshot.chapter_vision_requirement.trim()}`);
  }
  if (typeof snapshot.chapter_color_vision_requirement === "string" && snapshot.chapter_color_vision_requirement.trim()) {
    segments.push(`色觉：${snapshot.chapter_color_vision_requirement.trim()}`);
  }
  if (typeof snapshot.chapter_physical_exam_requirement === "string" && snapshot.chapter_physical_exam_requirement.trim()) {
    segments.push(`体检：${snapshot.chapter_physical_exam_requirement.trim()}`);
  }
  return segments.join(" / ") || "-";
}

function formatCareerMatch(item: RecommendationResult): string {
  const mapping: Record<string, string> = {
    core: "核心相关",
    high: "强相关",
    medium: "一般相关",
    transferable: "可转化",
    pending: "待维护",
  };
  const label = item.career_match_strength ? (mapping[item.career_match_strength] ?? item.career_match_strength) : "待维护";
  if (item.career_match_score !== null && item.career_match_score !== undefined) {
    return `${label} (${item.career_match_score.toFixed(1)})`;
  }
  return label;
}

function formatMatchedDirections(item: RecommendationResult): string {
  return (item.matched_direction_names_json ?? []).join(" / ") || "-";
}

function formatPathHints(item: RecommendationResult): string {
  const hints: string[] = [];
  if (item.requires_postgraduate_path) {
    hints.push("读研");
  }
  if (item.requires_certificate_path) {
    hints.push("资格证");
  }
  if (item.requires_long_training_path) {
    hints.push("长培养周期");
  }
  return hints.join(" / ") || "-";
}

function goBack(): void {
  window.history.back();
}

function printPage(): void {
  window.print();
}

async function loadPrintData(): Promise<void> {
  const studentId = Number(route.params.studentId);
  const schemeId = Number(route.params.schemeId);
  if (!studentId || !schemeId) {
    errorMessage.value = "打印参数无效";
    return;
  }

  const history = await apiRequest<RecommendationHistoryItem[]>(`/api/recommendations/history?student_id=${studentId}`);
  schemeMeta.value = history.find((item) => item.scheme_id === schemeId) ?? null;
  if (!schemeMeta.value) {
    errorMessage.value = "未找到对应推荐方案";
    return;
  }
  compareSchemeMeta.value = resolveRecommendationReportInsightContext(history, schemeMeta.value).compareScheme;

  const [currentResults, nextCompareResults, preference] = await Promise.all([
    apiRequest<RecommendationResult[]>(
      `/api/recommendations/history/${schemeId}/results?student_id=${studentId}`,
    ),
    compareSchemeMeta.value
      ? apiRequest<RecommendationResult[]>(
        `/api/recommendations/history/${compareSchemeMeta.value.scheme_id}/results?student_id=${studentId}`,
      ).catch(() => {
        compareSchemeMeta.value = null;
        return [] as RecommendationResult[];
      })
      : Promise.resolve([] as RecommendationResult[]),
    apiRequest<StudentCareerPreference | null>(`/api/students/${studentId}/career-preference`),
  ]);
  results.value = currentResults;
  compareResults.value = nextCompareResults;
  studentCareerPreference.value = preference;
}

onMounted(async () => {
  try {
    await loadPrintData();
  } catch (error) {
    errorMessage.value = (error as Error).message;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.print-shell {
  min-height: 100vh;
  padding: 24px;
  background: #eef3f7;
  color: #1f3348;
}

.print-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  max-width: 1080px;
  margin: 0 auto 20px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(123, 141, 158, 0.14);
}

.print-toolbar p {
  margin: 6px 0 0;
  color: #6d8194;
}

.print-page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 28px;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(31, 51, 72, 0.08);
}

.print-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(124, 141, 156, 0.16);
}

.print-eyebrow {
  color: #6b8093;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.print-header h1 {
  margin: 10px 0 0;
  font-size: 32px;
}

.print-header p {
  margin: 8px 0 0;
  color: #62778a;
}

.print-summary-grid {
  display: grid;
  gap: 12px;
  min-width: 280px;
}

.print-summary-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(245, 249, 252, 0.92);
  border: 1px solid rgba(123, 141, 158, 0.12);
}

.print-summary-item span {
  color: #6e8397;
  font-size: 12px;
}

.print-summary-item strong {
  display: block;
  margin-top: 8px;
  font-size: 18px;
}

.print-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.print-meta-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(245, 249, 252, 0.92);
  border: 1px solid rgba(123, 141, 158, 0.12);
}

.print-meta-item span {
  color: #6e8397;
  font-size: 12px;
}

.print-meta-item strong {
  display: block;
  margin-top: 8px;
  font-size: 16px;
  line-height: 1.6;
}

.print-section {
  margin-top: 24px;
}

.print-section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.print-section-head h2 {
  margin: 0;
  font-size: 20px;
}

.print-section-head span {
  color: #6d8194;
  font-size: 13px;
}

.print-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.print-table th,
.print-table td {
  padding: 10px 12px;
  border: 1px solid rgba(123, 141, 158, 0.2);
  text-align: left;
  vertical-align: top;
  line-height: 1.55;
}

.print-table th {
  background: rgba(243, 247, 250, 0.96);
}

.print-placeholder,
.print-empty {
  color: #6d8194;
  line-height: 1.7;
}

.print-placeholder.danger {
  color: #b24b3b;
}

@media print {
  .print-shell {
    padding: 0;
    background: #ffffff;
  }

  .print-toolbar {
    display: none;
  }

  .print-page {
    max-width: none;
    margin: 0;
    padding: 0;
    border-radius: 0;
    box-shadow: none;
  }
}
</style>
