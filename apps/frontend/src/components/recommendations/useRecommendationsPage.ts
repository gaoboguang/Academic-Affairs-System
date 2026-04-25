import { computed, onMounted, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { provinceOptions } from "./helpers";
import { useRecommendationCatalogManager } from "./useRecommendationCatalogManager";
import { useRecommendationCareerManager } from "./useRecommendationCareerManager";
import { useGaokaoPlanningManager } from "./useGaokaoPlanningManager";
import { useGaokaoVolunteerWorkspace } from "./useGaokaoVolunteerWorkspace";
import { useRecommendationWorkflow } from "./useRecommendationWorkflow";
import { useReferenceStore } from "../../stores/reference";
import { formatUserActionError } from "../../utils/userFeedback";

export function useRecommendationsPage() {
  const referenceStore = useReferenceStore();
  const catalog = useRecommendationCatalogManager();
  const career = useRecommendationCareerManager({
    majorDirectory: catalog.majorDirectory,
  });
  const planning = useGaokaoPlanningManager({
    collegeDirectory: catalog.collegeDirectory,
    reloadCollegeDirectory: catalog.loadCollegeDirectory,
    reloadMajorDirectory: catalog.loadMajorDirectory,
  });
  const workflow = useRecommendationWorkflow({
    referenceStore,
    collegeDirectory: catalog.collegeDirectory,
    majorDirectory: catalog.majorDirectory,
    admissions: catalog.admissions,
  });
  const volunteerWorkspace = useGaokaoVolunteerWorkspace({
    recommendationForm: workflow.recommendationForm,
    planYearOptions: planning.planYearOptions,
    batchOptions: planning.batchOptions,
    examModeOptions: planning.examModeOptions,
    employmentDirections: career.employmentDirections,
  });

  const summaryCards = computed(() => {
    const workflowCards = workflow.summaryCards.value;
    const planningCards = planning.summaryCards.value;
    return [
      workflowCards[0],
      workflowCards[1],
      planningCards[0],
      workflowCards[2],
      planningCards[1],
      planningCards[2],
      planningCards[3],
      workflowCards[3],
    ].filter(Boolean);
  });

  onMounted(async () => {
    try {
      await workflow.loadStudentAndExamOptions();
      await Promise.all([
        catalog.loadCollegeDirectory(),
        catalog.loadMajorDirectory(),
        career.loadEmploymentDirections(),
        career.loadMajorEmploymentMappings(),
        workflow.loadRecommendationSettings(),
        catalog.loadColleges(),
        catalog.loadMajors(),
        catalog.loadAdmissions(),
        planning.loadEnrollmentPlans(),
        planning.loadProvinceVolunteerRules(),
        workflow.loadHistory(),
      ]);
      volunteerWorkspace.syncFromRecommendationForm();
      if (workflow.historyItems.value.length) {
        await workflow.viewScheme(workflow.historyItems.value[0]);
      }
    } catch (error) {
      ElMessage.error(formatUserActionError("加载高考志愿页面", error, "确认本地服务已启动后刷新页面；若某个页签数据为空，可进入对应页签单独刷新。"));
    }
  });

  watch(
    () => workflow.activeTab.value,
    (tab) => {
      if (tab === "special-type-rules" && !planning.specialTypeRules.value.length) {
        void planning.loadSpecialTypeRules();
      }
      if (tab === "score-transform-rules" && !planning.provinceScoreTransformRules.value.length) {
        void planning.loadProvinceScoreTransformRules();
      }
      if (tab === "subject-requirements" && !planning.subjectRequirementDicts.value.length) {
        void planning.loadSubjectRequirementDicts();
      }
    },
  );

  return {
    ...catalog,
    ...career,
    ...planning,
    ...volunteerWorkspace,
    ...workflow,
    provinceOptions,
    summaryCards,
  };
}
