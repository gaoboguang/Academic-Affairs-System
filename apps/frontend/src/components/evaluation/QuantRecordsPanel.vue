<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>量化记录与汇总</h3>
        <p>按学期、教师查看量化明细和汇总，附件上传先于记录绑定。</p>
      </div>
      <div class="action-row">
        <el-button :loading="loadingQuantData" :disabled="controlsDisabled" @click="emit('reload')">刷新</el-button>
        <el-button type="primary" :disabled="createDisabled" @click="emit('open-create-quant-record')">新增量化记录</el-button>
      </div>
    </div>

    <el-alert
      v-if="quantDataError || teacherOptionsError"
      class="panel-alert"
      type="error"
      show-icon
      :closable="false"
      title="量化记录加载失败"
    >
      <template #default>
        <p v-if="quantDataError">{{ quantDataError }}</p>
        <p v-if="teacherOptionsError">{{ teacherOptionsError }}</p>
      </template>
    </el-alert>

    <div class="filter-grid">
      <el-select v-model="quantFilters.semester_id" filterable :disabled="controlsDisabled" placeholder="学期">
        <el-option
          v-for="item in semesters"
          :key="item.id"
          :label="semesterLabel(item)"
          :value="item.id"
        />
      </el-select>
      <el-select
        v-model="quantFilters.teacher_id"
        clearable
        filterable
        :loading="loadingTeacherOptions"
        :disabled="controlsDisabled || loadingTeacherOptions"
        placeholder="教师"
      >
        <el-option
          v-for="teacher in teacherOptions"
          :key="teacher.id"
          :label="teacher.name"
          :value="teacher.id"
        />
      </el-select>
      <el-select v-model="quantFilters.rule_version_id" clearable filterable :disabled="controlsDisabled" placeholder="规则版本">
        <el-option v-for="rule in ruleVersions" :key="rule.id" :label="rule.name" :value="rule.id" />
      </el-select>
    </div>

    <div class="action-row toolbar-row">
      <el-button type="primary" :loading="loadingQuantData" :disabled="controlsDisabled" @click="emit('reload')">查询</el-button>
      <el-button :disabled="controlsDisabled" @click="emit('reset-filters')">重置</el-button>
    </div>

    <div class="detail-grid-box">
      <div class="soft-card inner-card" v-loading="loadingQuantData">
        <h4>汇总</h4>
        <el-table :data="quantSummary" stripe>
          <el-table-column label="教师" prop="teacher_name" min-width="120" />
          <el-table-column label="总分" prop="total_score" width="90" />
          <el-table-column label="加分" prop="positive_score" width="90" />
          <el-table-column label="扣分" prop="negative_score" width="90" />
          <el-table-column label="记录数" prop="record_count" width="90" />
          <el-table-column label="班级" min-width="160">
            <template #default="{ row }">
              {{ (row.class_names ?? []).join(" / ") || "-" }}
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="quantDataError ? '量化汇总暂时加载失败。' : '当前筛选条件下暂无量化汇总。请先新增量化记录或调整学期、教师、规则版本。'" />
          </template>
        </el-table>
      </div>
      <div class="soft-card inner-card" v-loading="loadingQuantData">
        <h4>明细</h4>
        <el-table :data="quantRecords" stripe>
          <el-table-column label="月份" prop="record_month" width="90" />
          <el-table-column label="教师" prop="teacher_name" width="110" />
          <el-table-column label="班级" prop="class_name" width="100" />
          <el-table-column label="量化项" prop="item_name" min-width="160" />
          <el-table-column label="分值" prop="score" width="80" />
          <el-table-column label="附件" width="120">
            <template #default="{ row }">
              {{ row.attachments.length ? `${row.attachments.length} 个` : "-" }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :disabled="rowActionsDisabled" @click="emit('edit-quant-record', row)">编辑</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="quantDataError ? '量化明细暂时加载失败。' : '当前筛选条件下暂无量化明细。新增记录后会在这里显示附件和分值。'" />
          </template>
        </el-table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import type { OptionItem } from "../../stores/reference";
import { semesterLabel } from "./helpers";
import type { QuantFiltersState, QuantRecord, QuantSummary, RuleVersion, TeacherOption } from "./types";

defineProps<{
  quantFilters: QuantFiltersState;
  semesters: OptionItem[];
  teacherOptions: TeacherOption[];
  ruleVersions: RuleVersion[];
  quantSummary: QuantSummary[];
  quantRecords: QuantRecord[];
  loadingQuantData: boolean;
  quantDataError: string;
  loadingTeacherOptions: boolean;
  teacherOptionsError: string;
  controlsDisabled: boolean;
  createDisabled: boolean;
  rowActionsDisabled: boolean;
}>();

const emit = defineEmits<{
  reload: [];
  "open-create-quant-record": [];
  "reset-filters": [];
  "edit-quant-record": [record: QuantRecord];
}>();
</script>

<style scoped>
.toolbar-row {
  margin-bottom: 16px;
}

.panel-alert {
  margin-bottom: 14px;
}

.panel-alert p {
  margin: 0 0 4px;
  line-height: 1.5;
}

.detail-grid-box {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.inner-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(116, 133, 151, 0.14);
  background: rgba(248, 252, 255, 0.92);
}

.inner-card h4 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #22384b;
}

@media (max-width: 1080px) {
  .detail-grid-box {
    grid-template-columns: 1fr;
  }
}
</style>
