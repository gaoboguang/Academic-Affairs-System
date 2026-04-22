import type { Ref } from "vue";
import type {
  RecommendationHistoryItem,
  RecommendationResult,
} from "./types";
import { useRecommendationMultiComparison } from "./useRecommendationMultiComparison";
import { useRecommendationSchemeExport } from "./useRecommendationSchemeExport";
import { useRecommendationSingleComparison } from "./useRecommendationSingleComparison";

interface ComparisonOptions {
  historyItems: Ref<RecommendationHistoryItem[]>;
  selectedSchemeMeta: Ref<RecommendationHistoryItem | null>;
  selectedSchemeResults: Ref<RecommendationResult[]>;
}

export function useRecommendationSchemeComparison(options: ComparisonOptions) {
  const single = useRecommendationSingleComparison(options);
  const multi = useRecommendationMultiComparison({
    compareHistoryOptions: single.compareHistoryOptions,
    selectedSchemeMeta: options.selectedSchemeMeta,
  });
  const exporting = useRecommendationSchemeExport({
    getLoadedSchemeResults: (schemeId) =>
      options.selectedSchemeMeta.value?.scheme_id === schemeId ? options.selectedSchemeResults.value : null,
    getHistoryItems: (studentId) =>
      options.historyItems.value.filter((item) => item.student_id === studentId),
  });

  function resetComparisonState(): void {
    single.resetSingleComparison();
    multi.resetMultiComparison();
  }

  return {
    ...single,
    ...multi,
    ...exporting,
    resetComparisonState,
  };
}
