<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">教师详情</div>
        <h2 class="page-title">
          {{ profile?.teacher.name ?? "教师详情" }}
          <span v-if="profile" class="title-meta">{{ profile.teacher.teacher_no }}</span>
        </h2>
        <p class="page-subtitle">
          在一个页面里看教师基础信息、职称历史、任教安排、考试趋势和同学科横向对比。
        </p>
        <div v-if="profile" class="page-chip-row">
          <span class="page-chip"><strong>当前学科</strong>{{ profile.teacher.subject_name ?? "未设置" }}</span>
          <span class="page-chip"><strong>当前职称</strong>{{ resolveTitle(profile.teacher.title_code) }}</span>
          <span class="page-chip"><strong>任教状态</strong>{{ resolveStatus(profile.teacher.employment_status) }}</span>
          <span class="page-chip"><strong>班主任</strong>{{ profile.teacher.is_head_teacher ? "是" : "否" }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="router.push('/teachers')">返回列表</el-button>
        <el-button @click="router.push('/analytics')">分析中心</el-button>
        <el-button type="primary" @click="router.push('/reports')">报表中心</el-button>
      </div>
    </header>

    <template v-if="profile">
      <section class="profile-hero-grid">
        <article class="soft-card hero-summary-card">
          <div class="hero-kicker">教学画像</div>
          <h3>{{ heroHeadline }}</h3>
          <p>{{ teacherNarrative }}</p>
          <div class="hero-meta-grid">
            <div class="hero-meta-item">
              <span>岗位</span>
              <strong>{{ resolvePosition(profile.teacher.position_code) }}</strong>
            </div>
            <div class="hero-meta-item">
              <span>入职日期</span>
              <strong>{{ profile.teacher.entry_date ?? "未填写" }}</strong>
            </div>
            <div class="hero-meta-item">
              <span>最近考试均分</span>
              <strong>{{ latestTrend?.overall_average ?? "-" }}</strong>
            </div>
            <div class="hero-meta-item">
              <span>同科差值</span>
              <strong>{{ latestTrend?.peer_gap ?? "暂无" }}</strong>
            </div>
          </div>
        </article>

        <article
          v-for="item in teacherHeroCards"
          :key="item.label"
          class="soft-card hero-mini-card"
          :class="item.tone"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.help }}</p>
        </article>
      </section>

      <section class="metric-grid">
        <article class="soft-card stat-card">
          <span>当前学科</span>
          <strong>{{ profile.teacher.subject_name ?? "-" }}</strong>
        </article>
        <article class="soft-card stat-card">
          <span>当前职称</span>
          <strong>{{ resolveTitle(profile.teacher.title_code) }}</strong>
        </article>
        <article class="soft-card stat-card">
          <span>最近考试均分</span>
          <strong>{{ latestTrend?.overall_average ?? "-" }}</strong>
        </article>
        <article class="soft-card stat-card">
          <span>在用任教关系</span>
          <strong>{{ activeAssignmentCount }}</strong>
        </article>
      </section>

      <el-tabs class="profile-tabs">
        <el-tab-pane label="基础信息">
          <section class="soft-card detail-card">
            <div class="detail-grid">
              <div class="detail-item">
                <span>联系电话</span>
                <strong>{{ profile.teacher.phone ?? "-" }}</strong>
              </div>
              <div class="detail-item">
                <span>岗位</span>
                <strong>{{ resolvePosition(profile.teacher.position_code) }}</strong>
              </div>
              <div class="detail-item">
                <span>任教状态</span>
                <strong>{{ resolveStatus(profile.teacher.employment_status) }}</strong>
              </div>
              <div class="detail-item">
                <span>是否班主任</span>
                <strong>{{ profile.teacher.is_head_teacher ? "是" : "否" }}</strong>
              </div>
              <div class="detail-item">
                <span>入职日期</span>
                <strong>{{ profile.teacher.entry_date ?? "-" }}</strong>
              </div>
              <div class="detail-item">
                <span>备注</span>
                <strong>{{ profile.teacher.note ?? "-" }}</strong>
              </div>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="职称历史">
          <section class="soft-card detail-card">
            <div class="section-head">
              <div>
                <h3>职称与岗位历史</h3>
                <p>保留历史，不覆盖旧记录；保存后会同步当前职称。</p>
              </div>
              <div class="action-row">
                <el-button @click="addHistoryRow">新增一条</el-button>
                <el-button type="primary" :loading="savingHistory" @click="saveHistories">保存历史</el-button>
              </div>
            </div>
            <div v-if="titleHistories.length" class="history-list">
              <article v-for="(item, index) in titleHistories" :key="index" class="history-row">
                <div class="history-grid">
                  <el-select v-model="item.title_code" placeholder="选择职称">
                    <el-option
                      v-for="option in referenceStore.dicts.teacher_title ?? []"
                      :key="String(option.code)"
                      :label="option.name"
                      :value="option.code"
                    />
                  </el-select>
                  <el-date-picker
                    v-model="item.start_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    format="YYYY-MM-DD"
                    placeholder="开始日期"
                  />
                  <el-date-picker
                    v-model="item.end_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    format="YYYY-MM-DD"
                    placeholder="结束日期"
                  />
                  <el-input v-model="item.note" placeholder="备注" />
                </div>
                <div class="history-actions">
                  <el-button link type="danger" @click="removeHistoryRow(index)">移除</el-button>
                </div>
              </article>
            </div>
            <el-empty v-else description="暂无职称历史" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="任教安排">
          <section class="soft-card detail-card">
            <div class="table-shell">
              <el-table :data="profile.assignments" stripe>
                <el-table-column label="学期" prop="semester_name" min-width="180" />
                <el-table-column label="年级" prop="grade_name" width="100" />
                <el-table-column label="班级" prop="class_name" width="100" />
                <el-table-column label="学科" prop="subject_name" width="120" />
                <el-table-column label="课程类型" prop="course_type" width="120" />
                <el-table-column label="周课时" prop="weekly_periods_manual" width="100" />
              </el-table>
            </div>
            <el-empty v-if="!profile.assignments.length" description="暂无任教安排" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="考试趋势">
          <section class="soft-card detail-card">
            <div class="table-shell">
              <el-table :data="profile.recent_exam_trends" stripe>
                <el-table-column label="考试" prop="exam_name" min-width="220" />
                <el-table-column label="时间" prop="exam_date" width="120" />
                <el-table-column label="学期" prop="semester_name" min-width="160" />
                <el-table-column label="均分" prop="overall_average" width="100" />
                <el-table-column label="优秀率" prop="excellent_rate" width="100" />
                <el-table-column label="及格率" prop="pass_rate" width="100" />
                <el-table-column label="同科均值" prop="peer_average" width="110" />
                <el-table-column label="差值" prop="peer_gap" width="90" />
                <el-table-column label="班级数" prop="class_count" width="90" />
              </el-table>
            </div>
            <el-empty v-if="!profile.recent_exam_trends.length" description="暂无考试趋势数据" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="同科对比">
          <section class="soft-card detail-card">
            <div class="table-shell">
              <el-table :data="profile.peer_comparisons" stripe>
                <el-table-column label="排名" prop="rank" width="80" />
                <el-table-column label="教师" prop="teacher_name" min-width="140" />
                <el-table-column label="学科" prop="subject_name" width="120" />
                <el-table-column label="均分" prop="overall_average" width="100" />
                <el-table-column label="优秀率" prop="excellent_rate" width="100" />
                <el-table-column label="及格率" prop="pass_rate" width="100" />
                <el-table-column label="任教关系数" prop="assignment_count" width="110" />
              </el-table>
            </div>
            <el-empty v-if="!profile.peer_comparisons.length" description="暂无同学科横向对比数据" />
          </section>
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import { useRoute, useRouter } from "vue-router";

