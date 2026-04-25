<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">高考志愿 / 志愿辅助</div>
        <h2 class="page-title">高考志愿</h2>
        <p class="page-subtitle">
          先维护院校、专业、招生计划和录取数据，再配置省份志愿规则，最后生成推荐方案并保留历史记录。
        </p>
        <div class="page-chip-row recommendation-chip-row">
          <span v-for="item in summaryCards" :key="item.label" class="page-chip">
            <strong>{{ item.label }}</strong>{{ item.value }}
          </span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="$router.push('/gaokao-pathways')">升学方案中心</el-button>
        <el-button @click="downloadEnrollmentPlanTemplate">计划模板下载</el-button>
        <el-button @click="activeTab = 'enrollment-plans'">查看计划库</el-button>
        <el-button @click="activeTab = 'volunteer-rules'">维护省份规则</el-button>
        <el-button @click="activeTab = 'special-type-rules'">特殊类型规则</el-button>
        <el-button @click="activeTab = 'score-transform-rules'">赋分规则</el-button>
        <el-button @click="activeTab = 'subject-requirements'">选科字典</el-button>
        <el-button @click="activeTab = 'shandong-workbench'">山东普通类推荐</el-button>
        <el-button @click="activeTab = 'volunteer-workbench'">学生工作台</el-button>
        <el-button type="primary" @click="activeTab = 'recommendations'">生成推荐</el-button>
      </div>
    </header>

    <section class="hero-grid">
      <div class="soft-card summary-panel">
        <div class="summary-copy">
          <div class="summary-badge">当前概况</div>
          <h3>先把计划、规则和录取基线补齐，再进入志愿方案</h3>
          <p>
            推荐结果会同时显示依据、风险提示和历史方案对比。生成前建议先确认考试、学生位次、招生计划与省份规则是否完整。
          </p>
        </div>
        <div class="summary-metrics">
          <article v-for="item in summaryCards" :key="item.label" class="summary-metric" :class="item.tone">
            <div class="summary-metric-label">{{ item.label }}</div>
            <div class="summary-metric-value">{{ item.value }}</div>
            <div class="summary-metric-help">{{ item.help }}</div>
          </article>
        </div>
      </div>

      <div class="soft-card workflow-panel">
        <div class="section-head compact">
          <div>
            <h3>使用顺序</h3>
            <p>先补数据底座，再配置规则和策略，最后生成与复核方案。</p>
          </div>
        </div>
        <div class="workflow-list">
          <div class="workflow-item">
            <span>01</span>
            <div>
              <strong>维护院校与专业</strong>
              <p>先补齐院校、专业和层级标签，保证筛选基础完整。</p>
            </div>
          </div>
          <div class="workflow-item">
            <span>02</span>
            <div>
              <strong>导入招生计划与历年录取</strong>
              <p>计划库决定当年可报范围，录取库提供风险分层，两者都需要先补齐。</p>
            </div>
          </div>
          <div class="workflow-item">
            <span>03</span>
            <div>
              <strong>配置省份规则与推荐策略</strong>
              <p>先明确志愿单位、志愿上限和调剂规则，再调整黑白名单与冲稳保阈值。</p>
            </div>
          </div>
          <div class="workflow-item">
            <span>04</span>
            <div>
              <strong>生成方案并回看历史</strong>
              <p>生成后可回看历史方案，对比差异并导出推荐单。</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="guide-grid">
      <article v-for="item in recommendationGuideCards" :key="item.label" class="soft-card guide-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </section>

    <el-tabs v-model="activeTab" class="recommendation-tabs">
      <el-tab-pane label="院校库" name="colleges">
        <RecommendationCollegesPanel
          :colleges="colleges"
          :filters="collegeFilters"
          :province-options="provinceOptions"
          @load="loadColleges"
          @reset="resetCollegeFilters"
          @create="openCreateCollege"
          @edit="openEditCollege"
        />
      </el-tab-pane>

      <el-tab-pane label="专业库" name="majors">
        <RecommendationMajorsPanel
          :majors="majors"
          :filters="majorFilters"
          @load="loadMajors"
          @reset="resetMajorFilters"
          @create="openCreateMajor"
          @edit="openEditMajor"
        />
      </el-tab-pane>

      <el-tab-pane label="就业方向库" name="employment-directions">
        <RecommendationEmploymentDirectionsPanel
          :directions="employmentDirections"
          :filters="employmentDirectionFilters"
          :category-options="employmentDirectionCategoryFilterOptions"
          @load="loadEmploymentDirections"
          @reset="resetEmploymentDirectionFilters"
          @create="openCreateEmploymentDirection"
          @edit="openEditEmploymentDirection"
        />
      </el-tab-pane>

      <el-tab-pane label="专业就业映射" name="major-employment-maps">
        <RecommendationMajorEmploymentMappingsPanel
          :mappings="majorEmploymentMappings"
          :filters="majorEmploymentMappingFilters"
          :major-options="majorDirectory"
          :direction-options="employmentDirectionOptions"
          :strength-options="employmentMappingStrengthOptions"
          @load="loadMajorEmploymentMappings"
          @reset="resetMajorEmploymentMappingFilters"
          @create="openCreateMajorEmploymentMapping"
          @edit="openEditMajorEmploymentMapping"
        />
      </el-tab-pane>

      <el-tab-pane label="招生计划库" name="enrollment-plans">
        <RecommendationEnrollmentPlansPanel
          :enrollment-plans="enrollmentPlans"
          :filters="enrollmentPlanFilters"
          :year-options="planYearOptions"
          :province-options="provinceOptions"
          :batch-options="batchOptions"
          :college-options="collegeDirectory"
          :student-type-options="recommendationStudentTypeOptions"
          :enrollment-plan-import-result="enrollmentPlanImportResult"
          @download-template="downloadEnrollmentPlanTemplate"
          @import="handleEnrollmentPlanImport"
          @load="loadEnrollmentPlans"
          @reset="resetEnrollmentPlanFilters"
        />
      </el-tab-pane>

      <el-tab-pane label="录取库" name="admissions">
        <RecommendationAdmissionsPanel
          :admissions="admissions"
          :filters="admissionFilters"
          :admission-year-options="admissionYearOptions"
          :province-options="provinceOptions"
          :college-options="collegeDirectory"
          :student-type-options="recommendationStudentTypeOptions"
          :admission-import-result="admissionImportResult"
          @download-template="downloadAdmissionTemplate"
          @import="handleAdmissionImport"
          @load="loadAdmissions"
          @reset="resetAdmissionFilters"
        />
      </el-tab-pane>

      <el-tab-pane label="省份规则" name="volunteer-rules">
        <RecommendationVolunteerRulesPanel
          :rules="provinceVolunteerRules"
          :filters="volunteerRuleFilters"
          :bootstrapping="bootstrappingVolunteerRules"
          :year-options="ruleYearOptions"
          :province-options="provinceOptions"
          :exam-mode-options="examModeOptions"
          :candidate-type-options="gaokaoCandidateTypeOptions"
          @load="loadProvinceVolunteerRules"
          @bootstrap="bootstrapProvinceVolunteerRules"
          @reset="resetVolunteerRuleFilters"
          @create="openCreateVolunteerRule"
          @edit="openEditVolunteerRule"
        />
      </el-tab-pane>

      <el-tab-pane label="特殊类型规则" name="special-type-rules">
        <RecommendationSpecialTypeRulesPanel
          :rules="specialTypeRules"
          :filters="specialTypeRuleFilters"
          :bootstrapping="bootstrappingSpecialTypeRules"
          :year-options="specialTypeRuleYearOptions"
          :province-options="provinceOptions"
          :student-type-options="recommendationStudentTypeOptions"
          @load="loadSpecialTypeRules"
          @bootstrap="bootstrapSpecialTypeRules"
          @reset="resetSpecialTypeRuleFilters"
        />
      </el-tab-pane>

      <el-tab-pane label="赋分规则" name="score-transform-rules">
        <RecommendationScoreTransformRulesPanel
          :rules="provinceScoreTransformRules"
          :filters="scoreTransformRuleFilters"
          :bootstrapping="bootstrappingScoreTransformRules"
          :year-options="scoreTransformRuleYearOptions"
          :province-options="provinceOptions"
          :exam-mode-options="examModeOptions"
          @load="loadProvinceScoreTransformRules"
          @bootstrap="bootstrapProvinceScoreTransformRules"
          @reset="resetScoreTransformRuleFilters"
        />
      </el-tab-pane>

      <el-tab-pane label="选科字典" name="subject-requirements">
        <RecommendationSubjectRequirementDictsPanel
          :dicts="subjectRequirementDicts"
          :filters="subjectRequirementDictFilters"
          :bootstrapping="bootstrappingSubjectRequirementDicts"
          :year-options="subjectRequirementDictYearOptions"
          :province-options="provinceOptions"
          :exam-mode-options="examModeOptions"
          @load="loadSubjectRequirementDicts"
          @bootstrap="bootstrapSubjectRequirementDicts"
          @reset="resetSubjectRequirementDictFilters"
        />
      </el-tab-pane>

      <el-tab-pane label="山东普通类推荐" name="shandong-workbench">
        <RecommendationShandongWorkbenchPanel
          :form="shandongRecommendationForm"
          :student-options="studentOptions"
          :exam-options="examOptions"
          :year-options="workbenchYearOptions"
          :target-region-options="targetRegionOptions"
          :school-level-options="schoolLevelOptions"
          :result="shandongRecommendationResult"
          :result-groups="shandongResultGroups"
          :projection="shandongRecommendationProjection"
          :data-health="shandongDataHealth"
          :coverage-rows="shandongCoverageRows"
          :loading="generatingShandongRecommendation"
          :loading-data-health="loadingShandongDataHealth"
          :saving-projection="savingShandongProjection"
          :exporting-report="exportingShandongReport"
          @generate="generateShandongRecommendation"
          @reset="resetShandongRecommendation"
          @load-data-health="loadShandongDataHealth"
          @sync-from-recommendation="syncShandongRecommendationFromRecommendation"
          @print-report="openShandongRecommendationPrintPreview"
          @export-report="exportShandongRecommendationReport"
        />
      </el-tab-pane>

      <el-tab-pane label="学生志愿工作台" name="volunteer-workbench">
        <RecommendationVolunteerWorkbenchPanel
          :form="volunteerWorkbenchForm"
          :student-options="studentOptions"
          :exam-options="examOptions"
          :year-options="workbenchYearOptions"
          :batch-options="workbenchBatchOptions"
          :exam-mode-options="workbenchExamModeOptions"
          :employment-directions="employmentDirections"
          :career-industry-options="workbenchCareerIndustryOptions"
          :career-job-type-options="workbenchCareerJobTypeOptions"
          :student-career-preference="studentCareerPreference"
          :loading-student-career-preference="loadingStudentCareerPreference"
          :saving-student-career-preference="savingStudentCareerPreference"
          :province-options="provinceOptions"
          :target-region-options="targetRegionOptions"
          :school-level-options="schoolLevelOptions"
          :preview="workbenchPreview"
          :draft="volunteerDraft"
          v-model:draft-name="volunteerDraftName"
          :loading="workbenchLoading"
          :saving-draft="savingVolunteerDraft"
          :exporting-draft-id="exportingVolunteerDraftId"
          :loading-saved-drafts="loadingVolunteerDrafts"
          :deleting-draft-id="deletingVolunteerDraftId"
          :current-draft-id="currentVolunteerDraftId"
          :saved-drafts="savedVolunteerDrafts"
          :compare-draft-id="compareVolunteerDraftId"
          :compare-draft-loading="compareVolunteerDraftLoading"
          :draft-comparison="volunteerDraftComparison"
          :selected-plan-ids="selectedDraftPlanIds"
          :selected-rule="selectedVolunteerRule"
          :workbench-explanation="workbenchExplanation"
          :draft-checks="volunteerDraftChecks"
          :volunteer-limit="volunteerLimit"
          :remaining-slots="remainingVolunteerSlots"
          @load-preview="loadVolunteerWorkbenchPreview"
          @reset="resetVolunteerWorkbench"
          @sync-from-recommendation="syncVolunteerWorkbenchFromRecommendation"
          @save-draft="saveVolunteerDraft"
          @save-draft-as="saveVolunteerDraftAsNew"
          @print-draft="openVolunteerDraftPrintPreview"
          @export-draft="exportVolunteerDraft"
          @reload-drafts="loadVolunteerDrafts"
          @compare-draft-change="loadVolunteerDraftComparison"
          @load-draft="loadVolunteerDraftDetail"
          @delete-draft="deleteVolunteerDraft"
          @apply-student-career-preference="applyStudentCareerPreference"
          @save-student-career-preference="saveStudentCareerPreference"
          @add-candidate="addVolunteerCandidate"
          @remove-candidate="removeVolunteerCandidate"
          @move-candidate="moveVolunteerCandidate"
          @reorder-candidate="reorderVolunteerCandidate"
        />
      </el-tab-pane>

      <el-tab-pane label="推荐中心" name="recommendations">
        <div class="recommend-layout">
          <RecommendationGeneratePanel
            v-model:generation-mode="generationMode"
            :form="recommendationForm"
            :student-options="studentOptions"
            :exam-options="examOptions"
            :year-options="planYearOptions"
            :province-options="provinceOptions"
            :target-region-options="targetRegionOptions"
            :school-level-options="schoolLevelOptions"
            :generating="generating"
            :latest-generation-message="latestGenerationMessage"
            :alert-type="latestGeneration ? 'success' : 'info'"
            :recommendation-mode-label="recommendationModeLabel"
            :recommendation-mode-hint="recommendationModeHint"
            @submit="submitRecommendation"
            @reset="resetRecommendationForm"
          />

          <div class="recommend-side-stack">
            <RecommendationStrategyPanel
              :settings="recommendationSettings"
              :strategy-cards="strategyCards"
              :college-options="collegeDirectory"
              v-model:selected-strategy-preset-id="selectedStrategyPresetId"
              :strategy-preset-form="strategyPresetForm"
              :saving-settings="savingSettings"
              :saving-preset="savingPreset"
              :deleting-preset-id="deletingPresetId"
              @reload="reloadRecommendationSettings"
              @save-settings="saveRecommendationSettings"
              @apply-preset="applyStrategyPresetWithConfirm"
              @delete-preset="deleteStrategyPreset"
              @save-preset="saveStrategyPreset"
            />

            <RecommendationHistoryPanel
              :history-items="historyItems"
              :student-options="studentOptions"
              :history-filters="historyFilters"
              :loading-history="loadingHistory"
              :history-load-error="historyLoadError"
              @load-history="loadHistory"
              @reset-history="resetHistoryFilters"
              @view-scheme="viewScheme"
              @export-scheme="exportScheme"
            />
          </div>
        </div>

        <RecommendationSchemeResultsPanel
          :scheme-meta="selectedSchemeMeta"
          :compare-history-options="compareHistoryOptions"
          :selected-scheme-results="selectedSchemeResults"
          :loading-scheme="loadingSelectedScheme"
          :selected-scheme-error="selectedSchemeError"
          v-model:compare-scheme-id="compareSchemeId"
          :comparing-scheme="comparingScheme"
          :compare-scheme-error="compareSchemeError"
          :compare-scheme-results="compareSchemeResults"
          v-model:multi-compare-scheme-ids="multiCompareSchemeIds"
          :multi-compare-error="multiCompareError"
          :multi-compare-scheme-results="multiCompareSchemeResults"
          :multi-comparing-schemes="multiComparingSchemes"
          :exporting-scheme="exportingScheme"
          @compare-scheme-change="handleCompareSchemeChange"
          @multi-compare-change="handleMultiCompareChange"
          @export-scheme="exportScheme"
          @print-preview="openRecommendationPrintPreview"
          @reload-scheme="reloadSelectedScheme"
        />
      </el-tab-pane>
    </el-tabs>

    <RecommendationCollegeDialog
      v-model:visible="collegeDialogVisible"
      :title="collegeDialogTitle"
      :form="collegeForm"
      :province-options="provinceOptions"
      :school-level-options="schoolLevelOptions"
      :saving="savingCollege"
      @submit="submitCollege"
      @closed="handleCollegeDialogClosed"
    />

    <RecommendationMajorDialog
      v-model:visible="majorDialogVisible"
      :title="majorDialogTitle"
      :form="majorForm"
      :saving="savingMajor"
      @submit="submitMajor"
      @closed="handleMajorDialogClosed"
    />

    <RecommendationEmploymentDirectionDialog
      v-model:visible="employmentDirectionDialogVisible"
      :title="employmentDirectionDialogTitle"
      :form="employmentDirectionForm"
      :category-options="employmentDirectionCategoryFilterOptions"
      :saving="savingEmploymentDirection"
      @submit="submitEmploymentDirection"
      @closed="handleEmploymentDirectionDialogClosed"
    />

    <RecommendationMajorEmploymentMappingDialog
      v-model:visible="majorEmploymentMappingDialogVisible"
      :title="majorEmploymentMappingDialogTitle"
      :form="majorEmploymentMappingForm"
      :major-options="majorDirectory"
      :direction-options="employmentDirectionOptions"
      :strength-options="employmentMappingStrengthOptions"
      :saving="savingMajorEmploymentMapping"
      @submit="submitMajorEmploymentMapping"
      @closed="handleMajorEmploymentMappingDialogClosed"
    />

    <RecommendationVolunteerRuleDialog
      v-model:visible="volunteerRuleDialogVisible"
      :title="volunteerRuleDialogTitle"
      :form="volunteerRuleForm"
      :saving="savingVolunteerRule"
      :year-options="ruleYearOptions"
      :province-options="provinceOptions"
      :exam-mode-options="examModeOptions"
      :candidate-type-options="gaokaoCandidateTypeOptions"
      :subject-requirement-mode-options="subjectRequirementModeOptions"
      :parallel-rule-mode-options="parallelRuleModeOptions"
      :unit-type-options="volunteerUnitTypeOptions"
      :special-rule-options="specialRuleOptions"
      @submit="submitVolunteerRule"
      @closed="handleVolunteerRuleDialogClosed"
    />
  </div>
