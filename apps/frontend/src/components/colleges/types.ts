export type BooleanFilterValue = "all" | "true" | "false";

export interface CollegeCatalogItem {
  id: number;
  name: string;
  college_code?: string | null;
  province?: string | null;
  city?: string | null;
  school_type?: string | null;
  school_level_tags_json?: string[] | null;
  intro?: string | null;
  website?: string | null;
  supports_art: boolean;
  note?: string | null;
  alias_names?: string[] | null;
  is_active: boolean;
  has_profile: boolean;
  plan_count: number;
  admission_count: number;
  latest_plan_year?: number | null;
  latest_admission_year?: number | null;
}

export interface CollegeCatalogPage {
  items: CollegeCatalogItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface CollegeCatalogFilters {
  keyword: string;
  province: string;
  school_type: string;
  level_tag: string;
  has_profile: BooleanFilterValue;
  has_admission_data: BooleanFilterValue;
}

export interface PaginationState {
  page: number;
  page_size: number;
  total: number;
}
