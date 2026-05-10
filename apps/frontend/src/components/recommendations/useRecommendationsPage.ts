import { computed, onMounted, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { provinceOptions } from "./helpers";
import { useRecommendationCatalogManager } from "./useRecommendationCatalogManager";
import { useRecommendationCareerManager } from "./useRecommendationCareerManager";
import { useGaokaoPlanningManager } from "./useGaokaoPlanningManager";
import { useGaokaoVolunteerWorkspace } from "./useGaokaoVolunteerWorkspace";
import { useRecommendationWorkflow } from "./useRecommendationWorkflow";
import { useShandongRecommendationWorkbench } from "./useShandongRecommendationWorkbench";
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
    examOptions: workflow.examOptions,
    employmentDirections: career.employmentDirections,
  });
  const shandongWorkbench = useShandongRecommendationWorkbench({
    recommendationForm: workflow.recommendationForm,
  });
  const loadedTabs = new Set<string>();

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
      await Promise.all([
        workflow.loadStudentAndExamOptions(),
        workflow.loadRecommendationSettings(),
        workflow.loadHistory(),
        career.loadEmploymentDirections(),
      ]);
      loadedTabs.add("volunteer-workbench");
      volunteerWorkspace.syncFromRecommendationForm();
      if (workflow.historyItems.value.length) {
        await workflow.viewScheme(workflow.historyItems.value[0]);
      }
      void shandongWorkbench.loadShandongDataHealth();
    } catch (error) {
      ElMessage.error(formatUserActionError("加载高考志愿页面", error, "确认本地服务已启动后刷新页面；若某个页签数据为空，可进入对应页签单独刷新。"));
    }
  });

  async function loadTabData(tab: string): Promise<void> {
    if (loadedTabs.has(tab)) return;
    loadedTabs.add(tab);
    try {
      if (tab === "colleges") {
        await catalog.loadColleges({ resetPage: true });
        return;
      }
      if (tab === "recommendations") {
        await catalog.loadCollegeDirectory();
        return;
      }
      if (tab === "majors") {
        await catalog.loadMajors({ resetPage: true });
        return;
      }
      if (tab === "employment-directions") {
        await career.loadEmploymentDirections();
        return;
      }
      if (tab === "major-employment-maps") {
        await Promise.all([
          catalog.loadMajorDirectory(),
          career.loadEmploymentDirections(),
          career.loadMajorEmploymentMappings({ resetPage: true }),
        ]);
        return;
      }
      if (tab === "enrollment-plans") {
        await Promise.all([
          catalog.loadCollegeDirectory(),
          planning.loadEnrollmentPlans({ resetPage: true }),
        ]);
        return;
      }
      if (tab === "admissions") {
        await Promise.all([
          catalog.loadCollegeDirectory(),
          catalog.loadAdmissions({ resetPage: true }),
        ]);
        return;
      }
      if (tab === "volunteer-rules") {
        await planning.loadProvinceVolunteerRules();
        return;
      }
      if (tab === "special-type-rules") {
        await planning.loadSpecialTypeRules();
        return;
      }
      if (tab === "score-transform-rules") {
        await planning.loadProvinceScoreTransformRules();
        return;
      }
      if (tab === "subject-requirements") {
        await planning.loadSubjectRequirementDicts();
        return;
      }
      if (tab === "shandong-workbench") {
        await shandongWorkbench.loadShandongDataHealth();
        return;
      }
      if (tab === "history") {
        await workflow.loadHistory();
        return;
      }
      if (tab === "data-health") {
        await shandongWorkbench.loadShandongDataHealth();
        return;
      }
      if (tab === "volunteer-workbench") {
        await career.loadEmploymentDirections();
      }
    } catch (error) {
      loadedTabs.delete(tab);
      ElMessage.error(formatUserActionError("加载高考志愿页签", error, "请稍后重试，或先缩小筛选条件后再查询。"));
    }
  }

  watch(
    () => workflow.activeTab.value,
    (tab) => {
      void loadTabData(tab);
    },
  );

  return {
    ...catalog,
    ...career,
    ...planning,
    ...shandongWorkbench,
    ...volunteerWorkspace,
    ...workflow,
    provinceOptions,
    summaryCards,
  };
}
