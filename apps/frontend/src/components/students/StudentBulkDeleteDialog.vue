<template>
  <el-dialog
    v-model="visible"
    title="批量删除学生"
    width="920px"
    destroy-on-close
    :close-on-click-modal="false"
    @closed="resetDialog"
  >
    <div class="bulk-delete-dialog">
      <el-alert
        title="批量删除只会停用学生主档"
        type="warning"
        show-icon
        :closable="false"
        description="成绩、成长档案、附件、推荐记录、志愿草稿、升学画像和路径评估都会保留，后续仍可用于审计和追溯。"
      />

      <div class="bulk-delete-selected">
        <strong>本次选择 {{ studentIds.length }} 名学生</strong>
        <p>{{ selectedStudentSummary }}</p>
      </div>

      <el-form label-width="100px" class="bulk-delete-form">
        <el-form-item label="删除原因" required>
          <el-input
            v-model="reason"
            type="textarea"
            :rows="3"
            maxlength="255"
            show-word-limit
            placeholder="例如：误导入重复学生"
            @input="handleReasonInput"
          />
        </el-form-item>
      </el-form>

      <div v-if="!preview" class="bulk-delete-empty">
        填写删除原因后点击“删除预检”，系统会先检查每名学生的关联数据和阻断原因。
      </div>

      <div v-if="preview" class="bulk-delete-preview">
        <div class="bulk-delete-stat-grid">
          <div>
            <span>预检学生</span>
            <strong>{{ preview.total }}</strong>
          </div>
          <div>
            <span>可停用</span>
            <strong>{{ preview.deletable_count }}</strong>
          </div>
          <div>
            <span>已阻断</span>
            <strong>{{ preview.blocked_count }}</strong>
          </div>
        </div>

        <el-table :data="preview.items" border stripe max-height="280">
          <el-table-column label="学生" min-width="150">
            <template #default="{ row }">
              <div class="student-cell-main">{{ row.student_name ?? "-" }}</div>
              <div class="student-cell-sub">{{ row.student_no ?? "无学号" }}</div>
            </template>
          </el-table-column>
          <el-table-column label="当前班级" min-width="120">
            <template #default="{ row }">
              {{ row.current_class_name ?? "-" }}
            </template>
          </el-table-column>
          <el-table-column label="预检结果" width="100">
            <template #default="{ row }">
              <el-tag :type="resolvePreviewStatusType(row.status)" effect="light">
                {{ resolvePreviewStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="关联数据风险" min-width="260">
            <template #default="{ row }">
              <div class="risk-pill-row">
                <span
                  v-for="summary in formatBulkDeleteAssociationSummary(row.association_counts)"
                  :key="summary"
                  class="risk-pill"
                  :class="{ muted: summary === '暂无关联历史数据' }"
                >
                  {{ summary }}
                </span>
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
            <p>请输入下面这句话，确认只停用可删除学生，历史数据不清空。</p>
            <code>{{ preview.required_confirm_text }}</code>
          </div>
          <el-input
            v-model="confirmText"
            :disabled="executing || Boolean(executeResult)"
            :placeholder="preview.required_confirm_text"
          />
        </div>
      </div>

      <div v-if="executeResult" class="bulk-delete-result">
        <el-alert
          :title="executeResult.message"
          :type="executeResult.status === 'success' ? 'success' : 'warning'"
          show-icon
          :closable="false"
        />
        <el-table :data="executeResult.items" border stripe max-height="240">
          <el-table-column label="学生" min-width="150">
            <template #default="{ row }">
              <div class="student-cell-main">{{ row.student_name ?? "-" }}</div>
              <div class="student-cell-sub">{{ row.student_no ?? "无学号" }}</div>
            </template>
          </el-table-column>
          <el-table-column label="执行结果" width="100">
            <template #default="{ row }">
              <el-tag :type="resolveExecuteStatusType(row.status)" effect="light">
                {{ resolveExecuteStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="说明" min-width="280">
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
        {{ preview ? "重新预检" : "删除预检" }}
      </el-button>
      <el-button
        type="danger"
        :loading="executing"
        :disabled="!canSubmit"
        @click="executeDelete"
      >
        确认删除
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest } from "../../api/client";
import {
  canExecuteBulkDelete,
  formatBulkDeleteAssociationSummary,
  formatBulkDeleteResultMessage,
  resolveExecuteStatusLabel,
  resolveExecuteStatusType,
  resolvePreviewStatusLabel,
  resolvePreviewStatusType,
  type StudentBulkDeleteExecuteResponse,
  type StudentBulkDeletePreviewResponse,
} from "./studentBulkDelete";

const props = defineProps<{
  modelValue: boolean;
  studentIds: number[];
  studentLabels: string[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: boolean];
  completed: [];
}>();

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit("update:modelValue", value),
});
const reason = ref("");
const confirmText = ref("");
const previewLoading = ref(false);
const executing = ref(false);
const preview = ref<StudentBulkDeletePreviewResponse | null>(null);
const executeResult = ref<StudentBulkDeleteExecuteResponse | null>(null);

const selectedStudentSummary = computed(() => {
  if (!props.studentLabels.length) return "尚未选择学生";
  const visibleLabels = props.studentLabels.slice(0, 5).join("、");
  const hiddenCount = props.studentLabels.length - 5;
  return hiddenCount > 0 ? `${visibleLabels} 等 ${props.studentLabels.length} 名学生` : visibleLabels;
});
const canSubmit = computed(
  () =>
    canExecuteBulkDelete(preview.value, confirmText.value) &&
    !executing.value &&
    !executeResult.value,
);

function resetDialog(): void {
  reason.value = "";
  confirmText.value = "";
  preview.value = null;
  executeResult.value = null;
  previewLoading.value = false;
  executing.value = false;
}

function handleReasonInput(): void {
  if (!preview.value && !executeResult.value) return;
  preview.value = null;
  executeResult.value = null;
  confirmText.value = "";
}

async function loadPreview(): Promise<void> {
  const normalizedReason = reason.value.trim();
  if (!props.studentIds.length) {
    ElMessage.warning("请先勾选需要批量删除的学生");
    return;
  }
  if (!normalizedReason) {
    ElMessage.warning("请填写删除原因");
    return;
  }
  try {
    previewLoading.value = true;
    confirmText.value = "";
    executeResult.value = null;
    preview.value = await apiRequest<StudentBulkDeletePreviewResponse>(
      "/api/students/bulk-delete/preview",
      {
        method: "POST",
        body: JSON.stringify({
          student_ids: props.studentIds,
          mode: "soft_delete",
          reason: normalizedReason,
        }),
      },
    );
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    previewLoading.value = false;
  }
}

async function executeDelete(): Promise<void> {
  const currentPreview = preview.value;
  const normalizedReason = reason.value.trim();
  if (!canExecuteBulkDelete(currentPreview, confirmText.value)) {
    ElMessage.warning("请先完成预检，并按页面提示输入确认文字");
    return;
  }
  if (!currentPreview || !normalizedReason) {
    ElMessage.warning("请先完成删除预检");
    return;
  }
  try {
    executing.value = true;
    executeResult.value = await apiRequest<StudentBulkDeleteExecuteResponse>(
      "/api/students/bulk-delete",
      {
        method: "POST",
        body: JSON.stringify({
          student_ids: props.studentIds,
          mode: "soft_delete",
          reason: normalizedReason,
          confirm_token: currentPreview.confirm_token,
          confirm_text: confirmText.value.trim(),
        }),
      },
    );
    ElMessage({
      type: executeResult.value.status === "success" ? "success" : "warning",
      message: formatBulkDeleteResultMessage(executeResult.value),
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
.bulk-delete-dialog {
  display: grid;
  gap: 16px;
}

.bulk-delete-selected,
.bulk-delete-empty,
.confirm-box {
  padding: 14px 16px;
  border: 1px solid rgba(145, 163, 176, 0.24);
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.92);
}

.bulk-delete-selected strong,
.confirm-box strong {
  color: #1f3448;
}

.bulk-delete-selected p,
.confirm-box p {
  margin: 8px 0 0;
  color: #62788c;
  line-height: 1.6;
}

.bulk-delete-form {
  margin-bottom: -12px;
}

.bulk-delete-empty {
  color: #6d8194;
  line-height: 1.6;
}

.bulk-delete-preview,
.bulk-delete-result {
  display: grid;
  gap: 14px;
}

.bulk-delete-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.bulk-delete-stat-grid div {
  padding: 14px 16px;
  border: 1px solid rgba(145, 163, 176, 0.24);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.96);
}

.bulk-delete-stat-grid span {
  display: block;
  color: #6d8194;
  font-size: 13px;
}

.bulk-delete-stat-grid strong {
  display: block;
  margin-top: 8px;
  color: #1f3245;
  font-size: 26px;
  font-weight: 760;
}

.student-cell-main {
  color: #1f3448;
  font-weight: 700;
}

.student-cell-sub {
  margin-top: 3px;
  color: #7c8da0;
  font-size: 12px;
}

.risk-pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.risk-pill {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 3px 8px;
  border-radius: 8px;
  background: rgba(196, 91, 91, 0.1);
  color: #9f3e3e;
  font-size: 12px;
  line-height: 1.4;
}

.risk-pill.muted {
  background: rgba(102, 130, 153, 0.1);
  color: #62788c;
}

.confirm-box {
  display: grid;
  gap: 12px;
}

.confirm-box code {
  display: inline-flex;
  margin-top: 8px;
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f6c98;
  font-family: inherit;
  font-weight: 700;
}

@media (max-width: 900px) {
  .bulk-delete-stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
