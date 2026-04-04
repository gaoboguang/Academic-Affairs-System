<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">导出中心 / 报表工作流</div>
        <h2 class="page-title">报表中心</h2>
        <p class="page-subtitle">
          基于现有考试分析、工作量结果和成长档案生成 Excel 报表，并保留导出记录与参数。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>报表类型</strong>{{ reportTypeOptions.length }}</span>
          <span class="page-chip"><strong>当前类型</strong>{{ currentReportTypeLabel }}</span>
          <span class="page-chip"><strong>导出记录</strong>{{ exportRecords.length }}</span>
          <span class="page-chip"><strong>推荐方案</strong>{{ recommendationOptions.length }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="loadOptions">刷新选项</el-button>
        <el-button type="primary" plain @click="loadExportRecords">刷新记录</el-button>
      </div>
    </header>

    <section class="overview-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">导出流</div>
        <h3>{{ currentReportTypeLabel }}</h3>
        <p>先确定报表类型，再补齐考试、学生、教师、学期或推荐方案等依赖参数，最后统一从导出记录回看结果。</p>
      </article>
      <article v-for="item in overviewCards" :key="item.label" class="soft-card overview-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head compact">
        <div>
          <h3>报表参数</h3>
          <p>不同报表类型会动态暴露所需参数，避免在一个大表单里混杂无关字段。</p>
        </div>
      </div>
      <div class="filter-grid">
        <el-select v-model="form.report_type" placeholder="报表类型">
          <el-option
            v-for="item in reportTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-select v-if="requiresExam" v-model="form.exam_id" filterable placeholder="考试">
          <el-option
            v-for="exam in examOptions"
            :key="exam.id"
            :label="exam.name"
            :value="exam.id"
          />
        </el-select>
        <el-select v-if="requiresStudent" v-model="form.student_id" filterable placeholder="学生">
          <el-option
            v-for="student in studentOptions"
            :key="student.id"
            :label="`${student.student_no} - ${student.name}`"
            :value="student.id"
          />
        </el-select>
        <el-select v-if="requiresScheme" v-model="form.scheme_id" filterable placeholder="推荐方案">
          <el-option
            v-for="item in recommendationOptions"
            :key="item.scheme_id"
            :label="`${item.student_name} / ${item.scheme_name}`"
            :value="item.scheme_id"
          />
        </el-select>
        <el-select v-if="requiresBatch" v-model="form.batch_id" filterable placeholder="评教批次">
          <el-option
            v-for="item in evaluationBatchOptions"
            :key="item.id"
            :label="`${item.template_name ?? '-'} / ${item.semester_name ?? '-'}`"
            :value="item.id"
          />
        </el-select>
        <el-select v-if="requiresClass" v-model="form.class_id" filterable placeholder="班级">
          <el-option
            v-for="item in referenceStore.classes"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select v-if="requiresGrade" v-model="form.grade_id" filterable placeholder="年级">
          <el-option
            v-for="item in referenceStore.grades"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select v-if="requiresTeacher" v-model="form.teacher_id" filterable placeholder="教师">
          <el-option
            v-for="teacher in teacherOptions"
            :key="teacher.id"
            :label="teacher.name"
            :value="teacher.id"
          />
        </el-select>
        <el-select v-if="requiresSemester" v-model="form.semester_id" filterable placeholder="学期">
          <el-option
            v-for="semester in referenceStore.semesters"
            :key="semester.id"
            :label="semesterLabel(semester)"
            :value="semester.id"
          />
        </el-select>
        <el-select v-if="optionalRuleVersion" v-model="form.rule_version_id" clearable filterable placeholder="规则版本，可选">
          <el-option
            v-for="rule in currentRuleOptions"
            :key="rule.id"
            :label="rule.name"
            :value="rule.id"
          />
        </el-select>
      </div>
      <div class="action-row toolbar-row">
        <el-button type="primary" :loading="exporting" @click="exportReport">生成报表</el-button>
        <el-button @click="loadExportRecords">刷新记录</el-button>
      </div>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>导出记录</h3>
          <p>记录报表类型、参数、导出时间和下载入口，方便复现。</p>
        </div>
      </div>
      <div class="table-shell">
        <el-table :data="exportRecords" stripe>
          <el-table-column label="报表名称" prop="report_name" min-width="180" />
          <el-table-column label="类型" prop="report_type" min-width="140" />
          <el-table-column label="导出参数" min-width="260">
            <template #default="{ row }">
              {{ formatParams(row.params_json) }}
            </template>
          </el-table-column>
          <el-table-column label="导出时间" prop="exported_at" min-width="170" />
          <el-table-column label="状态" prop="status" width="100" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openFile(row.download_url)">下载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-if="!exportRecords.length" description="暂无导出记录" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest, openFile } from "../api/client";
import { type OptionItem, useReferenceStore } from "../stores/reference";

interface ExamOption {
  id: number;
  name: string;
}

interface StudentOption {
  id: number;
  student_no: string;
  name: string;
}

interface TeacherOption {
  id: number;
  name: string;
}

interface RuleVersion {
  id: number;
  name: string;
}

interface RecommendationOption {
  scheme_id: number;
  scheme_name: string;
  student_id: number;
  student_name: string;
  generated_at: string;
}

interface EvaluationBatchOption {
  id: number;
  template_name?: string | null;
  semester_name?: string | null;
}

interface ExportRecord {
  id: number;
  report_type: string;
  report_name: string;
  params_json?: Record<string, unknown> | null;
  exported_at: string;
  status: string;
  download_url: string;
}

const referenceStore = useReferenceStore();
const examOptions = ref<ExamOption[]>([]);
const studentOptions = ref<StudentOption[]>([]);
const teacherOptions = ref<TeacherOption[]>([]);
const ruleVersions = ref<RuleVersion[]>([]);
const adviserRuleVersions = ref<RuleVersion[]>([]);
const recommendationOptions = ref<RecommendationOption[]>([]);
const evaluationBatchOptions = ref<EvaluationBatchOption[]>([]);
const exportRecords = ref<ExportRecord[]>([]);
const exporting = ref(false);

const reportTypeOptions = [
  { value: "student_analysis", label: "学生成绩分析单" },
  { value: "class_analysis", label: "班级成绩分析报表" },
  { value: "grade_summary", label: "年级成绩汇总表" },
  { value: "teacher_analysis", label: "教师任教分析报表" },
  { value: "teacher_workload", label: "教师课时与工作量报表" },
  { value: "growth_summary", label: "学生成长档案摘要" },
  { value: "recommendation_summary", label: "学生推荐报告" },
  { value: "evaluation_summary", label: "评教汇总报表" },
  { value: "adviser_quant_summary", label: "班主任量化报表" },
];

const form = reactive({
  report_type: "student_analysis",
  exam_id: undefined as number | undefined,
  student_id: undefined as number | undefined,
  scheme_id: undefined as number | undefined,
  batch_id: undefined as number | undefined,
  class_id: undefined as number | undefined,
  grade_id: undefined as number | undefined,
  teacher_id: undefined as number | undefined,
  semester_id: undefined as number | undefined,
  rule_version_id: undefined as number | undefined,
});

const requiresExam = computed(() =>
  ["student_analysis", "class_analysis", "grade_summary", "teacher_analysis"].includes(form.report_type),
);
const requiresStudent = computed(() =>
  ["student_analysis", "growth_summary"].includes(form.report_type),
);
const requiresClass = computed(() => form.report_type === "class_analysis");
const requiresGrade = computed(() => form.report_type === "grade_summary");
const requiresTeacher = computed(() => form.report_type === "teacher_analysis");
const requiresSemester = computed(() => ["teacher_workload", "adviser_quant_summary"].includes(form.report_type));
const optionalRuleVersion = computed(() => ["teacher_workload", "adviser_quant_summary"].includes(form.report_type));
const requiresScheme = computed(() => form.report_type === "recommendation_summary");
const requiresBatch = computed(() => form.report_type === "evaluation_summary");
const currentRuleOptions = computed(() =>
  form.report_type === "adviser_quant_summary" ? adviserRuleVersions.value : ruleVersions.value,
);
const currentReportTypeLabel = computed(
  () => reportTypeOptions.find((item) => item.value === form.report_type)?.label ?? form.report_type,
);
const overviewCards = computed(() => [
  {
    label: "考试依赖",
    value: requiresExam.value ? "需要" : "可选",
    help: "当前报表是否要求先选择考试。",
    tone: "tone-blue",
  },
  {
    label: "规则版本",
    value: currentRuleOptions.value.length,
    help: "工作量和班主任量化报表可选的规则版本数。",
    tone: "tone-amber",
  },
  {
    label: "最近导出",
    value: exportRecords.value[0]?.status ?? "暂无",
    help: "最近一次导出记录的状态。",
    tone: "tone-slate",
  },
]);

function semesterLabel(item: OptionItem): string {
  return item.academic_year_name ? `${item.academic_year_name} ${item.name}` : item.name;
}

function formatParams(value?: Record<string, unknown> | null): string {
  if (!value) return "-";
  return Object.entries(value)
    .map(([key, item]) => `${key}=${item}`)
    .join(" / ");
}

async function loadOptions(): Promise<void> {
  await referenceStore.loadCore();
  const [examPayload, studentPayload, teacherPayload, rulePayload, adviserRulePayload] = await Promise.all([
    apiRequest<{ items: ExamOption[] }>("/api/exams?page=1&page_size=100"),
    apiRequest<{ items: StudentOption[] }>("/api/students?page=1&page_size=200"),
    apiRequest<{ items: TeacherOption[] }>("/api/teachers?page=1&page_size=200"),
    apiRequest<RuleVersion[]>("/api/workload/rules"),
    apiRequest<RuleVersion[]>("/api/adviser-quant/rules"),
  ]);
  recommendationOptions.value = await apiRequest<RecommendationOption[]>("/api/recommendations/history");
  evaluationBatchOptions.value = await apiRequest<EvaluationBatchOption[]>("/api/evaluation/batches");
  examOptions.value = examPayload.items;
  studentOptions.value = studentPayload.items;
  teacherOptions.value = teacherPayload.items;
  ruleVersions.value = rulePayload;
  adviserRuleVersions.value = adviserRulePayload;
}

async function loadExportRecords(): Promise<void> {
  exportRecords.value = await apiRequest<ExportRecord[]>("/api/reports/exports");
}

async function exportReport(): Promise<void> {
  try {
    exporting.value = true;
    const payload: Record<string, unknown> = { report_type: form.report_type };
    if (form.exam_id) payload.exam_id = form.exam_id;
    if (form.student_id) payload.student_id = form.student_id;
    if (form.class_id) payload.class_id = form.class_id;
    if (form.grade_id) payload.grade_id = form.grade_id;
    if (form.teacher_id) payload.teacher_id = form.teacher_id;
    if (form.semester_id) payload.semester_id = form.semester_id;
    if (form.rule_version_id) payload.rule_version_id = form.rule_version_id;
    if (form.scheme_id) payload.scheme_id = form.scheme_id;
    if (form.batch_id) payload.batch_id = form.batch_id;
    const result = await apiRequest<ExportRecord>("/api/reports/export", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    await loadExportRecords();
    openFile(result.download_url);
    ElMessage.success("报表已生成");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    exporting.value = false;
  }
}

watch(
  () => form.scheme_id,
  (schemeId) => {
    if (!schemeId) return;
    const current = recommendationOptions.value.find((item) => item.scheme_id === schemeId);
    if (current && form.report_type === "recommendation_summary") {
      form.student_id = current.student_id;
    }
  },
);

onMounted(async () => {
  try {
    await loadOptions();
    await loadExportRecords();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
});
</script>

<style scoped>
.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) repeat(3, minmax(0, 0.75fr));
  gap: 16px;
}

.overview-panel,
.overview-card {
  padding: 24px;
}

.overview-panel {
  background:
    radial-gradient(circle at top left, rgba(180, 219, 243, 0.32), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(244, 248, 252, 0.94));
}

.overview-kicker {
  display: inline-flex;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f6c98;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.overview-panel h3 {
  margin: 14px 0 0;
  color: #1f3448;
  font-size: 28px;
  line-height: 1.25;
}

.overview-panel p {
  margin: 12px 0 0;
  color: #62788c;
  line-height: 1.7;
}

.overview-card {
  display: grid;
  align-content: end;
  gap: 10px;
}

.overview-card span {
  color: #6d8194;
  font-size: 13px;
}

.overview-card strong {
  color: #1f3245;
  font-size: 30px;
  font-weight: 760;
}

.overview-card p {
  margin: 0;
  color: #73879b;
  line-height: 1.55;
  font-size: 13px;
}

.tone-blue {
  box-shadow: inset 0 4px 0 rgba(31, 108, 152, 0.78);
}

.tone-amber {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.84);
}

.tone-slate {
  box-shadow: inset 0 4px 0 rgba(92, 111, 129, 0.74);
}

.toolbar-row {
  margin-top: 14px;
}

.section-head {
  margin-bottom: 16px;
}

.section-head h3 {
  margin: 0;
  font-size: 18px;
}

.section-head p {
  margin: 6px 0 0;
  color: #60748a;
  line-height: 1.6;
}

@media (max-width: 1180px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