import { apiRequest } from "../api/client";
import { useReferenceStore } from "../stores/reference";

interface TeacherTrendItem {
  exam_name?: string | null;
  exam_date?: string | null;
  semester_name?: string | null;
  overall_average?: number | null;
  excellent_rate?: number | null;
  pass_rate?: number | null;
  peer_average?: number | null;
  peer_gap?: number | null;
  class_count?: number | null;
}

interface TeacherAssignmentItem {
  is_active: boolean;
  semester_name?: string | null;
  grade_name?: string | null;
  class_name?: string | null;
  subject_name?: string | null;
  course_type?: string | null;
  weekly_periods_manual?: number | null;
}

interface PeerComparisonItem {
  rank?: number | null;
  teacher_name?: string | null;
  subject_name?: string | null;
  overall_average?: number | null;
  excellent_rate?: number | null;
  pass_rate?: number | null;
  assignment_count?: number | null;
}

interface TeacherProfile {
  teacher: {
    id: number;
    teacher_no: string;
    name: string;
    subject_name?: string | null;
    title_code?: string | null;
    position_code?: string | null;
    employment_status?: string | null;
    phone?: string | null;
    entry_date?: string | null;
    note?: string | null;
    is_head_teacher: boolean;
  };
  title_histories: Array<{
    title_code: string;
    start_date?: string | null;
    end_date?: string | null;
    note?: string | null;
  }>;
  assignments: TeacherAssignmentItem[];
  recent_exam_trends: TeacherTrendItem[];
  peer_comparisons: PeerComparisonItem[];
}

