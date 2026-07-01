<template>
  <AppPage
    title="成长档案"
    eyebrow="学生中心 / 成长档案"
    description="以时间线方式维护学生成长记录，并展示批量调班生成的班级调整系统事件。"
    :meta="growthPageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button :disabled="!selectedStudentId" :loading="recordsLoading" @click="loadRecords">刷新时间线</el-button>
        <el-button :disabled="!selectedStudentId" @click="exportSummary">导出档案摘要</el-button>
        <el-button :disabled="!selectedStudentId" @click="openPrintPreview">打印预览</el-button>
        <el-button type="primary" :disabled="!selectedStudentId" @click="openCreateDialog">新增记录</el-button>
      </div>
    </template>

    <AppStatGrid :items="overviewCards" :columns="3" />

    <el-alert
      v-if="studentsLoadError"
      class="growth-page-alert"
      type="error"
      :title="studentsLoadError"
      show-icon
      :closable="false"
    >
      <template #default>
        <el-button size="small" :loading="studentsLoading" @click="loadStudentsAndRecords">重新加载学生</el-button>
      </template>
    </el-alert>

    <el-alert
      v-if="recordsLoadError"
      class="growth-page-alert"
      type="error"
      :title="recordsLoadError"
      show-icon
      :closable="false"
    >
      <template #default>
        <el-button size="small" :loading="recordsLoading" @click="loadRecords">重新加载时间线</el-button>
      </template>
    </el-alert>

    <el-alert
      v-if="recordActionError"
      class="growth-page-alert"
      type="error"
      :title="recordActionError"
      show-icon
      :closable="false"
    >
      <template #default>
        <el-button size="small" :loading="recordsLoading" @click="loadRecords">刷新时间线</el-button>
      </template>
    </el-alert>

    <AppFilterBar
      title="学生与筛选条件"
      description="先锁定学生，再按记录类型和时间范围筛选，避免把不同学生的成长信息混在一起看。"
      sticky
    >
      <div class="filter-grid">
        <el-select
          v-model="selectedStudentId"
          filterable
          placeholder="选择学生"
          :loading="studentsLoading"
          :disabled="studentsLoading || recordsLoading"
          @change="() => loadRecords()"
        >
          <el-option
            v-for="student in studentOptions"
            :key="student.id"
            :label="`${student.student_no} - ${student.name}`"
            :value="student.id"
          />
        </el-select>
        <el-select v-model="selectedTimelineType" placeholder="时间线类型" :disabled="!selectedStudentId || recordsLoading">
          <el-option
            v-for="item in timelineTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-select
          v-model="selectedRecordType"
          clearable
          placeholder="记录类型"
          :disabled="!selectedStudentId || recordsLoading || selectedTimelineType === 'class_transfer'"
        >
          <el-option
            v-for="item in recordTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-date-picker
          v-model="selectedDateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :disabled="!selectedStudentId || recordsLoading"
        />
      </div>
      <template #actions>
        <el-button :disabled="!selectedStudentId" :loading="recordsLoading" @click="loadRecords">查询</el-button>
        <el-button :disabled="recordsLoading" @click="resetFilters">重置</el-button>
      </template>
    </AppFilterBar>

    <AppTableShell
      title="成长时间线"
      description="人工成长记录可以编辑和删除；班级调整来自调班批次，只作为系统事件展示。"
    >
      <template #actions>
        <span class="panel-caption">共 {{ timelineTotal }} 条</span>
      </template>
      <el-empty v-if="!selectedStudentId" description="请先选择学生" />
      <div v-else v-loading="recordsLoading" class="growth-table-body">
        <el-table :data="timelineRecords" stripe>
          <el-table-column label="日期" prop="occurred_on" width="120" />
          <el-table-column label="类型" min-width="120">
            <template #default="{ row }">
              {{ typeLabel(row.record_type) }}
            </template>
          </el-table-column>
          <el-table-column label="标题" prop="title" min-width="180" />
          <el-table-column label="责任人" prop="owner_name" width="120" />
          <el-table-column label="内容摘要" min-width="220">
            <template #default="{ row }">
              {{ row.content || "-" }}
            </template>
          </el-table-column>
          <el-table-column label="附件" min-width="180">
            <template #default="{ row }">
              <div class="attachment-list">
                <el-button
                  v-for="item in row.attachments"
                  :key="item.id"
                  link
                  type="primary"
                  @click="openFile(item.file.download_url)"
                >
                  {{ item.file.original_filename }}
                </el-button>
                <span v-if="!row.attachments.length">-</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="130" fixed="right">
            <template #default="{ row }">
              <template v-if="row.kind === 'growth_record'">
                <el-button link type="primary" :disabled="recordsLoading || deletingRecordId === row.id" @click="openEditDialog(row)">编辑</el-button>
                <el-button link type="danger" :loading="deletingRecordId === row.id" :disabled="recordsLoading" @click="deleteRecord(row.id)">删除</el-button>
              </template>
              <span v-else class="system-event-label">系统事件</span>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="timelineEmptyDescription">
              <el-button v-if="recordsLoadError" type="primary" plain :loading="recordsLoading" @click="loadRecords">重新加载时间线</el-button>
            </el-empty>
          </template>
        </el-table>
      </div>
    </AppTableShell>

    <el-dialog
      v-model="dialogVisible"
      :title="form.id ? '编辑成长记录' : '新增成长记录'"
      width="720px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <div class="filter-grid">
        <el-date-picker
          v-model="form.occurred_on"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="发生日期"
          :disabled="saving || attachmentUploading"
        />
        <el-select v-model="form.record_type" placeholder="记录类型" :disabled="saving || attachmentUploading">
          <el-option
            v-for="item in recordTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-input v-model="form.title" placeholder="标题" :disabled="saving || attachmentUploading" />
        <el-input v-model="form.owner_name" placeholder="责任人" :disabled="saving || attachmentUploading" />
      </div>
      <div class="editor-grid">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="4"
          placeholder="记录内容"
          :disabled="saving || attachmentUploading"
        />
        <el-input
          v-model="form.note"
          type="textarea"
          :rows="3"
          placeholder="备注"
          :disabled="saving || attachmentUploading"
        />
      </div>
      <el-alert
        v-if="formActionError"
        class="dialog-alert"
        type="error"
        show-icon
        :closable="false"
        :title="formActionError"
      />
      <div class="section-head sub-head">
        <div>
          <h3>附件</h3>
          <p>附件先上传，再与成长记录绑定。</p>
        </div>
      </div>
      <div class="action-row">
        <input
          ref="attachmentInputRef"
          class="file-input"
          type="file"
          multiple
          :disabled="attachmentUploading || saving"
          @change="handleAttachmentUpload"
        />
      </div>
      <el-alert
        v-if="attachmentUploadError"
        class="dialog-alert"
        type="error"
        show-icon
        :closable="false"
        :title="attachmentUploadError"
      />
      <div class="attachment-tags">
        <el-tag
          v-for="item in form.attachments"
          :key="item.id"
          :closable="!saving && !attachmentUploading"
          @close="removeAttachment(item.id)"
        >
          {{ item.original_filename }}
        </el-tag>
        <span v-if="!form.attachments.length" class="hint-text">暂无附件</span>
      </div>
      <template #footer>
        <el-button :disabled="saving || attachmentUploading" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" :disabled="attachmentUploading" @click="saveRecord">保存</el-button>
      </template>
    </el-dialog>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";
