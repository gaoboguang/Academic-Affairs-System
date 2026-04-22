<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>成长档案打印预览</strong>
        <p>建议在浏览器中选择“打印”或“另存为 PDF”。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载成长档案...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="profile" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">学生成长档案 / 打印摘要</div>
          <h1>{{ profile.student.name }}</h1>
          <p>{{ profile.student.student_no }} · {{ profile.student.current_grade_name ?? "未分年级" }} {{ profile.student.current_class_name ?? "" }}</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item">
            <span>记录总数</span>
            <strong>{{ records.length }}</strong>
          </div>
          <div class="print-summary-item">
            <span>成长类型</span>
            <strong>{{ new Set(records.map((item) => item.record_type)).size }}</strong>
          </div>
          <div class="print-summary-item">
            <span>附件数量</span>
            <strong>{{ attachmentCount }}</strong>
          </div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head">
          <h2>摘要概览</h2>
        </div>
        <PrintInsightCards :cards="insightCards" />
      </section>

      <section class="print-section">
        <div class="print-section-head">
          <h2>成长记录</h2>
          <span>{{ records.length }} 条</span>
        </div>
        <table v-if="records.length" class="print-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>类型</th>
              <th>标题</th>
              <th>内容</th>
              <th>责任人</th>
              <th>附件</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in records" :key="item.id">
              <td>{{ item.occurred_on }}</td>
              <td>{{ typeLabel(item.record_type) }}</td>
              <td>{{ item.title }}</td>
              <td>{{ item.content || "-" }}</td>
              <td>{{ item.owner_name || "-" }}</td>
              <td>{{ item.attachments.length ? item.attachments.map((attachment) => attachment.file.original_filename).join(" / ") : "-" }}</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="print-empty">当前学生暂无成长记录。</div>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "../api/client";
import PrintInsightCards from "../components/reports/PrintInsightCards.vue";
import { buildGrowthInsightCards } from "../components/reports/reportInsights";

interface UploadedAttachment {
  id: number;
  original_filename: string;
  download_url: string;
}

interface RecordAttachment {
  id: number;
  stored_file_id: number;
  file: UploadedAttachment;
}

interface GrowthRecord {
  id: number;
  student_id: number;
  occurred_on: string;
  record_type: string;
  title: string;
  content?: string | null;
  owner_name?: string | null;
  attachments: RecordAttachment[];
}

interface GrowthListResponse {
  items: GrowthRecord[];
  total: number;
}

interface StudentProfile {
  student: {
    id: number;
    student_no: string;
    name: string;
    current_grade_name?: string | null;
    current_class_name?: string | null;
  };
}

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const profile = ref<StudentProfile | null>(null);
const records = ref<GrowthRecord[]>([]);

const attachmentCount = computed(() =>
  records.value.reduce((sum, item) => sum + item.attachments.length, 0),
);
const insightCards = computed(() =>
  profile.value
    ? buildGrowthInsightCards({
        profile: profile.value,
        records: records.value,
      })
    : [],
);

const recordTypeOptions: Record<string, string> = {
  reward: "奖励记录",
  discipline: "处分记录",
  activity: "活动记录",
  cadre: "干部任职",
  interview: "谈话记录",
  home_school: "家校沟通",
  mental_health: "心理关注",
  quality_eval: "综合素质评价",
  other: "其他",
};

function typeLabel(value: string): string {
  return recordTypeOptions[value] ?? value;
}

function goBack(): void {
  window.history.back();
}

function printPage(): void {
  window.print();
}

async function loadPrintData(): Promise<void> {
  const studentId = Number(route.params.studentId);
  if (!studentId) {
    errorMessage.value = "打印参数无效";
    return;
  }

  profile.value = await apiRequest<StudentProfile>(`/api/students/${studentId}/profile`);
  const timeline = await apiRequest<GrowthListResponse>(`/api/archives/students/${studentId}/records`);
  records.value = timeline.items;
}

onMounted(async () => {
  try {
    await loadPrintData();
  } catch (error) {
    errorMessage.value = (error as Error).message;
  } finally {
    loading.value = false;
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
  max-width: 1080px;
  margin: 0 auto 20px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(123, 141, 158, 0.14);
}

.print-toolbar p {
  margin: 6px 0 0;
  color: #6d8194;
}

.print-page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 28px;
  background: #ffffff;
  border-radius: 24px;
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
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.print-header h1 {
  margin: 10px 0 0;
  font-size: 32px;
}

.print-header p {
  margin: 8px 0 0;
  color: #62778a;
}

.print-summary-grid {
  display: grid;
  gap: 12px;
  min-width: 220px;
}

.print-summary-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(245, 249, 252, 0.92);
  border: 1px solid rgba(123, 141, 158, 0.12);
}

.print-summary-item span {
  color: #6e8397;
  font-size: 12px;
}

.print-summary-item strong {
  display: block;
  margin-top: 8px;
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
  margin-bottom: 12px;
}

.print-section-head h2 {
  margin: 0;
  font-size: 20px;
}

.print-section-head span {
  color: #6d8194;
  font-size: 13px;
}

.print-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.print-table th,
.print-table td {
  padding: 10px 12px;
  border: 1px solid rgba(123, 141, 158, 0.2);
  text-align: left;
  vertical-align: top;
  line-height: 1.55;
}

.print-table th {
  background: rgba(243, 247, 250, 0.96);
}

.print-placeholder,
.print-empty {
  color: #6d8194;
  line-height: 1.7;
}

.print-placeholder.danger {
  color: #b24b3b;
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
    margin: 0;
    padding: 0;
    border-radius: 0;
    box-shadow: none;
  }
}
</style>
