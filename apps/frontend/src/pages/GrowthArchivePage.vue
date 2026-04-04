<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">学生中心 / 成长档案</div>
        <h2 class="page-title">成长档案</h2>
        <p class="page-subtitle">
          以时间线方式维护学生成长记录，支持附件上传、分类筛选和单个学生档案摘要导出。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>当前学生</strong>{{ selectedStudentName }}</span>
          <span class="page-chip"><strong>记录数</strong>{{ total }}</span>
          <span class="page-chip"><strong>附件数</strong>{{ attachmentCount }}</span>
          <span class="page-chip"><strong>筛选类型</strong>{{ selectedRecordTypeLabel }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button :disabled="!selectedStudentId" @click="exportSummary">导出档案摘要</el-button>
        <el-button type="primary" :disabled="!selectedStudentId" @click="openCreateDialog">新增记录</el-button>
      </div>
    </header>

    <section class="overview-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">时间线视图</div>
        <h3>{{ selectedStudentName }}</h3>
        <p>奖励、处分、活动、谈话、家校沟通和心理关注都收在同一条成长时间线里，附件也跟随记录保存。</p>
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
          <h3>学生与筛选条件</h3>
          <p>先锁定学生，再按记录类型和时间范围筛选，避免把不同学生的成长信息混在一起看。</p>
        </div>
      </div>
      <div class="filter-grid">
        <el-select v-model="selectedStudentId" filterable placeholder="选择学生">
          <el-option
            v-for="student in studentOptions"
            :key="student.id"
            :label="`${student.student_no} - ${student.name}`"
            :value="student.id"
          />
        </el-select>
        <el-select v-model="selectedRecordType" clearable placeholder="记录类型">
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
        />
      </div>
      <div class="action-row toolbar-row">
        <el-button @click="loadRecords">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </section>

    <section class="metric-grid">
      <div class="soft-card stat-card">
        <div class="metric-label">当前学生记录数</div>
        <div class="metric-value">{{ total }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">已上传附件数</div>
        <div class="metric-value">{{ attachmentCount }}</div>
      </div>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>成长记录</h3>
          <p>支持奖励、处分、活动、干部任职、谈话、家校沟通、心理关注和综合素质评价等类型。</p>
        </div>
      </div>
      <el-empty v-if="!selectedStudentId" description="请先选择学生" />
      <div v-else class="table-shell">
        <el-table :data="records" stripe>
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
              <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
              <el-button link type="danger" @click="deleteRecord(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

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
        />
        <el-select v-model="form.record_type" placeholder="记录类型">
          <el-option
            v-for="item in recordTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
        <el-input v-model="form.title" placeholder="标题" />
        <el-input v-model="form.owner_name" placeholder="责任人" />
      </div>
      <div class="editor-grid">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="4"
          placeholder="记录内容"
        />
        <el-input
          v-model="form.note"
          type="textarea"
          :rows="3"
          placeholder="备注"
        />
      </div>
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
          @change="handleAttachmentUpload"
        />
      </div>
      <div class="attachment-tags">
        <el-tag
          v-for="item in form.attachments"
          :key="item.id"
          closable
          @close="removeAttachment(item.id)"
        >
          {{ item.original_filename }}
        </el-tag>
        <span v-if="!form.attachments.length" class="hint-text">暂无附件</span>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRecord">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";

import { apiRequest, openFile, uploadFile } from "../api/client";

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

const studentOptions = ref<StudentOption[]>([]);
const records = ref<GrowthRecord[]>([]);
const total = ref(0);
const selectedStudentId = ref<number | null>(null);
const selectedRecordType = ref<string | null>(null);
const selectedDateRange = ref<string[]>([]);
const dialogVisible = ref(false);
const saving = ref(false);
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

const attachmentCount = computed(() =>
  records.value.reduce((sum, item) => sum + item.attachments.length, 0),
);
const selectedStudentName = computed(() => {
  if (!selectedStudentId.value) return "未选择学生";
  const current = studentOptions.value.find((item) => item.id === selectedStudentId.value);
  return current ? `${current.student_no} - ${current.name}` : "未选择学生";
});
const selectedRecordTypeLabel = computed(
  () => recordTypeOptions.find((item) => item.value === selectedRecordType.value)?.label ?? "全部类型",
);
const overviewCards = computed(() => [
  {
    label: "时间线条目",
    value: total.value,
    help: "当前学生在当前筛选条件下的记录总数。",
    tone: "tone-blue",
  },
  {
    label: "附件关联",
    value: attachmentCount.value,
    help: "已上传并挂接到成长记录的附件数量。",
    tone: "tone-amber",
  },
  {
    label: "记录类型",
    value: new Set(records.value.map((item) => item.record_type)).size,
    help: "当前结果里出现的记录类型数量。",
    tone: "tone-slate",
  },
]);

function typeLabel(value: string): string {
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
  if (attachmentInputRef.value) {
    attachmentInputRef.value.value = "";
  }
}

async function loadStudents(): Promise<void> {
  const payload = await apiRequest<{ items: StudentOption[] }>("/api/students?page=1&page_size=200");
  studentOptions.value = payload.items;
  if (!selectedStudentId.value && payload.items.length) {
    selectedStudentId.value = payload.items[0].id;
  }
}

async function loadRecords(): Promise<void> {
  if (!selectedStudentId.value) {
    records.value = [];
    total.value = 0;
    return;
  }
  const params = new URLSearchParams();
  if (selectedRecordType.value) params.set("record_type", selectedRecordType.value);
  if (selectedDateRange.value[0]) params.set("start_date", selectedDateRange.value[0]);
  if (selectedDateRange.value[1]) params.set("end_date", selectedDateRange.value[1]);
  const query = params.toString();
  const payload = await apiRequest<GrowthListResponse>(
    `/api/archives/students/${selectedStudentId.value}/records${query ? `?${query}` : ""}`,
  );
  records.value = payload.items;
  total.value = payload.total;
}

function resetFilters(): void {
  selectedRecordType.value = null;
  selectedDateRange.value = [];
  loadRecords().catch((error) => ElMessage.error((error as Error).message));
}

function openCreateDialog(): void {
  if (!selectedStudentId.value) {
    ElMessage.warning("请先选择学生");
    return;
  }
  resetForm();
  dialogVisible.value = true;
}

function openEditDialog(row: GrowthRecord): void {
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

async function handleAttachmentUpload(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  if (!files.length) return;
  try {
    const uploaded = await Promise.all(
      files.map((file) => uploadFile<UploadedAttachment>("/api/files/upload", file, { category: "growth_archive" })),
    );
    form.value.attachments.push(...uploaded);
    ElMessage.success(`已上传 ${uploaded.length} 个附件`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    if (attachmentInputRef.value) {
      attachmentInputRef.value.value = "";
    }
  }
}

function removeAttachment(fileId: number): void {
  form.value.attachments = form.value.attachments.filter((item) => item.id !== fileId);
}

function handleDialogClosed(): void {
  resetForm();
}

async function saveRecord(): Promise<void> {
  if (!selectedStudentId.value) return;
  if (!form.value.occurred_on || !form.value.record_type || !form.value.title.trim()) {
    ElMessage.warning("日期、类型、标题不能为空");
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
    ElMessage.error((error as Error).message);
  } finally {
    saving.value = false;
  }
}

async function deleteRecord(recordId: number): Promise<void> {
  try {
    await ElMessageBox.confirm("删除后仍可从数据库日志追溯，但记录本身将不再显示。是否继续？", "删除记录", {
      type: "warning",
    });
    await apiRequest(`/api/archives/records/${recordId}`, { method: "DELETE" });
    await loadRecords();
    ElMessage.success("成长记录已删除");
  } catch (error) {
    if (error === "cancel" || error === "close") return;
    ElMessage.error((error as Error).message);
  }
}

function exportSummary(): void {
  if (!selectedStudentId.value) return;
  openFile(`/api/archives/students/${selectedStudentId.value}/summary/export`);
}

onMounted(async () => {
  try {
    await loadStudents();
    await loadRecords();
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

.stat-card {
  padding: 18px 20px;
}

.metric-label {
  color: #60748a;
  font-size: 13px;
}

.metric-value {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 700;
  color: #244560;
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

.hint-text {
  color: #60748a;
  font-size: 13px;
}

@media (max-width: 1180px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
