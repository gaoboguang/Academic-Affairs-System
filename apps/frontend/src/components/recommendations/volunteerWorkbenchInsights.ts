import { normalizeOptionalString } from "./scoreInput";
import type {
  ProvinceVolunteerRule,
  VolunteerBoundaryInsightCard,
  VolunteerRuleInsightCard,
  VolunteerWorkbenchCandidate,
  VolunteerWorkbenchPreviewResponse,
  VolunteerWorkbenchRuleAlert,
} from "./types";

const subjectRequirementModeLabels: Record<string, string> = {
  unified_subject_requirement: "统一选科要求",
  first_choice_reselect: "首选 + 再选",
  major_level_requirement: "专业级选科要求",
};

const parallelRuleModeLabels: Record<string, string> = {
  college_major_parallel: "院校 + 专业平行",
  group_parallel: "院校专业组平行",
  major_parallel: "专业平行",
  ordered_sequential: "顺序志愿",
};

const candidateTypeLabels: Record<string, string> = {
  general: "普通类",
  art: "艺体类",
  sports: "体育类",
  fine_art: "美术类",
  music: "音乐类",
  dance: "舞蹈类",
  media: "传媒类",
  spring_exam: "春季高考",
  independent_recruitment: "单独招生",
  comprehensive_evaluation: "综合评价招生",
};

export function buildVolunteerRuleInsightCards(
  preview: VolunteerWorkbenchPreviewResponse | null,
  selectedRule: ProvinceVolunteerRule | null,
): VolunteerRuleInsightCard[] {
  return buildVolunteerRuleInsightCardsFromRules(preview?.applicable_rules ?? [], selectedRule);
}

export function buildVolunteerRuleInsightCardsFromRules(
  rules: ProvinceVolunteerRule[],
  selectedRule: ProvinceVolunteerRule | null,
): VolunteerRuleInsightCard[] {
  if (!rules.length) {
    return [];
  }

  const hasMultipleRules = rules.length > 1;
  return rules.map((rule) => {
    const isSelected = Boolean(selectedRule && rule.id === selectedRule.id);
    const facts = [
      { label: "总分口径", value: `${rule.total_score} 分` },
      { label: "志愿上限", value: `${rule.volunteer_limit} 个` },
      { label: "志愿单位", value: rule.volunteer_unit_type },
      { label: "平行方式", value: formatParallelRuleMode(rule) },
      { label: "选科口径", value: formatSubjectRequirementMode(rule) },
      { label: "每单位专业数", value: rule.max_major_per_unit ? `${rule.max_major_per_unit} 个` : "未设" },
      { label: "征集志愿", value: rule.support_collect_round ? "支持" : "未设" },
      { label: "调剂", value: rule.allow_adjustment ? "允许" : "不允许" },
    ];

    const notes: string[] = [];
    const subjectSegments: string[] = [];
    if (rule.required_subjects_json.length) {
      subjectSegments.push(`必选 ${rule.required_subjects_json.join(" / ")}`);
    }
    if (rule.first_choice_subjects_json.length) {
      subjectSegments.push(`首选 ${rule.first_choice_subjects_json.join(" / ")}`);
    }
    if (rule.reselect_subjects_json.length) {
      subjectSegments.push(`再选 ${rule.reselect_subjects_json.join(" / ")}`);
    }
    if (subjectSegments.length) {
      notes.push(`选科细则：${subjectSegments.join("；")}`);
    }
    if (rule.score_rule_summary) {
      notes.push(`赋分摘要：${rule.score_rule_summary}`);
    }
    if (rule.special_rules_json.length) {
      notes.push(`附加要求：${rule.special_rules_json.join("；")}`);
    }
    if (rule.note) {
      notes.push(`备注：${rule.note}`);
    }

    let subtitle = "当前智能筛选与草稿都按这条规则解释。";
    if (hasMultipleRules) {
      subtitle = isSelected
        ? "当前草稿按这条规则控制上限，其余规则保留作兼容预览。"
        : "这是一条兼容命中的规则，可用于解释模式回退和智能筛选差异。";
    }

    return {
      key: String(rule.id),
      title: `${rule.province} ${rule.year} ${rule.exam_mode} · ${rule.batch}`,
      subtitle,
      facts,
      notes,
      isSelected,
    };
  });
}

