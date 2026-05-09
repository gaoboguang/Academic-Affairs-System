<template>
  <AppPage
    title="分析中心"
    eyebrow="教学分析 / 分析中心"
    description="当前覆盖学生、班级、年级和任课教师分析，依赖考试快照和任教关系，不在前端硬编码计算规则。"
    :meta="analyticsPageMeta"
  >
    <template #actions>
        <el-button @click="loadOptions">重载选项</el-button>
        <el-button type="primary" plain @click="resetAnalyticsState">清空结果</el-button>
    </template>

    <section v-if="scoreReadinessMessages.length" class="score-readiness-stack">
      <el-alert
        v-for="item in scoreReadinessMessages"
        :key="item"
        type="warning"
        show-icon
        :closable="false"
        :title="item"
      />
    </section>

    <AppFilterBar
      title="选择考试"
      description="所有分析结果都围绕同一场考试展开，统计口径为已导入成绩快照。"
      sticky
    >
      <el-select v-model="selectedExamId" filterable placeholder="请选择考试" class="global-exam-select">
          <el-option
            v-for="exam in examOptions"
            :key="exam.id"
            :label="exam.name"
            :value="exam.id"
          />
        </el-select>
      <template #actions>
          <el-button :disabled="!selectedExamId" :loading="loadingRankAudit" @click="loadScoreRankAudit">名次口径审计</el-button>
          <el-button type="primary" plain :disabled="!selectedExamId" :loading="rebuildingSnapshots" @click="rebuildScoreSnapshots">
            重建成绩快照
          </el-button>
      </template>
    </AppFilterBar>

    <section class="analysis-hero-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">分析上下文</div>
        <h2>{{ selectedExamName }}</h2>
        <p>先锁定同一场考试，再切学生、班级、年级和教师四个维度，避免跨考试横跳导致判断失真。</p>
      </article>
      <AppStatGrid :items="analyticsOverviewCards" :columns="3" />
    </section>

    <AppSectionCard v-if="rankAudit" title="名次口径审计" description="核对源班级映射、样本量和平台原始名次差异。">
      <div v-if="rankAudit" class="rank-audit-panel">
        <AppStatGrid :items="rankAuditCards" :columns="4" />
        <div v-if="rankAudit.warnings.length" class="dashboard-tip-stack">
          <el-alert
            v-for="item in rankAudit.warnings"
            :key="item"
            type="warning"
            show-icon
            :closable="false"
            :title="item"
          />
        </div>
        <div class="table-shell table-gap">
          <el-table :data="rankAudit.class_mappings" stripe>
            <el-table-column label="源班级" prop="source_class_name" min-width="120" />
            <el-table-column label="映射班级" min-width="120">
              <template #default="{ row }">{{ row.mapped_class_name ?? "未映射" }}</template>
            </el-table-column>
            <el-table-column label="学生数" prop="student_count" width="90" />
            <el-table-column label="状态" prop="mapping_status" width="130" />
          </el-table>
        </div>
      </div>
    </AppSectionCard>

    <el-tabs v-model="activeAnalyticsTab" class="analytics-tabs">
      <el-tab-pane label="班主任驾驶舱" name="adviser" lazy>
        <section class="soft-card panel-block">
          <div class="section-head compact">
            <div>
              <h3>班主任驾驶舱</h3>
              <p>按年级或班级汇总成绩波动、成长档案和规划任务，形成每日可执行的学生跟进清单。</p>
            </div>
          </div>
          <div class="filter-grid adviser-filter-grid">
            <el-select v-model="adviserGradeId" clearable filterable placeholder="年级">
              <el-option
                v-for="grade in referenceStore.grades"
                :key="grade.id"
                :label="grade.name"
                :value="grade.id"
              />
            </el-select>
            <el-select v-model="adviserClassId" clearable filterable placeholder="班级">
              <el-option
                v-for="schoolClass in referenceStore.classes"
                :key="schoolClass.id"
                :label="schoolClass.name"
                :value="schoolClass.id"
              />
            </el-select>
            <el-date-picker
              v-model="adviserDateRange"
              type="daterange"
              value-format="YYYY-MM-DD"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
            />
            <el-button type="primary" :loading="loadingAdviserDashboard" @click="loadAdviserDashboard">加载驾驶舱</el-button>
          </div>
          <div v-if="adviserDashboardTips.length" class="dashboard-tip-stack">
            <el-alert
              v-for="item in adviserDashboardTips"
              :key="item"
              type="warning"
              show-icon
              :closable="false"
              :title="item"
            />
          </div>
          <div v-if="adviserDashboard" class="metric-grid adviser-overview-grid">
            <article v-for="item in adviserOverviewCards" :key="item.label" class="soft-card stat-card" :class="item.tone">
              <div class="metric-label">{{ item.label }}</div>
              <div class="metric-value">{{ item.value }}</div>
              <p>{{ item.help }}</p>
            </article>
          </div>
          <div v-if="adviserDashboard" class="adviser-summary-grid">
            <article class="soft-card inner-panel">
              <h4>成长档案</h4>
              <p>{{ formatGrowthSummary(adviserDashboard.growth_summary) }}</p>
            </article>
            <article class="soft-card inner-panel">
              <h4>规划任务</h4>
              <p>{{ formatPlanningSummary(adviserDashboard.planning_summary) }}</p>
            </article>
            <article class="soft-card inner-panel">
              <h4>本周行动清单</h4>
              <div class="action-chip-list">
                <button
                  v-for="item in adviserDashboard.action_items"
                  :key="item.action_type"
                  type="button"
                  class="action-chip"
                  @click="openAdviserAction(item.target_route)"
                >
                  <span>{{ item.title }}</span>
                  <strong>{{ item.count }}</strong>
                </button>
              </div>
            </article>
          </div>
          <div v-if="adviserDashboard" class="table-shell table-gap">
            <el-table :data="adviserDashboard.risk_students" stripe>
              <el-table-column label="学生" min-width="150">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openRiskStudent(row)">
                    {{ row.student_name }}
                  </el-button>
                </template>
              </el-table-column>
              <el-table-column label="班级" prop="class_name" min-width="100" />
              <el-table-column label="风险等级" width="120">
                <template #default="{ row }">
                  <el-tag :type="adviserRiskTagType(row.risk_level)" effect="light">
                    {{ row.risk_label }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="主要原因" prop="primary_reason" min-width="220" />
              <el-table-column label="建议动作" min-width="260" fixed="right">
                <template #default="{ row }">
                  <div class="risk-action-group">
                    <el-button size="small" type="primary" plain @click="openRiskStudent(row)">查看学生</el-button>
                    <el-button size="small" plain @click="openRiskStudentFollowup(row)">跟进包</el-button>
                    <el-button size="small" plain @click="openRiskStudentReport(row)">报表</el-button>
                    <span v-if="!row.suggested_action" class="muted-inline">暂无建议</span>
                    <span v-else class="risk-action-text">{{ row.suggested_action }}</span>
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-empty
              v-if="!adviserDashboard.risk_students.length"
              description="当前范围暂无需要跟进的学生。"
            />
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="成绩报表" name="score-report" lazy>
        <section class="soft-card panel-block score-report-panel">
          <div class="section-head compact">
            <div>
              <h3>成绩报表</h3>
              <p>按本次考试查看学生单科成绩和综合成绩宽表，班级口径优先采用考试时点归属。</p>
            </div>
          </div>
          <div class="filter-grid score-report-filter-grid">
            <el-select v-model="scoreReportClassId" clearable filterable placeholder="全部班级">
              <el-option
                v-for="schoolClass in referenceStore.classes"
                :key="schoolClass.id"
                :label="schoolClass.name"
                :value="schoolClass.id"
              />
            </el-select>
            <el-input v-model="scoreReportKeyword" clearable placeholder="姓名 / 学号" />
            <el-select v-model="scoreReportSortMode" placeholder="排序">
              <el-option label="校内名次升序" value="grade_rank:asc" />
              <el-option label="总分降序" value="total_score:desc" />
              <el-option label="班级名次升序" value="class_rank:asc" />
              <el-option label="学号升序" value="student_no:asc" />
            </el-select>
            <el-button type="primary" :disabled="!selectedExamId" :loading="loadingScoreReport" @click="reloadScoreReportFromFirstPage">
              加载成绩报表
            </el-button>
          </div>

          <div v-if="scoreReport" class="score-report-toolbar">
            <el-select
              v-model="selectedScoreReportSubjectIds"
              multiple
              collapse-tags
              collapse-tags-tooltip
              clearable
              placeholder="显示全部科目"
            >
              <el-option
                v-for="subject in scoreReport.subjects"
                :key="subject.subject_id"
                :label="subject.subject_name"
                :value="subject.subject_id"
              />
            </el-select>
            <el-alert type="info" show-icon :closable="false" :title="scoreReport.rank_scope_label" />
          </div>

          <AppStatGrid v-if="scoreReport" :items="scoreReportCards" :columns="5" class="table-gap" />
          <el-empty v-else-if="selectedExamId && !scoreRecordTotal" description="当前成绩记录为 0。请先导入成绩，再查看本次考试成绩报表。" />

          <div v-if="scoreReport" class="table-shell table-gap score-report-table-shell">
            <el-table :data="scoreReportTableRows" stripe height="620">
              <el-table-column label="学号" prop="student_no" fixed min-width="120" />
              <el-table-column label="姓名" prop="student_name" fixed min-width="100" />
              <el-table-column label="考试班级" min-width="110">
                <template #default="{ row }">{{ row.class_name ?? "-" }}</template>
              </el-table-column>
              <el-table-column
                v-for="subject in visibleScoreReportSubjects"
                :key="subject.subject_id"
                :label="subject.subject_name"
                min-width="92"
                align="right"
              >
                <template #default="{ row }">
                  {{ formatScoreCell(getSubjectScore(row, subject.subject_id)?.score) }}
                </template>
              </el-table-column>
              <el-table-column label="总分" min-width="90" align="right">
                <template #default="{ row }">{{ formatScoreCell(row.total_score) }}</template>
              </el-table-column>
              <el-table-column label="班名次" min-width="90" align="right">
                <template #default="{ row }">{{ row.class_rank ?? "-" }}</template>
              </el-table-column>
              <el-table-column label="校内名次" min-width="100" align="right">
                <template #default="{ row }">{{ row.grade_rank ?? "-" }}</template>
              </el-table-column>
              <el-table-column label="PR" min-width="90" align="right">
                <template #default="{ row }">{{ formatPercentCell(row.grade_percentile) }}</template>
              </el-table-column>
              <el-table-column label="总分口径" prop="score_value_label" min-width="95" />
            </el-table>
            <el-pagination
              v-model:current-page="scoreReportPage"
              v-model:page-size="scoreReportPageSize"
              :total="scoreReport.total"
              :page-sizes="[20, 50, 100, 200]"
              layout="total, sizes, prev, pager, next"
              class="score-report-pagination"
              @current-change="loadScoreReport"
              @size-change="handleScoreReportPageSizeChange"
            />
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="学生分析" name="student" lazy>
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
                :label="formatExamStudentOptionLabel(student)"
                :value="student.id"
              />
            </el-select>
            <el-button type="primary" :disabled="!selectedStudentId" @click="loadStudentAnalytics">查询</el-button>
          </div>
          <div class="action-row knowledge-import-row">
            <el-select v-model="questionImportStrategy" style="width: 180px">
              <el-option label="覆盖已有题分" value="overwrite" />
              <el-option label="跳过已有题分" value="skip_existing" />
            </el-select>
            <el-upload :show-file-list="false" :auto-upload="false" :on-change="handleQuestionScoreImport">
              <el-button plain :disabled="!selectedExamId" :loading="importingQuestionScores">导入题分明细</el-button>
            </el-upload>
            <el-alert
              v-if="questionImportResult"
              class="inline-import-result"
              :type="questionImportResult.failed_rows ? 'warning' : 'success'"
              show-icon
              :closable="false"
              :title="questionImportResult.message"
            />
          </div>
          <el-empty v-if="!studentAnalytics && !scoreRecordTotal" description="当前成绩记录为 0。请先到考试成绩中心导入成绩，再查看学生分析。" />
          <el-empty
            v-else-if="!studentAnalytics && selectedExamId && !studentOptions.length"
            description="当前考试暂无可分析学生。请确认已导入成绩并重建成绩快照。"
          />
          <div v-if="studentAnalytics" class="metric-grid analytics-grid">
            <div class="soft-card stat-card">
              <div class="metric-label">总分{{ studentAnalytics.score_value_label ? `（${studentAnalytics.score_value_label}）` : "" }}</div>
              <div class="metric-value">{{ studentAnalytics.total_score }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">班级名次</div>
              <div class="metric-value">{{ studentAnalytics.class_rank ?? "-" }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">校内名次</div>
              <div class="metric-value">{{ studentAnalytics.grade_rank ?? "-" }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">校内PR</div>
              <div class="metric-value">{{ formatPercentValue(studentAnalytics.grade_percentile) }}</div>
            </div>
            <div class="soft-card stat-card">
              <div class="metric-label">目标线差距</div>
              <div class="metric-value small-value">{{ getTargetGapSummary(studentAnalytics.target_line_gaps) }}</div>
            </div>
          </div>
          <div v-if="studentAnalytics" class="student-report-grid">
            <article class="soft-card inner-panel student-overview-panel">
              <h4>本次画像</h4>
              <p>{{ studentAnalytics.overview_sentence }}</p>
              <div class="report-chip-row">
                <el-tag
                  v-for="item in studentAnalytics.target_line_gaps"
                  :key="item.line_id"
                  effect="light"
                  :type="item.status === 'reached' || item.status === 'near_above' ? 'success' : 'warning'"
                >
                  {{ item.line_name }} {{ formatSignedNumber(item.gap_score, "分") }}
                </el-tag>
              </div>
            </article>
            <article class="soft-card inner-panel radar-panel">
              <div class="panel-title-row">
                <h4>相对位置雷达</h4>
                <el-segmented v-model="studentRadarMetric" :options="studentRadarOptions" size="small" />
              </div>
              <div v-if="studentRadarRows.length" class="radar-bars">
                <div v-for="item in studentRadarRows" :key="item.subject" class="radar-row">
                  <span>{{ item.subject }}</span>
                  <div class="radar-track">
                    <i :style="{ width: `${Math.min(100, Math.max(0, item.value))}%` }" />
                  </div>
                  <strong>{{ item.label }}</strong>
                </div>
              </div>
              <el-empty v-else description="暂无可用于雷达展示的 PR 或 T 分。" />
            </article>
          </div>
          <div v-if="studentAnalytics" class="table-shell table-gap">
            <el-table :data="studentAnalytics.subjects" stripe>
              <el-table-column label="科目" prop="subject_name" min-width="120" />
              <el-table-column label="分数" prop="score" width="90" />
              <el-table-column label="口径" prop="score_value_label" width="90" />
              <el-table-column label="班名" prop="class_rank" width="90" />
              <el-table-column label="校内名" prop="grade_rank" width="90" />
              <el-table-column label="PR" width="90">
                <template #default="{ row }">{{ formatPercentValue(row.grade_percentile) }}</template>
              </el-table-column>
              <el-table-column label="T分" prop="t_score" width="80" />
              <el-table-column label="排名离差" prop="rank_deviation" width="100" />
              <el-table-column label="同档差距" width="100">
                <template #default="{ row }">{{ formatSignedNumber(row.peer_average_delta, "分") }}</template>
              </el-table-column>
              <el-table-column label="有效分差" width="100">
                <template #default="{ row }">{{ formatSignedNumber(row.primary_effective_score_gap, "分") }}</template>
              </el-table-column>
              <el-table-column label="分数变化" prop="score_delta" width="110" />
              <el-table-column label="名次变化" prop="rank_delta" width="110" />
              <el-table-column label="诊断" min-width="150">
                <template #default="{ row }">
                  <el-tag :type="studentDiagnosisTagType(row.diagnosis)" effect="light">{{ row.diagnosis }}</el-tag>
                  <span class="muted-inline">{{ formatDiagnosisTags(row.diagnosis_tags) }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <article v-if="studentAnalytics" class="soft-card inner-panel knowledge-panel table-gap">
            <div class="panel-title-row">
              <div>
                <h4>知识点诊断</h4>
                <p>按失分规模、可提升空间和科目短板权重排序，用于下一阶段学习清单。</p>
              </div>
              <div class="knowledge-actions">
                <el-select v-model="knowledgeSubjectFilter" clearable placeholder="全部科目" style="width: 180px">
                  <el-option
                    v-for="subject in studentAnalytics.subjects"
                    :key="subject.subject_id"
                    :label="subject.subject_name"
                    :value="subject.subject_id"
                  />
                </el-select>
                <el-button :loading="previewingStudentKnowledgeTasks" @click="previewStudentKnowledgeTasks">预览补弱任务</el-button>
                <el-button type="primary" plain :loading="generatingStudentKnowledgeTasks" @click="generateStudentKnowledgeTasks">一键生成任务</el-button>
                <el-button plain @click="openStudentKnowledgePrint">打印清单</el-button>
              </div>
            </div>
            <el-alert
              v-if="studentKnowledgeTaskPreview"
              class="table-gap"
              type="info"
              show-icon
              :closable="false"
              :title="formatTaskPreviewSummary(studentKnowledgeTaskPreview.create_count, studentKnowledgeTaskPreview.skip_count)"
            />
            <div v-if="filteredKnowledgePoints.length" class="table-shell table-gap">
              <el-table :data="filteredKnowledgePoints" stripe>
                <el-table-column label="科目" prop="subject_name" width="90" />
                <el-table-column label="知识路径" min-width="190">
                  <template #default="{ row }">{{ knowledgeDisplayName(row) }}</template>
                </el-table-column>
                <el-table-column label="得分率" width="90">
                  <template #default="{ row }">{{ formatPercentValue(row.score_rate) }}</template>
                </el-table-column>
                <el-table-column label="年级均值" width="100">
                  <template #default="{ row }">{{ formatPercentValue(row.grade_average_rate) }}</template>
                </el-table-column>
                <el-table-column label="年级差距" width="100">
                  <template #default="{ row }">{{ formatSignedNumber(row.grade_gap_rate ? row.grade_gap_rate * 100 : row.grade_gap_rate, "%") }}</template>
                </el-table-column>
                <el-table-column label="失分" width="80">
                  <template #default="{ row }">{{ formatSignedNumber(-row.lost_score, "分") }}</template>
                </el-table-column>
                <el-table-column label="诊断" width="110">
                  <template #default="{ row }">
                    <el-tag :type="getKnowledgeDiagnosisTone(row.diagnosis_label)" effect="light">{{ row.diagnosis_label }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="主错因" min-width="130">
                  <template #default="{ row }">{{ row.dominant_error_tag || formatErrorTagStats(row.error_tag_stats) }}</template>
                </el-table-column>
                <el-table-column label="题号" width="120">
                  <template #default="{ row }">{{ formatQuestionNumbers(row.question_numbers) }}</template>
                </el-table-column>
                <el-table-column label="建议" prop="suggestion" min-width="260" />
              </el-table>
            </div>
            <el-empty v-else description="当前学生暂无知识点题分明细。请先导入阅卷题分表。" />
            <div class="panel-title-row knowledge-trend-title">
              <div>
                <h4>连续知识点趋势</h4>
                <p>按最近 5 次已导入题分明细的趋势考试，识别持续薄弱、改善和反复波动的知识点。</p>
              </div>
            </div>
            <div v-if="filteredKnowledgeTrends.length" class="table-shell table-gap">
              <el-table :data="filteredKnowledgeTrends" stripe>
                <el-table-column label="科目" prop="subject_name" width="90" />
                <el-table-column label="知识路径" min-width="190">
                  <template #default="{ row }">{{ knowledgeDisplayName(row) }}</template>
                </el-table-column>
                <el-table-column label="趋势标签" width="110">
                  <template #default="{ row }">
                    <el-tag :type="getKnowledgeTrendTone(row.trend_label)" effect="light">{{ row.trend_label }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="最近得分率" width="110">
                  <template #default="{ row }">{{ formatPercentValue(row.latest_score_rate) }}</template>
                </el-table-column>
                <el-table-column label="平均得分率" width="110">
                  <template #default="{ row }">{{ formatPercentValue(row.average_score_rate) }}</template>
                </el-table-column>
                <el-table-column label="薄弱次数" width="100">
                  <template #default="{ row }">{{ row.weak_exam_count }} / {{ row.trend_exam_count }}</template>
                </el-table-column>
                <el-table-column label="主错因" min-width="130">
                  <template #default="{ row }">{{ row.dominant_error_tag || formatErrorTagStats(row.error_tag_stats) }}</template>
                </el-table-column>
                <el-table-column label="趋势变化" width="100">
                  <template #default="{ row }">{{ formatSignedNumber(row.trend_delta ? row.trend_delta * 100 : row.trend_delta, "%") }}</template>
                </el-table-column>
                <el-table-column label="轨迹" min-width="260">
                  <template #default="{ row }">{{ formatKnowledgeTrendTrack(row.points) }}</template>
                </el-table-column>
                <el-table-column label="建议" prop="suggestion" min-width="260" />
              </el-table>
            </div>
            <el-empty v-else description="需要至少 2 次导入题分明细后才能判断连续知识点趋势。" />
          </article>
          <div v-if="studentAnalytics" class="student-report-grid table-gap">
            <article class="soft-card inner-panel">
              <h4>进退步轨迹</h4>
              <div class="trend-list">
                <div v-for="item in studentAnalytics.trend_points" :key="item.exam_id" class="trend-row">
                  <span>{{ item.exam_name }}</span>
                  <strong>校内第 {{ item.grade_rank ?? "-" }}</strong>
                  <em>{{ item.total_score ?? "-" }} 分</em>
                </div>
              </div>
            </article>
            <article class="soft-card inner-panel">
              <h4>行动建议</h4>
              <div v-if="studentAnalytics.action_suggestions?.length" class="suggestion-list">
                <el-alert
                  v-for="item in studentAnalytics.action_suggestions"
                  :key="`${item.category}-${item.title}`"
                  :type="getSuggestionTone(item.category)"
                  :closable="false"
                  show-icon
                  :title="item.title"
                  :description="item.summary"
                />
              </div>
              <el-empty v-else description="当前暂无自动建议。" />
            </article>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="班级分析" name="class" lazy>
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
          <el-empty v-if="!classAnalytics && !scoreRecordTotal" description="当前成绩记录为 0。请先导入成绩，再查看班级均分、分科质量和横向比较。" />
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
          <article v-if="classAnalytics" class="soft-card inner-panel knowledge-panel table-gap">
            <div class="panel-title-row">
              <div>
                <h4>班级知识点讲评清单</h4>
                <p>按弱项学生数、失分规模和错因分布排序，服务备课组讲评与个人补弱任务。</p>
              </div>
              <div class="knowledge-actions">
                <el-select v-model="classKnowledgeSubjectFilter" clearable placeholder="全部科目" style="width: 180px">
                  <el-option
                    v-for="subject in classAnalytics.subject_breakdown"
                    :key="subject.subject_id"
                    :label="subject.subject_name"
                    :value="subject.subject_id"
                  />
                </el-select>
                <el-button :loading="loadingClassKnowledgeBriefing" @click="loadClassKnowledgeBriefing">加载讲评清单</el-button>
                <el-button :disabled="!selectedClassKnowledgeIds.length" @click="previewClassKnowledgeTasks">预览任务</el-button>
                <el-button type="primary" plain :disabled="!selectedClassKnowledgeIds.length" :loading="generatingClassKnowledgeTasks" @click="generateClassKnowledgeTasks">批量生成任务</el-button>
                <el-button plain @click="openClassKnowledgePrint">打印讲评</el-button>
              </div>
            </div>
            <el-alert
              v-if="classKnowledgeTaskPreview"
              class="table-gap"
              type="info"
              show-icon
              :closable="false"
              :title="formatTaskPreviewSummary(classKnowledgeTaskPreview.create_count, classKnowledgeTaskPreview.skip_count)"
            />
            <div v-if="classKnowledgeBriefing?.items?.length" class="table-shell table-gap">
              <el-table :data="classKnowledgeBriefing.items" stripe @selection-change="handleClassKnowledgeSelection">
                <el-table-column type="selection" width="45" />
                <el-table-column label="科目" prop="subject_name" width="90" />
                <el-table-column label="知识路径" prop="knowledge_path" min-width="190" />
                <el-table-column label="弱项学生" width="100">
                  <template #default="{ row }">{{ row.weak_student_count }} / {{ row.total_student_count }}</template>
                </el-table-column>
                <el-table-column label="平均得分率" width="110">
                  <template #default="{ row }">{{ formatPercentValue(row.average_score_rate) }}</template>
                </el-table-column>
                <el-table-column label="错因分布" min-width="160">
                  <template #default="{ row }">{{ formatErrorTagStats(row.error_tag_stats) }}</template>
                </el-table-column>
                <el-table-column label="题号" width="120">
                  <template #default="{ row }">{{ formatQuestionNumbers(row.question_numbers) }}</template>
                </el-table-column>
                <el-table-column label="优先级" width="90">
                  <template #default="{ row }">
                    <el-tag :type="getBriefingPriorityTone(row.priority_label)" effect="light">{{ row.priority_label }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="建议" prop="suggestion" min-width="260" />
              </el-table>
            </div>
            <el-empty v-else description="当前班级暂无知识点讲评清单。请先导入题分明细。" />
          </article>
        </section>
      </el-tab-pane>

      <el-tab-pane label="年级分析" name="grade" lazy>
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
          <section v-if="selectedExamId" class="soft-card inner-panel target-line-panel">
            <div class="inner-head">
              <h4>年级目标线</h4>
              <div class="action-row">
                <el-button size="small" @click="addTargetLineDraft">新增目标线</el-button>
                <el-button size="small" type="primary" :loading="savingTargetLines" @click="saveTargetLines">保存目标线</el-button>
              </div>
            </div>
            <div class="table-shell">
              <el-table :data="targetLineDrafts" stripe>
                <el-table-column label="名称" min-width="140">
                  <template #default="{ row }">
                    <el-input v-model="row.name" placeholder="如 本科线" />
                  </template>
                </el-table-column>
                <el-table-column label="类型" width="130">
                  <template #default="{ row }">
                    <el-select v-model="row.line_type">
                      <el-option label="分数线" value="score" />
                      <el-option label="名次线" value="rank" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="分数" width="130">
                  <template #default="{ row }">
                    <el-input-number v-model="row.score_value" :disabled="row.line_type !== 'score'" :min="0" controls-position="right" />
                  </template>
                </el-table-column>
                <el-table-column label="名次" width="130">
                  <template #default="{ row }">
                    <el-input-number v-model="row.rank_value" :disabled="row.line_type !== 'rank'" :min="1" controls-position="right" />
                  </template>
                </el-table-column>
                <el-table-column label="临界分" width="130">
                  <template #default="{ row }">
                    <el-input-number v-model="row.near_margin_score" :min="0" controls-position="right" />
                  </template>
                </el-table-column>
                <el-table-column label="临界名次" width="130">
                  <template #default="{ row }">
                    <el-input-number v-model="row.near_margin_rank" :min="0" controls-position="right" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="90">
                  <template #default="{ $index }">
                    <el-button link type="danger" @click="removeTargetLineDraft($index)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </section>
          <el-empty v-if="!gradeAnalytics && !scoreRecordTotal" description="当前成绩记录为 0。请先导入成绩，再查看年级分数段、名次段和班级横向对比。" />
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

          <div v-if="gradeAnalytics?.rank_audit_summary?.warnings?.length" class="dashboard-tip-stack">
            <el-alert
              v-for="item in gradeAnalytics.rank_audit_summary.warnings"
              :key="item"
              type="warning"
              show-icon
              :closable="false"
              :title="item"
            />
          </div>

          <div v-if="gradeAnalytics?.target_line_summaries?.length" class="distribution-grid">
            <article class="soft-card distribution-card">
              <h4>达线率</h4>
              <div class="distribution-list">
                <div v-for="item in gradeAnalytics.target_line_summaries" :key="item.line_id" class="distribution-item">
                  <span>{{ item.line_name }} · {{ item.threshold_label }}</span>
                  <strong>{{ item.reached_count }} / {{ formatPercent(item.reached_rate) }}</strong>
                </div>
              </div>
            </article>
            <article class="soft-card distribution-card">
              <h4>临界样本</h4>
              <div class="distribution-list">
                <div v-for="item in gradeAnalytics.target_line_summaries" :key="`${item.line_id}-near`" class="distribution-item">
                  <span>{{ item.line_name }}</span>
                  <strong>线下 {{ item.near_below_count }} · 线上 {{ item.near_above_count }}</strong>
                </div>
              </div>
            </article>
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
                  <el-table-column label="目标达线" min-width="150">
                    <template #default="{ row }">
                      {{ formatTargetLineCounts(row.target_line_counts) }}
                    </template>
                  </el-table-column>
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

          <div v-if="gradeAnalytics?.class_contributions?.length || gradeAnalytics?.critical_students?.length" class="split-grid">
            <section class="soft-card inner-panel">
              <div class="inner-head">
                <h4>班级贡献</h4>
              </div>
              <div class="table-shell">
                <el-table :data="gradeAnalytics.class_contributions" stripe>
                  <el-table-column label="班级" prop="class_name" min-width="100" />
                  <el-table-column label="人数" prop="student_count" width="80" />
                  <el-table-column label="均分" prop="average_score" width="90" />
                  <el-table-column label="前30" prop="top30_count" width="80" />
                  <el-table-column label="优势学科" prop="strongest_subject" width="100" />
                  <el-table-column label="攻坚学科" prop="weakest_subject" width="100" />
                  <el-table-column label="达线" min-width="150">
                    <template #default="{ row }">
                      {{ formatTargetLineCounts(row.target_line_counts) }}
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </section>
            <section class="soft-card inner-panel">
              <div class="inner-head">
                <h4>临界学生</h4>
              </div>
              <div class="table-shell">
                <el-table :data="gradeAnalytics.critical_students" stripe>
                  <el-table-column label="学生" prop="student_name" min-width="100" />
                  <el-table-column label="班级" prop="class_name" width="100" />
                  <el-table-column label="总分" prop="total_score" width="80" />
                  <el-table-column label="校内名次" prop="school_rank" width="100" />
                  <el-table-column label="目标线" prop="line_name" width="110" />
                  <el-table-column label="距离" prop="gap_label" width="90" />
                </el-table>
              </div>
            </section>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="教师分析" name="teacher" lazy>
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
          <el-empty v-if="!teacherAnalytics && !scoreRecordTotal" description="当前成绩记录为 0。请先导入成绩并维护任教关系，再查看教师分析。" />
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

      <el-tab-pane label="全景对比" name="grade-panorama" lazy>
        <GradePanoramaPanel
          v-model:selected-grade-id="selectedPanoramaGradeId"
          v-model:selected-academic-year-ids="selectedPanoramaAcademicYearIds"
          :grades="referenceStore.grades"
          :academic-years="referenceStore.academicYears"
          :panorama="gradePanorama"
          :loading="loadingGradePanorama"
          @load="loadGradePanorama"
          @reset="resetGradePanoramaFilters"
        />
      </el-tab-pane>

      <el-tab-pane label="班级全景" name="class-panorama" lazy>
        <ClassPanoramaPanel
          v-model:selected-class-id="selectedPanoramaClassId"
          v-model:selected-academic-year-ids="selectedClassPanoramaAcademicYearIds"
          :classes="referenceStore.classes"
          :academic-years="referenceStore.academicYears"
          :panorama="classPanorama"
          :loading="loadingClassPanorama"
          @load="loadClassPanorama"
          @reset="resetClassPanoramaFilters"
        />
      </el-tab-pane>

      <el-tab-pane label="教师全景" name="teacher-panorama" lazy>
        <TeacherPanoramaPanel
          v-model:selected-teacher-id="selectedPanoramaTeacherId"
          v-model:selected-academic-year-ids="selectedTeacherPanoramaAcademicYearIds"
          :teachers="teacherOptions"
          :academic-years="referenceStore.academicYears"
          :panorama="teacherPanorama"
          :loading="loadingTeacherPanorama"
          @load="loadTeacherPanorama"
          @reset="resetTeacherPanoramaFilters"
        />
      </el-tab-pane>
    </el-tabs>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import ElMessage from "element-plus/es/components/message/index";

import type { UploadFile } from "element-plus";

import { apiRequest, uploadFile } from "../api/client";
import {
  adviserRiskTagType,
  buildAdviserDashboardEmptyTips,
  formatGrowthSummary,
  formatPlanningSummary,
  type AdviserDashboardResponse,
  type AdviserRiskStudentItem,
} from "../components/analytics/adviserDashboard";
import ClassPanoramaPanel from "../components/analytics/ClassPanoramaPanel.vue";
import GradePanoramaPanel from "../components/analytics/GradePanoramaPanel.vue";
import {
  buildStudentRadarRows,
  filterKnowledgePointsBySubject,
  filterKnowledgeTrendsBySubject,
  formatErrorTagStats,
  formatExamStudentOptionLabel,
  formatDiagnosisTags,
  formatKnowledgeTrendTrack,
  formatPercentValue,
  formatQuestionNumbers,
  formatSignedNumber,
  formatTaskPreviewSummary,
  getBriefingPriorityTone,
  getKnowledgeDiagnosisTone,
  getKnowledgeTrendTone,
  getSuggestionTone,
  getTargetGapSummary,
  knowledgeDisplayName,
  pickExamStudentSelection,
  type RadarMetric,
} from "../components/analytics/studentReport";
import {
  buildExamScoreReportQuery,
  buildVisibleSubjectIds,
  formatPercentCell,
  formatScoreCell,
  getSubjectScore,
  normalizeExamScoreReportRows,
  type ExamScoreReportResponse,
} from "../components/analytics/scoreReport";
import type { ImportFeedbackResult } from "../utils/importFeedback";
import TeacherPanoramaPanel from "../components/analytics/TeacherPanoramaPanel.vue";
import type {
  ClassPanoramaResponse,
  GradePanoramaResponse,
  TeacherPanoramaResponse,
} from "../components/analytics/types";
import { AppFilterBar, AppPage, AppSectionCard, AppStatGrid, type StatCardItem } from "../components/ui";
import { useReferenceStore } from "../stores/reference";
import { buildScoreReadinessMessages } from "../utils/scoreReadiness";
import { classKnowledgeBriefingPrintPreviewPath, studentKnowledgePrintPreviewPath } from "../utils/print";

interface ExamOption {
  id: number;
  name: string;
}

interface StudentOption {
  id: number;
  student_no: string;
  name: string;
  current_class_name?: string | null;
  total_score?: number | null;
  grade_rank?: number | null;
}

interface TeacherOption {
  id: number;
  name: string;
}

interface ScoreClassMappingRead {
  id: number;
  exam_id: number;
  source_class_name: string;
  mapped_class_id?: number | null;
  mapped_class_name?: string | null;
  mapping_status: string;
  note?: string | null;
  student_count: number;
}

interface ScoreRankAudit {
  exam_id: number;
  exam_name: string;
  rank_scope_label: string;
  total_students: number;
  context_count: number;
  mapped_context_count: number;
  unmapped_context_count: number;
  mapping_rate: number;
  source_class_count: number;
  mapped_class_count: number;
  source_rank_count: number;
  rank_diff_count: number;
  warnings: string[];
  class_mappings: ScoreClassMappingRead[];
}

interface ScoreTargetLineDraft {
  id?: number;
  exam_id?: number;
  name: string;
  line_type: "score" | "rank";
  score_value?: number | null;
  rank_value?: number | null;
  near_margin_score?: number | null;
  near_margin_rank?: number | null;
  sort_order: number;
  note?: string | null;
  is_active: boolean;
}

const referenceStore = useReferenceStore();
const router = useRouter();
const examOptions = ref<ExamOption[]>([]);
const studentOptions = ref<StudentOption[]>([]);
const teacherOptions = ref<TeacherOption[]>([]);

const activeAnalyticsTab = ref("adviser");
const selectedExamId = ref<number | null>(null);
const selectedStudentId = ref<number | null>(null);
const selectedClassId = ref<number | null>(null);
const selectedGradeId = ref<number | null>(null);
const selectedTeacherId = ref<number | null>(null);
const selectedPanoramaGradeId = ref<number | null>(null);
const selectedPanoramaAcademicYearIds = ref<number[]>([]);
const selectedPanoramaClassId = ref<number | null>(null);
const selectedClassPanoramaAcademicYearIds = ref<number[]>([]);
const selectedPanoramaTeacherId = ref<number | null>(null);
const selectedTeacherPanoramaAcademicYearIds = ref<number[]>([]);
const loadingGradePanorama = ref(false);
const loadingClassPanorama = ref(false);
const loadingTeacherPanorama = ref(false);
const scoreRecordTotal = ref(0);
const adviserGradeId = ref<number | null>(null);
const adviserClassId = ref<number | null>(null);
const adviserDateRange = ref<[string, string] | null>(null);
const adviserDashboard = ref<AdviserDashboardResponse | null>(null);
const loadingAdviserDashboard = ref(false);
const scoreReport = ref<ExamScoreReportResponse | null>(null);
const loadingScoreReport = ref(false);
const scoreReportClassId = ref<number | null>(null);
const scoreReportKeyword = ref("");
const scoreReportSortMode = ref("grade_rank:asc");
const scoreReportPage = ref(1);
const scoreReportPageSize = ref(50);
const selectedScoreReportSubjectIds = ref<number[]>([]);
const rankAudit = ref<ScoreRankAudit | null>(null);
const loadingRankAudit = ref(false);
const rebuildingSnapshots = ref(false);
const targetLineDrafts = ref<ScoreTargetLineDraft[]>([]);
const savingTargetLines = ref(false);
const studentRadarMetric = ref<RadarMetric>("pr");
const knowledgeSubjectFilter = ref<number | null>(null);
const classKnowledgeSubjectFilter = ref<number | null>(null);
const importingQuestionScores = ref(false);
const questionImportStrategy = ref("overwrite");
const questionImportResult = ref<(ImportFeedbackResult & { batch_id?: number; snapshot_count?: number }) | null>(null);
const studentRadarOptions = [
  { label: "PR", value: "pr" },
  { label: "T分", value: "t_score" },
];

const studentAnalytics = ref<any>(null);
const classAnalytics = ref<any>(null);
const classKnowledgeBriefing = ref<any>(null);
const selectedClassKnowledgeIds = ref<number[]>([]);
const loadingClassKnowledgeBriefing = ref(false);
const studentKnowledgeTaskPreview = ref<any>(null);
const classKnowledgeTaskPreview = ref<any>(null);
const previewingStudentKnowledgeTasks = ref(false);
const generatingStudentKnowledgeTasks = ref(false);
const generatingClassKnowledgeTasks = ref(false);
const gradeAnalytics = ref<any>(null);
const teacherAnalytics = ref<any>(null);
const gradePanorama = ref<GradePanoramaResponse | null>(null);
const classPanorama = ref<ClassPanoramaResponse | null>(null);
const teacherPanorama = ref<TeacherPanoramaResponse | null>(null);
const selectedExamName = computed(
  () => examOptions.value.find((item) => item.id === selectedExamId.value)?.name ?? "未选择考试",
);
const analyticsPageMeta = computed(() => [
  { label: "考试", value: examOptions.value.length },
  { label: "可分析学生", value: studentOptions.value.length },
  { label: "教师", value: teacherOptions.value.length },
  { label: "当前考试", value: selectedExamName.value },
]);
const scoreReadinessMessages = computed(() =>
  buildScoreReadinessMessages({
    examCount: examOptions.value.length,
    scoreRecordTotal: scoreRecordTotal.value,
    selectedExamName: selectedExamId.value ? selectedExamName.value : null,
  }),
);
const analyticsOverviewCards = computed<StatCardItem[]>(() => [
  {
    label: "考试",
    value: examOptions.value.length,
    help: "当前系统可用于切换分析上下文的考试数量。",
    tone: "primary",
  },
  {
    label: "可分析学生",
    value: studentOptions.value.length,
    help: "当前考试已有成绩快照、可进入个人分析的学生数。",
    tone: "neutral",
  },
  {
    label: "分科条目",
    value: studentAnalytics.value ? studentAnalytics.value.subjects?.length ?? 0 : 0,
    help: "当前学生分析里可查看的分科条目。",
    tone: "primary",
  },
  {
    label: "班级结果",
    value: classAnalytics.value ? classAnalytics.value.subject_breakdown?.length ?? 0 : 0,
    help: "当前班级分析里的学科拆分数量。",
    tone: "warning",
  },
  {
    label: "年级结果",
    value: gradeAnalytics.value ? gradeAnalytics.value.student_count ?? 0 : 0,
    help: "当前年级分析覆盖的学生数。",
    tone: "neutral",
  },
]);
const scoreReportCards = computed<StatCardItem[]>(() => {
  const summary = scoreReport.value?.summary;
  return [
    {
      label: "学生数",
      value: summary?.student_count ?? 0,
      help: "当前筛选下进入本次考试成绩报表的学生数。",
      tone: "primary",
    },
    {
      label: "科目数",
      value: summary?.subject_count ?? 0,
      help: "本次考试可展示的单科成绩列。",
      tone: "neutral",
    },
    {
      label: "总分均分",
      value: formatScoreCell(summary?.total_average),
      help: "当前筛选结果中有总分快照学生的平均分。",
      tone: "success",
    },
    {
      label: "最高分",
      value: formatScoreCell(summary?.total_max),
      help: "当前筛选结果中的总分最高值。",
      tone: "primary",
    },
    {
      label: "最低分",
      value: formatScoreCell(summary?.total_min),
      help: "当前筛选结果中的总分最低值。",
      tone: "warning",
    },
  ];
});
const scoreReportTableRows = computed(() => normalizeExamScoreReportRows(scoreReport.value?.rows ?? []));
const visibleScoreReportSubjects = computed(() => {
  if (!scoreReport.value) return [];
  const visibleIds = new Set(buildVisibleSubjectIds(scoreReport.value.subjects, selectedScoreReportSubjectIds.value));
  return scoreReport.value.subjects.filter((item) => visibleIds.has(item.subject_id));
});
const rankAuditCards = computed<StatCardItem[]>(() =>
  rankAudit.value
    ? [
        { label: "名次口径", value: rankAudit.value.rank_scope_label, help: "当前考试快照采用的排名范围。", tone: "primary" },
        { label: "映射率", value: formatPercent(rankAudit.value.mapping_rate), help: "源班级成功映射到系统班级的比例。", tone: "success" },
        { label: "样本数", value: rankAudit.value.total_students, help: "参与本地排名重算的有效学生。", tone: "neutral" },
        { label: "名次差异", value: rankAudit.value.rank_diff_count, help: "平台原始名次与系统样本名次存在差异的记录。", tone: "warning" },
      ]
    : [],
);
const studentRadarRows = computed(() =>
  studentAnalytics.value ? buildStudentRadarRows(studentAnalytics.value.subjects ?? [], studentRadarMetric.value) : [],
);
const filteredKnowledgePoints = computed(() =>
  studentAnalytics.value
    ? filterKnowledgePointsBySubject(studentAnalytics.value.knowledge_points ?? [], knowledgeSubjectFilter.value)
    : [],
);
const filteredKnowledgeTrends = computed(() =>
  studentAnalytics.value
    ? filterKnowledgeTrendsBySubject(studentAnalytics.value.knowledge_trends ?? [], knowledgeSubjectFilter.value)
    : [],
);
const adviserDashboardTips = computed(() => buildAdviserDashboardEmptyTips(adviserDashboard.value));

const adviserOverviewCards = computed(() => {
  const overview = adviserDashboard.value?.overview;
  return [
    {
      label: "学生数",
      value: overview?.student_count ?? 0,
      help: "当前年级或班级范围内的在读学生样本。",
      tone: "tone-blue",
    },
    {
      label: "成绩样本",
      value: overview?.score_sample_count ?? 0,
      help: "用于本次风险判断的成绩快照样本。",
      tone: "tone-slate",
    },
    {
      label: "需跟进",
      value: overview?.follow_up_count ?? 0,
      help: "紧急跟进和需要跟进的学生合计。",
      tone: "tone-amber",
    },
    {
      label: "规划任务",
      value: overview?.open_task_count ?? 0,
      help: "当前范围内未完成的升学规划与阶段跟进任务。",
      tone: "tone-slate",
    },
  ];
});

async function loadOptions(): Promise<void> {
  await referenceStore.loadCore();
  const [examPayload, teacherPayload] = await Promise.all([
    apiRequest<{ items: ExamOption[] }>("/api/exams?page=1&page_size=100"),
    apiRequest<{ items: TeacherOption[] }>("/api/teachers?page=1&page_size=200"),
  ]);
  try {
    const dashboardPayload = await apiRequest<{ score_record_total?: number }>("/api/dashboard/summary");
    scoreRecordTotal.value = dashboardPayload.score_record_total ?? 0;
  } catch {
    scoreRecordTotal.value = 0;
  }
  examOptions.value = examPayload.items;
  teacherOptions.value = teacherPayload.items;
  if (!selectedExamId.value && examOptions.value.length) {
    selectedExamId.value = examOptions.value[0].id;
  }
  if (selectedExamId.value) {
    await loadExamStudentOptions({ preserveCurrent: true });
  }
  if (!selectedClassId.value && referenceStore.classes.length) {
    selectedClassId.value = referenceStore.classes[0].id;
  }
  if (!selectedGradeId.value && referenceStore.grades.length) {
    selectedGradeId.value = referenceStore.grades[0].id;
  }
  if (!selectedTeacherId.value && teacherOptions.value.length) {
    selectedTeacherId.value = teacherOptions.value[0].id;
  }
  if (!selectedPanoramaGradeId.value && referenceStore.grades.length) {
    selectedPanoramaGradeId.value = referenceStore.grades[0].id;
  }
  if (!selectedPanoramaClassId.value && referenceStore.classes.length) {
    selectedPanoramaClassId.value = referenceStore.classes[0].id;
  }
  if (!selectedPanoramaTeacherId.value && teacherOptions.value.length) {
    selectedPanoramaTeacherId.value = teacherOptions.value[0].id;
  }
  if (!adviserGradeId.value && referenceStore.grades.length) {
    adviserGradeId.value = referenceStore.grades[0].id;
  }
}

async function loadExamStudentOptions(options: { preserveCurrent?: boolean } = {}): Promise<void> {
  if (!selectedExamId.value) {
    studentOptions.value = [];
    selectedStudentId.value = null;
    studentAnalytics.value = null;
    return;
  }
  try {
    const payload = await apiRequest<{ items: StudentOption[]; total: number }>(
      `/api/analytics/exams/${selectedExamId.value}/students`,
    );
    studentOptions.value = payload.items;
    const nextStudentId = pickExamStudentSelection(
      studentOptions.value,
      options.preserveCurrent ? selectedStudentId.value : null,
    );
    if (selectedStudentId.value !== nextStudentId) {
      selectedStudentId.value = nextStudentId;
      studentAnalytics.value = null;
    }
  } catch (error) {
    studentOptions.value = [];
    selectedStudentId.value = null;
    studentAnalytics.value = null;
    ElMessage.error((error as Error).message);
  }
}

async function loadStudentAnalytics(): Promise<void> {
  if (!selectedExamId.value || !selectedStudentId.value) return;
  try {
    studentAnalytics.value = await apiRequest(`/api/analytics/students/${selectedStudentId.value}?exam_id=${selectedExamId.value}`);
    studentKnowledgeTaskPreview.value = null;
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function handleQuestionScoreImport(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw || !selectedExamId.value) return;
  try {
    importingQuestionScores.value = true;
    questionImportResult.value = await uploadFile<ImportFeedbackResult & { batch_id: number; snapshot_count: number }>(
      `/api/exams/${selectedExamId.value}/score-questions/import`,
      uploadFileItem.raw,
      { strategy: questionImportStrategy.value },
    );
    ElMessage({
      type: questionImportResult.value.failed_rows ? "warning" : "success",
      message: questionImportResult.value.message,
    });
    if (selectedStudentId.value) {
      await loadStudentAnalytics();
    }
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    importingQuestionScores.value = false;
  }
}

async function loadClassAnalytics(): Promise<void> {
  if (!selectedExamId.value || !selectedClassId.value) return;
  try {
    classAnalytics.value = await apiRequest(`/api/analytics/classes/${selectedClassId.value}?exam_id=${selectedExamId.value}`);
    classKnowledgeBriefing.value = null;
    classKnowledgeTaskPreview.value = null;
    selectedClassKnowledgeIds.value = [];
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadClassKnowledgeBriefing(): Promise<void> {
  if (!selectedExamId.value || !selectedClassId.value) return;
  try {
    loadingClassKnowledgeBriefing.value = true;
    const query = new URLSearchParams({ exam_id: String(selectedExamId.value) });
    if (classKnowledgeSubjectFilter.value) query.set("subject_id", String(classKnowledgeSubjectFilter.value));
    classKnowledgeBriefing.value = await apiRequest(`/api/analytics/classes/${selectedClassId.value}/knowledge-briefing?${query.toString()}`);
    selectedClassKnowledgeIds.value = [];
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    loadingClassKnowledgeBriefing.value = false;
  }
}

async function previewStudentKnowledgeTasks(): Promise<void> {
  if (!selectedExamId.value || !selectedStudentId.value) return;
  try {
    previewingStudentKnowledgeTasks.value = true;
    studentKnowledgeTaskPreview.value = await apiRequest(
      `/api/planning/students/${selectedStudentId.value}/knowledge-tasks/preview?exam_id=${selectedExamId.value}`,
    );
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    previewingStudentKnowledgeTasks.value = false;
  }
}

async function generateStudentKnowledgeTasks(): Promise<void> {
  if (!selectedExamId.value || !selectedStudentId.value) return;
  try {
    generatingStudentKnowledgeTasks.value = true;
    const result = await apiRequest<{ created_count: number; skipped_count: number }>(
      `/api/planning/students/${selectedStudentId.value}/knowledge-tasks/generate?exam_id=${selectedExamId.value}`,
      { method: "POST", body: JSON.stringify({}) },
    );
    ElMessage.success(`已生成 ${result.created_count} 项，跳过 ${result.skipped_count} 项已有任务`);
    await previewStudentKnowledgeTasks();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    generatingStudentKnowledgeTasks.value = false;
  }
}

async function previewClassKnowledgeTasks(): Promise<void> {
  if (!selectedExamId.value || !selectedClassId.value || !selectedClassKnowledgeIds.value.length) return;
  try {
    const query = new URLSearchParams({ exam_id: String(selectedExamId.value) });
    selectedClassKnowledgeIds.value.forEach((id) => query.append("knowledge_point_ids", String(id)));
    classKnowledgeTaskPreview.value = await apiRequest(`/api/planning/classes/${selectedClassId.value}/knowledge-tasks/preview?${query.toString()}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function generateClassKnowledgeTasks(): Promise<void> {
  if (!selectedExamId.value || !selectedClassId.value || !selectedClassKnowledgeIds.value.length) return;
  try {
    generatingClassKnowledgeTasks.value = true;
    const result = await apiRequest<{ created_count: number; skipped_count: number }>(
      `/api/planning/classes/${selectedClassId.value}/knowledge-tasks/generate?exam_id=${selectedExamId.value}`,
      {
        method: "POST",
        body: JSON.stringify({ knowledge_point_ids: selectedClassKnowledgeIds.value }),
      },
    );
    ElMessage.success(`已生成 ${result.created_count} 项，跳过 ${result.skipped_count} 项已有任务`);
    await previewClassKnowledgeTasks();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    generatingClassKnowledgeTasks.value = false;
  }
}

function handleClassKnowledgeSelection(rows: Array<{ knowledge_point_id: number }>): void {
  selectedClassKnowledgeIds.value = rows.map((item) => item.knowledge_point_id);
  classKnowledgeTaskPreview.value = null;
}

function openStudentKnowledgePrint(): void {
  if (!selectedExamId.value || !selectedStudentId.value) return;
  window.open(studentKnowledgePrintPreviewPath(selectedStudentId.value, selectedExamId.value), "_blank", "noopener,noreferrer");
}

function openClassKnowledgePrint(): void {
  if (!selectedExamId.value || !selectedClassId.value) return;
  window.open(classKnowledgeBriefingPrintPreviewPath(selectedClassId.value, selectedExamId.value), "_blank", "noopener,noreferrer");
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
    if (!targetLineDrafts.value.length) {
      await loadTargetLines();
    }
    gradeAnalytics.value = await apiRequest(`/api/analytics/grades/${selectedGradeId.value}?exam_id=${selectedExamId.value}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadScoreRankAudit(): Promise<void> {
  if (!selectedExamId.value) return;
  try {
    loadingRankAudit.value = true;
    rankAudit.value = await apiRequest<ScoreRankAudit>(`/api/exams/${selectedExamId.value}/score-rank-audit`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    loadingRankAudit.value = false;
  }
}

async function rebuildScoreSnapshots(): Promise<void> {
  if (!selectedExamId.value) return;
  try {
    rebuildingSnapshots.value = true;
    const payload = await apiRequest<{ message: string; audit: ScoreRankAudit }>(
      `/api/exams/${selectedExamId.value}/scores/rebuild-snapshots`,
      { method: "POST" },
    );
    rankAudit.value = payload.audit;
    ElMessage.success(payload.message);
    if (selectedGradeId.value) {
      await loadGradeAnalytics();
    }
    if (selectedClassId.value) {
      await loadClassAnalytics();
    }
    if (selectedStudentId.value) {
      await loadStudentAnalytics();
    }
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    rebuildingSnapshots.value = false;
  }
}

async function loadTargetLines(): Promise<void> {
  if (!selectedExamId.value) return;
  try {
    const payload = await apiRequest<ScoreTargetLineDraft[]>(`/api/exams/${selectedExamId.value}/score-target-lines`);
    targetLineDrafts.value = payload.map((item, index) => ({
      ...item,
      sort_order: item.sort_order ?? index,
      is_active: item.is_active ?? true,
    }));
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function addTargetLineDraft(): void {
  targetLineDrafts.value.push({
    name: "",
    line_type: "score",
    score_value: null,
    rank_value: null,
    near_margin_score: 10,
    near_margin_rank: 20,
    sort_order: targetLineDrafts.value.length,
    note: "",
    is_active: true,
  });
}

function removeTargetLineDraft(index: number): void {
  targetLineDrafts.value.splice(index, 1);
  targetLineDrafts.value.forEach((item, itemIndex) => {
    item.sort_order = itemIndex;
  });
}

async function saveTargetLines(): Promise<void> {
  if (!selectedExamId.value) return;
  const payload = targetLineDrafts.value
    .filter((item) => item.name.trim())
    .map((item, index) => ({
      name: item.name.trim(),
      line_type: item.line_type,
      score_value: item.line_type === "score" ? item.score_value ?? null : null,
      rank_value: item.line_type === "rank" ? item.rank_value ?? null : null,
      near_margin_score: item.near_margin_score ?? null,
      near_margin_rank: item.near_margin_rank ?? null,
      sort_order: index,
      note: item.note ?? "",
      is_active: item.is_active,
    }));
  try {
    savingTargetLines.value = true;
    targetLineDrafts.value = await apiRequest<ScoreTargetLineDraft[]>(
      `/api/exams/${selectedExamId.value}/score-target-lines`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
    );
    ElMessage.success("目标线已保存");
    if (selectedGradeId.value) {
      await loadGradeAnalytics();
    }
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingTargetLines.value = false;
  }
}

async function loadAdviserDashboard(): Promise<void> {
  try {
    loadingAdviserDashboard.value = true;
    const query = new URLSearchParams();
    if (adviserGradeId.value) query.set("grade_id", String(adviserGradeId.value));
    if (adviserClassId.value) query.set("class_id", String(adviserClassId.value));
    if (selectedExamId.value) query.set("exam_id", String(selectedExamId.value));
    if (adviserDateRange.value?.[0]) query.set("start_date", adviserDateRange.value[0]);
    if (adviserDateRange.value?.[1]) query.set("end_date", adviserDateRange.value[1]);
    const suffix = query.toString() ? `?${query.toString()}` : "";
    adviserDashboard.value = await apiRequest<AdviserDashboardResponse>(`/api/analytics/adviser-dashboard${suffix}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    loadingAdviserDashboard.value = false;
  }
}

async function loadScoreReport(): Promise<void> {
  if (!selectedExamId.value) return;
  const [sortBy, sortOrder] = scoreReportSortMode.value.split(":");
  try {
    loadingScoreReport.value = true;
    const query = buildExamScoreReportQuery({
      classId: scoreReportClassId.value,
      keyword: scoreReportKeyword.value,
      sortBy,
      sortOrder,
      page: scoreReportPage.value,
      pageSize: scoreReportPageSize.value,
    });
    scoreReport.value = await apiRequest<ExamScoreReportResponse>(
      `/api/analytics/exams/${selectedExamId.value}/score-report${query}`,
    );
    const selectedSubjectIds = new Set(selectedScoreReportSubjectIds.value);
    selectedScoreReportSubjectIds.value = scoreReport.value.subjects
      .filter((subject) => selectedSubjectIds.has(subject.subject_id))
      .map((subject) => subject.subject_id);
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    loadingScoreReport.value = false;
  }
}

async function reloadScoreReportFromFirstPage(): Promise<void> {
  scoreReportPage.value = 1;
  await loadScoreReport();
}

async function handleScoreReportPageSizeChange(): Promise<void> {
  scoreReportPage.value = 1;
  await loadScoreReport();
}

function openRiskStudent(row: AdviserRiskStudentItem): void {
  router.push(`/students/${row.student_id}`);
}

function openRiskStudentFollowup(row: AdviserRiskStudentItem): void {
  const query = new URLSearchParams({ report_type: "student_followup_package", student_id: String(row.student_id) });
  if (selectedExamId.value) query.set("exam_id", String(selectedExamId.value));
  router.push(`/reports?${query.toString()}`);
}

function openRiskStudentReport(row: AdviserRiskStudentItem): void {
  const query = new URLSearchParams({ report_type: "student_analysis", student_id: String(row.student_id) });
  if (selectedExamId.value) query.set("exam_id", String(selectedExamId.value));
  router.push(`/reports?${query.toString()}`);
}

function openAdviserAction(path?: string | null): void {
  if (!path) return;
  router.push(path);
}

async function loadGradePanorama(): Promise<void> {
  if (!selectedPanoramaGradeId.value || loadingGradePanorama.value) return;
  try {
    loadingGradePanorama.value = true;
    const query = new URLSearchParams();
    selectedPanoramaAcademicYearIds.value.forEach((item) => {
      query.append("academic_year_ids", String(item));
    });
    const suffix = query.toString() ? `?${query.toString()}` : "";
    gradePanorama.value = await apiRequest<GradePanoramaResponse>(
      `/api/analytics/grades/${selectedPanoramaGradeId.value}/panorama${suffix}`,
    );
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    loadingGradePanorama.value = false;
  }
}

async function loadClassPanorama(): Promise<void> {
  if (!selectedPanoramaClassId.value || loadingClassPanorama.value) return;
  try {
    loadingClassPanorama.value = true;
    const query = new URLSearchParams();
    selectedClassPanoramaAcademicYearIds.value.forEach((item) => {
      query.append("academic_year_ids", String(item));
    });
    const suffix = query.toString() ? `?${query.toString()}` : "";
    classPanorama.value = await apiRequest<ClassPanoramaResponse>(
      `/api/analytics/classes/${selectedPanoramaClassId.value}/panorama${suffix}`,
    );
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    loadingClassPanorama.value = false;
  }
}

async function loadTeacherPanorama(): Promise<void> {
  if (!selectedPanoramaTeacherId.value || loadingTeacherPanorama.value) return;
  try {
    loadingTeacherPanorama.value = true;
    const query = new URLSearchParams();
    selectedTeacherPanoramaAcademicYearIds.value.forEach((item) => {
      query.append("academic_year_ids", String(item));
    });
    const suffix = query.toString() ? `?${query.toString()}` : "";
    teacherPanorama.value = await apiRequest<TeacherPanoramaResponse>(
      `/api/analytics/teachers/${selectedPanoramaTeacherId.value}/panorama${suffix}`,
    );
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    loadingTeacherPanorama.value = false;
  }
}

function resetGradePanoramaFilters(): void {
  selectedPanoramaAcademicYearIds.value = [];
  gradePanorama.value = null;
  if (!selectedPanoramaGradeId.value && referenceStore.grades.length) {
    selectedPanoramaGradeId.value = referenceStore.grades[0].id;
  }
}

function resetClassPanoramaFilters(): void {
  selectedClassPanoramaAcademicYearIds.value = [];
  classPanorama.value = null;
  if (!selectedPanoramaClassId.value && referenceStore.classes.length) {
    selectedPanoramaClassId.value = referenceStore.classes[0].id;
  }
}

function resetTeacherPanoramaFilters(): void {
  selectedTeacherPanoramaAcademicYearIds.value = [];
  teacherPanorama.value = null;
  if (!selectedPanoramaTeacherId.value && teacherOptions.value.length) {
    selectedPanoramaTeacherId.value = teacherOptions.value[0].id;
  }
}

function resetAnalyticsState(): void {
  studentAnalytics.value = null;
  scoreReport.value = null;
  selectedScoreReportSubjectIds.value = [];
  knowledgeSubjectFilter.value = null;
  classAnalytics.value = null;
  classKnowledgeBriefing.value = null;
  classKnowledgeTaskPreview.value = null;
  studentKnowledgeTaskPreview.value = null;
  selectedClassKnowledgeIds.value = [];
  gradeAnalytics.value = null;
  teacherAnalytics.value = null;
  gradePanorama.value = null;
  classPanorama.value = null;
  teacherPanorama.value = null;
  adviserDashboard.value = null;
  rankAudit.value = null;
}

async function loadActivePanoramaIfNeeded(): Promise<void> {
  if (activeAnalyticsTab.value === "grade-panorama" && !gradePanorama.value) {
    await loadGradePanorama();
  } else if (activeAnalyticsTab.value === "class-panorama" && !classPanorama.value) {
    await loadClassPanorama();
  } else if (activeAnalyticsTab.value === "teacher-panorama" && !teacherPanorama.value) {
    await loadTeacherPanorama();
  }
}

function formatPercent(value?: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function studentDiagnosisTagType(value?: string): "success" | "warning" | "info" {
  if (value === "优势学科") return "success";
  if (value === "重点补弱" || value === "严重拖后腿" || value === "稳定性关注") return "warning";
  return "info";
}

function formatTargetLineCounts(value?: Record<string, number> | null): string {
  if (!value || !Object.keys(value).length) {
    return "-";
  }
  return Object.entries(value)
    .map(([name, count]) => `${name} ${count}`)
    .join(" / ");
}

watch(selectedExamId, async (examId) => {
  rankAudit.value = null;
  scoreReport.value = null;
  selectedScoreReportSubjectIds.value = [];
  gradeAnalytics.value = null;
  studentAnalytics.value = null;
  knowledgeSubjectFilter.value = null;
  classKnowledgeSubjectFilter.value = null;
  classKnowledgeBriefing.value = null;
  classKnowledgeTaskPreview.value = null;
  studentKnowledgeTaskPreview.value = null;
  selectedClassKnowledgeIds.value = [];
  questionImportResult.value = null;
  targetLineDrafts.value = [];
  if (examId) {
    await Promise.all([
      loadTargetLines(),
      loadExamStudentOptions({ preserveCurrent: true }),
    ]);
  } else {
    studentOptions.value = [];
    selectedStudentId.value = null;
  }
});

watch(activeAnalyticsTab, () => {
  void loadActivePanoramaIfNeeded();
});

onMounted(async () => {
  try {
    await loadOptions();
    if (selectedExamId.value) {
      await loadTargetLines();
    }
    await loadActivePanoramaIfNeeded();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
});
</script>

<style scoped>
.analysis-hero-grid {
  display: grid;
  grid-template-columns: minmax(280px, 0.9fr) minmax(0, 1.8fr);
  gap: 16px;
  align-items: stretch;
}

.score-readiness-stack {
  display: grid;
  gap: 10px;
}

.overview-panel,
.overview-card {
  padding: 20px;
}

.overview-panel {
  background: #fff;
}

.overview-kicker {
  display: inline-flex;
  padding: 5px 8px;
  border-radius: 6px;
  background: var(--accent-primary-soft);
  color: var(--accent-primary);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0;
}

.overview-panel h2 {
  margin: 14px 0 0;
  color: var(--text-main);
  font-size: 22px;
  font-weight: 650;
  line-height: 1.25;
}

.overview-panel p {
  margin: 12px 0 0;
  color: var(--text-muted);
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
  box-shadow: inset 3px 0 0 rgba(92, 111, 129, 0.74), var(--shadow-card);
}

.analytics-grid {
  margin-top: 16px;
}

.knowledge-import-row {
  margin-top: 12px;
}

.inline-import-result {
  flex: 1;
  min-width: 260px;
}

.score-report-filter-grid {
  grid-template-columns: minmax(150px, 0.9fr) minmax(180px, 1fr) minmax(180px, 0.9fr) minmax(130px, 0.6fr);
  align-items: center;
}

.score-report-filter-grid .el-button {
  width: 100%;
}

.score-report-toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 0.7fr) minmax(0, 1.3fr);
  gap: 12px;
  align-items: center;
  margin-top: 16px;
}

.score-report-table-shell {
  overflow: auto;
}

.score-report-pagination {
  justify-content: flex-end;
  margin-top: 14px;
}

.knowledge-panel p {
  margin: 6px 0 0;
  color: var(--text-muted);
  line-height: 1.55;
}

.knowledge-trend-title {
  margin-top: 18px;
}

.knowledge-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.adviser-filter-grid {
  grid-template-columns: minmax(150px, 0.8fr) minmax(150px, 0.8fr) minmax(280px, 1.4fr) minmax(120px, 0.6fr);
  align-items: center;
}

.adviser-filter-grid :deep(.el-date-editor--daterange) {
  width: 100%;
  max-width: 100%;
}

.adviser-filter-grid .el-button {
  width: 100%;
}

.dashboard-tip-stack {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.global-exam-select {
  width: 100%;
  max-width: 520px;
}

.analytics-tabs {
  padding: 18px 18px 0;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-lg);
  background: var(--bg-soft);
  box-shadow: var(--shadow-card);
}

.adviser-overview-grid {
  margin-top: 16px;
}

.adviser-overview-grid .stat-card p {
  margin: 8px 0 0;
  color: #6a7f92;
  line-height: 1.5;
}

.adviser-summary-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 0.8fr) minmax(0, 1.4fr);
  gap: 16px;
  margin-top: 16px;
}

.adviser-summary-grid p {
  margin: 0;
  color: #60748a;
  line-height: 1.6;
}

.action-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 7px 10px;
  border: 1px solid #d7e4ef;
  border-radius: 8px;
  background: #fff;
  color: #26394c;
  cursor: pointer;
}

.action-chip strong {
  color: var(--accent-primary);
}

.risk-action-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.risk-action-text {
  width: 100%;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.4;
}

.stat-card {
  padding: 18px 20px;
}

.table-gap {
  margin-top: 16px;
}

.student-report-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 16px;
  margin-top: 16px;
}

.student-overview-panel p {
  margin: 10px 0 0;
  color: #51677c;
  line-height: 1.65;
}

.report-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.panel-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-title-row h4,
.student-report-grid h4 {
  margin: 0;
  color: #21384d;
}

.radar-bars {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.radar-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr) 48px;
  align-items: center;
  gap: 10px;
  color: #52687e;
  font-size: 13px;
}

.radar-track {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #e7eef5;
}

.radar-track i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #1f6c98, #58a7bd);
}

.radar-row strong {
  color: #1f3448;
  text-align: right;
}

.muted-inline {
  margin-left: 8px;
  color: #73879b;
  font-size: 12px;
}

.trend-list,
.suggestion-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.trend-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 92px 70px;
  gap: 10px;
  align-items: center;
  min-height: 34px;
  color: #52687e;
  font-size: 13px;
}

.trend-row span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trend-row strong {
  color: #1f3448;
}

.trend-row em {
  color: #6d8194;
  font-style: normal;
  text-align: right;
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
  border-radius: var(--radius-md);
  background: var(--bg-panel);
}

@media (max-width: 1180px) {
  .analysis-hero-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .adviser-filter-grid,
  .score-report-filter-grid,
  .score-report-toolbar,
  .adviser-summary-grid,
  .student-report-grid,
  .distribution-grid,
  .split-grid {
    grid-template-columns: 1fr;
  }
}
</style>
