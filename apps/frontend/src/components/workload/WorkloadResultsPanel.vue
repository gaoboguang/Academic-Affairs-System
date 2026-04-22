<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>结果汇总</h3>
        <p>展示周课时、月度课时、学期课时和学期工作量，并保留可追溯计算明细。</p>
      </div>
      <el-button :disabled="!results.length" @click="emit('export-results')">导出工作量</el-button>
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
            <el-button link type="primary" @click="emit('open-result-drawer', row)">查看明细</el-button>
          </template>
        </el-table-column>
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
import type { WorkloadResultItem } from "./types";

const props = defineProps<{
  results: WorkloadResultItem[];
  activeResult: WorkloadResultItem | null;
  drawerVisible: boolean;
  courseTypeOptions: OptionItem[];
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
</script>

<style scoped>
.drawer-grid {
  margin-bottom: 18px;
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
</style>
