<template>
  <section class="soft-card panel-block" v-loading="loadingResults">
    <div class="section-head">
      <div>
        <h3>结果汇总</h3>
        <p>展示周课时、月度课时、学期课时和学期工作量，并保留可追溯计算明细。</p>
      </div>
      <el-button :disabled="exportDisabled" @click="emit('export-results')">导出工作量</el-button>
    </div>
    <el-alert
      v-if="resultsError"
      class="panel-alert"
      type="warning"
      show-icon
      :closable="false"
      :title="resultsError"
    />
    <div v-if="!resultsError && results.length" class="result-review-grid">
      <article v-for="item in resultReviewCards" :key="item.label" class="result-review-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </div>
    <div class="table-shell">
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
            <el-button
              link
              type="primary"
              :disabled="rowActionsDisabled"
              @click="emit('open-result-drawer', row)"
            >
              查看明细
            </el-button>
            </template>
          </el-table-column>
        <template #empty>
          <el-empty :description="resultsEmptyDescription" />
        </template>
      </el-table>
    </div>

    <el-drawer v-model="drawerVisibleModel" title="工作量明细" size="68%">
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
          <el-empty
            v-if="!(activeResult.snapshot_json?.details ?? []).length"
            description="当前结果没有课时明细。请回到课表批次确认是否已成功匹配教师、班级和学科。"
          />
          <div class="table-shell">
            <el-table v-if="(activeResult.snapshot_json?.details ?? []).length" :data="activeResult.snapshot_json?.details ?? []" stripe>
              <el-table-column label="星期/节次" width="120">
                <template #default="{ row }">
                  周{{ row.weekday }} / 第{{ row.period_no }}节
                </template>
              </el-table-column>
              <el-table-column label="班级" prop="class_name" min-width="120" />
              <el-table-column label="学科" prop="subject_name" min-width="120" />
              <el-table-column label="课程类型" min-width="120">
                <template #default="{ row }">
                  {{ formatCourseTypeLabel(row.course_type, row.course_type, courseTypeOptions) }}
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
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { OptionItem } from "../../stores/reference";
import { formatBreakdown, formatCourseTypeLabel, formatMonthlyHours } from "./helpers";
import type { StatusCard, WorkloadResultItem } from "./types";

const props = defineProps<{
  results: WorkloadResultItem[];
  activeResult: WorkloadResultItem | null;
  drawerVisible: boolean;
  courseTypeOptions: OptionItem[];
  resultReviewCards: StatusCard[];
  loadingResults: boolean;
  resultsError: string;
  exportDisabled: boolean;
  rowActionsDisabled: boolean;
}>();

const emit = defineEmits<{
  "export-results": [];
  "open-result-drawer": [row: WorkloadResultItem];
  "update:drawerVisible": [value: boolean];
}>();

const drawerVisibleModel = computed({
  get: () => props.drawerVisible,
  set: (value: boolean) => emit("update:drawerVisible", value),
});

const resultsEmptyDescription = computed(() => {
  if (props.resultsError) return "工作量结果加载失败，请使用页面顶部重试入口重新加载。";
  return "当前还没有工作量结果。请先确认学期、规则版本和课表批次，再点击“计算工作量”。";
});
</script>

<style scoped>
.drawer-grid {
  margin-bottom: 18px;
}

.result-review-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.result-review-card {
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(123, 141, 158, 0.18);
  background: rgba(248, 251, 253, 0.86);
}

.result-review-card span {
  color: #6c8094;
  font-size: 13px;
}

.result-review-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3245;
  font-size: 24px;
}

.result-review-card p {
  margin: 6px 0 0;
  color: #61778b;
  line-height: 1.5;
  font-size: 13px;
}

.tone-green {
  box-shadow: inset 0 4px 0 rgba(69, 141, 105, 0.78);
}

.tone-amber {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.84);
}

.tone-blue {
  box-shadow: inset 0 4px 0 rgba(31, 108, 152, 0.78);
}

.tone-slate {
  box-shadow: inset 0 4px 0 rgba(92, 111, 129, 0.74);
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

.panel-alert {
  margin-bottom: 14px;
}
</style>
