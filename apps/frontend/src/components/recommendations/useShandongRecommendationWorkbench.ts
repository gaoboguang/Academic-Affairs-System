import { computed, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest, openFile } from "../../api/client";
import { shandongRecommendationPrintPreviewPath } from "../../utils/print";
import { formatUserActionError } from "../../utils/userFeedback";
import {
  SHANDONG_RECOMMENDATION_PRINT_STORAGE_PREFIX,
  buildShandongRecommendationExportPayload,
  buildShandongRecommendationPrintPayload,
  buildShandongCoverageRows,
  buildShandongProjectionPayload,
  buildShandongRecommendationPayload,
  buildShandongResultGroups,
  createShandongRecommendationForm,
  shandongSubjectOptions,
  validateShandongRecommendationForm,
} from "./shandongRecommendationWorkbench";
import type {
  ExportRecord,
  RecommendationFormState,
  ShandongRecommendationDataHealth,
  ShandongRushStableSafeRecommendationResponse,
  StudentGaokaoScoreProjectionRead,
} from "./types";

interface ShandongRecommendationWorkbenchOptions {
  recommendationForm: RecommendationFormState;
}

export function useShandongRecommendationWorkbench(options: ShandongRecommendationWorkbenchOptions) {
  const shandongRecommendationForm = reactive(createShandongRecommendationForm());
  const shandongRecommendationResult = ref<ShandongRushStableSafeRecommendationResponse | null>(null);
  const shandongRecommendationProjection = ref<StudentGaokaoScoreProjectionRead | null>(null);
  const shandongDataHealth = ref<ShandongRecommendationDataHealth | null>(null);
  const generatingShandongRecommendation = ref(false);
  const exportingShandongReport = ref(false);
  const savingShandongProjection = ref(false);
  const loadingShandongDataHealth = ref(false);

  const shandongResultGroups = computed(() => buildShandongResultGroups(shandongRecommendationResult.value));
  const shandongCoverageRows = computed(() => buildShandongCoverageRows(shandongDataHealth.value));

  async function loadShandongDataHealth(): Promise<void> {
    try {
      loadingShandongDataHealth.value = true;
      shandongDataHealth.value = await apiRequest<ShandongRecommendationDataHealth>("/api/gaokao/data-health");
    } catch (error) {
      ElMessage.error(formatUserActionError("加载山东数据质量看板", error, "先确认本地后端服务已启动，再刷新本页。"));
    } finally {
      loadingShandongDataHealth.value = false;
    }
  }

  async function generateShandongRecommendation(): Promise<void> {
    const validationError = validateShandongRecommendationForm(shandongRecommendationForm);
    if (validationError) {
      ElMessage.warning(validationError);
      return;
    }

    try {
      generatingShandongRecommendation.value = true;
      shandongRecommendationResult.value = null;
      let projectionId: number | undefined;
      if (shandongRecommendationForm.source_mode === "exam_projection") {
        savingShandongProjection.value = true;
        const projection = await apiRequest<StudentGaokaoScoreProjectionRead>(
          "/api/recommendations/gaokao-score-projections",
          {
            method: "POST",
            body: JSON.stringify(buildShandongProjectionPayload(shandongRecommendationForm)),
          },
        );
        shandongRecommendationProjection.value = projection;
        projectionId = projection.id ?? undefined;
        savingShandongProjection.value = false;
        if (!projectionId) {
          ElMessage.warning("已生成预估结果，但缺少可用于推荐的预估记录编号。");
          return;
        }
      } else {
        shandongRecommendationProjection.value = null;
      }

      shandongRecommendationResult.value = await apiRequest<ShandongRushStableSafeRecommendationResponse>(
        "/api/recommendations/shandong-rush-stable-safe/preview",
        {
          method: "POST",
          body: JSON.stringify(buildShandongRecommendationPayload(shandongRecommendationForm, projectionId)),
        },
      );
      ElMessage.success("山东普通类冲稳保推荐已生成");
    } catch (error) {
      ElMessage.error(formatUserActionError("生成山东普通类推荐", error, "核对学生是否为山东普通类、分数/位次是否填写、最近三年投档数据是否已导入。"));
    } finally {
      savingShandongProjection.value = false;
      generatingShandongRecommendation.value = false;
    }
  }

  function resetShandongRecommendation(): void {
    Object.assign(shandongRecommendationForm, createShandongRecommendationForm());
    shandongRecommendationResult.value = null;
    shandongRecommendationProjection.value = null;
  }

  function openShandongRecommendationPrintPreview(): void {
    if (!shandongRecommendationResult.value) {
      ElMessage.warning("请先生成山东普通类推荐结果，再打印报告。");
      return;
    }
    const storageKey = `${SHANDONG_RECOMMENDATION_PRINT_STORAGE_PREFIX}${Date.now()}`;
    window.localStorage.setItem(
      storageKey,
      JSON.stringify(
        buildShandongRecommendationPrintPayload(
          shandongRecommendationResult.value,
          shandongRecommendationProjection.value,
          shandongDataHealth.value,
        ),
      ),
    );
    openFile(shandongRecommendationPrintPreviewPath(storageKey));
  }

  async function exportShandongRecommendationReport(): Promise<void> {
    if (!shandongRecommendationResult.value) {
      ElMessage.warning("请先生成山东普通类推荐结果，再导出 Excel。");
      return;
    }
    try {
      exportingShandongReport.value = true;
      const result = await apiRequest<ExportRecord>("/api/reports/shandong-recommendation/export", {
        method: "POST",
        body: JSON.stringify(buildShandongRecommendationExportPayload(shandongRecommendationResult.value)),
      });
      openFile(result.download_url);
      ElMessage.success("山东普通类推荐报告已生成");
    } catch (error) {
      ElMessage.error(formatUserActionError("导出山东普通类推荐报告", error, "先确认本次推荐结果仍在页面中，再重新点击导出。"));
    } finally {
      exportingShandongReport.value = false;
    }
  }

  function syncShandongRecommendationFromRecommendation(): void {
    const source = options.recommendationForm;
    shandongRecommendationForm.student_id = source.student_id;
    shandongRecommendationForm.exam_id = source.exam_id;
    shandongRecommendationForm.target_year = source.target_year || 2026;
    shandongRecommendationForm.batch = "常规批";
    shandongRecommendationForm.manual_score = source.comprehensive_score ?? source.culture_score;
    shandongRecommendationForm.manual_rank = source.student_rank_override;
    shandongRecommendationForm.risk_preference = source.risk_preference;
    shandongRecommendationForm.target_regions_json = [...source.target_regions_json];
    shandongRecommendationForm.school_level_tags_json = [...source.school_level_tags_json];
    shandongRecommendationForm.major_keyword = source.major_keyword;
    shandongRecommendationForm.selected_subjects_json = parseSubjectCombination(source.subject_combination);
    if (source.exam_id) {
      shandongRecommendationForm.source_mode = "exam_projection";
    } else if (source.student_rank_override) {
      shandongRecommendationForm.source_mode = "manual_rank";
    } else if (source.comprehensive_score || source.culture_score) {
      shandongRecommendationForm.source_mode = "manual_score";
    }
    ElMessage.success("已沿用推荐中心里的学生、考试、选科和筛选条件");
  }

  function parseSubjectCombination(value: string): string[] {
    return shandongSubjectOptions.filter((subject) => value.includes(subject));
  }

  return {
    exportShandongRecommendationReport,
    exportingShandongReport,
    generateShandongRecommendation,
    generatingShandongRecommendation,
    loadShandongDataHealth,
    loadingShandongDataHealth,
    openShandongRecommendationPrintPreview,
    resetShandongRecommendation,
    savingShandongProjection,
    shandongCoverageRows,
    shandongDataHealth,
    shandongRecommendationForm,
    shandongRecommendationProjection,
    shandongRecommendationResult,
    shandongResultGroups,
    syncShandongRecommendationFromRecommendation,
  };
}
