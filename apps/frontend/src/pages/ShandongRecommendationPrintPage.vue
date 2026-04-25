<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>山东普通类冲稳保推荐报告</strong>
        <p>建议在浏览器中选择“打印”或“另存为 PDF”。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="result" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">山东普通类 / 冲稳保推荐</div>
          <h1>{{ reportTitle }}</h1>
          <p>{{ result.student_name || "未命名学生" }} · {{ result.province }} · {{ result.target_year }} 年</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item">
            <span>输入来源</span>
            <strong>{{ formatShandongSourceMode(result.source_mode) }}</strong>
          </div>
          <div class="print-summary-item">
            <span>预估分数</span>
            <strong>{{ formatNullableNumber(result.predicted_score) }}</strong>
          </div>
          <div class="print-summary-item">
            <span>预估位次</span>
            <strong>{{ formatNullableNumber(result.predicted_rank) }}</strong>
          </div>
          <div class="print-summary-item">
            <span>冲 / 稳 / 保 / 关注</span>
            <strong>{{ result.summary.rush_count }} / {{ result.summary.stable_count }} / {{ result.summary.safe_count }} / {{ result.summary.watch_count }}</strong>
          </div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head">
          <h2>输入与数据提示</h2>
        </div>
        <div class="print-meta-grid">
          <div class="print-meta-item">
            <span>位次区间</span>
            <strong>{{ rankRangeText }}</strong>
          </div>
          <div class="print-meta-item">
            <span>风险偏好</span>
            <strong>{{ formatShandongRiskPreference(result.risk_preference) }}</strong>
          </div>
          <div class="print-meta-item">
            <span>数据年份</span>
            <strong>{{ formatYearList(result.data_years) }}</strong>
          </div>
          <div class="print-meta-item">
            <span>选科不符已排除</span>
            <strong>{{ result.summary.excluded_subject_mismatch_count }}</strong>
          </div>
        </div>
        <div class="notice-box">
          <strong>2026 数据提示</strong>
          <p>{{ SHANDONG_2026_DATA_NOTICE }}</p>
        </div>
        <ul v-if="result.input_notes.length || dataHealthGaps.length" class="print-note-list">
          <li v-for="note in result.input_notes" :key="`input-${note}`">{{ note }}</li>
          <li v-for="gap in dataHealthGaps" :key="`gap-${gap}`">{{ gap }}</li>
        </ul>
      </section>

      <section v-for="group in resultGroups" :key="group.key" class="print-section">
        <div class="print-section-head">
          <h2>{{ group.label }}列表</h2>
          <span>{{ group.items.length }} 条</span>
        </div>
        <table v-if="group.items.length" class="print-table">
          <thead>
            <tr>
              <th>院校 / 专业</th>
              <th>参考位次</th>
              <th>最近分 / 位次</th>
              <th>位次差</th>
              <th>计划变化</th>
              <th>选科要求</th>
              <th>风险说明</th>
              <th>来源</th>
              <th>推荐理由</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in group.items" :key="`${group.key}-${item.college_id}-${item.major_id ?? 'college'}`">
              <td>
                <strong>{{ item.college_name }}</strong>
                <span>{{ item.major_name || "院校级计划" }}</span>
              </td>
              <td>{{ formatNullableNumber(getShandongReferenceRank(item)) }}</td>
              <td>{{ formatNullableNumber(getShandongLatestMinScore(item)) }} / {{ formatNullableNumber(getShandongLatestMinRank(item)) }}</td>
              <td>{{ formatNullableNumber(item.rank_margin) }} 位，{{ formatPercent(item.rank_margin_ratio) }}</td>
              <td>{{ getShandongPlanChangeSummary(item) }}</td>
              <td>{{ item.subject_requirement || "不限或待补" }}</td>
              <td>{{ formatRiskList(item.risk_flags) }}</td>
              <td>{{ formatShandongSourceDocumentIds(item.source_document_ids) }}</td>
              <td>{{ item.explanation_text }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="print-empty">当前分组暂无结果。</div>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>数据来源说明</h2>
        </div>
        <p class="source-copy">
          本报告保留候选行关联的来源编号；来源编号对应本地官方来源登记记录。当前结果主要使用
          {{ formatYearList(result.data_years) }} 山东普通类历史投档数据，正式填报前仍需按最新招生计划和高校章程复核。
        </p>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import {
  SHANDONG_2026_DATA_NOTICE,
  buildShandongRecommendationReportName,
  buildShandongResultGroups,
  formatNullableNumber,
  formatPercent,
  formatShandongRiskFlag,
  formatShandongRiskPreference,
  formatShandongSourceDocumentIds,
  formatShandongSourceMode,
  formatYearList,
  getShandongLatestMinRank,
  getShandongLatestMinScore,
  getShandongPlanChangeSummary,
  getShandongReferenceRank,
  type ShandongRecommendationPrintPayload,
} from "../components/recommendations/shandongRecommendationWorkbench";

const route = useRoute();
const payload = ref<ShandongRecommendationPrintPayload | null>(null);
const errorMessage = ref("");

const result = computed(() => payload.value?.result ?? null);
const dataHealthGaps = computed(() => payload.value?.data_health_gaps ?? []);
const reportTitle = computed(() => (result.value ? buildShandongRecommendationReportName(result.value) : "山东普通类冲稳保推荐报告"));
const resultGroups = computed(() => buildShandongResultGroups(result.value ?? null));
const rankRangeText = computed(() => {
  if (!result.value) return "-";
  const low = result.value.rank_range_low;
  const high = result.value.rank_range_high;
  if (low === undefined && high === undefined) return "-";
  if (low === high) return formatNullableNumber(low);
  return `${formatNullableNumber(low)} - ${formatNullableNumber(high)}`;
});

function formatRiskList(flags: string[]): string {
  if (!flags.length) return "-";
  return flags.map((flag) => formatShandongRiskFlag(flag)).join(" / ");
}

function goBack(): void {
  window.history.back();
}

function printPage(): void {
  window.print();
}

onMounted(() => {
  const storageKey = String(route.params.storageKey || "");
  if (!storageKey) {
    errorMessage.value = "打印参数无效，请回到山东普通类推荐工作台重新打开打印报告。";
    return;
  }
  const raw = window.localStorage.getItem(storageKey);
  if (!raw) {
    errorMessage.value = "未找到本次推荐报告数据，请回到山东普通类推荐工作台重新生成报告。";
    return;
  }
  try {
    payload.value = JSON.parse(raw) as ShandongRecommendationPrintPayload;
  } catch {
    errorMessage.value = "本次推荐报告数据无法读取，请回到山东普通类推荐工作台重新生成报告。";
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
  max-width: 1120px;
  margin: 0 auto 20px;
  padding: 16px 18px;
  border: 1px solid rgba(123, 141, 158, 0.14);
  border-radius: 8px;
  background: #ffffff;
}

.print-toolbar p {
  margin: 6px 0 0;
  color: #6d8194;
}

.print-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 28px;
  border-radius: 8px;
  background: #ffffff;
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
}

.print-header h1 {
  margin: 10px 0 0;
  font-size: 30px;
}

.print-header p {
  margin: 8px 0 0;
  color: #62778a;
}

.print-summary-grid,
.print-meta-grid {
  display: grid;
  gap: 12px;
}

.print-summary-grid {
  min-width: 300px;
}

.print-meta-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.print-summary-item,
.print-meta-item,
.notice-box {
  padding: 14px 16px;
  border: 1px solid rgba(123, 141, 158, 0.12);
  border-radius: 8px;
  background: #f7fafc;
}

.print-summary-item span,
.print-meta-item span {
  color: #6e8397;
  font-size: 12px;
}

.print-summary-item strong,
.print-meta-item strong {
  display: block;
  margin-top: 8px;
  font-size: 16px;
  line-height: 1.55;
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

.print-section-head span,
.source-copy,
.print-note-list {
  color: #6d8194;
}

.notice-box {
  margin-top: 12px;
}

.notice-box p {
  margin: 8px 0 0;
  line-height: 1.65;
}

.print-note-list {
  margin: 12px 0 0;
  padding-left: 18px;
  line-height: 1.7;
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
  word-break: break-word;
}

.print-table th {
  background: #f3f7fa;
}

.print-table td span {
  display: block;
  margin-top: 4px;
  color: #6d8194;
}

.print-placeholder,
.print-empty {
  max-width: 1120px;
  margin: 0 auto;
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

  .print-section {
    break-inside: avoid;
  }
}
</style>
