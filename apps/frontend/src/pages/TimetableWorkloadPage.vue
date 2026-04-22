<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">教学执行 / 课表与工作量</div>
        <h2 class="page-title">课表与工作量</h2>
        <p class="page-subtitle">
          完成课表导入、未匹配项修正、规则版本配置、附加量化录入和教师工作量计算，历史结果按规则版本保留快照。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>当前学期</strong>{{ currentSemesterLabel }}</span>
          <span class="page-chip"><strong>规则版本</strong>{{ currentRuleLabel }}</span>
          <span class="page-chip"><strong>当前批次未匹配</strong>{{ currentBatch?.unresolved_count ?? 0 }}</span>
          <span class="page-chip"><strong>结果教师</strong>{{ results.length }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="refreshAll">刷新数据</el-button>
        <el-button @click="downloadTimetableTemplate">课表模板下载</el-button>
        <el-button type="primary" :loading="calculating" @click="calculateWorkload">
          计算工作量
        </el-button>
      </div>
    </header>

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
      :result-count="results.length"
      :total-workload="totalWorkload"
      :calculating="calculating"
      @calculate="calculateWorkload"
      @export-results="exportResults"
    />

    <el-tabs v-model="activeTab">
      <el-tab-pane label="课表导入与修正" name="timetable">
        <WorkloadTimetablePanel
          v-model:importRemark="importRemark"
          v-model:unresolvedOnly="unresolvedOnly"
          :file-input-key="fileInputKey"
          :selected-timetable-file-name="selectedTimetableFile?.name ?? ''"
          :importing="importing"
          :can-import="Boolean(selectedTimetableFile && selectedSemesterId)"
          :timetable-batches="timetableBatches"
          :selected-batch-id="selectedBatchId"
          :timetable-entries="timetableEntries"
          :course-type-options="courseTypeOptions"
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
          @export-results="exportResults"
          @open-result-drawer="openResultDrawer"
        />
      </el-tab-pane>
    </el-tabs>

    <WorkloadEntryDialog
      v-model:visible="entryDialogVisible"
      :form="entryForm"
      :teacher-options="teacherOptions"
      :classes="referenceStore.classes"
      :subjects="referenceStore.subjects"
      :course-type-options="courseTypeOptions"
      :saving="savingEntry"
      @closed="handleEntryDialogClosed"
      @save="saveEntry"
    />

    <WorkloadRuleVersionDialog
      v-model:visible="ruleDialogVisible"
      :form="newRuleForm"
      :semester-options="semesterOptions"
      :saving="creatingRuleVersion"
      @closed="handleRuleDialogClosed"
      @save="createRuleVersion"
    />
  </div>
</template>

<script setup lang="ts">
import WorkloadContextPanel from "../components/workload/WorkloadContextPanel.vue";
import WorkloadEntryDialog from "../components/workload/WorkloadEntryDialog.vue";
import WorkloadResultsPanel from "../components/workload/WorkloadResultsPanel.vue";
import WorkloadRuleVersionDialog from "../components/workload/WorkloadRuleVersionDialog.vue";
import WorkloadRulesPanel from "../components/workload/WorkloadRulesPanel.vue";
import WorkloadTimetablePanel from "../components/workload/WorkloadTimetablePanel.vue";
import { useTimetableWorkloadPage } from "../components/workload/useTimetableWorkloadPage";

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
  selectedTimetableFile,
  fileInputKey,
  importRemark,
  importing,
  savingEntry,
  creatingRuleVersion,
  savingRuleItems,
  savingExtra,
  calculating,
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
} = useTimetableWorkloadPage();
</script>