</template>

<script setup lang="ts">
import RecommendationAdmissionsPanel from "../components/recommendations/RecommendationAdmissionsPanel.vue";
import RecommendationCollegeDialog from "../components/recommendations/RecommendationCollegeDialog.vue";
import RecommendationCollegesPanel from "../components/recommendations/RecommendationCollegesPanel.vue";
import RecommendationEmploymentDirectionDialog from "../components/recommendations/RecommendationEmploymentDirectionDialog.vue";
import RecommendationEmploymentDirectionsPanel from "../components/recommendations/RecommendationEmploymentDirectionsPanel.vue";
import RecommendationEnrollmentPlansPanel from "../components/recommendations/RecommendationEnrollmentPlansPanel.vue";
import RecommendationGeneratePanel from "../components/recommendations/RecommendationGeneratePanel.vue";
import RecommendationHistoryPanel from "../components/recommendations/RecommendationHistoryPanel.vue";
import RecommendationMajorDialog from "../components/recommendations/RecommendationMajorDialog.vue";
import RecommendationMajorEmploymentMappingDialog from "../components/recommendations/RecommendationMajorEmploymentMappingDialog.vue";
import RecommendationMajorEmploymentMappingsPanel from "../components/recommendations/RecommendationMajorEmploymentMappingsPanel.vue";
import RecommendationMajorsPanel from "../components/recommendations/RecommendationMajorsPanel.vue";
import RecommendationScoreTransformRulesPanel from "../components/recommendations/RecommendationScoreTransformRulesPanel.vue";
import RecommendationSchemeResultsPanel from "../components/recommendations/RecommendationSchemeResultsPanel.vue";
import RecommendationShandongWorkbenchPanel from "../components/recommendations/RecommendationShandongWorkbenchPanel.vue";
import RecommendationSpecialTypeRulesPanel from "../components/recommendations/RecommendationSpecialTypeRulesPanel.vue";
import RecommendationStrategyPanel from "../components/recommendations/RecommendationStrategyPanel.vue";
import RecommendationSubjectRequirementDictsPanel from "../components/recommendations/RecommendationSubjectRequirementDictsPanel.vue";
import RecommendationVolunteerRuleDialog from "../components/recommendations/RecommendationVolunteerRuleDialog.vue";
import RecommendationVolunteerRulesPanel from "../components/recommendations/RecommendationVolunteerRulesPanel.vue";
import RecommendationVolunteerWorkbenchPanel from "../components/recommendations/RecommendationVolunteerWorkbenchPanel.vue";
import { useRecommendationsPage } from "../components/recommendations/useRecommendationsPage";

