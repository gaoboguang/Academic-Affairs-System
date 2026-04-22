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

const APP_MODEL_TABLE_KEYS = new Set(["enrollment_plan", "admission_record"]);

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
