<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">教学分析 / 分析中心</div>
        <h2 class="page-title">分析中心</h2>
        <p class="page-subtitle">
          当前覆盖学生、班级、年级和任课教师分析，依赖考试快照和任教关系，不在前端硬编码计算规则。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>考试</strong>{{ examOptions.length }}</span>
          <span class="page-chip"><strong>学生</strong>{{ studentOptions.length }}</span>
          <span class="page-chip"><strong>教师</strong>{{ teacherOptions.length }}</span>
          <span class="page-chip"><strong>当前考试</strong>{{ selectedExamName }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="loadOptions">重载选项</el-button>
        <el-button type="primary" plain @click="resetAnalyticsState">清空结果</el-button>
      </div>
    </header>

    <section class="analysis-hero-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">分析上下文</div>
        <h3>{{ selectedExamName }}</h3>
        <p>先锁定同一场考试，再切学生、班级、年级和教师四个维度，避免跨考试横跳导致判断失真。</p>
      </article>
      <article v-for="item in analyticsOverviewCards" :key="item.label" class="soft-card overview-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head compact">
        <div>
          <h3>选择考试</h3>
          <p>所有分析结果都围绕同一场考试展开，切换考试后建议重新查看各个分析维度。</p>
        </div>
      </div>
      <div class="filter-grid">
        <el-select v-model="selectedExamId" filterable placeholder="请选择考试">
          <el-option
            v-for="exam in examOptions"
            :key="exam.id"
            :label="exam.name"
            :value="exam.id"
          />
        </el-select>
      </div>
    </section>

    <el-tabs>
      <el-tab-pane label="学生分析">
        <section class="soft-card panel-block">
          <div class="section-head compact">
            <div>
              <h3>学生分析</h3>
              <p>查看单个学生的总分、名次和分科变化，适合接学生详情页继续追踪。</p>
            </div>
          </div>
          <div class="action-row">
            <el-select v-model="selectedStudentId" filterable placeholder="选择学生" style="width: 320px">
              <el-option
                v-for="student in studentOptions"
                :key="student.id"
                :label="`${student.student_no} - ${student.name}`"
                :value="student.id"
              />
            </el-select>
            <el-button type="primary" @click="loadStudentAnalytics">查询</el-button>
          </div>
          <div v-if="studentAnalytics" class="metric-grid analytics-grid">
            <div class="soft-card stat-card">
              <div class="metric-label">总分</div>
              <div class="metric-value">{{ studentAnalytics.total_score }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">班级名次</div>
              <div class="metric-value">{{ studentAnalytics.class_rank ?? "-" }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">年级名次</div>
              <div class="metric-value">{{ studentAnalytics.grade_rank ?? "-" }}</div>
            </div>
          </div>
          <div v-if="studentAnalytics" class="table-shell table-gap">
            <el-table :data="studentAnalytics.subjects" stripe>
              <el-table-column label="科目" prop="subject_name" min-width="120" />
              <el-table-column label="分数" prop="score" width="90" />
              <el-table-column label="班名" prop="class_rank" width="90" />
              <el-table-column label="年名" prop="grade_rank" width="90" />
              <el-table-column label="班百分位" prop="class_percentile" width="110" />
              <el-table-column label="年百分位" prop="grade_percentile" width="110" />
              <el-table-column label="分数变化" prop="score_delta" width="110" />
              <el-table-column label="名次变化" prop="rank_delta" width="110" />
            </el-table>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="班级分析">
        <section class="soft-card panel-block">
          <div class="section-head compact">
            <div>
              <h3>班级分析</h3>
              <p>用于看单个班的整体均分、中位数和分科质量，适合班级横向比较前先单独确认。</p>
            </div>
          </div>
          <div class="action-row">
            <el-select v-model="selectedClassId" filterable placeholder="选择班级" style="width: 280px">
              <el-option
                v-for="schoolClass in referenceStore.classes"
                :key="schoolClass.id"
                :label="schoolClass.name"
                :value="schoolClass.id"
              />
            </el-select>
            <el-button type="primary" @click="loadClassAnalytics">查询</el-button>
          </div>
          <div v-if="classAnalytics" class="metric-grid analytics-grid">
            <div class="soft-card stat-card">
              <div class="metric-label">总分均分</div>
              <div class="metric-value">{{ classAnalytics.total_average }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">总分中位数</div>
              <div class="metric-value">{{ classAnalytics.total_median }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">年级均分</div>
              <div class="metric-value">{{ classAnalytics.grade_average ?? "-" }}</div>
            </div>
          </div>
          <div v-if="classAnalytics" class="table-shell table-gap">
            <el-table :data="classAnalytics.subject_breakdown" stripe>
              <el-table-column label="科目" prop="subject_name" min-width="120" />
              <el-table-column label="均分" prop="average_score" width="90" />
              <el-table-column label="中位数" prop="median_score" width="100" />
              <el-table-column label="最高分" prop="max_score" width="90" />
              <el-table-column label="最低分" prop="min_score" width="90" />
              <el-table-column label="标准差" prop="standard_deviation" width="100" />
              <el-table-column label="优秀率" prop="excellent_rate" width="100" />
              <el-table-column label="及格率" prop="pass_rate" width="100" />
            </el-table>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="年级分析">
        <section class="soft-card panel-block">
          <div class="section-head compact">
            <div>
              <h3>年级分析</h3>
              <p>同时看年级整体表现、分数段和班级横向对比，适合校级和年级层判断。</p>
            </div>
          </div>
          <div class="action-row">
            <el-select v-model="selectedGradeId" filterable placeholder="选择年级" style="width: 280px">
              <el-option
                v-for="grade in referenceStore.grades"
                :key="grade.id"
                :label="grade.name"
                :value="grade.id"
              />
            </el-select>
            <el-button type="primary" @click="loadGradeAnalytics">查询</el-button>
          </div>
          <div v-if="gradeAnalytics" class="metric-grid analytics-grid">
            <div class="soft-card stat-card">
              <div class="metric-label">年级均分</div>
              <div class="metric-value">{{ gradeAnalytics.total_average }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">年级中位数</div>
              <div class="metric-value">{{ gradeAnalytics.total_median }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">优秀率</div>
              <div class="metric-value">{{ gradeAnalytics.excellent_rate ?? "-" }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">学生数</div>
              <div class="metric-value">{{ gradeAnalytics.student_count }}</div>
            </div>
          </div>

          <div v-if="gradeAnalytics" class="distribution-grid">
            <article class="soft-card distribution-card">
              <h4>分数段</h4>
              <div class="distribution-list">
                <div v-for="item in gradeAnalytics.score_bands" :key="item.label" class="distribution-item">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
              </div>
            </article>
            <article class="soft-card distribution-card">
              <h4>名次段</h4>
              <div class="distribution-list">
                <div v-for="item in gradeAnalytics.rank_bands" :key="item.label" class="distribution-item">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.count }}</strong>
                </div>
              </div>
            </article>
          </div>

          <div v-if="gradeAnalytics" class="split-grid">
            <section class="soft-card inner-panel">
              <div class="inner-head">
                <h4>班级横向对比</h4>
              </div>
              <div class="table-shell">
                <el-table :data="gradeAnalytics.class_breakdown" stripe>
                  <el-table-column label="班级" prop="class_name" min-width="100" />
                  <el-table-column label="人数" prop="student_count" width="80" />
                  <el-table-column label="均分" prop="average_score" width="90" />
                  <el-table-column label="中位数" prop="median_score" width="90" />
                  <el-table-column label="最高分" prop="max_score" width="90" />
                  <el-table-column label="优秀率" prop="excellent_rate" width="100" />
                </el-table>
              </div>
            </section>
            <section class="soft-card inner-panel">
              <div class="inner-head">
                <h4>学科横向对比</h4>
              </div>
              <div class="table-shell">
                <el-table :data="gradeAnalytics.subject_breakdown" stripe>
                  <el-table-column label="学科" prop="subject_name" min-width="100" />
                  <el-table-column label="均分" prop="average_score" width="90" />
                  <el-table-column label="优秀率" prop="excellent_rate" width="100" />
                  <el-table-column label="及格率" prop="pass_rate" width="100" />
                  <el-table-column label="贡献度" prop="contribution_rate" width="100" />
                </el-table>
              </div>
            </section>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="教师分析">
        <section class="soft-card panel-block">
          <div class="section-head compact">
            <div>
              <h3>教师分析</h3>
              <p>围绕考试快照和任教关系看教师均分与班级拆分，适合接教师详情继续下钻。</p>
            </div>
          </div>
          <div class="action-row">
            <el-select v-model="selectedTeacherId" filterable placeholder="选择教师" style="width: 280px">
              <el-option
                v-for="teacher in teacherOptions"
                :key="teacher.id"
                :label="teacher.name"
                :value="teacher.id"
              />
            </el-select>
            <el-button type="primary" @click="loadTeacherAnalytics">查询</el-button>
          </div>
          <div v-if="teacherAnalytics" class="metric-grid analytics-grid">
            <div class="soft-card stat-card">
              <div class="metric-label">教师均分</div>
              <div class="metric-value">{{ teacherAnalytics.overall_average ?? "-" }}</div>
            </div>
          </div>
          <div v-if="teacherAnalytics" class="table-shell table-gap">
            <el-table
              :data="teacherAnalytics.assignment_breakdown"
              stripe
            >
              <el-table-column label="班级" prop="class_name" min-width="100" />
              <el-table-column label="学科" prop="subject_name" min-width="100" />
              <el-table-column label="均分" prop="average_score" width="90" />
              <el-table-column label="优秀率" prop="excellent_rate" width="100" />
              <el-table-column label="及格率" prop="pass_rate" width="100" />
              <el-table-column label="有效人数" prop="valid_count" width="100" />
            </el-table>
          </div>
        </section>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest } from "../api/client";
import { useReferenceStore } from "../stores/reference";

interface ExamOption {
  id: number;
  name: string;
}

interface StudentOption {
  id: number;
  student_no: string;
  name: string;
}

interface TeacherOption {
  id: number;
  name: string;
}

const referenceStore = useReferenceStore();
const examOptions = ref<ExamOption[]>([]);
const studentOptions = ref<StudentOption[]>([]);
const teacherOptions = ref<TeacherOption[]>([]);

const selectedExamId = ref<number | null>(null);
const selectedStudentId = ref<number | null>(null);
const selectedClassId = ref<number | null>(null);
const selectedGradeId = ref<number | null>(null);
const selectedTeacherId = ref<number | null>(null);

const studentAnalytics = ref<any>(null);
const classAnalytics = ref<any>(null);
const gradeAnalytics = ref<any>(null);
const teacherAnalytics = ref<any>(null);
const selectedExamName = computed(
  () => examOptions.value.find((item) => item.id === selectedExamId.value)?.name ?? "未选择考试",
);
const analyticsOverviewCards = computed(() => [
  {
    label: "学生结果",
    value: studentAnalytics.value ? studentAnalytics.value.subjects?.length ?? 0 : 0,
    help: "当前学生分析里可查看的分科条目。",
    tone: "tone-blue",
  },
  {
    label: "班级结果",
    value: classAnalytics.value ? classAnalytics.value.subject_breakdown?.length ?? 0 : 0,
    help: "当前班级分析里的学科拆分数量。",
    tone: "tone-amber",
  },
  {
    label: "年级结果",
    value: gradeAnalytics.value ? gradeAnalytics.value.student_count ?? 0 : 0,
    help: "当前年级分析覆盖的学生数。",
    tone: "tone-slate",
  },
]);

async function loadOptions(): Promise<void> {
  await referenceStore.loadCore();
  const [examPayload, studentPayload, teacherPayload] = await Promise.all([
    apiRequest<{ items: ExamOption[] }>("/api/exams?page=1&page_size=100"),
    apiRequest<{ items: StudentOption[] }>("/api/students?page=1&page_size=200"),
    apiRequest<{ items: TeacherOption[] }>("/api/teachers?page=1&page_size=200"),
  ]);
  examOptions.value = examPayload.items;
  studentOptions.value = studentPayload.items;
  teacherOptions.value = teacherPayload.items;
}

async function loadStudentAnalytics(): Promise<void> {
  if (!selectedExamId.value || !selectedStudentId.value) return;
  try {
    studentAnalytics.value = await apiRequest(`/api/analytics/students/${selectedStudentId.value}?exam_id=${selectedExamId.value}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadClassAnalytics(): Promise<void> {
  if (!selectedExamId.value || !selectedClassId.value) return;
  try {
    classAnalytics.value = await apiRequest(`/api/analytics/classes/${selectedClassId.value}?exam_id=${selectedExamId.value}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadTeacherAnalytics(): Promise<void> {
  if (!selectedExamId.value || !selectedTeacherId.value) return;
  try {
    teacherAnalytics.value = await apiRequest(`/api/analytics/teachers/${selectedTeacherId.value}?exam_id=${selectedExamId.value}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadGradeAnalytics(): Promise<void> {
  if (!selectedExamId.value || !selectedGradeId.value) return;
  try {
    gradeAnalytics.value = await apiRequest(`/api/analytics/grades/${selectedGradeId.value}?exam_id=${selectedExamId.value}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function resetAnalyticsState(): void {
  studentAnalytics.value = null;
  classAnalytics.value = null;
  gradeAnalytics.value = null;
  teacherAnalytics.value = null;
}

onMounted(async () => {
  try {
    await loadOptions();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
});
</script>

<style scoped>
.analysis-hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) repeat(3, minmax(0, 0.7fr));
  gap: 16px;
}

.overview-panel,
.overview-card {
  padding: 24px;
}

.overview-panel {
  background:
    radial-gradient(circle at top left, rgba(180, 219, 243, 0.32), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(244, 248, 252, 0.94));
}

.overview-kicker {
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

.overview-panel h3 {
  margin: 14px 0 0;
  color: #1f3448;
  font-size: 28px;
  line-height: 1.25;
}

.overview-panel p {
  margin: 12px 0 0;
  color: #62788c;
  line-height: 1.7;
}

.overview-card {
  display: grid;
  align-content: end;
  gap: 10px;
}

.overview-card span {
  color: #6d8194;
  font-size: 13px;
}

.overview-card strong {
  color: #1f3245;
  font-size: 30px;
  font-weight: 760;
}

.overview-card p {
  margin: 0;
  color: #73879b;
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

.analytics-grid {
  margin-top: 16px;
}

.stat-card {
  padding: 18px 20px;
}

.table-gap {
  margin-top: 16px;
}

.distribution-grid,
.split-grid {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.distribution-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.split-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.distribution-card,
.inner-panel {
  padding: 18px;
}

.distribution-card h4,
.inner-head h4 {
  margin: 0 0 12px;
}

.distribution-list {
  display: grid;
  gap: 10px;
}

.distribution-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(242, 247, 251, 0.76);
}

@media (max-width: 1180px) {
  .analysis-hero-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .distribution-grid,
  .split-grid {
    grid-template-columns: 1fr;
  }
}
</style>