interface TitleHistoryPayload {
  title_code: string;
  start_date?: string | null;
  end_date?: string | null;
  note?: string | null;
  is_active: boolean;
}

const route = useRoute();
const router = useRouter();
const referenceStore = useReferenceStore();
const profile = ref<TeacherProfile | null>(null);
const titleHistories = ref<TitleHistoryPayload[]>([]);
const savingHistory = ref(false);

const activeAssignmentCount = computed(
  () => profile.value?.assignments.filter((item) => item.is_active).length ?? 0,
);

const latestTrend = computed(() => profile.value?.recent_exam_trends[0] ?? null);

const heroHeadline = computed(() => latestTrend.value?.exam_name ?? "暂无最近考试画像");

const teacherNarrative = computed(() => {
  if (!profile.value) return "暂无教师画像";
  const latestAverage = latestTrend.value?.overall_average ?? "暂无";
  return `${profile.value.teacher.subject_name ?? "未配置学科"}教师，当前有 ${activeAssignmentCount.value} 条在用任教关系，最近考试均分 ${latestAverage}。`;
});

const teacherHeroCards = computed(() => {
  if (!profile.value) return [];
  return [
    {
      label: "职称历史",
      value: titleHistories.value.length,
      help: "历史记录保留后会同步当前职称。",
      tone: "tone-blue",
    },
    {
      label: "在用任教",
      value: activeAssignmentCount.value,
      help: "当前仍有效的任教关系数量。",
      tone: "tone-green",
    },
    {
      label: "考试样本",
      value: profile.value.recent_exam_trends.length,
      help: "用于追踪近期考试表现的样本。",
      tone: "tone-amber",
    },
    {
      label: "同科对比",
      value: profile.value.peer_comparisons.length,
      help: "当前可用于横向比较的同科样本。",
      tone: "tone-slate",
    },
  ];
});

function resolveDictName(dictCode: string, code?: string | null): string {
  if (!code) return "-";
  return (
    referenceStore.dicts[dictCode]?.find((item) => String(item.code) === String(code))?.name ?? code
  );
}

function resolveTitle(code?: string | null): string {
  return resolveDictName("teacher_title", code);
}

function resolvePosition(code?: string | null): string {
  return resolveDictName("teacher_position", code);
}

function resolveStatus(code?: string | null): string {
  return resolveDictName("teacher_status", code);
}

function addHistoryRow(): void {
  titleHistories.value.unshift({
    title_code: "",
    start_date: null,
    end_date: null,
    note: "",
    is_active: true,
  });
}

function removeHistoryRow(index: number): void {
  titleHistories.value.splice(index, 1);
}

