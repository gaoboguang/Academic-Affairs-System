import type {
  CollegePayload,
  EmploymentDirectionItem,
  EmploymentDirectionPayload,
  MajorEmploymentMappingPayload,
  MajorPayload,
  ProvinceVolunteerRulePayload,
} from "./types";

export const provinceOptions = [
  "北京",
  "天津",
  "河北",
  "山西",
  "内蒙古",
  "辽宁",
  "吉林",
  "黑龙江",
  "上海",
  "江苏",
  "浙江",
  "安徽",
  "福建",
  "江西",
  "山东",
  "河南",
  "湖北",
  "湖南",
  "广东",
  "广西",
  "海南",
  "重庆",
  "四川",
  "贵州",
  "云南",
  "西藏",
  "陕西",
  "甘肃",
  "青海",
  "宁夏",
  "新疆",
];

export const baseSchoolLevelOptions = ["985", "211", "双一流", "省重点", "市重点", "公办", "民办", "艺体类"];

export const gaokaoExamModeOptions = ["3+3", "3+1+2", "物理类", "历史类", "文科", "理科", "综合改革"];

export const volunteerUnitTypeOptions = ["院校", "院校专业组", "专业"];

export const gaokaoCandidateTypeOptions = [
  { value: "general", label: "普通类" },
  { value: "art", label: "艺术类" },
  { value: "sports", label: "体育类" },
  { value: "spring_exam", label: "春季高考" },
  { value: "independent_recruitment", label: "高职单招" },
  { value: "comprehensive_evaluation", label: "高职综评" },
];

export const gaokaoArtTrackOptions = [
  { value: "fine_art_design", label: "美术与设计类" },
  { value: "music", label: "音乐类" },
  { value: "dance", label: "舞蹈类" },
  { value: "performance_directing", label: "表（导）演类" },
  { value: "calligraphy", label: "书法类" },
  { value: "broadcast_hosting", label: "播音与主持类" },
  { value: "opera", label: "戏曲类" },
];

export const scoreInputModeOptions = [
  { value: "actual_rank", label: "正式位次（高考省位次）" },
  { value: "actual_score", label: "正式分数" },
  { value: "estimated_score", label: "校内分数估算" },
  { value: "estimated_score_and_rank", label: "预估分 + 预估位次（本次考试/模拟推荐）" },
  { value: "score_range", label: "分数区间" },
  { value: "rank_range", label: "位次区间" },
] as const;

export const riskPreferenceOptions = [
  { value: "conservative", label: "保守" },
  { value: "balanced", label: "平衡" },
  { value: "aggressive", label: "激进" },
] as const;

export const subjectRequirementModeOptions = [
  { value: "unified_subject_requirement", label: "统一选科要求" },
  { value: "first_choice_reselect", label: "首选 / 再选拆分" },
  { value: "legacy_track", label: "文理 / 科类兼容" },
] as const;

export const parallelRuleModeOptions = [
  { value: "college_parallel", label: "院校平行" },
  { value: "major_parallel", label: "专业平行" },
  { value: "group_parallel", label: "专业组平行" },
  { value: "ordered_sequential", label: "顺序志愿" },
] as const;

export const employmentDirectionCategoryOptions = [
  "技术研发类",
  "医药健康类",
  "教育教学类",
  "法政公共服务类",
  "财经管理类",
  "传媒设计类",
  "制造工程类",
  "农林生态类",
  "艺术体育类",
  "服务运营类",
  "数字化与新职业类",
];

export const employmentDirectionUncategorizedLabel = "未分类";

export const employmentMappingStrengthOptions = [
  { value: "core", label: "核心相关" },
  { value: "high", label: "强相关" },
  { value: "medium", label: "一般相关" },
  { value: "transferable", label: "可转化" },
];

export const careerPriorityFocusOptions = [
  { value: "stability", label: "稳定性优先" },
  { value: "salary", label: "薪酬优先" },
  { value: "interest", label: "兴趣优先" },
  { value: "long_term", label: "长远发展优先" },
] as const;

