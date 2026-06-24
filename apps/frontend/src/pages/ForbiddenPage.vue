<template>
  <main class="forbidden-page">
    <ElEmpty description="当前账号无权访问该页面">
      <ElButton type="primary" @click="$router.push('/')">返回工作台</ElButton>
    </ElEmpty>
  </main>
</template>

<style scoped>
.forbidden-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: #f5f7fb;
}
</style>
