<template>
  <AppPage
    :title="profile?.student.name ?? '学生详情'"
    eyebrow="学生中心 / 学生档案"
    description="把学籍、成绩、成长档案、教师评语、推荐记录和附件归到同一页，减少来回切换。"
    :meta="pageMeta"
  >
    <template #actions>
      <el-button @click="router.push('/students')">返回列表</el-button>
      <el-button :disabled="!profile" @click="router.push(`/growth-archive?student_id=${studentId}`)">成长档案</el-button>
      <el-button :disabled="!profile" @click="router.push(`/gaokao-pathways?student_id=${studentId}`)">升学方案</el-button>
      <el-button :disabled="!profile" @click="openStudentGrowthReport">打印成长摘要</el-button>
      <el-button :disabled="!latestExamId" @click="openStudentAnalysisReport">打印成绩报告</el-button>
      <el-button :disabled="!profile" :loading="exportingFollowupPackage" @click="exportStudentFollowupPackage">生成跟进包</el-button>
      <el-button type="primary" @click="router.push('/recommendations')">升学推荐</el-button>
    </template>

    <el-alert
      v-if="profileLoadError"
      class="student-detail-alert"
      type="error"
      show-icon
      :closable="false"
      title="学生档案加载失败"
      :description="profileLoadError"
    >
      <template #default>
        <el-button size="small" type="primary" plain @click="loadDetailWithFeedback">重新加载学生档案</el-button>
      </template>
    </el-alert>

    <div v-loading="profileLoading" class="student-detail-body">
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

      <AppStatGrid :items="studentMetricCards" :columns="4" />

      <section class="soft-card panorama-card">
        <div class="section-head compact">
          <div>
            <h3>360° 总览与下一步</h3>
            <p>这里集中显示当前学生能不能分析、缺什么、下一步去哪里补。</p>
          </div>
        </div>
        <div class="risk-tag-list">
          <el-tag
            v-for="item in studentRiskTags"
            :key="item.label"
            :type="item.type"
            effect="light"
          >
            {{ item.label }}：{{ item.detail }}
          </el-tag>
          <el-tag v-if="!studentRiskTags.length" type="success" effect="light">当前关键数据可用于基础分析</el-tag>
        </div>
        <div class="student-risk-grid">
          <article class="student-risk-card">
            <span>风险等级</span>
            <strong>{{ studentRisk?.risk_label ?? "未计算" }}</strong>
            <p>{{ studentRisk?.reasons.join(" / ") ?? "加载后显示成绩、成长档案和规划任务综合判断。" }}</p>
          </article>
          <article class="student-risk-card">
            <span>成长档案</span>
            <strong>{{ studentRisk ? formatStudentGrowthSummary(studentRisk.growth_summary) : "未加载" }}</strong>
          </article>
          <article class="student-risk-card">
            <span>规划任务</span>
            <strong>{{ studentRisk ? formatStudentPlanningSummary(studentRisk.planning_summary) : "未加载" }}</strong>
          </article>
        </div>
        <el-alert
          v-if="studentRiskLoadError"
          class="section-alert"
          type="error"
          :title="studentRiskLoadError"
          show-icon
          :closable="false"
        >
          <template #default>
            <el-button size="small" :loading="studentRiskLoading" @click="loadStudentRiskWithFeedback">重新加载风险概览</el-button>
          </template>
        </el-alert>
        <div class="action-card-grid">
          <article v-for="item in student360Actions" :key="item.label" class="action-card" @click="router.push(item.path)">
            <strong>{{ item.label }}</strong>
            <p>{{ item.detail }}</p>
          </article>
        </div>
      </section>

      <el-tabs v-model="activeProfileTab" class="profile-tabs">
        <el-tab-pane label="基础信息" name="basic">
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

        <el-tab-pane label="学籍历史" name="status">
          <section class="soft-card detail-card">
            <div class="section-head compact">
              <div>
                <h3>班级历史</h3>
                <p>来自学生主档的学籍历史段，用于查看曾经所在年级和班级。</p>
              </div>
            </div>
            <div class="table-shell">
              <el-table :data="profile.class_histories" stripe>
                <el-table-column label="年级" prop="grade_name" min-width="120" />
                <el-table-column label="班级" prop="class_name" min-width="120" />
                <el-table-column label="开始日期" prop="start_date" min-width="140" />
                <el-table-column label="结束日期" prop="end_date" min-width="140" />
                <el-table-column label="原因" prop="reason" min-width="160" />
                <template #empty>
                  <el-empty description="暂无班级变动历史" />
                </template>
              </el-table>
            </div>
            <div class="section-split"></div>
            <div class="section-head compact">
              <div>
                <h3>调班记录</h3>
                <p>来自批量调班批次的系统记录，保留生效日期、原因、备注和操作人。</p>
              </div>
            </div>
            <div class="table-shell">
              <el-alert
                v-if="classTransferLoadError"
                class="section-alert"
                type="error"
                :title="classTransferLoadError"
                show-icon
                :closable="false"
              >
                <template #default>
                  <el-button size="small" :loading="classTransferLoading" @click="loadClassTransferHistoryWithFeedback">
                    重新加载调班记录
                  </el-button>
                </template>
              </el-alert>
              <el-table v-loading="classTransferLoading" :data="classTransferHistory" stripe>
                <el-table-column label="生效日期" prop="effective_on" width="120" />
                <el-table-column label="班级调整" min-width="240">
                  <template #default="{ row }">
                    {{ formatClassTransferRoute(row) }}
                  </template>
                </el-table-column>
                <el-table-column label="原因" prop="reason" min-width="160" />
                <el-table-column label="备注" prop="note" min-width="180" />
                <el-table-column label="操作人" prop="operator_name" width="120" />
                <template #empty>
                  <el-empty :description="classTransferLoadError ? '调班记录加载失败，请重试' : '暂无调班记录'">
                    <el-button
                      v-if="classTransferLoadError"
                      type="primary"
                      plain
                      :loading="classTransferLoading"
                      @click="loadClassTransferHistoryWithFeedback"
                    >
                      重新加载调班记录
                    </el-button>
                  </el-empty>
                </template>
              </el-table>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="成绩摘要" name="scores">
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
                <el-table-column type="expand" width="46">
                  <template #default="{ row }">
                    <div class="subject-score-panel">
                      <span
                        v-for="subject in row.subjects"
                        :key="`${row.exam_id}-${subject.subject_id}`"
                        class="subject-score-pill"
                      >
                        <strong>{{ subject.subject_name }}</strong>
                        <em>{{ subject.score ?? "-" }}</em>
                        <small>{{ subject.score_value_label }}</small>
                      </span>
                      <span v-if="!row.subjects?.length" class="muted-copy">暂无分科成绩</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="考试" prop="exam_name" min-width="190" />
                <el-table-column label="时间" prop="exam_date" width="120" />
                <el-table-column label="总分" prop="total_score" width="100" />
                <el-table-column label="口径" prop="score_value_label" width="90" />
                <el-table-column label="班名" prop="class_rank" width="90" />
                <el-table-column label="校内名" prop="grade_rank" width="90" />
                <el-table-column label="班百分位" prop="class_percentile" width="110" />
                <el-table-column label="校内百分位" prop="grade_percentile" width="120" />
                <template #empty>
                  <el-empty description="暂无考试趋势数据" />
                </template>
              </el-table>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="成长档案" name="growth">
          <section class="soft-card detail-card">
            <el-alert
              v-if="classTransferLoadError"
              class="section-alert"
              type="error"
              :title="classTransferLoadError"
              show-icon
              :closable="false"
            >
              <template #default>
                <el-button size="small" :loading="classTransferLoading" @click="loadClassTransferHistoryWithFeedback">
                  重新加载系统调班事件
                </el-button>
              </template>
            </el-alert>
            <div v-if="classTransferHistory.length" class="system-event-list">
              <article v-for="item in classTransferHistory" :key="item.item_id" class="system-event-card">
                <el-tag type="info" effect="light">班级调整</el-tag>
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ formatClassTransferEventSummary(item) }}</p>
                  <span v-if="item.note">备注：{{ item.note }}</span>
                </div>
              </article>
            </div>
            <div class="table-shell">
              <el-table :data="profile.recent_growth_records" stripe>
                <el-table-column label="日期" prop="occurred_on" width="120" />
                <el-table-column label="类型" prop="record_type" width="120" />
                <el-table-column label="标题" prop="title" min-width="220" />
                <el-table-column label="责任人" prop="owner_name" width="120" />
                <el-table-column label="附件数" prop="attachment_count" width="100" />
                <template #empty>
                  <el-empty
                    :description="classTransferHistory.length ? '暂无成长档案记录，已显示系统事件' : '暂无成长记录或系统事件'"
                  />
                </template>
              </el-table>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="教师评语" name="teacher-comments">
          <section class="soft-card detail-card">
            <div class="section-head compact">
              <div>
                <h3>教师评语</h3>
                <p>{{ teacherCommentsLoading ? "正在加载评语" : `${teacherComments.items.length} 条留言` }}</p>
              </div>
            </div>
            <el-alert
              v-if="teacherCommentsLoadError"
              class="section-alert"
              type="error"
              :title="teacherCommentsLoadError"
              show-icon
              :closable="false"
            >
              <template #default>
                <el-button size="small" :loading="teacherCommentsLoading" @click="loadTeacherCommentsWithFeedback">重新加载教师评语</el-button>
              </template>
            </el-alert>
            <el-alert
              v-if="teacherCommentActionError"
              class="section-alert"
              type="error"
              :title="teacherCommentActionError"
              show-icon
              :closable="false"
            />
            <div v-if="teacherComments.can_comment" class="teacher-comment-editor">
              <el-select
                v-model="teacherCommentDraft.subjectId"
                placeholder="评价科目"
                :disabled="teacherCommentFormDisabled || teacherComments.available_subjects.length <= 1"
              >
                <el-option
                  v-for="item in teacherComments.available_subjects"
                  :key="`${item.subject_id}-${item.class_id}-${item.semester_id}`"
                  :label="item.subject_name"
                  :value="item.subject_id"
                >
                  <span>{{ item.subject_name }}</span>
                  <small class="option-meta">{{ [item.class_name, item.semester_name].filter(Boolean).join(" · ") }}</small>
                </el-option>
              </el-select>
              <el-input
                v-model="teacherCommentDraft.content"
                type="textarea"
                :rows="3"
                maxlength="2000"
                show-word-limit
                placeholder="写下课堂表现、学习习惯或接手建议"
                :disabled="teacherCommentFormDisabled"
              />
              <el-button
                type="primary"
                :loading="submittingTeacherComment"
                :disabled="teacherCommentFormDisabled"
                @click="submitTeacherComment"
              >
                发布评语
              </el-button>
            </div>
            <div v-else class="teacher-comment-readonly-note">
              <el-tag type="info" effect="light">只读</el-tag>
              <span>当前账号没有该生任课评价权限</span>
            </div>
            <div v-loading="teacherCommentsLoading" v-if="teacherComments.items.length" class="teacher-comment-list">
              <article v-for="item in teacherComments.items" :key="item.id" class="teacher-comment-card">
                <div class="teacher-comment-card-head">
                  <strong>{{ item.subject_name ?? "教师评语" }}</strong>
                  <div class="teacher-comment-meta">
                    <span v-for="meta in buildTeacherCommentMeta(item)" :key="`${item.id}-${meta}`">{{ meta }}</span>
                  </div>
                </div>
                <p>{{ item.content }}</p>
              </article>
            </div>
            <el-empty v-else :description="teacherCommentsLoadError ? '教师评语加载失败，请重试' : '暂无教师评语'">
              <el-button
                v-if="teacherCommentsLoadError"
                type="primary"
                plain
                :loading="teacherCommentsLoading"
                @click="loadTeacherCommentsWithFeedback"
              >
                重新加载教师评语
              </el-button>
            </el-empty>
          </section>
        </el-tab-pane>

        <el-tab-pane label="推荐记录" name="recommendations">
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
                <el-table-column label="关注" prop="watch_count" width="76" />
                <template #empty>
                  <el-empty description="暂无推荐历史" />
                </template>
              </el-table>
            </div>
          </section>
        </el-tab-pane>

        <el-tab-pane label="升学画像" name="pathway-profile">
          <section class="soft-card detail-card">
            <StudentPathwayProfilePanel :student-id="studentId" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="升学规划" name="planning">
          <section class="soft-card detail-card">
            <StudentPlanningPanel :student-id="studentId" :latest-exam-id="latestExamId" />
          </section>
        </el-tab-pane>

        <el-tab-pane label="附件" name="attachments">
          <section class="soft-card detail-card">
            <div class="section-head">
              <div>
                <h3>学生附件</h3>
                <p>支持独立挂接学生附件，也保留成长档案里的引用附件视图。</p>
              </div>
            </div>
            <el-alert
              v-if="attachmentActionError"
              class="section-alert"
              type="error"
              :title="attachmentActionError"
              show-icon
              :closable="false"
            />
            <div class="attachment-toolbar">
              <el-input v-model="attachmentDraft.title" placeholder="附件标题，可选" :disabled="attachmentFormDisabled" />
              <el-input v-model="attachmentDraft.attachment_type" placeholder="附件类型，如证件/照片/证明" :disabled="attachmentFormDisabled" />
              <el-input v-model="attachmentDraft.note" placeholder="备注，可选" :disabled="attachmentFormDisabled" />
              <el-upload :show-file-list="false" :auto-upload="false" :disabled="attachmentFormDisabled" :on-change="handleAttachmentUpload">
                <el-button type="primary" :loading="uploadingAttachment" :disabled="attachmentFormDisabled">上传并挂接</el-button>
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
                    <el-button link type="primary" :disabled="attachmentFormDisabled" @click="openFile(row.download_url)">下载</el-button>
                    <el-button
                      v-if="row.id"
                      link
                      type="danger"
                      :loading="deletingAttachmentId === row.id"
                      :disabled="uploadingAttachment || (deletingAttachmentId !== null && deletingAttachmentId !== row.id)"
                      @click="removeAttachment(row.id)"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
                <template #empty>
                  <el-empty description="暂无附件" />
                </template>
              </el-table>
            </div>
          </section>
        </el-tab-pane>
      </el-tabs>
      </template>

      <el-empty v-else :description="studentDetailEmptyDescription">
        <el-button v-if="profileLoadError" type="primary" @click="loadDetailWithFeedback">重新加载学生档案</el-button>
      </el-empty>
    </div>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";
