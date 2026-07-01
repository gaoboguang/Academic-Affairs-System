<template>
  <AuthShell
    badge="学校服务器"
    title="受控账号登录"
    description="管理员创建账号后，教师按授权班级和任教范围进入对应数据。"
    panel-title="账号登录"
    panel-description="学校服务器登录"
  >
    <ElForm class="auth-form" label-position="top" @submit.prevent>
      <ElFormItem label="账号">
        <ElInput v-model="username" autocomplete="username" @keyup.enter="handleLogin" />
      </ElFormItem>
      <ElFormItem label="密码">
        <ElInput
          v-model="password"
          type="password"
          show-password
          autocomplete="current-password"
          @keyup.enter="handleLogin"
        />
      </ElFormItem>
      <ElAlert v-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
      <ElButton class="submit-button" type="primary" :loading="loading" @click="handleLogin">登录</ElButton>
    </ElForm>
  </AuthShell>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import AuthShell from "../components/auth/AuthShell.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();

const username = ref("");
const password = ref("");
const loading = ref(false);
const errorMessage = ref("");

async function handleLogin(): Promise<void> {
  errorMessage.value = "";
  if (!username.value.trim()) {
    errorMessage.value = "请输入账号";
    return;
  }
  if (!password.value) {
    errorMessage.value = "请输入密码";
    return;
  }
  loading.value = true;
  try {
    await auth.login(username.value, password.value);
    ElMessage.success("登录成功");
    if (auth.mustChangePassword) {
      await router.push("/change-password");
      return;
    }
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/";
    await router.push(redirect);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "登录失败";
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
