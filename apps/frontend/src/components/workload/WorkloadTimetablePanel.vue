<template>
  <div class="page-shell">
    <section class="soft-card panel-block">
      <div class="section-head">
        <div>
          <h3>导入课表</h3>
          <p>导入后自动映射教师、班级、学科和课程类型，未匹配条目进入待修正列表。</p>
        </div>
      </div>
      <div class="action-row">
        <input
          :key="fileInputKey"
          class="file-input"
          type="file"
          accept=".xlsx,.xls"
          @change="emit('file-change', $event)"
        />
        <el-input v-model="importRemarkModel" placeholder="导入备注，可选" maxlength="120" style="max-width: 280px" />
        <el-button
          type="primary"
          :loading="importing"
          :disabled="!canImport"
          @click="emit('import-timetable')"
        >
          上传课表
        </el-button>
      </div>
      <div v-if="selectedTimetableFileName" class="hint-text">
        当前文件：{{ selectedTimetableFileName }}
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
                {{ formatBatchStatus(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="总条数" prop="entry_count" width="90" />
          <el-table-column label="未匹配" prop="unresolved_count" width="90" />
          <el-table-column label="备注" prop="remark" min-width="140" />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="emit('select-batch', row.id)">查看条目</el-button>
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
          <el-switch v-model="unresolvedOnlyModel" />
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
              {{ formatCourseTypeLabel(row.course_type, row.raw_course_type, courseTypeOptions) }}
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
              <el-button link type="primary" @click="emit('open-entry-dialog', row)">修正</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { OptionItem } from "../../stores/reference";
import { batchTagType, formatBatchStatus, formatCourseTypeLabel, formatWeekRule } from "./helpers";
import type { TimetableBatchItem, TimetableEntryItem } from "./types";

const props = defineProps<{
  fileInputKey: number;
  selectedTimetableFileName: string;
  importRemark: string;
  importing: boolean;
  canImport: boolean;
  timetableBatches: TimetableBatchItem[];
  selectedBatchId: number | null;
  unresolvedOnly: boolean;
  timetableEntries: TimetableEntryItem[];
  courseTypeOptions: OptionItem[];
}>();

const emit = defineEmits<{
  "update:importRemark": [value: string];
  "file-change": [event: Event];
  "import-timetable": [];
  "select-batch": [batchId: number];
  "update:unresolvedOnly": [value: boolean];
  "open-entry-dialog": [row: TimetableEntryItem];
}>();

const importRemarkModel = computed({
  get: () => props.importRemark,
  set: (value: string) => emit("update:importRemark", value),
});

const unresolvedOnlyModel = computed({
  get: () => props.unresolvedOnly,
  set: (value: boolean) => emit("update:unresolvedOnly", value),
});
</script>
