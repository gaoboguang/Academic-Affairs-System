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
        <el-button @click="activeTab = 'data-health'">数据健康</el-button>
        <el-button @click="activeTab = 'colleges'">打开数据与规则</el-button>
        <el-button type="primary" @click="activeTab = 'volunteer-workbench'"
          >回到推荐向导</el-button
        >
      </div>
    </template>

    <AppStatGrid :items="pageStatCards" :columns="4" />

    <el-collapse class="risk-review-collapse">
      <el-collapse-item name="risk-review">
        <template #title>
          <span class="risk-review-title">数据风险与人工复核</span>
          <span class="risk-review-count"
            >{{ recommendationGlobalRiskNotices.length }} 条</span
          >
        </template>
        <ul class="risk-review-list">
          <li v-for="notice in recommendationGlobalRiskNotices" :key="notice">
            {{ notice }}
          </li>
        </ul>
      </el-collapse-item>
    </el-collapse>

    <nav class="recommendation-section-nav" aria-label="高考志愿工作台分区">
      <button
        v-for="section in primarySections"
        :key="section.key"
        type="button"
        class="section-nav-button"
        :class="{ active: activePrimarySection === section.key }"
        @click="switchPrimarySection(section.key)"
      >
        <span>{{ section.label }}</span>
        <strong>{{ section.value }}</strong>
      </button>
    </nav>

    <section
      v-if="activePrimarySection === 'workbench'"
      class="recommendation-section-stack"
    >
      <AppFilterBar
        title="考生条件"
        description="先确认学生、考试、年份、批次、科类和成绩/位次；生成后再进入智能筛选和草稿复核。"
        sticky
      >
        <div class="command-fields">
          <el-select
            v-model="volunteerWorkbenchForm.student_id"
            filterable
            placeholder="学生"
          >
            <el-option
              v-for="student in studentOptions"
              :key="student.id"
              :label="`${student.student_no} - ${student.name}`"
              :value="student.id"
            />
          </el-select>
          <el-select
            v-model="volunteerWorkbenchForm.exam_id"
            filterable
            placeholder="参考考试"
          >
            <el-option
              v-for="exam in examOptions"
              :key="exam.id"
              :label="exam.name"
              :value="exam.id"
            />
          </el-select>
          <el-select
            v-model="volunteerWorkbenchForm.province"
            filterable
            placeholder="省份"
          >
            <el-option
              v-for="province in provinceOptions"
              :key="province"
              :label="province"
              :value="province"
            />
          </el-select>
          <el-select
            v-model="volunteerWorkbenchForm.target_year"
            filterable
            placeholder="年份"
          >
            <el-option
              v-for="year in workbenchYearOptions"
              :key="year"
              :label="String(year)"
              :value="year"
            />
          </el-select>
          <el-select
            v-model="volunteerWorkbenchForm.batch"
            clearable
            filterable
            placeholder="批次"
          >
            <el-option
              v-for="batch in workbenchBatchOptions"
              :key="batch"
              :label="batch"
              :value="batch"
            />
          </el-select>
          <el-select
            v-model="volunteerWorkbenchForm.exam_mode"
            clearable
            filterable
            placeholder="科类/模式"
          >
            <el-option
              v-for="mode in workbenchExamModeOptions"
              :key="mode"
              :label="mode"
              :value="mode"
            />
          </el-select>
          <el-select
            v-model="volunteerWorkbenchForm.score_input_mode"
            placeholder="成绩/位次来源"
          >
            <el-option
              v-for="item in scoreInputModeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-button
            type="primary"
            :loading="workbenchLoading"
            @click="loadVolunteerWorkbenchPreview"
            >生成智能筛选</el-button
          >
        </div>
      </AppFilterBar>

      <div class="guide-step-grid">
        <article
          v-for="step in volunteerGuideStepCards"
          :key="step.key"
          class="soft-card guide-step-card"
          :class="`status-${step.status}`"
        >
          <span>{{ step.title }}</span>
          <strong>{{ step.summary }}</strong>
        </article>
      </div>

      <section class="soft-card guide-readiness-card">
        <div class="section-head compact">
          <div>
            <h3>生成前复核</h3>
            <p>系统会把缺位次、缺规则、选科待核、特殊类型初筛等事项集中列出。</p>
          </div>
          <el-tag :type="volunteerGuideReadiness.status === 'blocked' ? 'danger' : volunteerGuideReadiness.status === 'warning' ? 'warning' : 'success'" effect="plain">
            {{
              volunteerGuideReadiness.status === "blocked"
                ? "需要先处理"
                : volunteerGuideReadiness.status === "warning"
                ? "可生成但需复核"
                : "条件就绪"
            }}
          </el-tag>
        </div>
        <div class="guide-readiness-list">
          <article
            v-for="item in volunteerGuideReadiness.items"
            :key="`${item.code}-${item.detail}`"
            class="guide-readiness-item"
            :class="`level-${item.level}`"
          >
            <strong>{{ item.title }}</strong>
            <p>{{ item.detail }}</p>
          </article>
        </div>
      </section>

      <el-tabs v-model="activeTab" class="secondary-tabs">
        <el-tab-pane label="志愿推荐向导" name="volunteer-workbench">
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
            :guide-preview="volunteerGuidePreview"
            :guide-groups="volunteerGuideGroups"
            :volunteer-limit="volunteerLimit"
            :remaining-slots="remainingVolunteerSlots"
            :exam-score-autofill-notice="examScoreAutofillNotice"
            :loading-exam-score-autofill="loadingExamScoreAutofill"
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
            @sync-from-recommendation="
              syncShandongRecommendationFromRecommendation
            "
            @print-report="openShandongRecommendationPrintPreview"
            @export-report="exportShandongRecommendationReport"
          />
        </el-tab-pane>
      </el-tabs>
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
import { scoreInputModeOptions } from "../components/recommendations/helpers";
import { RECOMMENDATION_GLOBAL_RISK_NOTICES } from "../components/recommendations/recommendationCopy";
import { useRecommendationsPage } from "../components/recommendations/useRecommendationsPage";
import AppFilterBar from "../components/ui/AppFilterBar.vue";
import AppPage from "../components/ui/AppPage.vue";
import AppStatGrid from "../components/ui/AppStatGrid.vue";
import type {
  PageMetaItem,
  StatCardItem,
  UiTone,
} from "../components/ui/types";

