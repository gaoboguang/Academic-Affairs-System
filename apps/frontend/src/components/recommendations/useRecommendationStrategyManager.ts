import { computed } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";

import { differsFromStrategyPreset } from "./recommendationStrategy";
import { useRecommendationStrategyPresets } from "./useRecommendationStrategyPresets";
import { useRecommendationStrategySettings } from "./useRecommendationStrategySettings";

function reportError(error: unknown): void {
  ElMessage.error((error as Error).message);
}

export function useRecommendationStrategyManager() {
  const settings = useRecommendationStrategySettings();
  const presets = useRecommendationStrategyPresets({
    recommendationSettings: settings.recommendationSettings,
  });

  const strategyCards = computed(() => [
    {
      label: "保底阈值",
      value: `<= ${settings.recommendationSettings.safe_ratio_max.toFixed(2)}`,
      help: "位次比进入这一段后优先归入保底池。",
      tone: "tone-green",
    },
    {
      label: "稳妥阈值",
      value: `<= ${settings.recommendationSettings.steady_ratio_max.toFixed(2)}`,
      help: "控制主干志愿的密度，不让稳妥区间过宽。",
      tone: "tone-amber",
    },
    {
      label: "冲刺阈值",
      value: `<= ${settings.recommendationSettings.rush_ratio_max.toFixed(2)}`,
      help: "超过这一阈值的候选会被排除，不直接展示。",
      tone: "tone-blue",
    },
    {
      label: "白 / 黑名单",
      value: `${settings.recommendationSettings.whitelist_college_ids.length} / ${settings.recommendationSettings.blacklist_college_ids.length}`,
      help: "白名单放宽限制，黑名单直接剔除。",
      tone: "tone-slate",
    },
  ]);

  async function loadRecommendationSettings(): Promise<void> {
    presets.selectedStrategyPresetId.value = await settings.loadRecommendationSettings(
      presets.selectedStrategyPresetId.value,
    );
  }

  async function reloadRecommendationSettings(): Promise<void> {
    if (settings.hasUnsavedRecommendationSettings.value) {
      try {
        await ElMessageBox.confirm(
          "会用当前已保存的推荐策略覆盖本地未保存的阈值、白名单和黑名单调整。是否继续？",
          "重载推荐策略",
          {
            type: "warning",
            confirmButtonText: "继续重载",
            cancelButtonText: "取消",
          },
        );
      } catch (error) {
        if (error === "cancel" || error === "close") return;
        reportError(error);
        return;
      }
    }
    await loadRecommendationSettings();
  }

  async function applyStrategyPresetWithConfirm(): Promise<void> {
    if (
      settings.hasUnsavedRecommendationSettings.value
      && differsFromStrategyPreset(settings.recommendationSettings, presets.selectedStrategyPreset.value)
    ) {
      try {
        await ElMessageBox.confirm(
          `会用模板“${presets.selectedStrategyPreset.value?.name ?? ""}”覆盖当前未保存的阈值和院校名单设置。是否继续？`,
          "应用策略模板",
          {
            type: "warning",
            confirmButtonText: "继续应用",
            cancelButtonText: "取消",
          },
        );
      } catch (error) {
        if (error === "cancel" || error === "close") return;
        reportError(error);
        return;
      }
    }
    presets.applyStrategyPreset();
  }

  return {
    applyStrategyPresetWithConfirm,
    ...presets,
    reloadRecommendationSettings,
    ...settings,
    loadRecommendationSettings,
    strategyCards,
  };
}
