<template>
  <div class="layout-shell">
    <aside class="side-panel">
      <div class="brand-block">
        <div class="brand-row">
          <div class="brand-mark">教</div>
          <div class="brand-copy">
            <h1>本地教务工具</h1>
            <p>面向高中场景的本地单机教务管理与分析工具。</p>
          </div>
        </div>
        <div class="brand-meta">
          <span>本地运行</span>
          <span>单用户</span>
          <span>离线优先</span>
        </div>
      </div>

      <div class="nav-sections">
        <section v-for="section in navSections" :key="section.id" class="nav-section">
          <div class="nav-section-head">
            <strong>{{ section.title }}</strong>
            <p>{{ section.summary }}</p>
          </div>
          <div class="nav-link-list">
            <button
              v-for="item in section.items"
              :key="item.path"
              type="button"
              class="nav-link"
              :class="{ active: activeMenuPath === item.path }"
              @click="handleSelect(item.path)"
            >
              <component :is="item.icon" class="menu-icon" />
              <span>{{ item.label }}</span>
            </button>
          </div>
        </section>
      </div>
    </aside>

    <main class="content-panel">
      <div class="content-topbar">
        <div class="content-topbar-copy">
          <span class="content-topbar-label">{{ activeNavItem.sectionTitle }}</span>
          <strong>{{ activeNavItem.label }}</strong>
          <p>{{ activeNavItem.description }}</p>
        </div>
        <div class="content-topbar-hint">
          <span>使用提示</span>
          <p>{{ activeNavItem.helper }}</p>
        </div>
      </div>

      <div class="content-stage">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { navSections, resolveNavItem } from "./navigation";

const route = useRoute();
const router = useRouter();

const activeNavItem = computed(() => resolveNavItem(route.path));
const activeMenuPath = computed(() => activeNavItem.value.path);

function handleSelect(path: string): void {
  if (path === route.path) return;
  void router.push(path);
}
</script>

<style scoped>
.layout-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  gap: 0;
  max-width: 1920px;
  margin: 0 auto;
  background: var(--bg-layout);
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 18px 14px;
  border-right: 1px solid #e5eaf2;
  background: #001529;
  color: #f0f5ff;
  position: sticky;
  top: 0;
  max-height: 100vh;
  overflow: hidden;
}

.brand-block {
  padding: 4px 6px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.10);
}

.brand-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.brand-mark {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: #1677b3;
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}

.brand-copy h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 650;
  line-height: 1.25;
}

.brand-copy p {
  margin: 6px 0 0;
  color: rgba(240, 245, 255, 0.62);
  line-height: 1.55;
  font-size: 13px;
}

.brand-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.brand-meta span {
  padding: 5px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(240, 245, 255, 0.76);
  font-size: 12px;
}

.nav-sections {
  display: grid;
  gap: 16px;
  min-height: 0;
  overflow: auto;
  padding-right: 2px;
}

.nav-section {
  display: grid;
  gap: 10px;
}

.nav-section-head {
  padding: 0 4px;
}

.nav-section-head strong {
  color: rgba(240, 245, 255, 0.86);
  font-size: 13px;
}

.nav-section-head p {
  margin: 6px 0 0;
  color: rgba(240, 245, 255, 0.45);
  font-size: 12px;
  line-height: 1.5;
}

.nav-link-list {
  display: grid;
  gap: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: rgba(240, 245, 255, 0.72);
  text-align: left;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.nav-link.active {
  background: #1677b3;
  color: #ffffff;
}

.menu-icon {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
}

.content-panel {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 0;
}

.content-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border-soft);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 2px 8px rgba(22, 34, 61, 0.04);
  width: 100%;
  max-width: none;
  margin: 0 auto;
  position: sticky;
  top: 0;
  z-index: 9;
}

.content-topbar-copy {
  display: grid;
  gap: 6px;
}

.content-topbar-label {
  color: var(--text-soft);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
}

.content-topbar-copy strong {
  color: var(--text-main);
  font-size: 18px;
  font-weight: 650;
}

.content-topbar-copy p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.55;
}

.content-topbar-hint {
  max-width: 320px;
  padding: 10px 12px;
  border-radius: 8px;
  background: var(--bg-panel);
  border: 1px solid var(--border-soft);
}

.content-topbar-hint span {
  color: var(--text-soft);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
}

.content-topbar-hint p {
  margin: 6px 0 0;
  color: var(--text-muted);
  line-height: 1.55;
  font-size: 13px;
}

.content-stage {
  min-width: 0;
  width: 100%;
  max-width: 1480px;
  margin: 0 auto;
  display: grid;
  align-content: start;
  gap: 18px;
  padding: 24px;
}

@media (max-width: 960px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .side-panel {
    position: static;
    max-height: none;
  }

  .content-topbar {
    flex-direction: column;
    position: static;
  }

  .content-topbar-hint {
    max-width: none;
    width: 100%;
  }
}

@media (max-width: 640px) {
  .layout-shell {
    gap: 12px;
  }

  .content-stage {
    padding: 14px;
  }
}
</style>
