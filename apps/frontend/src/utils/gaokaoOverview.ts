export interface GaokaoOverviewTableStat {
  key: string;
  label: string;
  record_total: number;
  covered_total?: number | null;
  coverage_rate?: number | null;
  latest_updated_at?: string | null;
  latest_batch_label?: string | null;
  status: string;
  notes: string[];
}

export interface GaokaoOverviewGapCard extends GaokaoOverviewTableStat {
  summary: string;
}

export interface GaokaoOverviewHelpText {
  overallHelp: string;
  recruitSiteHelp: string;
  chapterUrlHelp: string;
  fallbackUrlHelp: string;
}

const APP_MODEL_TABLE_KEYS = new Set(["enrollment_plan", "admission_record"]);

const DEFAULT_OVERVIEW_HELP: GaokaoOverviewHelpText = {
  overallHelp: "这里的覆盖率只统计高校主档和章程证据链里的链接字段，不代表录取数据或招生计划完整度。",
  recruitSiteHelp: "高校主档中已维护招生网链接的学校数；用于追溯官网，不代表招生计划覆盖率。",
  chapterUrlHelp: "章程证据链中已有正式章程链接的学校数；影响章程复核，不代表录取结果缺失。",
  fallbackUrlHelp: "没有正式章程入口时可用于人工只读核对的备用链接数。",
};

export function buildGaokaoOverviewGapCards(
  tables: GaokaoOverviewTableStat[],
): GaokaoOverviewGapCard[] {
  return tables
    .filter((item) => APP_MODEL_TABLE_KEYS.has(item.key) && item.record_total === 0)
    .map((item) => ({
      ...item,
      summary: buildGaokaoOverviewGapSummary(item),
    }));
}

function buildGaokaoOverviewGapSummary(item: GaokaoOverviewTableStat): string {
  if (item.status === "partial") {
    return "独立只读库已有原始数据，但应用模型还没接上当前链路。";
  }
  if (item.status === "waiting") {
    return "应用模型为空，且本地只读库还没暴露对应原始表。";
  }
  if (item.status === "empty") {
    return "应用模型与当前只读原始表都还没有数据。";
  }
  return `${item.label} 当前还没有应用侧数据。`;
}

export function buildGaokaoOverviewHelpText(tables: GaokaoOverviewTableStat[]): GaokaoOverviewHelpText {
  const enrollment = tables.find((item) => item.key === "enrollment_plan");
  const admission = tables.find((item) => item.key === "admission_record");
  const hasAppData = Boolean((enrollment?.record_total ?? 0) > 0 || (admission?.record_total ?? 0) > 0);
  if (!hasAppData) {
    return DEFAULT_OVERVIEW_HELP;
  }
  return {
    ...DEFAULT_OVERVIEW_HELP,
    overallHelp: `应用侧数据已入库：招生计划 ${enrollment?.record_total ?? 0} 条，录取结果 ${admission?.record_total ?? 0} 条；上方覆盖率只表示官网 / 章程链接证据链还需继续补齐。`,
  };
}
