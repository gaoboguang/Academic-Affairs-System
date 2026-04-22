import { ref } from "vue";
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

interface MultiComparisonOptions {
  compareHistoryOptions: Ref<RecommendationHistoryItem[]>;
  selectedSchemeMeta: Ref<RecommendationHistoryItem | null>;
}

export function useRecommendationMultiComparison(options: MultiComparisonOptions) {
  const { compareHistoryOptions, selectedSchemeMeta } = options;

  const multiCompareSchemeResults = ref<Record<number, RecommendationResult[]>>({});
  const multiCompareSchemeIds = ref<number[]>([]);
  const multiComparingSchemes = ref(false);
  const multiCompareError = ref<string | null>(null);

  function resetMultiComparison(): void {
    multiCompareError.value = null;
    multiCompareSchemeIds.value = [];
    multiCompareSchemeResults.value = {};
  }

  async function handleMultiCompareChange(value: number[] | string[] | undefined | null): Promise<void> {
    const targetIds = (value ?? []).map((item) => Number(item));
    if (!targetIds.length || !selectedSchemeMeta.value) {
      multiCompareError.value = null;
      multiCompareSchemeResults.value = {};
      return;
    }
    const nextResults = Object.fromEntries(
      Object.entries(multiCompareSchemeResults.value).filter(([schemeId]) =>
        targetIds.includes(Number(schemeId))),
    ) as Record<number, RecommendationResult[]>;
    const missingIds = targetIds.filter((item) => !nextResults[item]);
    if (!missingIds.length) {
      multiCompareError.value = null;
      multiCompareSchemeResults.value = nextResults;
      return;
    }
    try {
      multiComparingSchemes.value = true;
      multiCompareError.value = null;
      const loaded = await Promise.allSettled(
        missingIds.map(async (schemeId) => {
          const meta = compareHistoryOptions.value.find((item) => item.scheme_id === schemeId);
          if (!meta) return null;
          const results = await apiRequest<RecommendationResult[]>(
            `/api/recommendations/history/${schemeId}/results?student_id=${meta.student_id}`,
          );
          return { schemeId, results };
        }),
      );
      const failedSchemeNames: string[] = [];
      for (let index = 0; index < loaded.length; index += 1) {
        const result = loaded[index];
        const schemeId = missingIds[index];
        const meta = compareHistoryOptions.value.find((item) => item.scheme_id === schemeId);
        if (result.status === "fulfilled") {
          if (result.value) {
            nextResults[result.value.schemeId] = result.value.results;
          }
          continue;
        }
        failedSchemeNames.push(meta?.scheme_name ?? `方案 ${schemeId}`);
        reportError(result.reason);
      }
      multiCompareSchemeResults.value = nextResults;
      if (failedSchemeNames.length) {
        multiCompareError.value = `以下方案读取失败：${failedSchemeNames.join("、")}`;
      }
    } finally {
      multiComparingSchemes.value = false;
    }
  }

  return {
    handleMultiCompareChange,
    multiCompareError,
    multiComparingSchemes,
    multiCompareSchemeIds,
    multiCompareSchemeResults,
    resetMultiComparison,
  };
}
