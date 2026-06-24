<template>
  <main class="auth-page">
    <section class="auth-panel">
      <div>
        <h1>修改初始密码</h1>
        <p>首次登录后需要更换密码，再进入系统。</p>
      </div>

      <ElForm label-position="top" @submit.prevent>
        <ElFormItem label="当前密码">
          <ElInput v-model="currentPassword" type="password" show-password autocomplete="current-password" />
        </ElFormItem>
        <ElFormItem label="新密码">
          <ElInput v-model="newPassword" type="password" show-password autocomplete="new-password" />
        </ElFormItem>
        <ElAlert v-if="errorMessage" type="error" :closable="false" :title="errorMessage" />
        <ElButton class="submit-button" type="primary" :loading="loading" @click="handleSubmit">保存并进入系统</ElButton>
      </ElForm>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();
const currentPassword = ref("");
const newPassword = ref("");
const loading = ref(false);
const errorMessage = ref("");

async function handleSubmit(): Promise<void> {
  errorMessage.value = "";
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
  gap: 18px;
  padding: 28px;
  border: 1px solid #e5eaf2;
  border-radius: 8px;
  background: #fff;
}

.auth-panel h1 {
  margin: 0;
  font-size: 22px;
}

.auth-panel p {
  margin: 8px 0 0;
  color: var(--text-muted);
}

.submit-button {
  width: 100%;
  margin-top: 10px;
}
</style>
