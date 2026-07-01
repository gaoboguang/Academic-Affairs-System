import { computed, onMounted, ref, watch } from "vue";

import { gaokaoCandidateTypeOptions, provinceOptions } from "./helpers";
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
  const recommendationPageLoading = ref(false);
  const recommendationPageLoadError = ref("");
  const loadingTabs = ref<Set<string>>(new Set());
  const tabLoadError = ref<{ tab: string; message: string } | null>(null);
  const guideCandidateTypeOptions = computed(() =>
    volunteerWorkspace.volunteerGuideOptions.value?.candidate_types.length
      ? volunteerWorkspace.volunteerGuideOptions.value.candidate_types
      : gaokaoCandidateTypeOptions,
  );
  const activeRecommendationTabLoading = computed(() => loadingTabs.value.has(workflow.activeTab.value));
  const activeRecommendationTabLoadError = computed(() =>
    tabLoadError.value?.tab === workflow.activeTab.value ? tabLoadError.value.message : "",
  );

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

  function setTabLoading(tab: string, loading: boolean): void {
    const next = new Set(loadingTabs.value);
    if (loading) {
      next.add(tab);
    } else {
      next.delete(tab);
    }
    loadingTabs.value = next;
  }

  async function retryRecommendationPageLoad(): Promise<void> {
    await loadInitialPageData();
  }

  async function loadInitialPageData(): Promise<void> {
    try {
      recommendationPageLoading.value = true;
      recommendationPageLoadError.value = "";
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
      recommendationPageLoadError.value = formatUserActionError(
        "加载高考志愿页面",
        error,
        "确认本地服务已启动后点击重新加载；若某个页签数据为空，可进入对应页签单独刷新。",
      );
    } finally {
      recommendationPageLoading.value = false;
    }
  }

  onMounted(() => {
    void loadInitialPageData();
  });

  async function loadTabData(tab: string, options: { force?: boolean } = {}): Promise<void> {
    if (options.force) {
      loadedTabs.delete(tab);
    }
    if (loadedTabs.has(tab)) return;
    try {
      setTabLoading(tab, true);
      if (tabLoadError.value?.tab === tab) {
        tabLoadError.value = null;
      }
      if (tab === "colleges") {
        await catalog.loadColleges({ resetPage: true });
        loadedTabs.add(tab);
        return;
      }
      if (tab === "recommendations") {
        await catalog.loadCollegeDirectory();
        loadedTabs.add(tab);
        return;
      }
      if (tab === "majors") {
        await catalog.loadMajors({ resetPage: true });
        loadedTabs.add(tab);
        return;
      }
      if (tab === "employment-directions") {
        await career.loadEmploymentDirections();
        loadedTabs.add(tab);
        return;
      }
      if (tab === "major-employment-maps") {
        await Promise.all([
          catalog.loadMajorDirectory(),
          career.loadEmploymentDirections(),
          career.loadMajorEmploymentMappings({ resetPage: true }),
        ]);
        loadedTabs.add(tab);
        return;
      }
      if (tab === "enrollment-plans") {
        await Promise.all([
          catalog.loadCollegeDirectory(),
          planning.loadEnrollmentPlans({ resetPage: true }),
        ]);
        loadedTabs.add(tab);
        return;
      }
      if (tab === "admissions") {
        await Promise.all([
          catalog.loadCollegeDirectory(),
          catalog.loadAdmissions({ resetPage: true }),
        ]);
        loadedTabs.add(tab);
        return;
      }
      if (tab === "volunteer-rules") {
        await planning.loadProvinceVolunteerRules();
        loadedTabs.add(tab);
        return;
      }
      if (tab === "special-type-rules") {
        await planning.loadSpecialTypeRules();
        loadedTabs.add(tab);
        return;
      }
      if (tab === "score-transform-rules") {
        await planning.loadProvinceScoreTransformRules();
        loadedTabs.add(tab);
        return;
      }
      if (tab === "subject-requirements") {
        await planning.loadSubjectRequirementDicts();
        loadedTabs.add(tab);
        return;
      }
      if (tab === "shandong-workbench") {
        await shandongWorkbench.loadShandongDataHealth();
        loadedTabs.add(tab);
        return;
      }
      if (tab === "history") {
        await workflow.loadHistory();
        loadedTabs.add(tab);
        return;
      }
      if (tab === "data-health") {
        await shandongWorkbench.loadShandongDataHealth();
        loadedTabs.add(tab);
        return;
      }
      if (tab === "volunteer-workbench") {
        await career.loadEmploymentDirections();
        loadedTabs.add(tab);
      }
    } catch (error) {
      tabLoadError.value = {
        tab,
        message: formatUserActionError("加载高考志愿页签", error, "请稍后重试，或先缩小筛选条件后再查询。"),
      };
    } finally {
      setTabLoading(tab, false);
    }
  }

  async function reloadActiveRecommendationTab(): Promise<void> {
    await loadTabData(workflow.activeTab.value, { force: true });
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
    activeRecommendationTabLoadError,
    activeRecommendationTabLoading,
    gaokaoCandidateTypeOptions: guideCandidateTypeOptions,
    provinceOptions,
    recommendationPageLoadError,
    recommendationPageLoading,
    reloadActiveRecommendationTab,
    retryRecommendationPageLoad,
    summaryCards,
  };
}
