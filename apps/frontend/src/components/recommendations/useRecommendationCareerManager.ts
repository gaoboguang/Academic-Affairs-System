import { computed, reactive, ref } from "vue";
import type { Ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest } from "../../api/client";
import { formatUserActionError } from "../../utils/userFeedback";
import {
  createEmploymentDirectionForm,
  createMajorEmploymentMappingForm,
  employmentDirectionCategoryOptions,
  employmentMappingStrengthOptions,
  uniqueStrings,
} from "./helpers";
import type {
  EmploymentDirectionFiltersState,
  EmploymentDirectionItem,
  EmploymentDirectionPayload,
  MajorEmploymentMappingFiltersState,
  MajorEmploymentMappingItem,
  MajorEmploymentMappingPayload,
  MajorItem,
} from "./types";

function reportError(error: unknown): void {
  ElMessage.error(formatUserActionError("维护职业方向或专业映射", error, "先确认筛选条件和表单字段正确；如果仍失败，请刷新当前页签后重试。"));
}

interface RecommendationCareerManagerOptions {
  majorDirectory: Ref<MajorItem[]>;
}

export function useRecommendationCareerManager(options: RecommendationCareerManagerOptions) {
  const employmentDirections = ref<EmploymentDirectionItem[]>([]);
  const majorEmploymentMappings = ref<MajorEmploymentMappingItem[]>([]);
  const employmentDirectionDialogVisible = ref(false);
  const majorEmploymentMappingDialogVisible = ref(false);
  const editingEmploymentDirectionId = ref<number | null>(null);
  const editingMajorEmploymentMappingId = ref<number | null>(null);
  const savingEmploymentDirection = ref(false);
  const savingMajorEmploymentMapping = ref(false);

  const employmentDirectionFilters = reactive<EmploymentDirectionFiltersState>({
    keyword: "",
    category: "",
  });
  const majorEmploymentMappingFilters = reactive<MajorEmploymentMappingFiltersState>({
    keyword: "",
    major_id: undefined,
    direction_id: undefined,
    strength: "",
  });

  const employmentDirectionForm = reactive<EmploymentDirectionPayload>(createEmploymentDirectionForm());
  const majorEmploymentMappingForm = reactive<MajorEmploymentMappingPayload>(createMajorEmploymentMappingForm());

  const employmentDirectionDialogTitle = computed(() =>
    editingEmploymentDirectionId.value ? "编辑就业方向" : "新增就业方向",
  );
  const majorEmploymentMappingDialogTitle = computed(() =>
    editingMajorEmploymentMappingId.value ? "编辑专业就业映射" : "新增专业就业映射",
  );
  const employmentDirectionOptions = computed(() => employmentDirections.value.filter((item) => item.is_active));
  const employmentDirectionCategoryFilterOptions = computed(() =>
    uniqueStrings([
      ...employmentDirectionCategoryOptions,
      ...employmentDirections.value.map((item) => item.category),
    ]),
  );

  async function loadEmploymentDirections(): Promise<void> {
    try {
      const query = new URLSearchParams();
      if (employmentDirectionFilters.keyword) query.set("keyword", employmentDirectionFilters.keyword);
      if (employmentDirectionFilters.category) query.set("category", employmentDirectionFilters.category);
      employmentDirections.value = await apiRequest<EmploymentDirectionItem[]>(
        `/api/employment-directions?${query.toString()}`,
      );
    } catch (error) {
      reportError(error);
    }
  }

  async function loadMajorEmploymentMappings(): Promise<void> {
    try {
      const query = new URLSearchParams();
      if (majorEmploymentMappingFilters.keyword) query.set("keyword", majorEmploymentMappingFilters.keyword);
      if (majorEmploymentMappingFilters.major_id) query.set("major_id", String(majorEmploymentMappingFilters.major_id));
      if (majorEmploymentMappingFilters.direction_id) query.set("direction_id", String(majorEmploymentMappingFilters.direction_id));
      if (majorEmploymentMappingFilters.strength) query.set("strength", majorEmploymentMappingFilters.strength);
      majorEmploymentMappings.value = await apiRequest<MajorEmploymentMappingItem[]>(
        `/api/major-employment-maps?${query.toString()}`,
      );
    } catch (error) {
      reportError(error);
    }
  }

  function resetEmploymentDirectionFilters(): void {
    employmentDirectionFilters.keyword = "";
    employmentDirectionFilters.category = "";
    void loadEmploymentDirections();
  }

  function resetMajorEmploymentMappingFilters(): void {
    majorEmploymentMappingFilters.keyword = "";
    majorEmploymentMappingFilters.major_id = undefined;
    majorEmploymentMappingFilters.direction_id = undefined;
    majorEmploymentMappingFilters.strength = "";
    void loadMajorEmploymentMappings();
  }

  function openCreateEmploymentDirection(): void {
    editingEmploymentDirectionId.value = null;
    Object.assign(employmentDirectionForm, createEmploymentDirectionForm());
    employmentDirectionDialogVisible.value = true;
  }

  function openEditEmploymentDirection(row: EmploymentDirectionItem): void {
    editingEmploymentDirectionId.value = row.id;
    Object.assign(employmentDirectionForm, {
      name: row.name,
      category: row.category ?? null,
      alias_names_json: [...(row.alias_names_json ?? [])],
      description: row.description ?? null,
      common_job_types_json: [...(row.common_job_types_json ?? [])],
      common_industries_json: [...(row.common_industries_json ?? [])],
      prefers_postgraduate: row.prefers_postgraduate,
      requires_certificate: row.requires_certificate,
      requires_long_cycle: row.requires_long_cycle,
      supports_art: row.supports_art,
      risk_note: row.risk_note ?? null,
      source_note: row.source_note ?? null,
      is_active: row.is_active,
    });
    employmentDirectionDialogVisible.value = true;
  }

  async function submitEmploymentDirection(): Promise<void> {
    if (!employmentDirectionForm.name.trim()) {
      ElMessage.warning("就业方向名称不能为空");
      return;
    }
    try {
      savingEmploymentDirection.value = true;
      const path = editingEmploymentDirectionId.value
        ? `/api/employment-directions/${editingEmploymentDirectionId.value}`
        : "/api/employment-directions";
      const method = editingEmploymentDirectionId.value ? "PUT" : "POST";
      const payload: EmploymentDirectionPayload = {
        ...employmentDirectionForm,
        alias_names_json: uniqueStrings(employmentDirectionForm.alias_names_json),
        common_job_types_json: uniqueStrings(employmentDirectionForm.common_job_types_json),
        common_industries_json: uniqueStrings(employmentDirectionForm.common_industries_json),
      };
      await apiRequest(path, { method, body: JSON.stringify(payload) });
      employmentDirectionDialogVisible.value = false;
      await Promise.all([loadEmploymentDirections(), loadMajorEmploymentMappings()]);
      ElMessage.success("就业方向保存成功");
    } catch (error) {
      reportError(error);
    } finally {
      savingEmploymentDirection.value = false;
    }
  }

  function openCreateMajorEmploymentMapping(): void {
    editingMajorEmploymentMappingId.value = null;
    Object.assign(majorEmploymentMappingForm, createMajorEmploymentMappingForm());
    majorEmploymentMappingDialogVisible.value = true;
  }

  function openEditMajorEmploymentMapping(row: MajorEmploymentMappingItem): void {
    editingMajorEmploymentMappingId.value = row.id;
    Object.assign(majorEmploymentMappingForm, {
      major_id: row.major_id,
      direction_id: row.direction_id,
      strength: row.strength,
      recommendation_note: row.recommendation_note ?? null,
      requires_postgraduate: row.requires_postgraduate,
      requires_certificate: row.requires_certificate,
      supported_student_types_json: [...(row.supported_student_types_json ?? [])],
      supports_art: row.supports_art,
      note: row.note ?? null,
      is_active: row.is_active,
    });
    majorEmploymentMappingDialogVisible.value = true;
  }

  async function submitMajorEmploymentMapping(): Promise<void> {
    if (!majorEmploymentMappingForm.major_id || !majorEmploymentMappingForm.direction_id) {
      ElMessage.warning("专业和就业方向都不能为空");
      return;
    }
    try {
      savingMajorEmploymentMapping.value = true;
      const path = editingMajorEmploymentMappingId.value
        ? `/api/major-employment-maps/${editingMajorEmploymentMappingId.value}`
        : "/api/major-employment-maps";
      const method = editingMajorEmploymentMappingId.value ? "PUT" : "POST";
      const payload: MajorEmploymentMappingPayload = {
        ...majorEmploymentMappingForm,
        supported_student_types_json: uniqueStrings(majorEmploymentMappingForm.supported_student_types_json),
      };
      await apiRequest(path, { method, body: JSON.stringify(payload) });
      majorEmploymentMappingDialogVisible.value = false;
      await loadMajorEmploymentMappings();
      ElMessage.success("专业就业映射保存成功");
    } catch (error) {
      reportError(error);
    } finally {
      savingMajorEmploymentMapping.value = false;
    }
  }

  function handleEmploymentDirectionDialogClosed(): void {
    editingEmploymentDirectionId.value = null;
    Object.assign(employmentDirectionForm, createEmploymentDirectionForm());
  }

  function handleMajorEmploymentMappingDialogClosed(): void {
    editingMajorEmploymentMappingId.value = null;
    Object.assign(majorEmploymentMappingForm, createMajorEmploymentMappingForm());
  }

  return {
    employmentDirectionCategoryFilterOptions,
    employmentDirectionDialogTitle,
    employmentDirectionDialogVisible,
    employmentDirectionFilters,
    employmentDirectionForm,
    employmentDirectionOptions,
    employmentDirections,
    handleEmploymentDirectionDialogClosed,
    handleMajorEmploymentMappingDialogClosed,
    loadEmploymentDirections,
    loadMajorEmploymentMappings,
    majorDirectory: options.majorDirectory,
    majorEmploymentMappingDialogTitle,
    majorEmploymentMappingDialogVisible,
    majorEmploymentMappingFilters,
    majorEmploymentMappingForm,
    majorEmploymentMappings,
    employmentMappingStrengthOptions,
    openCreateEmploymentDirection,
    openCreateMajorEmploymentMapping,
    openEditEmploymentDirection,
    openEditMajorEmploymentMapping,
    resetEmploymentDirectionFilters,
    resetMajorEmploymentMappingFilters,
    savingEmploymentDirection,
    savingMajorEmploymentMapping,
    submitEmploymentDirection,
    submitMajorEmploymentMapping,
  };
}