import type { UploadFile } from "element-plus";
import { useRoute, useRouter } from "vue-router";

import { apiRequest, openFile, uploadFile } from "../api/client";
import { AppPage, AppStatGrid, type PageMetaItem, type StatCardItem } from "../components/ui";
import StudentPathwayProfilePanel from "../components/students/StudentPathwayProfilePanel.vue";
import StudentPlanningPanel from "../components/students/StudentPlanningPanel.vue";
import {
  formatClassTransferEventSummary,
  formatClassTransferRoute,
  type ClassTransferHistoryItem,
} from "../components/students/studentClassTransfer";
import {
  buildTeacherCommentMeta,
  buildTeacherCommentRequest,
  type TeacherCommentMetaSource,
} from "../components/students/teacherComments";
import {
  buildStudent360Actions,
  buildStudent360RiskTags,
} from "../utils/profile360";
import {
  growthSummaryPrintPreviewPath,
  studentAnalysisPrintPreviewPath,
} from "../utils/print";
import { formatUserActionError, getErrorMessage } from "../utils/userFeedback";

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

interface ExamSubjectScoreItem {
  subject_id: number;
  subject_name?: string | null;
  score?: number | null;
  score_value_type?: string | null;
  score_value_label?: string | null;
  class_rank?: number | null;
  grade_rank?: number | null;
}

