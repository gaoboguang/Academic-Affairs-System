<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">学生详情</div>
        <h2 class="page-title">
          {{ profile?.student.name ?? "学生详情" }}
          <span v-if="profile" class="title-meta">{{ profile.student.student_no }}</span>
        </h2>
        <p class="page-subtitle">
          把学籍、成绩、成长档案、推荐记录和附件归到同一页，减少来回切换。
        </p>
        <div v-if="profile" class="page-chip-row">
          <span class="page-chip"><strong>当前班级</strong>{{ currentClassLabel }}</span>
          <span class="page-chip"><strong>学生状态</strong>{{ profile.student.status ?? "未标注" }}</span>
          <span class="page-chip"><strong>学生类别</strong>{{ formatStudentType(profile.student.student_type) }}</span>
          <span class="page-chip"><strong>生源地</strong>{{ profile.student.origin_province ?? "未维护" }}</span>
          <span class="page-chip"><strong>艺体方向</strong>{{ profile.student.art_track ?? "普通方向" }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="router.push('/students')">返回列表</el-button>
        <el-button @click="router.push('/growth-archive')">成长档案</el-button>
        <el-button type="primary" @click="router.push('/recommendations')">升学推荐</el-button>
      </div>
    </header>

    <template v-if="profile">
      <section class="profile-hero-grid">
        <article class="soft-card hero-summary-card">
          <div class="hero-kicker">综合画像</div>
          <h3>{{ latestExamName }}</h3>
          <p>{{ studentNarrative }}</p>
          <div class="hero-meta-grid">
            <div class="hero-meta-item">
              <span>主联系人</span>
              <strong>{{ primaryGuardianLabel }}</strong>
            </div>
            <div class="hero-meta-item">
              <span>联系电话</span>
              <strong>{{ profile.student.phone ?? "未填写" }}</strong>
            </div>
            <div class="hero-meta-item">
              <span>家庭住址</span>
              <strong>{{ profile.student.address ?? "未填写" }}</strong>
            </div>
            <div class="hero-meta-item">
              <span>薄弱学科</span>
              <strong>{{ weaknessSummary }}</strong>
            </div>
          </div>
        </article>

        <article
          v-for="item in studentHeroCards"
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
          <span>当前班级</span>
          <strong>{{ currentClassLabel }}</strong>
        </article>
        <article class="soft-card stat-card">
          <span>最近考试总分</span>
          <strong>{{ profile.performance_summary.latest_total_score ?? "-" }}</strong>
        </article>
        <article class="soft-card stat-card">
          <span>最近年级名次</span>
          <strong>{{ profile.performance_summary.latest_grade_rank ?? "-" }}</strong>
        </article>
        <article class="soft-card stat-card">
          <span>考试次数</span>
          <strong>{{ profile.performance_summary.exam_count }}</strong>
        </article>
      </section>

      <el-tabs class="profile-tabs">
        <el-tab-pane label="基础信息">
          <section class="soft-card detail-card">
            <div class="detail-grid">
              <div class="detail-item">
                <span>性别</span>
                <strong>{{ profile.student.gender ?? "-" }}</strong>
              </div>
              <div class="detail-item">
                <span>学生状态</span>
                <strong>{{ profile.student.status ?? "-" }}</strong>
              </div>
              <div class="detail-item">
                <span>学生类别</span>
                <strong>{{ formatStudentType(profile.student.student_type) }}</strong>
              </div>
              <div class="detail-item">
                <span>艺体方向</span>
                <strong>{{ profile.student.art_track ?? "-" }}</strong>
              </div>
              <div class="detail-item">
                <span>生源地</span>
                <strong>{{ profile.student.origin_province ?? "-" }}</strong>
              </div>
              <div class="detail-item">
                <span>联系电话</span>
                <strong>{{ profile.student.phone ?? "-" }}</strong>
              </div>
              <div class="detail-item">
                <span>家庭住址</span>
                <strong>{{ profile.student.address ?? "-" }}</strong>
              </div>
            </div>
            <div class="section-split"></div>
            <div class="section-head compact">
              <div>
                <h3>家庭联系人</h3>
                <p>支持展示主联系人与补充联系人。</p>
              </div>
            </div>
            <div v-if="profile.student.guardians.length" class="guardian-grid">
              <article v-for="item in profile.student.guardians" :key="item.id" class="guardian-card">
                <div class="guardian-head">
                  <strong>{{ item.name }}</strong>
                  <el-tag v-if="item.is_primary" type="success" effect="light">主联系人</el-tag>
                </div>
                <p>{{ item.relation }} · {{ item.phone ?? "无电话" }}</p>
                <span>{{ item.work_unit ?? "未填写单位" }}</span>
              </article>
            </div>
            <el-empty v-else description="暂无家庭联系人" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="学籍历史">
          <section class="soft-card detail-card">
            <div class="table-shell">
              <el-table :data="profile.class_histories" stripe>
                <el-table-column label="年级" prop="grade_name" min-width="120" />
                <el-table-column label="班级" prop="class_name" min-width="120" />
                <el-table-column label="开始日期" prop="start_date" min-width="140" />
                <el-table-column label="结束日期" prop="end_date" min-width="140" />
                <el-table-column label="原因" prop="reason" min-width="160" />
              </el-table>
            </div>
            <el-empty v-if="!profile.class_histories.length" description="暂无班级变动历史" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="成绩摘要">
          <section class="soft-card detail-card">
            <div class="section-head compact">
              <div>
                <h3>最近一次成绩画像</h3>
                <p>{{ latestExamName }}</p>
              </div>
            </div>
            <div class="tag-row">
              <div class="tag-block">
                <span>优势学科</span>
                <div class="tag-cluster">
                  <el-tag
                    v-for="item in profile.performance_summary.strength_subjects"
                    :key="item"
                    type="success"
                    effect="light"
                  >
                    {{ item }}
                  </el-tag>
                  <span v-if="!profile.performance_summary.strength_subjects.length" class="muted-copy">暂无明显优势</span>
                </div>
              </div>
              <div class="tag-block">
                <span>薄弱学科</span>
                <div class="tag-cluster">
                  <el-tag
                    v-for="item in profile.performance_summary.weakness_subjects"
                    :key="item"
                    type="warning"
                    effect="light"
                  >
                    {{ item }}
                  </el-tag>
                  <span v-if="!profile.performance_summary.weakness_subjects.length" class="muted-copy">暂无明显薄弱项</span>
                </div>
              </div>
            </div>
            <div class="table-shell">
              <el-table :data="profile.exam_trends" stripe>
                <el-table-column label="考试" prop="exam_name" min-width="190" />
                <el-table-column label="时间" prop="exam_date" width="120" />
                <el-table-column label="总分" prop="total_score" width="100" />
                <el-table-column label="班名" prop="class_rank" width="90" />
                <el-table-column label="年名" prop="grade_rank" width="90" />
                <el-table-column label="班百分位" prop="class_percentile" width="110" />
                <el-table-column label="年百分位" prop="grade_percentile" width="110" />
              </el-table>
            </div>
            <el-empty v-if="!profile.exam_trends.length" description="暂无考试趋势数据" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="成长档案">
          <section class="soft-card detail-card">
            <div class="table-shell">
              <el-table :data="profile.recent_growth_records" stripe>
                <el-table-column label="日期" prop="occurred_on" width="120" />
                <el-table-column label="类型" prop="record_type" width="120" />
                <el-table-column label="标题" prop="title" min-width="220" />
                <el-table-column label="责任人" prop="owner_name" width="120" />
                <el-table-column label="附件数" prop="attachment_count" width="100" />
              </el-table>
            </div>
            <el-empty v-if="!profile.recent_growth_records.length" description="暂无成长档案记录" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="推荐记录">
          <section class="soft-card detail-card">
            <div class="table-shell">
              <el-table :data="profile.recommendation_history" stripe>
                <el-table-column label="方案名称" prop="scheme_name" min-width="180" />
                <el-table-column label="考试 ID" prop="exam_id" width="90" />
                <el-table-column label="生成时间" prop="generated_at" min-width="180" />
                <el-table-column label="总条数" prop="result_count" width="90" />
                <el-table-column label="冲" prop="challenge_count" width="70" />
                <el-table-column label="稳" prop="steady_count" width="70" />
                <el-table-column label="保" prop="safe_count" width="70" />
              </el-table>
            </div>
            <el-empty v-if="!profile.recommendation_history.length" description="暂无推荐历史" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="升学画像">
          <section class="soft-card detail-card">
            <StudentPathwayProfilePanel :student-id="studentId" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="附件">
          <section class="soft-card detail-card">
            <div class="section-head">
              <div>
                <h3>学生附件</h3>
                <p>支持独立挂接学生附件，也保留成长档案里的引用附件视图。</p>
              </div>
            </div>
            <div class="attachment-toolbar">
              <el-input v-model="attachmentDraft.title" placeholder="附件标题，可选" />
              <el-input v-model="attachmentDraft.attachment_type" placeholder="附件类型，如证件/照片/证明" />
              <el-input v-model="attachmentDraft.note" placeholder="备注，可选" />
              <el-upload :show-file-list="false" :auto-upload="false" :on-change="handleAttachmentUpload">
                <el-button type="primary" :loading="uploadingAttachment">上传并挂接</el-button>
              </el-upload>
            </div>
            <div class="table-shell">
              <el-table :data="profile.attachments" stripe>
                <el-table-column label="文件名" prop="original_filename" min-width="220" />
                <el-table-column label="标题" prop="title" min-width="160" />
                <el-table-column label="来源记录" prop="source_title" min-width="180" />
                <el-table-column label="来源" min-width="140">
                  <template #default="{ row }">
                    {{ formatAttachmentSource(row.source_type) }}
                  </template>
                </el-table-column>
                <el-table-column label="分类" prop="category" width="120" />
                <el-table-column label="上传时间" prop="created_at" min-width="180" />
                <el-table-column label="操作" width="150" fixed="right">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="openFile(row.download_url)">下载</el-button>
                    <el-button v-if="row.id" link type="danger" @click="removeAttachment(row.id)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <el-empty v-if="!profile.attachments.length" description="暂无附件" />
          </section>
        </el-tab-pane>
      </el-tabs>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";
import type { UploadFile } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { apiRequest, openFile, uploadFile } from "../api/client";
import StudentPathwayProfilePanel from "../components/students/StudentPathwayProfilePanel.vue";

interface GuardianItem {
  id: number;
  name: string;
  relation: string;
  phone?: string | null;
  work_unit?: string | null;
  is_primary: boolean;
}

interface StudentDetail {
  id: number;
  student_no: string;
  name: string;
  gender?: string | null;
  current_grade_name?: string | null;
  current_class_name?: string | null;
  status?: string | null;
  student_type?: string | null;
  art_track?: string | null;
  origin_province?: string | null;
  phone?: string | null;
  address?: string | null;
  guardians: GuardianItem[];
}

interface ClassHistoryItem {
  grade_name?: string | null;
  class_name?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  reason?: string | null;
}

interface ExamTrendItem {
  exam_name?: string | null;
  exam_date?: string | null;
  total_score?: number | null;
  class_rank?: number | null;
  grade_rank?: number | null;
  class_percentile?: number | null;
  grade_percentile?: number | null;
}

interface GrowthRecordItem {
  occurred_on?: string | null;
  record_type?: string | null;
  title?: string | null;
  owner_name?: string | null;
  attachment_count?: number | null;
}

interface RecommendationHistoryItem {
  scheme_name?: string | null;
  exam_id?: number | null;
  generated_at?: string | null;
  result_count?: number | null;
  challenge_count?: number | null;
  steady_count?: number | null;
  safe_count?: number | null;
}

interface AttachmentItem {
  id?: number | null;
  download_url?: string | null;
  source_type?: string | null;
  original_filename?: string | null;
  title?: string | null;
  source_title?: string | null;
  category?: string | null;
  created_at?: string | null;
}

interface StudentProfile {
  student: StudentDetail;
  class_histories: ClassHistoryItem[];
  performance_summary: {
    latest_total_score?: number | null;
    latest_grade_rank?: number | null;
    latest_exam_name?: string | null;
    exam_count: number;
    strength_subjects: string[];
    weakness_subjects: string[];
  };
  exam_trends: ExamTrendItem[];
  recent_growth_records: GrowthRecordItem[];
  recommendation_history: RecommendationHistoryItem[];
  attachments: AttachmentItem[];
}

const route = useRoute();
const router = useRouter();
const profile = ref<StudentProfile | null>(null);
const studentId = computed(() => Number(route.params.studentId));
const uploadingAttachment = ref(false);
const attachmentDraft = reactive({
  title: "",
  attachment_type: "",
  note: "",
});

const currentClassLabel = computed(() => {
  if (!profile.value) return "-";
  return [profile.value.student.current_grade_name, profile.value.student.current_class_name].filter(Boolean).join(" ") || "未分班";
});

const latestExamName = computed(
  () => profile.value?.performance_summary.latest_exam_name ?? "暂无考试画像",
);

const primaryGuardian = computed(
  () => profile.value?.student.guardians.find((item) => item.is_primary) ?? profile.value?.student.guardians[0] ?? null,
);

const primaryGuardianLabel = computed(() => {
  if (!primaryGuardian.value) return "暂无";
  return `${primaryGuardian.value.name} · ${primaryGuardian.value.relation}`;
});

const weaknessSummary = computed(() => {
  const items = profile.value?.performance_summary.weakness_subjects ?? [];
  return items.length ? items.join(" / ") : "暂无明显薄弱项";
});

const studentNarrative = computed(() => {
  if (!profile.value) return "暂无学生画像";
  const rank = profile.value.performance_summary.latest_grade_rank ?? "未出名次";
  return `${currentClassLabel.value}，已累计 ${profile.value.performance_summary.exam_count} 次考试记录，最近一次年级名次为 ${rank}。`;
});

const studentHeroCards = computed(() => {
  if (!profile.value) return [];
  return [
    {
      label: "家庭联系人",
      value: profile.value.student.guardians.length,
      help: "主联系人与补充联系人统一展示。",
      tone: "tone-blue",
    },
    {
      label: "成长记录",
      value: profile.value.recent_growth_records.length,
      help: "最近成长档案条目，可直达查看。",
      tone: "tone-green",
    },
    {
      label: "推荐方案",
      value: profile.value.recommendation_history.length,
      help: "保留历史方案与冲稳保分组结果。",
      tone: "tone-amber",
    },
    {
      label: "附件数量",
      value: profile.value.attachments.length,
      help: "独立附件与引用附件统一在此查看。",
      tone: "tone-slate",
    },
  ];
});

function resetAttachmentDraft(): void {
  attachmentDraft.title = "";
  attachmentDraft.attachment_type = "";
  attachmentDraft.note = "";
}

function formatAttachmentSource(sourceType?: string | null): string {
  if (!sourceType) return "-";
  if (sourceType === "student_attachment") return "独立附件";
  if (sourceType.startsWith("growth:")) return `成长档案 / ${sourceType.replace("growth:", "")}`;
  return sourceType;
}

function formatStudentType(value?: string | null): string {
  if (!value) return "未标注";
  const mapping: Record<string, string> = {
    general: "普通生",
    repeat: "复读生",
  };
  return mapping[value] ?? value;
}

async function loadProfile(): Promise<void> {
  try {
    profile.value = await apiRequest<StudentProfile>(`/api/students/${route.params.studentId}/profile`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function handleAttachmentUpload(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw) return;
  try {
    uploadingAttachment.value = true;
    const uploaded = await uploadFile<{ id: number }>("/api/files/upload", uploadFileItem.raw, {
      category: "student_attachment",
    });
    await apiRequest(`/api/students/${route.params.studentId}/attachments`, {
      method: "POST",
      body: JSON.stringify({
        stored_file_id: uploaded.id,
        title: attachmentDraft.title || null,
        attachment_type: attachmentDraft.attachment_type || null,
        note: attachmentDraft.note || null,
        is_active: true,
      }),
    });
    resetAttachmentDraft();
    ElMessage.success("学生附件已上传");
    await loadProfile();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    uploadingAttachment.value = false;
  }
}

async function removeAttachment(attachmentId: number): Promise<void> {
  try {
    await ElMessageBox.confirm(
      "删除后附件记录将不再显示，如仍需保留请先确认是否已完成下载或归档。是否继续？",
      "删除学生附件",
      { type: "warning" },
    );
    await apiRequest(`/api/students/${route.params.studentId}/attachments/${attachmentId}`, {
      method: "DELETE",
    });
    ElMessage.success("学生附件已删除");
    await loadProfile();
  } catch (error) {
    if (error === "cancel" || error === "close") return;
    ElMessage.error((error as Error).message);
  }
}

onMounted(loadProfile);
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

.section-split {
  height: 1px;
  margin: 22px 0;
  background: rgba(120, 138, 156, 0.12);
}

.guardian-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.guardian-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(114, 132, 150, 0.14);
  background: rgba(255, 255, 255, 0.8);
}

.guardian-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.guardian-card p,
.guardian-card span {
  color: #617487;
}

.guardian-card p {
  margin: 10px 0 6px;
}

.tag-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.tag-block {
  padding: 16px;
  border-radius: 18px;
  background: rgba(243, 247, 251, 0.78);
}

.tag-block > span {
  display: block;
  margin-bottom: 10px;
  color: #6c8194;
  font-size: 13px;
}

.tag-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.muted-copy {
  color: #6e8295;
  font-size: 13px;
}

.attachment-toolbar {
  display: grid;
  grid-template-columns: 1.1fr 1fr 1.2fr auto;
  gap: 12px;
  margin-bottom: 16px;
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
  .tag-row,
  .attachment-toolbar,
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