const {
  activeTab,
  addVolunteerCandidate,
  admissionFilters,
  admissionImportResult,
  admissionYearOptions,
  admissions,
  applyStrategyPresetWithConfirm,
  batchOptions,
  bootstrapProvinceScoreTransformRules,
  bootstrapSpecialTypeRules,
  bootstrapSubjectRequirementDicts,
  collegeDialogTitle,
  collegeDialogVisible,
  collegeDirectory,
  collegeFilters,
  collegeForm,
  colleges,
  compareHistoryOptions,
  compareSchemeId,
  compareSchemeError,
  compareSchemeResults,
  compareVolunteerDraftId,
  compareVolunteerDraftLoading,
  comparingScheme,
  currentVolunteerDraftId,
  deletingVolunteerDraftId,
  deletingPresetId,
  deleteVolunteerDraft,
  deleteStrategyPreset,
  downloadAdmissionTemplate,
  downloadEnrollmentPlanTemplate,
  employmentDirectionCategoryFilterOptions,
  employmentDirectionDialogTitle,
  employmentDirectionDialogVisible,
  employmentDirectionFilters,
  employmentDirectionForm,
  employmentDirectionOptions,
  employmentDirections,
  employmentMappingStrengthOptions,
  enrollmentPlanFilters,
  enrollmentPlanImportResult,
  enrollmentPlans,
  exportShandongRecommendationReport,
  exportVolunteerDraft,
  exportScheme,
  examModeOptions,
  exportingVolunteerDraftId,
  exportingShandongReport,
  gaokaoCandidateTypeOptions,
  generateShandongRecommendation,
  generatingShandongRecommendation,
  openShandongRecommendationPrintPreview,
  openRecommendationPrintPreview,
  openVolunteerDraftPrintPreview,
  reloadRecommendationSettings,
  reloadSelectedScheme,
  generating,
  generationMode,
  handleAdmissionImport,
  handleEnrollmentPlanImport,
  handleCollegeDialogClosed,
  handleEmploymentDirectionDialogClosed,
  handleCompareSchemeChange,
  handleMajorDialogClosed,
  handleMajorEmploymentMappingDialogClosed,
  handleVolunteerRuleDialogClosed,
  handleMultiCompareChange,
  historyLoadError,
  historyFilters,
  historyItems,
  latestGeneration,
  latestGenerationMessage,
  loadShandongDataHealth,
  loadAdmissions,
  loadColleges,
  loadEmploymentDirections,
  loadEnrollmentPlans,
  loadHistory,
  loadMajorEmploymentMappings,
  loadMajors,
  loadProvinceScoreTransformRules,
  loadProvinceVolunteerRules,
  loadSpecialTypeRules,
  loadSubjectRequirementDicts,
  loadVolunteerDraftComparison,
  loadVolunteerDraftDetail,
  loadVolunteerDrafts,
  loadingVolunteerDrafts,
  loadingStudentCareerPreference,
  loadingHistory,
  loadingShandongDataHealth,
  loadingSelectedScheme,
  loadVolunteerWorkbenchPreview,
  majorDialogTitle,
  majorDialogVisible,
  majorDirectory,
  majorFilters,
  majorForm,
  majorEmploymentMappingDialogTitle,
  majorEmploymentMappingDialogVisible,
  majorEmploymentMappingFilters,
  majorEmploymentMappingForm,
  majorEmploymentMappings,
  majors,
  moveVolunteerCandidate,
  multiCompareSchemeIds,
  multiCompareError,
  multiComparingSchemes,
  multiCompareSchemeResults,
  openCreateCollege,
  openCreateEmploymentDirection,
  openCreateMajor,
  openCreateMajorEmploymentMapping,
  openCreateVolunteerRule,
  openEditCollege,
  openEditEmploymentDirection,
  openEditMajor,
  openEditMajorEmploymentMapping,
  openEditVolunteerRule,
  parallelRuleModeOptions,
  exportingScheme,
  planYearOptions,
  provinceOptions,
  provinceScoreTransformRules,
  provinceVolunteerRules,
  bootstrapProvinceVolunteerRules,
  bootstrappingScoreTransformRules,
  bootstrappingSpecialTypeRules,
  bootstrappingSubjectRequirementDicts,
  bootstrappingVolunteerRules,
  recommendationForm,
  recommendationGuideCards,
  recommendationModeHint,
  recommendationModeLabel,
  recommendationStudentTypeOptions,
  recommendationSettings,
  resetAdmissionFilters,
  resetCollegeFilters,
  resetEmploymentDirectionFilters,
  resetEnrollmentPlanFilters,
  resetHistoryFilters,
  resetMajorFilters,
  resetMajorEmploymentMappingFilters,
  resetRecommendationForm,
  resetShandongRecommendation,
  resetScoreTransformRuleFilters,
  resetSpecialTypeRuleFilters,
  resetSubjectRequirementDictFilters,
  resetVolunteerWorkbench,
  resetVolunteerRuleFilters,
  remainingVolunteerSlots,
  removeVolunteerCandidate,
  reorderVolunteerCandidate,
  ruleYearOptions,
  saveRecommendationSettings,
  saveStudentCareerPreference,
  saveStrategyPreset,
  saveVolunteerDraft,
  saveVolunteerDraftAsNew,
  savingCollege,
  savingEmploymentDirection,
  savingShandongProjection,
  savingVolunteerDraft,
  savingMajor,
  savingMajorEmploymentMapping,
  savingPreset,
  savingVolunteerRule,
  savingSettings,
  schoolLevelOptions,
  selectedSchemeMeta,
  selectedSchemeError,
  selectedSchemeResults,
  selectedStrategyPresetId,
  shandongCoverageRows,
  shandongDataHealth,
  shandongRecommendationForm,
  shandongRecommendationProjection,
  shandongRecommendationResult,
  shandongResultGroups,
  scoreTransformRuleFilters,
  scoreTransformRuleYearOptions,
  specialRuleOptions,
  specialTypeRuleFilters,
  specialTypeRuleYearOptions,
  specialTypeRules,
  studentOptions,
  studentCareerPreference,
  subjectRequirementDictFilters,
  subjectRequirementDictYearOptions,
  subjectRequirementDicts,
  subjectRequirementModeOptions,
  strategyCards,
  strategyPresetForm,
  submitCollege,
  submitEmploymentDirection,
  submitMajor,
  submitMajorEmploymentMapping,
  submitRecommendation,
  submitVolunteerRule,
  summaryCards,
  syncShandongRecommendationFromRecommendation,
  targetRegionOptions,
  syncVolunteerWorkbenchFromRecommendation,
  applyStudentCareerPreference,
  viewScheme,
  volunteerRuleDialogTitle,
  volunteerRuleDialogVisible,
  volunteerRuleFilters,
  volunteerRuleForm,
  volunteerUnitTypeOptions,
  volunteerDraft,
  volunteerDraftComparison,
  volunteerDraftChecks,
  volunteerDraftName,
  volunteerLimit,
  volunteerWorkbenchForm,
  workbenchExplanation,
  workbenchBatchOptions,
  workbenchCareerIndustryOptions,
  workbenchCareerJobTypeOptions,
  workbenchExamModeOptions,
  workbenchLoading,
  workbenchPreview,
  workbenchYearOptions,
  savingStudentCareerPreference,
  savedVolunteerDrafts,
  selectedDraftPlanIds,
  selectedVolunteerRule,
  examOptions,
} = useRecommendationsPage();
</script>