const recommendationGlobalRiskNotices = RECOMMENDATION_GLOBAL_RISK_NOTICES;
const router = useRouter();

const {
  activeTab,
  addVolunteerCandidate,
  admissionFilters,
  admissionImportResult,
  admissionPagination,
  admissionYearOptions,
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
  enrollmentPlanPagination,
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
  majorPagination,
  majorEmploymentMappingDialogTitle,
  majorEmploymentMappingDialogVisible,
  majorEmploymentMappingFilters,
  majorEmploymentMappingForm,
  majorEmploymentMappingPagination,
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
  volunteerGuideGroups,
  volunteerGuidePreview,
  volunteerGuideReadiness,
  volunteerGuideStepCards,
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

type PrimarySectionKey = "workbench" | "history" | "data-rules" | "data-health";

const workbenchTabs = new Set([
  "volunteer-workbench",
  "recommendations",
  "shandong-workbench",
]);
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

const primarySections = computed(() => [
  {
    key: "workbench" as const,
    label: "工作台",
    value: volunteerDraft.value.length
      ? `${volunteerDraft.value.length} 条草稿`
      : "默认入口",
  },
  {
    key: "history" as const,
    label: "历史方案",
    value: historyItems.value.length
      ? `${historyItems.value.length} 份`
      : "待生成",
  },
  {
    key: "data-rules" as const,
    label: "数据与规则",
    value: `${collegePagination.total || colleges.value.length} 所院校`,
  },
  {
    key: "data-health" as const,
    label: "数据健康",
    value: shandongDataHealth.value
      ? `${shandongDataHealth.value.gaps.length} 条缺口`
      : "待刷新",
  },
]);

function normalizeTone(tone?: string): UiTone {
  if (!tone) return "neutral";
  if (tone.includes("green") || tone.includes("teal")) return "success";
  if (tone.includes("amber")) return "warning";
  if (tone.includes("blue") || tone.includes("indigo")) return "primary";
  return "neutral";
}

const pageMeta = computed<PageMetaItem[]>(() =>
  summaryCards.value.slice(0, 4).map((item) => ({
    label: item.label,
    value: item.value,
  })),
);

const pageStatCards = computed<StatCardItem[]>(() =>
  summaryCards.value.map((item) => ({
    label: item.label,
    value: item.value,
    help: item.help,
    tone: normalizeTone(item.tone),
  })),
);

const activePrimarySection = computed<PrimarySectionKey>(() => {
  if (activeTab.value === "history") return "history";
  if (activeTab.value === "data-health") return "data-health";
  if (dataRuleTabs.has(activeTab.value)) return "data-rules";
  if (workbenchTabs.has(activeTab.value)) return "workbench";
  return "workbench";
});

function switchPrimarySection(section: PrimarySectionKey): void {
  const targetTab: Record<PrimarySectionKey, string> = {
    workbench: "volunteer-workbench",
    history: "history",
    "data-rules": "colleges",
    "data-health": "data-health",
  };
  activeTab.value = targetTab[section];
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

.recommendation-section-nav {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.section-nav-button {
  min-height: 74px;
  padding: 14px 16px;
  border: 1px solid rgba(124, 142, 158, 0.18);
  border-radius: 8px;
  background: #ffffff;
  color: #25394f;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.16s ease,
    box-shadow 0.16s ease,
    background 0.16s ease;
}

.section-nav-button span,
.guide-step-card span,
.data-health-card span {
  display: block;
  color: #667b8e;
  font-size: 13px;
}

.section-nav-button strong,
.guide-step-card strong,
.data-health-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3245;
  font-size: 20px;
  line-height: 1.3;
}

.section-nav-button.active {
  border-color: rgba(37, 115, 161, 0.45);
  background: #f2f8fc;
  box-shadow: inset 0 3px 0 rgba(37, 115, 161, 0.78);
}

.recommendation-section-stack,
.history-layout {
  display: grid;
  gap: 16px;
}

.guide-step-card strong,
.data-health-card p {
  margin: 7px 0 0;
  color: #6c8194;
  line-height: 1.55;
}

.command-fields {
  display: grid;
  grid-template-columns: repeat(4, minmax(150px, 1fr));
  gap: 10px;
}

.guide-step-grid,
.data-health-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.guide-step-card,
.data-health-card {
  padding: 18px;
}

.guide-step-card {
  min-height: 112px;
  border-left: 4px solid transparent;
}

.guide-step-card.status-ready {
  border-left-color: #2f8f5b;
}

.guide-step-card.status-warning {
  border-left-color: #c8882f;
}

.guide-step-card.status-blocked {
  border-left-color: #c45656;
}

.guide-readiness-card {
  padding: 18px;
}

.guide-readiness-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.guide-readiness-item {
  padding: 12px;
  border: 1px solid rgba(124, 142, 158, 0.16);
  border-radius: 8px;
  background: #f8fbfd;
}

.guide-readiness-item strong {
  color: #263b50;
}

.guide-readiness-item p {
  margin: 6px 0 0;
  color: #667b8e;
  line-height: 1.5;
}

.guide-readiness-item.level-blocking {
  border-color: rgba(196, 86, 86, 0.28);
  background: #fff6f6;
}

.guide-readiness-item.level-warning {
  border-color: rgba(200, 136, 47, 0.28);
  background: #fffaf1;
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
  .recommendation-section-nav,
  .command-fields,
  .workbench-priority-grid,
  .guide-step-grid,
  .guide-readiness-list,
  .data-health-grid,
  .health-columns,
  .recommend-layout,
  .recommend-side-stack {
    grid-template-columns: 1fr;
  }
}
</style>