import { useRoute } from "vue-router";

import { apiRequest, openFile, uploadFile } from "../api/client";
import {
  AppFilterBar,
  AppPage,
  AppStatGrid,
  AppTableShell,
  type PageMetaItem,
  type StatCardItem,
} from "../components/ui";
import {
  formatClassTransferEventSummary,
  type ClassTransferHistoryItem,
} from "../components/students/studentClassTransfer";
import { growthSummaryPrintPreviewPath } from "../utils/print";
import { formatUserActionError } from "../utils/userFeedback";

interface StudentOption {
  id: number;
  student_no: string;
  name: string;
}

interface UploadedAttachment {
  id: number;
  original_filename: string;
  download_url: string;
}

interface RecordAttachment {
  id: number;
  stored_file_id: number;
  file: UploadedAttachment;
}

interface GrowthRecord {
  id: number;
  kind?: "growth_record";
  student_id: number;
  student_name?: string | null;
  occurred_on: string;
  record_type: string;
  title: string;
  content?: string | null;
  owner_name?: string | null;
  note?: string | null;
  is_active: boolean;
  attachments: RecordAttachment[];
}

interface GrowthTimelineRecord extends GrowthRecord {
  kind: "growth_record";
}

interface ClassTransferTimelineRecord {
  id: number;
  kind: "class_transfer";
  student_id: number;
  occurred_on: string;
  record_type: "class_transfer";
  title: string;
  content: string;
  owner_name?: string | null;
  note?: string | null;
  is_active: boolean;
  attachments: [];
  transfer: ClassTransferHistoryItem;
}

