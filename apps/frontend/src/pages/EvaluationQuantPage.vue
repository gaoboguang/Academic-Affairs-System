<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">教学评价 / 评教与量化</div>
        <h2 class="page-title">评教与班主任量化</h2>
        <p class="page-subtitle">
          统一维护评教模板、导入批次、量化规则版本、月度记录和学期汇总，让评价结果和过程依据放在同一条链路里。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>当前学期</strong>{{ currentSemesterLabel }}</span>
          <span class="page-chip"><strong>评教批次</strong>{{ currentBatchLabel }}</span>
          <span class="page-chip"><strong>量化规则</strong>{{ currentRuleVersionLabel }}</span>
          <span class="page-chip"><strong>量化记录</strong>{{ quantRecords.length }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="downloadEvaluationTemplate">评教模板下载</el-button>
        <el-button @click="downloadQuantTemplate">量化模板下载</el-button>
        <el-button type="primary" @click="activeTab = 'evaluation'">进入评教</el-button>
      </div>
    </header>

    <section class="metric-grid">
      <div class="soft-card stat-card">
        <div class="metric-label">评教模板</div>
        <div class="metric-value">{{ templates.length }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">评教批次</div>
        <div class="metric-value">{{ batches.length }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">量化规则版本</div>
        <div class="metric-value">{{ ruleVersions.length }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">量化记录</div>
        <div class="metric-value">{{ quantRecords.length }}</div>
      </div>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head compact">
        <div>
          <h3>当前操作提示</h3>
          <p>先确认模板、批次和规则版本，再进入教师详情、量化记录或汇总查询。</p>
        </div>
      </div>
      <div class="guide-grid">
        <article v-for="item in guideCards" :key="item.label" class="guide-card" :class="item.tone">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.help }}</p>
        </article>
      </div>
    </section>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="评教系统" name="evaluation">
        <EvaluationTemplatesPanel
          :templates="templates"
          :batches="batches"
          :evaluation-import-result="evaluationImportResult"
          :evaluation-import-form="evaluationImportForm"
          :semesters="referenceStore.semesters"
          @reload-templates="loadTemplates"
          @open-create-template="openCreateTemplate"
          @edit-template="openEditTemplate"
          @import-file="handleEvaluationImport"
          @reload-batches="loadBatches"
          @select-batch="selectBatch"
        />

        <EvaluationBatchOverviewPanel
          :evaluation-overview="evaluationOverview"
          :selected-compare-batch-id="selectedCompareBatchId"
          :compare-batch-options="compareBatchOptions"
          :evaluation-comparison="evaluationComparison"
          :evaluation-detail="evaluationDetail"
          :evaluation-teacher-trend="evaluationTeacherTrend"
          :trend-delta-score="trendDeltaScore"
          :trend-rank-delta="trendRankDelta"
          :trend-peak-score="trendPeakScore"
          @change-compare-batch="handleCompareBatchChange"
          @load-teacher-detail="loadTeacherDetail"
        />
      </el-tab-pane>

      <el-tab-pane label="班主任量化" name="quant">
        <div class="page-shell">
          <QuantRulesPanel
            :rule-versions="ruleVersions"
            :selected-rule-version-id="selectedRuleVersionId"
            :selected-rule-version-meta="selectedRuleVersionMeta"
            :rule-item-rows="ruleItemRows"
            :saving-rule-items="savingRuleItems"
            @reload-rule-versions="loadRuleVersions"
            @open-create-rule-version="openCreateRuleVersion"
            @select-rule-version="selectRuleVersion"
            @add-rule-item-row="addRuleItemRow"
            @save-rule-items="saveRuleItems"
            @remove-rule-item-row="removeRuleItemRow"
          />

          <QuantRecordsPanel
            :quant-filters="quantFilters"
            :semesters="referenceStore.semesters"
            :teacher-options="teacherOptions"
            :rule-versions="ruleVersions"
            :quant-summary="quantSummary"
            :quant-records="quantRecords"
            @reload="reloadQuantData"
            @open-create-quant-record="openCreateQuantRecord"
            @reset-filters="resetQuantFilters"
            @edit-quant-record="openEditQuantRecord"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <EvaluationTemplateDialog
      v-model:visible="templateDialogVisible"
      :title="templateDialogTitle"
      :saving="savingTemplate"
      :form="templateForm"
      :questions="templateQuestions"
      @closed="handleTemplateDialogClosed"
      @add-question="addTemplateQuestionRow"
      @remove-question="removeTemplateQuestionRow"
      @save="saveTemplate"
    />

    <RuleVersionDialog
      v-model:visible="ruleVersionDialogVisible"
      :title="ruleVersionDialogTitle"
      :saving="savingRuleVersion"
      :form="ruleVersionForm"
      :semesters="referenceStore.semesters"
      @closed="handleRuleVersionDialogClosed"
      @save="saveRuleVersion"
    />

    <QuantRecordDialog
      v-model:visible="quantDialogVisible"
      :title="quantDialogTitle"
      :saving="savingQuant"
      :form="quantForm"
      :teacher-options="teacherOptions"
      :classes="referenceStore.classes"
      :semesters="referenceStore.semesters"
      :quant-rule-item-options="quantRuleItemOptions"
      @closed="handleQuantDialogClosed"
      @upload-attachments="handleQuantAttachmentUpload"
      @remove-attachment="removeQuantAttachment"
      @save="saveQuantRecord"
    />
  </div>
</template>

<script setup lang="ts">
import EvaluationBatchOverviewPanel from "../components/evaluation/EvaluationBatchOverviewPanel.vue";
import EvaluationTemplateDialog from "../components/evaluation/EvaluationTemplateDialog.vue";
import EvaluationTemplatesPanel from "../components/evaluation/EvaluationTemplatesPanel.vue";
import QuantRecordDialog from "../components/evaluation/QuantRecordDialog.vue";
import QuantRecordsPanel from "../components/evaluation/QuantRecordsPanel.vue";
import QuantRulesPanel from "../components/evaluation/QuantRulesPanel.vue";
import RuleVersionDialog from "../components/evaluation/RuleVersionDialog.vue";
import { useEvaluationQuantPage } from "../components/evaluation/useEvaluationQuantPage";

const {
  referenceStore,
  activeTab,
  templates,
  teacherOptions,
  batches,
  evaluationOverview,
  evaluationComparison,
  evaluationDetail,
  evaluationTeacherTrend,
  evaluationImportResult,
  ruleVersions,
  ruleItemRows,
  quantRecords,
  quantSummary,
  selectedRuleVersionId,
  selectedCompareBatchId,
  templateDialogVisible,
  ruleVersionDialogVisible,
  quantDialogVisible,
  savingTemplate,
  savingRuleVersion,
  savingRuleItems,
  savingQuant,
  evaluationImportForm,
  quantFilters,
  templateForm,
  templateQuestions,
  ruleVersionForm,
  quantForm,
  templateDialogTitle,
  ruleVersionDialogTitle,
  quantDialogTitle,
  quantRuleItemOptions,
  selectedRuleVersionMeta,
  currentSemesterLabel,
  currentBatchLabel,
  currentRuleVersionLabel,
  guideCards,
  compareBatchOptions,
  trendDeltaScore,
  trendRankDelta,
  trendPeakScore,
  downloadEvaluationTemplate,
  downloadQuantTemplate,
  loadTemplates,
  loadBatches,
  handleEvaluationImport,
  selectBatch,
  openCreateTemplate,
  openEditTemplate,
  handleCompareBatchChange,
  loadTeacherDetail,
  loadRuleVersions,
  openCreateRuleVersion,
  selectRuleVersion,
  addRuleItemRow,
  saveRuleItems,
  removeRuleItemRow,
  reloadQuantData,
  openCreateQuantRecord,
  resetQuantFilters,
  openEditQuantRecord,
  handleTemplateDialogClosed,
  handleRuleVersionDialogClosed,
  handleQuantDialogClosed,
  addTemplateQuestionRow,
  removeTemplateQuestionRow,
  saveTemplate,
  saveRuleVersion,
  handleQuantAttachmentUpload,
  removeQuantAttachment,
  saveQuantRecord,
} = useEvaluationQuantPage();
</script>

<style scoped>
.stat-card {
  padding: 18px 20px;
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

.guide-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.guide-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(248, 252, 255, 0.92);
  border: 1px solid rgba(116, 133, 151, 0.14);
}

.guide-card span {
  color: #6d8194;
  font-size: 13px;
}

.guide-card strong {
  display: block;
  margin-top: 8px;
  color: #21374b;
  font-size: 20px;
  font-weight: 760;
  line-height: 1.35;
}

.guide-card p {
  margin: 8px 0 0;
  color: #6a8094;
  line-height: 1.55;
  font-size: 13px;
}

.tone-blue {
  box-shadow: inset 0 4px 0 rgba(31, 108, 152, 0.78);
}

.tone-amber {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.84);
}

.tone-slate {
  box-shadow: inset 0 4px 0 rgba(92, 111, 129, 0.74);
}

.tone-green {
  box-shadow: inset 0 4px 0 rgba(66, 145, 102, 0.76);
}

@media (max-width: 1080px) {
  .guide-grid {
    grid-template-columns: 1fr;
  }
}
</style>