export function buildVolunteerBoundaryInsightCards(
  preview: VolunteerWorkbenchPreviewResponse | null,
): VolunteerBoundaryInsightCard[] {
  if (!preview) {
    return [];
  }

  const candidates = preview.candidates ?? [];
  const alertMap = new Map(preview.rule_alerts.map((item) => [item.code, item]));
  const cards: VolunteerBoundaryInsightCard[] = [];

  const baselineCount = candidates.filter((item) => item.matched_rule_is_baseline).length;
  if (baselineCount || alertMap.has("baseline_rule_matched")) {
    cards.push({
      key: "baseline",
      title: "系统基线命中",
      summary: baselineCount ? `${baselineCount} 条候选仍按系统基线解释` : "当前结果仍带系统基线提醒",
      detail:
        alertMap.get("baseline_rule_matched")?.detail
        ?? "当前省份/年份还缺少更细规则，志愿上限、单位结构和征集志愿仍需按当年公告复核。",
      tone: "info",
    });
  }

  const compatibleCount = candidates.filter((item) => item.match_tags_json.includes("兼容模式命中")).length;
  if (compatibleCount || alertMap.has("compatible_exam_mode_fallback")) {
    cards.push({
      key: "compatible_mode",
      title: "兼容模式预览",
      summary: compatibleCount ? `${compatibleCount} 条候选走兼容模式命中` : "当前规则存在兼容模式回退",
      detail:
        alertMap.get("compatible_exam_mode_fallback")?.detail
        ?? "当前未命中该省的精确模式规则，系统先按兼容模式预览，填报前仍需核对当年政策。",
      tone: "warning",
    });
  }

  const specificRuleSummary = getVolunteerSpecificRuleSummary(candidates);
  if (specificRuleSummary) {
    cards.push({
      key: "candidate_specific_rule",
      title: "类别专用规则口径",
      summary: `${specificRuleSummary.count} 条候选当前按${specificRuleSummary.labelText}专用规则解释`,
      detail: `当前命中的省份规则已细分到${specificRuleSummary.labelText}；同省同年其他类别可能适用不同的志愿上限、单位结构和选科口径。`,
      tone: "info",
    });
  }

  const missingRuleCount = candidates.filter((item) => !hasMatchedVolunteerRule(item)).length;
  const generalRuleCount = candidates.filter(
    (item) =>
      hasMatchedVolunteerRule(item)
      && !item.matched_rule_is_baseline
      && !normalizeOptionalString(item.matched_rule_candidate_type ?? ""),
  ).length;

  const generalReferenceFallbackCount = candidates.filter((item) =>
    item.risk_flags_json.includes("general_reference_fallback"),
  ).length;
  if (generalReferenceFallbackCount) {
    const fallbackAlert = alertMap.get("fallback_general_reference_data");
    cards.push({
      key: "general_reference_fallback",
      title: fallbackAlert?.title ?? "普通类录取参考回退",
      summary: `${generalReferenceFallbackCount} 条候选当前按普通类录取结果参考`,
      detail:
        fallbackAlert?.detail
        ?? "这类结果说明当前缺少该类别专门录取结果，只能先借普通类录取结果做方向性筛选；正式填报前仍需结合该类别公告、批次规则和学校章程再复核。",
      tone: fallbackAlert?.level === "warning" ? "warning" : "info",
    });
  }

  const collegeFallbackCount = candidates.filter((item) => item.reference_scope === "college" && item.major_id).length;
  if (collegeFallbackCount) {
    cards.push({
      key: "college_fallback",
      title: "院校线回退",
      summary: `${collegeFallbackCount} 条候选缺少专业线，只能先按院校线参考`,
      detail: "这类计划更适合做方向性参考，同校不同专业的真实录取差异仍需人工复核。",
      tone: "warning",
    });
  }

  const scoreLineReferenceCount = candidates.filter((item) => item.reference_scope === "score_line").length;
  if (scoreLineReferenceCount) {
    cards.push({
      key: "score_line_reference",
      title: "省控线初筛",
      summary: `${scoreLineReferenceCount} 条候选当前仅按省控线做资格参考`,
      detail: "这类结果说明当前缺少该类别专门录取结果，只能先按山东控制线筛掉明显不满足线的计划；正式填报前仍需逐校核对录取与章程口径。",
      tone: "warning",
    });
  }

  const planOnlyReferenceCount = candidates.filter((item) => item.reference_scope === "plan_only").length;
  if (planOnlyReferenceCount) {
    cards.push({
      key: "plan_only_reference",
      title: "计划清单初筛",
      summary: `${planOnlyReferenceCount} 条候选当前仅按当年招生计划做方向性初筛`,
      detail: "这类结果说明当前缺少该类别专门录取结果，也没有可直接复用的官方控制线；正式填报前必须结合该类别公告、章程和后续结果再复核。",
      tone: "warning",
    });
  }

  const subjectCheckCount = candidates.filter(
    (item) => item.match_tags_json.includes("待核对选科") || item.risk_flags_json.includes("subject_requirement_check"),
  ).length;
  if (subjectCheckCount) {
    cards.push({
      key: "subject_check",
      title: "选科仍需核对",
      summary: `${subjectCheckCount} 条候选仍需逐条核对选科限制`,
      detail: "当前筛选只做了工作台层面的匹配提示，最终仍要回到招生章程确认专业或专业组要求。",
      tone: "warning",
    });
  }

  const referenceYearMixSummary = getVolunteerReferenceYearMixSummary(candidates);
  if (referenceYearMixSummary) {
    cards.push({
      key: "mixed_reference_years",
      title: "跨年份参考样本",
      summary: `${referenceYearMixSummary.count} 条候选最近录取样本分布在 ${referenceYearMixSummary.yearText}`,
      detail:
        referenceYearMixSummary.scopeText.length === 1
          ? `当前候选都按 ${referenceYearMixSummary.scopeText[0]} 口径，但最近录取样本并非同一年；同省跨年份比较时，录取位次、最低分和冲稳保分组变化属于正常现象。`
          : `当前候选涉及 ${referenceYearMixSummary.scopeText.join(" / ")} 等多个口径，最近录取样本也并非同一年；跨省或跨年份比较时，录取位次、最低分和冲稳保分组变化属于正常现象。`,
      tone: "info",
    });
  }

  const staleReferenceCount = candidates.filter((item) => hasStaleVolunteerReferenceYears(item.year, item.reference_years_json)).length;
  if (staleReferenceCount) {
    cards.push({
      key: "stale_reference_years",
      title: "参考年份偏旧",
      summary: `${staleReferenceCount} 条候选最近录取样本与目标年份相差 2 年及以上`,
      detail: "这类结果更适合作为方向性参考；若近一年录取数据尚未补齐，分层、排序和口径说明都可能继续变化。",
      tone: "warning",
    });
  }

  const provinceScopeSummary = getVolunteerProvinceScopeSummary(candidates);
  if (provinceScopeSummary) {
    cards.push({
      key: "cross_province",
      title: "跨省口径差异",
      summary: `${provinceScopeSummary.count} 个省份口径混合`,
      detail: `当前候选涉及 ${provinceScopeSummary.scopeText.join(" / ")} 等多个口径，跨省比较时，录取位次、最低分和冲稳保分组变化属于正常现象。`,
      tone: "info",
    });
  }

  const alertSummaryMap: Record<string, string> = {
    missing_rule_province: "当前省份规则尚未入库",
    missing_rule_year: "当前结果缺少更细规则支撑",
    missing_rule_batch: "当前结果缺少更细规则支撑",
    missing_rule_candidate_type: "当前结果缺少更细规则支撑",
    missing_rule_exam_mode: "当前结果缺少更细规则支撑",
  };
  const missingRuleSummaryMap: Record<string, string> = {
    missing_rule_province: "当前省份规则尚未入库",
    missing_rule_year: "当前缺少目标年份规则支撑",
    missing_rule_batch: "当前缺少目标批次规则支撑",
    missing_rule_candidate_type: "当前缺少类别专用规则支撑",
    missing_rule_exam_mode: "当前缺少目标模式规则支撑",
  };
  for (const code of [
    "missing_rule_province",
    "missing_rule_year",
    "missing_rule_batch",
    "missing_rule_candidate_type",
    "missing_rule_exam_mode",
  ] as const) {
    const alert = alertMap.get(code);
    if (!alert) continue;
    cards.push({
      key: code,
      title: alert.title,
      summary: missingRuleCount ? `${missingRuleCount} 条候选${missingRuleSummaryMap[code]}` : alertSummaryMap[code] ?? "当前结果缺少更细规则支撑",
      detail: alert.detail,
      tone: alert.level === "warning" ? "warning" : "info",
    });
  }

  const fallbackAlert = alertMap.get("fallback_general_candidate_rule");
  if (fallbackAlert) {
    cards.push({
      key: "fallback_general_candidate_rule",
      title: fallbackAlert?.title ?? "已回退到通用考生规则",
      summary: generalRuleCount ? `${generalRuleCount} 条候选当前按通用考生规则解释` : "当前先按通用类别规则预览",
      detail: fallbackAlert?.detail ?? "这通常表示该省该年尚未配置更细的类别专用规则；若后续补齐普通类、艺术类等专用规则，候选解释和排序可能变化。",
      tone: fallbackAlert?.level === "warning" ? "warning" : "info",
    });
  }

  if (!cards.length && candidates.length) {
    cards.push({
      key: "stable",
      title: "当前结果边界较清晰",
      summary: `${candidates.length} 条候选主要按精确规则和现有专业线解释`,
      detail: "目前未发现明显的基线回退、兼容模式回退或大面积专业线缺失，可直接继续做草稿筛选与排序。",
      tone: "success",
    });
  }

  return cards;
}