interface ExamTrendItem {
  exam_id?: number | null;
  exam_name?: string | null;
  exam_date?: string | null;
  total_score?: number | null;
  score_value_type?: string | null;
  score_value_label?: string | null;
  class_rank?: number | null;
  grade_rank?: number | null;
  class_percentile?: number | null;
  grade_percentile?: number | null;
  subjects?: ExamSubjectScoreItem[];
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
  watch_count?: number | null;
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
    latest_exam_id?: number | null;
    latest_total_score?: number | null;
    latest_score_value_type?: string | null;
    latest_score_value_label?: string | null;
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

interface StudentRiskSummary {
  risk_level: "urgent" | "follow_up" | "watch" | "normal";
  risk_label: string;
  reasons: string[];
  suggested_actions: string[];
  growth_summary: {
    record_count: number;
    latest_record_date?: string | null;
  };
  planning_summary: {
    open_task_count: number;
    overdue_task_count: number;
    due_soon_task_count: number;
    high_priority_open_count: number;
    no_goal: boolean;
    next_due_date?: string | null;
  };
}

interface TeacherCommentSubjectOption {
  subject_id: number;
  subject_name: string;
  teacher_id: number;
  teacher_name: string;
  class_id?: number | null;
  class_name?: string | null;
  semester_id?: number | null;
  semester_name?: string | null;
}

interface TeacherCommentItem extends TeacherCommentMetaSource {
  id: number;
  student_id: number;
  teacher_id: number;
  subject_id?: number | null;
  class_id?: number | null;
  semester_id?: number | null;
  content: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

interface TeacherCommentListResponse {
  items: TeacherCommentItem[];
  can_comment: boolean;
  available_subjects: TeacherCommentSubjectOption[];
}

interface ReportExportRecord {
  download_url: string;
}

const route = useRoute();
const router = useRouter();
const profile = ref<StudentProfile | null>(null);
const classTransferHistory = ref<ClassTransferHistoryItem[]>([]);
const teacherComments = ref<TeacherCommentListResponse>({
  items: [],
  can_comment: false,
  available_subjects: [],
});
const studentRisk = ref<StudentRiskSummary | null>(null);
const studentId = computed(() => Number(route.params.studentId));
const activeProfileTab = ref(String(route.query.tab || "basic"));
const profileLoading = ref(false);
const profileLoadError = ref("");
const classTransferLoading = ref(false);
const classTransferLoadError = ref("");
const teacherCommentsLoading = ref(false);
const teacherCommentsLoadError = ref("");
const teacherCommentActionError = ref("");
const studentRiskLoading = ref(false);
const studentRiskLoadError = ref("");
const attachmentActionError = ref("");
const uploadingAttachment = ref(false);
const deletingAttachmentId = ref<number | null>(null);
const exportingFollowupPackage = ref(false);
const submittingTeacherComment = ref(false);
const attachmentDraft = reactive({
  title: "",
  attachment_type: "",
  note: "",
});
const teacherCommentDraft = reactive({
  subjectId: null as number | null,
  content: "",
});
const teacherCommentFormDisabled = computed(
  () => submittingTeacherComment.value || teacherCommentsLoading.value || profileLoading.value,
);
const attachmentFormDisabled = computed(
  () => uploadingAttachment.value || profileLoading.value || deletingAttachmentId.value !== null,
);

const currentClassLabel = computed(() => {
  if (!profile.value) return "-";
  return [profile.value.student.current_grade_name, profile.value.student.current_class_name].filter(Boolean).join(" ") || "未分班";
});

const pageMeta = computed<PageMetaItem[]>(() => {
  if (!profile.value) {
    return [{ label: "学生 ID", value: Number.isFinite(studentId.value) ? studentId.value : "-" }];
  }
  return [
    { label: "学号", value: profile.value.student.student_no },
    { label: "当前班级", value: currentClassLabel.value },
    { label: "学生状态", value: profile.value.student.status ?? "未标注" },
    { label: "学生类别", value: formatStudentType(profile.value.student.student_type) },
    { label: "生源地", value: profile.value.student.origin_province ?? "未维护" },
  ];
});

const latestExamName = computed(
  () => profile.value?.performance_summary.latest_exam_name ?? "暂无考试画像",
);

const latestExamId = computed(() => profile.value?.performance_summary.latest_exam_id ?? null);

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
  return `${currentClassLabel.value}，已累计 ${profile.value.performance_summary.exam_count} 次考试记录，最近一次校内名次为 ${rank}。`;
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

const studentMetricCards = computed<StatCardItem[]>(() => {
  if (!profile.value) return [];
  const scoreLabel = profile.value.performance_summary.latest_score_value_label;
  return [
    {
      label: "当前班级",
      value: currentClassLabel.value,
      help: "来自学生当前学籍档案。",
      tone: "primary",
    },
    {
      label: scoreLabel ? `最近考试总分（${scoreLabel}）` : "最近考试总分",
      value: profile.value.performance_summary.latest_total_score ?? "-",
      help: latestExamName.value,
      tone: "success",
    },
    {
      label: "最近校内名次",
      value: profile.value.performance_summary.latest_grade_rank ?? "-",
      help: "校内名次只作校内分析参考。",
      tone: "warning",
    },
    {
      label: "考试次数",
      value: profile.value.performance_summary.exam_count,
      help: "已纳入学生详情的考试趋势记录。",
      tone: "info",
    },
  ];
});

const studentRiskTags = computed(() => {
  if (!profile.value) return [];
  return buildStudent360RiskTags({
    examCount: profile.value.performance_summary.exam_count,
    growthRecordCount: profile.value.recent_growth_records.length,
    recommendationCount: profile.value.recommendation_history.length,
    attachmentCount: profile.value.attachments.length,
    classTransferCount: classTransferHistory.value.length,
    studentType: profile.value.student.student_type,
    riskLevel: studentRisk.value?.risk_level,
  });
});

const student360Actions = computed(() => buildStudent360Actions(studentId.value));

const studentDetailEmptyDescription = computed(() => {
  if (profileLoading.value) return "正在加载学生档案";
  if (profileLoadError.value) return "学生档案加载失败，请检查本地服务或学生记录后重试";
  return "暂无学生档案";
});

function resetDetailState(): void {
  profile.value = null;
  classTransferHistory.value = [];
  teacherComments.value = {
    items: [],
    can_comment: false,
    available_subjects: [],
  };
  studentRisk.value = null;
  classTransferLoadError.value = "";
  teacherCommentsLoadError.value = "";
  teacherCommentActionError.value = "";
  studentRiskLoadError.value = "";
  attachmentActionError.value = "";
  deletingAttachmentId.value = null;
  teacherCommentDraft.subjectId = null;
  teacherCommentDraft.content = "";
}

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

function formatStudentGrowthSummary(summary: StudentRiskSummary["growth_summary"]): string {
  if (summary.record_count <= 0) return "暂无成长档案记录";
  return `${summary.record_count} 条，最近 ${summary.latest_record_date ?? "-"}`;
}

function formatStudentPlanningSummary(summary: StudentRiskSummary["planning_summary"]): string {
  if (summary.open_task_count <= 0) return summary.no_goal ? "尚未建立规划目标" : "暂无开放任务";
  return `开放 ${summary.open_task_count} 项，逾期 ${summary.overdue_task_count}`;
}

function openStudentGrowthReport(): void {
  openFile(growthSummaryPrintPreviewPath(studentId.value));
}

function openStudentAnalysisReport(): void {
  if (!latestExamId.value) return;
  openFile(studentAnalysisPrintPreviewPath(studentId.value, latestExamId.value));
}

async function exportStudentFollowupPackage(): Promise<void> {
  try {
    exportingFollowupPackage.value = true;
    const payload: Record<string, unknown> = {
      report_type: "student_followup_package",
      student_id: studentId.value,
    };
    if (latestExamId.value) payload.exam_id = latestExamId.value;
    const result = await apiRequest<ReportExportRecord>("/api/reports/export", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    openFile(result.download_url);
    ElMessage.success("学生跟进包已生成");
  } catch (error) {
    ElMessage.error(formatUserActionError("生成学生跟进包", error, "请确认学生档案和报表服务可用后重试"));
  } finally {
    exportingFollowupPackage.value = false;
  }
}

async function loadProfile(): Promise<void> {
  profile.value = await apiRequest<StudentProfile>(`/api/students/${studentId.value}/profile`);
}

async function loadClassTransferHistory(): Promise<void> {
  classTransferHistory.value = await apiRequest<ClassTransferHistoryItem[]>(
    `/api/students/${studentId.value}/class-transfer-history`,
  );
}

async function loadTeacherComments(): Promise<void> {
  teacherComments.value = await apiRequest<TeacherCommentListResponse>(
    `/api/students/${studentId.value}/teacher-comments`,
  );
  const optionIds = teacherComments.value.available_subjects.map((item) => item.subject_id);
  if (!teacherCommentDraft.subjectId || !optionIds.includes(teacherCommentDraft.subjectId)) {
    teacherCommentDraft.subjectId = optionIds[0] ?? null;
  }
}

async function loadStudentRisk(): Promise<void> {
  const query = new URLSearchParams();
  if (latestExamId.value) query.set("exam_id", String(latestExamId.value));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  studentRisk.value = await apiRequest<StudentRiskSummary>(`/api/analytics/student-risk/${studentId.value}${suffix}`);
}

async function loadClassTransferHistoryWithFeedback(): Promise<void> {
  try {
    classTransferLoading.value = true;
    classTransferLoadError.value = "";
    await loadClassTransferHistory();
  } catch (error) {
    classTransferHistory.value = [];
    classTransferLoadError.value = formatUserActionError("加载调班记录", error, "请稍后重试，学生主档仍可继续查看");
    ElMessage.error(classTransferLoadError.value);
  } finally {
    classTransferLoading.value = false;
  }
}

async function loadTeacherCommentsWithFeedback(): Promise<void> {
  try {
    teacherCommentsLoading.value = true;
    teacherCommentsLoadError.value = "";
    await loadTeacherComments();
  } catch (error) {
    teacherComments.value = {
      items: [],
      can_comment: false,
      available_subjects: [],
    };
    teacherCommentDraft.subjectId = null;
    teacherCommentsLoadError.value = formatUserActionError("加载教师评语", error, "请稍后重试，学生主档仍可继续查看");
    ElMessage.error(teacherCommentsLoadError.value);
  } finally {
    teacherCommentsLoading.value = false;
  }
}

async function loadStudentRiskWithFeedback(): Promise<void> {
  try {
    studentRiskLoading.value = true;
    studentRiskLoadError.value = "";
    await loadStudentRisk();
  } catch (error) {
    studentRisk.value = null;
    studentRiskLoadError.value = formatUserActionError("加载学生风险概览", error, "请稍后重试，学生主档仍可继续查看");
    ElMessage.error(studentRiskLoadError.value);
  } finally {
    studentRiskLoading.value = false;
  }
}

async function loadDetailWithFeedback(): Promise<void> {
  profileLoading.value = true;
  profileLoadError.value = "";
  try {
    await loadProfile();
    await Promise.all([loadClassTransferHistoryWithFeedback(), loadTeacherCommentsWithFeedback()]);
    await loadStudentRiskWithFeedback();
  } catch (error) {
    profile.value = null;
    studentRisk.value = null;
    profileLoadError.value = getErrorMessage(error);
    ElMessage.error(formatUserActionError("加载学生档案", error, "请确认学生是否存在，或稍后重新加载"));
  } finally {
    profileLoading.value = false;
  }
}

async function submitTeacherComment(): Promise<void> {
  const request = buildTeacherCommentRequest(teacherCommentDraft);
  if (!request) {
    teacherCommentActionError.value = "请填写教师评语";
    ElMessage.warning(teacherCommentActionError.value);
    return;
  }
  if (teacherComments.value.available_subjects.length && !request.subject_id) {
    teacherCommentActionError.value = "请选择评价科目";
    ElMessage.warning(teacherCommentActionError.value);
    return;
  }
  try {
    submittingTeacherComment.value = true;
    teacherCommentActionError.value = "";
    await apiRequest(`/api/students/${studentId.value}/teacher-comments`, {
      method: "POST",
      body: JSON.stringify(request),
    });
    teacherCommentDraft.content = "";
    ElMessage.success("教师评语已发布");
    await loadTeacherCommentsWithFeedback();
  } catch (error) {
    teacherCommentActionError.value = formatUserActionError("发布教师评语", error, "请确认任教权限和评语内容后重试");
    ElMessage.error(teacherCommentActionError.value);
  } finally {
    submittingTeacherComment.value = false;
  }
}

async function handleAttachmentUpload(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw) return;
  try {
    uploadingAttachment.value = true;
    attachmentActionError.value = "";
    const uploaded = await uploadFile<{ id: number }>("/api/files/upload", uploadFileItem.raw, {
      category: "student_attachment",
    });
    await apiRequest(`/api/students/${studentId.value}/attachments`, {
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
    await loadDetailWithFeedback();
  } catch (error) {
    attachmentActionError.value = formatUserActionError("上传学生附件", error, "请确认文件可访问且本地服务正常后重试");
    ElMessage.error(attachmentActionError.value);
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
    deletingAttachmentId.value = attachmentId;
    attachmentActionError.value = "";
    await apiRequest(`/api/students/${studentId.value}/attachments/${attachmentId}`, {
      method: "DELETE",
    });
    ElMessage.success("学生附件已删除");
    await loadDetailWithFeedback();
  } catch (error) {
    if (error === "cancel" || error === "close") return;
    attachmentActionError.value = formatUserActionError("删除学生附件", error, "请确认附件记录仍存在后重试");
    ElMessage.error(attachmentActionError.value);
  } finally {
    if (deletingAttachmentId.value === attachmentId) {
      deletingAttachmentId.value = null;
    }
  }
}

watch(studentId, () => {
  resetDetailState();
  void loadDetailWithFeedback();
});

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab === "string" && tab) {
      activeProfileTab.value = tab;
    }
  },
);

onMounted(loadDetailWithFeedback);
</script>

<style scoped>
.student-detail-alert {
  margin-bottom: 16px;
}

.section-alert {
  margin-bottom: 14px;
}

.student-detail-body {
  display: grid;
  gap: 16px;
  min-height: 260px;
}

.profile-hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) repeat(2, minmax(0, 0.8fr));
  gap: 16px;
}

