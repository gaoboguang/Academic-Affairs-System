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

// ---------------------------------------------------------------------------
// 编译期兼容性检查：与后端 OpenAPI 1:1 对应的几个 Detail 类型必须是生成类型的子集。
// 如果 `npm run gen:api` 之后这一块标红，说明后端 schema 改了，先把上面的 interface
// 对齐再继续。
// ---------------------------------------------------------------------------

import type { components as _ApiComponents } from "../../types/api.generated";

type _DetailSchemas = _ApiComponents["schemas"];
type _DetailIsAssignable<L, R> = [L] extends [R] ? true : false;

interface _DetailSchemaAssertions {
  collegeProfile: _DetailIsAssignable<
    CollegeProfileDetail,
    _DetailSchemas["CollegeProfileDetailRead"]
  >;
  collegeYearSummary: _DetailIsAssignable<
    CollegeYearSummary,
    _DetailSchemas["CollegeYearSummaryRead"]
  >;
  majorProfile: _DetailIsAssignable<
    MajorProfileDetail,
    _DetailSchemas["MajorProfileDetailRead"]
  >;
  collegeMajorProfile: _DetailIsAssignable<
    CollegeMajorProfile,
    _DetailSchemas["CollegeMajorProfileRead"]
  >;
  gaokaoProfileSource: _DetailIsAssignable<
    GaokaoProfileSource,
    _DetailSchemas["GaokaoProfileSourceRead"]
  >;
  collegeDetail: _DetailIsAssignable<
    CollegeDetail,
    _DetailSchemas["CollegeDetailRead"]
  >;
  majorDetail: _DetailIsAssignable<MajorDetail, _DetailSchemas["MajorDetailRead"]>;
}

type _DetailAllTrue<T> = { [K in keyof T]: T[K] extends true ? T[K] : never };
type _DetailSchemaCompatOk = _DetailAllTrue<_DetailSchemaAssertions>;
const _detailSchemaCompatOk: _DetailSchemaCompatOk = {} as _DetailSchemaCompatOk;
void _detailSchemaCompatOk;
