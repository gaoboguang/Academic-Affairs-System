<template>
  <AppPage
    title="知识库"
    subtitle="维护题分明细归一所需的知识点树、平台别名和错因标签。"
    :meta="[{ label: '数据来源', value: '题分明细与知识库模板' }]"
  >
    <AppStatGrid :items="cards" />

    <AppSectionCard title="知识点维护" subtitle="先统一知识点路径，再导入题分明细。">
      <div class="knowledge-grid">
        <article class="knowledge-panel">
          <strong>知识点树</strong>
          <p>按学科维护模块、子模块和具体知识点，支持后续生成个人补弱清单。</p>
        </article>
        <article class="knowledge-panel">
          <strong>平台别名</strong>
          <p>把阅卷平台中的不同写法归一到标准知识点，减少重复诊断。</p>
        </article>
        <article class="knowledge-panel">
          <strong>错因标签</strong>
          <p>维护概念不清、计算错误、审题失误等标签，便于题分导入后聚合原因。</p>
        </article>
      </div>
    </AppSectionCard>
  </AppPage>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { AppPage, AppSectionCard, AppStatGrid } from "../components/ui";
import type { StatCardItem } from "../components/ui";

const cards = computed<StatCardItem[]>(() => [
  { label: "知识点树", value: "可维护", help: "按学科和层级组织标准知识点。", tone: "primary" },
  { label: "平台别名", value: "可归一", help: "把平台导出的知识点写法映射到标准库。", tone: "success" },
  { label: "错因标签", value: "可沉淀", help: "为题分明细补充错因分类。", tone: "warning" },
]);
</script>

<style scoped>
.knowledge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.knowledge-panel {
  border: 1px solid var(--app-border);
  border-radius: 8px;
  padding: 16px;
  background: var(--app-surface);
}

.knowledge-panel strong {
  display: block;
  margin-bottom: 8px;
  color: var(--app-text);
}

.knowledge-panel p {
  margin: 0;
  color: var(--app-text-secondary);
  line-height: 1.7;
}
</style>
