<template>
  <AppPage
    title="账号管理"
    subtitle="由管理员开设教师账号，维护关联教师和额外可访问班级。"
    content-width="wide"
  >
    <template #actions>
      <ElButton type="primary" @click="openCreateDialog">新建教师账号</ElButton>
    </template>

    <AppSectionCard title="账号列表">
      <ElTable :data="users" row-key="id" v-loading="loading">
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
            <ElButton text type="warning" @click="handleResetPassword(row)">重置密码</ElButton>
            <ElButton text :type="row.is_active ? 'danger' : 'success'" @click="handleToggle(row)">
              {{ row.is_active ? "停用" : "启用" }}
            </ElButton>
          </template>
        </ElTableColumn>
      </ElTable>
    </AppSectionCard>

    <ElDialog v-model="dialogVisible" :title="editingUser ? '编辑账号' : '新建教师账号'" width="520px">
      <ElForm label-position="top">
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
          <ElSelect v-model="form.teacher_id" filterable clearable>
            <ElOption v-for="teacher in teachers" :key="teacher.id" :label="teacher.name" :value="teacher.id" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="额外可访问班级">
          <ElSelect v-model="form.extra_class_ids" multiple filterable clearable>
            <ElOption v-for="item in classes" :key="item.id" :label="item.name" :value="item.id" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="账号状态" v-if="editingUser">
          <ElSwitch v-model="form.is_active" active-text="启用" inactive-text="停用" />
        </ElFormItem>
      </ElForm>
      <template #footer>
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
  </AppPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import { apiRequest } from "../api/client";
import AppPage from "../components/ui/AppPage.vue";
import AppSectionCard from "../components/ui/AppSectionCard.vue";
import type { AdminUserCreatePayload, AdminUserCreateResponse, AdminUserUpdatePayload, AppUser } from "../stores/auth";

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

const users = ref<AppUser[]>([]);
const teachers = ref<TeacherOption[]>([]);
const classes = ref<ClassOption[]>([]);
const loading = ref(false);
const saving = ref(false);
const dialogVisible = ref(false);
const tempPasswordVisible = ref(false);
const temporaryPassword = ref("");
const editingUser = ref<AppUser | null>(null);

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
  const [teacherPayload, classPayload] = await Promise.all([
    apiRequest<TeacherListResponse>("/api/teachers?page=1&page_size=200"),
    apiRequest<ClassOption[]>("/api/base/classes"),
  ]);
  teachers.value = teacherPayload.items;
  classes.value = classPayload;
}

async function loadUsers(): Promise<void> {
  loading.value = true;
  try {
    users.value = await apiRequest<AppUser[]>("/api/admin/users");
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

async function handleSave(): Promise<void> {
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
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

async function handleResetPassword(user: AppUser): Promise<void> {
  const response = await apiRequest<AdminUserCreateResponse>(`/api/admin/users/${user.id}/reset-password`, {
    method: "POST",
  });
  temporaryPassword.value = response.temporary_password;
  tempPasswordVisible.value = true;
  await loadUsers();
}

async function handleToggle(user: AppUser): Promise<void> {
  const action = user.is_active ? "disable" : "enable";
  await apiRequest<AppUser>(`/api/admin/users/${user.id}/${action}`, { method: "POST" });
  ElMessage.success(user.is_active ? "账号已停用" : "账号已启用");
  await loadUsers();
}

onMounted(async () => {
  await loadOptions();
  await loadUsers();
});
</script>

<style scoped>
.temp-password {
  margin-top: 14px;
}
</style>
