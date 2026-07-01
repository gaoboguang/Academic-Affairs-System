<template>
  <AuthShell
    badge="权限范围"
    title="当前页面不可访问"
    description="普通教师只能进入本人任教或班主任关联范围内的学生、成绩、分析和报表。"
    panel-badge="访问受限"
    panel-title="无权访问"
    panel-description="当前账号无权访问该页面"
  >
    <div class="forbidden-actions">
      <ElAlert
        type="warning"
        :closable="false"
        title="如需开通该功能，请联系管理员调整账号权限或班级范围。"
      />
      <ElButton type="primary" @click="$router.push('/')">返回工作台</ElButton>
    </div>
  </AuthShell>
</template>

<script setup lang="ts">
import AuthShell from "../components/auth/AuthShell.vue";
</script>

<style scoped>
.forbidden-actions {
  display: grid;
  gap: 16px;
}
</style>