type TimelineRecord = GrowthTimelineRecord | ClassTransferTimelineRecord;

interface GrowthListResponse {
  items: GrowthRecord[];
  total: number;
}

interface FormState {
  id?: number;
  occurred_on: string;
  record_type: string;
  title: string;
  content: string;
  owner_name: string;
  note: string;
  attachments: UploadedAttachment[];
}

const recordTypeOptions = [
  { value: "reward", label: "奖励记录" },
  { value: "discipline", label: "处分记录" },
  { value: "activity", label: "活动记录" },
  { value: "cadre", label: "干部任职" },
  { value: "interview", label: "谈话记录" },
  { value: "home_school", label: "家校沟通" },
  { value: "mental_health", label: "心理关注" },
  { value: "quality_eval", label: "综合素质评价" },
  { value: "other", label: "其他" },
];

const timelineTypeOptions = [
  { value: "all", label: "全部" },
  { value: "growth_record", label: "成长记录" },
  { value: "class_transfer", label: "班级调整" },
];

const route = useRoute();
const studentOptions = ref<StudentOption[]>([]);
const growthRecords = ref<GrowthTimelineRecord[]>([]);
const classTransferRecords = ref<ClassTransferTimelineRecord[]>([]);
const selectedStudentId = ref<number | null>(null);
const selectedTimelineType = ref<"all" | "growth_record" | "class_transfer">("all");
const selectedRecordType = ref<string | null>(null);
const selectedDateRange = ref<string[] | null>([]);
const dialogVisible = ref(false);
const saving = ref(false);
const studentsLoading = ref(false);
const recordsLoading = ref(false);
const attachmentUploading = ref(false);
const deletingRecordId = ref<number | null>(null);
const studentsLoadError = ref("");
const recordsLoadError = ref("");
const recordActionError = ref("");
const formActionError = ref("");
const attachmentUploadError = ref("");
const attachmentInputRef = ref<HTMLInputElement | null>(null);

const form = ref<FormState>({
  occurred_on: "",
  record_type: "reward",
  title: "",
  content: "",
  owner_name: "",
  note: "",
  attachments: [],
});

