import { computed, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import type { UploadFile } from "element-plus";

import { apiRequest, openFile, uploadFile } from "../../api/client";
import { formatUserActionError } from "../../utils/userFeedback";
import {
  baseSchoolLevelOptions,
  createCollegeForm,
  createMajorForm,
  provinceOptions,
  recommendationStudentTypeOptions,
  uniqueStrings,
} from "./helpers";
import type {
  AdmissionFiltersState,
  AdmissionImportResponse,
  AdmissionRecord,
  CollegeFiltersState,
  CollegeItem,
  CollegePayload,
  MajorFiltersState,
  MajorItem,
  MajorPayload,
  PaginatedResponse,
  PaginationState,
} from "./types";

function reportError(error: unknown): void {
  ElMessage.error(formatUserActionError("维护院校专业基础库", error, "先确认筛选条件、表单字段或导入模板正确；如果仍失败，请刷新当前页签后重试。"));
}

export function useRecommendationCatalogManager() {
  const collegeDirectory = ref<CollegeItem[]>([]);
  const majorDirectory = ref<MajorItem[]>([]);
  const colleges = ref<CollegeItem[]>([]);
  const majors = ref<MajorItem[]>([]);
  const admissions = ref<AdmissionRecord[]>([]);
  const admissionImportResult = ref<AdmissionImportResponse | null>(null);
  const collegePagination = reactive<PaginationState>({ page: 1, page_size: 50, total: 0 });
  const majorPagination = reactive<PaginationState>({ page: 1, page_size: 50, total: 0 });
  const admissionPagination = reactive<PaginationState>({ page: 1, page_size: 50, total: 0 });

  const collegeDialogVisible = ref(false);
  const majorDialogVisible = ref(false);
  const editingCollegeId = ref<number | null>(null);
  const editingMajorId = ref<number | null>(null);
  const savingCollege = ref(false);
  const savingMajor = ref(false);

  const collegeFilters = reactive<CollegeFiltersState>({
    keyword: "",
    province: "",
    supports_art: "all",
  });

  const majorFilters = reactive<MajorFiltersState>({
    keyword: "",
    is_art_related: "all",
  });

  const admissionFilters = reactive<AdmissionFiltersState>({
    year: undefined,
    province: "山东",
    college_id: undefined,
    student_type: "",
  });

  const collegeForm = reactive<CollegePayload>(createCollegeForm());
  const majorForm = reactive<MajorPayload>(createMajorForm());

  const schoolLevelOptions = computed(() =>
    uniqueStrings([
      ...baseSchoolLevelOptions,
      ...collegeDirectory.value.flatMap((item) => item.school_level_tags_json ?? []),
    ]),
  );

  const targetRegionOptions = computed(() =>
    uniqueStrings([
      ...provinceOptions,
      ...collegeDirectory.value.map((item) => item.province).filter((item): item is string => Boolean(item)),
      ...collegeDirectory.value.map((item) => item.city).filter((item): item is string => Boolean(item)),
    ]),
  );

  const admissionYearOptions = computed(() => {
    const years = new Set<number>();
    for (let year = 2026; year >= 2020; year -= 1) years.add(year);
    admissions.value.forEach((item) => years.add(item.year));
    return Array.from(years).sort((left, right) => right - left);
  });

  const collegeDialogTitle = computed(() => (editingCollegeId.value ? "编辑院校" : "新增院校"));
  const majorDialogTitle = computed(() => (editingMajorId.value ? "编辑专业" : "新增专业"));

  function downloadAdmissionTemplate(): void {
    openFile(`/api/system/files?path=${encodeURIComponent("data/templates/admission_records_import_template.xlsx")}`);
  }

  async function loadCollegeDirectory(): Promise<void> {
    collegeDirectory.value = await apiRequest<CollegeItem[]>("/api/colleges");
  }

  async function loadMajorDirectory(): Promise<void> {
    majorDirectory.value = await apiRequest<MajorItem[]>("/api/majors");
  }

  async function loadColleges(options: { resetPage?: boolean } = {}): Promise<void> {
    try {
      if (options.resetPage) collegePagination.page = 1;
      const query = new URLSearchParams();
      if (collegeFilters.keyword) query.set("keyword", collegeFilters.keyword);
      if (collegeFilters.province) query.set("province", collegeFilters.province);
      if (collegeFilters.supports_art !== "all") query.set("supports_art", String(collegeFilters.supports_art === "true"));
      query.set("page", String(collegePagination.page));
      query.set("page_size", String(collegePagination.page_size));
      const response = await apiRequest<PaginatedResponse<CollegeItem>>(`/api/colleges/page?${query.toString()}`);
      colleges.value = response.items;
      collegePagination.total = response.total;
      collegePagination.page = response.page;
      collegePagination.page_size = response.page_size;
    } catch (error) {
      reportError(error);
    }
  }

  async function loadMajors(options: { resetPage?: boolean } = {}): Promise<void> {
    try {
      if (options.resetPage) majorPagination.page = 1;
      const query = new URLSearchParams();
      if (majorFilters.keyword) query.set("keyword", majorFilters.keyword);
      if (majorFilters.is_art_related !== "all") query.set("is_art_related", String(majorFilters.is_art_related === "true"));
      query.set("page", String(majorPagination.page));
      query.set("page_size", String(majorPagination.page_size));
      const response = await apiRequest<PaginatedResponse<MajorItem>>(`/api/majors/page?${query.toString()}`);
      majors.value = response.items;
      majorPagination.total = response.total;
      majorPagination.page = response.page;
      majorPagination.page_size = response.page_size;
    } catch (error) {
      reportError(error);
    }
  }

  async function loadAdmissions(options: { resetPage?: boolean } = {}): Promise<void> {
    try {
      if (options.resetPage) admissionPagination.page = 1;
      const query = new URLSearchParams();
      if (admissionFilters.year) query.set("year", String(admissionFilters.year));
      if (admissionFilters.province) query.set("province", admissionFilters.province);
      if (admissionFilters.college_id) query.set("college_id", String(admissionFilters.college_id));
      if (admissionFilters.student_type) query.set("student_type", admissionFilters.student_type);
      query.set("page", String(admissionPagination.page));
      query.set("page_size", String(admissionPagination.page_size));
      const response = await apiRequest<PaginatedResponse<AdmissionRecord>>(`/api/admissions/page?${query.toString()}`);
      admissions.value = response.items;
      admissionPagination.total = response.total;
      admissionPagination.page = response.page;
      admissionPagination.page_size = response.page_size;
    } catch (error) {
      reportError(error);
    }
  }

  function resetCollegeFilters(): void {
    collegeFilters.keyword = "";
    collegeFilters.province = "";
    collegeFilters.supports_art = "all";
    void loadColleges({ resetPage: true });
  }

  function resetMajorFilters(): void {
    majorFilters.keyword = "";
    majorFilters.is_art_related = "all";
    void loadMajors({ resetPage: true });
  }

  function resetAdmissionFilters(): void {
    admissionFilters.year = undefined;
    admissionFilters.province = "山东";
    admissionFilters.college_id = undefined;
    admissionFilters.student_type = "";
    void loadAdmissions({ resetPage: true });
  }

  function handleMajorPageChange(page: number): void {
    majorPagination.page = page;
    void loadMajors();
  }

  function handleMajorPageSizeChange(pageSize: number): void {
    majorPagination.page_size = pageSize;
    majorPagination.page = 1;
    void loadMajors();
  }

  function handleCollegePageChange(page: number): void {
    collegePagination.page = page;
    void loadColleges();
  }

  function handleCollegePageSizeChange(pageSize: number): void {
    collegePagination.page_size = pageSize;
    collegePagination.page = 1;
    void loadColleges();
  }

  function handleAdmissionPageChange(page: number): void {
    admissionPagination.page = page;
    void loadAdmissions();
  }

  function handleAdmissionPageSizeChange(pageSize: number): void {
    admissionPagination.page_size = pageSize;
    admissionPagination.page = 1;
    void loadAdmissions();
  }

  function openCreateCollege(): void {
    editingCollegeId.value = null;
    Object.assign(collegeForm, createCollegeForm());
    collegeDialogVisible.value = true;
  }

  function openEditCollege(row: CollegeItem): void {
    editingCollegeId.value = row.id;
    Object.assign(collegeForm, {
      name: row.name,
      college_code: row.college_code ?? null,
      province: row.province ?? null,
      city: row.city ?? null,
      school_type: row.school_type ?? null,
      school_level_tags_json: [...(row.school_level_tags_json ?? [])],
      intro: row.intro ?? null,
      website: row.website ?? null,
      supports_art: row.supports_art,
      note: row.note ?? null,
      alias_names: [...(row.alias_names ?? [])],
      is_active: row.is_active,
    });
    collegeDialogVisible.value = true;
  }

  async function submitCollege(): Promise<void> {
    if (!collegeForm.name.trim()) {
      ElMessage.warning("院校名称不能为空");
      return;
    }
    try {
      savingCollege.value = true;
      const payload: CollegePayload = {
        ...collegeForm,
        school_level_tags_json: uniqueStrings(collegeForm.school_level_tags_json),
        alias_names: uniqueStrings(collegeForm.alias_names),
      };
      const path = editingCollegeId.value ? `/api/colleges/${editingCollegeId.value}` : "/api/colleges";
      const method = editingCollegeId.value ? "PUT" : "POST";
      await apiRequest(path, { method, body: JSON.stringify(payload) });
      collegeDialogVisible.value = false;
      await Promise.all([loadCollegeDirectory(), loadColleges({ resetPage: true })]);
      ElMessage.success("院校保存成功");
    } catch (error) {
      reportError(error);
    } finally {
      savingCollege.value = false;
    }
  }

  function openCreateMajor(): void {
    editingMajorId.value = null;
    Object.assign(majorForm, createMajorForm());
    majorDialogVisible.value = true;
  }

  function openEditMajor(row: MajorItem): void {
    editingMajorId.value = row.id;
    Object.assign(majorForm, {
      name: row.name,
      major_code: row.major_code ?? null,
      category: row.category ?? null,
      direction: row.direction ?? null,
      career_path: row.career_path ?? null,
      is_art_related: row.is_art_related,
      note: row.note ?? null,
      is_active: row.is_active,
    });
    majorDialogVisible.value = true;
  }

  async function submitMajor(): Promise<void> {
    if (!majorForm.name.trim()) {
      ElMessage.warning("专业名称不能为空");
      return;
    }
    try {
      savingMajor.value = true;
      const path = editingMajorId.value ? `/api/majors/${editingMajorId.value}` : "/api/majors";
      const method = editingMajorId.value ? "PUT" : "POST";
      await apiRequest(path, { method, body: JSON.stringify(majorForm) });
      majorDialogVisible.value = false;
      await Promise.all([loadMajorDirectory(), loadMajors({ resetPage: true })]);
      ElMessage.success("专业保存成功");
    } catch (error) {
      reportError(error);
    } finally {
      savingMajor.value = false;
    }
  }

  function handleCollegeDialogClosed(): void {
    editingCollegeId.value = null;
    Object.assign(collegeForm, createCollegeForm());
  }

  function handleMajorDialogClosed(): void {
    editingMajorId.value = null;
    Object.assign(majorForm, createMajorForm());
  }

  async function handleAdmissionImport(uploadFileItem: UploadFile): Promise<void> {
    if (!uploadFileItem.raw) return;
    try {
      admissionImportResult.value = await uploadFile<AdmissionImportResponse>("/api/admissions/import", uploadFileItem.raw);
      await Promise.all([loadCollegeDirectory(), loadMajorDirectory(), loadAdmissions({ resetPage: true })]);
      ElMessage({
        type: admissionImportResult.value.failed_rows ? "warning" : "success",
        message: admissionImportResult.value.message,
      });
    } catch (error) {
      reportError(error);
    }
  }

  return {
    admissionFilters,
    admissionImportResult,
    admissionPagination,
    admissionYearOptions,
    admissions,
    recommendationStudentTypeOptions,
    collegeDialogTitle,
    collegeDialogVisible,
    collegeDirectory,
    collegeFilters,
    collegeForm,
    collegePagination,
    colleges,
    downloadAdmissionTemplate,
    handleAdmissionImport,
    handleAdmissionPageChange,
    handleAdmissionPageSizeChange,
    handleCollegePageChange,
    handleCollegePageSizeChange,
    handleCollegeDialogClosed,
    handleMajorPageChange,
    handleMajorPageSizeChange,
    handleMajorDialogClosed,
    loadAdmissions,
    loadCollegeDirectory,
    loadColleges,
    loadMajorDirectory,
    loadMajors,
    majorDialogTitle,
    majorDialogVisible,
    majorDirectory,
    majorFilters,
    majorForm,
    majorPagination,
    majors,
    openCreateCollege,
    openCreateMajor,
    openEditCollege,
    openEditMajor,
    resetAdmissionFilters,
    resetCollegeFilters,
    resetMajorFilters,
    savingCollege,
    savingMajor,
    schoolLevelOptions,
    submitCollege,
    submitMajor,
    targetRegionOptions,
  };
}
