<template>
  <AppPage
    title="系统设置"
    eyebrow="系统层 / 设置与修复"
    description="统一管理参数配置、模板、数据修复、备份恢复和审计日志，让系统级动作集中、可追溯、可回滚。"
    :meta="systemPageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button type="primary" :loading="creatingBackup" @click="createBackup">立即备份</el-button>
        <el-switch
          v-model="autoBackupBeforeRestore"
          inline-prompt
          active-text="恢复前自动备份"
          inactive-text="直接恢复"
        />
      </div>
    </template>

    <AppStatGrid :items="overviewCards" :columns="4" />

    <section class="soft-card panel-block safety-panel">
      <div class="section-head">
        <div>
          <h3>本地数据保险箱</h3>
          <p>查看主库路径、目录大小、最近备份/恢复、SQLite 完整性和迁移版本。</p>
        </div>
        <el-button @click="loadSafetyStatus">重新检查</el-button>
      </div>
      <div class="safety-grid">
        <article v-for="item in safetyCards" :key="item.label" class="safety-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.help }}</p>
        </article>
      </div>
      <el-alert
        v-for="warning in safetyStatus?.warnings ?? []"
        :key="warning"
        class="system-alert"
        type="warning"
        show-icon
        :closable="false"
        :title="warning"
      />
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
              <el-table-column label="校验" min-width="220">
                <template #default="{ row }">
                  <span>{{ backupVerificationText(row.id) }}</span>
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
              <el-table-column label="操作" width="280" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openFile(row.download_url)">下载</el-button>
                  <el-button link type="primary" :loading="verifyingBackupId === row.id" @click="verifyBackup(row.id)">
                    校验
                  </el-button>
                  <el-button link type="warning" :loading="dryRunningBackupId === row.id" @click="dryRunRestore(row.id)">
                    演练
                  </el-button>
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
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";

import { apiRequest, openFile } from "../api/client";
import { AppPage, AppStatGrid, type PageMetaItem, type StatCardItem } from "../components/ui";

interface BackupRecord {
  id: number;
  backup_name: string;
  file_path?: string;
  file_size: number;
  created_at: string;
  status: string;
  download_url: string;
}

interface BackupVerification {
  backup_id: number;
  backup_name: string;
  valid: boolean;
  message: string;
  file_size: number;
  will_overwrite_path: string;
  sqlite_integrity?: string | null;
}

