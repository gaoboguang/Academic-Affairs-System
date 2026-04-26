<template>
  <el-dialog
    v-model="visible"
    title="批量调班"
    width="960px"
    destroy-on-close
    :close-on-click-modal="false"
    @closed="resetDialog"
  >
    <div class="class-transfer-dialog">
      <el-alert
        title="调班会更新学生当前班级，并保留批次和历史记录"
        type="info"
        show-icon
        :closable="false"
        description="调班成功后会写入调班批次、逐学生明细和班级历史，学生详情与成长档案会按系统事件展示。"
      />

      <div class="class-transfer-selected">
        <strong>本次选择 {{ studentIds.length }} 名学生</strong>
        <p>{{ selectedStudentSummary }}</p>
      </div>

      <el-form label-width="110px" class="class-transfer-form">
        <div class="form-grid">
          <el-form-item label="目标班级" required>
            <el-select
              v-model="targetClassId"
              filterable
              placeholder="选择调入班级"
              @change="handleTransferInput"
            >
              <el-option
                v-for="item in classOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="生效日期" required>
            <el-date-picker
              v-model="effectiveOn"
              type="date"
              value-format="YYYY-MM-DD"
              format="YYYY-MM-DD"
              style="width: 100%"
              @change="handleTransferInput"
            />
          </el-form-item>
        </div>
        <el-form-item label="调班原因" required>
          <el-input
            v-model="reason"
            type="textarea"
            :rows="3"
            maxlength="255"
            show-word-limit
            placeholder="例如：文理方向调整"
            @input="handleTransferInput"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="note"
            type="textarea"
            :rows="2"
            maxlength="1000"
            show-word-limit
            placeholder="例如：按年级统一调班方案执行"
            @input="handleTransferInput"
          />
        </el-form-item>
        <el-form-item label="跨年级确认">
          <el-checkbox v-model="allowCrossGrade" @change="handleTransferInput">
            允许把学生调入不同年级的班级
          </el-checkbox>
        </el-form-item>
      </el-form>

      <div v-if="!preview" class="class-transfer-empty">
        选择目标班级并填写调班原因后点击“调班预检”，系统会先检查当前班级、目标班级和跨年级风险。
      </div>

      <div v-if="preview" class="class-transfer-preview">
        <div class="class-transfer-stat-grid">
          <div>
            <span>预检学生</span>
            <strong>{{ preview.total }}</strong>
          </div>
          <div>
            <span>可调班</span>
            <strong>{{ preview.transferable_count }}</strong>
          </div>
          <div>
            <span>已阻断</span>
            <strong>{{ preview.blocked_count }}</strong>
          </div>
        </div>

        <el-table :data="preview.items" border stripe max-height="300">
          <el-table-column label="学生" min-width="150">
            <template #default="{ row }">
              <div class="student-cell-main">{{ row.student_name ?? "-" }}</div>
              <div class="student-cell-sub">{{ row.student_no ?? "无学号" }}</div>
            </template>
          </el-table-column>
          <el-table-column label="班级流向" min-width="230">
            <template #default="{ row }">
              {{ formatClassTransferRoute(row) }}
            </template>
          </el-table-column>
          <el-table-column label="预检结果" width="100">
            <template #default="{ row }">
              <el-tag :type="resolveClassTransferPreviewStatusType(row.status)" effect="light">
                {{ resolveClassTransferPreviewStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="风险提示" min-width="220">
            <template #default="{ row }">
              <div class="warning-list">
                <el-tag
                  v-for="warning in row.warnings"
                  :key="warning"
                  type="warning"
                  effect="light"
                >
                  {{ warning }}
                </el-tag>
                <span v-if="!row.warnings.length">-</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="说明" min-width="240">
            <template #default="{ row }">
              {{ row.message }}
            </template>
          </el-table-column>
        </el-table>

        <div class="confirm-box">
          <div>
            <strong>二次确认</strong>
            <p>请输入下面这句话，确认只对可调班学生执行，阻断学生不会被强行处理。</p>
            <code>{{ preview.required_confirm_text }}</code>
          </div>
          <el-input
            v-model="confirmText"
            :disabled="executing || Boolean(executeResult)"
            :placeholder="preview.required_confirm_text"
          />
        </div>
      </div>

      <div v-if="executeResult" class="class-transfer-result">
        <el-alert
          :title="executeResult.message"
          :type="executeResult.status === 'success' ? 'success' : 'warning'"
          show-icon
          :closable="false"
        />
        <el-table :data="executeResult.items" border stripe max-height="260">
          <el-table-column label="学生" min-width="150">
            <template #default="{ row }">
              <div class="student-cell-main">{{ row.student_name ?? "-" }}</div>
              <div class="student-cell-sub">{{ row.student_no ?? "无学号" }}</div>
            </template>
          </el-table-column>
          <el-table-column label="班级流向" min-width="230">
            <template #default="{ row }">
              {{ formatClassTransferRoute(row) }}
            </template>
          </el-table-column>
          <el-table-column label="执行结果" width="100">
            <template #default="{ row }">
              <el-tag :type="resolveClassTransferExecuteStatusType(row.status)" effect="light">
                {{ resolveClassTransferExecuteStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="说明" min-width="260">
            <template #default="{ row }">
              {{ row.error_message ?? row.message }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">
        {{ executeResult ? "完成" : "取消" }}
      </el-button>
      <el-button
        :loading="previewLoading"
        :disabled="executing || Boolean(executeResult)"
        @click="loadPreview"
      >
        {{ preview ? "重新预检" : "调班预检" }}
      </el-button>
      <el-button
        type="primary"
        :loading="executing"
        :disabled="!canSubmit"
        @click="executeTransfer"
      >
        确认调班
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest } from "../../api/client";
import {
  canExecuteClassTransfer,
  formatClassTransferResultMessage,
  formatClassTransferRoute,
  resolveClassTransferExecuteStatusLabel,
  resolveClassTransferExecuteStatusType,
  resolveClassTransferPreviewStatusLabel,
  resolveClassTransferPreviewStatusType,
  type ClassTransferExecuteResponse,
  type ClassTransferPreviewResponse,
} from "./studentClassTransfer";

interface ClassOption {
  id: number;
  name: string;
}

const props = defineProps<{
  modelValue: boolean;
  studentIds: number[];
  studentLabels: string[];
  classOptions: ClassOption[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  completed: [];
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit("update:modelValue", value),
});
const targetClassId = ref<number | null>(null);
const effectiveOn = ref(todayString());
const reason = ref("");
const note = ref("");
const allowCrossGrade = ref(false);
const confirmText = ref("");
const previewLoading = ref(false);
const executing = ref(false);
const preview = ref<ClassTransferPreviewResponse | null>(null);
const executeResult = ref<ClassTransferExecuteResponse | null>(null);

const selectedStudentSummary = computed(() => {
  if (!props.studentLabels.length) return "尚未选择学生";
  const visibleLabels = props.studentLabels.slice(0, 5).join("、");
  const hiddenCount = props.studentLabels.length - 5;
  return hiddenCount > 0 ? `${visibleLabels} 等 ${props.studentLabels.length} 名学生` : visibleLabels;
});
const canSubmit = computed(
  () =>
    canExecuteClassTransfer(preview.value, confirmText.value) &&
    !executing.value &&
    !executeResult.value,
);

function todayString(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function resetDialog(): void {
  targetClassId.value = null;
  effectiveOn.value = todayString();
  reason.value = "";
  note.value = "";
  allowCrossGrade.value = false;
  confirmText.value = "";
  preview.value = null;
  executeResult.value = null;
  previewLoading.value = false;
  executing.value = false;
}

function handleTransferInput(): void {
  if (!preview.value && !executeResult.value) return;
  preview.value = null;
  executeResult.value = null;
  confirmText.value = "";
}

function buildRequestPayload(): Record<string, unknown> | null {
  const normalizedReason = reason.value.trim();
  if (!props.studentIds.length) {
    ElMessage.warning("请先勾选需要调班的学生");
    return null;
  }
  if (!targetClassId.value) {
    ElMessage.warning("请选择目标班级");
    return null;
  }
  if (!effectiveOn.value) {
    ElMessage.warning("请选择生效日期");
    return null;
  }
  if (!normalizedReason) {
    ElMessage.warning("请填写调班原因");
    return null;
  }
  return {
    student_ids: props.studentIds,
    target_class_id: targetClassId.value,
    effective_on: effectiveOn.value,
    reason: normalizedReason,
    note: note.value.trim() || null,
    allow_cross_grade: allowCrossGrade.value,
  };
}

async function loadPreview(): Promise<void> {
  const payload = buildRequestPayload();
  if (!payload) return;
  try {
    previewLoading.value = true;
    confirmText.value = "";
    executeResult.value = null;
    preview.value = await apiRequest<ClassTransferPreviewResponse>(
      "/api/students/class-transfer/preview",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    previewLoading.value = false;
  }
}

async function executeTransfer(): Promise<void> {
  const currentPreview = preview.value;
  if (!canExecuteClassTransfer(currentPreview, confirmText.value)) {
    ElMessage.warning("请先完成预检，并按页面提示输入确认文字");
    return;
  }
  const payload = buildRequestPayload();
  if (!payload || !currentPreview) return;
  try {
    executing.value = true;
    executeResult.value = await apiRequest<ClassTransferExecuteResponse>(
      "/api/students/class-transfer",
      {
        method: "POST",
        body: JSON.stringify({
          ...payload,
          confirm_token: currentPreview.confirm_token,
          confirm_text: confirmText.value.trim(),
        }),
      },
    );
    ElMessage({
      type: executeResult.value.status === "success" ? "success" : "warning",
      message: formatClassTransferResultMessage(executeResult.value),
    });
    emit("completed");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    executing.value = false;
  }
}
</script>

<style scoped>
.class-transfer-dialog {
  display: grid;
  gap: 16px;
}

.class-transfer-selected,
.class-transfer-empty,
.confirm-box {
  padding: 14px 16px;
  border: 1px solid rgba(145, 163, 176, 0.24);
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.92);
}

.class-transfer-selected strong,
.confirm-box strong {
  color: #1f3448;
}

.class-transfer-selected p,
.confirm-box p {
  margin: 8px 0 0;
  color: #62788c;
  line-height: 1.6;
}

.class-transfer-form {
  margin-bottom: -12px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.class-transfer-empty {
  color: #6d8194;
  line-height: 1.6;
}

.class-transfer-preview,
.class-transfer-result {
  display: grid;
  gap: 14px;
}

.class-transfer-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.class-transfer-stat-grid div {
  padding: 14px 16px;
  border: 1px solid rgba(145, 163, 176, 0.24);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.96);
}

.class-transfer-stat-grid span {
  display: block;
  color: #6d8194;
  font-size: 13px;
}

.class-transfer-stat-grid strong {
  display: block;
  margin-top: 4px;
  color: #1f3448;
  font-size: 24px;
}

.student-cell-main {
  color: #1f3448;
  font-weight: 700;
}

.student-cell-sub {
  margin-top: 4px;
  color: #71869a;
  font-size: 12px;
}

.warning-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.confirm-box {
  display: grid;
  gap: 12px;
}

.confirm-box code {
  display: inline-block;
  margin-top: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f5876;
}

@media (max-width: 760px) {
  .form-grid,
  .class-transfer-stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