const timelineRecords = computed<TimelineRecord[]>(() => {
  const source =
    selectedTimelineType.value === "growth_record"
      ? growthRecords.value
      : selectedTimelineType.value === "class_transfer"
        ? classTransferRecords.value
        : [...growthRecords.value, ...classTransferRecords.value];
  return [...source].sort((left, right) => {
    const leftDate = left.occurred_on || "";
    const rightDate = right.occurred_on || "";
    return rightDate.localeCompare(leftDate);
  });
});
const timelineTotal = computed(() => timelineRecords.value.length);
const attachmentCount = computed(() =>
  growthRecords.value.reduce((sum, item) => sum + item.attachments.length, 0),
);
const selectedStudentName = computed(() => {
  if (!selectedStudentId.value) return "未选择学生";
  const current = studentOptions.value.find((item) => item.id === selectedStudentId.value);
  return current ? `${current.student_no} - ${current.name}` : "未选择学生";
});
const selectedRecordTypeLabel = computed(
  () => {
    const timelineLabel = timelineTypeOptions.find((item) => item.value === selectedTimelineType.value)?.label ?? "全部";
    const recordLabel = recordTypeOptions.find((item) => item.value === selectedRecordType.value)?.label;
    if (selectedTimelineType.value === "class_transfer") return timelineLabel;
    return recordLabel ? `${timelineLabel} / ${recordLabel}` : timelineLabel;
  },
);
const activeFilterCount = computed(() => {
  let count = 0;
  if (selectedTimelineType.value !== "all") count += 1;
  if (selectedRecordType.value) count += 1;
  if (selectedDateRange.value?.[0] || selectedDateRange.value?.[1]) count += 1;
  return count;
});
const growthPageMeta = computed<PageMetaItem[]>(() => [
  { label: "当前学生", value: selectedStudentName.value },
  { label: "时间线条目", value: timelineTotal.value },
  { label: "班级调整", value: classTransferRecords.value.length },
  { label: "附件数", value: attachmentCount.value },
  { label: "筛选类型", value: selectedRecordTypeLabel.value },
]);
const overviewCards = computed<StatCardItem[]>(() => [
  {
    label: "时间线条目",
    value: timelineTotal.value,
    help: "当前学生在当前筛选条件下的记录总数。",
    tone: "primary",
    loading: recordsLoading.value,
  },
  {
    label: "附件关联",
    value: attachmentCount.value,
    help: "已上传并挂接到成长记录的附件数量。",
    tone: "warning",
    loading: recordsLoading.value,
  },
  {
    label: "班级调整",
    value: classTransferRecords.value.length,
    help: "批量调班生成的系统事件数量。",
    tone: "info",
    loading: recordsLoading.value,
  },
]);
const timelineEmptyDescription = computed(() => {
  if (recordsLoadError.value) return "时间线加载失败，请点击重新加载";
  if (activeFilterCount.value) return "当前筛选条件下暂无时间线记录";
  return "暂无成长记录，可以先新增记录或查看调班后生成的系统事件";
});

function typeLabel(value: string): string {
  if (value === "class_transfer") return "班级调整";
  if (value === "growth_record") return "成长记录";
  return recordTypeOptions.find((item) => item.value === value)?.label ?? value;
}

function resetForm(): void {
  form.value = {
    occurred_on: "",
    record_type: "reward",
    title: "",
    content: "",
    owner_name: "",
    note: "",
    attachments: [],
  };
  formActionError.value = "";
  attachmentUploadError.value = "";
  if (attachmentInputRef.value) {
    attachmentInputRef.value.value = "";
  }
}

async function loadStudents(): Promise<void> {
  try {
    studentsLoading.value = true;
    studentsLoadError.value = "";
    const payload = await apiRequest<{ items: StudentOption[] }>("/api/students?page=1&page_size=200");
    studentOptions.value = payload.items;
    const queryStudentId = Number(route.query.student_id);
    if (!selectedStudentId.value && Number.isFinite(queryStudentId) && queryStudentId > 0) {
      selectedStudentId.value = queryStudentId;
    }
    if (!selectedStudentId.value && payload.items.length) {
      selectedStudentId.value = payload.items[0].id;
    }
  } catch (error) {
    studentOptions.value = [];
    selectedStudentId.value = null;
    growthRecords.value = [];
    classTransferRecords.value = [];
    recordActionError.value = "";
    studentsLoadError.value = formatUserActionError(
      "加载学生列表",
      error,
      "确认本地服务已启动，再点击“重新加载学生”；也可以回到学生中心检查学生数据。",
    );
    ElMessage.error(studentsLoadError.value);
  } finally {
    studentsLoading.value = false;
  }
}

