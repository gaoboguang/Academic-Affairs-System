<template>
  <AppPage
    title="统一查看模板、批次、错误报告和撤销说明"
    eyebrow="数据治理 / 导入中心"
    description="统一查看模板、批次、错误报告和撤销说明；导入后可回看结果、下载错误报告并回到对应业务页面修正。"
    :meta="importPageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button :disabled="loading" @click="router.push('/system-tools')">备份与审计</el-button>
        <el-button type="primary" :loading="loading" @click="loadBatches">刷新</el-button>
      </div>
    </template>

    <el-alert
      v-if="loadError"
      class="page-alert"
      type="error"
      show-icon
      :closable="false"
      :title="loadError"
    >
      <template #default>
        <div class="action-row toolbar-row">
          <el-button size="small" type="danger" plain :loading="loading" @click="loadBatches">重新刷新</el-button>
          <el-button size="small" plain @click="router.push('/system-tools')">查看备份与审计</el-button>
        </div>
      </template>
    </el-alert>

    <AppStatGrid :items="importStatCards" :columns="4" />

    <section class="soft-card trial-run-panel">
      <div class="section-head">
        <div>
          <h3>真实学校数据试跑流程</h3>
          <p>按这个顺序跑一份真实或脱敏数据；每次大批量导入前先备份，导入后先看摘要和错误报告。</p>
        </div>
        <el-button type="primary" plain :disabled="loading" @click="router.push('/system-tools')">先创建备份</el-button>
      </div>
      <div class="trial-step-grid">
        <article v-for="item in importCenterTrialRunSteps" :key="item.title" class="trial-step-card">
          <strong>{{ item.title }}</strong>
          <p>{{ item.detail }}</p>
          <el-button link type="primary" :disabled="loading" @click="router.push(item.path)">
            {{ item.actionLabel }}
          </el-button>
        </article>
      </div>
      <el-alert
        class="rollback-alert"
        type="warning"
        show-icon
        :closable="false"
        title="本系统当前不支持无快照逐行回滚；导入前请先创建备份，少量错误优先回业务页或重新导入正确模板修正。"
      />
    </section>

    <AppSectionCard
      title="导入前预检"
      description="重点检查模板版本、必填列、重复行，以及年级、班级、学科、教师等名称能否在系统中匹配。"
    >
      <ul class="check-list">
        <li>模板表头必须来自本页下载的最新模板。</li>
        <li>学号、工号、考试名称、科目、班级等关键列不要留空。</li>
        <li>同一学生同一科目、同一教师工号等重复行需先清理。</li>
        <li>无法匹配的年级 / 班级 / 学科 / 教师，先到基础数据或对应业务页维护。</li>
      </ul>
    </AppSectionCard>

    <AppSectionCard
      title="模板与上传入口"
      description="下载系统模板后，进入对应业务页完成上传、预检和结果确认。"
    >
      <div class="template-grid-shell" v-loading="loading && !payload.templates.length">
        <div v-if="payload.templates.length" class="template-grid">
          <article v-for="item in payload.templates" :key="item.job_type" class="template-card">
            <div>
              <strong>{{ item.job_type_label }}</strong>
              <p>{{ item.guidance }}</p>
            </div>
            <div class="template-actions">
              <el-button link type="primary" :disabled="loading" @click="openFile(item.download_url)">下载模板</el-button>
              <el-button link :disabled="loading" @click="router.push(item.business_path)">进入上传</el-button>
            </div>
          </article>
        </div>
        <el-empty v-else-if="!loading" :description="templateEmptyDescription">
          <el-button type="primary" plain :loading="loading" @click="loadBatches">重新加载模板</el-button>
        </el-empty>
      </div>
    </AppSectionCard>

    <AppTableShell
      title="导入批次"
      description="聚合通用导入任务、成绩批次、课表批次和评教批次；有错误报告的批次可直接下载。"
    >
      <template #actions>
        <div class="filter-row">
          <el-select
            v-model="filters.jobType"
            clearable
            :disabled="batchFiltersDisabled"
            placeholder="导入类型"
            style="width: 180px"
            @change="loadBatches"
          >
            <el-option
              v-for="item in payload.templates"
              :key="item.job_type"
              :label="item.job_type_label"
              :value="item.job_type"
            />
          </el-select>
          <el-select
            v-model="filters.status"
            clearable
            :disabled="batchFiltersDisabled"
            placeholder="状态"
            style="width: 150px"
            @change="loadBatches"
          >
            <el-option label="成功" value="success" />
            <el-option label="部分成功" value="partially_failed" />
            <el-option label="失败" value="failed" />
            <el-option label="处理中" value="running" />
            <el-option label="已回滚" value="rolled_back" />
          </el-select>
          <el-button v-if="hasBatchFilters" plain :disabled="loading" @click="clearBatchFilters">清空筛选</el-button>
        </div>
      </template>

      <el-table :data="payload.batches" stripe row-key="id" v-loading="loading">
          <el-table-column label="类型" min-width="140">
            <template #default="{ row }">
              <strong>{{ row.job_type_label }}</strong>
              <p class="table-subtext">{{ row.source_type_label }}</p>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="importCenterStatusType(row.status)" effect="light">
                {{ formatImportCenterStatus(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="来源文件" prop="source_filename" min-width="180" />
          <el-table-column label="摘要" min-width="240">
            <template #default="{ row }">
              {{ buildImportCenterRowSummary(row) }}
            </template>
          </el-table-column>
          <el-table-column label="开始时间" prop="started_at" min-width="170" />
          <el-table-column label="结束时间" prop="finished_at" min-width="170" />
          <el-table-column label="操作" width="250" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                :loading="loadingDetailBatchId === row.id"
                :disabled="detailLoading && loadingDetailBatchId !== row.id"
                @click="openDetail(row)"
              >
                详情
              </el-button>
              <el-button
                link
                type="primary"
                :disabled="!buildImportCenterErrorReportUrl(row)"
                @click="openErrorReport(row)"
              >
                错误报告
              </el-button>
              <el-button link @click="router.push(row.business_path)">业务页</el-button>
              <el-button link type="warning" @click="openRollbackHint(row)">撤销说明</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="importBatchEmptyDescription">
              <el-button
                v-if="loadError"
                type="primary"
                plain
                :loading="loading"
                @click="loadBatches"
              >
                重新刷新
              </el-button>
              <el-button v-else-if="hasBatchFilters" plain @click="clearBatchFilters">清空筛选</el-button>
            </el-empty>
          </template>
      </el-table>
    </AppTableShell>

    <el-drawer v-model="detailVisible" title="导入批次详情" size="520px" @closed="resetDetailDrawer">
      <div class="detail-stack detail-drawer-body" v-loading="detailLoading">
        <el-alert
          v-if="detailError"
          type="error"
          show-icon
          :closable="false"
          title="导入详情加载失败"
        >
          <template #default>
            <p class="alert-detail">{{ detailError }}</p>
            <div class="action-row toolbar-row">
              <el-button size="small" type="danger" plain :loading="detailLoading" @click="retryDetail">重新读取详情</el-button>
              <el-button size="small" plain :disabled="!activeDetailBatch" @click="activeDetailBatch && router.push(activeDetailBatch.business_path)">
                回到业务页
              </el-button>
            </div>
          </template>
        </el-alert>

        <template v-if="selectedDetail">
          <el-alert
            :title="selectedDetail.batch.rollback_hint"
            type="warning"
            show-icon
            :closable="false"
          />
          <el-descriptions :column="1" border>
            <el-descriptions-item label="导入类型">{{ selectedDetail.batch.job_type_label }}</el-descriptions-item>
            <el-descriptions-item label="批次来源">{{ selectedDetail.batch.source_type_label }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="importCenterStatusType(selectedDetail.batch.status)" effect="light">
                {{ formatImportCenterStatus(selectedDetail.batch.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="来源文件">{{ selectedDetail.batch.source_filename ?? "-" }}</el-descriptions-item>
            <el-descriptions-item label="行数摘要">{{ buildImportCenterRowSummary(selectedDetail.batch) }}</el-descriptions-item>
            <el-descriptions-item label="详情">{{ selectedDetail.batch.detail_summary }}</el-descriptions-item>
          </el-descriptions>

        <section v-if="selectedDetail.error_items.length" class="detail-section">
          <h4>错误预览</h4>
          <div class="error-item-list">
            <article v-for="item in selectedDetail.error_items" :key="formatImportCenterErrorItem(item)" class="error-item-card">
              <strong>{{ item.row_number ? `第 ${item.row_number} 行` : "未知行" }}</strong>
              <p>{{ formatImportCenterErrorItem(item) }}</p>
            </article>
          </div>
        </section>

        <section v-else-if="selectedDetail.error_preview.length" class="detail-section">
          <h4>错误预览</h4>
          <ul>
            <li v-for="item in selectedDetail.error_preview" :key="item">{{ item }}</li>
          </ul>
        </section>

        <section v-if="selectedDetail.notice_preview.length" class="detail-section">
          <h4>导入提示</h4>
          <ul>
            <li v-for="item in selectedDetail.notice_preview" :key="item">{{ item }}</li>
          </ul>
        </section>

        <section class="detail-section">
          <h4>撤销处理步骤</h4>
          <ol>
            <li v-for="item in selectedDetail.rollback_steps" :key="item">{{ item }}</li>
          </ol>
        </section>

        <section class="detail-section">
          <h4>审计日志</h4>
          <el-empty v-if="!selectedDetail.audit_logs.length" description="暂无关联审计日志" />
          <div v-else class="audit-list">
            <article v-for="log in selectedDetail.audit_logs" :key="log.id" class="audit-item">
              <strong>{{ log.module }} / {{ log.action }}</strong>
              <span>{{ log.created_at }}</span>
              <p>{{ formatImportCenterDetails(log.detail_json) }}</p>
            </article>
          </div>
        </section>

        <div class="action-row">
          <el-button
            v-if="selectedDetail.batch.error_report_path"
            type="primary"
            plain
            @click="openErrorReport(selectedDetail.batch)"
          >
            下载错误报告
          </el-button>
          <el-button @click="router.push(selectedDetail.batch.business_path)">回到业务页</el-button>
          <el-button @click="router.push('/system-tools')">备份恢复</el-button>
        </div>
        </template>
        <el-empty
          v-else-if="!detailLoading && !detailError"
          description="请选择一个导入批次查看详情。"
        />
      </div>
    </el-drawer>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";
import { useRouter } from "vue-router";

import { apiRequest, openFile } from "../api/client";
import {
  AppPage,
  AppSectionCard,
  AppStatGrid,
  AppTableShell,
  type PageMetaItem,
  type StatCardItem,
} from "../components/ui";
import {
  buildImportCenterErrorReportUrl,
  buildImportCenterRowSummary,
  formatImportCenterDetails,
  formatImportCenterErrorItem,
  formatImportCenterStatus,
  formatLatestBackupLabel,
  importCenterTrialRunSteps,
  importCenterStatusType,
  type ImportCenterBatch,
  type ImportCenterBatchDetail,
  type ImportCenterResponse,
} from "../utils/importCenter";
import { formatUserActionError } from "../utils/userFeedback";

const router = useRouter();
const loading = ref(false);
const detailLoading = ref(false);
const detailVisible = ref(false);
const activeDetailBatch = ref<ImportCenterBatch | null>(null);
const loadingDetailBatchId = ref("");
const selectedDetail = ref<ImportCenterBatchDetail | null>(null);
const loadError = ref("");
const detailError = ref("");
const filters = reactive({
  jobType: "",
  status: "",
});
const payload = reactive<ImportCenterResponse>({
  generated_at: "",
  summary: {
    total_batches: 0,
    failed_batches: 0,
    partial_batches: 0,
    error_report_count: 0,
  },
  latest_backup: null,
  templates: [],
  batches: [],
});

const batchFiltersDisabled = computed(() => loading.value || Boolean(loadError.value && !payload.templates.length));
const reviewBatchCount = computed(() => payload.summary.failed_batches + payload.summary.partial_batches);
const latestBackupLabel = computed(() => formatLatestBackupLabel(payload.latest_backup));
const hasBatchFilters = computed(() => Boolean(filters.jobType || filters.status));
const templateEmptyDescription = computed(() => (
  loadError.value
    ? "模板入口暂时加载失败，请重新加载导入中心。"
    : "当前没有可用导入模板；请确认本地服务和导入中心接口可用。"
));
const importBatchEmptyDescription = computed(() => {
  if (loadError.value && !payload.batches.length) return "导入批次暂时加载失败，请重新刷新。";
  if (hasBatchFilters.value) return "当前筛选条件下没有导入批次，可清空筛选或回到业务页完成上传。";
  return "当前没有导入批次。可先下载模板，到对应业务页完成上传；如果刚导入过，请点击刷新。";
});
const importPageMeta = computed<PageMetaItem[]>(() => [
  { label: "批次", value: loadError.value ? "加载失败" : payload.summary.total_batches },
  { label: "需复核", value: loadError.value ? "加载失败" : reviewBatchCount.value },
  { label: "最近备份", value: loadError.value ? "加载失败" : latestBackupLabel.value },
]);
const importStatCards = computed<StatCardItem[]>(() => [
  {
    label: "导入批次",
    value: loadError.value ? "加载失败" : payload.summary.total_batches,
    help: loadError.value ? "请重新刷新导入中心。" : "系统记录的导入任务总数。",
    tone: loadError.value ? "danger" : "primary",
    loading: loading.value && !loadError.value,
  },
  {
    label: "需复核批次",
    value: loadError.value ? "加载失败" : reviewBatchCount.value,
    help: loadError.value ? "当前无法判断需复核批次。" : "失败或部分成功的批次建议优先处理。",
    tone: loadError.value ? "danger" : reviewBatchCount.value ? "warning" : "success",
    loading: loading.value && !loadError.value,
  },
  {
    label: "错误报告",
    value: loadError.value ? "加载失败" : payload.summary.error_report_count,
    help: loadError.value ? "重新刷新后再下载错误报告。" : "可下载并回到业务页修正的数据问题。",
    tone: loadError.value ? "danger" : payload.summary.error_report_count ? "danger" : "neutral",
    loading: loading.value && !loadError.value,
  },
  {
    label: "模板入口",
    value: loadError.value ? "加载失败" : payload.templates.length,
    help: loadError.value ? "模板入口已清空，请重新刷新。" : "覆盖当前已统一治理的导入类型。",
    tone: loadError.value ? "danger" : "info",
    loading: loading.value && !loadError.value,
  },
]);

function createEmptyImportCenterResponse(): ImportCenterResponse {
  return {
    generated_at: "",
    summary: {
      total_batches: 0,
      failed_batches: 0,
      partial_batches: 0,
      error_report_count: 0,
    },
    latest_backup: null,
    templates: [],
    batches: [],
  };
}

function resetPayload(): void {
  Object.assign(payload, createEmptyImportCenterResponse());
}

async function loadBatches(): Promise<void> {
  try {
    loading.value = true;
    loadError.value = "";
    const params = new URLSearchParams({ limit: "120" });
    if (filters.jobType) params.set("job_type", filters.jobType);
    if (filters.status) params.set("status", filters.status);
    const response = await apiRequest<ImportCenterResponse>(`/api/import-center/batches?${params.toString()}`);
    Object.assign(payload, response);
  } catch (error) {
    resetPayload();
    loadError.value = formatUserActionError("刷新导入中心", error, "确认本地服务已启动，再点击“重新刷新”；如果是刚导入失败，请回到业务页检查模板。");
    ElMessage.error(loadError.value);
  } finally {
    loading.value = false;
  }
}

function clearBatchFilters(): void {
  filters.jobType = "";
  filters.status = "";
  void loadBatches();
}

async function openDetail(batch: ImportCenterBatch): Promise<void> {
  const requestedBatchId = batch.id;
  activeDetailBatch.value = batch;
  detailVisible.value = true;
  detailLoading.value = true;
  loadingDetailBatchId.value = requestedBatchId;
  detailError.value = "";
  selectedDetail.value = null;
  try {
    const response = await apiRequest<ImportCenterBatchDetail>(
      `/api/import-center/batches/${batch.source_type}/${batch.numeric_id}`,
    );
    if (activeDetailBatch.value?.id !== requestedBatchId) return;
    selectedDetail.value = response;
  } catch (error) {
    if (activeDetailBatch.value?.id !== requestedBatchId) return;
    detailError.value = formatUserActionError("读取导入详情", error, "先刷新批次列表；如果仍失败，请下载错误报告或到业务页重新查看本次导入。");
  } finally {
    if (activeDetailBatch.value?.id === requestedBatchId) {
      detailLoading.value = false;
      loadingDetailBatchId.value = "";
    }
  }
}

function retryDetail(): void {
  if (!activeDetailBatch.value) return;
  void openDetail(activeDetailBatch.value);
}

function resetDetailDrawer(): void {
  activeDetailBatch.value = null;
  selectedDetail.value = null;
  detailError.value = "";
  detailLoading.value = false;
  loadingDetailBatchId.value = "";
}

function openErrorReport(batch: ImportCenterBatch): void {
  const url = buildImportCenterErrorReportUrl(batch);
  if (!url) return;
  openFile(url);
}

async function openRollbackHint(batch: ImportCenterBatch): Promise<void> {
  await ElMessageBox.alert(
    batch.rollback_hint,
    `${batch.job_type_label}撤销说明`,
    {
      type: "warning",
      confirmButtonText: "知道了",
    },
  );
}

onMounted(loadBatches);
</script>

<style scoped>
.page-alert {
  margin-top: -4px;
}

.toolbar-row {
  margin-top: 10px;
}

.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) repeat(3, minmax(0, 0.75fr));
  gap: 16px;
}

.trial-run-panel {
  padding: 20px;
}

.trial-step-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.trial-step-card {
  display: grid;
  align-content: start;
  gap: 8px;
  min-height: 142px;
  padding: 14px;
  border: 1px solid rgba(123, 141, 158, 0.22);
  border-radius: 8px;
  background: rgba(248, 251, 253, 0.82);
}

.trial-step-card strong {
  color: #1e3448;
}

.trial-step-card p {
  margin: 0;
  color: #61778b;
  line-height: 1.6;
}

.rollback-alert {
  margin-top: 14px;
}

.overview-panel,
.overview-card,
.panel-block {
  padding: 20px;
}

.overview-panel,
.overview-card {
  padding: 24px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}

.template-grid-shell {
  min-height: 120px;
}

.template-card {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  min-height: 112px;
  padding: 14px;
  border: 1px solid rgba(123, 141, 158, 0.22);
  border-radius: 8px;
  background: rgba(248, 251, 253, 0.78);
}

.template-card strong {
  color: #1e3448;
}

.template-card p,
.table-subtext {
  margin: 4px 0 0;
  color: #6c8194;
  line-height: 1.6;
}

.check-list {
  margin: 12px 0 0;
  padding-left: 18px;
  color: #52687c;
  line-height: 1.8;
}

.template-actions {
  display: grid;
  align-content: start;
  justify-items: end;
  min-width: 84px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

.detail-stack {
  display: grid;
  gap: 16px;
}

.detail-drawer-body {
  min-height: 220px;
  align-content: start;
}

.alert-detail {
  margin: 0;
  color: #52687c;
  line-height: 1.6;
}

.detail-section {
  display: grid;
  gap: 8px;
}

.detail-section h4 {
  margin: 0;
  color: #1e3448;
}

.detail-section ul,
.detail-section ol {
  margin: 0;
  padding-left: 20px;
  color: #52687c;
  line-height: 1.8;
}

.error-item-list {
  display: grid;
  gap: 10px;
}

.error-item-card {
  padding: 12px;
  border: 1px solid rgba(218, 125, 94, 0.24);
  border-radius: 8px;
  background: rgba(255, 248, 244, 0.9);
}

.error-item-card strong {
  color: #994b2f;
}

.error-item-card p {
  margin: 6px 0 0;
  color: #52687c;
  line-height: 1.6;
}

.audit-list {
  display: grid;
  gap: 10px;
}

.audit-item {
  padding: 12px;
  border: 1px solid rgba(123, 141, 158, 0.22);
  border-radius: 8px;
  background: #fff;
}

.audit-item strong,
.audit-item span,
.audit-item p {
  display: block;
}

.audit-item span {
  margin-top: 4px;
  color: #6c8194;
  font-size: 13px;
}

.audit-item p {
  margin: 6px 0 0;
  color: #52687c;
  line-height: 1.6;
}

@media (max-width: 960px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .template-card {
    display: grid;
  }

  .template-actions {
    justify-items: start;
  }
}
</style>
