import { useRecommendationStrategyManager } from "./useRecommendationStrategyManager";
import { useRecommendationSubmissionManager } from "./useRecommendationSubmissionManager";
import type { useReferenceStore } from "../../stores/reference";

type ReferenceStore = ReturnType<typeof useReferenceStore>;

interface GenerationManagerOptions {
  referenceStore: ReferenceStore;
}

export function useRecommendationGenerationManager(options: GenerationManagerOptions) {
  const submission = useRecommendationSubmissionManager(options);
  const strategy = useRecommendationStrategyManager();

  return {
    ...submission,
    ...strategy,
  };
}
