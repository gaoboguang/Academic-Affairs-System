import { useRecommendationHistoryCollection } from "./useRecommendationHistoryCollection";
import { useRecommendationSchemeComparison } from "./useRecommendationSchemeComparison";

export function useRecommendationHistoryManager() {
  const collection = useRecommendationHistoryCollection();
  const comparison = useRecommendationSchemeComparison({
    historyItems: collection.historyItems,
    selectedSchemeMeta: collection.selectedSchemeMeta,
    selectedSchemeResults: collection.selectedSchemeResults,
  });

  async function viewScheme(item: Parameters<typeof collection.viewScheme>[0]): Promise<void> {
    comparison.resetComparisonState();
    await collection.viewScheme(item);
  }

  return {
    ...collection,
    ...comparison,
    viewScheme,
  };
}
