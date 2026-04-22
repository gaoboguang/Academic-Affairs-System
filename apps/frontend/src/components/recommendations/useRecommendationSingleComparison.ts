import { computed, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import type { Ref } from "vue";

import { apiRequest } from "../../api/client";
import type {
  RecommendationHistoryItem,
  RecommendationResult,
} from "./types";

function reportError(error: unknown): void {
  ElMessage.error((error as Error).message);
}

interface SingleComparisonOptions {
  historyItems: Ref<RecommendationHistoryItem[]>;
  selectedSchemeMeta: Ref<RecommendationHistoryItem | null>;
}

export function useRecommendationSingleComparison(options: SingleComparisonOptions) {
  const { historyItems, selectedSchemeMeta } = options;

  const compareSchemeResults = ref<RecommendationResult[]>([]);
  const compareSchemeId = ref<number | undefined>(undefined);
  const comparingScheme = ref(false);
  const compareSchemeError = ref<string | null>(null);

  const compareHistoryOptions = computed(() =>
    selectedSchemeMeta.value
      ? historyItems.value.filter(
          (item) =>
            item.student_id === selectedSchemeMeta.value?.student_id &&
            item.scheme_id !== selectedSchemeMeta.value?.scheme_id,
        )
      : [],
  );

  function resetSingleComparison(): void {
    compareSchemeId.value = undefined;
    compareSchemeError.value = null;
    compareSchemeResults.value = [];
  }

  async function handleCompareSchemeChange(value: number | string | undefined | null): Promise<void> {
    if (!value || !selectedSchemeMeta.value) {
      compareSchemeId.value = undefined;
      compareSchemeError.value = null;
      compareSchemeResults.value = [];
      return;
    }
    const target = compareHistoryOptions.value.find((item) => item.scheme_id === Number(value));
    if (!target) {
      compareSchemeError.value = null;
      compareSchemeResults.value = [];
      return;
    }
    try {
      comparingScheme.value = true;
      compareSchemeError.value = null;
      compareSchemeResults.value = [];
      compareSchemeResults.value = await apiRequest<RecommendationResult[]>(
        `/api/recommendations/history/${target.scheme_id}/results?student_id=${target.student_id}`,
      );
    } catch (error) {
      compareSchemeResults.value = [];
      compareSchemeError.value = (error as Error).message;
      reportError(error);
    } finally {
      comparingScheme.value = false;
    }
  }

  return {
    compareHistoryOptions,
    compareSchemeId,
    compareSchemeError,
    compareSchemeResults,
    comparingScheme,
    handleCompareSchemeChange,
    resetSingleComparison,
  };
}
