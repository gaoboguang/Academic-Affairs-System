<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>志愿草稿打印预览</strong>
        <p>建议先确认草稿排序和规则说明，再在浏览器中打印或另存为 PDF。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载志愿草稿...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="draft" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">高考志愿 / 志愿草稿</div>
          <h1>{{ draft.name }}</h1>
          <p>{{ draft.student_name }} · {{ draft.batch || "未设批次" }} · {{ draft.exam_mode || "未设模式" }}</p>
          <p>{{ draft.exam_name }} · {{ draft.province }} · {{ draft.target_year }} 年</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item">
            <span>志愿数量</span>
            <strong>{{ draft.items.length }}</strong>
          </div>
          <div class="print-summary-item">
            <span>批次 / 模式</span>
            <strong>{{ draft.batch || "未设批次" }} / {{ draft.exam_mode || "未设模式" }}</strong>
          </div>
          <div class="print-summary-item">
            <span>更新时间</span>
            <strong>{{ draft.updated_at }}</strong>
          </div>
          <div class="print-summary-item">
            <span>分数模式</span>
            <strong>{{ formatScoreInputMode(draft.score_input_mode) }}</strong>
          </div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head">
          <h2>筛选条件</h2>
        </div>
        <div class="print-meta-grid">
          <div class="print-meta-item">
            <span>目标地区</span>
            <strong>{{ draft.target_regions_json.length ? draft.target_regions_json.join(" / ") : "未设置" }}</strong>
          </div>
          <div class="print-meta-item">
            <span>院校层级</span>
            <strong>{{ draft.school_level_tags_json.length ? draft.school_level_tags_json.join(" / ") : "未设置" }}</strong>
          </div>
          <div class="print-meta-item">
            <span>专业关键词</span>
            <strong>{{ draft.major_keyword || "未设置" }}</strong>
          </div>
          <div class="print-meta-item">
            <span>选科组合</span>
            <strong>{{ draft.subject_combination || "未设置" }}</strong>
          </div>
          <div class="print-meta-item">
            <span>分数模式</span>
            <strong>{{ formatScoreInputMode(draft.score_input_mode) }}</strong>
          </div>
          <div class="print-meta-item">
            <span>模拟说明</span>
            <strong>{{ formatSimulationNote(draft) }}</strong>
          </div>
        </div>
      </section>

      <section v-if="draft.selected_rule" class="print-section">
        <div class="print-section-head">
          <h2>规则快照</h2>
        </div>
        <div class="print-meta-grid">
          <div class="print-meta-item">
            <span>规则批次</span>
            <strong>{{ draft.selected_rule.batch }}</strong>
          </div>
          <div class="print-meta-item">
            <span>志愿单位</span>
            <strong>{{ draft.selected_rule.volunteer_unit_type }}</strong>
          </div>
          <div class="print-meta-item">
            <span>志愿上限</span>
            <strong>{{ draft.selected_rule.volunteer_limit }}</strong>
          </div>
          <div class="print-meta-item">
            <span>调剂</span>
            <strong>{{ draft.selected_rule.allow_adjustment ? "允许" : "不允许" }}</strong>
          </div>
        </div>
      </section>

      <section v-for="group in draftInsightGroups" :key="group.key" class="print-section">
        <div class="print-section-head">
          <h2>{{ group.title }}</h2>
        </div>
        <PrintInsightCards :cards="group.cards" />
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>志愿表</h2>
          <span>{{ draft.items.length }} 条</span>
        </div>
        <table v-if="draft.items.length" class="print-table">
          <thead>
            <tr>
              <th>顺序</th>
              <th>分层</th>
              <th>院校</th>
              <th>院校代码</th>
              <th>专业</th>
              <th>专业代码</th>
              <th>专业组</th>
              <th>计划数</th>
              <th>参考位次</th>
              <th>依据</th>
              <th>风险提示</th>
              <th>章程/备注</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in draft.items" :key="item.id">
              <td>{{ item.order }}</td>
              <td>{{ resultTypeLabel(item.candidate.result_type) }}</td>
              <td>{{ item.candidate.college_name }}</td>
              <td>{{ item.candidate.college_code_snapshot || "-" }}</td>
              <td>{{ item.candidate.major_name || item.candidate.major_group_code || "院校级计划" }}</td>
              <td>{{ item.candidate.major_code_snapshot || "-" }}</td>
              <td>{{ item.candidate.major_group_code || "-" }}</td>
              <td>{{ item.candidate.plan_count }}</td>
              <td>{{ item.candidate.reference_rank ?? item.candidate.latest_min_rank ?? "-" }}</td>
              <td>{{ formatScoreBasis(item.candidate.score_basis) }}</td>
              <td>{{ formatRiskFlags(item.candidate.risk_flags_json) }}</td>
              <td>{{ formatChapterNotes(item.candidate) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="print-empty">当前草稿暂无志愿。</div>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>说明</h2>
        </div>
        <div class="print-notes">
          <p v-if="draft.note">{{ draft.note }}</p>
          <p v-else>当前草稿未填写补充说明。</p>
        </div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "../api/client";
import { formatRecommendationRiskFlags } from "../components/recommendations/recommendationCopy";
import PrintInsightCards from "../components/reports/PrintInsightCards.vue";
import { buildReportInsightGroups } from "../components/reports/reportInsightPresenter";
import {
  buildVolunteerDraftReportInsightCards,
} from "../components/reports/reportInsights";
import type { VolunteerDraftDetail } from "../components/recommendations/types";

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const draft = ref<VolunteerDraftDetail | null>(null);
const draftInsightCards = computed(() =>
  draft.value
    ? buildVolunteerDraftReportInsightCards({
        rules: draft.value.applicable_rules ?? [],
        selectedRule: draft.value.selected_rule ?? null,
        draftItems: draft.value.items,
        ruleAlerts: draft.value.rule_alerts ?? [],
      })
    : [],
);
const draftInsightGroups = computed(() => buildReportInsightGroups("volunteer_draft_summary", draftInsightCards.value));

function goBack(): void {
  window.history.back();
}

function printPage(): void {
  window.print();
}

function resultTypeLabel(value: string): string {
  const mapping: Record<string, string> = {
    challenge: "冲刺",
    steady: "稳妥",
    safe: "保底",
  };
  return mapping[value] ?? value;
}

function formatScoreBasis(value: string): string {
  const mapping: Record<string, string> = {
    rank: "位次",
    score: "分数",
    comprehensive_score: "综合分",
  };
  return mapping[value] ?? value;
}

function formatRiskFlags(flags?: string[] | null): string {
  return formatRecommendationRiskFlags(flags);
}

function formatChapterNotes(candidate: VolunteerDraftDetail["items"][number]["candidate"]): string {
  const segments: string[] = [];
  if (candidate.chapter_url?.trim()) {
    segments.push(`章程：${candidate.chapter_url.trim()}`);
  }
  if (candidate.chapter_campus_note?.trim()) {
    segments.push(`校区：${candidate.chapter_campus_note.trim()}`);
  }
  if (candidate.chapter_other_risk_note?.trim()) {
    segments.push(`备注：${candidate.chapter_other_risk_note.trim()}`);
  }
  if (candidate.chapter_language_requirement?.trim()) {
    segments.push(`语言：${candidate.chapter_language_requirement.trim()}`);
  }
  if (candidate.chapter_single_subject_requirement?.trim()) {
    segments.push(`单科：${candidate.chapter_single_subject_requirement.trim()}`);
  }
  if (candidate.chapter_gender_requirement?.trim()) {
    segments.push(`性别：${candidate.chapter_gender_requirement.trim()}`);
  }
  if (candidate.chapter_height_requirement?.trim()) {
    segments.push(`身高：${candidate.chapter_height_requirement.trim()}`);
  }
  if (candidate.chapter_vision_requirement?.trim()) {
    segments.push(`视力：${candidate.chapter_vision_requirement.trim()}`);
  }
  if (candidate.chapter_color_vision_requirement?.trim()) {
    segments.push(`色觉：${candidate.chapter_color_vision_requirement.trim()}`);
  }
  if (candidate.chapter_physical_exam_requirement?.trim()) {
    segments.push(`体检：${candidate.chapter_physical_exam_requirement.trim()}`);
  }
  return segments.join(" / ") || "-";
}

function formatScoreInputMode(value: string): string {
  const mapping: Record<string, string> = {
    actual_rank: "正式位次",
    actual_score: "正式分数",
    estimated_score: "预估分数",
    estimated_score_and_rank: "预估分数 + 预估位次",
    score_range: "分数区间",
    rank_range: "位次区间",
  };
  return mapping[value] ?? value;
}

function formatSimulationNote(item: VolunteerDraftDetail): string {
  const hints: string[] = [];
  if (item.reference_exam_name?.trim()) {
    hints.push(`参考考试：${item.reference_exam_name.trim()}`);
  }
  if (item.use_historical_mapping) {
    hints.push("已启用历史映射");
  }
  return hints.join(" / ") || "当前按默认链路保存";
}

async function loadPrintData(): Promise<void> {
  const draftId = Number(route.params.draftId);
  if (!draftId) {
    errorMessage.value = "打印参数无效";
    return;
  }
  draft.value = await apiRequest<VolunteerDraftDetail>(`/api/recommendations/volunteer-drafts/${draftId}`);
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

.print-summary-grid,
.print-meta-grid {
  display: grid;
  gap: 12px;
}

.print-summary-grid {
  min-width: 280px;
}

.print-meta-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.print-summary-item,
.print-meta-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(245, 249, 252, 0.92);
  border: 1px solid rgba(123, 141, 158, 0.12);
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
  font-size: 18px;
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

.print-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.print-table th,
.print-table td {
  padding: 10px 12px;
  border: 1px solid rgba(126, 143, 158, 0.18);
  text-align: left;
  vertical-align: top;
}

.print-table th {
  background: rgba(242, 247, 251, 0.92);
  color: #43596d;
}

.print-notes {
  padding: 16px;
  border-radius: 16px;
  background: rgba(247, 250, 253, 0.92);
  border: 1px solid rgba(126, 143, 158, 0.12);
  color: #4f6578;
  line-height: 1.7;
}

.print-placeholder,
.print-empty {
  max-width: 1080px;
  margin: 0 auto;
  padding: 36px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.94);
  color: #5f7387;
  text-align: center;
}

.print-placeholder.danger {
  color: #b42318;
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
    padding: 0;
    border-radius: 0;
    box-shadow: none;
  }

  .print-meta-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
