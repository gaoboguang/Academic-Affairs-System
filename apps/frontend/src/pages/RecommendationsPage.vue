<template>
  <AppPage
    eyebrow="高考志愿 / 智能推荐向导"
    title="高考志愿推荐向导"
    description="按考生条件、意向偏好、智能筛选和志愿草稿复核组织一次完整辅导；结果只作本地参考，正式填报仍以省级志愿系统为准。"
    :meta="pageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button @click="$router.push('/gaokao-pathways')"
          >升学方案中心</el-button
        >
        <el-dropdown
          trigger="click"
          popper-class="recommendation-advanced-menu"
          :teleported="false"
          @command="handleAdvancedToolCommand"
        >
          <el-button data-testid="recommendation-advanced-tools-button">高级工具</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="recommendations">推荐中心</el-dropdown-item>
              <el-dropdown-item command="shandong-workbench">山东普通类推荐</el-dropdown-item>
              <el-dropdown-item command="history">历史方案</el-dropdown-item>
              <el-dropdown-item command="colleges">数据与规则</el-dropdown-item>
              <el-dropdown-item command="data-health">数据健康</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button
          v-if="activeTab !== 'volunteer-workbench'"
          type="primary"
          @click="activeTab = 'volunteer-workbench'"
          >回到推荐向导</el-button
        >
      </div>
    </template>

    <div
      v-if="recommendationLoadBannerVisible"
      class="recommendation-load-banner"
      :class="{ 'tone-warning': recommendationLoadBannerTone === 'warning' }"
    >
      <div>
        <strong>{{ recommendationLoadBannerTitle }}</strong>
        <p>{{ recommendationLoadBannerDescription }}</p>
      </div>
      <div class="action-row">
        <el-button
          v-if="recommendationPageLoadError"
          :loading="recommendationPageLoading"
          @click="retryRecommendationPageLoad"
        >
          重新加载推荐中心
        </el-button>
        <el-button
          v-if="activeRecommendationTabLoadError"
          type="primary"
          :loading="activeRecommendationTabLoading"
          @click="reloadActiveRecommendationTab"
        >
          重新加载当前页签
        </el-button>
      </div>
    </div>

    <section
      v-if="activePrimarySection === 'workbench'"
      class="recommendation-section-stack"
    >
      <div class="guide-status-strip">
        <article v-for="item in guideStatusItems" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </article>
        <button type="button" class="risk-summary-button" @click="activeTab = 'data-health'">
          数据风险 {{ shandongDataHealth?.gaps?.length ?? 0 }} 条
        </button>
      </div>

      <el-collapse class="risk-review-collapse compact-risk">
        <el-collapse-item name="risk-review">
          <template #title>
            <span class="risk-review-title">人工复核提醒</span>
            <span class="risk-review-count">{{ recommendationGlobalRiskNotices.length }} 条</span>
          </template>
          <ul class="risk-review-list">
            <li v-for="notice in recommendationGlobalRiskNotices" :key="notice">
              {{ notice }}
            </li>
          </ul>
        </el-collapse-item>
      </el-collapse>

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
        :volunteer-rules="provinceVolunteerRules"
        :preview="workbenchPreview"
        :draft="volunteerDraft"
        v-model:draft-name="volunteerDraftName"
        :loading="workbenchLoading"
        :workbench-preview-error="workbenchPreviewError"
        :saving-draft="savingVolunteerDraft"
        :exporting-draft-id="exportingVolunteerDraftId"
        :loading-saved-drafts="loadingVolunteerDrafts"
        :volunteer-drafts-error="volunteerDraftsError"
        :deleting-draft-id="deletingVolunteerDraftId"
        :current-draft-id="currentVolunteerDraftId"
        :saved-drafts="savedVolunteerDrafts"
        :compare-draft-id="compareVolunteerDraftId"
        :compare-draft-loading="compareVolunteerDraftLoading"
        :compare-volunteer-draft-error="compareVolunteerDraftError"
        :draft-comparison="volunteerDraftComparison"
        :selected-plan-ids="selectedDraftPlanIds"
        :selected-rule="selectedVolunteerRule"
        :workbench-explanation="workbenchExplanation"
        :draft-checks="volunteerDraftChecks"
        :guide-preview="volunteerGuidePreview"
        :guide-groups="volunteerGuideGroups"
        :guide-options="volunteerGuideOptions"
        :volunteer-limit="volunteerLimit"
        :remaining-slots="remainingVolunteerSlots"
        :exam-score-autofill-notice="examScoreAutofillNotice"
        :loading-exam-score-autofill="loadingExamScoreAutofill"
        :loading-volunteer-guide-options="loadingVolunteerGuideOptions"
        :volunteer-guide-options-error="volunteerGuideOptionsError"
        :student-profile-error="studentProfileError"
        :art-comprehensive-score-preview="volunteerSelectedArtFormula"
        @load-preview="loadVolunteerWorkbenchPreview"
        @reset="resetVolunteerWorkbench"
        @sync-from-recommendation="syncVolunteerWorkbenchFromRecommendation"
        @apply-exam-score-autofill="applyCurrentExamScoreToWorkbench"
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
    </section>

    <section
      v-else-if="activePrimarySection === 'legacy-recommendations'"
      class="recommendation-section-stack"
    >
      <div class="advanced-section-head">
        <div>
          <h3>推荐中心</h3>
          <p>保留旧推荐方案和策略能力；日常志愿辅导建议优先回到分步向导。</p>
        </div>
        <el-button type="primary" @click="activeTab = 'volunteer-workbench'">回到推荐向导</el-button>
      </div>

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
    </section>

    <section
      v-else-if="activePrimarySection === 'shandong-workbench'"
      class="recommendation-section-stack"
    >
      <div class="advanced-section-head">
        <div>
          <h3>山东普通类推荐</h3>
          <p>保留山东普通类专项工作台；分步向导会继续复用同一批本地数据。</p>
        </div>
        <el-button type="primary" @click="activeTab = 'volunteer-workbench'">回到推荐向导</el-button>
      </div>
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
            @sync-from-recommendation="
              syncShandongRecommendationFromRecommendation
            "
            @print-report="openShandongRecommendationPrintPreview"
            @export-report="exportShandongRecommendationReport"
          />
    </section>

    <section
      v-else-if="activePrimarySection === 'history'"
      class="history-layout"
    >
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
    </section>

    <section
      v-else-if="activePrimarySection === 'data-rules'"
      class="recommendation-section-stack"
    >
      <el-tabs v-model="activeTab" class="secondary-tabs data-rules-tabs">
        <el-tab-pane label="院校库" name="colleges">
          <RecommendationCollegesPanel
            :colleges="colleges"
            :filters="collegeFilters"
            :pagination="collegePagination"
            :province-options="provinceOptions"
            :loading="loadingColleges"
            :load-error="collegesLoadError"
            @load="loadColleges({ resetPage: true })"
            @reset="resetCollegeFilters"
            @page-change="handleCollegePageChange"
            @page-size-change="handleCollegePageSizeChange"
            @create="openCreateCollege"
            @edit="openEditCollege"
            @open-detail="openCollegeDetail"
          />
        </el-tab-pane>

        <el-tab-pane label="专业库" name="majors">
          <RecommendationMajorsPanel
            :majors="majors"
            :filters="majorFilters"
            :pagination="majorPagination"
            :loading="loadingMajors"
            :load-error="majorsLoadError"
            @load="loadMajors({ resetPage: true })"
            @reset="resetMajorFilters"
            @page-change="handleMajorPageChange"
            @page-size-change="handleMajorPageSizeChange"
            @create="openCreateMajor"
            @edit="openEditMajor"
            @open-detail="openMajorDetail"
          />
        </el-tab-pane>

        <el-tab-pane label="就业方向库" name="employment-directions">
          <RecommendationEmploymentDirectionsPanel
            :directions="employmentDirections"
            :filters="employmentDirectionFilters"
            :category-options="employmentDirectionCategoryFilterOptions"
            :loading="loadingEmploymentDirections"
            :load-error="employmentDirectionsLoadError"
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
            :pagination="majorEmploymentMappingPagination"
            :loading="loadingMajorEmploymentMappings"
            :load-error="majorEmploymentMappingsLoadError"
            @load="loadMajorEmploymentMappings({ resetPage: true })"
            @reset="resetMajorEmploymentMappingFilters"
            @page-change="handleMajorEmploymentMappingPageChange"
            @page-size-change="handleMajorEmploymentMappingPageSizeChange"
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
            :pagination="enrollmentPlanPagination"
            :loading="loadingEnrollmentPlans"
            :load-error="enrollmentPlansLoadError"
            :importing="importingEnrollmentPlans"
            @download-template="downloadEnrollmentPlanTemplate"
            @import="handleEnrollmentPlanImport"
            @load="loadEnrollmentPlans({ resetPage: true })"
            @reset="resetEnrollmentPlanFilters"
            @page-change="handleEnrollmentPlanPageChange"
            @page-size-change="handleEnrollmentPlanPageSizeChange"
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
            :pagination="admissionPagination"
            :loading="loadingAdmissions"
            :load-error="admissionsLoadError"
            :importing="importingAdmissions"
            @download-template="downloadAdmissionTemplate"
            @import="handleAdmissionImport"
            @load="loadAdmissions({ resetPage: true })"
            @reset="resetAdmissionFilters"
            @page-change="handleAdmissionPageChange"
            @page-size-change="handleAdmissionPageSizeChange"
          />
        </el-tab-pane>

        <el-tab-pane label="省份规则" name="volunteer-rules">
          <RecommendationVolunteerRulesPanel
            :rules="provinceVolunteerRules"
            :filters="volunteerRuleFilters"
            :bootstrapping="bootstrappingVolunteerRules"
            :loading="loadingVolunteerRules"
            :load-error="volunteerRulesLoadError"
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
            :loading="loadingSpecialTypeRules"
            :load-error="specialTypeRulesLoadError"
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
            :loading="loadingScoreTransformRules"
            :load-error="scoreTransformRulesLoadError"
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
            :loading="loadingSubjectRequirementDicts"
            :load-error="subjectRequirementDictsLoadError"
            :year-options="subjectRequirementDictYearOptions"
            :province-options="provinceOptions"
            :exam-mode-options="examModeOptions"
            @load="loadSubjectRequirementDicts"
            @bootstrap="bootstrapSubjectRequirementDicts"
            @reset="resetSubjectRequirementDictFilters"
          />
        </el-tab-pane>
      </el-tabs>
    </section>

    <section v-else class="recommendation-section-stack">
      <div class="data-health-grid">
        <article class="soft-card data-health-card">
          <span>健康摘要</span>
          <strong>{{ shandongDataHealth?.summary || "待加载" }}</strong>
          <p>
            {{
              shandongDataHealth
                ? "山东覆盖、P0 缺口和发布状态来自本地数据健康接口。"
                : "点击刷新读取当前本地库状态。"
            }}
          </p>
        </article>
        <article class="soft-card data-health-card">
          <span>P0 缺口</span>
          <strong>{{ shandongDataHealth?.gaps?.length ?? 0 }}</strong>
          <p>缺口存在时，志愿结果必须保留人工复核。</p>
        </article>
        <article class="soft-card data-health-card">
          <span>2026 发布状态</span>
          <strong>{{
            shandongDataHealth?.publication_status?.length ?? 0
          }}</strong>
          <p>正式数据未发布前，不把模拟结果包装成录取结论。</p>
        </article>
      </div>

      <section class="soft-card panel-block">
        <div class="section-head">
          <div>
            <h3>数据健康</h3>
            <p>
              只读查看山东覆盖、P0
              缺口和人工复核入口；维护动作收在“数据与规则”。
            </p>
          </div>
          <div class="action-row">
            <el-button
              :loading="loadingShandongDataHealth"
              @click="loadShandongDataHealth"
              >刷新</el-button
            >
            <el-button @click="$router.push('/gaokao-data')"
              >打开高考数据看板</el-button
            >
          </div>
        </div>

        <div class="health-columns">
          <article class="health-column">
            <h4>2023-2025 覆盖矩阵</h4>
            <el-table :data="shandongCoverageRows" size="small" stripe>
              <el-table-column label="年份" prop="year" width="90" />
              <el-table-column
                label="一分一段"
                prop="scoreRank"
                min-width="120"
              />
              <el-table-column
                label="省控线"
                prop="scoreLine"
                min-width="120"
              />
              <el-table-column label="招生计划" prop="plan" min-width="120" />
              <el-table-column label="录取结果" prop="result" min-width="120" />
            </el-table>
            <el-empty
              v-if="!shandongCoverageRows.length"
              description="暂无覆盖矩阵，请刷新数据健康"
            />
          </article>

          <article class="health-column">
            <h4>P0 缺口</h4>
            <ul v-if="shandongDataHealth?.gaps.length" class="health-gap-list">
              <li v-for="gap in shandongDataHealth.gaps" :key="gap">
                {{ gap }}
              </li>
            </ul>
            <p v-else class="muted-copy">
              当前未加载缺口，或 P0 规则内未发现明显缺口。
            </p>
          </article>
        </div>
      </section>
    </section>

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
  </AppPage>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRouter } from "vue-router";

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
import { RECOMMENDATION_GLOBAL_RISK_NOTICES } from "../components/recommendations/recommendationCopy";
import { useRecommendationsPage } from "../components/recommendations/useRecommendationsPage";
import AppPage from "../components/ui/AppPage.vue";
import type { PageMetaItem } from "../components/ui/types";

