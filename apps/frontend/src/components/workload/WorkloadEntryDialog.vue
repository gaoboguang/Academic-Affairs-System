<template>
  <el-dialog
    v-model="dialogVisible"
    title="修正课表条目"
    width="560px"
    destroy-on-close
      :close-on-click-modal="false"
    :close-on-press-escape="!saving"
    @closed="emit('closed')"
  >
    <div class="filter-grid">
      <el-select v-model="form.teacher_id" filterable clearable placeholder="教师" :disabled="controlsDisabled">
        <el-option v-for="teacher in teacherOptions" :key="teacher.id" :label="teacher.name" :value="teacher.id" />
      </el-select>
      <el-select v-model="form.class_id" filterable clearable placeholder="班级" :disabled="controlsDisabled">
        <el-option v-for="schoolClass in classes" :key="schoolClass.id" :label="schoolClass.name" :value="schoolClass.id" />
      </el-select>
      <el-select v-model="form.subject_id" filterable clearable placeholder="学科" :disabled="controlsDisabled">
        <el-option v-for="subject in subjects" :key="subject.id" :label="subject.name" :value="subject.id" />
      </el-select>
      <el-select v-model="form.course_type" clearable placeholder="课程类型" :disabled="controlsDisabled">
        <el-option
          v-for="item in courseTypeOptions"
          :key="item.code"
          :label="item.name"
          :value="item.code"
        />
      </el-select>
      <el-input v-model="form.note" placeholder="备注" :disabled="controlsDisabled" />
      <el-switch
        v-model="form.is_active"
        inline-prompt
        active-text="启用"
        inactive-text="停用"
        :disabled="controlsDisabled"
      />
    </div>
    <template #footer>
      <el-button :disabled="saving" @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" :disabled="controlsDisabled" @click="emit('save')">保存修正</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { OptionItem } from "../../stores/reference";
import type { EntryFormState, TeacherOption } from "./types";

const props = defineProps<{
  visible: boolean;
  form: EntryFormState;
  teacherOptions: TeacherOption[];
  classes: OptionItem[];
  subjects: OptionItem[];
  courseTypeOptions: OptionItem[];
  saving: boolean;
  controlsDisabled: boolean;
}>();

const emit = defineEmits<{
  "update:visible": [value: boolean];
  closed: [];
  save: [];
}>();

const dialogVisible = computed({
  get: () => props.visible,
  set: (value: boolean) => emit("update:visible", value),
});
</script>
