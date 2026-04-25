import { computed, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest } from "../../api/client";
import { formatUserActionError } from "../../utils/userFeedback";
import {
  buildRecommendationSettingsSnapshot,
  hasRecommendationSettingsPendingChanges,
} from "./recommendationStrategy";
import type { RecommendationSettings } from "./types";

function reportError(error: unknown): void {
  ElMessage.error(formatUserActionError("保存推荐策略", error, "先确认阈值、黑名单和白名单设置正确；如果仍失败，请刷新策略后重试。"));
}

const defaultRecommendationSettings: RecommendationSettings = {
  safe_ratio_max: 0.85,
  steady_ratio_max: 1.0,
  rush_ratio_max: 1.15,
  whitelist_college_ids: [],
  blacklist_college_ids: [],
  whitelist_colleges: [],
  blacklist_colleges: [],
  strategy_presets: [],
};

export function useRecommendationStrategySettings() {
  const savingSettings = ref(false);
  const settingsSnapshot = ref(buildRecommendationSettingsSnapshot(defaultRecommendationSettings));

  const recommendationSettings = reactive<RecommendationSettings>({ ...defaultRecommendationSettings });

  const hasUnsavedRecommendationSettings = computed(() =>
    hasRecommendationSettingsPendingChanges(recommendationSettings, settingsSnapshot.value),
  );

  async function loadRecommendationSettings(previousPresetId?: string): Promise<string | undefined> {
    try {
      const payload = await apiRequest<RecommendationSettings>("/api/recommendations/settings");
      Object.assign(recommendationSettings, payload);
      settingsSnapshot.value = buildRecommendationSettingsSnapshot(payload);
      return payload.strategy_presets.some((item) => item.id === previousPresetId)
        ? previousPresetId
        : undefined;
    } catch (error) {
      reportError(error);
      return previousPresetId;
    }
  }

  async function saveRecommendationSettings(): Promise<void> {
    const safeRatioMax = Number(recommendationSettings.safe_ratio_max);
    const steadyRatioMax = Number(recommendationSettings.steady_ratio_max);
    const rushRatioMax = Number(recommendationSettings.rush_ratio_max);
    if (!(safeRatioMax > 0 && safeRatioMax <= steadyRatioMax && steadyRatioMax <= rushRatioMax)) {
      ElMessage.warning("推荐阈值需要满足 保底 <= 稳妥 <= 冲刺");
      return;
    }
    const whitelistCollegeIds = Array.from(new Set(recommendationSettings.whitelist_college_ids));
    const blacklistCollegeIds = Array.from(new Set(recommendationSettings.blacklist_college_ids));
    if (whitelistCollegeIds.some((item) => blacklistCollegeIds.includes(item))) {
      ElMessage.warning("同一院校不能同时存在于白名单和黑名单");
      return;
    }
    try {
      savingSettings.value = true;
      const payload = await apiRequest<RecommendationSettings>("/api/recommendations/settings", {
        method: "PUT",
        body: JSON.stringify({
          safe_ratio_max: safeRatioMax,
          steady_ratio_max: steadyRatioMax,
          rush_ratio_max: rushRatioMax,
          whitelist_college_ids: whitelistCollegeIds,
          blacklist_college_ids: blacklistCollegeIds,
        }),
      });
      Object.assign(recommendationSettings, payload);
      settingsSnapshot.value = buildRecommendationSettingsSnapshot(payload);
      ElMessage.success("推荐策略已保存");
    } catch (error) {
      reportError(error);
    } finally {
      savingSettings.value = false;
    }
  }

  return {
    hasUnsavedRecommendationSettings,
    loadRecommendationSettings,
    recommendationSettings,
    saveRecommendationSettings,
    savingSettings,
  };
}