export const recommendationStudentTypeOptions = [
  { value: "general", label: "普通生" },
  { value: "repeat", label: "复读生" },
  { value: "art", label: "艺体生" },
  { value: "sports", label: "体育生" },
  { value: "spring_exam", label: "春季高考" },
  { value: "independent_recruitment", label: "单独招生" },
  { value: "comprehensive_evaluation", label: "综合评价招生" },
];

export function createCollegeForm(): CollegePayload {
  return {
    name: "",
    college_code: null,
    province: null,
    city: null,
    school_type: null,
    school_level_tags_json: [],
    intro: null,
    website: null,
    supports_art: false,
    note: null,
    alias_names: [],
    is_active: true,
  };
}

export function createMajorForm(): MajorPayload {
  return {
    name: "",
    major_code: null,
    category: null,
    direction: null,
    career_path: null,
    is_art_related: false,
    note: null,
    is_active: true,
  };
}

export function createEmploymentDirectionForm(): EmploymentDirectionPayload {
  return {
    name: "",
    category: null,
    alias_names_json: [],
    description: null,
    common_job_types_json: [],
    common_industries_json: [],
    prefers_postgraduate: false,
    requires_certificate: false,
    requires_long_cycle: false,
    supports_art: false,
    risk_note: null,
    source_note: null,
    is_active: true,
  };
}

export interface EmploymentDirectionCategorySection {
  key: string;
  label: string;
  count: number;
  directions: EmploymentDirectionItem[];
}

export function createMajorEmploymentMappingForm(): MajorEmploymentMappingPayload {
  return {
    major_id: 0,
    direction_id: 0,
    strength: "medium",
    recommendation_note: null,
    requires_postgraduate: false,
    requires_certificate: false,
    supported_student_types_json: [],
    supports_art: false,
    note: null,
    is_active: true,
  };
}

export function createProvinceVolunteerRuleForm(): ProvinceVolunteerRulePayload {
  return {
    province: "山东",
    year: new Date().getFullYear(),
    exam_mode: "3+3",
    batch: "",
    candidate_type: "",
    batch_order: undefined,
    total_score: 750,
    volunteer_limit: 96,
    volunteer_unit_type: "专业",
    subject_requirement_mode: "unified_subject_requirement",
    required_subjects_json: ["物理", "化学", "生物", "政治", "历史", "地理"],
    first_choice_subjects_json: [],
    reselect_subjects_json: [],
    score_rule_summary: null,
    parallel_rule_mode: "major_parallel",
    max_major_per_unit: undefined,
    is_parallel: true,
    allow_adjustment: true,
    support_collect_round: false,
    special_rules_json: [],
    note: null,
    is_active: true,
  };
}

export function uniqueStrings(items: Array<string | null | undefined>): string[] {
  return Array.from(
    new Set(
      items
        .map((item) => item?.trim())
        .filter((item): item is string => Boolean(item)),
    ),
  );
}

export function buildEmploymentDirectionCategorySections(
  items: EmploymentDirectionItem[],
): EmploymentDirectionCategorySection[] {
  const sections = new Map<string, EmploymentDirectionCategorySection>();
  const categoryOrder = new Map(employmentDirectionCategoryOptions.map((item, index) => [item, index]));

  for (const item of items) {
    const category = item.category?.trim() || employmentDirectionUncategorizedLabel;
    const key = item.category?.trim() || "__uncategorized__";
    const existing = sections.get(key);
    if (existing) {
      existing.count += 1;
      existing.directions.push(item);
      continue;
    }
    sections.set(key, {
      key,
      label: category,
      count: 1,
      directions: [item],
    });
  }

  return [...sections.values()]
    .map((section) => ({
      ...section,
      directions: [...section.directions].sort((left, right) => left.name.localeCompare(right.name, "zh-Hans-CN")),
    }))
    .sort((left, right) => {
      const leftOrder = categoryOrder.get(left.label);
      const rightOrder = categoryOrder.get(right.label);
      if (leftOrder !== undefined && rightOrder !== undefined) return leftOrder - rightOrder;
      if (leftOrder !== undefined) return -1;
      if (rightOrder !== undefined) return 1;
      if (left.label === employmentDirectionUncategorizedLabel) return 1;
      if (right.label === employmentDirectionUncategorizedLabel) return -1;
      return left.label.localeCompare(right.label, "zh-Hans-CN");
    });
}