interface SystemSafetyStatus {
  main_db_path: string;
  main_db_size: number;
  data_dir_path: string;
  data_dir_size: number;
  backup_dir_path: string;
  backup_dir_size: number;
  backup_count: number;
  latest_backup?: BackupRecord | null;
  latest_restore_at?: string | null;
  sqlite_integrity: string;
  alembic_version?: string | null;
  warnings: string[];
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
const safetyStatus = ref<SystemSafetyStatus | null>(null);
const backupVerifications = ref<Record<number, BackupVerification>>({});
const creatingBackup = ref(false);
const restoringBackupId = ref<number | null>(null);
const verifyingBackupId = ref<number | null>(null);
const dryRunningBackupId = ref<number | null>(null);
const repairingAction = ref<string | null>(null);
const autoBackupBeforeRestore = ref(true);

const configItemCount = computed(
  () => configGroups.value.reduce((sum, group) => sum + group.items.length, 0),
);
const repairErrorCount = computed(
  () => repairScan.value?.issues.filter((item) => item.severity === "error").length ?? 0,
);
const latestBackupName = computed(() => backups.value[0]?.backup_name ?? "暂无");
const systemPageMeta = computed<PageMetaItem[]>(() => [
  { label: "配置项", value: configItemCount.value },
  { label: "模板", value: templates.value.length },
  { label: "高风险问题", value: repairErrorCount.value },
  { label: "最近备份", value: latestBackupName.value },
  { label: "主库状态", value: safetyStatus.value?.sqlite_integrity ?? "待检查" },
]);
const overviewCards = computed<StatCardItem[]>(() => [
  {
    label: "配置项",
    value: configItemCount.value,
    help: "当前可在系统设置中维护的参数数量。",
    tone: "primary",
  },
  {
    label: "模板文件",
    value: templates.value.length,
    help: "运行目录中可下载的导入模板。",
    tone: "info",
  },
  {
    label: "数据问题",
    value: repairScan.value?.issues.length ?? 0,
    help: "数据修复扫描发现的问题总数。",
    tone: repairErrorCount.value ? "danger" : "success",
  },
  {
    label: "备份数量",
    value: backups.value.length,
    help: "恢复前建议确认最近一次可用备份。",
    tone: backups.value.length ? "warning" : "neutral",
  },
]);
const safetyCards = computed(() => [
  {
    label: "主库路径",
    value: safetyStatus.value?.main_db_path ?? "待检查",
    help: `大小：${formatBytes(safetyStatus.value?.main_db_size ?? 0)}`,
  },
  {
    label: "data 目录",
    value: formatBytes(safetyStatus.value?.data_dir_size ?? 0),
    help: safetyStatus.value?.data_dir_path ?? "待检查",
  },
  {
    label: "备份目录",
    value: formatBytes(safetyStatus.value?.backup_dir_size ?? 0),
    help: `${safetyStatus.value?.backup_count ?? 0} 个备份包`,
  },
  {
    label: "最近恢复",
    value: safetyStatus.value?.latest_restore_at ?? "暂无",
    help: "恢复操作会记录在审计日志中。",
  },
  {
    label: "迁移版本",
    value: safetyStatus.value?.alembic_version ?? "未读取",
    help: "当前主库记录的 Alembic 版本。",
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

async function loadSafetyStatus(): Promise<void> {
  safetyStatus.value = await apiRequest<SystemSafetyStatus>("/api/system/safety-status");
}

async function reloadMeta(): Promise<void> {
  await Promise.all([loadTemplates(), loadRepairScan(), loadBackups(), loadAuditLogs(), loadSafetyStatus()]);
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
    await Promise.all([loadBackups(), loadAuditLogs(), loadSafetyStatus()]);
    ElMessage.success(result.message);
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    creatingBackup.value = false;
  }
}

function backupVerificationText(backupId: number): string {
  const verification = backupVerifications.value[backupId];
  if (!verification) return "未校验";
  return verification.valid ? `通过，SQLite ${verification.sqlite_integrity ?? "ok"}` : verification.message;
}

async function verifyBackup(backupId: number): Promise<void> {
  try {
    verifyingBackupId.value = backupId;
    const result = await apiRequest<BackupVerification>(`/api/system/backups/${backupId}/verify`);
    backupVerifications.value = { ...backupVerifications.value, [backupId]: result };
    if (result.valid) {
      ElMessage.success(result.message);
    } else {
      ElMessage.warning(result.message);
    }
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    verifyingBackupId.value = null;
  }
}

async function dryRunRestore(backupId: number): Promise<void> {
  try {
    dryRunningBackupId.value = backupId;
    const result = await apiRequest<BackupVerification>(`/api/system/backups/${backupId}/restore-dry-run`, {
      method: "POST",
    });
    backupVerifications.value = { ...backupVerifications.value, [backupId]: result };
    if (result.valid) {
      ElMessage.success(result.message);
    } else {
      ElMessage.warning(result.message);
    }
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    dryRunningBackupId.value = null;
  }
}

async function restoreBackup(backupId: number): Promise<void> {
  try {
    const backup = backups.value.find((item) => item.id === backupId);
    const verifyResult = backupVerifications.value[backupId]
      ?? await apiRequest<BackupVerification>(`/api/system/backups/${backupId}/verify`);
    backupVerifications.value = { ...backupVerifications.value, [backupId]: verifyResult };
    if (!verifyResult.valid) {
      ElMessage.warning(verifyResult.message);
      return;
    }
    await ElMessageBox.confirm(
      `恢复会覆盖当前主库：${verifyResult.will_overwrite_path}。备份包：${backup?.backup_name ?? verifyResult.backup_name}。建议确保其他页面已停止操作。是否继续？`,
      "恢复备份",
      { type: "warning" },
    );
    await ElMessageBox.confirm(
      "这是恢复前的第二次确认。点击确认后会替换当前数据库和附件目录。",
      "确认覆盖当前数据",
      { type: "error" },
    );
    restoringBackupId.value = backupId;
    const result = await apiRequest<{ message: string }>("/api/system/restore", {
      method: "POST",
      body: JSON.stringify({
        backup_id: backupId,
        auto_backup_current: autoBackupBeforeRestore.value,
      }),
    });
    await Promise.all([loadBackups(), loadAuditLogs(), loadSafetyStatus()]);
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
  grid-template-columns: minmax(0, 1.25fr) repeat(4, minmax(0, 0.75fr));
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

.safety-panel {
  display: grid;
  gap: 14px;
}

.safety-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.safety-card {
  display: grid;
  gap: 8px;
  min-height: 128px;
  padding: 14px;
  border: 1px solid #dfe9f2;
  border-radius: 8px;
  background: #fbfdff;
}

.safety-card span {
  color: #6d8092;
  font-size: 13px;
}

.safety-card strong {
  color: #1f3245;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.safety-card p {
  margin: 0;
  color: #60748a;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.system-alert {
  margin-top: 2px;
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
