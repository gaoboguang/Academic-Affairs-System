<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">教学执行 / 课表与工作量</div>
        <h2 class="page-title">课表与工作量</h2>
        <p class="page-subtitle">
          完成课表导入、未匹配项修正、规则版本配置、附加量化录入和教师工作量计算，历史结果按规则版本保留快照。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>当前学期</strong>{{ currentSemesterLabel }}</span>
          <span class="page-chip"><strong>规则版本</strong>{{ currentRuleLabel }}</span>
          <span class="page-chip"><strong>当前批次未匹配</strong>{{ currentBatch?.unresolved_count ?? 0 }}</span>
          <span class="page-chip"><strong>结果教师</strong>{{ results.length }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="refreshAll">刷新数据</el-button>
        <el-button @click="downloadTimetableTemplate">课表模板下载</el-button>
        <el-button type="primary" :loading="calculating" @click="calculateWorkload">
          计算工作量
        </el-button>
      </div>
    </header>

    <section class="overview-grid">
      <article class="soft-card overview-panel">
        <div class="overview-kicker">工作量闭环</div>
        <h3>{{ currentSemesterLabel }}</h3>
        <p>先导入课表并修正未匹配项，再确认规则版本和附加项，最后统一计算并导出工作量结果。</p>
      </article>
      <article v-for="item in overviewCards" :key="item.label" class="soft-card overview-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </section>

    <section class="soft-card panel-block">
      <div class="section-head compact">
        <div>
          <h3>计算上下文</h3>
          <p>工作量结果由学期、规则版本和课表批次共同决定，切换其中任一项后都建议重新确认结果。</p>
        </div>
      </div>
      <div class="filter-grid">
        <el-select v-model="selectedSemesterId" filterable placeholder="选择学期">
          <el-option
            v-for="semester in semesterOptions"
            :key="semester.id"
            :label="formatSemesterLabel(semester)"
            :value="semester.id"
          />
        </el-select>
        <el-select v-model="selectedRuleVersionId" filterable placeholder="选择规则版本">
          <el-option
            v-for="rule in ruleVersions"
            :key="rule.id"
            :label="ruleLabel(rule)"
            :value="rule.id"
          />
        </el-select>
        <el-select v-model="selectedBatchId" filterable clearable placeholder="选择课表批次">
          <el-option
            v-for="batch in timetableBatches"
            :key="batch.id"
            :label="batchLabel(batch)"
            :value="batch.id"
          />
        </el-select>
      </div>
      <div class="action-row toolbar-row">
        <el-button type="primary" :loading="calculating" @click="calculateWorkload">
          计算工作量
        </el-button>
        <el-button :disabled="!results.length" @click="exportResults">
          导出工作量
        </el-button>
      </div>
    </section>

    <section class="metric-grid">
      <div class="soft-card stat-card">
        <div class="metric-label">当前批次未匹配</div>
        <div class="metric-value">{{ currentBatch?.unresolved_count ?? 0 }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">结果教师数</div>
        <div class="metric-value">{{ results.length }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">学期总工作量</div>
        <div class="metric-value">{{ totalWorkload }}</div>
      </div>
    </section>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="课表导入与修正" name="timetable">
        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>导入课表</h3>
              <p>导入后自动映射教师、班级、学科和课程类型，未匹配条目进入待修正列表。</p>
            </div>
          </div>
          <div class="action-row">
            <input
              ref="timetableFileInputRef"
              class="file-input"
              type="file"
              accept=".xlsx,.xls"
              @change="handleTimetableFileChange"
            />
            <el-input
              v-model="importRemark"
              placeholder="导入备注，可选"
              maxlength="120"
              style="max-width: 280px"
            />
            <el-button
              type="primary"
              :loading="importing"
              :disabled="!selectedTimetableFile || !selectedSemesterId"
              @click="importTimetable"
            >
              上传课表
            </el-button>
          </div>
          <div v-if="selectedTimetableFile" class="hint-text">
            当前文件：{{ selectedTimetableFile.name }}
          </div>
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>导入批次</h3>
              <p>支持多份课表批次管理，默认取当前学期最新有效批次参与计算。</p>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="timetableBatches" stripe>
              <el-table-column label="导入时间" min-width="170">
                <template #default="{ row }">
                  {{ row.import_time }}
                </template>
              </el-table-column>
              <el-table-column label="文件名" prop="source_filename" min-width="180" />
              <el-table-column label="状态" width="170">
                <template #default="{ row }">
                  <el-tag :type="batchTagType(row.status)">
                    {{ row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="总条数" prop="entry_count" width="90" />
              <el-table-column label="未匹配" prop="unresolved_count" width="90" />
              <el-table-column label="备注" prop="remark" min-width="140" />
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="selectBatch(row.id)">查看条目</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>课表条目</h3>
              <p>未匹配条目修正后会重新判断是否可参与课时统计。</p>
            </div>
            <div class="action-row">
              <el-switch v-model="unresolvedOnly" />
              <span class="hint-text">仅看未匹配</span>
            </div>
          </div>
          <el-empty v-if="!selectedBatchId" description="请先选择一个课表批次" />
          <div v-else class="table-shell">
            <el-table :data="timetableEntries" stripe>
              <el-table-column label="星期/节次" width="110">
                <template #default="{ row }">
                  周{{ row.weekday }} / 第{{ row.period_no }}节
                </template>
              </el-table-column>
              <el-table-column label="教师" min-width="120">
                <template #default="{ row }">
                  {{ row.teacher_name ?? row.raw_teacher_name ?? "-" }}
                </template>
              </el-table-column>
              <el-table-column label="班级" min-width="100">
                <template #default="{ row }">
                  {{ row.class_name ?? row.raw_class_name ?? "-" }}
                </template>
              </el-table-column>
              <el-table-column label="学科" min-width="100">
                <template #default="{ row }">
                  {{ row.subject_name ?? row.raw_subject_name ?? "-" }}
                </template>
              </el-table-column>
              <el-table-column label="课程类型" min-width="110">
                <template #default="{ row }">
                  {{ formatCourseTypeLabel(row.course_type, row.raw_course_type) }}
                </template>
              </el-table-column>
              <el-table-column label="周次规则" min-width="120">
                <template #default="{ row }">
                  {{ formatWeekRule(row) }}
                </template>
              </el-table-column>
              <el-table-column label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.mapping_status === 'matched' ? 'success' : 'warning'">
                    {{ row.mapping_status === "matched" ? "已匹配" : "待修正" }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openEntryDialog(row)">修正</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="规则与附加项" name="rules">
        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>规则版本</h3>
              <p>规则版本计算后会锁定，不允许原地修改，避免历史结果被后续调整覆盖。</p>
            </div>
            <div class="action-row">
              <el-button type="primary" @click="openRuleVersionDialog">新建规则版本</el-button>
              <el-button :disabled="!selectedRuleVersionId" :loading="savingRuleItems" @click="saveRuleItems">
                保存规则项
              </el-button>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="ruleVersions" stripe>
            <el-table-column label="名称" min-width="180">
              <template #default="{ row }">
                <span class="row-link" @click="selectedRuleVersionId = row.id">
                  {{ row.name }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="适用学期" min-width="140">
              <template #default="{ row }">
                {{ row.semester_name ?? "通用规则" }}
              </template>
            </el-table-column>
            <el-table-column label="默认" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.is_default" type="success">默认</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" prop="status" width="100" />
            <el-table-column label="备注" prop="note" min-width="150" />
            </el-table>
          </div>

          <div class="section-head sub-head">
            <div>
              <h3>规则项</h3>
              <p>覆盖学科、年级、班型、课程类型、班额和班主任附加量。</p>
            </div>
            <el-button :disabled="!selectedRuleVersionId" @click="addRuleItem">新增规则项</el-button>
          </div>
          <el-empty v-if="!selectedRuleVersionId" description="请选择一个规则版本" />
          <div v-else class="table-shell">
            <el-table :data="ruleItems" stripe>
            <el-table-column label="维度" width="140">
              <template #default="{ row }">
                <el-select v-model="row.dimension_type">
                  <el-option
                    v-for="option in dimensionOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="匹配值" min-width="160">
              <template #default="{ row }">
                <el-input v-model="row.match_key" placeholder="如 math / 高二 / key / true" />
              </template>
            </el-table-column>
            <el-table-column label="系数" width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.coefficient" :precision="2" :step="0.05" controls-position="right" />
              </template>
            </el-table-column>
            <el-table-column label="固定量" width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.fixed_value" :precision="2" :step="0.5" controls-position="right" />
              </template>
            </el-table-column>
            <el-table-column label="备注" min-width="180">
              <template #default="{ row }">
                <el-input v-model="row.note" placeholder="说明" />
              </template>
            </el-table-column>
            <el-table-column label="启用" width="90">
              <template #default="{ row }">
                <el-switch v-model="row.is_active" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90" fixed="right">
              <template #default="{ $index }">
                <el-button link type="danger" @click="removeRuleItem($index)">删除</el-button>
              </template>
            </el-table-column>
            </el-table>
          </div>
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>附加量化项</h3>
              <p>用于备课组长、公开课、竞赛辅导等手工补录量化项。</p>
            </div>
            <el-button type="primary" :loading="savingExtra" @click="createExtra">新增附加项</el-button>
          </div>
          <div class="filter-grid">
            <el-select v-model="extraForm.teacher_id" filterable placeholder="教师">
              <el-option
                v-for="teacher in teacherOptions"
                :key="teacher.id"
                :label="teacher.name"
                :value="teacher.id"
              />
            </el-select>
            <el-input v-model="extraForm.item_name" placeholder="项目名称" />
            <el-input-number v-model="extraForm.quantity" :precision="2" :step="0.5" controls-position="right" />
            <el-input-number v-model="extraForm.coefficient" :precision="2" :step="0.5" controls-position="right" />
            <el-input-number v-model="extraForm.amount" :precision="2" :step="0.5" controls-position="right" />
            <el-input v-model="extraForm.note" placeholder="备注" />
          </div>
          <div class="hint-text">
            如填写“固定量”，系统优先使用固定量；否则按数量 × 系数计算。
          </div>
          <div class="table-shell table-gap">
            <el-table :data="extras" stripe>
              <el-table-column label="教师" prop="teacher_name" min-width="120" />
              <el-table-column label="项目" prop="item_name" min-width="140" />
              <el-table-column label="数量" prop="quantity" width="90" />
              <el-table-column label="系数" prop="coefficient" width="90" />
              <el-table-column label="固定量" prop="amount" width="90" />
              <el-table-column label="备注" prop="note" min-width="150" />
            </el-table>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="工作量结果" name="results">
        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>结果汇总</h3>
              <p>展示周课时、月度课时、学期课时和学期工作量，并保留可追溯计算明细。</p>
            </div>
          </div>
          <el-empty v-if="!results.length" description="当前筛选条件下暂无工作量结果" />
          <div v-else class="table-shell">
            <el-table :data="results" stripe>
              <el-table-column label="教师" prop="teacher_name" min-width="120" />
              <el-table-column label="周课时" prop="weekly_hours" width="90" />
              <el-table-column label="学期课时" prop="semester_hours" width="100" />
              <el-table-column label="学期工作量" prop="semester_workload" width="110" />
              <el-table-column label="月度课时" min-width="200">
                <template #default="{ row }">
                  {{ formatMonthlyHours(row.monthly_hours_json) }}
                </template>
              </el-table-column>
              <el-table-column label="计算时间" prop="calculated_at" min-width="170" />
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openResultDrawer(row)">查看明细</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="entryDialogVisible"
      title="修正课表条目"
      width="560px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleEntryDialogClosed"
    >
      <div class="filter-grid">
        <el-select v-model="entryForm.teacher_id" filterable clearable placeholder="教师">
          <el-option
            v-for="teacher in teacherOptions"
            :key="teacher.id"
            :label="teacher.name"
            :value="teacher.id"
          />
        </el-select>
        <el-select v-model="entryForm.class_id" filterable clearable placeholder="班级">
          <el-option
            v-for="schoolClass in referenceStore.classes"
            :key="schoolClass.id"
            :label="schoolClass.name"
            :value="schoolClass.id"
          />
        </el-select>
        <el-select v-model="entryForm.subject_id" filterable clearable placeholder="学科">
          <el-option
            v-for="subject in referenceStore.subjects"
            :key="subject.id"
            :label="subject.name"
            :value="subject.id"
          />
        </el-select>
        <el-select v-model="entryForm.course_type" clearable placeholder="课程类型">
          <el-option
            v-for="item in courseTypeOptions"
            :key="item.code"
            :label="item.name"
            :value="item.code"
          />
        </el-select>
        <el-input v-model="entryForm.note" placeholder="备注" />
        <el-switch v-model="entryForm.is_active" inline-prompt active-text="启用" inactive-text="停用" />
      </div>
      <template #footer>
        <el-button @click="entryDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingEntry" @click="saveEntry">保存修正</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="ruleDialogVisible"
      title="新建规则版本"
      width="520px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleRuleDialogClosed"
    >
      <div class="filter-grid">
        <el-input v-model="newRuleForm.name" placeholder="规则名称" />
        <el-select v-model="newRuleForm.semester_id" clearable filterable placeholder="适用学期，可不选">
          <el-option
            v-for="semester in semesterOptions"
            :key="semester.id"
            :label="formatSemesterLabel(semester)"
            :value="semester.id"
          />
        </el-select>
        <el-select v-model="newRuleForm.status" placeholder="状态">
          <el-option label="active" value="active" />
          <el-option label="draft" value="draft" />
        </el-select>
        <el-switch v-model="newRuleForm.is_default" inline-prompt active-text="默认" inactive-text="普通" />
        <el-input v-model="newRuleForm.note" placeholder="备注" />
        <el-switch v-model="newRuleForm.is_active" inline-prompt active-text="启用" inactive-text="停用" />
      </div>
      <template #footer>
        <el-button @click="ruleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creatingRuleVersion" @click="createRuleVersion">
          创建
        </el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="resultDrawerVisible" title="工作量明细" size="68%">
      <template v-if="activeResult">
        <section class="metric-grid drawer-grid">
          <div class="soft-card stat-card">
            <div class="metric-label">教师</div>
            <div class="metric-value">{{ activeResult.teacher_name }}</div>
          </div>
          <div class="soft-card stat-card">
            <div class="metric-label">周课时</div>
            <div class="metric-value">{{ activeResult.weekly_hours }}</div>
          </div>
          <div class="soft-card stat-card">
            <div class="metric-label">班主任附加量</div>
            <div class="metric-value">{{ activeResult.snapshot_json?.head_teacher_bonus ?? 0 }}</div>
          </div>
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>课时明细</h3>
              <p>按课表条目拆分后的工作量贡献。</p>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="activeResult.snapshot_json?.details ?? []" stripe>
              <el-table-column label="星期/节次" width="120">
                <template #default="{ row }">
                  周{{ row.weekday }} / 第{{ row.period_no }}节
                </template>
              </el-table-column>
              <el-table-column label="班级" prop="class_name" min-width="120" />
              <el-table-column label="学科" prop="subject_name" min-width="120" />
              <el-table-column label="课程类型" min-width="120">
                <template #default="{ row }">
                  {{ formatCourseTypeLabel(row.course_type, row.course_type) }}
                </template>
              </el-table-column>
              <el-table-column label="有效周数" prop="active_week_count" width="100" />
              <el-table-column label="综合系数" prop="coefficient" width="100" />
              <el-table-column label="贡献值" prop="semester_contribution" width="100" />
              <el-table-column label="系数拆解" min-width="260">
                <template #default="{ row }">
                  {{ formatBreakdown(row.coefficient_breakdown) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>附加项</h3>
              <p>手工补录的额外量化记录。</p>
            </div>
          </div>
          <el-empty v-if="!(activeResult.snapshot_json?.extras ?? []).length" description="无附加项" />
          <div v-else class="table-shell">
            <el-table :data="activeResult.snapshot_json?.extras ?? []" stripe>
              <el-table-column label="项目" prop="item_name" min-width="160" />
              <el-table-column label="数量" prop="quantity" width="90" />
              <el-table-column label="系数" prop="coefficient" width="90" />
              <el-table-column label="量化值" prop="amount" width="100" />
            </el-table>
          </div>
        </section>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import ElMessageBox from "element-plus/es/components/message-box/index";

import { apiRequest, openFile, uploadFile } from "../api/client";
import { type OptionItem, useReferenceStore } from "../stores/reference";

interface TeacherOption {
  id: number;
  name: string;
}

interface TimetableBatchItem {
  id: number;
  semester_id: number;
  semester_name?: string | null;
  source_filename?: string | null;
  import_time: string;
  status: string;
  remark?: string | null;
  entry_count: number;
  unresolved_count: number;
  is_active: boolean;
}

interface TimetableEntryItem {
  id: number;
  batch_id: number;
  semester_id: number;
  weekday: number;
  period_no: number;
  teacher_id?: number | null;
  teacher_name?: string | null;
  class_id?: number | null;
  class_name?: string | null;
  subject_id?: number | null;
  subject_name?: string | null;
  course_type?: string | null;
  week_rule: string;
  week_list_json?: number[] | null;
  note?: string | null;
  mapping_status: string;
  raw_teacher_name?: string | null;
  raw_class_name?: string | null;
  raw_subject_name?: string | null;
  raw_course_type?: string | null;
  is_active: boolean;
}

interface RuleVersionItem {
  id: number;
  name: string;
  semester_id?: number | null;
  semester_name?: string | null;
  is_default: boolean;
  status: string;
  note?: string | null;
  is_active: boolean;
}

interface RuleItem {
  id?: number;
  dimension_type: string;
  match_key: string;
  coefficient?: number | null;
  fixed_value?: number | null;
  note?: string | null;
  is_active: boolean;
}

interface ExtraItem {
  id: number;
  teacher_id: number;
  teacher_name?: string | null;
  semester_id: number;
  item_name: string;
  quantity: number;
  coefficient: number;
  amount?: number | null;
  note?: string | null;
  is_active: boolean;
}

interface ResultDetailRow {
  weekday: number;
  period_no: number;
  class_name?: string | null;
  subject_name?: string | null;
  course_type?: string | null;
  active_week_count: number;
  coefficient: number;
  coefficient_breakdown?: Record<string, number>;
  semester_contribution: number;
}

interface ResultExtraRow {
  item_name: string;
  quantity: number;
  coefficient: number;
  amount: number;
}

interface WorkloadResultItem {
  id: number;
  teacher_id: number;
  teacher_name?: string | null;
  semester_id: number;
  semester_name?: string | null;
  rule_version_id: number;
  rule_version_name?: string | null;
  weekly_hours: number;
  monthly_hours_json?: Record<string, number> | null;
  semester_hours: number;
  semester_workload: number;
  snapshot_json?: {
    batch_id?: number;
    batch_filename?: string | null;
    entry_count?: number;
    head_teacher_bonus?: number;
    details?: ResultDetailRow[];
    extras?: ResultExtraRow[];
  } | null;
  calculated_at: string;
  is_active: boolean;
}

interface CreateRuleForm {
  name: string;
  semester_id?: number | null;
  is_default: boolean;
  status: string;
  note: string;
  is_active: boolean;
}

interface EntryFormState {
  id?: number;
  teacher_id?: number | null;
  class_id?: number | null;
  subject_id?: number | null;
  course_type?: string | null;
  note?: string | null;
  is_active: boolean;
}

interface ExtraFormState {
  teacher_id?: number;
  item_name: string;
  quantity: number;
  coefficient: number;
  amount?: number | null;
  note: string;
}

const referenceStore = useReferenceStore();

const activeTab = ref("timetable");
const teacherOptions = ref<TeacherOption[]>([]);
const ruleVersions = ref<RuleVersionItem[]>([]);
const ruleItems = ref<RuleItem[]>([]);
const timetableBatches = ref<TimetableBatchItem[]>([]);
const timetableEntries = ref<TimetableEntryItem[]>([]);
const extras = ref<ExtraItem[]>([]);
const results = ref<WorkloadResultItem[]>([]);

const selectedSemesterId = ref<number | null>(null);
const selectedRuleVersionId = ref<number | null>(null);
const selectedBatchId = ref<number | null>(null);
const unresolvedOnly = ref(false);

const selectedTimetableFile = ref<File | null>(null);
const timetableFileInputRef = ref<HTMLInputElement | null>(null);
const importRemark = ref("");

const importing = ref(false);
const savingEntry = ref(false);
const creatingRuleVersion = ref(false);
const savingRuleItems = ref(false);
const savingExtra = ref(false);
const calculating = ref(false);

const entryDialogVisible = ref(false);
const ruleDialogVisible = ref(false);
const resultDrawerVisible = ref(false);

const entryForm = ref<EntryFormState>({
  teacher_id: undefined,
  class_id: undefined,
  subject_id: undefined,
  course_type: undefined,
  note: "",
  is_active: true,
});

const newRuleForm = ref<CreateRuleForm>({
  name: "",
  semester_id: null,
  is_default: false,
  status: "active",
  note: "",
  is_active: true,
});

const extraForm = ref<ExtraFormState>({
  teacher_id: undefined,
  item_name: "",
  quantity: 0,
  coefficient: 1,
  amount: null,
  note: "",
});

const activeResult = ref<WorkloadResultItem | null>(null);

const semesterOptions = computed(() => referenceStore.semesters);
const courseTypeOptions = computed(() => referenceStore.dicts.course_type ?? []);
const currentBatch = computed(() => timetableBatches.value.find((item) => item.id === selectedBatchId.value) ?? null);
const totalWorkload = computed(() =>
  results.value.reduce((sum, item) => sum + item.semester_workload, 0).toFixed(2),
);
const currentSemesterLabel = computed(() =>
  semesterOptions.value.find((item) => item.id === selectedSemesterId.value)?.name
    ? formatSemesterLabel(semesterOptions.value.find((item) => item.id === selectedSemesterId.value)!)
    : "未选择学期",
);
const currentRuleLabel = computed(() =>
  ruleVersions.value.find((item) => item.id === selectedRuleVersionId.value)?.name ?? "未选择规则",
);
const overviewCards = computed(() => [
  {
    label: "课表批次",
    value: timetableBatches.value.length,
    help: "当前学期可用的课表导入批次数量。",
    tone: "tone-blue",
  },
  {
    label: "规则项",
    value: ruleItems.value.length,
    help: "当前规则版本下的有效规则项数量。",
    tone: "tone-amber",
  },
  {
    label: "附加项",
    value: extras.value.length,
    help: "当前学期已补录的附加量化项数量。",
    tone: "tone-slate",
  },
]);

const dimensionOptions = [
  { value: "subject", label: "学科" },
  { value: "grade", label: "年级" },
  { value: "class_type", label: "班型" },
  { value: "course_type", label: "课程类型" },
  { value: "class_size", label: "班额" },
  { value: "head_teacher", label: "班主任附加量" },
];

function formatSemesterLabel(item: OptionItem): string {
  return item.academic_year_name ? `${item.academic_year_name} ${item.name}` : item.name;
}

function batchLabel(item: TimetableBatchItem): string {
  return `${item.import_time} | ${item.source_filename ?? "未命名"} | 未匹配 ${item.unresolved_count}`;
}

function ruleLabel(item: RuleVersionItem): string {
  const suffix = item.is_default ? "默认" : item.status;
  return `${item.name} | ${item.semester_name ?? "通用"} | ${suffix}`;
}

function batchTagType(status: string): "success" | "warning" | "info" {
  if (status === "completed") return "success";
  if (status === "completed_with_unresolved") return "warning";
  return "info";
}

function formatWeekRule(row: TimetableEntryItem): string {
  if (row.week_rule === "all") return "全周";
  if (row.week_rule === "odd") return "单周";
  if (row.week_rule === "even") return "双周";
  if (row.week_rule === "custom" && row.week_list_json?.length) {
    return `指定周 ${row.week_list_json.join(",")}`;
  }
  return row.week_rule;
}

function formatCourseTypeLabel(code?: string | null, fallback?: string | null): string {
  if (!code) return fallback ?? "-";
  const match = courseTypeOptions.value.find((item) => item.code === code);
  return match ? match.name : (fallback ?? code);
}

function formatMonthlyHours(value?: Record<string, number> | null): string {
  if (!value) return "-";
  const items = Object.entries(value);
  if (!items.length) return "-";
  return items.map(([month, hours]) => `${month}: ${hours}`).join(" / ");
}

function formatBreakdown(value?: Record<string, number>): string {
  if (!value) return "-";
  return Object.entries(value)
    .map(([key, score]) => `${key}=${score}`)
    .join(" × ");
}

function resetExtraForm(): void {
  extraForm.value = {
    teacher_id: undefined,
    item_name: "",
    quantity: 0,
    coefficient: 1,
    amount: null,
    note: "",
  };
}

async function loadTeachers(): Promise<void> {
  const payload = await apiRequest<{ items: TeacherOption[] }>("/api/teachers?page=1&page_size=200");
  teacherOptions.value = payload.items;
}

async function loadRuleVersions(): Promise<void> {
  const payload = await apiRequest<RuleVersionItem[]>("/api/workload/rules");
  ruleVersions.value = payload;
  if (!payload.length) {
    selectedRuleVersionId.value = null;
    return;
  }
  const exists = payload.some((item) => item.id === selectedRuleVersionId.value);
  if (exists) return;
  selectedRuleVersionId.value = payload.find((item) => item.is_default)?.id ?? payload[0].id;
}

async function loadRuleItems(): Promise<void> {
  if (!selectedRuleVersionId.value) {
    ruleItems.value = [];
    return;
  }
  ruleItems.value = await apiRequest<RuleItem[]>(`/api/workload/rules/${selectedRuleVersionId.value}/items`);
}

async function loadBatches(): Promise<void> {
  if (!selectedSemesterId.value) {
    timetableBatches.value = [];
    selectedBatchId.value = null;
    return;
  }
  const payload = await apiRequest<TimetableBatchItem[]>(
    `/api/timetable/batches?semester_id=${selectedSemesterId.value}`,
  );
  timetableBatches.value = payload;
  if (!payload.length) {
    selectedBatchId.value = null;
    timetableEntries.value = [];
    return;
  }
  const exists = payload.some((item) => item.id === selectedBatchId.value);
  if (!exists) {
    selectedBatchId.value = payload[0].id;
  }
}

async function loadEntries(): Promise<void> {
  if (!selectedBatchId.value) {
    timetableEntries.value = [];
    return;
  }
  timetableEntries.value = await apiRequest<TimetableEntryItem[]>(
    `/api/timetable/batches/${selectedBatchId.value}/entries?unresolved_only=${unresolvedOnly.value}`,
  );
}

async function loadExtras(): Promise<void> {
  if (!selectedSemesterId.value) {
    extras.value = [];
    return;
  }
  extras.value = await apiRequest<ExtraItem[]>(`/api/workload/extras?semester_id=${selectedSemesterId.value}`);
}

async function loadResults(): Promise<void> {
  if (!selectedSemesterId.value || !selectedRuleVersionId.value) {
    results.value = [];
    return;
  }
  results.value = await apiRequest<WorkloadResultItem[]>(
    `/api/workload/results?semester_id=${selectedSemesterId.value}&rule_version_id=${selectedRuleVersionId.value}`,
  );
}

async function refreshAll(): Promise<void> {
  try {
    await loadTeachers();
    await loadRuleVersions();
    await Promise.all([loadBatches(), loadExtras(), loadResults()]);
    await loadEntries();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function handleTimetableFileChange(event: Event): void {
  const input = event.target as HTMLInputElement;
  selectedTimetableFile.value = input.files?.[0] ?? null;
}

async function importTimetable(): Promise<void> {
  if (!selectedSemesterId.value || !selectedTimetableFile.value) return;
  try {
    importing.value = true;
    const payload = await uploadFile<{ batch_id: number; unresolved_rows: number; message: string }>(
      "/api/timetable/import",
      selectedTimetableFile.value,
      {
        semester_id: String(selectedSemesterId.value),
        remark: importRemark.value,
      },
    );
    ElMessage.success(payload.message);
    selectedBatchId.value = payload.batch_id;
    selectedTimetableFile.value = null;
    if (timetableFileInputRef.value) {
      timetableFileInputRef.value.value = "";
    }
    importRemark.value = "";
    await Promise.all([loadBatches(), loadResults()]);
    await loadEntries();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    importing.value = false;
  }
}

function selectBatch(batchId: number): void {
  selectedBatchId.value = batchId;
  activeTab.value = "timetable";
}

function openEntryDialog(row: TimetableEntryItem): void {
  entryForm.value = {
    id: row.id,
    teacher_id: row.teacher_id ?? undefined,
    class_id: row.class_id ?? undefined,
    subject_id: row.subject_id ?? undefined,
    course_type: row.course_type ?? undefined,
    note: row.note ?? "",
    is_active: row.is_active,
  };
  entryDialogVisible.value = true;
}

function handleEntryDialogClosed(): void {
  entryForm.value = {
    teacher_id: undefined,
    class_id: undefined,
    subject_id: undefined,
    course_type: undefined,
    note: "",
    is_active: true,
  };
}

async function saveEntry(): Promise<void> {
  if (!entryForm.value.id) return;
  try {
    savingEntry.value = true;
    await apiRequest<TimetableEntryItem>(`/api/timetable/entries/${entryForm.value.id}`, {
      method: "PUT",
      body: JSON.stringify({
        teacher_id: entryForm.value.teacher_id ?? null,
        class_id: entryForm.value.class_id ?? null,
        subject_id: entryForm.value.subject_id ?? null,
        course_type: entryForm.value.course_type ?? null,
        note: entryForm.value.note ?? "",
        is_active: entryForm.value.is_active,
      }),
    });
    entryDialogVisible.value = false;
    ElMessage.success("课表条目已更新");
    await Promise.all([loadBatches(), loadEntries()]);
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingEntry.value = false;
  }
}

function addRuleItem(): void {
  ruleItems.value.push({
    dimension_type: "subject",
    match_key: "",
    coefficient: 1,
    fixed_value: null,
    note: "",
    is_active: true,
  });
}

function removeRuleItem(index: number): void {
  ruleItems.value.splice(index, 1);
}

async function saveRuleItems(): Promise<void> {
  if (!selectedRuleVersionId.value) return;
  try {
    savingRuleItems.value = true;
    const payload = ruleItems.value.map((item) => ({
      dimension_type: item.dimension_type,
      match_key: item.match_key.trim(),
      coefficient: item.coefficient ?? null,
      fixed_value: item.fixed_value ?? null,
      note: item.note?.trim() ?? null,
      is_active: item.is_active,
    }));
    if (payload.some((item) => !item.dimension_type || !item.match_key)) {
      throw new Error("规则项的维度和匹配值不能为空");
    }
    ruleItems.value = await apiRequest<RuleItem[]>(
      `/api/workload/rules/${selectedRuleVersionId.value}/items`,
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
    );
    ElMessage.success("规则项已保存");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingRuleItems.value = false;
  }
}

async function createRuleVersion(): Promise<void> {
  if (!newRuleForm.value.name.trim()) {
    ElMessage.warning("请填写规则名称");
    return;
  }
  try {
    creatingRuleVersion.value = true;
    const payload = await apiRequest<RuleVersionItem>("/api/workload/rules", {
      method: "POST",
      body: JSON.stringify({
        name: newRuleForm.value.name.trim(),
        semester_id: newRuleForm.value.semester_id ?? null,
        is_default: newRuleForm.value.is_default,
        status: newRuleForm.value.status,
        note: newRuleForm.value.note.trim() || null,
        is_active: newRuleForm.value.is_active,
      }),
    });
    ruleDialogVisible.value = false;
    resetNewRuleForm();
    await loadRuleVersions();
    selectedRuleVersionId.value = payload.id;
    ElMessage.success("规则版本已创建");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    creatingRuleVersion.value = false;
  }
}

function resetNewRuleForm(): void {
  newRuleForm.value = {
    name: "",
    semester_id: selectedSemesterId.value,
    is_default: false,
    status: "active",
    note: "",
    is_active: true,
  };
}

function openRuleVersionDialog(): void {
  resetNewRuleForm();
  ruleDialogVisible.value = true;
}

function handleRuleDialogClosed(): void {
  resetNewRuleForm();
}

async function createExtra(): Promise<void> {
  if (!selectedSemesterId.value) {
    ElMessage.warning("请先选择学期");
    return;
  }
  if (!extraForm.value.teacher_id || !extraForm.value.item_name.trim()) {
    ElMessage.warning("请填写教师和项目名称");
    return;
  }
  try {
    savingExtra.value = true;
    await apiRequest<ExtraItem>("/api/workload/extras", {
      method: "POST",
      body: JSON.stringify({
        teacher_id: extraForm.value.teacher_id,
        semester_id: selectedSemesterId.value,
        item_name: extraForm.value.item_name.trim(),
        quantity: extraForm.value.quantity,
        coefficient: extraForm.value.coefficient,
        amount: extraForm.value.amount ?? null,
        note: extraForm.value.note.trim() || null,
        is_active: true,
      }),
    });
    resetExtraForm();
    await Promise.all([loadExtras(), loadResults()]);
    ElMessage.success("附加项已新增");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingExtra.value = false;
  }
}

async function calculateWorkload(): Promise<void> {
  if (!selectedSemesterId.value || !selectedRuleVersionId.value) {
    ElMessage.warning("请先选择学期和规则版本");
    return;
  }
  try {
    if (currentBatch.value?.unresolved_count) {
      await ElMessageBox.confirm(
        "当前批次仍有未匹配条目，未修正条目不会参与课时统计。是否继续计算？",
        "继续计算",
        { type: "warning" },
      );
    }
    calculating.value = true;
    const payload = await apiRequest<{ message: string; result_count: number }>("/api/workload/calculate", {
      method: "POST",
      body: JSON.stringify({
        semester_id: selectedSemesterId.value,
        rule_version_id: selectedRuleVersionId.value,
        batch_id: selectedBatchId.value,
      }),
    });
    await loadResults();
    activeTab.value = "results";
    ElMessage.success(`${payload.message}，共生成 ${payload.result_count} 位教师结果`);
  } catch (error) {
    if (error === "cancel" || error === "close") return;
    ElMessage.error((error as Error).message);
  } finally {
    calculating.value = false;
  }
}

function downloadTimetableTemplate(): void {
  openFile(
    `/api/system/files?path=${encodeURIComponent("data/templates/timetable_import_template.xlsx")}`,
  );
}

function exportResults(): void {
  if (!selectedSemesterId.value || !selectedRuleVersionId.value) return;
  openFile(
    `/api/workload/results/export?semester_id=${selectedSemesterId.value}&rule_version_id=${selectedRuleVersionId.value}`,
  );
}

function openResultDrawer(row: WorkloadResultItem): void {
  activeResult.value = row;
  resultDrawerVisible.value = true;
}

watch(selectedBatchId, async () => {
  try {
    await loadEntries();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
});

watch(unresolvedOnly, async () => {
  try {
    await loadEntries();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
});

watch(selectedSemesterId, async () => {
  try {
    await Promise.all([loadBatches(), loadExtras(), loadResults()]);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
});

watch(selectedRuleVersionId, async () => {
  try {
    await Promise.all([loadRuleItems(), loadResults()]);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
});

onMounted(async () => {
  try {
    await referenceStore.loadAll();
    const currentSemester = semesterOptions.value.find((item) => item.is_current) ?? semesterOptions.value[0];
    selectedSemesterId.value = currentSemester?.id ?? null;
    await refreshAll();
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
});
</script>

<style scoped>
.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) repeat(3, minmax(0, 0.75fr));
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

.toolbar-row {
  margin-top: 14px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-head h3 {
  margin: 0;
  font-size: 18px;
}

.section-head p {
  margin: 6px 0 0;
  color: #60748a;
  line-height: 1.6;
}

.sub-head {
  margin-top: 22px;
}

.stat-card {
  padding: 18px 20px;
}

.metric-label {
  color: #60748a;
  font-size: 13px;
}

.metric-value {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 700;
  color: #244560;
}

.hint-text {
  color: #60748a;
  font-size: 13px;
}

.file-input {
  min-width: 260px;
}

.row-link {
  color: #2d5883;
  cursor: pointer;
}

.drawer-grid {
  margin-bottom: 18px;
}

@media (max-width: 1180px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .section-head {
    flex-direction: column;
  }
}
</style>
