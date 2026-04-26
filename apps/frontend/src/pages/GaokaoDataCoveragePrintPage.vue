<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>高考数据覆盖报告</strong>
        <p>用于查看已补齐、部分补齐、官方未发布和需人工复核的数据项。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="report" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">山东高考数据 / 补齐状态</div>
          <h1>{{ report.report_name }}</h1>
          <p>{{ generatedAtText }} · {{ report.schema_version || "版本待确认" }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item">
            <span>交付判断</span>
            <strong>{{ report.delivery_label }}</strong>
          </div>
          <div class="print-summary-item">
            <span>P0 缺口</span>
            <strong>{{ report.gaps.length }}</strong>
          </div>
          <div class="print-summary-item">
            <span>覆盖域</span>
            <strong>{{ report.coverage_matrix.length }}</strong>
          </div>
          <div class="print-summary-item">
            <span>发布项</span>
            <strong>{{ report.publication_status.length }}</strong>
          </div>
        </div>
      </header>

      <section class="print-section">
        <div class="notice-box">
          <strong>{{ report.summary || report.delivery_label }}</strong>
          <p>{{ report.delivery_summary }}</p>
          <p>主库：{{ report.db_path }}</p>
        </div>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>数据库补齐结果说明</h2>
        </div>
        <div class="print-card-grid">
          <div v-for="item in report.result_cards" :key="item.key" class="print-card" :class="`tone-${item.tone}`">
            <strong>{{ item.title }}</strong>
            <span>{{ item.statusLabel }}</span>
            <p>{{ item.summary }}</p>
            <small>{{ item.detail }}</small>
          </div>
        </div>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>2020-2026 覆盖矩阵</h2>
          <span>2026 未发布项不视为历史缺口</span>
        </div>
        <table class="print-table compact">
          <thead>
            <tr>
              <th>数据域</th>
              <th v-for="year in matrixYears" :key="year">{{ year }}</th>
              <th>当前记录</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in report.coverage_matrix" :key="row.key">
              <td>
                <strong>{{ row.label }}</strong>
                <span>{{ row.readinessLabel }}</span>
              </td>
              <td v-for="cell in row.cells" :key="`${row.key}_${cell.year}`">{{ cell.label }}</td>
              <td>{{ row.total }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="print-section two-column-print">
        <div>
          <div class="print-section-head">
            <h2>剩余缺口</h2>
          </div>
          <ul v-if="report.gaps.length" class="print-note-list">
            <li v-for="gap in report.gaps" :key="gap">{{ gap }}</li>
          </ul>
          <div v-else class="print-empty">当前未发现 P0 规则内的明显缺口。</div>
        </div>
        <div>
          <div class="print-section-head">
            <h2>审计摘要</h2>
          </div>
          <ul class="print-note-list">
            <li v-for="item in report.audit_summary" :key="item.key">
              <strong>{{ item.label }}</strong>：当前 {{ item.updated }} 条，待复核 {{ item.pending_review }} 条。
            </li>
          </ul>
        </div>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>2026 发布状态</h2>
        </div>
        <table class="print-table compact">
          <thead>
            <tr>
              <th>数据项</th>
              <th>状态</th>
              <th>下一步</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in report.publication_status" :key="item.key">
              <td>{{ item.label }}</td>
              <td>{{ item.status_label }}</td>
              <td>{{ item.action_label }}</td>
              <td>{{ item.explanation }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="print-section">
        <div class="notice-box">
          <strong>使用边界</strong>
          <p>
            本报告只说明当前本地数据库覆盖状态。官方未发布的数据不能伪造；招生计划补充信息不能当作完整计划；
            章程限制链未人工核验前只能作为风险提示。
          </p>
        </div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import type { DataCompletionPrintPayload } from "../components/gaokao-data/dataCompletionReport";

const route = useRoute();
const report = ref<DataCompletionPrintPayload | null>(null);
const errorMessage = ref("");

const generatedAtText = computed(() => {
  if (!report.value?.generated_at) return "生成时间待确认";
  return new Date(report.value.generated_at).toLocaleString("zh-CN");
});
const matrixYears = computed(() => report.value?.coverage_matrix[0]?.cells.map((item) => item.year) ?? []);

function goBack(): void {
  window.history.back();
}

function printPage(): void {
  window.print();
}

onMounted(() => {
  const storageKey = String(route.params.storageKey || "");
  if (!storageKey) {
    errorMessage.value = "打印参数无效，请回到高考数据页重新打开覆盖报告。";
    return;
  }
  const raw = window.localStorage.getItem(storageKey);
  if (!raw) {
    errorMessage.value = "未找到本次覆盖报告数据，请回到高考数据页刷新后重新打开。";
    return;
  }
  try {
    report.value = JSON.parse(raw) as DataCompletionPrintPayload;
  } catch {
    errorMessage.value = "本次覆盖报告数据无法读取，请回到高考数据页重新生成。";
  }
});
</script>

<style scoped>
.print-shell {
  min-height: 100vh;
  padding: 24px;
  background: #eef3f7;
  color: #1f3348;
}

.print-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  max-width: 1120px;
  margin: 0 auto 20px;
  padding: 16px 18px;
  border: 1px solid rgba(123, 141, 158, 0.14);
  border-radius: 8px;
  background: #ffffff;
}

.print-toolbar p {
  margin: 4px 0 0;
  color: #64788b;
}

.print-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 34px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 18px 48px rgba(31, 51, 72, 0.12);
}

.print-header {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.8fr);
  gap: 22px;
  align-items: start;
  padding-bottom: 22px;
  border-bottom: 2px solid #dce6ef;
}

