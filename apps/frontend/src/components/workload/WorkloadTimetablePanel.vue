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
          :disabled="controlsDisabled"
          @change="emit('file-change', $event)"
        />
        <el-input
          v-model="importRemarkModel"
          placeholder="导入备注，可选"
          maxlength="120"
          style="max-width: 280px"
          :disabled="controlsDisabled"
        />
        <el-button
          type="primary"
          :loading="importing"
          :disabled="importDisabled || !canImport"
          @click="emit('import-timetable')"
        >
          上传课表
        </el-button>
      </div>
      <div v-if="selectedTimetableFileName" class="hint-text">
        当前文件：{{ selectedTimetableFileName }}
      </div>
      <ImportFeedbackPanel :result="importResult" />
      <div v-if="reviewCards.length" class="review-grid">
        <article v-for="item in reviewCards" :key="item.label" class="review-card" :class="item.tone">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <p>{{ item.help }}</p>
        </article>
      </div>
    </section>

    <section class="soft-card panel-block" v-loading="loadingBatches">
      <div class="section-head">
        <div>
          <h3>导入批次</h3>
          <p>支持多份课表批次管理，默认取当前学期最新有效批次参与计算。</p>
        </div>
      </div>
      <el-alert
        v-if="batchesError"
        class="panel-alert"
        type="warning"
        show-icon
        :closable="false"
        :title="batchesError"
      />
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
              <el-button
                link
                type="primary"
                :disabled="rowActionsDisabled"
                @click="emit('select-batch', row.id)"
              >
                查看条目
              </el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="batchesEmptyDescription" />
          </template>
        </el-table>
      </div>
    </section>

    <section class="soft-card panel-block" v-loading="loadingEntries">
      <div class="section-head">
        <div>
          <h3>课表条目</h3>
          <p>未匹配条目修正后会重新判断是否可参与课时统计。</p>
        </div>
        <div class="action-row">
          <el-radio-group
            v-model="viewModeModel"
            size="small"
            :disabled="controlsDisabled || loadingEntries"
          >
            <el-radio-button label="raw">原始顺序</el-radio-button>
            <el-radio-button label="teacher">按教师</el-radio-button>
            <el-radio-button label="class">按班级</el-radio-button>
          </el-radio-group>
          <el-switch
            v-model="unresolvedOnlyModel"
            :disabled="controlsDisabled || loadingEntries || !selectedBatchId"
          />
          <span class="hint-text">仅看未匹配</span>
        </div>
      </div>
      <el-alert
        v-if="entriesError"
        class="panel-alert"
        type="warning"
        show-icon
        :closable="false"
        :title="entriesError"
      />
      <div class="table-shell">
        <el-table :data="displayedEntries" stripe>
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
              <el-button
                link
                type="primary"
                :disabled="rowActionsDisabled"
                @click="emit('open-entry-dialog', row)"
              >
                修正
              </el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty :description="entriesEmptyDescription" />
          </template>
        </el-table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import ImportFeedbackPanel from "../common/ImportFeedbackPanel.vue";
import type { OptionItem } from "../../stores/reference";
import type { ImportFeedbackResult } from "../../utils/importFeedback";
import { batchTagType, formatBatchStatus, formatCourseTypeLabel, formatWeekRule } from "./helpers";
import type { StatusCard, TimetableBatchItem, TimetableEntryItem } from "./types";

const props = defineProps<{
  fileInputKey: number;
  selectedTimetableFileName: string;
  importResult: (ImportFeedbackResult & { batch_id: number; unresolved_rows: number }) | null;
  importRemark: string;
  importing: boolean;
  canImport: boolean;
  controlsDisabled: boolean;
  importDisabled: boolean;
  rowActionsDisabled: boolean;
  timetableBatches: TimetableBatchItem[];
  selectedBatchId: number | null;
  unresolvedOnly: boolean;
  viewMode: "raw" | "teacher" | "class";
  timetableEntries: TimetableEntryItem[];
  reviewCards: StatusCard[];
  courseTypeOptions: OptionItem[];
  loadingBatches: boolean;
  batchesError: string;
  loadingEntries: boolean;
  entriesError: string;
}>();

const emit = defineEmits<{
  "update:importRemark": [value: string];
  "file-change": [event: Event];
  "import-timetable": [];
  "select-batch": [batchId: number];
  "update:unresolvedOnly": [value: boolean];
  "update:viewMode": [value: "raw" | "teacher" | "class"];
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

const viewModeModel = computed({
  get: () => props.viewMode,
  set: (value: "raw" | "teacher" | "class") => emit("update:viewMode", value),
});

const batchesEmptyDescription = computed(() => {
  if (props.batchesError) return "课表批次加载失败，请使用页面顶部重试入口重新加载。";
  return "当前学期还没有课表批次。请先选择学期、上传课表模板，再回到这里查看未匹配项。";
});

const entriesEmptyDescription = computed(() => {
  if (!props.selectedBatchId) return "请先选择一个课表批次。";
  if (props.entriesError) return "课表条目加载失败，请使用页面顶部重试入口重新加载。";
  return "当前批次没有符合筛选条件的课表条目。可以关闭“仅看未匹配”，或重新选择批次。";
});

const displayedEntries = computed(() => {
  const rows = [...props.timetableEntries];
  if (props.viewMode === "teacher") {
    return rows.sort((a, b) =>
      `${a.teacher_name ?? a.raw_teacher_name ?? ""}-${a.weekday}-${a.period_no}`.localeCompare(
        `${b.teacher_name ?? b.raw_teacher_name ?? ""}-${b.weekday}-${b.period_no}`,
        "zh-Hans-CN",
      ),
    );
  }
  if (props.viewMode === "class") {
    return rows.sort((a, b) =>
      `${a.class_name ?? a.raw_class_name ?? ""}-${a.weekday}-${a.period_no}`.localeCompare(
        `${b.class_name ?? b.raw_class_name ?? ""}-${b.weekday}-${b.period_no}`,
        "zh-Hans-CN",
      ),
    );
  }
  return rows;
});
</script>

<style scoped>
.review-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.review-card {
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(123, 141, 158, 0.18);
  background: rgba(248, 251, 253, 0.86);
}

.review-card span {
  color: #6c8094;
  font-size: 13px;
}

.review-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3245;
  font-size: 24px;
}

.review-card p {
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

.panel-alert {
  margin-bottom: 14px;
}
</style>
