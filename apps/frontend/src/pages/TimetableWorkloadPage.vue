<template>
  <AppPage
    eyebrow="教学执行 / 课表与工作量"
    title="课表与工作量"
    description="完成课表导入、未匹配项修正、规则版本配置、附加量化录入和教师工作量计算，历史结果按规则版本保留快照。"
    :meta="pageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button
          :loading="workloadRefreshBusy"
          :disabled="workloadWriteBusy"
          @click="refreshAll"
        >
          刷新数据
        </el-button>
        <el-button
          :disabled="workloadWriteBusy"
          @click="downloadTimetableTemplate"
        >
          课表模板下载
        </el-button>
        <el-button
          type="primary"
          :loading="calculating"
          :disabled="calculateDisabled"
          @click="calculateWorkload"
        >
          计算工作量
        </el-button>
      </div>
    </template>

    <AppStatGrid :items="pageStatCards" :columns="4" />

    <el-alert
      v-if="workloadLoadErrorItems.length"
      class="workload-page-alert"
      type="warning"
      show-icon
      :closable="false"
      title="课表与工作量部分数据加载失败"
    >
      <div class="workload-load-error-list">
        <div
          v-for="item in workloadLoadErrorItems"
          :key="item.key"
          class="workload-load-error-item"
        >
          <span>{{ item.label }}：{{ item.message }}</span>
          <el-button
            link
            type="primary"
            :loading="item.loading"
            @click="retryWorkloadLoadItem(item.key)"
          >
            重试
          </el-button>
        </div>
      </div>
    </el-alert>

    <el-alert
      v-if="workloadActionError"
      class="workload-page-alert"
      type="error"
      show-icon
      :closable="false"
      title="课表与工作量操作失败"
    >
      <div class="workload-load-error-item">
        <span>{{ workloadActionError }}</span>
        <el-button link type="primary" @click="clearWorkloadActionError">
          知道了
        </el-button>
      </div>
    </el-alert>

    <WorkloadContextPanel
      v-model:selectedSemesterId="selectedSemesterId"
      v-model:selectedRuleVersionId="selectedRuleVersionId"
      v-model:selectedBatchId="selectedBatchId"
      :semester-options="semesterOptions"
      :rule-versions="ruleVersions"
      :timetable-batches="timetableBatches"
      :current-semester-label="currentSemesterLabel"
      :current-batch="currentBatch"
      :overview-cards="overviewCards"
      :process-cards="processCards"
      :precheck-messages="workloadPrecheckMessages"
      :result-count="results.length"
      :total-workload="totalWorkload"
      :calculating="calculating"
      :loading-reference="loadingReference"
      :reference-error="referenceError"
      :loading-rule-versions="loadingRuleVersions"
      :rule-versions-error="ruleVersionsError"
      :loading-batches="loadingBatches"
      :batches-error="batchesError"
      :loading-results="loadingResults"
      :results-error="resultsError"
      :controls-disabled="workloadSelectionDisabled"
      :calculate-disabled="calculateDisabled"
      :export-disabled="exportResultsDisabled"
      @calculate="calculateWorkload"
      @export-results="exportResults"
    />

    <AppSectionCard
      title="工作量业务模块"
      description="按导入修正、规则配置和结果输出三个阶段收纳，减少长页面滚动。"
    >
      <el-tabs v-model="activeTab" class="workspace-tabs">
        <el-tab-pane label="课表导入与修正" name="timetable">
          <WorkloadTimetablePanel
            v-model:importRemark="importRemark"
            v-model:unresolvedOnly="unresolvedOnly"
            v-model:viewMode="timetableViewMode"
            :file-input-key="fileInputKey"
            :selected-timetable-file-name="selectedTimetableFile?.name ?? ''"
            :import-result="timetableImportResult"
            :importing="importing"
            :can-import="Boolean(selectedTimetableFile && selectedSemesterId)"
            :controls-disabled="timetablePanelActionsDisabled"
            :import-disabled="timetableImportDisabled"
            :row-actions-disabled="timetablePanelActionsDisabled"
            :timetable-batches="timetableBatches"
            :selected-batch-id="selectedBatchId"
            :timetable-entries="timetableEntries"
            :review-cards="timetableReviewCards"
            :course-type-options="courseTypeOptions"
            :loading-batches="loadingBatches"
            :batches-error="batchesError"
            :loading-entries="loadingEntries"
            :entries-error="entriesError"
            @file-change="handleTimetableFileChange"
            @import-timetable="importTimetable"
            @select-batch="selectBatch"
            @open-entry-dialog="openEntryDialog"
          />
        </el-tab-pane>

        <el-tab-pane label="规则与附加项" name="rules">
          <WorkloadRulesPanel
            v-model:selectedRuleVersionId="selectedRuleVersionId"
            :rule-versions="ruleVersions"
            :rule-items="ruleItems"
            :saving-rule-items="savingRuleItems"
            :extras="extras"
            :extra-form="extraForm"
            :teacher-options="teacherOptions"
            :saving-extra="savingExtra"
            :loading-rule-versions="loadingRuleVersions"
            :rule-versions-error="ruleVersionsError"
            :loading-rule-items="loadingRuleItems"
            :rule-items-error="ruleItemsError"
            :loading-extras="loadingExtras"
            :extras-error="extrasError"
            :loading-teacher-options="loadingTeacherOptions"
            :teacher-options-error="teacherOptionsError"
            :rule-actions-disabled="ruleActionsDisabled"
            :rule-item-controls-disabled="ruleItemControlsDisabled"
            :extra-controls-disabled="extraControlsDisabled"
            @open-rule-version-dialog="openRuleVersionDialog"
            @save-rule-items="saveRuleItems"
            @add-rule-item="addRuleItem"
            @remove-rule-item="removeRuleItem"
            @create-extra="createExtra"
          />
        </el-tab-pane>

        <el-tab-pane label="工作量结果" name="results">
          <WorkloadResultsPanel
            v-model:drawerVisible="resultDrawerVisible"
            :results="results"
            :active-result="activeResult"
            :course-type-options="courseTypeOptions"
            :result-review-cards="workloadResultReviewCards"
            :loading-results="loadingResults"
            :results-error="resultsError"
            :export-disabled="exportResultsDisabled"
            :row-actions-disabled="workloadWriteBusy || loadingResults"
            @export-results="exportResults"
            @open-result-drawer="openResultDrawer"
          />
        </el-tab-pane>
      </el-tabs>
    </AppSectionCard>

    <WorkloadEntryDialog
      v-model:visible="entryDialogVisible"
      :form="entryForm"
      :teacher-options="teacherOptions"
      :classes="referenceStore.classes"
      :subjects="referenceStore.subjects"
      :course-type-options="courseTypeOptions"
      :saving="savingEntry"
      :controls-disabled="savingEntry"
      @closed="handleEntryDialogClosed"
      @save="saveEntry"
    />

    <WorkloadRuleVersionDialog
      v-model:visible="ruleDialogVisible"
      :form="newRuleForm"
      :semester-options="semesterOptions"
      :saving="creatingRuleVersion"
      :controls-disabled="creatingRuleVersion"
      @closed="handleRuleDialogClosed"
      @save="createRuleVersion"
    />
  </AppPage>
