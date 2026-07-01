import { computed, reactive, ref } from "vue";
import type { Ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";
import type { UploadFile } from "element-plus";

import { apiRequest, openFile, uploadFile } from "../../api/client";
import { formatUserActionError } from "../../utils/userFeedback";
import {
  createProvinceVolunteerRuleForm,
  gaokaoCandidateTypeOptions,
  gaokaoExamModeOptions,
  parallelRuleModeOptions,
  provinceOptions,
  recommendationStudentTypeOptions,
  subjectRequirementModeOptions,
  uniqueStrings,
  volunteerUnitTypeOptions,
} from "./helpers";
import type {
  CollegeItem,
  EnrollmentPlanFiltersState,
  EnrollmentPlanImportResponse,
  EnrollmentPlanItem,
  PaginatedResponse,
  PaginationState,
  ProvinceVolunteerRuleBootstrapResponse,
  ProvinceVolunteerRule,
  ProvinceVolunteerRuleFiltersState,
  ProvinceVolunteerRulePayload,
  ProvinceScoreTransformRule,
  ProvinceScoreTransformRuleBootstrapResponse,
  ProvinceScoreTransformRuleFiltersState,
  SpecialTypeRule,
  SpecialTypeRuleBootstrapResponse,
  SpecialTypeRuleFiltersState,
  SubjectRequirementDict,
  SubjectRequirementDictBootstrapResponse,
  SubjectRequirementDictFiltersState,
} from "./types";

interface GaokaoPlanningManagerOptions {
  collegeDirectory: Ref<CollegeItem[]>;
  reloadCollegeDirectory?: () => Promise<void>;
  reloadMajorDirectory?: () => Promise<void>;
}

function reportError(error: unknown): void {
  ElMessage.error(formatUserActionError("维护高考规则或数据", error, "先确认筛选条件、导入模板或规则字段正确；如果仍失败，请刷新当前页签后重试。"));
}

function createYearOptions(values: number[]): number[] {
  const years = new Set<number>();
  const currentYear = new Date().getFullYear();
  for (let year = currentYear; year >= 2020; year -= 1) years.add(year);
  values.forEach((value) => years.add(value));
  return Array.from(years).sort((left, right) => right - left);
}

const commonBatchOptions = [
  "本科批",
  "专科批",
  "常规批",
  "普通类常规批",
  "艺术本科批",
  "体育常规批",
  "春季高考本科批",
  "春季高考专科批",
];

export function useGaokaoPlanningManager(options: GaokaoPlanningManagerOptions) {
  const enrollmentPlans = ref<EnrollmentPlanItem[]>([]);
  const provinceVolunteerRules = ref<ProvinceVolunteerRule[]>([]);
  const provinceScoreTransformRules = ref<ProvinceScoreTransformRule[]>([]);
  const subjectRequirementDicts = ref<SubjectRequirementDict[]>([]);
  const specialTypeRules = ref<SpecialTypeRule[]>([]);
  const enrollmentPlanImportResult = ref<EnrollmentPlanImportResponse | null>(null);
  const enrollmentPlanPagination = reactive<PaginationState>({ page: 1, page_size: 50, total: 0 });
  const loadingEnrollmentPlans = ref(false);
  const enrollmentPlansLoadError = ref("");
  const importingEnrollmentPlans = ref(false);

  const volunteerRuleDialogVisible = ref(false);
  const editingVolunteerRuleId = ref<number | null>(null);
  const savingVolunteerRule = ref(false);
  const loadingVolunteerRules = ref(false);
  const volunteerRulesLoadError = ref("");
  const loadingScoreTransformRules = ref(false);
  const scoreTransformRulesLoadError = ref("");
  const loadingSubjectRequirementDicts = ref(false);
  const subjectRequirementDictsLoadError = ref("");
  const loadingSpecialTypeRules = ref(false);
  const specialTypeRulesLoadError = ref("");
  const bootstrappingVolunteerRules = ref(false);
  const bootstrappingScoreTransformRules = ref(false);
  const bootstrappingSubjectRequirementDicts = ref(false);
  const bootstrappingSpecialTypeRules = ref(false);

  const enrollmentPlanFilters = reactive<EnrollmentPlanFiltersState>({
    year: undefined,
    province: "山东",
    batch: "",
    college_id: undefined,
    student_type: "",
    keyword: "",
  });

  const volunteerRuleFilters = reactive<ProvinceVolunteerRuleFiltersState>({
    year: undefined,
    province: "山东",
    exam_mode: "",
    candidate_type: "",
  });

  const scoreTransformRuleFilters = reactive<ProvinceScoreTransformRuleFiltersState>({
    year: undefined,
    province: "山东",
    exam_mode: "",
    subject_name: "",
  });

  const subjectRequirementDictFilters = reactive<SubjectRequirementDictFiltersState>({
    year: undefined,
    province: "山东",
    exam_mode: "",
    requirement_code: "",
  });

  const specialTypeRuleFilters = reactive<SpecialTypeRuleFiltersState>({
    year: undefined,
    province: "山东",
    student_type: "",
  });

  const volunteerRuleForm = reactive<ProvinceVolunteerRulePayload>(createProvinceVolunteerRuleForm());

  const planYearOptions = computed(() => createYearOptions(enrollmentPlans.value.map((item) => item.year)));
  const ruleYearOptions = computed(() => createYearOptions(provinceVolunteerRules.value.map((item) => item.year)));
  const scoreTransformRuleYearOptions = computed(() => createYearOptions(provinceScoreTransformRules.value.map((item) => item.year)));
  const subjectRequirementDictYearOptions = computed(() => createYearOptions(subjectRequirementDicts.value.map((item) => item.year)));
  const specialTypeRuleYearOptions = computed(() => createYearOptions(specialTypeRules.value.map((item) => item.year)));

  const examModeOptions = computed(() =>
    uniqueStrings([
      ...gaokaoExamModeOptions,
      ...enrollmentPlans.value.map((item) => item.exam_mode),
      ...provinceVolunteerRules.value.map((item) => item.exam_mode),
      ...provinceScoreTransformRules.value.map((item) => item.exam_mode),
      ...subjectRequirementDicts.value.map((item) => item.exam_mode),
    ]),
  );

  const batchOptions = computed(() =>
    uniqueStrings([
      ...commonBatchOptions,
      ...enrollmentPlans.value.map((item) => item.batch),
      ...provinceVolunteerRules.value.map((item) => item.batch),
    ]),
  );

  const specialRuleOptions = computed(() =>
    uniqueStrings(provinceVolunteerRules.value.flatMap((item) => item.special_rules_json ?? [])),
  );

  const volunteerRuleDialogTitle = computed(() => (editingVolunteerRuleId.value ? "编辑省份规则" : "新增省份规则"));

  const summaryCards = computed(() => [
    {
      label: "招生计划库",
      value: enrollmentPlans.value.length,
      help: `${new Set(enrollmentPlans.value.map((item) => item.year)).size} 个年份样本`,
      tone: "tone-indigo",
    },
    {
      label: "省份规则",
      value: provinceVolunteerRules.value.length,
      help: provinceVolunteerRules.value.length
        ? `${new Set(provinceVolunteerRules.value.map((item) => item.province)).size} 个省份已配置`
        : "建议先维护当前省份批次规则",
      tone: provinceVolunteerRules.value.length ? "tone-teal" : "tone-slate",
    },
    {
      label: "特殊类型规则",
      value: specialTypeRules.value.length,
      help: specialTypeRules.value.length
        ? `${new Set(specialTypeRules.value.map((item) => item.student_type)).size} 类特殊类型`
        : "建议先装载山东基线规则",
      tone: specialTypeRules.value.length ? "tone-amber" : "tone-slate",
    },
    {
      label: "赋分/选科字典",
      value: provinceScoreTransformRules.value.length + subjectRequirementDicts.value.length,
      help: `${provinceScoreTransformRules.value.length} 条赋分，${subjectRequirementDicts.value.length} 条选科`,
      tone: provinceScoreTransformRules.value.length && subjectRequirementDicts.value.length ? "tone-green" : "tone-slate",
    },
  ]);

  function downloadEnrollmentPlanTemplate(): void {
    openFile(`/api/system/files?path=${encodeURIComponent("data/templates/enrollment_plans_import_template.xlsx")}`);
  }

  async function loadEnrollmentPlans(options: { resetPage?: boolean } = {}): Promise<void> {
    loadingEnrollmentPlans.value = true;
    enrollmentPlansLoadError.value = "";
    try {
      if (options.resetPage) enrollmentPlanPagination.page = 1;
      const query = new URLSearchParams();
      if (enrollmentPlanFilters.year) query.set("year", String(enrollmentPlanFilters.year));
      if (enrollmentPlanFilters.province) query.set("province", enrollmentPlanFilters.province);
      if (enrollmentPlanFilters.batch) query.set("batch", enrollmentPlanFilters.batch);
      if (enrollmentPlanFilters.college_id) query.set("college_id", String(enrollmentPlanFilters.college_id));
      if (enrollmentPlanFilters.student_type) query.set("student_type", enrollmentPlanFilters.student_type);
      if (enrollmentPlanFilters.keyword) query.set("keyword", enrollmentPlanFilters.keyword);
      query.set("page", String(enrollmentPlanPagination.page));
      query.set("page_size", String(enrollmentPlanPagination.page_size));
      const response = await apiRequest<PaginatedResponse<EnrollmentPlanItem>>(
        `/api/enrollment-plans/page?${query.toString()}`,
      );
      enrollmentPlans.value = response.items;
      enrollmentPlanPagination.total = response.total;
      enrollmentPlanPagination.page = response.page;
      enrollmentPlanPagination.page_size = response.page_size;
    } catch (error) {
      enrollmentPlans.value = [];
      enrollmentPlanPagination.total = 0;
      enrollmentPlansLoadError.value = formatUserActionError(
        "加载招生计划库",
        error,
        "检查筛选条件或本地服务后重新加载招生计划库",
      );
    } finally {
      loadingEnrollmentPlans.value = false;
    }
  }

  async function loadProvinceVolunteerRules(): Promise<void> {
    loadingVolunteerRules.value = true;
    volunteerRulesLoadError.value = "";
    try {
      const query = new URLSearchParams();
      if (volunteerRuleFilters.year) query.set("year", String(volunteerRuleFilters.year));
      if (volunteerRuleFilters.province) query.set("province", volunteerRuleFilters.province);
      if (volunteerRuleFilters.exam_mode) query.set("exam_mode", volunteerRuleFilters.exam_mode);
      if (volunteerRuleFilters.candidate_type) query.set("candidate_type", volunteerRuleFilters.candidate_type);
      provinceVolunteerRules.value = await apiRequest<ProvinceVolunteerRule[]>(`/api/province-volunteer-rules?${query.toString()}`);
    } catch (error) {
      provinceVolunteerRules.value = [];
      volunteerRulesLoadError.value = formatUserActionError(
        "加载省份规则",
        error,
        "检查筛选条件或本地服务后重新加载省份规则",
      );
    } finally {
      loadingVolunteerRules.value = false;
    }
  }

  async function loadProvinceScoreTransformRules(): Promise<void> {
    loadingScoreTransformRules.value = true;
    scoreTransformRulesLoadError.value = "";
    try {
      const query = new URLSearchParams();
      if (scoreTransformRuleFilters.year) query.set("year", String(scoreTransformRuleFilters.year));
      if (scoreTransformRuleFilters.province) query.set("province", scoreTransformRuleFilters.province);
      if (scoreTransformRuleFilters.exam_mode) query.set("exam_mode", scoreTransformRuleFilters.exam_mode);
      if (scoreTransformRuleFilters.subject_name) query.set("subject_name", scoreTransformRuleFilters.subject_name);
      provinceScoreTransformRules.value = await apiRequest<ProvinceScoreTransformRule[]>(
        `/api/province-score-transform-rules?${query.toString()}`,
      );
    } catch (error) {
      provinceScoreTransformRules.value = [];
      scoreTransformRulesLoadError.value = formatUserActionError(
        "加载赋分/成绩转换规则",
        error,
        "检查筛选条件或本地服务后重新加载赋分规则",
      );
    } finally {
      loadingScoreTransformRules.value = false;
    }
  }

  async function loadSubjectRequirementDicts(): Promise<void> {
    loadingSubjectRequirementDicts.value = true;
    subjectRequirementDictsLoadError.value = "";
    try {
      const query = new URLSearchParams();
      if (subjectRequirementDictFilters.year) query.set("year", String(subjectRequirementDictFilters.year));
      if (subjectRequirementDictFilters.province) query.set("province", subjectRequirementDictFilters.province);
      if (subjectRequirementDictFilters.exam_mode) query.set("exam_mode", subjectRequirementDictFilters.exam_mode);
      if (subjectRequirementDictFilters.requirement_code) query.set("requirement_code", subjectRequirementDictFilters.requirement_code);
      subjectRequirementDicts.value = await apiRequest<SubjectRequirementDict[]>(
        `/api/subject-requirement-dicts?${query.toString()}`,
      );
    } catch (error) {
      subjectRequirementDicts.value = [];
      subjectRequirementDictsLoadError.value = formatUserActionError(
        "加载选科要求字典",
        error,
        "检查筛选条件或本地服务后重新加载选科字典",
      );
    } finally {
      loadingSubjectRequirementDicts.value = false;
    }
  }

  async function loadSpecialTypeRules(): Promise<void> {
    loadingSpecialTypeRules.value = true;
    specialTypeRulesLoadError.value = "";
    try {
      const query = new URLSearchParams();
      if (specialTypeRuleFilters.year) query.set("year", String(specialTypeRuleFilters.year));
      if (specialTypeRuleFilters.province) query.set("province", specialTypeRuleFilters.province);
      if (specialTypeRuleFilters.student_type) query.set("student_type", specialTypeRuleFilters.student_type);
      specialTypeRules.value = await apiRequest<SpecialTypeRule[]>(`/api/special-type-rules?${query.toString()}`);
    } catch (error) {
      specialTypeRules.value = [];
      specialTypeRulesLoadError.value = formatUserActionError(
        "加载特殊类型规则",
        error,
        "检查筛选条件或本地服务后重新加载特殊类型规则",
      );
    } finally {
      loadingSpecialTypeRules.value = false;
    }
  }

  async function bootstrapProvinceVolunteerRules(): Promise<void> {
    const targetYear = volunteerRuleFilters.year ?? new Date().getFullYear();
    try {
      await ElMessageBox.confirm(
        `会为 ${targetYear} 年补齐全国省份的本科批基线规则；已存在的同键规则会自动跳过。是否继续？`,
        "装载全国基线",
        {
          type: "warning",
          confirmButtonText: "继续装载",
          cancelButtonText: "取消",
        },
      );
    } catch {
      return;
    }

    try {
      bootstrappingVolunteerRules.value = true;
      const response = await apiRequest<ProvinceVolunteerRuleBootstrapResponse>(
        `/api/province-volunteer-rules/bootstrap?year=${targetYear}`,
        { method: "POST" },
      );
      volunteerRuleFilters.year = targetYear;
      await loadProvinceVolunteerRules();
      if (response.created_count > 0) {
        ElMessage.success(
          `已装载 ${response.created_count} 条基线规则，跳过 ${response.skipped_count} 条已存在规则`,
        );
      } else {
        ElMessage.success(`${targetYear} 年全国省份基线规则已存在，无需重复装载`);
      }
    } catch (error) {
      reportError(error);
    } finally {
      bootstrappingVolunteerRules.value = false;
    }
  }

  async function bootstrapProvinceScoreTransformRules(): Promise<void> {
    const targetYear = scoreTransformRuleFilters.year ?? new Date().getFullYear();
    try {
      await ElMessageBox.confirm(
        `会为 ${targetYear} 年装载省份赋分/成绩转换基线；已存在规则会自动跳过。是否继续？`,
        "装载赋分规则",
        {
          type: "warning",
          confirmButtonText: "继续装载",
          cancelButtonText: "取消",
        },
      );
    } catch {
      return;
    }

    try {
      bootstrappingScoreTransformRules.value = true;
      const response = await apiRequest<ProvinceScoreTransformRuleBootstrapResponse>(
        `/api/province-score-transform-rules/bootstrap?year=${targetYear}`,
        { method: "POST" },
      );
      scoreTransformRuleFilters.year = targetYear;
      await loadProvinceScoreTransformRules();
      if (response.created_count > 0) {
        ElMessage.success(`已装载 ${response.created_count} 条赋分规则，跳过 ${response.skipped_count} 条已存在规则`);
      } else {
        ElMessage.success(`${targetYear} 年赋分规则已存在，无需重复装载`);
      }
    } catch (error) {
      reportError(error);
    } finally {
      bootstrappingScoreTransformRules.value = false;
    }
  }

  async function bootstrapSubjectRequirementDicts(): Promise<void> {
    const targetYear = subjectRequirementDictFilters.year ?? new Date().getFullYear();
    try {
      await ElMessageBox.confirm(
        `会为 ${targetYear} 年装载选科要求字典基线；已存在字典会自动跳过。是否继续？`,
        "装载选科字典",
        {
          type: "warning",
          confirmButtonText: "继续装载",
          cancelButtonText: "取消",
        },
      );
    } catch {
      return;
    }

    try {
      bootstrappingSubjectRequirementDicts.value = true;
      const response = await apiRequest<SubjectRequirementDictBootstrapResponse>(
        `/api/subject-requirement-dicts/bootstrap?year=${targetYear}`,
        { method: "POST" },
      );
      subjectRequirementDictFilters.year = targetYear;
      await loadSubjectRequirementDicts();
      if (response.created_count > 0) {
        ElMessage.success(`已装载 ${response.created_count} 条选科字典，跳过 ${response.skipped_count} 条已存在字典`);
      } else {
        ElMessage.success(`${targetYear} 年选科字典已存在，无需重复装载`);
      }
    } catch (error) {
      reportError(error);
    } finally {
      bootstrappingSubjectRequirementDicts.value = false;
    }
  }

  async function bootstrapSpecialTypeRules(): Promise<void> {
    const targetYear = specialTypeRuleFilters.year ?? new Date().getFullYear();
    try {
      await ElMessageBox.confirm(
        `会为 ${targetYear} 年装载山东春考、综评、单招、艺术、体育等特殊类型规则；已存在规则会自动跳过。是否继续？`,
        "装载特殊类型规则",
        {
          type: "warning",
          confirmButtonText: "继续装载",
          cancelButtonText: "取消",
        },
      );
    } catch {
      return;
    }

    try {
      bootstrappingSpecialTypeRules.value = true;
      const response = await apiRequest<SpecialTypeRuleBootstrapResponse>(
        `/api/special-type-rules/bootstrap?year=${targetYear}`,
        { method: "POST" },
      );
      specialTypeRuleFilters.year = targetYear;
      specialTypeRuleFilters.province = "山东";
      await loadSpecialTypeRules();
      if (response.created_count > 0) {
        ElMessage.success(`已装载 ${response.created_count} 条特殊类型规则，跳过 ${response.skipped_count} 条已存在规则`);
      } else {
        ElMessage.success(`${targetYear} 年山东特殊类型规则已存在，无需重复装载`);
      }
    } catch (error) {
      reportError(error);
    } finally {
      bootstrappingSpecialTypeRules.value = false;
    }
  }

  function resetEnrollmentPlanFilters(): void {
    enrollmentPlanFilters.year = undefined;
    enrollmentPlanFilters.province = "山东";
    enrollmentPlanFilters.batch = "";
    enrollmentPlanFilters.college_id = undefined;
    enrollmentPlanFilters.student_type = "";
    enrollmentPlanFilters.keyword = "";
    void loadEnrollmentPlans({ resetPage: true });
  }

  function handleEnrollmentPlanPageChange(page: number): void {
    enrollmentPlanPagination.page = page;
    void loadEnrollmentPlans();
  }

  function handleEnrollmentPlanPageSizeChange(pageSize: number): void {
    enrollmentPlanPagination.page_size = pageSize;
    enrollmentPlanPagination.page = 1;
    void loadEnrollmentPlans();
  }

  function resetVolunteerRuleFilters(): void {
    volunteerRuleFilters.year = undefined;
    volunteerRuleFilters.province = "山东";
    volunteerRuleFilters.exam_mode = "";
    volunteerRuleFilters.candidate_type = "";
    void loadProvinceVolunteerRules();
  }

  function resetScoreTransformRuleFilters(): void {
    scoreTransformRuleFilters.year = undefined;
    scoreTransformRuleFilters.province = "山东";
    scoreTransformRuleFilters.exam_mode = "";
    scoreTransformRuleFilters.subject_name = "";
    void loadProvinceScoreTransformRules();
  }

  function resetSubjectRequirementDictFilters(): void {
    subjectRequirementDictFilters.year = undefined;
    subjectRequirementDictFilters.province = "山东";
    subjectRequirementDictFilters.exam_mode = "";
    subjectRequirementDictFilters.requirement_code = "";
    void loadSubjectRequirementDicts();
  }

  function resetSpecialTypeRuleFilters(): void {
    specialTypeRuleFilters.year = undefined;
    specialTypeRuleFilters.province = "山东";
    specialTypeRuleFilters.student_type = "";
    void loadSpecialTypeRules();
  }

  function openCreateVolunteerRule(): void {
    editingVolunteerRuleId.value = null;
    Object.assign(volunteerRuleForm, createProvinceVolunteerRuleForm());
    volunteerRuleDialogVisible.value = true;
  }

  function openEditVolunteerRule(rule: ProvinceVolunteerRule): void {
    editingVolunteerRuleId.value = rule.id;
    Object.assign(volunteerRuleForm, {
      province: rule.province,
      year: rule.year,
      exam_mode: rule.exam_mode,
      batch: rule.batch,
      candidate_type: rule.candidate_type,
      batch_order: rule.batch_order ?? undefined,
      total_score: rule.total_score,
      volunteer_limit: rule.volunteer_limit,
      volunteer_unit_type: rule.volunteer_unit_type,
      subject_requirement_mode: rule.subject_requirement_mode ?? null,
      required_subjects_json: [...(rule.required_subjects_json ?? [])],
      first_choice_subjects_json: [...(rule.first_choice_subjects_json ?? [])],
      reselect_subjects_json: [...(rule.reselect_subjects_json ?? [])],
      score_rule_summary: rule.score_rule_summary ?? null,
      parallel_rule_mode: rule.parallel_rule_mode ?? null,
      max_major_per_unit: rule.max_major_per_unit ?? undefined,
      is_parallel: rule.is_parallel,
      allow_adjustment: rule.allow_adjustment,
      support_collect_round: rule.support_collect_round,
      special_rules_json: [...(rule.special_rules_json ?? [])],
      note: rule.note ?? null,
      is_active: rule.is_active,
    });
    volunteerRuleDialogVisible.value = true;
  }

  async function submitVolunteerRule(): Promise<void> {
    if (!volunteerRuleForm.province.trim()) {
      ElMessage.warning("省份不能为空");
      return;
    }
    if (!volunteerRuleForm.exam_mode.trim()) {
      ElMessage.warning("高考模式不能为空");
      return;
    }
    if (!volunteerRuleForm.batch.trim()) {
      ElMessage.warning("批次不能为空");
      return;
    }
    if (volunteerRuleForm.total_score <= 0) {
      ElMessage.warning("总分口径必须大于 0");
      return;
    }
    if (volunteerRuleForm.volunteer_limit <= 0) {
      ElMessage.warning("志愿数上限必须大于 0");
      return;
    }
    if (volunteerRuleForm.max_major_per_unit !== undefined && volunteerRuleForm.max_major_per_unit <= 0) {
      ElMessage.warning("同单位专业上限必须大于 0");
      return;
    }

    try {
      savingVolunteerRule.value = true;
      const payload: ProvinceVolunteerRulePayload = {
        ...volunteerRuleForm,
        candidate_type: volunteerRuleForm.candidate_type.trim(),
        required_subjects_json: uniqueStrings(volunteerRuleForm.required_subjects_json),
        first_choice_subjects_json: uniqueStrings(volunteerRuleForm.first_choice_subjects_json),
        reselect_subjects_json: uniqueStrings(volunteerRuleForm.reselect_subjects_json),
        score_rule_summary: volunteerRuleForm.score_rule_summary?.trim() || null,
        parallel_rule_mode: volunteerRuleForm.parallel_rule_mode?.trim() || null,
        special_rules_json: uniqueStrings(volunteerRuleForm.special_rules_json),
        note: volunteerRuleForm.note?.trim() || null,
      };
      const path = editingVolunteerRuleId.value
        ? `/api/province-volunteer-rules/${editingVolunteerRuleId.value}`
        : "/api/province-volunteer-rules";
      const method = editingVolunteerRuleId.value ? "PUT" : "POST";
      await apiRequest(path, { method, body: JSON.stringify(payload) });
      volunteerRuleDialogVisible.value = false;
      await loadProvinceVolunteerRules();
      ElMessage.success("省份规则保存成功");
    } catch (error) {
      reportError(error);
    } finally {
      savingVolunteerRule.value = false;
    }
  }

  function handleVolunteerRuleDialogClosed(): void {
    editingVolunteerRuleId.value = null;
    Object.assign(volunteerRuleForm, createProvinceVolunteerRuleForm());
  }

  async function handleEnrollmentPlanImport(uploadFileItem: UploadFile): Promise<void> {
    if (!uploadFileItem.raw) return;
    importingEnrollmentPlans.value = true;
    try {
      enrollmentPlanImportResult.value = null;
      enrollmentPlanImportResult.value = await uploadFile<EnrollmentPlanImportResponse>(
        "/api/enrollment-plans/import",
        uploadFileItem.raw,
      );
      const tasks: Promise<void>[] = [loadEnrollmentPlans({ resetPage: true })];
      if (options.reloadCollegeDirectory) tasks.push(options.reloadCollegeDirectory());
      if (options.reloadMajorDirectory) tasks.push(options.reloadMajorDirectory());
      await Promise.all(tasks);
      ElMessage({
        type: enrollmentPlanImportResult.value.failed_rows ? "warning" : "success",
        message: enrollmentPlanImportResult.value.message,
      });
    } catch (error) {
      reportError(error);
    } finally {
      importingEnrollmentPlans.value = false;
    }
  }

  return {
    batchOptions,
    bootstrapProvinceScoreTransformRules,
    bootstrapSpecialTypeRules,
    bootstrapSubjectRequirementDicts,
    bootstrapProvinceVolunteerRules,
    bootstrappingScoreTransformRules,
    bootstrappingSpecialTypeRules,
    bootstrappingSubjectRequirementDicts,
    bootstrappingVolunteerRules,
    downloadEnrollmentPlanTemplate,
    enrollmentPlanFilters,
    enrollmentPlanImportResult,
    enrollmentPlanPagination,
    enrollmentPlansLoadError,
    enrollmentPlans,
    examModeOptions,
    gaokaoCandidateTypeOptions,
    handleEnrollmentPlanImport,
    handleEnrollmentPlanPageChange,
    handleEnrollmentPlanPageSizeChange,
    handleVolunteerRuleDialogClosed,
    importingEnrollmentPlans,
    loadEnrollmentPlans,
    loadProvinceVolunteerRules,
    loadProvinceScoreTransformRules,
    loadSpecialTypeRules,
    loadSubjectRequirementDicts,
    loadingEnrollmentPlans,
    loadingScoreTransformRules,
    loadingSpecialTypeRules,
    loadingSubjectRequirementDicts,
    loadingVolunteerRules,
    openCreateVolunteerRule,
    openEditVolunteerRule,
    planYearOptions,
    provinceOptions,
    provinceVolunteerRules,
    provinceScoreTransformRules,
    recommendationStudentTypeOptions,
    resetEnrollmentPlanFilters,
    resetScoreTransformRuleFilters,
    resetSpecialTypeRuleFilters,
    resetSubjectRequirementDictFilters,
    resetVolunteerRuleFilters,
    ruleYearOptions,
    savingVolunteerRule,
    parallelRuleModeOptions,
    scoreTransformRulesLoadError,
    specialRuleOptions,
    scoreTransformRuleFilters,
    scoreTransformRuleYearOptions,
    specialTypeRulesLoadError,
    specialTypeRuleFilters,
    specialTypeRuleYearOptions,
    specialTypeRules,
    subjectRequirementDictsLoadError,
    subjectRequirementDictFilters,
    subjectRequirementDictYearOptions,
    subjectRequirementDicts,
    subjectRequirementModeOptions,
    submitVolunteerRule,
    summaryCards,
    volunteerRuleDialogTitle,
    volunteerRuleDialogVisible,
    volunteerRuleFilters,
    volunteerRuleForm,
    volunteerRulesLoadError,
    volunteerUnitTypeOptions,
  };
}
