import { computed, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";
import type { RecommendationSettings, StrategyPresetFormState } from "./types";
import { apiRequest } from "../../api/client";
import { formatUserActionError } from "../../utils/userFeedback";

function reportError(error: unknown): void {
  ElMessage.error(formatUserActionError("处理策略模板", error, "先确认模板名称和当前策略设置；如果仍失败，请刷新策略后重试。"));
}

interface PresetOptions {
  recommendationSettings: RecommendationSettings;
}

export function useRecommendationStrategyPresets(options: PresetOptions) {
  const { recommendationSettings } = options;

  const savingPreset = ref(false);
  const selectedStrategyPresetId = ref<string | undefined>(undefined);
  const deletingPresetId = ref<string | null>(null);

  const strategyPresetForm = reactive<StrategyPresetFormState>({
    name: "",
    note: "",
  });

  const selectedStrategyPreset = computed(
    () => recommendationSettings.strategy_presets.find((item) => item.id === selectedStrategyPresetId.value) ?? null,
  );

  function applyStrategyPreset(): void {
    if (!selectedStrategyPreset.value) return;
    Object.assign(recommendationSettings, {
      safe_ratio_max: selectedStrategyPreset.value.safe_ratio_max,
      steady_ratio_max: selectedStrategyPreset.value.steady_ratio_max,
      rush_ratio_max: selectedStrategyPreset.value.rush_ratio_max,
      whitelist_college_ids: [...selectedStrategyPreset.value.whitelist_college_ids],
      blacklist_college_ids: [...selectedStrategyPreset.value.blacklist_college_ids],
    });
    strategyPresetForm.name = selectedStrategyPreset.value.name;
    strategyPresetForm.note = selectedStrategyPreset.value.note ?? "";
    ElMessage.success(`已应用模板：${selectedStrategyPreset.value.name}`);
  }

  async function saveStrategyPreset(): Promise<void> {
    if (!strategyPresetForm.name.trim()) {
      ElMessage.warning("请先填写模板名称");
      return;
    }
    try {
      savingPreset.value = true;
      const payload = await apiRequest<RecommendationSettings>("/api/recommendations/strategy-presets", {
        method: "POST",
        body: JSON.stringify({
          name: strategyPresetForm.name.trim(),
          note: strategyPresetForm.note.trim() || undefined,
          safe_ratio_max: recommendationSettings.safe_ratio_max,
          steady_ratio_max: recommendationSettings.steady_ratio_max,
          rush_ratio_max: recommendationSettings.rush_ratio_max,
          whitelist_college_ids: recommendationSettings.whitelist_college_ids,
          blacklist_college_ids: recommendationSettings.blacklist_college_ids,
        }),
      });
      Object.assign(recommendationSettings, payload);
      selectedStrategyPresetId.value = payload.strategy_presets.at(-1)?.id;
      ElMessage.success("策略模板已保存");
    } catch (error) {
      reportError(error);
    } finally {
      savingPreset.value = false;
    }
  }

  async function deleteStrategyPreset(): Promise<void> {
    if (!selectedStrategyPreset.value) return;
    try {
      await ElMessageBox.confirm(
        `删除后将无法直接复用模板“${selectedStrategyPreset.value.name}”。是否继续？`,
        "删除策略模板",
        { type: "warning" },
      );
      deletingPresetId.value = selectedStrategyPreset.value.id;
      const payload = await apiRequest<RecommendationSettings>(
        `/api/recommendations/strategy-presets/${selectedStrategyPreset.value.id}`,
        { method: "DELETE" },
      );
      Object.assign(recommendationSettings, payload);
      selectedStrategyPresetId.value = undefined;
      ElMessage.success("策略模板已删除");
    } catch (error) {
      if (error === "cancel" || error === "close") return;
      reportError(error);
    } finally {
      deletingPresetId.value = null;
    }
  }

  return {
    applyStrategyPreset,
    deleteStrategyPreset,
    deletingPresetId,
    saveStrategyPreset,
    savingPreset,
    selectedStrategyPreset,
    selectedStrategyPresetId,
    strategyPresetForm,
  };
}