</template>

<script setup lang="ts">
import { computed } from "vue";

import WorkloadContextPanel from "../components/workload/WorkloadContextPanel.vue";
import WorkloadEntryDialog from "../components/workload/WorkloadEntryDialog.vue";
import WorkloadResultsPanel from "../components/workload/WorkloadResultsPanel.vue";
import WorkloadRuleVersionDialog from "../components/workload/WorkloadRuleVersionDialog.vue";
import WorkloadRulesPanel from "../components/workload/WorkloadRulesPanel.vue";
import WorkloadTimetablePanel from "../components/workload/WorkloadTimetablePanel.vue";
import { useTimetableWorkloadPage } from "../components/workload/useTimetableWorkloadPage";
import AppPage from "../components/ui/AppPage.vue";
import AppSectionCard from "../components/ui/AppSectionCard.vue";
import AppStatGrid from "../components/ui/AppStatGrid.vue";
import type {
  PageMetaItem,
  StatCardItem,
  UiTone,
} from "../components/ui/types";

const {
  referenceStore,
  activeTab,
  teacherOptions,
  ruleVersions,
  ruleItems,
  timetableBatches,
  timetableEntries,
  extras,
  results,
  selectedSemesterId,
  selectedRuleVersionId,
  selectedBatchId,
  unresolvedOnly,
  timetableViewMode,
  selectedTimetableFile,
  timetableImportResult,
  fileInputKey,
  importRemark,
  importing,
  savingEntry,
  creatingRuleVersion,
  savingRuleItems,
  savingExtra,
  calculating,
  loadingReference,
  loadingTeacherOptions,
  loadingRuleVersions,
  loadingRuleItems,
  loadingBatches,
  loadingEntries,
  loadingExtras,
  loadingResults,
  workloadActionError,
  workloadWriteBusy,
  workloadRefreshBusy,
  workloadSelectionDisabled,
  calculateDisabled,
  exportResultsDisabled,
  timetableImportDisabled,
  timetablePanelActionsDisabled,
  ruleActionsDisabled,
  ruleItemControlsDisabled,
  extraControlsDisabled,
  referenceError,
  teacherOptionsError,
  ruleVersionsError,
  ruleItemsError,
  batchesError,
  entriesError,
  extrasError,
  resultsError,
  entryDialogVisible,
  ruleDialogVisible,
  resultDrawerVisible,
  entryForm,
  newRuleForm,
  extraForm,
  activeResult,
  semesterOptions,
  courseTypeOptions,
  currentBatch,
  totalWorkload,
  currentSemesterLabel,
  currentRuleLabel,
  overviewCards,
  processCards,
  timetableReviewCards,
  workloadPrecheckMessages,
  workloadResultReviewCards,
  workloadLoadErrorItems,
  refreshAll,
  handleTimetableFileChange,
  importTimetable,
  selectBatch,
  openEntryDialog,
  handleEntryDialogClosed,
  saveEntry,
  addRuleItem,
  removeRuleItem,
  saveRuleItems,
  createRuleVersion,
  openRuleVersionDialog,
  handleRuleDialogClosed,
  createExtra,
  calculateWorkload,
  downloadTimetableTemplate,
  exportResults,
  openResultDrawer,
  retryWorkloadLoadItem,
  clearWorkloadActionError,
} = useTimetableWorkloadPage();

