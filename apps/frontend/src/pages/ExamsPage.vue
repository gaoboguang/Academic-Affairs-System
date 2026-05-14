<template>
  <AppPage
    title="考试成绩中心"
    eyebrow="考试治理 / 成绩中心"
    description="集中维护考试、科目、成绩导入和快照重建；先完成考试配置，再进入分析中心查看口径与结果。"
    :meta="examPageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button @click="downloadTemplate">成绩模板下载</el-button>
        <el-button type="primary" @click="openCreate">新建考试</el-button>
      </div>
    </template>

    <el-alert
      v-for="item in scoreReadinessMessages"
      :key="item"
      class="page-alert"
      type="warning"
      show-icon
      :closable="false"
      :title="item"
    />

    <AppStatGrid :items="examStatCards" :columns="4" />

    <AppFilterBar
      title="全局筛选"
      description="按考试名称和学期快速定位，查询结果会同步到下方考试列表。"
      sticky
    >
      <div class="filter-grid">
        <el-input v-model="filters.name" placeholder="按考试名称筛选" />
        <el-select v-model="filters.semester_id" clearable placeholder="选择学期">
          <el-option
            v-for="semester in referenceStore.semesters"
            :key="semester.id"
            :label="`${semester.academic_year_name ?? ''} ${semester.name}`"
            :value="semester.id"
          />
        </el-select>
      </div>
      <template #actions>
        <el-button type="primary" @click="loadExams">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </template>
    </AppFilterBar>

    <AppTableShell
      title="考试列表"
      description="每场考试的科目配置、成绩导入和快照重建都从这里进入。"
    >
      <el-table :data="exams.items" stripe>
        <el-table-column label="考试名称" prop="name" min-width="180" />
        <el-table-column label="类型" prop="exam_type" width="100" />
        <el-table-column label="考试日期" prop="exam_date" width="120" />
        <el-table-column label="学期" prop="semester_name" min-width="180" />
        <el-table-column label="年级范围" min-width="140">
          <template #default="{ row }">
            {{ (row.grade_scope_names ?? []).join(" / ") || "未设置" }}
          </template>
        </el-table-column>
        <el-table-column label="科目数" prop="subject_count" width="90" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="examStatusType(row.status)" effect="light">
              {{ formatExamStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="240" fixed="right">
          <template #default="{ row }">
            <div class="action-row compact-actions">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="primary" @click="openSubjects(row)">科目配置</el-button>
              <el-button link type="primary" @click="openImport(row)">导入成绩</el-button>
              <el-button link type="primary" @click="rebuild(row.id)">重建</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </AppTableShell>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="720px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleExamDialogClosed"
    >
      <el-form label-width="110px">
        <div class="form-grid">
          <el-form-item label="考试名称">
            <el-input v-model="examForm.name" />
          </el-form-item>
          <el-form-item label="考试类型">
            <el-input v-model="examForm.exam_type" />
          </el-form-item>
          <el-form-item label="考试日期">
            <el-date-picker
              v-model="examForm.exam_date"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="学期">
            <el-select v-model="examForm.semester_id" filterable style="width: 100%">
              <el-option
                v-for="semester in referenceStore.semesters"
                :key="semester.id"
                :label="`${semester.academic_year_name ?? ''} ${semester.name}`"
                :value="semester.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="examForm.status" style="width: 100%">
              <el-option label="草稿" value="draft" />
              <el-option label="已发布" value="published" />
              <el-option label="已归档" value="archived" />
            </el-select>
          </el-form-item>
          <el-form-item label="趋势分析">
            <el-switch v-model="examForm.is_trend_enabled" />
          </el-form-item>
          <el-form-item label="年级范围" class="span-two">
            <el-select
              v-model="examForm.grade_scope_json"
              multiple
              collapse-tags
              filterable
              style="width: 100%"
            >
              <el-option
                v-for="grade in referenceStore.grades"
                :key="grade.id"
                :label="grade.name"
                :value="grade.id"
              />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="备注">
          <el-input v-model="examForm.note" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingExam" @click="submitExam">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="subjectsDialogVisible"
      :title="subjectsDialogTitle"
      width="920px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleSubjectsDialogClosed"
    >
      <div class="assignment-toolbar">
        <div>
          <strong>勾选本次考试涉及的科目</strong>
          <p class="subject-selector-note">
            语文 / 数学 / 英语 / 日语 / 俄语默认 150 分，政治 / 历史 / 地理 / 物理 / 化学 / 生物默认 100 分；下方仍可逐科改分。
          </p>
        </div>
        <div class="action-row compact-actions">
          <el-button @click="selectStandardSubjects">常规九科</el-button>
          <el-button @click="clearSelectedSubjects">清空</el-button>
        </div>
      </div>
      <el-checkbox-group
        class="subject-selector-group"
        :model-value="selectedSubjectIds"
        @change="handleSubjectSelectionChange"
      >
        <el-checkbox-button
          v-for="subject in subjectOptions"
          :key="subject.id"
          :label="subject.id"
        >
          {{ formatSubjectOptionLabel(subject) }}
        </el-checkbox-button>
      </el-checkbox-group>
      <div v-if="!subjectRows.length" class="subject-empty-state">
        请先勾选本次考试涉及的科目，再在下方调整满分、分数线和是否计入总分。
      </div>
      <el-table v-else :data="subjectRows" stripe>
        <el-table-column label="学科" min-width="160">
          <template #default="{ row }">
            <div class="subject-cell">
              <strong>{{ resolveSubjectName(row.subject_id) }}</strong>
              <span>默认 {{ resolveSubjectDefaultScore(row.subject_id) }} 分</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="满分" width="110">
          <template #default="{ row }">
            <el-input-number v-model="row.full_score" :min="0" :max="300" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="优秀线" width="110">
          <template #default="{ row }">
            <el-input-number v-model="row.excellent_line" :min="0" :max="300" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="及格线" width="110">
          <template #default="{ row }">
            <el-input-number v-model="row.pass_line" :min="0" :max="300" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="总分" width="90">
          <template #default="{ row }">
            <el-switch v-model="row.is_in_total" />
          </template>
        </el-table-column>
        <el-table-column label="排序" width="100">
          <template #default="{ row }">
            <el-input-number v-model="row.sort_order" :min="0" :max="99" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeSelectedSubject(row.subject_id)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="subjectsDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingSubjects" @click="saveSubjects">保存科目配置</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="importDialogVisible"
      :title="importDialogTitle"
      width="900px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleImportDialogClosed"
    >
      <el-steps class="score-import-steps" :active="scoreImportStepActive" finish-status="success" simple>
        <el-step title="上传识别" />
        <el-step title="确认映射" />
        <el-step title="导入结果" />
      </el-steps>

      <div class="action-row import-row">
        <el-select v-model="importStrategy" style="width: 180px">
          <el-option label="覆盖已有成绩" value="overwrite" />
          <el-option label="跳过已有成绩" value="skip_existing" />
        </el-select>
        <el-select
          v-model="selectedProfileId"
          clearable
          filterable
          placeholder="选择平台模板"
          style="width: 220px"
        >
          <el-option
            v-for="profile in scoreProfiles"
            :key="profile.id"
            :label="profile.name"
            :value="profile.id"
          />
        </el-select>
        <el-upload :show-file-list="false" :auto-upload="false" :on-change="handleScorePreview">
          <el-button type="primary" :loading="previewLoading">上传并识别</el-button>
        </el-upload>
        <el-upload :show-file-list="false" :auto-upload="false" :on-change="handleStandardImport">
          <el-button plain :loading="importingScores">按统一模板导入</el-button>
        </el-upload>
        <el-button @click="reloadBatches">刷新批次</el-button>
      </div>
      <el-alert
        class="import-tip"
        type="info"
        show-icon
        :closable="false"
        title="推荐先用“上传并识别”：系统会识别宽表/长表和科目列，确认映射后再写入成绩；统一模板仍可直接导入。"
      />

      <section v-if="scorePreview && editableScoreMapping" class="score-mapping-panel">
        <div class="section-head">
          <div>
            <h3>识别结果</h3>
            <p>
              {{ scorePreview.sheet_name }} / 第 {{ scorePreview.header_row }} 行表头 /
              {{ scorePreview.layout_type === "wide" ? "宽表" : "长表" }} /
              置信度 {{ Math.round(scorePreview.confidence * 100) }}%
            </p>
          </div>
          <el-tag :type="scorePreview.import_ready ? 'success' : 'warning'" effect="light">
            {{ scorePreview.import_ready ? "可导入" : "需复核" }}
          </el-tag>
        </div>
        <el-alert
          v-for="message in scorePreview.messages"
          :key="message"
          class="mapping-message"
          type="warning"
          show-icon
          :closable="false"
          :title="message"
        />

        <el-form label-width="110px" class="mapping-form">
          <div class="form-grid">
            <el-form-item label="板式">
              <el-select v-model="editableScoreMapping.layout_type" style="width: 100%">
                <el-option label="宽表：一行一个学生，多科成绩列" value="wide" />
                <el-option label="长表：一行一个学生一科" value="long" />
              </el-select>
            </el-form-item>
            <el-form-item label="保存模板">
              <div class="profile-save-row">
                <el-switch v-model="saveScoreProfile" />
                <el-input
                  v-model="scoreProfileName"
                  :disabled="!saveScoreProfile"
                  placeholder="如：七天网络成绩导出"
                />
              </div>
            </el-form-item>
            <el-form-item
              v-for="field in SCORE_IMPORT_FIELD_OPTIONS"
              :key="field.value"
              :label="field.label"
            >
              <el-select
                :model-value="editableScoreMapping.field_mapping[field.value]"
                clearable
                filterable
                placeholder="选择列"
                style="width: 100%"
                @change="updateScoreFieldMapping(field.value, $event)"
              >
                <el-option
                  v-for="header in scoreImportHeaders"
                  :key="header"
                  :label="header"
                  :value="header"
                />
              </el-select>
            </el-form-item>
          </div>
        </el-form>

        <section v-if="editableScoreMapping.layout_type === 'wide'" class="subject-map-section">
          <div class="section-head compact-section-head">
            <div>
              <h4>宽表科目列</h4>
              <p>总分、名次等统计列可以留空，系统会在导入后重新计算。</p>
            </div>
          </div>
          <el-table :data="scoreSubjectColumns" size="small" stripe>
            <el-table-column label="来源列" min-width="180">
              <template #default="{ row }">{{ row }}</template>
            </el-table-column>
            <el-table-column label="对应科目" min-width="180">
              <template #default="{ row }">
                <el-select
                  :model-value="editableScoreMapping.subject_mapping[row]"
                  clearable
                  filterable
                  placeholder="忽略或选择科目"
                  style="width: 100%"
                  @change="updateScoreSubjectMapping(row, $event)"
                >
                  <el-option
                    v-for="subject in subjectOptions"
                    :key="subject.id"
                    :label="subject.name"
                    :value="subject.name"
                  />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="成绩口径" width="130">
              <template #default="{ row }">
                <el-select
                  :model-value="editableScoreMapping.subject_score_types[row] ?? 'original'"
                  :disabled="!editableScoreMapping.subject_mapping[row]"
                  style="width: 100%"
                  @change="updateScoreSubjectScoreType(row, $event)"
                >
                  <el-option label="原始分" value="original" />
                  <el-option label="赋分" value="converted" />
                </el-select>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <el-alert
          class="import-tip"
          type="info"
          show-icon
          :closable="false"
          :title="scoreImportReadinessText"
        />
        <el-table :data="scorePreview.normalized_preview" size="small" stripe class="preview-table">
          <el-table-column
            v-for="header in ['学号', '姓名', '班级', '科目', '分数', '成绩口径', '缺考标记']"
            :key="header"
            :label="header"
            :prop="header"
            min-width="100"
          />
        </el-table>
        <div class="action-row import-row">
          <el-button
            type="primary"
            :disabled="!pendingImportFile || !editableScoreMapping"
            :loading="importingScores"
            @click="executeSmartImport"
          >
            确认并导入
          </el-button>
        </div>
      </section>

      <ImportFeedbackPanel :result="importResult" />
      <AppTableShell class="score-batch-shell" title="最近导入批次">
        <el-table :data="scoreBatches" stripe>
          <el-table-column label="批次 ID" prop="id" width="90" />
          <el-table-column label="来源文件" prop="source_filename" min-width="180" />
          <el-table-column label="导入时间" prop="import_time" min-width="160" />
          <el-table-column label="成功" prop="success_rows" width="90" />
          <el-table-column label="失败" prop="failed_rows" width="90" />
          <el-table-column label="识别方式" min-width="140">
            <template #default="{ row }">
              {{ formatScoreBatchImportMode(row) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="scoreBatchStatusType(row.status)" effect="light">
                {{ formatScoreBatchStatus(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </AppTableShell>
    </el-dialog>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import type { UploadFile } from "element-plus";
import type { components as ExamApiSchemas } from "../types/api.generated";

type ExamPayloadSchema = ExamApiSchemas["schemas"]["ExamPayload"];

import { apiRequest, openFile, uploadFile } from "../api/client";
import { api } from "../api/typedClient";
import ImportFeedbackPanel from "../components/common/ImportFeedbackPanel.vue";
import {
  buildExamSubjectOptions,
  getExamSubjectDefaultFullScore,
  getStandardExamSubjectIds,
  syncExamSubjectRows,
  type ExamSubjectDraftRow,
  type ExamSubjectOption,
} from "../components/exams/examSubjectConfig";
import {
  SCORE_IMPORT_FIELD_OPTIONS,
  buildScoreImportMappingPayload,
  buildScoreImportReadinessText,
  cloneScoreImportMapping,
  getScoreImportHeaders,
  getUnassignedScoreColumns,
  type ScoreImportMapping,
  type ScoreImportPreview,
  type ScoreImportProfile,
} from "../components/exams/scoreImportMapping";
import {
  AppFilterBar,
  AppPage,
  AppStatGrid,
  AppTableShell,
  type PageMetaItem,
  type StatCardItem,
} from "../components/ui";
import { useReferenceStore } from "../stores/reference";
import { formatImportStatus, importStatusTagType, type ImportFeedbackResult } from "../utils/importFeedback";
import { buildScoreReadinessMessages } from "../utils/scoreReadiness";

interface ExamItem {
  id: number;
  name: string;
  exam_type: string;
  exam_date: string;
  semester_id: number;
  semester_name?: string;
  grade_scope_json: number[];
  grade_scope_names?: string[];
  is_trend_enabled: boolean;
  status: string;
  note?: string;
  subject_count: number;
}

interface ExamListResponse {
  items: ExamItem[];
  total: number;
  page: number;
  page_size: number;
}

interface ExamSubjectRow {
  subject_id: number | null;
  subject_name?: string | null;
  full_score: number;
  excellent_line: number | null;
  pass_line: number | null;
  is_in_total: boolean;
  sort_order: number;
  is_active: boolean;
}

interface ScoreBatch {
  id: number;
  source_filename?: string;
  import_time: string;
  success_rows: number;
  failed_rows: number;
  status: string;
  profile_id?: number | null;
  detection_summary?: Record<string, unknown> | null;
}

const referenceStore = useReferenceStore();
const dialogVisible = ref(false);
const subjectsDialogVisible = ref(false);
const importDialogVisible = ref(false);
const editingExamId = ref<number | null>(null);
const subjectsExamId = ref<number | null>(null);
const importExamId = ref<number | null>(null);
const savingExam = ref(false);
const savingSubjects = ref(false);
const previewLoading = ref(false);
const importingScores = ref(false);
const importStrategy = ref("overwrite");
const importResult = ref<(ImportFeedbackResult & { batch_id: number }) | null>(null);
const scoreRecordTotal = ref(0);
const scoreProfiles = ref<ScoreImportProfile[]>([]);
const selectedProfileId = ref<number | null>(null);
const pendingImportFile = ref<File | null>(null);
const scorePreview = ref<ScoreImportPreview | null>(null);
const editableScoreMapping = ref<ScoreImportMapping | null>(null);
const saveScoreProfile = ref(false);
const scoreProfileName = ref("");

const filters = reactive({
  name: "",
  semester_id: undefined as number | undefined,
});

const exams = reactive<ExamListResponse>({
  items: [],
  total: 0,
  page: 1,
  page_size: 100,
});

const examForm = reactive({
  name: "",
  exam_type: "月考",
  exam_date: "",
  semester_id: null as number | null,
  grade_scope_json: [] as number[],
  is_trend_enabled: true,
  status: "draft",
  note: "",
  is_active: true,
});

const subjectRows = ref<ExamSubjectDraftRow[]>([]);
const scoreBatches = ref<ScoreBatch[]>([]);
const subjectOptions = computed(() => buildExamSubjectOptions(referenceStore.subjects));
const scoreImportHeaders = computed(() => getScoreImportHeaders(scorePreview.value));
const scoreSubjectColumns = computed(() =>
  editableScoreMapping.value ? getUnassignedScoreColumns(scorePreview.value, editableScoreMapping.value) : [],
);
const selectedSubjectIds = computed(() =>
  subjectRows.value
    .map((item) => item.subject_id)
    .filter((value): value is number => typeof value === "number"),
);

const dialogTitle = computed(() => (editingExamId.value ? "编辑考试" : "新建考试"));
const subjectsDialogTitle = computed(() => {
  const current = exams.items.find((item) => item.id === subjectsExamId.value);
  return current ? `科目配置 - ${current.name}` : "科目配置";
});
const importDialogTitle = computed(() => {
  const current = exams.items.find((item) => item.id === importExamId.value);
  return current ? `导入成绩 - ${current.name}` : "导入成绩";
});
const scoreReadinessMessages = computed(() =>
  buildScoreReadinessMessages({
    examCount: exams.items.length,
    scoreRecordTotal: scoreRecordTotal.value,
  }),
);
const publishedExamCount = computed(() => exams.items.filter((item) => item.status === "published").length);
const configuredSubjectCount = computed(() =>
  exams.items.reduce((total, item) => total + (item.subject_count > 0 ? 1 : 0), 0),
);
const examPageMeta = computed<PageMetaItem[]>(() => [
  { label: "考试", value: exams.total },
  { label: "已发布", value: publishedExamCount.value },
  { label: "成绩记录", value: scoreRecordTotal.value },
]);
const examStatCards = computed<StatCardItem[]>(() => [
  {
    label: "考试总数",
    value: exams.total,
    help: "当前考试成绩中心维护的考试数量。",
    tone: "primary",
  },
  {
    label: "已发布考试",
    value: publishedExamCount.value,
    help: "可用于正式分析与报表输出的考试。",
    tone: "success",
  },
  {
    label: "已配科目考试",
    value: configuredSubjectCount.value,
    help: "至少配置过一个考试科目的考试。",
    tone: configuredSubjectCount.value === exams.items.length && exams.items.length ? "success" : "warning",
  },
  {
    label: "成绩记录",
    value: scoreRecordTotal.value,
    help: "系统当前已保存的成绩明细记录。",
    tone: scoreRecordTotal.value ? "info" : "neutral",
  },
]);
const scoreImportStepActive = computed(() => {
  if (importResult.value) return 2;
  if (scorePreview.value) return 1;
  return 0;
});
const scoreImportReadinessText = computed(() =>
  buildScoreImportReadinessText(scorePreview.value, editableScoreMapping.value),
);

function formatExamStatus(status: string): string {
  const mapping: Record<string, string> = {
    draft: "草稿",
    published: "已发布",
    archived: "已归档",
  };
  return mapping[status] ?? status;
}

function examStatusType(status: string): "info" | "success" | "warning" {
  if (status === "published") return "success";
  if (status === "archived") return "warning";
  return "info";
}

function formatScoreBatchStatus(status: string): string {
  return formatImportStatus(status);
}

function formatScoreBatchImportMode(row: ScoreBatch): string {
  const layoutType = row.detection_summary?.layout_type;
  if (layoutType === "standard") return "统一模板";
  if (layoutType === "wide") return "智能宽表";
  if (layoutType === "long") return "智能长表";
  return "-";
}

function scoreBatchStatusType(status: string): "info" | "success" | "warning" | "danger" {
  return importStatusTagType(status);
}

function resetExamForm(): void {
  Object.assign(examForm, {
    name: "",
    exam_type: "月考",
    exam_date: "",
    semester_id: null,
    grade_scope_json: [],
    is_trend_enabled: true,
    status: "draft",
    note: "",
    is_active: true,
  });
}

async function loadExams(): Promise<void> {
  try {
    const payload = await api.get("/api/exams", {
      query: {
        page: 1,
        page_size: 100,
        name: filters.name || null,
        semester_id: filters.semester_id ?? null,
      },
    });
    Object.assign(exams, payload);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadScoreReadiness(): Promise<void> {
  try {
    const payload = await apiRequest<{ score_record_total?: number }>("/api/dashboard/summary");
    scoreRecordTotal.value = payload.score_record_total ?? 0;
  } catch {
    scoreRecordTotal.value = 0;
  }
}

function resetFilters(): void {
  filters.name = "";
  filters.semester_id = undefined;
  void loadExams();
}

function downloadTemplate(): void {
  openFile(`/api/system/files?path=${encodeURIComponent("data/templates/exam_scores_import_template.xlsx")}`);
}

function openCreate(): void {
  if (!referenceStore.semesters.length) {
    ElMessage.warning("请先维护学期数据");
    return;
  }
  editingExamId.value = null;
  resetExamForm();
  dialogVisible.value = true;
}

async function openEdit(row: ExamItem): Promise<void> {
  try {
    const detail = await api.get("/api/exams/{exam_id}", {
      path: { exam_id: row.id },
    });
    editingExamId.value = row.id;
    resetExamForm();
    Object.assign(examForm, detail);
    dialogVisible.value = true;
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function submitExam(): Promise<void> {
  if (!examForm.name.trim() || !examForm.exam_date || !examForm.semester_id) {
    ElMessage.warning("考试名称、考试日期和学期不能为空");
    return;
  }
  try {
    savingExam.value = true;
    if (editingExamId.value) {
      await api.put("/api/exams/{exam_id}", {
        path: { exam_id: editingExamId.value },
        body: examForm as unknown as ExamPayloadSchema,
      });
    } else {
      await api.post("/api/exams", { body: examForm as unknown as ExamPayloadSchema });
    }
    ElMessage.success("考试保存成功");
    dialogVisible.value = false;
    await loadExams();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingExam.value = false;
  }
}

function formatSubjectOptionLabel(subject: ExamSubjectOption): string {
  return `${subject.name}（${subject.defaultFullScore} 分）`;
}

function resolveSubjectName(subjectId: number | null): string {
  return subjectOptions.value.find((item) => item.id === subjectId)?.name ?? "未识别学科";
}

function resolveSubjectDefaultScore(subjectId: number | null): number {
  const subject = subjectOptions.value.find((item) => item.id === subjectId);
  return subject?.defaultFullScore ?? getExamSubjectDefaultFullScore({ code: "", name: "" });
}

function handleSubjectSelectionChange(values: Array<string | number>): void {
  const selectedIds = values
    .map((item) => Number(item))
    .filter((item) => Number.isInteger(item) && item > 0);
  subjectRows.value = syncExamSubjectRows(selectedIds, referenceStore.subjects, subjectRows.value);
}

function selectStandardSubjects(): void {
  handleSubjectSelectionChange(getStandardExamSubjectIds(referenceStore.subjects));
}

function clearSelectedSubjects(): void {
  subjectRows.value = [];
}

function removeSelectedSubject(subjectId: number | null): void {
  if (subjectId == null) {
    return;
  }
  handleSubjectSelectionChange(selectedSubjectIds.value.filter((item) => item !== subjectId));
}

async function openSubjects(row: ExamItem): Promise<void> {
  try {
    subjectsExamId.value = row.id;
    const items = await apiRequest<ExamSubjectRow[]>(`/api/exams/${row.id}/subjects`);
    subjectRows.value = items.map((item, index) => ({
      subject_id: item.subject_id,
      full_score: item.full_score,
      excellent_line: item.excellent_line,
      pass_line: item.pass_line,
      is_in_total: item.is_in_total,
      sort_order: item.sort_order ?? index + 1,
      is_active: true,
    }));
    subjectsDialogVisible.value = true;
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function saveSubjects(): Promise<void> {
  if (!subjectsExamId.value) return;
  if (!subjectRows.value.length) {
    ElMessage.warning("请至少配置一个考试科目");
    return;
  }
  if (subjectRows.value.some((item) => !item.subject_id)) {
    ElMessage.warning("考试科目不能为空");
    return;
  }
  const subjectIds = subjectRows.value.map((item) => item.subject_id);
  if (new Set(subjectIds).size !== subjectIds.length) {
    ElMessage.warning("考试科目不能重复");
    return;
  }
  try {
    savingSubjects.value = true;
    await apiRequest(`/api/exams/${subjectsExamId.value}/subjects`, {
      method: "POST",
      body: JSON.stringify(subjectRows.value),
    });
    ElMessage.success("考试科目保存成功");
    subjectsDialogVisible.value = false;
    await loadExams();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingSubjects.value = false;
  }
}

async function openImport(row: ExamItem): Promise<void> {
  importExamId.value = row.id;
  importResult.value = null;
  scoreBatches.value = [];
  pendingImportFile.value = null;
  scorePreview.value = null;
  editableScoreMapping.value = null;
  saveScoreProfile.value = false;
  scoreProfileName.value = "";
  importDialogVisible.value = true;
  await Promise.all([reloadBatches(), loadScoreProfiles()]);
}

async function loadScoreProfiles(): Promise<void> {
  try {
    scoreProfiles.value = await apiRequest<ScoreImportProfile[]>("/api/exams/score-import-profiles");
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function handleScorePreview(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw || !importExamId.value) return;
  pendingImportFile.value = uploadFileItem.raw;
  importResult.value = null;
  try {
    previewLoading.value = true;
    const fields: Record<string, string> = {};
    if (selectedProfileId.value) fields.profile_id = String(selectedProfileId.value);
    scorePreview.value = await uploadFile<ScoreImportPreview>(
      `/api/exams/${importExamId.value}/scores/import/preview`,
      uploadFileItem.raw,
      fields,
    );
    editableScoreMapping.value = cloneScoreImportMapping(scorePreview.value.mapping);
    if (selectedProfileId.value) {
      const profile = scoreProfiles.value.find((item) => item.id === selectedProfileId.value);
      scoreProfileName.value = profile?.name ?? "";
    }
    ElMessage({
      type: scorePreview.value.import_ready ? "success" : "warning",
      message: scorePreview.value.import_ready ? "成绩单识别完成，请确认映射后导入" : "成绩单已识别，请先补齐必要字段",
    });
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    previewLoading.value = false;
  }
}

async function handleStandardImport(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw || !importExamId.value) return;
  try {
    importingScores.value = true;
    importResult.value = await uploadFile<ImportFeedbackResult & { batch_id: number }>(
      `/api/exams/${importExamId.value}/scores/import`,
      uploadFileItem.raw,
      {
        strategy: importStrategy.value,
        rebuild: "true",
      },
    );
    ElMessage({
      type: importResult.value.failed_rows ? "warning" : "success",
      message: importResult.value.message,
    });
    await reloadBatches();
    await loadScoreReadiness();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    importingScores.value = false;
  }
}

async function executeSmartImport(): Promise<void> {
  if (!pendingImportFile.value || !importExamId.value || !editableScoreMapping.value) {
    ElMessage.warning("请先上传成绩文件并完成识别");
    return;
  }
  try {
    importingScores.value = true;
    const fields: Record<string, string> = {
      strategy: importStrategy.value,
      rebuild: "true",
      mapping_json: buildScoreImportMappingPayload(editableScoreMapping.value),
    };
    if (selectedProfileId.value) fields.profile_id = String(selectedProfileId.value);
    if (saveScoreProfile.value && scoreProfileName.value.trim()) {
      fields.save_profile_name = scoreProfileName.value.trim();
    }
    importResult.value = await uploadFile<ImportFeedbackResult & { batch_id: number }>(
      `/api/exams/${importExamId.value}/scores/import`,
      pendingImportFile.value,
      fields,
    );
    ElMessage({
      type: importResult.value.failed_rows ? "warning" : "success",
      message: importResult.value.message,
    });
    await Promise.all([reloadBatches(), loadScoreReadiness(), loadScoreProfiles()]);
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    importingScores.value = false;
  }
}

function updateScoreFieldMapping(role: string, header: string | number | boolean | undefined): void {
  if (!editableScoreMapping.value) return;
  const next = String(header ?? "");
  if (!next) {
    delete editableScoreMapping.value.field_mapping[role];
    return;
  }
  editableScoreMapping.value.field_mapping[role] = next;
  delete editableScoreMapping.value.subject_mapping[next];
}

function updateScoreSubjectMapping(header: string, subjectName: string | number | boolean | undefined): void {
  if (!editableScoreMapping.value) return;
  const next = String(subjectName ?? "");
  if (!next) {
    delete editableScoreMapping.value.subject_mapping[header];
    delete editableScoreMapping.value.subject_score_types[header];
    return;
  }
  editableScoreMapping.value.subject_mapping[header] = next;
  editableScoreMapping.value.subject_score_types[header] =
    editableScoreMapping.value.subject_score_types[header] ?? "original";
}

function updateScoreSubjectScoreType(
  header: string,
  scoreValueType: string | number | boolean | undefined,
): void {
  if (!editableScoreMapping.value) return;
  const next = String(scoreValueType ?? "");
  if (next === "converted" || next === "original" || next === "display") {
    editableScoreMapping.value.subject_score_types[header] = next;
  }
}

async function reloadBatches(): Promise<void> {
  if (!importExamId.value) return;
  try {
    scoreBatches.value = await apiRequest<ScoreBatch[]>(`/api/exams/${importExamId.value}/score-batches`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function rebuild(examId: number): Promise<void> {
  try {
    const payload = await apiRequest<{ message: string }>(`/api/exams/${examId}/rebuild`, {
      method: "POST",
    });
    ElMessage.success(payload.message);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function handleExamDialogClosed(): void {
  editingExamId.value = null;
  resetExamForm();
}

function handleSubjectsDialogClosed(): void {
  subjectsExamId.value = null;
  subjectRows.value = [];
}

function handleImportDialogClosed(): void {
  importExamId.value = null;
  importResult.value = null;
  scoreBatches.value = [];
  selectedProfileId.value = null;
  pendingImportFile.value = null;
  scorePreview.value = null;
  editableScoreMapping.value = null;
  saveScoreProfile.value = false;
  scoreProfileName.value = "";
}

onMounted(async () => {
  await referenceStore.loadCore();
  await Promise.all([loadExams(), loadScoreReadiness()]);
});
</script>

<style scoped>
.page-alert {
  margin-top: -4px;
}

.import-tip {
  margin-top: 12px;
}

.score-import-steps {
  margin-bottom: 14px;
}

.score-batch-shell {
  margin-top: 16px;
}

.score-mapping-panel {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid rgba(123, 141, 158, 0.24);
  border-radius: 8px;
  background: rgba(248, 251, 253, 0.76);
}

.mapping-message {
  margin-top: 8px;
}

.mapping-form {
  margin-top: 14px;
}

.profile-save-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 10px;
  width: 100%;
  align-items: center;
}

.subject-map-section {
  margin-top: 10px;
}

.compact-section-head {
  margin-bottom: 8px;
}

.compact-section-head h4 {
  margin: 0;
  color: #22384c;
}

.compact-section-head p {
  margin: 4px 0 0;
  color: #6d8194;
}

.preview-table {
  margin-top: 12px;
}

.panel-block {
  padding: 18px;
}

.compact-actions {
  gap: 4px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.span-two {
  grid-column: span 2;
}

.assignment-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.subject-selector-note {
  margin: 6px 0 0;
  color: #6d8194;
  line-height: 1.6;
}

.subject-selector-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.subject-empty-state {
  padding: 16px 18px;
  margin-bottom: 14px;
  border: 1px dashed rgba(123, 141, 158, 0.35);
  border-radius: 14px;
  color: #6d8194;
  background: rgba(245, 249, 252, 0.82);
  line-height: 1.7;
}

.subject-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subject-cell strong {
  color: #22384c;
}

.subject-cell span {
  color: #6d8194;
  font-size: 12px;
}

.import-row {
  margin-top: 14px;
  align-items: center;
}

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .span-two {
    grid-column: span 1;
  }

  .assignment-toolbar {
    flex-direction: column;
  }
}
</style>