async function loadRecords(): Promise<void> {
  if (!selectedStudentId.value) {
    growthRecords.value = [];
    classTransferRecords.value = [];
    recordsLoadError.value = "";
    recordActionError.value = "";
    return;
  }
  try {
    recordsLoading.value = true;
    recordsLoadError.value = "";
    recordActionError.value = "";
    const shouldLoadGrowth = selectedTimelineType.value !== "class_transfer";
    const shouldLoadClassTransfer =
      selectedTimelineType.value === "class_transfer" ||
      (selectedTimelineType.value === "all" && !selectedRecordType.value);
    const params = new URLSearchParams();
    if (selectedRecordType.value) params.set("record_type", selectedRecordType.value);
    if (selectedDateRange.value?.[0]) params.set("start_date", selectedDateRange.value[0]);
    if (selectedDateRange.value?.[1]) params.set("end_date", selectedDateRange.value[1]);
    const query = params.toString();
    let nextGrowthRecords: GrowthTimelineRecord[] = [];
    let nextClassTransferRecords: ClassTransferTimelineRecord[] = [];
    if (shouldLoadGrowth) {
      const payload = await apiRequest<GrowthListResponse>(
        `/api/archives/students/${selectedStudentId.value}/records${query ? `?${query}` : ""}`,
      );
      nextGrowthRecords = payload.items.map((item) => ({ ...item, kind: "growth_record" }));
    }
    if (shouldLoadClassTransfer) {
      const history = await apiRequest<ClassTransferHistoryItem[]>(
        `/api/students/${selectedStudentId.value}/class-transfer-history`,
      );
      nextClassTransferRecords = history
        .filter((item) => isWithinDateRange(item.effective_on))
        .map(mapClassTransferToTimelineRecord);
    }
    growthRecords.value = nextGrowthRecords;
    classTransferRecords.value = nextClassTransferRecords;
  } catch (error) {
    growthRecords.value = [];
    classTransferRecords.value = [];
    recordsLoadError.value = formatUserActionError(
      "加载成长时间线",
      error,
      "确认本地服务已启动，再点击“重新加载时间线”；如果刚切换过学生，请先回到学生中心确认该学生仍可访问。",
    );
    ElMessage.error(recordsLoadError.value);
  } finally {
    recordsLoading.value = false;
  }
}

async function loadStudentsAndRecords(): Promise<void> {
  await loadStudents();
  await loadRecords();
}

function resetFilters(): void {
  selectedTimelineType.value = "all";
  selectedRecordType.value = null;
  selectedDateRange.value = [];
  void loadRecords();
}

function openCreateDialog(): void {
  if (!selectedStudentId.value) {
    ElMessage.warning("请先选择学生");
    return;
  }
  resetForm();
  formActionError.value = "";
  attachmentUploadError.value = "";
  dialogVisible.value = true;
}

function openEditDialog(row: GrowthTimelineRecord): void {
  formActionError.value = "";
  attachmentUploadError.value = "";
  form.value = {
    id: row.id,
    occurred_on: row.occurred_on,
    record_type: row.record_type,
    title: row.title,
    content: row.content ?? "",
    owner_name: row.owner_name ?? "",
    note: row.note ?? "",
    attachments: row.attachments.map((item) => item.file),
  };
  dialogVisible.value = true;
}

function isWithinDateRange(value: string): boolean {
  if (selectedDateRange.value?.[0] && value < selectedDateRange.value[0]) return false;
  if (selectedDateRange.value?.[1] && value > selectedDateRange.value[1]) return false;
  return true;
}

function mapClassTransferToTimelineRecord(item: ClassTransferHistoryItem): ClassTransferTimelineRecord {
  return {
    id: item.item_id,
    kind: "class_transfer",
    student_id: item.student_id,
    occurred_on: item.effective_on,
    record_type: "class_transfer",
    title: item.title,
    content: formatClassTransferEventSummary(item),
    owner_name: item.operator_name,
    note: item.note,
    is_active: true,
    attachments: [],
    transfer: item,
  };
}