const recommendationGlobalRiskNotices = RECOMMENDATION_GLOBAL_RISK_NOTICES;
const router = useRouter();

const {
  activeTab,
  activeRecommendationTabLoadError,
  activeRecommendationTabLoading,
  addVolunteerCandidate,
  admissionFilters,
  admissionImportResult,
  admissionPagination,
  admissionYearOptions,
  admissionsLoadError,
  admissions,
  applyCurrentExamScoreToWorkbench,
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
  collegePagination,
  collegesLoadError,
  colleges,
  compareHistoryOptions,
  compareSchemeId,
  compareSchemeError,
  compareSchemeResults,
  compareVolunteerDraftId,
  compareVolunteerDraftError,
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
  employmentDirectionsLoadError,
  employmentMappingStrengthOptions,
  enrollmentPlanFilters,
  enrollmentPlanImportResult,
  enrollmentPlanPagination,
  enrollmentPlansLoadError,
  enrollmentPlans,
  examScoreAutofillNotice,
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
  handleAdmissionPageChange,
  handleAdmissionPageSizeChange,
  handleCollegePageChange,
  handleCollegePageSizeChange,
  handleEnrollmentPlanImport,
  handleEnrollmentPlanPageChange,
  handleEnrollmentPlanPageSizeChange,
  handleCollegeDialogClosed,
  handleEmploymentDirectionDialogClosed,
  handleCompareSchemeChange,
  handleMajorDialogClosed,
  handleMajorEmploymentMappingDialogClosed,
  handleVolunteerRuleDialogClosed,
  handleMultiCompareChange,
  handleMajorPageChange,
  handleMajorPageSizeChange,
  handleMajorEmploymentMappingPageChange,
  handleMajorEmploymentMappingPageSizeChange,
  importingAdmissions,
  importingEnrollmentPlans,
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
  loadingExamScoreAutofill,
  loadingVolunteerGuideOptions,
  loadingVolunteerDrafts,
  loadingAdmissions,
  loadingEnrollmentPlans,
  loadingStudentCareerPreference,
  loadingHistory,
  loadingEmploymentDirections,
  loadingColleges,
  loadingMajorEmploymentMappings,
  loadingMajors,
  loadingScoreTransformRules,
  loadingShandongDataHealth,
  loadingSelectedScheme,
  loadingSpecialTypeRules,
  loadVolunteerWorkbenchPreview,
  loadingSubjectRequirementDicts,
  loadingVolunteerRules,
  majorDialogTitle,
  majorDialogVisible,
  majorDirectory,
  majorFilters,
  majorForm,
  majorPagination,
  majorEmploymentMappingDialogTitle,
  majorEmploymentMappingDialogVisible,
  majorEmploymentMappingFilters,
  majorEmploymentMappingForm,
  majorEmploymentMappingsLoadError,
  majorEmploymentMappingPagination,
  majorEmploymentMappings,
  majorsLoadError,
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
  recommendationModeHint,
  recommendationModeLabel,
  recommendationPageLoadError,
  recommendationPageLoading,
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
  reloadActiveRecommendationTab,
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
  scoreTransformRulesLoadError,
  scoreTransformRuleYearOptions,
  specialRuleOptions,
  specialTypeRuleFilters,
  specialTypeRulesLoadError,
  specialTypeRuleYearOptions,
  specialTypeRules,
  studentOptions,
  studentCareerPreference,
  studentProfileError,
  subjectRequirementDictFilters,
  subjectRequirementDictsLoadError,
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
  retryRecommendationPageLoad,
  syncVolunteerWorkbenchFromRecommendation,
  applyStudentCareerPreference,
  viewScheme,
  volunteerRuleDialogTitle,
  volunteerRuleDialogVisible,
  volunteerRuleFilters,
  volunteerRuleForm,
  volunteerRulesLoadError,
  volunteerUnitTypeOptions,
  volunteerDraft,
  volunteerDraftsError,
  volunteerDraftComparison,
  volunteerDraftChecks,
  volunteerGuideGroups,
  volunteerGuideOptions,
  volunteerGuideOptionsError,
  volunteerGuidePreview,
  volunteerSelectedArtFormula,
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
  workbenchPreviewError,
  workbenchYearOptions,
  savingStudentCareerPreference,
  savedVolunteerDrafts,
  selectedDraftPlanIds,
  selectedVolunteerRule,
  examOptions,
} = useRecommendationsPage();