<style scoped>
.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.9fr);
  gap: 20px;
}

.guide-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.guide-card {
  padding: 18px 20px;
}

.guide-card span {
  color: #6d8194;
  font-size: 13px;
}

.guide-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3245;
  font-size: 22px;
  font-weight: 760;
  line-height: 1.35;
}

.guide-card p {
  margin: 8px 0 0;
  color: #73879b;
  line-height: 1.55;
  font-size: 13px;
}

.summary-panel,
.workflow-panel,
.panel-block {
  padding: 24px;
}

.summary-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(300px, 0.95fr);
  gap: 22px;
  background:
    radial-gradient(circle at top left, rgba(180, 219, 243, 0.34), transparent 26%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(244, 248, 252, 0.94));
}

.recommendation-chip-row {
  max-width: 760px;
}

.summary-copy h3 {
  margin: 12px 0 0;
  color: #203549;
  font-size: 30px;
  line-height: 1.2;
}

.summary-copy p {
  margin: 12px 0 0;
  color: #5f7387;
  line-height: 1.7;
}

.summary-badge {
  display: inline-flex;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f6c98;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.summary-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-content: start;
  gap: 14px;
}

.summary-metric {
  padding: 18px;
  border-radius: 20px;
  background: rgba(248, 251, 254, 0.96);
  border: 1px solid rgba(123, 142, 161, 0.12);
}

