<template>
  <AppPage
    eyebrow="教学评价 / 评教与量化"
    title="评教与班主任量化"
    description="统一维护评教模板、导入批次、量化规则版本、月度记录和学期汇总，让评价结果和过程依据放在同一条链路里。"
    :meta="pageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button :disabled="topActionsDisabled" @click="downloadEvaluationTemplate">评教模板下载</el-button>
        <el-button :disabled="topActionsDisabled" @click="downloadQuantTemplate">量化模板下载</el-button>
        <el-button type="primary" :disabled="topActionsDisabled" @click="activeTab = 'evaluation'"
          >进入评教</el-button
        >
      </div>
    </template>

    <AppStatGrid :items="pageStatCards" :columns="4" />

    <el-alert
      v-if="evaluationActionError"
      class="evaluation-page-alert"
      type="error"
      show-icon
      title="评教量化操作失败"
      @close="clearEvaluationActionError"
    >
      <template #default>{{ evaluationActionError }}</template>
    </el-alert>

    <el-alert
      v-if="evaluationLoadErrorItems.length"
      class="evaluation-page-alert"
      type="warning"
      show-icon
      :closable="false"
      title="评教量化部分数据加载失败"
    >
      <template #default>
        <div class="evaluation-load-error-list">
          <article v-for="item in evaluationLoadErrorItems" :key="item.key" class="evaluation-load-error-item">
            <div>
              <strong>{{ item.label }}</strong>
              <p>{{ item.message }}</p>
            </div>
            <el-button size="small" type="warning" plain :loading="item.loading" @click="retryEvaluationLoadItem(item.key)">
              重试
            </el-button>
          </article>
        </div>
      </template>
    </el-alert>

    <AppSectionCard
      title="当前操作提示"
      description="先确认模板、批次和规则版本，再进入教师详情、量化记录或汇总查询。"
    >
      <div class="guide-grid">
        <article
          v-for="item in guideCards"
          :key="item.label"
          class="guide-card"
          :class="item.tone"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.help }}</p>
        </article>
      </div>
    </AppSectionCard>

    <AppSectionCard
      title="评教量化模块"
      description="评教系统与班主任量化分区展示，保留原有导入、规则和汇总能力。"
    >
      <el-tabs v-model="activeTab" class="workspace-tabs">
        <el-tab-pane label="评教系统" name="evaluation">
          <EvaluationTemplatesPanel
            :templates="templates"
            :batches="batches"
            :evaluation-import-result="evaluationImportResult"
            :evaluation-import-form="evaluationImportForm"
            :semesters="referenceStore.semesters"
            :loading-templates="loadingTemplates"
            :templates-error="templatesError"
            :loading-batches="loadingBatches"
            :batches-error="batchesError"
            :importing-evaluation="importingEvaluation"
            :template-actions-disabled="templateActionsDisabled"
            :evaluation-import-disabled="evaluationImportDisabled"
            :batch-actions-disabled="batchActionsDisabled"
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
            :loading-evaluation-overview="loadingEvaluationOverview"
            :evaluation-overview-error="evaluationOverviewError"
            :loading-evaluation-comparison="loadingEvaluationComparison"
            :evaluation-comparison-error="evaluationComparisonError"
            :loading-teacher-detail="loadingTeacherDetail"
            :teacher-detail-error="teacherDetailError"
            :controls-disabled="evaluationOverviewControlsDisabled"
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
              :loading-rule-versions="loadingRuleVersions"
              :rule-versions-error="ruleVersionsError"
              :loading-rule-items="loadingRuleItems"
              :rule-items-error="ruleItemsError"
              :rule-actions-disabled="ruleActionsDisabled"
              :rule-item-controls-disabled="ruleItemControlsDisabled"
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
              :loading-quant-data="loadingQuantData"
              :quant-data-error="quantDataError"
              :loading-teacher-options="loadingTeacherOptions"
              :teacher-options-error="teacherOptionsError"
              :controls-disabled="quantControlsDisabled"
              :create-disabled="createQuantRecordDisabled"
              :row-actions-disabled="quantRowActionsDisabled"
              @reload="reloadQuantData"
              @open-create-quant-record="openCreateQuantRecord"
              @reset-filters="resetQuantFilters"
              @edit-quant-record="openEditQuantRecord"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </AppSectionCard>

    <EvaluationTemplateDialog
      v-model:visible="templateDialogVisible"
      :title="templateDialogTitle"
      :saving="savingTemplate"
      :controls-disabled="savingTemplate"
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
      :controls-disabled="savingRuleVersion"
      :form="ruleVersionForm"
      :semesters="referenceStore.semesters"
      @closed="handleRuleVersionDialogClosed"
      @save="saveRuleVersion"
    />

    <QuantRecordDialog
      v-model:visible="quantDialogVisible"
      :title="quantDialogTitle"
      :saving="savingQuant"
      :controls-disabled="savingQuant || uploadingQuantAttachments"
      :uploading-attachments="uploadingQuantAttachments"
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
  </AppPage>
</template>

<script setup lang="ts">
import { computed } from "vue";

