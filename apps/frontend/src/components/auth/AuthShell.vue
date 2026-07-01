<template>
  <main class="auth-shell">
    <section class="auth-layout" aria-label="账号访问">
      <aside class="auth-aside">
        <div class="auth-brand">
          <div class="brand-mark">教</div>
          <div>
            <p>{{ eyebrow }}</p>
            <h1>本地教务工具</h1>
          </div>
        </div>

        <div class="auth-positioning">
          <span>{{ badge }}</span>
          <strong>{{ title }}</strong>
          <p>{{ description }}</p>
        </div>

        <div class="auth-cues" aria-label="系统特性">
          <span>本地优先</span>
          <span>受控账号</span>
          <span>中文后台</span>
        </div>
      </aside>

      <section class="auth-card">
        <div class="auth-card-head">
          <span>{{ panelBadge }}</span>
          <h2>{{ panelTitle }}</h2>
          <p v-if="panelDescription">{{ panelDescription }}</p>
        </div>
        <slot />
      </section>
    </section>
  </main>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    eyebrow?: string;
    badge?: string;
    title?: string;
    description?: string;
    panelBadge?: string;
    panelTitle: string;
    panelDescription?: string;
  }>(),
  {
    eyebrow: "学校教务",
    badge: "离线优先",
    title: "学校服务器受控访问",
    description: "数据保存在本机或学校服务器，由管理员创建账号并分配访问范围。",
    panelBadge: "账号验证",
    panelDescription: "",
  },
);
</script>

<style scoped>
.auth-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px;
  background:
    linear-gradient(90deg, rgba(22, 119, 179, 0.08) 0 1px, transparent 1px 100%),
    linear-gradient(180deg, rgba(88, 121, 149, 0.08) 0 1px, transparent 1px 100%),
    #f4f7fa;
  background-size: 34px 34px;
}

.auth-layout {
  width: min(920px, 100%);
  min-height: 560px;
  display: grid;
  grid-template-columns: minmax(300px, 0.92fr) minmax(360px, 1fr);
  border: 1px solid rgba(123, 141, 158, 0.24);
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 24px 60px rgba(31, 50, 69, 0.12);
}

.auth-aside {
  display: grid;
  align-content: space-between;
  gap: 34px;
  padding: 34px;
  color: #f8fbfd;
  background: #1f405b;
}

.auth-brand {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-mark {
  width: 46px;
  height: 46px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: #f2b15e;
  color: #1f3245;
  font-size: 21px;
  font-weight: 760;
}

.auth-brand p,
.auth-positioning p {
  margin: 0;
  color: rgba(248, 251, 253, 0.72);
  line-height: 1.7;
}

.auth-brand h1 {
  margin: 4px 0 0;
  color: #fff;
  font-size: 24px;
  font-weight: 760;
}

.auth-positioning {
  display: grid;
  gap: 14px;
}

.auth-positioning span,
.auth-card-head span {
  width: fit-content;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.auth-positioning span {
  color: #1f405b;
  background: #cfe5d4;
}

.auth-positioning strong {
  max-width: 360px;
  color: #fff;
  font-size: 36px;
  line-height: 1.18;
  font-weight: 780;
}

.auth-cues {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.auth-cues span {
  padding: 7px 10px;
  border: 1px solid rgba(248, 251, 253, 0.2);
  border-radius: 8px;
  color: rgba(248, 251, 253, 0.82);
  background: rgba(255, 255, 255, 0.08);
  font-size: 12px;
}

.auth-card {
  display: grid;
  align-content: center;
  gap: 22px;
  padding: 42px;
}

.auth-card-head {
  display: grid;
  gap: 8px;
}

.auth-card-head span {
  color: #1f6c98;
  background: rgba(31, 108, 152, 0.1);
}

.auth-card-head h2 {
  margin: 0;
  color: #203549;
  font-size: 26px;
  font-weight: 760;
}

.auth-card-head p {
  margin: 0;
  color: #687d90;
  line-height: 1.65;
}

@media (max-width: 840px) {
  .auth-shell {
    padding: 18px;
  }

  .auth-layout {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .auth-aside {
    gap: 26px;
    padding: 26px;
  }

  .auth-positioning strong {
    font-size: 28px;
  }

  .auth-card {
    padding: 28px;
  }
}
</style>