export function buildVolunteerDraftBoundaryInsightCards(
  draftItems: Array<{ candidate: VolunteerWorkbenchCandidate }>,
  selectedRule: ProvinceVolunteerRule | null | undefined,
  ruleAlerts: VolunteerWorkbenchRuleAlert[] = [],
): VolunteerBoundaryInsightCard[] {
  const candidates = draftItems.map((item) => item.candidate);
  if (!candidates.length) {
    return [];
  }

  const cards: VolunteerBoundaryInsightCard[] = [];
  const alertMap = new Map(ruleAlerts.map((item) => [item.code, item]));
  const baselineCount = candidates.filter((item) => item.matched_rule_is_baseline).length;
  const selectedRuleIsBaseline = Boolean(selectedRule?.note?.includes("系统基线初始化生成"));
  if (baselineCount || selectedRuleIsBaseline) {
    cards.push({
      key: "baseline",
      title: "草稿内仍含系统基线口径",
      summary: baselineCount ? `${baselineCount} 条已选志愿仍按系统基线解释` : "当前草稿规则快照仍带系统基线属性",
      detail: "打印或定稿前，建议继续核对当年省份公告中的志愿上限、单位结构和征集志愿要求。",
      tone: "info",
    });
  }

  const compatibleCount = candidates.filter((item) => item.match_tags_json.includes("兼容模式命中")).length;
  if (compatibleCount) {
    cards.push({
      key: "compatible_mode",
      title: "草稿内含兼容模式结果",
      summary: `${compatibleCount} 条已选志愿按兼容模式预览命中`,
      detail: "这类结果适合做方向性参考，正式填报前仍需核对该省该年的精确模式规则。",
      tone: "warning",
    });
  }

  const specificRuleSummary = getVolunteerSpecificRuleSummary(candidates);
  if (specificRuleSummary) {
    cards.push({
      key: "candidate_specific_rule",
      title: "草稿内含类别专用规则口径",
      summary: `${specificRuleSummary.count} 条已选志愿当前按${specificRuleSummary.labelText}专用规则解释`,
      detail: `当前命中的省份规则已细分到${specificRuleSummary.labelText}；同省同年其他类别可能适用不同的志愿上限、单位结构和选科口径。`,
      tone: "info",
    });
  }

  const missingRuleCount = candidates.filter((item) => !hasMatchedVolunteerRule(item)).length;
  if (missingRuleCount) {
    const missingRuleSummaryMap: Record<string, string> = {
      missing_rule_province: "当前省份规则尚未入库",
      missing_rule_year: "当前缺少目标年份规则支撑",
      missing_rule_batch: "当前缺少目标批次规则支撑",
      missing_rule_candidate_type: "当前缺少类别专用规则支撑",
      missing_rule_exam_mode: "当前缺少目标模式规则支撑",
    };
    let hasSpecificMissingRuleAlert = false;
    for (const code of [
      "missing_rule_province",
      "missing_rule_year",
      "missing_rule_batch",
      "missing_rule_candidate_type",
      "missing_rule_exam_mode",
    ] as const) {
      const alert = alertMap.get(code);
      if (!alert) continue;
      hasSpecificMissingRuleAlert = true;
      cards.push({
        key: code,
        title: alert.title,
        summary: `${missingRuleCount} 条已选志愿${missingRuleSummaryMap[code]}`,
        detail: alert.detail,
        tone: alert.level === "warning" ? "warning" : "info",
      });
    }
    if (!hasSpecificMissingRuleAlert) {
      cards.push({
        key: "missing_rule",
        title: "草稿内缺少明确规则",
        summary: `${missingRuleCount} 条已选志愿当前缺少明确省份规则支撑`,
        detail: "这些志愿在保存时未命中明确的省份规则，可能缺少省份、年份、批次或模式规则；打印或导出前建议回到工作台核对规则差异摘要。",
        tone: "warning",
      });
    }
  }

  const generalRuleCount = candidates.filter(
    (item) =>
      hasMatchedVolunteerRule(item)
      && !item.matched_rule_is_baseline
      && !normalizeOptionalString(item.matched_rule_candidate_type ?? ""),
  ).length;
  if (generalRuleCount) {
    const fallbackAlert = alertMap.get("fallback_general_candidate_rule");
    cards.push({
      key: "general_candidate_rule",
      title: fallbackAlert?.title ?? "草稿内含通用类别规则口径",
      summary: `${generalRuleCount} 条已选志愿当前按通用考生规则解释`,
      detail: fallbackAlert?.detail ?? "这通常表示该省该年尚未配置更细的类别专用规则；若后续补齐普通类、艺术类等专用规则，候选解释和排序可能变化。",
      tone: fallbackAlert?.level === "warning" ? "warning" : "info",
    });
  }

  const generalReferenceFallbackCount = candidates.filter((item) =>
    item.risk_flags_json.includes("general_reference_fallback"),
  ).length;
  if (generalReferenceFallbackCount) {
    const fallbackAlert = alertMap.get("fallback_general_reference_data");
    cards.push({
      key: "general_reference_fallback",
      title: fallbackAlert?.title ?? "草稿内含普通类录取参考回退",
      summary: `${generalReferenceFallbackCount} 条已选志愿当前按普通类录取结果参考`,
      detail:
        fallbackAlert?.detail
        ?? "这类志愿说明当前缺少该类别专门录取结果，只能先借普通类录取结果做方向性筛选；正式填报前仍需结合该类别公告、批次规则和学校章程再复核。",
      tone: fallbackAlert?.level === "warning" ? "warning" : "info",
    });
  }

  const collegeFallbackCount = candidates.filter((item) => item.reference_scope === "college" && item.major_id).length;
  if (collegeFallbackCount) {
    cards.push({
      key: "college_fallback",
      title: "草稿内含院校线回退",
      summary: `${collegeFallbackCount} 条已选志愿缺少专业线，只能先按院校线参考`,
      detail: "同校不同专业的真实录取难度仍可能继续分化，最终定稿前应结合专业线或章程再核对一次。",
      tone: "warning",
    });
  }

  const scoreLineReferenceCount = candidates.filter((item) => item.reference_scope === "score_line").length;
  if (scoreLineReferenceCount) {
    cards.push({
      key: "score_line_reference",
      title: "草稿内含省控线初筛",
      summary: `${scoreLineReferenceCount} 条已选志愿当前仅按省控线做资格参考`,
      detail: "这类志愿说明当前缺少该类别专门录取结果，只能先按山东控制线筛掉明显不满足线的计划；正式填报前仍需逐校核对录取与章程口径。",
      tone: "warning",
    });
  }

  const planOnlyReferenceCount = candidates.filter((item) => item.reference_scope === "plan_only").length;
  if (planOnlyReferenceCount) {
    cards.push({
      key: "plan_only_reference",
      title: "草稿内含计划清单初筛",
      summary: `${planOnlyReferenceCount} 条已选志愿当前仅按当年招生计划做方向性初筛`,
      detail: "这类志愿说明当前缺少该类别专门录取结果，也没有可直接复用的官方控制线；正式填报前必须结合该类别公告、章程和后续结果再复核。",
      tone: "warning",
    });
  }

  const subjectCheckCount = candidates.filter(
    (item) => item.match_tags_json.includes("待核对选科") || item.risk_flags_json.includes("subject_requirement_check"),
  ).length;
  if (subjectCheckCount) {
    cards.push({
      key: "subject_check",
      title: "草稿内仍有选科待核对项",
      summary: `${subjectCheckCount} 条已选志愿仍需逐条核对选科限制`,
      detail: "打印稿可用于讨论和汇报，但最终填报前仍应回到招生章程确认专业或专业组要求。",
      tone: "warning",
    });
  }

  const referenceYearMixSummary = getVolunteerReferenceYearMixSummary(candidates);
  if (referenceYearMixSummary) {
    cards.push({
      key: "mixed_reference_years",
      title: "草稿内含跨年份参考样本",
      summary: `${referenceYearMixSummary.count} 条已选志愿最近录取样本分布在 ${referenceYearMixSummary.yearText}`,
      detail:
        referenceYearMixSummary.scopeText.length === 1
          ? `这些志愿当前都按 ${referenceYearMixSummary.scopeText[0]} 口径，但最近录取样本并非同一年；同省跨年份比较时，录取位次、最低分和冲稳保分组变化属于正常现象。`
          : `这些志愿当前涉及 ${referenceYearMixSummary.scopeText.join(" / ")} 等多个口径，最近录取样本也并非同一年；跨省或跨年份比较时，录取位次、最低分和冲稳保分组变化属于正常现象。`,
      tone: "info",
    });
  }

  const staleReferenceCount = candidates.filter((item) => hasStaleVolunteerReferenceYears(item.year, item.reference_years_json)).length;
  if (staleReferenceCount) {
    cards.push({
      key: "stale_reference_years",
      title: "草稿内含偏旧年份样本",
      summary: `${staleReferenceCount} 条已选志愿最近录取样本与目标年份相差 2 年及以上`,
      detail: "这类志愿当前更适合作为方向性参考；若后续补齐近一年录取数据，排序、边界说明和最终取舍都可能变化。",
      tone: "warning",
    });
  }

  const provinceScopeSummary = getVolunteerProvinceScopeSummary(candidates);
  if (provinceScopeSummary) {
    cards.push({
      key: "cross_province",
      title: "草稿内含跨省口径",
      summary: `${provinceScopeSummary.count} 个省份口径混合`,
      detail: `当前草稿涉及 ${provinceScopeSummary.scopeText.join(" / ")} 等多个口径，跨省比较时，录取位次、最低分和冲稳保分组变化属于正常现象。`,
      tone: "info",
    });
  }

  if (!cards.length) {
    cards.push({
      key: "stable",
      title: "当前草稿边界较清晰",
      summary: `${draftItems.length} 条已选志愿主要按精确规则和现有专业线解释`,
      detail: "当前草稿未发现明显的系统基线回退、兼容模式回退或大面积专业线缺失，可继续做排序和汇报材料整理。",
      tone: "success",
    });
  }

  return cards;
}

