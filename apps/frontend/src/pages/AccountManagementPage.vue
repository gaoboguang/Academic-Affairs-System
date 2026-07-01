<template>
  <AppPage
    title="账号管理"
    subtitle="由管理员开设教师账号，维护关联教师和额外可访问班级。"
    content-width="wide"
  >
    <template #actions>
      <div class="account-actions">
        <ElButton :icon="UploadFilled" @click="openImportDialog">批量导入教师账号</ElButton>
        <ElButton type="primary" @click="openCreateDialog">新建教师账号</ElButton>
      </div>
    </template>

    <section v-if="accountListError || optionsLoadError" class="account-status-stack">
      <ElAlert
        v-if="accountListError"
        type="error"
        show-icon
        :closable="false"
        title="账号列表加载失败"
      >
        <template #default>
          <div class="account-alert-body">
            <span>{{ accountListError }}</span>
            <ElButton link type="primary" :loading="loading" @click="loadUsers">重新加载账号列表</ElButton>
          </div>
        </template>
      </ElAlert>
      <ElAlert
        v-if="optionsLoadError"
        type="warning"
        show-icon
        :closable="false"
        title="账号基础选项加载不完整"
      >
        <template #default>
          <div class="account-alert-body">
            <span>{{ optionsLoadError }}</span>
            <ElButton link type="primary" :loading="optionsLoading" @click="loadOptions">重新加载教师和班级选项</ElButton>
          </div>
        </template>
      </ElAlert>
    </section>

    <AppSectionCard title="账号列表">
      <div class="account-list-toolbar">
        <span>当前共 {{ users.length }} 个账号</span>
        <ElButton :loading="loading" @click="loadUsers">刷新列表</ElButton>
      </div>
      <ElTable :data="users" row-key="id" v-loading="loading">
        <template #empty>
          <ElEmpty :description="accountListEmptyDescription">
            <ElButton v-if="accountListError" type="primary" plain :loading="loading" @click="loadUsers">
              重新加载账号列表
            </ElButton>
          </ElEmpty>
        </template>
        <ElTableColumn prop="username" label="账号" min-width="120" />
        <ElTableColumn prop="display_name" label="姓名" min-width="120" />
        <ElTableColumn label="角色" width="100">
          <template #default="{ row }">
            <ElTag :type="row.role === 'admin' ? 'danger' : 'primary'">
              {{ row.role === "admin" ? "管理员" : "教师" }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="teacher_name" label="关联教师" min-width="140" />
        <ElTableColumn label="状态" width="110">
          <template #default="{ row }">
            <ElTag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? "启用" : "停用" }}</ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="首次改密" width="110">
          <template #default="{ row }">
            <ElTag :type="row.must_change_password ? 'warning' : 'success'">
              {{ row.must_change_password ? "待修改" : "已完成" }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="班级范围" min-width="180">
          <template #default="{ row }">
            {{ formatClassScope(row.effective_class_ids) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <ElButton text type="primary" @click="openEditDialog(row)">编辑</ElButton>
            <ElButton
              text
              type="warning"
              :loading="resettingUserId === row.id"
              :disabled="togglingUserId === row.id"
              @click="handleResetPassword(row)"
            >
              重置密码
            </ElButton>
            <ElButton
              text
              :type="row.is_active ? 'danger' : 'success'"
              :loading="togglingUserId === row.id"
              :disabled="resettingUserId === row.id"
              @click="handleToggle(row)"
            >
              {{ row.is_active ? "停用" : "启用" }}
            </ElButton>
          </template>
        </ElTableColumn>
      </ElTable>
    </AppSectionCard>

    <ElDialog v-model="dialogVisible" :title="editingUser ? '编辑账号' : '新建教师账号'" width="520px">
      <ElForm label-position="top">
        <ElAlert
          v-if="optionsLoadError"
          class="dialog-inline-alert"
          type="warning"
          show-icon
          :closable="false"
          title="教师和班级选项加载不完整，保存教师账号前请先重新加载选项。"
        >
          <template #default>
            <ElButton link type="primary" :loading="optionsLoading" @click="loadOptions">重新加载选项</ElButton>
          </template>
        </ElAlert>
        <div v-if="!editingUser" class="batch-import-entry">
          <div>
            <span class="batch-import-badge">批量导入</span>
            <strong>一次创建多名教师账号</strong>
            <p>下载模板后填写账号和教师档案信息，系统会生成临时密码。</p>
          </div>
          <ElButton type="primary" plain :icon="UploadFilled" @click="openImportFromCreateDialog">
            批量导入教师账号
          </ElButton>
        </div>
        <ElFormItem label="账号" v-if="!editingUser">
          <ElInput v-model="form.username" />
        </ElFormItem>
        <ElFormItem label="显示名称">
          <ElInput v-model="form.display_name" />
        </ElFormItem>
        <ElFormItem label="角色">
          <ElSelect v-model="form.role">
            <ElOption label="教师" value="teacher" />
            <ElOption label="管理员" value="admin" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="关联教师" v-if="form.role === 'teacher'">
          <ElSelect v-model="form.teacher_id" filterable clearable :loading="optionsLoading" :disabled="optionsLoading">
            <ElOption v-for="teacher in teachers" :key="teacher.id" :label="teacher.name" :value="teacher.id" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="额外可访问班级">
          <ElSelect
            v-model="form.extra_class_ids"
            multiple
            filterable
            clearable
            :loading="optionsLoading"
            :disabled="optionsLoading"
          >
            <ElOption v-for="item in classes" :key="item.id" :label="item.name" :value="item.id" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="账号状态" v-if="editingUser">
          <ElSwitch v-model="form.is_active" active-text="启用" inactive-text="停用" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton
          v-if="!editingUser"
          :icon="UploadFilled"
          :disabled="saving"
          @click="openImportFromCreateDialog"
        >
          批量导入教师账号
        </ElButton>
        <ElButton @click="dialogVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="saving" @click="handleSave">保存</ElButton>
      </template>
    </ElDialog>

    <ElDialog v-model="tempPasswordVisible" title="临时密码" width="460px">
      <ElAlert type="warning" :closable="false" title="临时密码只显示一次，请交给对应教师并提醒首次登录后修改。" />
      <ElInput class="temp-password" :model-value="temporaryPassword" readonly />
      <template #footer>
        <ElButton type="primary" @click="tempPasswordVisible = false">我已记录</ElButton>
      </template>
    </ElDialog>

    <ElDialog
      v-model="importDialogVisible"
      title="批量导入教师账号"
      width="760px"
      :close-on-click-modal="false"
    >
      <div class="account-import-dialog">
        <ElAlert
          type="warning"
          :closable="false"
          title="导入只创建教师账号，临时密码只在本次结果中显示，请及时记录。"
        />
        <div class="account-import-toolbar">
          <ElButton :icon="Download" @click="openFile('/api/admin/users/import-template')">模板下载</ElButton>
          <ElSelect v-model="accountImportStrategy" class="account-import-strategy">
            <ElOption label="跳过已存在账号" value="skip_existing" />
            <ElOption label="已存在时报错" value="create" />
          </ElSelect>
          <ElUpload
            :show-file-list="false"
            :auto-upload="false"
            :disabled="importing"
            :on-change="handleAccountImport"
            accept=".xlsx,.xls"
          >
            <ElButton type="primary" :icon="UploadFilled" :loading="importing">选择文件并导入</ElButton>
          </ElUpload>
        </div>

        <ElAlert
          v-if="importActionError"
          type="error"
          show-icon
          :closable="false"
          title="教师账号导入失败"
        >
          <template #default>
            <div class="account-alert-body">
              <span>{{ importActionError }}</span>
              <ElButton link type="primary" :loading="importing" @click="openFile('/api/admin/users/import-template')">
                重新下载模板
              </ElButton>
            </div>
          </template>
        </ElAlert>

        <ImportFeedbackPanel :result="importResult" />

        <div v-if="importedAccounts.length" class="temporary-password-list">
          <div class="temporary-password-head">
            <strong>临时密码清单</strong>
            <ElButton link type="primary" @click="copyImportedAccounts">复制清单</ElButton>
          </div>
          <ElTable :data="importedAccounts" max-height="280" stripe>
            <ElTableColumn prop="username" label="账号" min-width="120" />
            <ElTableColumn prop="display_name" label="显示名称" min-width="120" />
            <ElTableColumn prop="teacher_name" label="关联教师" min-width="120" />
            <ElTableColumn prop="temporary_password" label="临时密码" min-width="160" />
          </ElTable>
        </div>
      </div>
      <template #footer>
        <ElButton type="primary" @click="importDialogVisible = false">关闭</ElButton>
      </template>
    </ElDialog>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { Download, UploadFilled } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import type { UploadFile } from "element-plus";

import { apiRequest, openFile, uploadFile } from "../api/client";
import ImportFeedbackPanel from "../components/common/ImportFeedbackPanel.vue";
import AppPage from "../components/ui/AppPage.vue";
import AppSectionCard from "../components/ui/AppSectionCard.vue";
import type { AdminUserCreatePayload, AdminUserCreateResponse, AdminUserUpdatePayload, AppUser } from "../stores/auth";
import type { ImportFeedbackResult } from "../utils/importFeedback";
import { formatUserActionError, getErrorMessage } from "../utils/userFeedback";

interface TeacherOption {
  id: number;
  name: string;
}

interface TeacherListResponse {
  items: TeacherOption[];
}

interface ClassOption {
  id: number;
  name: string;
}

interface ImportedAccount {
  username: string;
  display_name: string;
  teacher_no?: string | null;
  teacher_name?: string | null;
  temporary_password: string;
}

interface AccountImportResult extends ImportFeedbackResult {
  created_accounts: ImportedAccount[];
}

const users = ref<AppUser[]>([]);
const teachers = ref<TeacherOption[]>([]);
const classes = ref<ClassOption[]>([]);
const loading = ref(false);
const optionsLoading = ref(false);
const saving = ref(false);
const importing = ref(false);
const dialogVisible = ref(false);
const importDialogVisible = ref(false);
const tempPasswordVisible = ref(false);
const temporaryPassword = ref("");
const editingUser = ref<AppUser | null>(null);
const accountImportStrategy = ref("skip_existing");
const importResult = ref<AccountImportResult | null>(null);
const accountListError = ref("");
const optionsLoadError = ref("");
const importActionError = ref("");
const resettingUserId = ref<number | null>(null);
const togglingUserId = ref<number | null>(null);
const importedAccounts = computed(() => importResult.value?.created_accounts ?? []);
const accountListEmptyDescription = computed(() => {
  if (loading.value) return "正在加载账号列表";
  if (accountListError.value) return "账号列表加载失败，请重新加载。";
  return "暂无账号记录，可以先新建或批量导入教师账号。";
});

const form = reactive<AdminUserCreatePayload & { is_active: boolean }>({
  username: "",
  display_name: "",
  role: "teacher",
  teacher_id: null,
  extra_class_ids: [],
  is_active: true,
});

function formatClassScope(classIds: number[]): string {
  if (!classIds.length) return "无班级范围";
  const names = classIds.map((id) => classes.value.find((item) => item.id === id)?.name ?? String(id));
  return names.join("、");
}

async function loadOptions(): Promise<void> {
  optionsLoading.value = true;
  optionsLoadError.value = "";
  const [teacherResult, classResult] = await Promise.allSettled([
    apiRequest<TeacherListResponse>("/api/teachers?page=1&page_size=200"),
    apiRequest<ClassOption[]>("/api/base/classes"),
  ]);
  const errorMessages: string[] = [];
  if (teacherResult.status === "fulfilled") {
    teachers.value = teacherResult.value.items;
  } else {
    teachers.value = [];
    errorMessages.push(`教师档案：${getErrorMessage(teacherResult.reason)}`);
  }
  if (classResult.status === "fulfilled") {
    classes.value = classResult.value;
  } else {
    classes.value = [];
    errorMessages.push(`班级选项：${getErrorMessage(classResult.reason)}`);
  }
  if (errorMessages.length) {
    optionsLoadError.value = `${errorMessages.join("；")}。关联教师和班级范围可能暂时无法选择。`;
  }
  optionsLoading.value = false;
}

async function loadUsers(): Promise<void> {
  loading.value = true;
  accountListError.value = "";
  try {
    users.value = await apiRequest<AppUser[]>("/api/admin/users");
  } catch (error) {
    users.value = [];
    accountListError.value = formatUserActionError("加载账号列表", error, "检查本地服务状态后重新加载账号列表");
  } finally {
    loading.value = false;
  }
}

function resetForm(): void {
  form.username = "";
  form.display_name = "";
  form.role = "teacher";
  form.teacher_id = null;
  form.extra_class_ids = [];
  form.is_active = true;
}

function openCreateDialog(): void {
  editingUser.value = null;
  resetForm();
  dialogVisible.value = true;
}

function openImportDialog(): void {
  importResult.value = null;
  importActionError.value = "";
  importDialogVisible.value = true;
}

function openImportFromCreateDialog(): void {
  dialogVisible.value = false;
  openImportDialog();
}

function openEditDialog(user: AppUser): void {
  editingUser.value = user;
  form.username = user.username;
  form.display_name = user.display_name;
  form.role = user.role;
  form.teacher_id = user.teacher_id ?? null;
  form.extra_class_ids = [...user.extra_class_ids];
  form.is_active = user.is_active;
  dialogVisible.value = true;
}

function validateAccountForm(): string {
  if (!editingUser.value && !form.username.trim()) {
    return "请输入账号";
  }
  if (!form.display_name.trim()) {
    return "请输入显示名称";
  }
  if (form.role === "teacher" && !form.teacher_id) {
    return "教师账号必须关联教师档案";
  }
  return "";
}

async function handleSave(): Promise<void> {
  const validationError = validateAccountForm();
  if (validationError) {
    ElMessage.warning(validationError);
    return;
  }
  saving.value = true;
  try {
    if (editingUser.value) {
      const payload: AdminUserUpdatePayload = {
        display_name: form.display_name,
        role: form.role,
        teacher_id: form.role === "teacher" ? form.teacher_id : null,
        extra_class_ids: form.extra_class_ids,
        is_active: form.is_active,
      };
      await apiRequest<AppUser>(`/api/admin/users/${editingUser.value.id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      ElMessage.success("账号已更新");
    } else {
      const payload: AdminUserCreatePayload = {
        username: form.username,
        display_name: form.display_name,
        role: form.role,
        teacher_id: form.role === "teacher" ? form.teacher_id : null,
        extra_class_ids: form.extra_class_ids,
      };
      const response = await apiRequest<AdminUserCreateResponse>("/api/admin/users", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      temporaryPassword.value = response.temporary_password;
      tempPasswordVisible.value = true;
      ElMessage.success("账号已创建");
    }
    dialogVisible.value = false;
    await loadUsers();
  } catch (error) {
    ElMessage.error(formatUserActionError("保存账号", error, "检查账号、教师档案和班级范围后重试"));
  } finally {
    saving.value = false;
  }
}

async function handleResetPassword(user: AppUser): Promise<void> {
  resettingUserId.value = user.id;
  try {
    const response = await apiRequest<AdminUserCreateResponse>(`/api/admin/users/${user.id}/reset-password`, {
      method: "POST",
    });
    temporaryPassword.value = response.temporary_password;
    tempPasswordVisible.value = true;
    ElMessage.success("密码已重置");
    await loadUsers();
  } catch (error) {
    ElMessage.error(formatUserActionError("重置密码", error, "确认账号仍存在后重试"));
  } finally {
    resettingUserId.value = null;
  }
}

async function handleToggle(user: AppUser): Promise<void> {
  const action = user.is_active ? "disable" : "enable";
  togglingUserId.value = user.id;
  try {
    await apiRequest<AppUser>(`/api/admin/users/${user.id}/${action}`, { method: "POST" });
    ElMessage.success(user.is_active ? "账号已停用" : "账号已启用");
    await loadUsers();
  } catch (error) {
    ElMessage.error(formatUserActionError(user.is_active ? "停用账号" : "启用账号", error, "确认账号状态后重试"));
  } finally {
    togglingUserId.value = null;
  }
}

async function handleAccountImport(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw) {
    return;
  }
  importing.value = true;
  importActionError.value = "";
  try {
    importResult.value = await uploadFile<AccountImportResult>("/api/admin/users/import", uploadFileItem.raw, {
      strategy: accountImportStrategy.value,
    });
    ElMessage({
      type: importResult.value.failed_rows ? "warning" : "success",
      message: importResult.value.message,
    });
    await loadUsers();
  } catch (error) {
    importResult.value = null;
    importActionError.value = formatUserActionError("导入教师账号", error, "下载最新模板，确认账号和教师档案信息后重新导入");
    ElMessage.error(importActionError.value);
  } finally {
    importing.value = false;
  }
}

async function copyImportedAccounts(): Promise<void> {
  if (!importedAccounts.value.length) return;
  const content = importedAccounts.value
    .map((item) => `${item.username}\t${item.display_name}\t${item.teacher_name ?? ""}\t${item.temporary_password}`)
    .join("\n");
  try {
    await navigator.clipboard.writeText(`账号\t显示名称\t关联教师\t临时密码\n${content}`);
    ElMessage.success("临时密码清单已复制");
  } catch {
    ElMessage.error("复制失败，请手动选中表格内容记录");
  }
}

onMounted(async () => {
  await Promise.all([loadOptions(), loadUsers()]);
});
</script>

<style scoped>
.account-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.temp-password {
  margin-top: 14px;
}

.account-status-stack {
  display: grid;
  gap: 10px;
}

.account-alert-body {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
}

.account-list-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 12px;
  color: #5f6f7f;
  font-size: 13px;
}

.dialog-inline-alert {
  margin-bottom: 14px;
}

.batch-import-entry {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  margin-bottom: 16px;
  border: 1px solid #d8e4ee;
  border-radius: 8px;
  background: #f7fafc;
}

.batch-import-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  margin-bottom: 6px;
  border-radius: 999px;
  background: rgba(64, 158, 255, 0.12);
  color: #2b6fb8;
  font-size: 12px;
  font-weight: 700;
}

.batch-import-entry strong {
  display: block;
  color: #1f2d3d;
}

.batch-import-entry p {
  margin: 4px 0 0;
  color: #6b7b8c;
  font-size: 13px;
  line-height: 1.45;
}

.account-import-dialog {
  display: grid;
  gap: 14px;
}

.account-import-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.account-import-strategy {
  width: 180px;
}

.temporary-password-list {
  display: grid;
  gap: 10px;
}

.temporary-password-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #2f4356;
}
</style>
