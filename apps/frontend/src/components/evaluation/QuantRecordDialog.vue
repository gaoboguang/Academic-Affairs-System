<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="760px"
    destroy-on-close
    :close-on-click-modal="false"
    @closed="emit('closed')"
  >
    <el-form label-width="92px">
      <div class="form-grid">
        <el-form-item label="教师">
          <el-select v-model="form.teacher_id" filterable style="width: 100%">
            <el-option v-for="teacher in teacherOptions" :key="teacher.id" :label="teacher.name" :value="teacher.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="班级">
          <el-select v-model="form.class_id" clearable filterable style="width: 100%">
            <el-option v-for="item in classes" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="学期">
          <el-select v-model="form.semester_id" filterable style="width: 100%">
            <el-option
              v-for="item in semesters"
              :key="item.id"
              :label="semesterLabel(item)"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="月份">
          <el-input v-model="form.record_month" placeholder="YYYY-MM" />
        </el-form-item>
        <el-form-item label="规则项" class="span-two">
          <el-select v-model="form.rule_item_id" filterable style="width: 100%">
            <el-option
              v-for="item in quantRuleItemOptions"
              :key="item.id"
              :label="`${item.item_name} / ${item.default_score}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="得分">
          <el-input-number v-model="form.score" :step="0.5" />
        </el-form-item>
      </div>
      <el-form-item label="说明">
        <el-input v-model="form.description" type="textarea" :rows="3" />
      </el-form-item>
    </el-form>

    <div class="section-head compact">
      <div>
        <h4>附件</h4>
        <p>量化项要求附件时，这里必须至少上传一个文件。</p>
      </div>
    </div>
    <div class="action-row">
      <input
        class="file-input"
        type="file"
        multiple
        @change="emit('upload-attachments', $event)"
      />
    </div>
    <div class="attachment-tags">
      <el-tag
        v-for="item in form.attachments"
        :key="item.id"
        closable
        @close="emit('remove-attachment', item.id)"
      >
        {{ item.original_filename }}
      </el-tag>
      <span v-if="!form.attachments.length" class="hint-text">暂无附件</span>
    </div>

    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="emit('save')">保存记录</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { OptionItem } from "../../stores/reference";
import { semesterLabel } from "./helpers";
import type { QuantFormState, RuleItem, TeacherOption } from "./types";

const props = defineProps<{
  visible: boolean;
  title: string;
  saving: boolean;
  form: QuantFormState;
  teacherOptions: TeacherOption[];
  classes: OptionItem[];
  semesters: OptionItem[];
  quantRuleItemOptions: RuleItem[];
}>();

const emit = defineEmits<{
  "update:visible": [value: boolean];
  closed: [];
  "upload-attachments": [event: Event];
  "remove-attachment": [fileId: number];
  save: [];
}>();

const dialogVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit("update:visible", value),
});
</script>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.span-two {
  grid-column: span 2;
}

.file-input {
  width: 100%;
  padding: 12px 14px;
  border: 1px dashed rgba(114, 132, 150, 0.36);
  border-radius: 16px;
  background: rgba(248, 252, 255, 0.7);
}

.attachment-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.hint-text {
  color: #7c8f9f;
  font-size: 13px;
}

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .span-two {
    grid-column: span 1;
  }
}
</style>
