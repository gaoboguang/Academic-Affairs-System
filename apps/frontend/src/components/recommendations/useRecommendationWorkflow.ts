import { computed, ref } from "vue";

import type { AdmissionRecord, CollegeItem, MajorItem } from "./types";
import type { useReferenceStore } from "../../stores/reference";
import { useRecommendationGenerationManager } from "./useRecommendationGenerationManager";
import { useRecommendationHistoryManager } from "./useRecommendationHistoryManager";

type ReferenceStore = ReturnType<typeof useReferenceStore>;

interface WorkflowOptions {
  referenceStore: ReferenceStore;
  collegeDirectory: { value: CollegeItem[] };
  majorDirectory: { value: MajorItem[] };
  admissions: { value: AdmissionRecord[] };
}

export function useRecommendationWorkflow(options: WorkflowOptions) {
  const activeTab = ref("volunteer-workbench");
  const generation = useRecommendationGenerationManager({
    referenceStore: options.referenceStore,
  });
  const history = useRecommendationHistoryManager();

  const summaryCards = computed(() => [
    {
      label: "院校库",
      value: options.collegeDirectory.value.length,
      help: `${options.collegeDirectory.value.filter((item) => item.supports_art).length} 所支持艺体招生`,
      tone: "tone-blue",
    },
    {
      label: "专业库",
      value: options.majorDirectory.value.length,
      help: `${options.majorDirectory.value.filter((item) => item.is_art_related).length} 个艺体相关专业`,
      tone: "tone-amber",
    },
    {
      label: "录取库",
      value: options.admissions.value.length,
      help: `${new Set(options.admissions.value.map((item) => item.year)).size} 个年度样本`,
      tone: "tone-slate",
    },
    {
      label: "历史方案",
      value: history.historyItems.value.length,
      help: "保留推荐生成时间、方案名称与结果分组",
      tone: "tone-green",
    },
  ]);

  const recommendationGuideCards = computed(() => [
    {
      label: "当前模式",
      value: generation.isBatchMode.value ? "批量学生" : "单个学生",
      help: generation.isBatchMode.value ? "适合统一条件批量出方案。" : "适合精细调整单个学生参数。",
      tone: "tone-blue",
    },
    {
      label: "当前学生",
      value: generation.selectedStudentLabel.value,
      help: generation.isBatchMode.value ? "批量模式会按统一参数生成多份方案。" : "单个学生模式支持补录位次或分数。",
      tone: generation.selectedStudentLabel.value === "未选择" ? "tone-slate" : "tone-green",
    },
    {
      label: "参考考试",
      value: generation.selectedExamLabel.value,
      help: generation.selectedExamLabel.value === "未选择" ? "生成前请先选择参考考试。" : "推荐会优先引用该考试的位次和成绩。",
      tone: generation.selectedExamLabel.value === "未选择" ? "tone-slate" : "tone-blue",
    },
    {
      label: "历史方案",
      value: history.historyItems.value.length ? `${history.historyItems.value.length} 份` : "暂无",
      help: history.historyItems.value.length ? "可回看历史方案并做差异对比。" : "生成首份方案后会自动出现在历史记录中。",
      tone: history.historyItems.value.length ? "tone-amber" : "tone-slate",
    },
  ]);

  const latestGenerationMessage = computed(() => {
    if (generation.latestGeneration.value) {
      return `已生成方案 ${generation.latestGeneration.value.scheme_name}，共 ${generation.latestGeneration.value.result_count} 条推荐结果。`;
    }
    if (generation.batchGeneration.value) {
      const provinceCount = new Set(generation.batchGeneration.value.items.map((item) => item.province).filter(Boolean)).size;
      const provinceSummary = provinceCount > 1 ? `，覆盖 ${provinceCount} 个生源地` : "";
      return `${generation.batchGeneration.value.message}，共生成 ${generation.batchGeneration.value.scheme_ids.length} 个方案，累计 ${generation.batchGeneration.value.result_count} 条结果${provinceSummary}。`;
    }
    return "";
  });

  async function submitRecommendation(): Promise<void> {
    await generation.submitRecommendationAction({
      setActiveTab: (tab) => {
        activeTab.value = tab;
      },
      loadHistory: history.loadHistory,
      findHistoryItem: (schemeId) => history.historyItems.value.find((item) => item.scheme_id === schemeId),
      viewScheme: history.viewScheme,
    });
  }

  return {
    activeTab,
    latestGenerationMessage,
    recommendationGuideCards,
    summaryCards,
    ...generation,
    ...history,
    submitRecommendation,
  };
}
