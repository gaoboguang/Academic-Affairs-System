import { computed, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import { useRouter } from "vue-router";

import { apiRequest } from "../../api/client";
import { formatUserActionError } from "../../utils/userFeedback";
import type {
  BooleanFilterValue,
  CollegeCatalogFilters,
  CollegeCatalogItem,
  CollegeCatalogPage,
  PaginationState,
} from "./types";

function boolFilterToQuery(value: BooleanFilterValue): string | null {
  if (value === "all") return null;
  return value;
}

export function useCollegeCatalogBrowser() {
  const router = useRouter();
  const colleges = ref<CollegeCatalogItem[]>([]);
  const loading = ref(false);
  const filters = reactive<CollegeCatalogFilters>({
    keyword: "",
    province: "",
    school_type: "",
    level_tag: "",
    has_profile: "all",
    has_admission_data: "all",
  });
  const pagination = reactive<PaginationState>({ page: 1, page_size: 50, total: 0 });

  const provinceOptions = computed(() =>
    Array.from(new Set(colleges.value.map((item) => item.province).filter((item): item is string => Boolean(item)))).sort(),
  );
  const schoolTypeOptions = computed(() =>
    Array.from(new Set(colleges.value.map((item) => item.school_type).filter((item): item is string => Boolean(item)))).sort(),
  );
  const levelTagOptions = computed(() =>
    Array.from(new Set(colleges.value.flatMap((item) => item.school_level_tags_json ?? []))).sort(),
  );

  async function loadCatalog(options: { resetPage?: boolean } = {}): Promise<void> {
    if (options.resetPage) pagination.page = 1;
    const query = new URLSearchParams();
    if (filters.keyword) query.set("keyword", filters.keyword);
    if (filters.province) query.set("province", filters.province);
    if (filters.school_type) query.set("school_type", filters.school_type);
    if (filters.level_tag) query.set("level_tag", filters.level_tag);
    const hasProfile = boolFilterToQuery(filters.has_profile);
    if (hasProfile) query.set("has_profile", hasProfile);
    const hasAdmissionData = boolFilterToQuery(filters.has_admission_data);
    if (hasAdmissionData) query.set("has_admission_data", hasAdmissionData);
    query.set("page", String(pagination.page));
    query.set("page_size", String(pagination.page_size));
    try {
      loading.value = true;
      const response = await apiRequest<CollegeCatalogPage>(`/api/colleges/catalog/page?${query.toString()}`);
      colleges.value = response.items;
      pagination.total = response.total;
      pagination.page = response.page;
      pagination.page_size = response.page_size;
    } catch (error) {
      ElMessage.error(formatUserActionError("查看院校库", error, "请调整筛选条件或刷新页面后重试。"));
    } finally {
      loading.value = false;
    }
  }

  async function resetFilters(): Promise<void> {
    filters.keyword = "";
    filters.province = "";
    filters.school_type = "";
    filters.level_tag = "";
    filters.has_profile = "all";
    filters.has_admission_data = "all";
    await loadCatalog({ resetPage: true });
  }

  function handlePageChange(page: number): void {
    pagination.page = page;
    void loadCatalog();
  }

  function handlePageSizeChange(pageSize: number): void {
    pagination.page_size = pageSize;
    pagination.page = 1;
    void loadCatalog();
  }

  function openDetail(collegeId: number): void {
    void router.push(`/colleges/${collegeId}`);
  }

  return {
    colleges,
    filters,
    handlePageChange,
    handlePageSizeChange,
    levelTagOptions,
    loadCatalog,
    loading,
    openDetail,
    pagination,
    provinceOptions,
    resetFilters,
    schoolTypeOptions,
  };
}
