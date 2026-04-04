<template>
  <div class="layout-shell">
    <aside class="side-panel">
      <div class="brand-block">
        <div class="brand-row">
          <div class="brand-mark">EDU</div>
          <div>
            <span class="brand-tag">高中教务系统</span>
            <h1>本地教务工具</h1>
          </div>
        </div>
        <p>围绕学生、教师、考试、分析与报表，覆盖学校日常教务管理的核心流程。</p>
        <div class="brand-pills">
          <span>学生档案</span>
          <span>教学分析</span>
          <span>升学辅助</span>
        </div>
      </div>
      <div class="shell-note">
        <strong>使用顺序</strong>
        <p>先维护基础数据，再导入成绩与课表，最后进入分析、推荐、量化与报表输出。</p>
      </div>
      <div class="nav-sections">
        <section v-for="section in navSections" :key="section.title" class="nav-section">
          <div class="nav-section-title">{{ section.title }}</div>
          <el-menu
            :default-active="activeMenuPath"
            class="nav-menu"
            @select="handleSelect"
          >
            <el-menu-item
              v-for="item in section.items"
              :key="item.path"
              :index="item.path"
            >
              <component :is="item.icon" class="menu-icon" />
              <span>{{ item.label }}</span>
            </el-menu-item>
          </el-menu>
        </section>
      </div>
      <div class="side-footer">
        <div class="side-footer-label">操作建议</div>
        <strong>先维护，再计算</strong>
        <div class="side-footer-meta">基础台账准确后，分析、量化、推荐和报表结果才可靠。</div>
      </div>
    </aside>
    <main class="content-panel">
      <div class="content-topbar">
        <div class="content-topbar-copy">
          <span class="content-topbar-label">{{ activeSectionTitle }}</span>
          <strong>{{ activeItemLabel }}</strong>
        </div>
        <div class="content-topbar-tags">
          <span v-for="tag in activeTagItems" :key="tag">{{ tag }}</span>
        </div>
      </div>
      <div class="content-stage">
        <div class="content-stage-inner">
          <RouterView />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
  DataAnalysis,
  Document,
  EditPen,
  Files,
  Histogram,
  HomeFilled,
  Notebook,
  Reading,
  School,
  Setting,
  Tickets,
  UserFilled,
} from "@element-plus/icons-vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const activeMenuPath = computed(() => {
  if (route.path.startsWith("/students/")) return "/students";
  if (route.path.startsWith("/teachers/")) return "/teachers";
  return route.path;
});

const navSections = [
  {
    title: "基础台账",
    items: [
      { path: "/", label: "工作台", icon: HomeFilled },
      { path: "/base-data", label: "基础数据", icon: Files },
      { path: "/students", label: "学生中心", icon: UserFilled },
      { path: "/growth-archive", label: "成长档案", icon: Notebook },
      { path: "/teachers", label: "教师中心", icon: Reading },
    ],
  },
  {
    title: "教学分析",
    items: [
      { path: "/exams", label: "考试成绩", icon: EditPen },
      { path: "/analytics", label: "分析中心", icon: DataAnalysis },
      { path: "/workload", label: "课表工作量", icon: Histogram },
      { path: "/evaluation-quant", label: "评教量化", icon: Tickets },
    ],
  },
  {
    title: "升学与系统",
    items: [
      { path: "/recommendations", label: "升学推荐", icon: School },
      { path: "/reports", label: "报表中心", icon: Document },
      { path: "/system-tools", label: "系统设置", icon: Setting },
    ],
  },
];

const flatNavItems = navSections.flatMap((section) =>
  section.items.map((item) => ({
    ...item,
    sectionTitle: section.title,
  })),
);

const activeNavItem = computed(
  () => flatNavItems.find((item) => item.path === activeMenuPath.value) ?? flatNavItems[0],
);

const activeSectionTitle = computed(() => activeNavItem.value.sectionTitle);
const activeItemLabel = computed(() => activeNavItem.value.label);
const activeTagItems = computed(() => {
  const tagMap: Record<string, string[]> = {
    基础台账: ["主数据维护", "档案管理", "关系台账"],
    教学分析: ["过程记录", "结果分析", "量化汇总"],
    升学与系统: ["升学推荐", "报表导出", "系统安全"],
  };
  return tagMap[activeSectionTitle.value] ?? ["业务流程", "数据校验", "结果输出"];
});

function handleSelect(path: string): void {
  router.push(path);
}
</script>

<style scoped>
.layout-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 20px;
  padding: 18px;
}