function normalizeTone(tone: string): UiTone {
  if (tone.includes("red")) return "danger";
  if (tone.includes("green")) return "success";
  if (tone.includes("amber")) return "warning";
  if (tone.includes("blue")) return "primary";
  if (tone.includes("teal")) return "info";
  return "neutral";
}

const pageMeta = computed<PageMetaItem[]>(() => [
  { label: "当前学期", value: currentSemesterLabel.value },
  { label: "规则版本", value: currentRuleLabel.value },
  {
    label: "当前批次未匹配",
    value: batchesError.value ? "加载失败" : currentBatch.value?.unresolved_count ?? 0,
  },
  { label: "结果教师", value: resultsError.value ? "加载失败" : results.value.length },
]);

const pageStatCards = computed<StatCardItem[]>(() => [
  ...overviewCards.value.map((item) => ({
    label: item.label,
    value: item.value,
    help: item.help,
    tone: normalizeTone(item.tone),
  })),
  {
    label: "结果教师",
    value: resultsError.value ? "加载失败" : results.value.length,
    help: resultsError.value
      ? "工作量结果暂时不可用，请重试当前区块。"
      : results.value.length
      ? `当前总工作量 ${totalWorkload.value}`
      : "完成计算后生成教师工作量结果。",
    tone: resultsError.value ? "danger" : results.value.length ? "success" : "neutral",
  },
]);
</script>

<style scoped>
.workload-page-alert {
  margin-top: 16px;
}

.workload-load-error-list {
  display: grid;
  gap: 8px;
  margin-top: 8px;
}

.workload-load-error-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

@media (max-width: 760px) {
  .workload-load-error-item {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
