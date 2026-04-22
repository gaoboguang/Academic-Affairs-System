import { ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";

import { apiRequest, openFile } from "../../api/client";
import { resolveRecommendationReportInsightContext } from "../reports/reportInsightRecommendation";
import { recommendationPrintPreviewPath } from "../../utils/print";
import { buildRecommendationSchemeOutputWarningMessage } from "./recommendationOutputGuards";
import type {
  ExportRecord,
  RecommendationHistoryItem,
  RecommendationResult,
} from "./types";

function reportError(error: unknown): void {
  ElMessage.error((error as Error).message);
}

function reportExportError(error: unknown): void {
  const message = (error as Error).message;
  ElMessage.error(`推荐报告导出失败：${message}`);
}

interface RecommendationSchemeExportOptions {
  getLoadedSchemeResults?: (schemeId: number) => RecommendationResult[] | null | undefined;
  getHistoryItems?: (studentId: number) => RecommendationHistoryItem[] | null | undefined;
}

export function useRecommendationSchemeExport(options: RecommendationSchemeExportOptions = {}) {
  const exportingScheme = ref<number | null>(null);

  async function confirmSchemeOutput(item: RecommendationHistoryItem, actionLabel: string): Promise<boolean> {
    const results = await loadSchemeResultsForOutput(item);
    const historyItems = await loadHistoryItemsForOutput(item.student_id);
    const compareScheme = resolveRecommendationReportInsightContext(historyItems, item).compareScheme;
    const compareResults = compareScheme ? await loadSchemeResultsForOutput(compareScheme) : [];
    const warningMessage = buildRecommendationSchemeOutputWarningMessage(item, results, {
      history: historyItems,
      compareResults,
    });
    if (!warningMessage) {
      return true;
    }
    try {
      await ElMessageBox.confirm(warningMessage, `${actionLabel}前复核`, {
        type: "warning",
        confirmButtonText: `仍要${actionLabel}`,
        cancelButtonText: "取消",
      });
      return true;
    } catch (error) {
      if (error === "cancel" || error === "close") {
        return false;
      }
      reportError(error);
      return false;
    }
  }

  async function loadSchemeResultsForOutput(item: RecommendationHistoryItem): Promise<RecommendationResult[]> {
    const loadedResults = options.getLoadedSchemeResults?.(item.scheme_id);
    if (loadedResults) {
      return loadedResults;
    }
    try {
      return await apiRequest<RecommendationResult[]>(
        `/api/recommendations/history/${item.scheme_id}/results?student_id=${item.student_id}`,
      );
    } catch (error) {
      reportError(error);
      return [];
    }
  }

  async function loadHistoryItemsForOutput(studentId: number): Promise<RecommendationHistoryItem[]> {
    const loadedHistoryItems = options.getHistoryItems?.(studentId);
    if (loadedHistoryItems?.length) {
      return loadedHistoryItems;
    }
    try {
      return await apiRequest<RecommendationHistoryItem[]>(`/api/recommendations/history?student_id=${studentId}`);
    } catch (error) {
      reportError(error);
      return [];
    }
  }

  async function openRecommendationPrintPreview(item: RecommendationHistoryItem): Promise<void> {
    const confirmed = await confirmSchemeOutput(item, "打印");
    if (!confirmed) {
      return;
    }
    openFile(recommendationPrintPreviewPath(item.student_id, item.scheme_id));
  }

  async function exportScheme(item: RecommendationHistoryItem): Promise<void> {
    const confirmed = await confirmSchemeOutput(item, "导出");
    if (!confirmed) {
      return;
    }
    try {
      exportingScheme.value = item.scheme_id;
      const result = await apiRequest<ExportRecord>("/api/reports/export", {
        method: "POST",
        body: JSON.stringify({
          report_type: "recommendation_summary",
          scheme_id: item.scheme_id,
          student_id: item.student_id,
        }),
      });
      openFile(result.download_url);
      ElMessage.success("推荐报告已生成");
    } catch (error) {
      reportExportError(error);
    } finally {
      exportingScheme.value = null;
    }
  }

  return {
    exportScheme,
    exportingScheme,
    openRecommendationPrintPreview,
  };
}