async function loadProfile(): Promise<void> {
  try {
    profile.value = await apiRequest<TeacherProfile>(`/api/teachers/${route.params.teacherId}/profile`);
    titleHistories.value = profile.value.title_histories.map((item) => ({
      title_code: item.title_code,
      start_date: item.start_date ?? null,
      end_date: item.end_date ?? null,
      note: item.note ?? "",
      is_active: true,
    }));
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function saveHistories(): Promise<void> {
  try {
    savingHistory.value = true;
    await apiRequest(`/api/teachers/${route.params.teacherId}/title-histories`, {
      method: "PUT",
      body: JSON.stringify(
        titleHistories.value.filter((item) => item.title_code.trim()),
      ),
    });
    ElMessage.success("职称历史已保存");
    await loadProfile();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingHistory.value = false;
  }
}

onMounted(async () => {
  await referenceStore.loadAll();
  await loadProfile();
});
</script>

<style scoped>
.profile-hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) repeat(2, minmax(0, 0.8fr));
  gap: 16px;
}

.hero-summary-card,
.hero-mini-card,
.stat-card,
.detail-card {
  padding: 24px;
}

.hero-summary-card {
  grid-row: span 2;
  background:
    radial-gradient(circle at top left, rgba(180, 219, 243, 0.34), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(244, 248, 252, 0.94));
}

.hero-kicker {
  display: inline-flex;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f6c98;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-summary-card h3 {
  margin: 16px 0 0;
  color: #1d3247;
  font-size: 30px;
}

.hero-summary-card > p {
  margin: 12px 0 0;
  color: #61778b;
  line-height: 1.7;
}

.hero-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 22px;
}

.hero-meta-item {
  padding: 16px;
  border-radius: 18px;
  background: rgba(247, 250, 253, 0.84);
  border: 1px solid rgba(120, 138, 156, 0.12);
}

.hero-meta-item span {
  display: block;
  color: #6f8397;
  font-size: 13px;
}

.hero-meta-item strong {
  display: block;
  margin-top: 8px;
  color: #1f3448;
  line-height: 1.5;
}

.hero-mini-card {
  display: grid;
  align-content: end;
  gap: 10px;
}

.hero-mini-card span {
  color: #6c8094;
  font-size: 13px;
}

.hero-mini-card strong {
  color: #1f3245;
  font-size: 30px;
  font-weight: 760;
}

.hero-mini-card p {
  margin: 0;
  color: #72879b;
  line-height: 1.55;
  font-size: 13px;
}

.tone-blue {
  box-shadow: inset 0 4px 0 rgba(31, 108, 152, 0.78);
}

.tone-amber {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.84);
}

.tone-slate {
  box-shadow: inset 0 4px 0 rgba(92, 111, 129, 0.74);
}

.tone-green {
  box-shadow: inset 0 4px 0 rgba(69, 141, 105, 0.8);
}

.stat-card span {
  display: block;
  color: #6d8092;
  font-size: 13px;
}

.stat-card strong {
  display: block;
  margin-top: 10px;
  color: #1f3245;
  font-size: 28px;
}

.profile-tabs :deep(.el-tabs__item) {
  min-width: 92px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.detail-item {
  padding: 16px;
  border-radius: 18px;
  background: rgba(243, 247, 251, 0.78);
}

.detail-item span {
  display: block;
  color: #6c8094;
  font-size: 13px;
}

.detail-item strong {
  display: block;
  margin-top: 10px;
  line-height: 1.5;
}

.history-list {
  display: grid;
  gap: 12px;
}

.history-row {
  padding: 14px;
  border-radius: 18px;
  background: rgba(248, 251, 253, 0.88);
  border: 1px solid rgba(114, 132, 150, 0.14);
}

.history-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr 1fr 1.2fr;
  gap: 12px;
}

.history-actions {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 1180px) {
  .profile-hero-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-summary-card {
    grid-column: 1 / -1;
    grid-row: auto;
  }
}

@media (max-width: 980px) {
  .detail-grid,
  .history-grid,
  .hero-meta-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .profile-hero-grid {
    grid-template-columns: 1fr;
  }
}
</style>
