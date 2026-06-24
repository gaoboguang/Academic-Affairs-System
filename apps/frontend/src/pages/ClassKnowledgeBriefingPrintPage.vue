<template>
  <div class="print-shell">
    <div class="print-toolbar">
      <div>
        <strong>班级知识点讲评报告</strong>
        <p>包含班级共性薄弱知识点、错因分布、弱项学生和讲评建议。</p>
      </div>
      <div class="action-row">
        <el-button @click="goBack">返回</el-button>
        <el-button type="primary" @click="printPage">打印 / 保存为 PDF</el-button>
      </div>
    </div>

    <div v-if="loading" class="print-placeholder">正在加载讲评报告...</div>
    <div v-else-if="errorMessage" class="print-placeholder danger">{{ errorMessage }}</div>
    <article v-else-if="briefing" class="print-page">
      <header class="print-header">
        <div>
          <div class="print-eyebrow">知识点讲评报告 / 班级</div>
          <h1>{{ briefing.class_name }}</h1>
          <p>{{ briefing.exam_name }}</p>
          <p>按弱项学生数、失分规模和错因分布排序。</p>
        </div>
        <div class="print-summary-grid">
          <div class="print-summary-item"><span>讲评知识点</span><strong>{{ briefing.items.length }}</strong></div>
          <div class="print-summary-item"><span>高优先级</span><strong>{{ highPriorityCount }}</strong></div>
          <div class="print-summary-item"><span>生成时间</span><strong>{{ briefing.generated_at?.slice(0, 10) }}</strong></div>
        </div>
      </header>

      <section class="print-section">
        <div class="print-section-head">
          <h2>讲评清单</h2>
        </div>
        <table class="print-table">
          <thead>
            <tr>
              <th>科目</th>
              <th>知识路径</th>
              <th>弱项学生</th>
              <th>平均得分率</th>
              <th>错因分布</th>
              <th>题号</th>
              <th>优先级</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in briefing.items" :key="item.knowledge_point_id">
              <td>{{ item.subject_name }}</td>
              <td>{{ item.knowledge_path || item.knowledge_point_name }}</td>
              <td>{{ item.weak_student_count }} / {{ item.total_student_count }}</td>
              <td>{{ formatPercentValue(item.average_score_rate) }}</td>
              <td>{{ formatErrorTagStats(item.error_tag_stats) }}</td>
              <td>{{ formatQuestionNumbers(item.question_numbers) }}</td>
              <td>{{ item.priority_label }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="print-section" v-for="item in briefing.items" :key="`detail-${item.knowledge_point_id}`">
        <div class="print-section-head">
          <h2>{{ item.subject_name }} · {{ item.knowledge_path || item.knowledge_point_name }}</h2>
          <span>{{ item.priority_label }}优先级</span>
        </div>
        <p class="print-lead">{{ item.suggestion }}</p>
        <table class="print-table">
          <thead>
            <tr>
              <th>学生</th>
              <th>得分率</th>
              <th>失分</th>
              <th>诊断</th>
              <th>主错因</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in item.weak_students" :key="`${item.knowledge_point_id}-${student.student_id}`">
              <td>{{ student.student_name }}</td>
              <td>{{ formatPercentValue(student.score_rate) }}</td>
              <td>{{ student.lost_score }}</td>
              <td>{{ student.diagnosis_label }}</td>
              <td>{{ student.main_error_tag || "-" }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </article>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "../api/client";
import { formatErrorTagStats, formatPercentValue, formatQuestionNumbers } from "../components/analytics/studentReport";

interface BriefingItem {
  subject_name: string;
  knowledge_point_id: number;
  knowledge_point_name: string;
  knowledge_path?: string | null;
  weak_student_count: number;
  total_student_count: number;
  average_score_rate?: number | null;
  question_numbers?: string[];
  error_tag_stats?: Array<{ tag?: string; count?: number }>;
  priority_label: string;
  suggestion: string;
  weak_students: Array<{
    student_id: number;
    student_name: string;
    score_rate?: number | null;
    lost_score: number;
    diagnosis_label: string;
    main_error_tag?: string | null;
  }>;
}

interface BriefingResponse {
  exam_name: string;
  class_name: string;
  generated_at: string;
  items: BriefingItem[];
}

const route = useRoute();
const loading = ref(true);
const errorMessage = ref("");
const briefing = ref<BriefingResponse | null>(null);
const highPriorityCount = computed(() => briefing.value?.items.filter((item) => item.priority_label === "高").length ?? 0);

function goBack(): void {
  window.history.back();
}

function printPage(): void {
  window.print();
}

onMounted(async () => {
  try {
    const classId = Number(route.params.classId);
    const examId = Number(route.params.examId);
    if (!classId || !examId) {
      errorMessage.value = "打印参数无效";
      return;
    }
    briefing.value = await apiRequest<BriefingResponse>(`/api/analytics/classes/${classId}/knowledge-briefing?exam_id=${examId}`);
  } catch (error) {
    errorMessage.value = (error as Error).message;
  } finally {
    loading.value = false;
  }
});
</script>
