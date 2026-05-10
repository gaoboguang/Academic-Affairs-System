import type {
  VolunteerGuideCandidateGroup,
  VolunteerGuideGroupKey,
  VolunteerGuidePreviewResponse,
  VolunteerGuideReadiness,
  VolunteerGuideStepCard,
} from "./types";

const GUIDE_GROUP_ORDER: VolunteerGuideGroupKey[] = ["challenge", "steady", "safe", "watch"];

export function buildVolunteerGuideReadiness(
  guide: VolunteerGuidePreviewResponse | null,
): VolunteerGuideReadiness {
  if (guide) {
    return guide.readiness;
  }
  return {
    status: "blocked",
    blocking_count: 1,
    warning_count: 0,
    info_count: 0,
    items: [
      {
        code: "not_generated",
        level: "blocking",
        title: "尚未生成智能筛选",
        detail: "请先确认考生条件和意向偏好，再点击生成推荐。",
      },
    ],
  };
}

export function groupVolunteerGuideCandidates(
  guide: VolunteerGuidePreviewResponse | null,
): VolunteerGuideCandidateGroup[] {
  if (!guide) {
    return GUIDE_GROUP_ORDER.map((key) => ({
      key,
      label: groupLabel(key),
      count: 0,
      candidates: [],
    }));
  }
  return GUIDE_GROUP_ORDER.map((key) => guide.groups[key] ?? {
    key,
    label: groupLabel(key),
    count: 0,
    candidates: [],
  });
}

export function buildVolunteerGuideStepCards(
  guide: VolunteerGuidePreviewResponse | null,
  draftCount = 0,
): VolunteerGuideStepCard[] {
  const readiness = buildVolunteerGuideReadiness(guide);
  const candidateCount = guide?.source_preview.candidate_count ?? 0;
  const preferenceStatus = hasPreferenceSignal(guide) ? "已纳入偏好" : "可继续补充";
  return [
    {
      key: "candidate",
      title: "考生条件",
      summary: guide
        ? `${guide.student_name || "当前学生"} · ${guide.province} · ${guide.target_year} · ${guide.source_preview.score_input_label}`
        : "选择学生、考试、年份、批次、科类、成绩/位次和选科组合",
      status: readiness.status,
    },
    {
      key: "preference",
      title: "意向偏好",
      summary: preferenceStatus,
      status: readiness.status === "blocked" ? "blocked" : "ready",
    },
    {
      key: "screening",
      title: "智能筛选",
      summary: candidateCount ? `${candidateCount} 条候选，按冲稳保分组` : "生成后展示冲刺、稳妥、保底和仅关注",
      status: candidateCount ? readiness.status : "blocked",
    },
    {
      key: "draft",
      title: "志愿草稿",
      summary: draftCount ? `已加入 ${draftCount} 条志愿` : "从候选加入草稿后排序、复核、保存和导出",
      status: draftCount ? "ready" : "warning",
    },
  ];
}

function hasPreferenceSignal(guide: VolunteerGuidePreviewResponse | null): boolean {
  if (!guide) return false;
  return groupVolunteerGuideCandidates(guide).some((group) =>
    group.candidates.some((item) => Boolean(item.candidate.career_match_summary || item.candidate.matched_direction_names_json.length)),
  );
}

function groupLabel(key: VolunteerGuideGroupKey): string {
  const labels: Record<VolunteerGuideGroupKey, string> = {
    challenge: "冲刺",
    steady: "稳妥",
    safe: "保底",
    watch: "仅关注",
  };
  return labels[key];
}