.hero-summary-card,
.hero-mini-card,
.detail-card {
  padding: 24px;
}

.system-event-list {
  display: grid;
  gap: 10px;
  margin-bottom: 14px;
}

.panorama-card {
  display: grid;
  gap: 16px;
  padding: 24px;
}

.risk-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.risk-tag-list :deep(.el-tag) {
  height: auto;
  min-height: 30px;
  padding: 6px 10px;
  white-space: normal;
}

.action-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.student-risk-grid {
  display: grid;
  grid-template-columns: 1.2fr repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.student-risk-card {
  padding: 14px;
  border: 1px solid rgba(123, 141, 158, 0.2);
  border-radius: 8px;
  background: rgba(248, 251, 253, 0.82);
}

.student-risk-card span {
  display: block;
  color: #6c8094;
  font-size: 13px;
}

.student-risk-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3448;
  line-height: 1.5;
}

.student-risk-card p {
  margin: 8px 0 0;
  color: #61778b;
  line-height: 1.55;
}

.action-card {
  padding: 14px;
  border: 1px solid rgba(123, 141, 158, 0.2);
  border-radius: 8px;
  background: rgba(248, 251, 253, 0.82);
  cursor: pointer;
}

.action-card strong {
  color: #1e3448;
}

.action-card p {
  margin: 6px 0 0;
  color: #61778b;
  line-height: 1.55;
}

