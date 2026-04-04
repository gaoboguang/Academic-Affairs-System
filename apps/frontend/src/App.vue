<template>
  <ElConfigProvider :locale="zhCn">
    <RouterView />
  </ElConfigProvider>
</template>

<script setup lang="ts">
import ElConfigProvider from "element-plus/es/components/config-provider/index";
import zhCn from "element-plus/es/locale/lang/zh-cn";
</script>
