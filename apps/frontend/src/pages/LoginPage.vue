<template>
  <main class="auth-page">
    <section class="auth-panel">
      <div class="auth-brand">
        <div class="brand-mark">教</div>
        <div>
          <h1>本地教务工具</h1>
          <p>学校服务器登录</p>
        </div>
      </div>

      <ElForm label-position="top" @submit.prevent>
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
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";

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
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #f5f7fb;
}

.auth-panel {
  width: min(420px, 100%);
  display: grid;
  gap: 24px;
  padding: 28px;
  border: 1px solid #e5eaf2;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 12px 28px rgba(22, 34, 61, 0.08);
}

.auth-brand {
  display: flex;
  gap: 12px;
  align-items: center;
}

.brand-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: #1677b3;
  color: #fff;
  font-size: 20px;
  font-weight: 700;
}

.auth-brand h1 {
  margin: 0;
  font-size: 22px;
}

.auth-brand p {
  margin: 6px 0 0;
  color: var(--text-muted);
}

.submit-button {
  width: 100%;
  margin-top: 10px;
}
</style>
