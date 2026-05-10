<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>生成推荐方案</h3>
        <p>单个学生支持位次覆盖、综合分输入和艺体辅助参数，批量模式则复用统一筛选条件。</p>
      </div>
      <el-radio-group v-model="generationModeModel" size="default">
        <el-radio-button label="single">单个学生</el-radio-button>
        <el-radio-button label="batch">批量学生</el-radio-button>
      </el-radio-group>
    </div>

    <el-alert
      class="recommend-form-alert"
      :title="recommendationModeLabel"
      type="info"
      show-icon
      :closable="false"
    >
      <template #default>
        {{ recommendationModeHint }}
      </template>
    </el-alert>
    <div v-if="isBatchMode" class="batch-selection-status">
      已选 {{ form.student_ids.length }} 名学生
    </div>

    <div class="filter-grid">
      <el-select v-if="!isBatchMode" v-model="form.student_id" filterable placeholder="选择学生">
        <el-option
          v-for="student in studentOptions"
          :key="student.id"
          :label="`${student.student_no} - ${student.name}`"
          :value="student.id"
        />
      </el-select>
      <el-select
        v-else
        v-model="form.student_ids"
        multiple
        collapse-tags
        filterable
        placeholder="选择多个学生"
      >
        <el-option
          v-for="student in studentOptions"
          :key="student.id"
          :label="`${student.student_no} - ${student.name}`"
          :value="student.id"
        />
      </el-select>
        <el-select v-model="form.exam_id" filterable placeholder="参考考试">
          <el-option v-for="exam in examOptions" :key="exam.id" :label="exam.name" :value="exam.id" />
        </el-select>
      <el-select v-model="form.target_year" filterable placeholder="目标年份">
        <el-option v-for="year in yearOptions" :key="year" :label="`${year}`" :value="year" />
      </el-select>
      <el-select v-model="form.province" clearable filterable placeholder="生源地省份，留空则优先用学生档案">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-input v-model="form.name" placeholder="方案名称，可选" />
      <el-input v-model="form.subject_combination" placeholder="选科组合，可选" />
      <el-select v-if="!isBatchMode" v-model="form.score_input_mode" placeholder="成绩/位次来源">
        <el-option label="正式位次（高考省位次）" value="actual_rank" />
        <el-option label="正式分数" value="actual_score" />
        <el-option label="预估分数" value="estimated_score" />
        <el-option label="预估分 + 预估位次（本次考试/模拟推荐）" value="estimated_score_and_rank" />
        <el-option label="分数区间" value="score_range" />
        <el-option label="位次区间" value="rank_range" />
      </el-select>
      <el-select
        v-model="form.target_regions_json"
        multiple
        filterable
        allow-create
        default-first-option
        collapse-tags
        placeholder="目标地区偏好"
      >
        <el-option v-for="item in targetRegionOptions" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select
        v-model="form.school_level_tags_json"
        multiple
        filterable
        allow-create
        default-first-option
        collapse-tags
        placeholder="院校层级偏好"
      >
        <el-option v-for="item in schoolLevelOptions" :key="item" :label="item" :value="item" />
      </el-select>
      <el-input v-model="form.major_keyword" placeholder="专业方向关键词，可选" />
      <el-switch v-model="form.obey_adjustment" inline-prompt active-text="服从" inactive-text="不服从" />
      <el-input-number
        v-if="!isBatchMode && showRankInput"
        v-model="form.student_rank_override"
        :min="1"
        :max="999999"
        controls-position="right"
        style="width: 100%"
        :placeholder="rankInputPlaceholder"
      />
      <el-input-number
        v-if="!isBatchMode && showScoreInput"
        v-model="form.comprehensive_score"
        :min="0"
        :max="1000"
        controls-position="right"
        style="width: 100%"
        :placeholder="scoreInputPlaceholder"
      />
      <el-input-number
        v-if="!isBatchMode && showCultureScoreInput"
        v-model="form.culture_score"
        :min="0"
        :max="1000"
        controls-position="right"
        style="width: 100%"
        placeholder="文化分"
      />
      <el-input-number
        v-if="!isBatchMode && showProfessionalScoreInput"
        v-model="form.professional_score"
        :min="0"
        :max="1000"
        controls-position="right"
        style="width: 100%"
        placeholder="专业分"
      />
      <el-input-number
        v-if="!isBatchMode && showScoreRangeInput"
        v-model="form.score_range_min"
        :min="0"
        :max="1000"
        controls-position="right"
        style="width: 100%"
        placeholder="分数区间下限"
      />
      <el-input-number
        v-if="!isBatchMode && showScoreRangeInput"
        v-model="form.score_range_max"
        :min="0"
        :max="1000"
        controls-position="right"
        style="width: 100%"
        placeholder="分数区间上限"
      />
      <el-input-number
        v-if="!isBatchMode && showRankRangeInput"
        v-model="form.rank_range_min"
        :min="1"
        :max="999999"
        controls-position="right"
        style="width: 100%"
        placeholder="位次区间下限"
      />
      <el-input-number
        v-if="!isBatchMode && showRankRangeInput"
        v-model="form.rank_range_max"
        :min="1"
        :max="999999"
        controls-position="right"
        style="width: 100%"
        placeholder="位次区间上限"
      />
      <el-input
        v-if="!isBatchMode && showReferenceExamInput"
        v-model="form.reference_exam_name"
        placeholder="参考考试，如一模/二模"
      />
      <el-switch
        v-if="!isBatchMode && showHistoricalMapping"
        v-model="form.use_historical_mapping"
        inline-prompt
        active-text="历史映射"
        inactive-text="直接参考"
      />
      <el-radio-group v-if="!isBatchMode && showRiskPreference" v-model="form.risk_preference" class="risk-group">
        <el-radio-button label="conservative">保守</el-radio-button>
        <el-radio-button label="balanced">平衡</el-radio-button>
        <el-radio-button label="aggressive">激进</el-radio-button>
      </el-radio-group>
    </div>

    <el-input
      v-model="form.note"
      class="note-box"
      type="textarea"
      :rows="3"
      placeholder="补充说明、人工判断依据或特别关注项"
    />

    <div class="action-row toolbar-row">
      <el-button type="primary" :loading="generating" @click="emit('submit')">
        {{ isBatchMode ? "批量生成" : "生成推荐" }}
      </el-button>
      <el-button @click="emit('reset')">重置参数</el-button>
    </div>

    <el-alert
      v-if="latestGenerationMessage"
      class="result-alert"
      :title="latestGenerationMessage"
      :type="alertType"
      show-icon
      :closable="false"
    />
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { ExamOption, RecommendationFormState, StudentOption } from "./types";