.system-event-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 14px 16px;
  border: 1px solid rgba(145, 163, 176, 0.24);
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.92);
}

.system-event-card strong {
  color: #1f3448;
}

.system-event-card p {
  margin: 6px 0 0;
  color: #415a70;
  line-height: 1.6;
}

.system-event-card span {
  display: block;
  margin-top: 4px;
  color: #6d8194;
  font-size: 13px;
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

.subject-score-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 8px;
}

.subject-score-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 6px 10px;
  border-radius: 8px;
  background: rgba(243, 247, 251, 0.92);
  color: #355067;
}

.subject-score-pill em {
  color: #111827;
  font-style: normal;
  font-weight: 700;
}

.subject-score-pill small {
  color: #6e8295;
}

.attachment-toolbar {
  display: grid;
  grid-template-columns: 1.1fr 1fr 1.2fr auto;
  gap: 12px;
  margin-bottom: 16px;
}

.teacher-comment-editor {
  display: grid;
  grid-template-columns: minmax(160px, 220px) minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
  margin-bottom: 18px;
}

.teacher-comment-readonly-note {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
  color: #617487;
}

.teacher-comment-list {
  display: grid;
  gap: 12px;
}

.teacher-comment-card {
  padding: 16px;
  border: 1px solid rgba(114, 132, 150, 0.16);
  border-radius: 8px;
  background: rgba(248, 251, 253, 0.86);
}

.teacher-comment-card-head {
  display: grid;
  gap: 8px;
}

.teacher-comment-card-head strong {
  color: #1f3448;
  font-size: 16px;
}

.teacher-comment-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.teacher-comment-meta span {
  min-height: 24px;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.08);
  color: #446176;
  font-size: 12px;
  line-height: 18px;
}

.teacher-comment-card p {
  margin: 12px 0 0;
  color: #344f64;
  line-height: 1.7;
  white-space: pre-wrap;
}

.option-meta {
  float: right;
  margin-left: 20px;
  color: #8494a4;
  font-size: 12px;
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
  .student-risk-grid,
  .tag-row,
  .attachment-toolbar,
  .teacher-comment-editor,
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
