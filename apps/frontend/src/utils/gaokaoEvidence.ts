export interface GaokaoCollegeEvidenceOption {
  college_id: number;
  college_name?: string | null;
  college_code?: string | null;
  province?: string | null;
  review_status?: string | null;
  source_mode?: string | null;
}

export function formatGaokaoCollegeEvidenceOptionLabel(option: GaokaoCollegeEvidenceOption): string {
  const segments = [option.college_name, option.college_code, option.province].filter((item) => item && item.trim());
  return segments.join(" · ") || `学校 ${option.college_id}`;
}

export function resolveGaokaoEvidenceCollegeId(options: {
  keyword: string;
  selectedCollegeId: number | null;
  candidates: GaokaoCollegeEvidenceOption[];
}): number | null {
  if (options.selectedCollegeId) {
    return options.selectedCollegeId;
  }

  const normalizedKeyword = options.keyword.trim();
  if (/^\d+$/.test(normalizedKeyword)) {
    return Number(normalizedKeyword);
  }

  if (options.candidates.length === 1) {
    return options.candidates[0]?.college_id ?? null;
  }

  return null;
}
