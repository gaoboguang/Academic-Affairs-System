<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">系统层 / 设置与修复</div>
        <h2 class="page-title">系统设置</h2>
        <p class="page-subtitle">
          统一管理参数配置、模板、数据修复、备份恢复和审计日志，把系统层动作集中到一个页面。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>配置项</strong>{{ configItemCount }}</span>
          <span class="page-chip"><strong>模板</strong>{{ templates.length }}</span>
          <span class="page-chip"><strong>高风险问题</strong>{{ repairErrorCount }}</span>
          <span class="page-chip"><strong>最近备份</strong>{{ latestBackupName }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button type="primary" :loading="creatingBackup" @click="createBackup">立即备份</el-button>
        <el-switch
          v-model="autoBackupBeforeRestore"
          inline-prompt
          active-text="恢复前自动备份"
          inactive-text="直接恢复"
        />
      </div>
    </header>

    <section class="overview-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">系统安全</div>
        <h3>先备份，再修复，再执行恢复</h3>
        <p>
          参数、模板、数据修复、备份和审计日志放在同一页，核心目标是让每次系统级动作都可追溯、可回滚。
        </p>
      </article>
      <article v-for="item in overviewCards" :key="item.label" class="soft-card overview-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </section>

    <section class="metric-grid">
      <article class="soft-card stat-card">
        <span>配置项</span>
        <strong>{{ configItemCount }}</strong>
      </article>
      <article class="soft-card stat-card">
        <span>模板文件</span>
        <strong>{{ templates.length }}</strong>
      </article>
      <article class="soft-card stat-card">
        <span>数据问题</span>
        <strong>{{ repairScan?.issues.length ?? 0 }}</strong>
      </article>
      <article class="soft-card stat-card">
        <span>备份数量</span>
        <strong>{{ backups.length }}</strong>
      </article>
    </section>

    <el-tabs>
      <el-tab-pane label="参数配置">
        <section v-for="group in configGroups" :key="group.config_group" class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>{{ group.title }}</h3>
              <p>{{ group.config_group }}</p>
            </div>
            <el-button type="primary" @click="saveGroup(group)">保存本组</el-button>
          </div>
          <div class="config-grid">
            <article v-for="item in group.items" :key="item.config_key" class="config-card">
              <div class="config-label">{{ item.config_key }}</div>
              <p>{{ item.description ?? "未填写说明" }}</p>
              <el-switch
                v-if="item.value_type === 'bool'"
                v-model="item.draft_value"
              />
              <el-input
                v-else-if="item.value_type === 'json'"
                v-model="item.draft_value"
                type="textarea"
                :rows="5"
              />
              <el-input
                v-else
                v-model="item.draft_value"
              />
            </article>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="模板管理">
        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>导入模板</h3>
              <p>统一查看当前运行目录里的模板文件，便于学生、教师、成绩、课表等导入前下载。</p>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="templates" stripe>
              <el-table-column label="模板名" prop="name" min-width="220" />
              <el-table-column label="文件名" prop="file_name" min-width="220" />
              <el-table-column label="更新时间" prop="updated_at" min-width="180" />
              <el-table-column label="大小" width="120">
                <template #default="{ row }">
                  {{ formatBytes(row.file_size) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openFile(row.download_url)">下载</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-if="!templates.length" description="暂无模板文件" />
        </section>
      </el-tab-pane>

      <el-tab-pane label="数据修复">
        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>修复扫描</h3>
              <p>优先修正年级班级不一致、班级人数不一致、学籍历史缺失等问题。</p>
            </div>
            <el-button @click="loadRepairScan">重新扫描</el-button>
          </div>
          <div v-if="repairScan?.issues.length" class="repair-grid">
            <article v-for="issue in repairScan.issues" :key="issue.code" class="repair-card">
              <div class="repair-head">
                <el-tag :type="issue.severity === 'error' ? 'danger' : 'warning'" effect="light">
                  {{ issue.severity === "error" ? "高风险" : "提醒" }}
                </el-tag>
                <strong>{{ issue.count }}</strong>
              </div>
              <h4>{{ issue.title }}</h4>
              <p>{{ issue.summary }}</p>
              <div v-if="issue.samples.length" class="sample-list">
                <span v-for="sample in issue.samples" :key="sample">{{ sample }}</span>
              </div>
            </article>
          </div>
          <el-empty v-else description="当前没有待处理的数据问题" />

          <div class="section-split"></div>
          <div class="section-head compact">
            <div>
              <h3>修复动作</h3>
              <p>仅提供可追溯、相对安全的自动修复；高风险问题仍需人工核对。</p>
            </div>
          </div>
          <div class="action-list">
            <div v-for="action in repairScan?.actions ?? []" :key="action.code" class="action-card">
              <div>
                <strong>{{ action.title }}</strong>
                <p>{{ action.description }}</p>
              </div>
              <el-button
                type="primary"
                :disabled="!action.enabled"
                :loading="repairingAction === action.code"
                @click="executeRepair(action.code)"
              >
                执行
              </el-button>
            </div>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="备份恢复">
        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>备份记录</h3>
              <p>备份包含数据库、上传附件、模板和配置文件。</p>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="backups" stripe>
              <el-table-column label="备份名称" prop="backup_name" min-width="220" />
              <el-table-column label="文件大小" width="120">
                <template #default="{ row }">
                  {{ formatBytes(row.file_size) }}
                </template>
              </el-table-column>
              <el-table-column label="创建时间" prop="created_at" min-width="170" />
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="backupStatusType(row.status)" effect="light">
                    {{ formatBackupStatus(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="180" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openFile(row.download_url)">下载</el-button>
                  <el-button link type="danger" :loading="restoringBackupId === row.id" @click="restoreBackup(row.id)">
                    恢复
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty v-if="!backups.length" description="暂无备份记录" />
        </section>
      </el-tab-pane>

      <el-tab-pane label="操作日志">
        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>审计日志</h3>
              <p>记录导入、导出、备份、恢复、配置变更与关键数据修复动作。</p>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="auditLogs" stripe>
              <el-table-column label="时间" prop="created_at" min-width="170" />
              <el-table-column label="模块" prop="module" width="120" />
              <el-table-column label="动作" prop="action" width="160" />
              <el-table-column label="目标" min-width="140">
                <template #default="{ row }">
                  {{ formatAuditTargetType(row.target_type) }} / {{ row.target_id ?? "-" }}
                </template>
              </el-table-column>
              <el-table-column label="详情" min-width="260">
                <template #default="{ row }">
                  {{ formatDetails(row.detail_json) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";

import { apiRequest, openFile } from "../api/client";

interface BackupRecord {
  id: number;
  backup_name: string;
  file_size: number;
  created_at: string;
  status: string;
  download_url: string;
}

interface AuditLog {
  id: number;
  module: string;
  action: string;
  target_type?: string | null;
  target_id?: string | null;
  detail_json?: Record<string, unknown> | null;
  created_at: string;
}

interface ConfigItemRow {
  id: number;
  config_group: string;
  config_key: string;
  config_value: string;
  parsed_value: unknown;
  value_type: string;
  description?: string | null;
  draft_value: string | boolean;
}

interface ConfigGroup {
  config_group: string;
  title: string;
  items: ConfigItemRow[];
}

interface TemplateItem {
  name: string;
  file_name: string;
  file_size: number;
  updated_at: string;
  download_url: string;
}

interface RepairIssue {
  code: string;
  title: string;
  severity: string;
  count: number;
  summary: string;
  samples: string[];
}

interface RepairAction {
  code: string;
  title: string;
  description: string;
  enabled: boolean;
}

interface RepairScan {
  generated_at: string;
  issues: RepairIssue[];
  actions: RepairAction[];
}

const configGroups = ref<ConfigGroup[]>([]);
const templates = ref<TemplateItem[]>([]);
const repairScan = ref<RepairScan | null>(null);
const backups = ref<BackupRecord[]>([]);
const auditLogs = ref<AuditLog[]>([]);
const creatingBackup = ref(false);
const restoringBackupId = ref<number | null>(null);
const repairingAction = ref<string | null>(null);
const autoBackupBeforeRestore = ref(true);

const configItemCount = computed(
  () => configGroups.value.reduce((sum, group) => sum + group.items.length, 0),
);
const repairErrorCount = computed(
  () => repairScan.value?.issues.filter((item) => item.severity === "error").length ?? 0,
);
const latestBackupName = computed(() => backups.value[0]?.backup_name ?? "暂无");
const overviewCards = computed(() => [
  {
    label: "修复动作",
    value: repairScan.value?.actions.length ?? 0,
    help: "当前可直接执行的自动修复动作数量。",
    tone: "tone-blue",
  },
  {
    label: "备份记录",
    value: backups.value.length,
    help: "恢复前建议确认最近一次可用备份。",
    tone: "tone-amber",
  },
  {
    label: "审计日志",
    value: auditLogs.value.length,
    help: "最近 100 条系统级动作都会记录在这里。",
    tone: "tone-slate",
  },
]);

function formatBackupStatus(status: string): string {
  const mapping: Record<string, string> = {
    success: "成功",
    processing: "处理中",
    failed: "失败",
  };
  return mapping[status] ?? status;
}

function backupStatusType(status: string): "success" | "info" | "danger" {
  if (status === "success") return "success";
  if (status === "failed") return "danger";
  return "info";
}

function formatAuditTargetType(targetType?: string | null): string {
  if (!targetType) return "-";
  const mapping: Record<string, string> = {
    config_item: "配置项",
    backup_record: "备份记录",
    import_job: "导入任务",
    student: "学生",
    teacher: "教师",
    exam: "考试",
    recommendation_scheme: "推荐方案",
    evaluation_batch: "评教批次",
    workload_result: "工作量结果",
  };
  return mapping[targetType] ?? targetType;
}

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}

function formatDetails(value?: Record<string, unknown> | null): string {
  if (!value) return "-";
  return Object.entries(value)
    .map(([key, item]) => `${key}=${item}`)
    .join(" / ");
}

function formatDraftValue(item: Omit<ConfigItemRow, "draft_value">): string | boolean {
  if (item.value_type === "bool") {
    return Boolean(item.parsed_value);
  }
  if (item.value_type === "json") {
    if (typeof item.parsed_value === "string") return item.parsed_value;
    return JSON.stringify(item.parsed_value ?? {}, null, 2);
  }
  return String(item.parsed_value ?? item.config_value ?? "");
}

async function loadConfigGroups(): Promise<void> {
  const payload = await apiRequest<Array<Omit<ConfigGroup, "items"> & { items: Omit<ConfigItemRow, "draft_value">[] }>>(
    "/api/system/config-groups",
  );
  configGroups.value = payload.map((group) => ({
    ...group,
    items: group.items.map((item) => ({
      ...item,
      draft_value: formatDraftValue(item),
    })),
  }));
  const restoreConfig = configGroups.value
    .flatMap((group) => group.items)
    .find((item) => item.config_key === "auto_backup_before_restore");
  if (restoreConfig?.value_type === "bool") {
    autoBackupBeforeRestore.value = Boolean(restoreConfig.draft_value);
  }
}

async function loadTemplates(): Promise<void> {
  templates.value = await apiRequest<TemplateItem[]>("/api/system/templates");
}

async function loadRepairScan(): Promise<void> {
  repairScan.value = await apiRequest<RepairScan>("/api/system/data-repair/scan");
}

async function loadBackups(): Promise<void> {
  backups.value = await apiRequest<BackupRecord[]>("/api/system/backups");
}

async function loadAuditLogs(): Promise<void> {
  auditLogs.value = await apiRequest<AuditLog[]>("/api/system/audit-logs?limit=100");
}

async function reloadMeta(): Promise<void> {
  await Promise.all([loadTemplates(), loadRepairScan(), loadBackups(), loadAuditLogs()]);
}

async function saveGroup(group: ConfigGroup): Promise<void> {
  try {
    const payload = group.items.map((item) => ({
      config_group: item.config_group,
      config_key: item.config_key,
      value_type: item.value_type,
      description: item.description ?? undefined,
      config_value: item.value_type === "json" ? JSON.parse(String(item.draft_value || "{}")) : item.draft_value,
    }));
    await apiRequest("/api/system/config-items", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    ElMessage.success(`${group.title}已保存`);
    await loadConfigGroups();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function executeRepair(actionCode: string): Promise<void> {
  try {
    const action = repairScan.value?.actions.find((item) => item.code === actionCode);
    await ElMessageBox.confirm(
      `${action?.description ?? "该修复会直接调整当前数据。"} 建议先确认最近备份可用。是否继续？`,
      `执行修复：${action?.title ?? actionCode}`,
      { type: "warning" },
    );
    repairingAction.value = actionCode;
    const result = await apiRequest<{ message: string }>("/api/system/data-repair/execute", {
      method: "POST",
      body: JSON.stringify({ action_code: actionCode }),
    });
    ElMessage.success(result.message);
    await Promise.all([loadRepairScan(), loadAuditLogs()]);
  } catch (error) {
    if (error === "cancel" || error === "close") return;
    ElMessage.error((error as Error).message);
  } finally {
    repairingAction.value = null;
  }
}

async function createBackup(): Promise<void> {
  try {
    creatingBackup.value = true;
    const result = await apiRequest<{ message: string }>("/api/system/backup", { method: "POST" });
    await Promise.all([loadBackups(), loadAuditLogs()]);
    ElMessage.success(result.message);
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    creatingBackup.value = false;
  }
}

async function restoreBackup(backupId: number): Promise<void> {
  try {
    await ElMessageBox.confirm(
      "恢复会覆盖当前数据库和附件。建议确保其他页面已停止操作。是否继续？",
      "恢复备份",
      { type: "warning" },
    );
    restoringBackupId.value = backupId;
    const result = await apiRequest<{ message: string }>("/api/system/restore", {
      method: "POST",
      body: JSON.stringify({
        backup_id: backupId,
        auto_backup_current: autoBackupBeforeRestore.value,
      }),
    });
    await Promise.all([loadBackups(), loadAuditLogs()]);
    ElMessage.success(result.message);
  } catch (error) {
    if (error === "cancel" || error === "close") return;
    ElMessage.error((error as Error).message);
  } finally {
    restoringBackupId.value = null;
  }
}

onMounted(async () => {
  try {
    await Promise.all([loadConfigGroups(), reloadMeta()]);
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
.overview-card,
.stat-card,
.panel-block {
  padding: 20px;
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

.stat-card span {
  display: block;
  color: #6d8092;
  font-size: 13px;
}

.stat-card strong {
  display: block;
  margin-top: 10px;
  color: #1f3245;
  font-size: 28px;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-head.compact {
  margin-bottom: 14px;
}

.section-head h3 {
  margin: 0;
}

.section-head p {
  margin: 6px 0 0;
  color: #60748a;
  line-height: 1.6;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}

.config-card,
.repair-card,
.action-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(114, 132, 150, 0.14);
  background: rgba(255, 255, 255, 0.8);
}

.config-label {
  font-weight: 700;
  color: #233547;
}

.config-card p,
.repair-card p,
.action-card p {
  margin: 8px 0 12px;
  color: #617487;
  line-height: 1.6;
}

.repair-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.repair-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.repair-card h4 {
  margin: 14px 0 8px;
}

.sample-list {
  display: grid;
  gap: 6px;
}

.sample-list span {
  color: #54687a;
  font-size: 13px;
}

.section-split {
  height: 1px;
  margin: 24px 0;
  background: rgba(120, 138, 156, 0.12);
}

.action-list {
  display: grid;
  gap: 12px;
}

.action-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

@media (max-width: 1180px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .action-card {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