.summary-metric-label {
  color: #688095;
  font-size: 13px;
}

.summary-metric-value {
  margin-top: 10px;
  font-size: 28px;
  font-weight: 760;
  color: #1e3348;
}

.summary-metric-help {
  margin-top: 8px;
  color: #72879b;
  font-size: 13px;
  line-height: 1.5;
}

.tone-blue {
  box-shadow: inset 0 4px 0 rgba(31, 108, 152, 0.85);
}

.tone-indigo {
  box-shadow: inset 0 4px 0 rgba(79, 89, 167, 0.82);
}

.tone-amber {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.88);
}

.tone-slate {
  box-shadow: inset 0 4px 0 rgba(79, 101, 122, 0.72);
}

.tone-green {
  box-shadow: inset 0 4px 0 rgba(67, 142, 110, 0.78);
}

.tone-teal {
  box-shadow: inset 0 4px 0 rgba(44, 142, 132, 0.78);
}

.section-head.compact {
  margin-bottom: 10px;
}

.workflow-list {
  display: grid;
  gap: 12px;
}

.workflow-panel {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 252, 0.94));
}

.workflow-item {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
  padding: 16px;
  border-radius: 20px;
  background: rgba(248, 251, 254, 0.88);
  border: 1px solid rgba(121, 138, 154, 0.14);
}

.workflow-item span {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(31, 108, 152, 0.14), rgba(209, 141, 72, 0.14));
  color: #26425d;
  font-size: 13px;
  font-weight: 800;
}

.workflow-item strong {
  display: block;
  color: #20354a;
}

.workflow-item p {
  margin: 6px 0 0;
  color: #6a7f92;
  line-height: 1.5;
}

.recommend-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
  gap: 18px;
}

.recommend-side-stack {
  display: grid;
  gap: 18px;
}

:deep(.recommendation-tabs .el-tabs__content) {
  overflow: visible;
}

@media (max-width: 1280px) {
  .summary-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1080px) {
  .hero-grid,
  .guide-grid,
  .recommend-layout,
  .summary-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