type PrimarySectionKey =
  | "workbench"
  | "legacy-recommendations"
  | "shandong-workbench"
  | "history"
  | "data-rules"
  | "data-health";

interface GuideStatusItem {
  label: string;
  value: string;
}

const dataRuleTabs = new Set([
  "colleges",
  "majors",
  "employment-directions",
  "major-employment-maps",
  "enrollment-plans",
  "admissions",
  "volunteer-rules",
  "special-type-rules",
  "score-transform-rules",
  "subject-requirements",
]);

const recommendationTabLabels: Record<string, string> = {
  "volunteer-workbench": "推荐向导",
  recommendations: "推荐中心",
  "shandong-workbench": "山东普通类推荐",
  history: "历史方案",
  colleges: "院校库",
  majors: "专业库",
  "employment-directions": "就业方向库",
  "major-employment-maps": "专业就业映射",
  "enrollment-plans": "招生计划库",
  admissions: "录取库",
  "volunteer-rules": "省份规则",
  "special-type-rules": "特殊类型规则",
  "score-transform-rules": "赋分规则",
  "subject-requirements": "选科字典",
  "data-health": "数据健康",
};

const pageMeta = computed<PageMetaItem[]>(() =>
  summaryCards.value.slice(0, 4).map((item) => ({
    label: item.label,
    value: item.value,
  })),
);

