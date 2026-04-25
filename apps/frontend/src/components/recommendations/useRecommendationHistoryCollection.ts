import { reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest } from "../../api/client";
import { formatUserActionError } from "../../utils/userFeedback";
import type {
  HistoryFiltersState,
  RecommendationHistoryItem,
  RecommendationResult,
} from "./types";

function reportError(error: unknown): void {
  ElMessage.error(formatUserActionError("读取推荐历史", error, "先确认已经生成过推荐方案；如果仍失败，请刷新推荐中心后重试。"));
}

export function useRecommendationHistoryCollection() {
  const historyItems = ref<RecommendationHistoryItem[]>([]);
  const selectedSchemeResults = ref<RecommendationResult[]>([]);
  const selectedSchemeMeta = ref<RecommendationHistoryItem | null>(null);
  const loadingHistory = ref(false);
  const loadingSelectedScheme = ref(false);
  const historyLoadError = ref<string | null>(null);
  const selectedSchemeError = ref<string | null>(null);

  const historyFilters = reactive<HistoryFiltersState>({
    student_id: undefined,
  });

  async function loadHistory(): Promise<void> {
    try {
      loadingHistory.value = true;
      historyLoadError.value = null;
      const query = new URLSearchParams();
      if (historyFilters.student_id) query.set("student_id", String(historyFilters.student_id));
      historyItems.value = await apiRequest<RecommendationHistoryItem[]>(
        `/api/recommendations/history?${query.toString()}`,
      );
    } catch (error) {
      historyItems.value = [];
      historyLoadError.value = (error as Error).message;
      reportError(error);
    } finally {
      loadingHistory.value = false;
    }
  }

  function resetHistoryFilters(): void {
    historyFilters.student_id = undefined;
    void loadHistory();
  }

  async function viewScheme(item: RecommendationHistoryItem): Promise<void> {
    try {
      selectedSchemeMeta.value = item;
      loadingSelectedScheme.value = true;
      selectedSchemeError.value = null;
      selectedSchemeResults.value = [];
      selectedSchemeResults.value = await apiRequest<RecommendationResult[]>(
        `/api/recommendations/history/${item.scheme_id}/results?student_id=${item.student_id}`,
      );
    } catch (error) {
      selectedSchemeResults.value = [];
      selectedSchemeError.value = (error as Error).message;
      reportError(error);
    } finally {
      loadingSelectedScheme.value = false;
    }
  }

  async function reloadSelectedScheme(): Promise<void> {
    if (!selectedSchemeMeta.value) {
      return;
    }
    await viewScheme(selectedSchemeMeta.value);
  }

  return {
    historyFilters,
    historyLoadError,
    historyItems,
    loadingHistory,
    loadingSelectedScheme,
    loadHistory,
    reloadSelectedScheme,
    resetHistoryFilters,
    selectedSchemeError,
    selectedSchemeMeta,
    selectedSchemeResults,
    viewScheme,
  };
}
