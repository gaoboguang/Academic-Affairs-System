export const GAOKAO_DATA_COVERAGE_PRINT_STORAGE_PREFIX = "local-edu-tool:gaokao-data-coverage:";

type CoverageTone = "success" | "warning" | "danger" | "info";

export interface DataHealthType {
  key: string;
  label?: string | null;
  count: number;
}

export interface DataHealthYearBreakdown {
  year: number;
  total: number;
  student_types: DataHealthType[];
  batches: DataHealthType[];
  status: string;
}

export interface DataHealthCoverage {
  key: string;
  label: string;
  status: string;
  total: number;
  years: number[];
  missing_years: number[];
  readiness: string;
  readiness_label?: string | null;
  risk_level: string;
  explanation?: string | null;
  notes: string[];
  student_types: DataHealthType[];
  batch_distribution: DataHealthType[];
  year_breakdown: DataHealthYearBreakdown[];
}

export interface DataHealthAuditItem {
  key: string;
  label: string;
  status: string;
  created: number;
  updated: number;
  duplicates: number;
  conflicts: number;
  pending_review: number;
  notes: string[];
}

export interface DataHealthDeliveryAssessment {
  status: string;
  label: string;
  summary: string;
  pass_items: string[];
  warning_items: string[];
  blocking_items: string[];
}

export interface DataHealthPublicationStatus {
  key: string;
  label: string;
  category: string;
  target_year: number;
  status: string;
  status_label: string;
  record_count: number;
  action_label: string;
  explanation: string;
  notes: string[];
  blocks_recommendation: boolean;
}

export interface DataCompletionHealthInput {
  db_path: string;
  exists: boolean;
  generated_at: string;
  schema_version?: string | null;
  province: string;
  expected_years: number[];
  delivery_assessment?: DataHealthDeliveryAssessment | null;
  coverage: DataHealthCoverage[];
  publication_status: DataHealthPublicationStatus[];
  audit_summary: DataHealthAuditItem[];
  gaps: string[];
  summary: string;
}

export interface DataCompletionCard {
  key: string;
  title: string;
  statusLabel: string;
  tone: CoverageTone;
  summary: string;
  detail: string;
}

export interface CoverageMatrixCell {
  year: number;
  label: string;
  tone: CoverageTone;
  detail: string;
}

export interface CoverageMatrixRow {
  key: string;
  label: string;
  total: number;
  readinessLabel: string;
  cells: CoverageMatrixCell[];
  notes: string[];
}

export interface DataCompletionPrintPayload {
  report_name: string;
  generated_at: string;
  db_path: string;
  schema_version?: string | null;
  summary: string;
  delivery_label: string;
  delivery_summary: string;
  result_cards: DataCompletionCard[];
  coverage_matrix: CoverageMatrixRow[];
  publication_status: DataHealthPublicationStatus[];
  audit_summary: DataHealthAuditItem[];
  gaps: string[];
}

const KEY_DATA_DOMAINS = new Set([
  "score_rank_segment",
  "gaokao_score_line",
  "enrollment_plan",
  "gaokao_policy_reference",
  "gaokao_college_chapter_rule",
]);

export function buildDataCompletionResultCards(dataHealth: DataCompletionHealthInput): DataCompletionCard[] {
  const rank = findCoverage(dataHealth, "score_rank_segment");
  const scoreLine = findCoverage(dataHealth, "gaokao_score_line");
  const plan = findCoverage(dataHealth, "enrollment_plan");
  const policy = findCoverage(dataHealth, "gaokao_policy_reference");
  const chapterAudit = findAudit(dataHealth, "gaokao_college_chapter_rule");

  return [
    {
      key: "history-covered",
      title: "历史成绩线已补齐",
      statusLabel: "已补齐",
      tone: hasYears(rank, [2020, 2021, 2022]) && hasYears(scoreLine, [2020, 2021, 2022]) ? "success" : "warning",
      summary: "2020-2022 一分一段和省控线已进入健康检查口径。",
      detail: `一分一段当前覆盖 ${formatYears(rank?.years)}，共 ${rank?.total ?? 0} 条；省控线当前覆盖 ${formatYears(scoreLine?.years)}，共 ${scoreLine?.total ?? 0} 条。`,
    },
    {
      key: "plan-coverage",
      title: "招生计划仍是部分补齐",
      statusLabel: "部分补齐",
      tone: "warning",
      summary: "当前招生计划可以支撑部分推荐和路径判断，但 2024 数量偏少仍要核验。",
      detail: `应用侧招生计划当前共 ${plan?.total ?? 0} 条，覆盖 ${formatYears(plan?.years)}；2023 完整计划和 2024 完整性仍需官方文件或人工核验。`,
    },
    {
      key: "policy-reference",
      title: "政策参考还需要补来源",
      statusLabel: (policy?.total ?? 0) >= 10 ? "已补齐" : "部分补齐",
      tone: (policy?.total ?? 0) >= 10 ? "success" : "warning",
      summary: "政策参考用于解释报名、填报和特殊路径边界，不能替代招生计划。",
      detail: `当前政策参考 ${policy?.total ?? 0} 条；已登记的 2026 政策可继续推进到本地文件 SHA256 和结构化政策记录。`,
    },
    {
      key: "chapter-review",
      title: "章程限制链仍需人工复核",
      statusLabel: chapterAudit?.pending_review ? "需人工复核" : "已复核",
      tone: chapterAudit?.pending_review ? "warning" : "success",
      summary: "章程限制不能批量自动确认，仍应按学校官网和招生章程逐项核对。",
      detail: `当前章程限制链待复核 ${chapterAudit?.pending_review ?? 0} 条；未核验前只能作为风险提醒，不作为最终填报结论。`,
    },
    {
      key: "official-release",
      title: "2026 普通类正式数据等待发布",
      statusLabel: "官方未发布",
      tone: "info",
      summary: "2026 普通类正式计划、一分一段、省控线和投档结果不能提前伪造。",
      detail: "正式发布前，系统只能使用历史数据、已公开政策和明确的待发布提示；推荐或报告必须保留数据风险说明。",
    },
  ];
}