import EvaluationBatchOverviewPanel from "../components/evaluation/EvaluationBatchOverviewPanel.vue";
import EvaluationTemplateDialog from "../components/evaluation/EvaluationTemplateDialog.vue";
import EvaluationTemplatesPanel from "../components/evaluation/EvaluationTemplatesPanel.vue";
import QuantRecordDialog from "../components/evaluation/QuantRecordDialog.vue";
import QuantRecordsPanel from "../components/evaluation/QuantRecordsPanel.vue";
import QuantRulesPanel from "../components/evaluation/QuantRulesPanel.vue";
import RuleVersionDialog from "../components/evaluation/RuleVersionDialog.vue";
import { useEvaluationQuantPage } from "../components/evaluation/useEvaluationQuantPage";
import AppPage from "../components/ui/AppPage.vue";
import AppSectionCard from "../components/ui/AppSectionCard.vue";
import AppStatGrid from "../components/ui/AppStatGrid.vue";
import type { PageMetaItem, StatCardItem } from "../components/ui/types";

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
  uploadingQuantAttachments,
  importingEvaluation,
  evaluationActionError,
  topActionsDisabled,
  templateActionsDisabled,
  evaluationImportDisabled,
  batchActionsDisabled,
  evaluationOverviewControlsDisabled,
  ruleActionsDisabled,
  ruleItemControlsDisabled,
  quantControlsDisabled,
  createQuantRecordDisabled,
  quantRowActionsDisabled,
  loadingTeacherOptions,
  loadingTemplates,
  loadingBatches,
  loadingEvaluationOverview,
  loadingEvaluationComparison,
  loadingTeacherDetail,
  loadingRuleVersions,
  loadingRuleItems,
  loadingQuantData,
  teacherOptionsError,
  templatesError,
  batchesError,
  evaluationOverviewError,
  evaluationComparisonError,
  teacherDetailError,
  ruleVersionsError,
  ruleItemsError,
  quantDataError,
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
  evaluationLoadErrorItems,
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
  retryEvaluationLoadItem,
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
  clearEvaluationActionError,
} = useEvaluationQuantPage();

const pageMeta = computed<PageMetaItem[]>(() => [
  { label: "当前学期", value: currentSemesterLabel.value },
  { label: "评教批次", value: currentBatchLabel.value },
  { label: "量化规则", value: currentRuleVersionLabel.value },
  { label: "量化记录", value: quantRecords.value.length },
]);

const pageStatCards = computed<StatCardItem[]>(() => {
  const templatesFailed = Boolean(templatesError.value && !templates.value.length);
  const batchesFailed = Boolean(batchesError.value && !batches.value.length);
  const ruleVersionsFailed = Boolean(ruleVersionsError.value && !ruleVersions.value.length);
  const quantRecordsFailed = Boolean(quantDataError.value && !quantRecords.value.length);

  return [
    {
      label: "评教模板",
      value: templatesFailed ? "加载失败" : templates.value.length,
      help: templatesFailed
        ? "请重新加载评教模板。"
        : templates.value.length
          ? "模板就绪，可继续导入评教数据。"
          : "建议先创建评教模板。",
      tone: templatesFailed ? "danger" : templates.value.length ? "primary" : "neutral",
      loading: loadingTemplates.value,
    },
    {
      label: "评教批次",
      value: batchesFailed ? "加载失败" : batches.value.length,
      help: batchesFailed
        ? "请重新加载评教批次。"
        : batches.value.length
          ? "可查看批次概览、对比和教师趋势。"
          : "暂无评教批次。",
      tone: batchesFailed ? "danger" : batches.value.length ? "success" : "neutral",
      loading: loadingBatches.value,
    },
    {
      label: "量化规则版本",
      value: ruleVersionsFailed ? "加载失败" : ruleVersions.value.length,
      help: ruleVersionsFailed
        ? "请重新加载量化规则版本。"
        : selectedRuleVersionMeta.value
          ? `当前：${currentRuleVersionLabel.value}`
          : "请选择或创建量化规则版本。",
      tone: ruleVersionsFailed ? "danger" : selectedRuleVersionMeta.value ? "primary" : "warning",
      loading: loadingRuleVersions.value,
    },
    {
      label: "量化记录",
      value: quantRecordsFailed ? "加载失败" : quantRecords.value.length,
      help: quantRecordsFailed
        ? "请重新查询量化记录。"
        : quantRecords.value.length
          ? "可按学期、教师和规则版本继续筛选。"
          : "可从当前规则版本开始新增记录。",
      tone: quantRecordsFailed ? "danger" : quantRecords.value.length ? "warning" : "neutral",
      loading: loadingQuantData.value,
    },
  ];
});
</script>

<style scoped>
.guide-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.evaluation-page-alert {
  margin-top: 16px;
}

.evaluation-load-error-list {
  display: grid;
  gap: 10px;
  margin-top: 8px;
}

.evaluation-load-error-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #fff7ed;
}

.evaluation-load-error-item strong {
  display: block;
  color: #7c3f00;
}

.evaluation-load-error-item p {
  margin: 4px 0 0;
  color: #8a5d19;
  line-height: 1.5;
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

  .evaluation-load-error-item {
    display: grid;
  }
}
</style>