function hasMatchedVolunteerRule(candidate: VolunteerWorkbenchCandidate): boolean {
  return Boolean(
    candidate.matched_rule_is_baseline
    || normalizeOptionalString(candidate.matched_rule_exam_mode ?? "")
    || normalizeOptionalString(candidate.matched_rule_batch ?? "")
    || normalizeOptionalString(candidate.matched_rule_candidate_type ?? ""),
  );
}

function getVolunteerProvinceScopeSummary(
  candidates: VolunteerWorkbenchCandidate[],
): { count: number; scopeText: string[] } | null {
  const provinces = Array.from(
    new Set(
      candidates
        .map((item) => normalizeOptionalString(item.province))
        .filter((value): value is string => Boolean(value)),
    ),
  ).sort();
  if (provinces.length <= 1) {
    return null;
  }
  return {
    count: provinces.length,
    scopeText: provinces,
  };
}

function getVolunteerSpecificRuleSummary(
  candidates: VolunteerWorkbenchCandidate[],
): { count: number; labelText: string } | null {
  const labels = Array.from(
    new Set(
      candidates
        .filter((item) => hasMatchedVolunteerRule(item) && !item.matched_rule_is_baseline)
        .map((item) => formatVolunteerCandidateType(item.matched_rule_candidate_type))
        .filter(Boolean),
    ),
  );
  if (!labels.length) {
    return null;
  }
  const count = candidates.filter(
    (item) =>
      hasMatchedVolunteerRule(item)
      && !item.matched_rule_is_baseline
      && Boolean(formatVolunteerCandidateType(item.matched_rule_candidate_type)),
  ).length;
  return {
    count,
    labelText: labels.join(" / "),
  };
}