export function buildCoverageMatrixRows(dataHealth: DataCompletionHealthInput): CoverageMatrixRow[] {
  const years = dataHealth.expected_years.length ? dataHealth.expected_years : [2020, 2021, 2022, 2023, 2024, 2025, 2026];
  return dataHealth.coverage
    .filter((item) => KEY_DATA_DOMAINS.has(item.key))
    .map((item) => ({
      key: item.key,
      label: item.label,
      total: item.total,
      readinessLabel: item.readiness_label || item.status,
      cells: years.map((year) => buildCoverageCell(dataHealth, item, year)),
      notes: item.notes,
    }));
}

export function buildDataCompletionPrintPayload(dataHealth: DataCompletionHealthInput): DataCompletionPrintPayload {
  return {
    report_name: buildDataCompletionReportName(dataHealth),
    generated_at: new Date().toISOString(),
    db_path: dataHealth.db_path,
    schema_version: dataHealth.schema_version,
    summary: dataHealth.summary,
    delivery_label: dataHealth.delivery_assessment?.label || "待检查",
    delivery_summary: dataHealth.delivery_assessment?.summary || "请先刷新高考数据健康检查。",
    result_cards: buildDataCompletionResultCards(dataHealth),
    coverage_matrix: buildCoverageMatrixRows(dataHealth),
    publication_status: dataHealth.publication_status,
    audit_summary: dataHealth.audit_summary,
    gaps: dataHealth.gaps,
  };
}

export function buildDataCompletionReportName(dataHealth: DataCompletionHealthInput): string {
  return `${dataHealth.province || "山东"}高考数据覆盖报告`;
}

function buildCoverageCell(
  dataHealth: DataCompletionHealthInput,
  item: DataHealthCoverage,
  year: number,
): CoverageMatrixCell {
  const breakdown = item.year_breakdown.find((entry) => entry.year === year);
  if (breakdown) {
    if (item.key === "enrollment_plan" && year === 2024 && breakdown.total < 1000) {
      return {
        year,
        label: "部分补齐",
        tone: "warning",
        detail: `${year} 年当前 ${breakdown.total} 条，数量偏少，需继续核验完整性。`,
      };
    }
    if (item.key === "gaokao_college_chapter_rule") {
      return {
        year,
        label: "需复核",
        tone: "warning",
        detail: `${year} 年已有 ${breakdown.total} 条章程限制链，仍需结合待复核状态人工确认。`,
      };
    }
    if (item.key === "gaokao_policy_reference" && item.total < 10) {
      return {
        year,
        label: "部分补齐",
        tone: "warning",
        detail: `${year} 年当前 ${breakdown.total} 条政策参考，交付前仍需补官方政策和填报规则。`,
      };
    }
    return {
      year,
      label: "已补齐",
      tone: "success",
      detail: `${year} 年已有 ${breakdown.total} 条记录。`,
    };
  }

  if (year >= 2026) {
    const publication = dataHealth.publication_status.find((entry) => publicationMatchesCoverage(item.key, entry.key));
    return {
      year,
      label: publication?.status_label || "官方未发布",
      tone: publicationTone(publication?.status),
      detail: publication?.action_label || "等待官方发布或人工核验后再导入。",
    };
  }

  if (item.key === "enrollment_plan") {
    return {
      year,
      label: "需人工下载",
      tone: "warning",
      detail: `${year} 年招生计划缺少可核验完整官方文件，不能用第三方整理表替代。`,
    };
  }
  if (item.key === "gaokao_policy_reference" || item.key === "gaokao_college_chapter_rule") {
    return {
      year,
      label: "需人工复核",
      tone: "warning",
      detail: `${year} 年需要继续补官方政策、章程或复核记录。`,
    };
  }
  return {
    year,
    label: "待补齐",
    tone: "danger",
    detail: `${year} 年暂无结构化记录。`,
  };
}

function publicationMatchesCoverage(coverageKey: string, publicationKey: string): boolean {
  if (coverageKey === "score_rank_segment") return publicationKey === "score_rank_segment";
  if (coverageKey === "gaokao_score_line") return publicationKey === "score_line";
  if (coverageKey === "enrollment_plan") return publicationKey === "general_admission_plan";
  if (coverageKey === "gaokao_policy_reference") return publicationKey === "single_comprehensive_policy";
  if (coverageKey === "gaokao_college_chapter_rule") return publicationKey === "college_chapters";
  return false;
}

function publicationTone(status?: string): CoverageTone {
  if (status === "imported") return "success";
  if (status === "published" || status === "manual_review_required") return "warning";
  if (status === "pending_official_release" || status === "not_applicable") return "info";
  return "info";
}

function findCoverage(dataHealth: DataCompletionHealthInput, key: string): DataHealthCoverage | undefined {
  return dataHealth.coverage.find((item) => item.key === key);
}

function findAudit(dataHealth: DataCompletionHealthInput, key: string): DataHealthAuditItem | undefined {
  return dataHealth.audit_summary.find((item) => item.key === key);
}

function hasYears(item: DataHealthCoverage | undefined, years: number[]): boolean {
  if (!item) return false;
  return years.every((year) => item.years.includes(year));
}

function formatYears(years?: number[]): string {
  return years?.length ? years.join("、") : "暂无";
}