const activePrimarySection = computed<PrimarySectionKey>(() => {
  if (activeTab.value === "history") return "history";
  if (activeTab.value === "data-health") return "data-health";
  if (dataRuleTabs.has(activeTab.value)) return "data-rules";
  if (activeTab.value === "recommendations") return "legacy-recommendations";
  if (activeTab.value === "shandong-workbench") return "shandong-workbench";
  return "workbench";
});

const activeRecommendationTabLabel = computed(() => recommendationTabLabels[activeTab.value] ?? "当前页签");
const recommendationLoadBannerVisible = computed(
  () =>
    Boolean(recommendationPageLoadError.value)
    || Boolean(activeRecommendationTabLoadError.value)
    || recommendationPageLoading.value
    || activeRecommendationTabLoading.value,
);
const recommendationLoadBannerTone = computed(() =>
  recommendationPageLoadError.value || activeRecommendationTabLoadError.value ? "warning" : "info",
);
const recommendationLoadBannerTitle = computed(() => {
  if (recommendationPageLoadError.value) return "推荐中心基础数据加载失败";
  if (activeRecommendationTabLoadError.value) return `${activeRecommendationTabLabel.value}加载失败`;
  if (recommendationPageLoading.value) return "正在加载推荐中心基础数据";
  return `正在加载${activeRecommendationTabLabel.value}`;
});
const recommendationLoadBannerDescription = computed(() => {
  if (recommendationPageLoadError.value) return recommendationPageLoadError.value;
  if (activeRecommendationTabLoadError.value) return activeRecommendationTabLoadError.value;
  if (recommendationPageLoading.value) return "正在读取学生、考试、策略、历史方案和就业方向数据。";
  return "正在读取当前页签所需数据，完成后会保留已加载的可用区块。";
});