async function handleAttachmentUpload(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  if (!files.length) return;
  try {
    attachmentUploading.value = true;
    attachmentUploadError.value = "";
    const uploaded = await Promise.all(
      files.map((file) => uploadFile<UploadedAttachment>("/api/files/upload", file, { category: "growth_archive" })),
    );
    form.value.attachments.push(...uploaded);
    ElMessage.success(`已上传 ${uploaded.length} 个附件`);
  } catch (error) {
    attachmentUploadError.value = formatUserActionError(
      "上传成长档案附件",
      error,
      "确认文件仍在本机可访问，再重新选择上传。",
    );
    ElMessage.error(attachmentUploadError.value);
  } finally {
    attachmentUploading.value = false;
    if (attachmentInputRef.value) {
      attachmentInputRef.value.value = "";
    }
  }
}

function removeAttachment(fileId: number): void {
  attachmentUploadError.value = "";
  form.value.attachments = form.value.attachments.filter((item) => item.id !== fileId);
}

function handleDialogClosed(): void {
  resetForm();
}

async function saveRecord(): Promise<void> {
  if (!selectedStudentId.value) return;
  formActionError.value = "";
  if (!form.value.occurred_on || !form.value.record_type || !form.value.title.trim()) {
    formActionError.value = "日期、类型、标题不能为空";
    ElMessage.warning(formActionError.value);
    return;
  }
  try {
    saving.value = true;
    const payload = {
      occurred_on: form.value.occurred_on,
      record_type: form.value.record_type,
      title: form.value.title.trim(),
      content: form.value.content.trim() || null,
      owner_name: form.value.owner_name.trim() || null,
      note: form.value.note.trim() || null,
      attachment_file_ids: form.value.attachments.map((item) => item.id),
      is_active: true,
    };
    if (form.value.id) {
      await apiRequest(`/api/archives/records/${form.value.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } else {
      await apiRequest(`/api/archives/students/${selectedStudentId.value}/records`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
    dialogVisible.value = false;
    await loadRecords();
    ElMessage.success("成长记录已保存");
  } catch (error) {
    formActionError.value = formatUserActionError(
      "保存成长记录",
      error,
      "请检查日期、类型、标题和附件是否有效，然后重新保存。",
    );
    ElMessage.error(formActionError.value);
  } finally {
    saving.value = false;
  }
}

async function deleteRecord(recordId: number): Promise<void> {
  try {
    await ElMessageBox.confirm("删除后仍可从数据库日志追溯，但记录本身将不再显示。是否继续？", "删除记录", {
      type: "warning",
    });
    deletingRecordId.value = recordId;
    recordActionError.value = "";
    await apiRequest(`/api/archives/records/${recordId}`, { method: "DELETE" });
    await loadRecords();
    ElMessage.success("成长记录已删除");
  } catch (error) {
    if (error === "cancel" || error === "close") return;
    recordActionError.value = formatUserActionError(
      "删除成长记录",
      error,
      "刷新时间线后确认记录状态，再重新删除。",
    );
    ElMessage.error(recordActionError.value);
  } finally {
    if (deletingRecordId.value === recordId) {
      deletingRecordId.value = null;
    }
  }
}

function exportSummary(): void {
  if (!selectedStudentId.value) return;
  openFile(`/api/archives/students/${selectedStudentId.value}/summary/export`);
}

function openPrintPreview(): void {
  if (!selectedStudentId.value) return;
  openFile(growthSummaryPrintPreviewPath(selectedStudentId.value));
}

onMounted(loadStudentsAndRecords);
</script>

<style scoped>
.growth-page-alert {
  margin-top: -4px;
}

.panel-caption {
  color: #6c8194;
  font-size: 13px;
}

.growth-table-body {
  min-height: 260px;
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

.editor-grid {
  display: grid;
  gap: 12px;
  margin-top: 12px;
}

.dialog-alert {
  margin-top: 12px;
}

.sub-head {
  margin-top: 20px;
}

.attachment-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
}

.attachment-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.file-input {
  min-width: 260px;
}

.file-input[disabled] {
  cursor: not-allowed;
  opacity: 0.64;
}

.hint-text {
  color: #60748a;
  font-size: 13px;
}

.system-event-label {
  color: #6d8194;
  font-size: 13px;
}
</style>
