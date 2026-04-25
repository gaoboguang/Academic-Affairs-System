<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>山东升学路径规划报告</strong>
        <p>建议先和学生逐项复核材料，再在浏览器中打印或另存为 PDF。</p>
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
          <div class="print-eyebrow">山东生源地 / 多路径资格初筛</div>
          <h1>{{ reportTitle }}</h1>
          <p>{{ report.student_name }} · {{ report.target_year }} 年 · {{ generatedAtText }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item">
            <span>路径卡</span>
            <strong>{{ report.cards.length }}</strong>
          </div>
          <div class="print-summary-item">
            <span>材料缺口</span>
            <strong>{{ report.material_gaps.length }}</strong>
          </div>
          <div class="print-summary-item">
            <span>P0 数据缺口</span>
            <strong>{{ report.p0_gaps.length }}</strong>
          </div>
          <div class="print-summary-item">
            <span>数据状态</span>
            <strong>{{ report.data_health_summary || "待检查" }}</strong>
          </div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head">
          <h2>学生升学画像摘要</h2>
        </div>
        <div class="print-meta-grid">
          <div v-for="item in report.profile_summary" :key="item.key" class="print-meta-item">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>路径建议排序</h2>
          <span>只有普通类常规批接入完整位次推荐</span>
        </div>
        <table class="print-table">
          <thead>
            <tr>
              <th>路径</th>
              <th>状态</th>
              <th>推荐深度</th>
              <th>关键要求</th>
              <th>缺失材料</th>
              <th>风险提示</th>
              <th>下一步</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="card in report.cards" :key="card.code">
              <td>
                <strong>{{ card.name }}</strong>
                <span>{{ card.group }} · {{ card.applicable_object }}</span>
              </td>
              <td>{{ card.status_label }}</td>
              <td>{{ card.depth_label }}</td>
              <td>{{ formatList(card.key_requirements) }}</td>
              <td>{{ formatList(card.missing_materials) }}</td>
              <td>{{ formatList(card.risk_messages) }}</td>
              <td>{{ formatList(card.next_actions) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="print-section two-column-print">
        <div>
          <div class="print-section-head">
            <h2>材料缺口</h2>
          </div>
          <ul v-if="report.material_gaps.length" class="print-note-list">
            <li v-for="gap in report.material_gaps" :key="gap.key">
              <strong>{{ gap.label }}</strong>：{{ gap.nextAction }} 影响 {{ gap.count }} 条路径。
            </li>
          </ul>
          <div v-else class="print-empty">当前没有系统识别到的集中材料缺口。</div>
        </div>
        <div>
          <div class="print-section-head">
            <h2>下一步行动</h2>
          </div>
          <ul class="print-note-list">
            <li v-for="item in report.next_actions" :key="item.key">
              <strong>{{ item.title }}</strong>：{{ item.detail }}
            </li>
          </ul>
        </div>
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>2026 数据发布状态与风险</h2>
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
        <ul v-if="report.p0_gaps.length" class="print-note-list">
          <li v-for="gap in report.p0_gaps" :key="gap">{{ gap }}</li>
        </ul>
      </section>

      <section class="print-section">
        <div class="notice-box">
          <strong>边界说明</strong>
          <p>
            本报告用于山东升学路径规划和材料核对。普通类常规批可以进入山东普通类冲稳保推荐；
            单招、综评、春考、艺体、体育、提前批和特殊类型只做资格初筛、政策提醒和人工复核清单，不代表录取概率。
          </p>
        </div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import {
  buildGaokaoPathwayReportName,
  type GaokaoPathwayReportPayload,
} from "../components/gaokao-pathways/pathwayCenter";

const route = useRoute();
const report = ref<GaokaoPathwayReportPayload | null>(null);
const errorMessage = ref("");

const reportTitle = computed(() => (report.value ? buildGaokaoPathwayReportName(report.value) : "山东升学路径规划报告"));
const generatedAtText = computed(() => {
  if (!report.value?.generated_at) return "生成时间待确认";
  return new Date(report.value.generated_at).toLocaleString("zh-CN");
});

function formatList(items: string[]): string {
  return items.length ? items.join("；") : "-";
}

function goBack(): void {
  window.history.back();
}

function printPage(): void {
  window.print();
}

onMounted(() => {
  const storageKey = String(route.params.storageKey || "");
  if (!storageKey) {
    errorMessage.value = "打印参数无效，请回到山东升学方案中心重新打开报告。";
    return;
  }
  const raw = window.localStorage.getItem(storageKey);
  if (!raw) {
    errorMessage.value = "未找到本次路径规划报告数据，请回到山东升学方案中心重新生成报告。";
    return;
  }
  try {
    report.value = JSON.parse(raw) as GaokaoPathwayReportPayload;
  } catch {
    errorMessage.value = "本次路径规划报告数据无法读取，请回到山东升学方案中心重新生成报告。";
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
  margin: 6px 0 0;
  color: #6d8194;
}

.print-page {
  max-width: 1120px;
  margin: 0 auto;
  padding: 28px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 18px 40px rgba(31, 51, 72, 0.08);
}

.print-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(124, 141, 156, 0.16);
}

.print-eyebrow {
  color: #6b8093;
  font-size: 12px;
}

.print-header h1 {
  margin: 10px 0 0;
  font-size: 30px;
}

.print-header p {
  margin: 8px 0 0;
  color: #62778a;
}

.print-summary-grid,
.print-meta-grid {
  display: grid;
  gap: 12px;
}

.print-summary-grid {
  grid-template-columns: repeat(2, minmax(120px, 1fr));
  min-width: 360px;
}

.print-meta-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.print-summary-item,
.print-meta-item {
  padding: 10px 12px;
  border: 1px solid rgba(124, 141, 156, 0.16);
  border-radius: 8px;
  background: #f8fbfd;
}

.print-summary-item span,
.print-meta-item span {
  display: block;
  color: #657a8e;
  font-size: 12px;
}

.print-summary-item strong,
.print-meta-item strong {
  display: block;
  margin-top: 5px;
  color: #1f3348;
}

.print-section {
  margin-top: 24px;
}

.print-section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.print-section-head h2 {
  margin: 0;
  font-size: 18px;
}

.print-section-head span {
  color: #657a8e;
  font-size: 12px;
}

.print-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.print-table th,
.print-table td {
  vertical-align: top;
  padding: 9px;
  border: 1px solid rgba(124, 141, 156, 0.22);
  text-align: left;
}

.print-table th {
  background: #edf4f8;
  color: #34495e;
}

.print-table td span {
  display: block;
  margin-top: 4px;
  color: #6b8093;
}

.print-table.compact td,
.print-table.compact th {
  padding: 8px;
}

.two-column-print {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.print-note-list {
  margin: 0;
  padding-left: 18px;
  color: #40556b;
}

.print-note-list li {
  margin-bottom: 8px;
}

.notice-box,
.print-empty,
.print-placeholder {
  padding: 12px 14px;
  border-radius: 8px;
  background: #fff8e8;
  color: #6a4b12;
}

.print-placeholder.danger {
  max-width: 1120px;
  margin: 0 auto;
  background: #fff2f0;
  color: #a12b1f;
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
</style>
