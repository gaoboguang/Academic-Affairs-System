<template>
  <div v-if="result" class="import-feedback-panel">
    <el-alert
      :title="result.message"
      :type="alertType"
      show-icon
      :closable="false"
    />
    <div class="import-feedback-body">
      <div class="import-feedback-summary-row">
        <p class="import-feedback-summary">{{ summary }}</p>
        <el-tag :type="statusTagType(result.status)" effect="light">
          {{ formatImportStatus(result.status) }}
        </el-tag>
      </div>
      <template v-if="result.notice_preview?.length">
        <p class="import-feedback-title">本次导入提示</p>
        <ul class="import-feedback-list import-feedback-list-notice">
          <li v-for="item in result.notice_preview" :key="item">{{ item }}</li>
        </ul>
      </template>
      <template v-if="result.error_preview?.length">
        <p class="import-feedback-title">前三条错误</p>
        <ul class="import-feedback-list">
          <li v-for="item in result.error_preview" :key="item">{{ item }}</li>
        </ul>
      </template>
      <div v-if="result.error_report_path" class="action-row import-feedback-actions">
        <el-button link type="primary" @click="openErrorReport">下载错误报告</el-button>
      </div>
      <p v-if="hasFailures" class="import-feedback-next-step">
        下一步：先下载错误报告，按“错误原因 / 建议修复”修改原文件，再回到对应业务页重新导入。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { openFile } from "../../api/client";
import {
  buildImportErrorReportUrl,
  buildImportSummary,
  formatImportStatus,
  importStatusTagType,
  resolveImportAlertType,
  type ImportFeedbackResult,
} from "../../utils/importFeedback";

const props = defineProps<{
  result: ImportFeedbackResult | null;
}>();

const alertType = computed(() => (props.result ? resolveImportAlertType(props.result) : "success"));
const summary = computed(() => (props.result ? buildImportSummary(props.result) : ""));
const hasFailures = computed(() => (props.result?.failed_rows ?? 0) > 0 || Boolean(props.result?.error_preview?.length));

function statusTagType(status?: string | null): "success" | "warning" | "info" | "danger" {
  return importStatusTagType(status);
}

function openErrorReport(): void {
  if (!props.result?.error_report_path) return;
  openFile(buildImportErrorReportUrl(props.result.error_report_path));
}
</script>

<style scoped>
.import-feedback-panel {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.import-feedback-body {
  padding: 12px 14px;
  border: 1px solid rgba(123, 141, 158, 0.24);
  border-radius: 8px;
  background: rgba(248, 251, 253, 0.86);
}

.import-feedback-summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.import-feedback-summary,
.import-feedback-title {
  margin: 0;
  color: #42576b;
  line-height: 1.6;
}

.import-feedback-title {
  margin-top: 10px;
  font-weight: 700;
}

.import-feedback-list {
  margin: 6px 0 0;
  padding-left: 18px;
  color: #8a4a36;
  line-height: 1.7;
}

.import-feedback-list-notice {
  color: #52687c;
}

.import-feedback-actions {
  margin-top: 8px;
}

.import-feedback-next-step {
  margin: 8px 0 0;
  color: #5e7184;
  line-height: 1.6;
}
</style>