const props = defineProps<{
  generationMode: "single" | "batch";
  form: RecommendationFormState;
  studentOptions: StudentOption[];
  examOptions: ExamOption[];
  yearOptions: number[];
  provinceOptions: string[];
  targetRegionOptions: string[];
  schoolLevelOptions: string[];
  generating: boolean;
  latestGenerationMessage: string;
  alertType: "success" | "info";
  recommendationModeLabel: string;
  recommendationModeHint: string;
}>();

const emit = defineEmits<{
  "update:generationMode": [value: "single" | "batch"];
  submit: [];
  reset: [];
}>();

const isBatchMode = computed(() => props.generationMode === "batch");
const showRankInput = computed(() => ["actual_rank", "estimated_score_and_rank"].includes(props.form.score_input_mode));
const showScoreInput = computed(() =>
  ["actual_score", "estimated_score", "estimated_score_and_rank"].includes(props.form.score_input_mode),
);
const showCultureScoreInput = computed(() =>
  ["actual_score", "estimated_score", "estimated_score_and_rank"].includes(props.form.score_input_mode),
);
const showProfessionalScoreInput = computed(() =>
  ["actual_score", "estimated_score", "estimated_score_and_rank"].includes(props.form.score_input_mode),
);
const showScoreRangeInput = computed(() => props.form.score_input_mode === "score_range");
const showRankRangeInput = computed(() => props.form.score_input_mode === "rank_range");
const showReferenceExamInput = computed(() =>
  ["actual_score", "estimated_score", "estimated_score_and_rank", "score_range", "rank_range"].includes(props.form.score_input_mode),
);
const showHistoricalMapping = computed(() =>
  ["actual_score", "estimated_score", "score_range"].includes(props.form.score_input_mode),
);
const showRiskPreference = computed(() => ["score_range", "rank_range"].includes(props.form.score_input_mode));
const rankInputPlaceholder = computed(() =>
  props.form.score_input_mode === "estimated_score_and_rank" ? "预估位次" : "位次覆盖",
);
const scoreInputPlaceholder = computed(() => {
  if (props.form.score_input_mode === "actual_score") return "正式分数";
  if (props.form.score_input_mode === "estimated_score") return "预估分数";
  if (props.form.score_input_mode === "estimated_score_and_rank") return "预估分数";
  return "综合分";
});

const generationModeModel = computed({
  get: () => props.generationMode,
  set: (value: "single" | "batch") => emit("update:generationMode", value),
});
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.recommend-form-alert {
  margin-bottom: 16px;
}

.batch-selection-status {
  margin: -4px 0 14px;
  color: #51687c;
  font-size: 13px;
  font-weight: 700;
}

.note-box {
  margin-top: 4px;
}

.toolbar-row {
  margin-bottom: 16px;
}

.risk-group {
  width: 100%;
  display: flex;
}

.result-alert {
  margin-top: 16px;
}
</style>