const selectedStudentName = computed(() => {
  const student = studentOptions.value.find((item) => item.id === volunteerWorkbenchForm.student_id);
  return volunteerGuidePreview.value?.student_name || student?.name || "未选择";
});

const selectedExamName = computed(() => {
  const exam = examOptions.value.find((item) => item.id === volunteerWorkbenchForm.exam_id);
  return volunteerGuidePreview.value?.exam_name || exam?.name || "未选择";
});

const guideStatusItems = computed<GuideStatusItem[]>(() => [
  { label: "学生", value: selectedStudentName.value },
  { label: "考试", value: selectedExamName.value },
  { label: "批次", value: volunteerWorkbenchForm.batch || "未选择" },
  {
    label: "候选 / 草稿",
    value: `${workbenchPreview.value?.candidate_count ?? volunteerGuidePreview.value?.source_preview.candidate_count ?? 0} / ${volunteerDraft.value.length}`,
  },
]);

function handleAdvancedToolCommand(command: string | number | object): void {
  if (typeof command !== "string") return;
  activeTab.value = command;
}

function openCollegeDetail(collegeId: number): void {
  void router.push(`/colleges/${collegeId}`);
}

function openMajorDetail(majorId: number): void {
  void router.push(`/majors/${majorId}`);
}
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.risk-review-collapse {
  border: 1px solid rgba(213, 151, 67, 0.28);
  border-radius: 8px;
  overflow: hidden;
  background: #fffaf1;
}