.side-panel {
  padding: 24px 18px 18px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  border-radius: 30px;
  background:
    radial-gradient(circle at top right, rgba(252, 208, 148, 0.18), transparent 28%),
    radial-gradient(circle at bottom left, rgba(78, 125, 161, 0.18), transparent 28%),
    linear-gradient(180deg, #102030 0%, #14283c 48%, #18314a 100%);
  color: #f2f6fb;
  box-shadow: 0 26px 70px rgba(19, 30, 45, 0.28);
  position: sticky;
  top: 18px;
  height: calc(100vh - 36px);
}

.brand-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(244, 172, 94, 0.95), rgba(255, 225, 182, 0.92));
  color: #132536;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.brand-block h1 {
  margin: 6px 0 0;
  font-size: 28px;
  font-family: "IBM Plex Sans", "PingFang SC", "Noto Sans SC", sans-serif;
  letter-spacing: 0.03em;
}

.brand-block p {
  margin: 10px 0 0;
  color: rgba(225, 233, 242, 0.72);
  line-height: 1.6;
}

.brand-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.brand-pills span {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(239, 245, 252, 0.84);
  font-size: 12px;
  letter-spacing: 0.06em;
}

.brand-tag {
  display: inline-flex;
  color: rgba(247, 210, 163, 0.88);
  font-size: 11px;
  letter-spacing: 0.18em;
}

.shell-note {
  padding: 16px;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.04));
}

.shell-note strong {
  display: block;
  color: #ffffff;
  font-size: 14px;
}

.shell-note p {
  margin: 8px 0 0;
  color: rgba(220, 230, 240, 0.76);
  line-height: 1.6;
  font-size: 13px;
}

.nav-sections {
  display: grid;
  gap: 14px;
  overflow: auto;
  padding-right: 4px;
}

.nav-section {
  display: grid;
  gap: 8px;
}

.nav-section-title {
  padding: 0 14px;
  color: rgba(198, 210, 224, 0.56);
  font-size: 12px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.nav-menu {
  border-right: none;
  background: transparent;
}

.nav-menu :deep(.el-menu-item) {
  margin-bottom: 4px;
  border-radius: 16px;
  color: rgba(238, 245, 252, 0.82);
  font-size: 14px;
  height: 46px;
  line-height: 46px;
  gap: 12px;
  padding: 0 14px !important;
}

.nav-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(244, 172, 94, 0.2), rgba(246, 207, 157, 0.12));
  color: #ffffff;
  box-shadow: inset 0 0 0 1px rgba(244, 196, 135, 0.18);
}

.menu-icon {
  width: 17px;
  height: 17px;
  flex: 0 0 17px;
}

.side-footer {
  margin-top: auto;
  padding: 14px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(228, 236, 244, 0.84);
}

.side-footer-label {
  color: rgba(200, 211, 223, 0.6);
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.side-footer-meta {
  margin-top: 6px;
  color: rgba(200, 211, 223, 0.7);
  font-size: 13px;
  line-height: 1.5;
}

.content-panel {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 14px;
}

.content-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 18px;
  border-radius: 24px;
  border: 1px solid rgba(120, 138, 156, 0.14);
  background: rgba(255, 255, 255, 0.56);
  box-shadow: 0 10px 24px rgba(35, 56, 81, 0.05);
  backdrop-filter: blur(10px);
}

.content-topbar-copy {
  display: grid;
  gap: 6px;
}

.content-topbar-label {
  color: #72859a;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.content-topbar-copy strong {
  color: #1e3448;
  font-size: 18px;
}

.content-topbar-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.content-topbar-tags span {
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(245, 249, 252, 0.96);
  border: 1px solid rgba(120, 138, 156, 0.12);
  color: #5f768a;
  font-size: 12px;
}

.content-stage {
  min-height: calc(100vh - 112px);
  padding: 10px;
  border-radius: 32px;
  border: 1px solid rgba(120, 138, 156, 0.16);
  background:
    radial-gradient(circle at top left, rgba(176, 219, 245, 0.24), transparent 26%),
    radial-gradient(circle at top right, rgba(255, 233, 206, 0.5), transparent 22%),
    linear-gradient(180deg, rgba(252, 253, 255, 0.88) 0%, rgba(245, 248, 252, 0.92) 100%);
  box-shadow: 0 24px 60px rgba(35, 56, 81, 0.08);
  backdrop-filter: blur(12px);
}

.content-stage-inner {
  min-height: 100%;
  padding: 18px;
  border-radius: 26px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.48), rgba(255, 255, 255, 0.24));
}

@media (max-width: 960px) {
  .layout-shell {
    grid-template-columns: 1fr;
  }

  .side-panel {
    position: static;
    height: auto;
  }

  .content-topbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .content-topbar-tags {
    justify-content: flex-start;
  }

  .content-stage {
    min-height: auto;
    padding: 8px;
  }

  .content-stage-inner {
    padding: 12px;
  }
}
</style>
