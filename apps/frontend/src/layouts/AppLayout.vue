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
  grid-template-columns: 252px minmax(0, 1fr);
  gap: 18px;
  padding: 18px;
  max-width: 1680px;
  margin: 0 auto;
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 20px 16px;
  border-radius: 24px;
  background: linear-gradient(180deg, #1f3548 0%, #233b50 100%);
  color: #eef4fa;
  box-shadow: 0 18px 42px rgba(26, 43, 62, 0.16);
  position: sticky;
  top: 18px;
  max-height: calc(100vh - 36px);
  overflow: hidden;
}

.brand-block {
  padding: 4px 4px 0;
}

.brand-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.brand-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, #f0c58d, #f7e2bf);
  color: #20364a;
  font-size: 18px;
  font-weight: 800;
}

.brand-copy h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 760;
}

.brand-copy p {
  margin: 6px 0 0;
  color: rgba(224, 233, 241, 0.74);
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
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(236, 243, 249, 0.86);
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
  color: rgba(245, 249, 252, 0.96);
  font-size: 13px;
}

.nav-section-head p {
  margin: 6px 0 0;
  color: rgba(198, 211, 223, 0.64);
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
  padding: 11px 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  color: rgba(236, 243, 249, 0.86);
  text-align: left;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.nav-link:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
}

.nav-link.active {
  background: linear-gradient(135deg, rgba(240, 197, 141, 0.18), rgba(255, 255, 255, 0.1));
  border-color: rgba(240, 197, 141, 0.24);
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
  gap: 18px;
}

.content-topbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 22px;
  border: 1px solid rgba(112, 127, 141, 0.12);
  background: rgba(255, 255, 255, 0.68);
  box-shadow: 0 10px 24px rgba(35, 56, 81, 0.05);
  backdrop-filter: blur(8px);
  width: 100%;
  max-width: 1480px;
  margin: 0 auto;
}

.content-topbar-copy {
  display: grid;
  gap: 6px;
}

.content-topbar-label {
  color: #72859a;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.content-topbar-copy strong {
  color: #1e3448;
  font-size: 22px;
}

.content-topbar-copy p {
  margin: 0;
  color: #65798b;
  line-height: 1.55;
}

.content-topbar-hint {
  max-width: 320px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(250, 251, 253, 0.88);
  border: 1px solid rgba(112, 127, 141, 0.12);
}

.content-topbar-hint span {
  color: #7a8c9b;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.content-topbar-hint p {
  margin: 8px 0 0;
  color: #617486;
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
}

@media (max-width: 960px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .content-topbar {
    flex-direction: column;
  }

  .content-topbar-hint {
    max-width: none;
    width: 100%;
  }
}

@media (max-width: 640px) {
  .layout-shell {
    padding: 12px;
    gap: 12px;
  }

  .side-panel,
  .content-topbar {
    border-radius: 18px;
  }
}
</style>