:deep(.risk-review-collapse .el-collapse-item__header) {
  padding: 0 16px;
  background: #fffaf1;
  color: #7a4c0f;
  font-weight: 760;
}

:deep(.risk-review-collapse .el-collapse-item__content) {
  padding: 0 18px 16px;
}

.risk-review-title {
  margin-right: 10px;
}

.risk-review-count {
  color: #9c6a20;
  font-size: 13px;
}

.risk-review-list {
  margin: 0;
  padding-left: 18px;
  color: #7a4c0f;
  line-height: 1.7;
}

.recommendation-load-banner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(37, 115, 161, 0.2);
  border-radius: 8px;
  background: #f4f9fd;
  color: #21394f;
}

.recommendation-load-banner.tone-warning {
  border-color: rgba(201, 121, 45, 0.28);
  background: #fff8ed;
}

.recommendation-load-banner strong {
  display: block;
  color: #20364b;
}

.recommendation-load-banner p {
  margin: 5px 0 0;
  color: #667b8e;
  line-height: 1.55;
}

.guide-status-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
}

.guide-status-strip article,
.risk-summary-button {
  min-height: 68px;
  padding: 14px 16px;
  border: 1px solid rgba(124, 142, 158, 0.18);
  border-radius: 8px;
  background: #ffffff;
  color: #25394f;
}

.risk-summary-button {
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.16s ease,
    background 0.16s ease;
}

.guide-status-strip span,
.data-health-card span {
  display: block;
  color: #667b8e;
  font-size: 13px;
}

.guide-status-strip strong,
.data-health-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3245;
  font-size: 18px;
  line-height: 1.3;
}

.risk-summary-button:hover {
  border-color: rgba(37, 115, 161, 0.36);
  background: #f5f9fd;
}

.recommendation-section-stack,
.history-layout {
  display: grid;
  gap: 16px;
}

.data-health-card p {
  margin: 7px 0 0;
  color: #6c8194;
  line-height: 1.55;
}

.data-health-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.data-health-card {
  padding: 18px;
}

.advanced-section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px;
  border: 1px solid rgba(124, 142, 158, 0.14);
  border-radius: 8px;
  background: #ffffff;
}

.advanced-section-head h3 {
  margin: 0;
  color: #20364b;
}

.advanced-section-head p {
  margin: 6px 0 0;
  color: #667b8e;
  line-height: 1.55;
}

.secondary-tabs {
  background: #ffffff;
  border: 1px solid rgba(124, 142, 158, 0.14);
  border-radius: 8px;
  padding: 0 16px 16px;
}

:deep(.secondary-tabs .el-tabs__content) {
  overflow: visible;
}

.data-rules-tabs {
  padding-top: 0;
}

.health-columns {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.65fr);
  gap: 16px;
}

.health-column {
  min-width: 0;
  padding: 16px;
  border: 1px solid rgba(124, 142, 158, 0.14);
  border-radius: 8px;
  background: #f8fbfd;
}

.health-column h4 {
  margin: 0 0 12px;
  color: #25394f;
}

.health-gap-list {
  margin: 0;
  padding-left: 18px;
  color: #5d7082;
  line-height: 1.7;
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

.muted-copy {
  color: #7d8f9d;
  font-size: 13px;
}

@media (max-width: 1080px) {
  .guide-status-strip,
  .workbench-priority-grid,
  .data-health-grid,
  .health-columns,
  .recommend-layout,
  .recommend-side-stack {
    grid-template-columns: 1fr;
  }
}
</style>
