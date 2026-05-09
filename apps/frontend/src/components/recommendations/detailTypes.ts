import type {
  AdmissionRecord,
  CollegeItem,
  EnrollmentPlanItem,
  MajorEmploymentMappingItem,
  MajorItem,
} from "./types";

export interface CollegeProfileDetail {
  id: number;
  college_id: number;
  enrollment_code?: string | null;
  authority_department?: string | null;
  education_level?: string | null;
  is_985: boolean;
  is_211: boolean;
  is_dual_class: boolean;
  ruanke_rank?: number | null;
  eol_rank?: number | null;
  area?: string | null;
  master_program_count?: number | null;
  doctor_program_count?: number | null;
  official_website?: string | null;
  admission_website?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  summary?: string | null;
  source_path?: string | null;
  source_sha256?: string | null;
  is_active: boolean;
}

export interface CollegeYearSummary {
  id: number;
  college_id: number;
  province: string;
  year: number;
  total_plan_count?: number | null;
  specialty_count?: number | null;
  min_rank?: number | null;
  estimated_min_score?: number | null;
  source_note?: string | null;
  source_path?: string | null;
  source_sha256?: string | null;
  is_active: boolean;
}

export interface MajorProfileDetail {
  id: number;
  major_id: number;
  major_code?: string | null;
  education_level?: string | null;
  schooling_years?: string | null;
  direction?: string | null;
  tags_json: string[];
  summary?: string | null;
  source_path?: string | null;
  source_sha256?: string | null;
  is_active: boolean;
}

export interface CollegeMajorProfile {
  id: number;
  college_id: number;
  college_name?: string | null;
  major_id: number;
  major_name?: string | null;
  school_major_feature?: string | null;
  is_national_feature: boolean;
  is_provincial_feature: boolean;
  is_key_major: boolean;
  schooling_years?: string | null;
  education_level?: string | null;
  source_path?: string | null;
  source_sha256?: string | null;
  is_active: boolean;
}

export interface GaokaoProfileSource {
  source_path?: string | null;
  source_sha256?: string | null;
  source_type: string;
  title?: string | null;
}

export interface CollegeDetail {
  college: CollegeItem;
  profile?: CollegeProfileDetail | null;
  year_summaries: CollegeYearSummary[];
  major_profiles: CollegeMajorProfile[];
  recent_admissions: AdmissionRecord[];
  recent_plans: EnrollmentPlanItem[];
  source_documents: GaokaoProfileSource[];
}

export interface MajorDetail {
  major: MajorItem;
  profile?: MajorProfileDetail | null;
  college_profiles: CollegeMajorProfile[];
  employment_mappings: MajorEmploymentMappingItem[];
  recent_admissions: AdmissionRecord[];
  recent_plans: EnrollmentPlanItem[];
  subject_requirement_samples: string[];
  source_documents: GaokaoProfileSource[];
}
