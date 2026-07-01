<template>
  <AuthShell
    badge="首次登录"
    title="更换初始密码"
    description="初始密码只用于首次进入系统，更新后再继续处理教务数据。"
    panel-badge="密码更新"
    panel-title="修改初始密码"
    panel-description="首次登录后需要更换密码，再进入系统。"
  >
    <ElForm class="auth-form" label-position="top" @submit.prevent>
      <ElFormItem label="当前密码">
        <ElInput v-model="currentPassword" type="password" show-password autocomplete="current-password" />
      </ElFormItem>
      <ElFormItem label="新密码">
        <ElInput v-model="newPassword" type="password" show-password autocomplete="new-password" />
      </ElFormItem>
      <ElAlert v-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
      <ElButton class="submit-button" type="primary" :loading="loading" @click="handleSubmit">保存并进入系统</ElButton>
    </ElForm>
  </AuthShell>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import AuthShell from "../components/auth/AuthShell.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();
const currentPassword = ref("");
const newPassword = ref("");
const loading = ref(false);
const errorMessage = ref("");

async function handleSubmit(): Promise<void> {
  errorMessage.value = "";
  if (!currentPassword.value) {
    errorMessage.value = "请输入当前密码";
    return;
  }
  if (!newPassword.value) {
    errorMessage.value = "请输入新密码";
    return;
  }
  if (newPassword.value.length < 8) {
    errorMessage.value = "新密码至少 8 位";
    return;
  }
  if (!/[A-Za-z]/.test(newPassword.value) || !/\d/.test(newPassword.value)) {
    errorMessage.value = "新密码至少包含字母和数字";
    return;
  }
  loading.value = true;
  try {
    await auth.changePassword(currentPassword.value, newPassword.value);
    ElMessage.success("密码已更新");
    await router.push("/");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "密码修改失败";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-form {
  display: grid;
  gap: 2px;
}

.submit-button {
  width: 100%;
  margin-top: 10px;
}
</style>