function getVolunteerReferenceYearMixSummary(
  candidates: VolunteerWorkbenchCandidate[],
): { count: number; yearText: string; scopeText: string[] } | null {
  const latestReferenceYears = candidates
    .map((item) => getLatestVolunteerReferenceYear(item.reference_years_json))
    .filter((value): value is number => value !== null);
  const uniqueYears = Array.from(new Set(latestReferenceYears)).sort((left, right) => right - left);
  if (uniqueYears.length <= 1) {
    return null;
  }
  const scopeText = Array.from(
    new Set(
      candidates
        .map((item) => normalizeOptionalString(item.province))
        .filter((value): value is string => Boolean(value)),
    ),
  );
  return {
    count: latestReferenceYears.length,
    yearText: `${uniqueYears.join(" / ")} 年`,
    scopeText: scopeText.length ? scopeText : ["当前省份"],
  };
}

function hasStaleVolunteerReferenceYears(targetYear: number, referenceYears: number[]): boolean {
  const gap = getVolunteerReferenceYearGap(targetYear, referenceYears);
  return gap !== null && gap >= 2;
}

function getLatestVolunteerReferenceYear(referenceYears: number[]): number | null {
  if (!referenceYears.length) {
    return null;
  }
  const latestYear = Math.max(...referenceYears);
  return Number.isFinite(latestYear) ? latestYear : null;
}

function getVolunteerReferenceYearGap(targetYear: number, referenceYears: number[]): number | null {
  const latestYear = getLatestVolunteerReferenceYear(referenceYears);
  if (latestYear === null) {
    return null;
  }
  return targetYear - latestYear;
}

function formatVolunteerCandidateType(value: string | null | undefined): string {
  const normalized = normalizeOptionalString(value ?? "");
  if (!normalized) {
    return "";
  }
  return candidateTypeLabels[normalized] ?? normalized;
}

function formatSubjectRequirementMode(rule: ProvinceVolunteerRule): string {
  return subjectRequirementModeLabels[rule.subject_requirement_mode ?? ""] ?? rule.subject_requirement_mode ?? "未设";
}

function formatParallelRuleMode(rule: ProvinceVolunteerRule): string {
  if (!rule.is_parallel) {
    return "顺序志愿";
  }
  return parallelRuleModeLabels[rule.parallel_rule_mode ?? ""] ?? rule.parallel_rule_mode ?? "平行志愿";
}
