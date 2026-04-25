<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">数据治理 / 导入中心</div>
        <h2 class="page-title">统一查看模板、批次、错误报告和撤销说明</h2>
        <p class="page-subtitle">
          聚合学生、教师、成绩、课表、录取数据、招生计划和评教导入历史，便于导入后回看结果、下载错误报告并回到对应业务页面修正。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>批次</strong>{{ payload.summary.total_batches }}</span>
          <span class="page-chip"><strong>部分成功</strong>{{ payload.summary.partial_batches }}</span>
          <span class="page-chip"><strong>失败</strong>{{ payload.summary.failed_batches }}</span>
          <span class="page-chip"><strong>错误报告</strong>{{ payload.summary.error_report_count }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="router.push('/system-tools')">备份与审计</el-button>
        <el-button type="primary" :loading="loading" @click="loadBatches">刷新</el-button>
      </div>
    </header>

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

    <section class="overview-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">导入流程</div>
        <h3>先下载模板，再回到业务页上传</h3>
        <p>
          这里不替代学生、考试、课表等业务页面的导入动作，而是把模板、批次结果、错误报告和撤销边界集中起来，方便非程序员回看最近发生了什么。
        </p>
      </article>
      <article class="soft-card overview-card tone-blue">
        <span>模板入口</span>
        <strong>{{ payload.templates.length }}</strong>
        <p>覆盖当前已统一治理的导入类型。</p>
      </article>
      <article class="soft-card overview-card tone-amber">
        <span>需复核批次</span>
        <strong>{{ reviewBatchCount }}</strong>
        <p>失败或部分成功的批次建议优先处理。</p>
      </article>
      <article class="soft-card overview-card tone-slate">
        <span>自动回滚</span>
        <strong>关闭</strong>
        <p>当前只给出撤销说明，避免误删业务数据。</p>
      </article>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>模板与上传入口</h3>
          <p>下载系统模板后，进入对应业务页完成上传、预检和结果确认。</p>
        </div>
      </div>
      <div class="template-grid">
        <article v-for="item in payload.templates" :key="item.job_type" class="template-card">
          <div>
            <strong>{{ item.job_type_label }}</strong>
            <p>{{ item.guidance }}</p>
          </div>
          <div class="template-actions">
            <el-button link type="primary" @click="openFile(item.download_url)">下载模板</el-button>
            <el-button link @click="router.push(item.business_path)">进入上传</el-button>
          </div>
        </article>
      </div>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>导入批次</h3>
          <p>聚合通用导入任务、成绩批次、课表批次和评教批次；有错误报告的批次可直接下载。</p>
        </div>
        <div class="filter-row">
          <el-select v-model="filters.jobType" clearable placeholder="导入类型" style="width: 180px" @change="loadBatches">
            <el-option
              v-for="item in payload.templates"
              :key="item.job_type"
              :label="item.job_type_label"
              :value="item.job_type"
            />
          </el-select>
          <el-select v-model="filters.status" clearable placeholder="状态" style="width: 150px" @change="loadBatches">
            <el-option label="成功" value="success" />
            <el-option label="部分成功" value="partially_failed" />
            <el-option label="失败" value="failed" />
            <el-option label="处理中" value="running" />
            <el-option label="已回滚" value="rolled_back" />
          </el-select>
        </div>
      </div>

      <div class="table-shell">
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
              <el-button link type="primary" @click="openDetail(row)">详情</el-button>
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
        </el-table>
      </div>
      <el-empty
        v-if="!loading && !payload.batches.length"
        description="当前没有符合条件的导入批次。可先下载模板，到对应业务页完成上传；如果刚导入过，请点击刷新。"
      />
    </section>

    <el-drawer v-model="detailVisible" title="导入批次详情" size="520px">
      <div v-if="selectedDetail" class="detail-stack">
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

        <section v-if="selectedDetail.error_preview.length" class="detail-section">
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
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";
import { useRouter } from "vue-router";

import { apiRequest, openFile } from "../api/client";
import {
  buildImportCenterErrorReportUrl,
  buildImportCenterRowSummary,
  formatImportCenterDetails,
  formatImportCenterStatus,
  importCenterStatusType,
  type ImportCenterBatch,
  type ImportCenterBatchDetail,
  type ImportCenterResponse,
} from "../utils/importCenter";
import { formatUserActionError } from "../utils/userFeedback";

const router = useRouter();
const loading = ref(false);
const detailVisible = ref(false);
const selectedDetail = ref<ImportCenterBatchDetail | null>(null);
const loadError = ref("");
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
  templates: [],
  batches: [],
});

const reviewBatchCount = computed(() => payload.summary.failed_batches + payload.summary.partial_batches);

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
    loadError.value = formatUserActionError("刷新导入中心", error, "确认本地服务已启动，再点击“重新刷新”；如果是刚导入失败，请回到业务页检查模板。");
    ElMessage.error(loadError.value);
  } finally {
    loading.value = false;
  }
}

async function openDetail(batch: ImportCenterBatch): Promise<void> {
  try {
    selectedDetail.value = await apiRequest<ImportCenterBatchDetail>(
      `/api/import-center/batches/${batch.source_type}/${batch.numeric_id}`,
    );
    detailVisible.value = true;
  } catch (error) {
    ElMessage.error(formatUserActionError("读取导入详情", error, "先刷新批次列表；如果仍失败，请下载错误报告或到业务页重新查看本次导入。"));
  }
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