.print-eyebrow {
  color: #5f7386;
  font-size: 13px;
  font-weight: 700;
}

.print-header h1 {
  margin: 8px 0;
  font-size: 30px;
}

.print-header p {
  margin: 0;
  color: #617589;
}

.print-summary-grid,
.print-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.print-summary-item,
.print-card,
.notice-box {
  border: 1px solid #d8e1ea;
  border-radius: 8px;
  padding: 12px;
  background: #f8fbfd;
}

.print-summary-item span,
.print-card span {
  display: block;
  color: #617589;
  font-size: 12px;
}

.print-summary-item strong {
  display: block;
  margin-top: 4px;
  font-size: 18px;
}

.print-section {
  margin-top: 24px;
}

.print-section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.print-section-head h2 {
  margin: 0;
  font-size: 20px;
}

.print-section-head span {
  color: #617589;
  font-size: 13px;
}

.print-card {
  display: grid;
  gap: 6px;
}

.print-card p,
.print-card small,
.notice-box p {
  margin: 0;
  color: #4e6174;
  line-height: 1.6;
}

.print-card.tone-success {
  border-color: #9ed6b6;
  background: #f3fbf6;
}

.print-card.tone-warning {
  border-color: #f0d39a;
  background: #fffaf0;
}

.print-card.tone-danger {
  border-color: #f2b5b5;
  background: #fff5f5;
}

.print-card.tone-info {
  border-color: #b7d1ef;
  background: #f4f8ff;
}

.print-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.print-table th,
.print-table td {
  padding: 10px;
  border: 1px solid #dce6ef;
  text-align: left;
  vertical-align: top;
}

.print-table th {
  background: #f5f8fb;
}

.print-table td span {
  display: block;
  margin-top: 3px;
  color: #617589;
}

.two-column-print {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.print-note-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding-left: 18px;
  line-height: 1.6;
}

.print-empty,
.print-placeholder {
  padding: 18px;
  border-radius: 8px;
  background: #ffffff;
  color: #617589;
}

.print-placeholder.danger {
  max-width: 880px;
  margin: 24px auto;
  border: 1px solid #f2b5b5;
  color: #9f2d2d;
}

@media print {
  .print-shell {
    padding: 0;
    background: #ffffff;
  }

  .print-toolbar {
    display: none;
  }

  .print-page {
    max-width: none;
    padding: 0;
    box-shadow: none;
  }
}

@media (max-width: 820px) {
  .print-toolbar,
  .print-header,
  .two-column-print {
    grid-template-columns: 1fr;
  }

  .print-toolbar {
    display: grid;
  }

  .print-summary-grid,
  .print-card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
