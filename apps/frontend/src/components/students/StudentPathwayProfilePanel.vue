<template>
  <section class="pathway-profile-panel">
    <div class="section-head">
      <div>
        <h3>升学画像</h3>
        <p>记录山东升学路径会用到的身份、选科、意向和材料状态。这里的评估只做资格初筛，不代表录取概率。</p>
      </div>
      <div class="action-row">
        <el-button :loading="evaluating" @click="refreshEvaluations">刷新评估</el-button>
        <el-button type="primary" :loading="saving" @click="saveProfile">保存画像并重新评估</el-button>
      </div>
    </div>

    <el-alert
      v-if="errorMessage"
      class="pathway-alert"
      type="error"
      :closable="false"
      :title="errorMessage"
      show-icon
    />
    <el-alert
      v-else
      class="pathway-alert"
      type="info"
      :closable="false"
      title="先把事实填准，再看系统提示缺什么。单招、综评、春考、艺体、体育、提前批和特殊类型都需要人工复核官方公告和高校章程。"
      show-icon
    />

    <div class="pathway-status-strip">
      <span v-for="item in readinessItems" :key="item.key" class="pathway-readiness-chip" :class="{ ready: item.ready }">
        <strong>{{ item.label }}</strong>{{ item.value }}
      </span>
    </div>

    <div class="pathway-layout" v-loading="loading">
      <section class="pathway-form-block">
        <div class="section-head compact">
          <div>
            <h3>学生事实</h3>
            <p>这些字段会直接影响路径初筛。未确认时系统会按“信息不足”提醒。</p>
          </div>
        </div>

        <div class="pathway-field-grid">
          <label class="pathway-field">
            <span>生源地</span>
            <el-select v-model="form.province" filterable>
              <el-option label="山东" value="山东" />
            </el-select>
          </label>
          <label class="pathway-field">
            <span>考生类型</span>
            <el-select v-model="form.candidate_type" filterable placeholder="选择考生类型">
              <el-option v-for="item in pathwayCandidateTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </label>
          <label class="pathway-field">
            <span>考试类型</span>
            <el-select v-model="form.exam_type" filterable placeholder="选择考试类型">
              <el-option v-for="item in pathwayExamTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </label>
          <label class="pathway-field wide">
            <span>选科组合</span>
            <el-input v-model="form.subject_combination" placeholder="如：物理,化学,生物" />
          </label>
          <label class="pathway-field">
            <span>春考专业类别</span>
            <el-input v-model="form.spring_exam_category" placeholder="如：软件与应用技术" />
          </label>
          <label class="pathway-field">
            <span>艺术类别</span>
            <el-input v-model="form.art_track" placeholder="如：美术与设计类" />
          </label>
          <label class="pathway-field">
            <span>体育类别</span>
            <el-input v-model="form.sports_track" placeholder="如：体育类 / 运动训练" />
          </label>
        </div>

        <div class="section-head compact subsection-head">
          <div>
            <h3>身份与意向</h3>
            <p>选择“不符合 / 不接受”时，相关路径可能直接显示为不建议。</p>
          </div>
        </div>
        <div class="pathway-bool-grid">
          <label v-for="item in booleanFields" :key="item.field" class="pathway-field">
            <span>{{ item.label }}</span>
            <el-select v-model="form[item.field]" placeholder="未确认">
              <el-option v-for="option in pathwayBooleanOptions" :key="`${item.field}-${option.label}`" :label="option.label" :value="option.value" />
            </el-select>
            <small>{{ item.help }}</small>
          </label>
        </div>

        <div class="section-head compact subsection-head">
          <div>
            <h3>材料准备</h3>
            <p>勾选的是“材料已经整理到位”，不是系统自动判定。</p>
          </div>
        </div>
        <div class="pathway-material-grid">
          <label v-for="item in materialChecklist" :key="item.key" class="pathway-material-item">
            <el-checkbox v-model="form.materials_json[item.key]">{{ item.label }}</el-checkbox>
            <small>{{ item.help }}</small>
          </label>
        </div>

        <div class="pathway-note-grid">
          <label class="pathway-field">
            <span>体检限制</span>
            <el-input
              v-model="bodyLimitationsText"
              type="textarea"
              :rows="3"
              placeholder="如色觉、身高、视力、语种、单科成绩等需要逐校核对的限制"
            />
          </label>
          <label class="pathway-field">
            <span>材料备注</span>
            <el-input
              v-model="form.note"
              type="textarea"
              :rows="3"
              placeholder="记录已联系家长、材料存放位置、仍待确认的问题"
            />
          </label>
        </div>
      </section>

      <aside class="pathway-result-block">
        <div class="section-head compact">
          <div>
            <h3>路径初筛结果</h3>
            <p>先看缺口，再决定是否进入具体院校和专业核对。</p>
          </div>
        </div>

        <div v-if="statusSummary.length" class="pathway-summary-grid">
          <span v-for="item in statusSummary" :key="item.status" class="pathway-summary-chip">
            <strong>{{ item.count }}</strong>{{ item.label }}
          </span>
        </div>
        <el-empty v-else description="暂无路径评估结果，保存画像后刷新评估。" />

        <div class="pathway-gap-box">
          <h4>系统识别到的缺口</h4>
          <div v-if="aggregatedGaps.length" class="pathway-gap-list">
            <article v-for="gap in aggregatedGaps" :key="gap.key" class="pathway-gap-item">
              <div>
                <strong>{{ gap.label }}</strong>
                <span>影响 {{ gap.count }} 条路径：{{ gap.pathways.join("、") }}</span>
              </div>
              <p>{{ gap.nextAction }}</p>
            </article>
          </div>
          <p v-else class="muted-copy">暂无系统识别到的材料缺口。仍需在正式报名前逐校核对官方公告、招生章程和报名时间。</p>
        </div>

        <div class="pathway-evaluation-list">
          <article v-for="item in evaluations" :key="item.pathway_id" class="pathway-evaluation-item">
            <div class="pathway-evaluation-head">
              <div>
                <strong>{{ item.pathway_name }}</strong>
                <span>{{ item.pathway_group }} · {{ item.recommendation_depth === "full_rank_recommendation" ? "可接冲稳保推荐" : "资格初筛 / 人工复核" }}</span>
              </div>
              <el-tag :type="pathwayStatusTagType(item.status)" effect="light">{{ item.status_label }}</el-tag>
            </div>
            <p>{{ item.summary }}</p>
            <ul v-if="item.next_actions_json.length" class="pathway-action-list">
              <li v-for="action in item.next_actions_json.slice(0, 3)" :key="action">{{ action }}</li>
            </ul>
          </article>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest } from "../../api/client";
import { formatUserActionError } from "../../utils/userFeedback";
import {
  applyPathwayProfileToForm,
  buildPathwayMaterialChecklist,
  buildPathwayProfileReadiness,
  buildStudentPathwayProfilePayload,
  collectStudentPathwayGaps,
  createStudentPathwayProfileForm,
  pathwayBooleanOptions,
  pathwayCandidateTypeOptions,
  pathwayExamTypeOptions,
  pathwayStatusTagType,
  summarizePathwayStatuses,
  type PathwayBooleanValue,
  type StudentPathwayEvaluation,
  type StudentPathwayEvaluationResponse,
  type StudentPathwayProfile,
  type StudentPathwayProfilePayload,
} from "./studentPathwayProfile";

type BooleanFieldKey = {
  [Key in keyof StudentPathwayProfilePayload]: StudentPathwayProfilePayload[Key] extends PathwayBooleanValue ? Key : never;
}[keyof StudentPathwayProfilePayload];

interface BooleanFieldConfig {
  field: BooleanFieldKey;
  label: string;
  help: string;
}

const props = defineProps<{
  studentId: number;
}>();

const targetYear = ref(2026);
const loading = ref(false);
const saving = ref(false);
const evaluating = ref(false);
const errorMessage = ref<string | null>(null);
const form = reactive(createStudentPathwayProfileForm());
const evaluations = ref<StudentPathwayEvaluation[]>([]);

const booleanFields: BooleanFieldConfig[] = [
  { field: "has_gaokao_registration", label: "已完成高考报名", help: "普通类、单招、体育等路径都会先看这个事实。" },
  { field: "is_fresh_graduate", label: "普通高中应届", help: "高职综评等路径会用到。" },
  { field: "is_vocational_student", label: "中职学生", help: "单招和春考路径会重点核对。" },
  { field: "is_social_candidate", label: "社会人员", help: "社会人员走单招时需补学历或同等学力材料。" },
  { field: "has_high_school_equivalent", label: "高中阶段学历或同等学力", help: "用于社会人员资格核验。" },
  { field: "accept_junior_college", label: "接受专科", help: "影响专科批、单招和综评路径是否可继续关注。" },
  { field: "accept_private_college", label: "接受民办院校", help: "用于后续筛选和家校沟通。" },
  { field: "accept_sino_foreign", label: "接受中外合作", help: "涉及费用和培养方式，建议提前确认。" },
  { field: "accept_outside_province", label: "接受省外院校", help: "用于后续地域筛选。" },
  { field: "accept_early_batch", label: "接受提前批", help: "提前批常伴随特殊流程和限制。" },
  { field: "accept_service_commitment", label: "接受定向服务", help: "公费师范、定向就业等路径需要确认。" },
  { field: "accept_interview_or_physical_test", label: "接受面试体检政审", help: "提前批、招飞、警校等路径需要确认。" },
];

const readinessItems = computed(() => buildPathwayProfileReadiness(form));
const materialChecklist = computed(() => buildPathwayMaterialChecklist(form.materials_json));
const aggregatedGaps = computed(() => collectStudentPathwayGaps(evaluations.value));
const statusSummary = computed(() => summarizePathwayStatuses(evaluations.value));

const bodyLimitationsText = computed({
  get() {
    const note = form.known_body_limitations_json.note;
    return typeof note === "string" ? note : "";
  },
  set(value: string) {
    const normalized = value.trim();
    form.known_body_limitations_json = normalized ? { note: normalized } : {};
  },
});

async function loadProfile(): Promise<void> {
  if (!props.studentId) return;
  loading.value = true;
  errorMessage.value = null;
  try {
    const payload = await apiRequest<StudentPathwayProfile>(`/api/gaokao/students/${props.studentId}/pathway-profile`);
    applyPathwayProfileToForm(form, payload);
    await refreshEvaluations();
  } catch (error) {
    errorMessage.value = formatUserActionError("加载学生升学画像", error, "确认本地服务已启动，或返回学生列表后重新进入详情页。");
  } finally {
    loading.value = false;
  }
}

async function saveProfile(): Promise<void> {
  if (!props.studentId) return;
  saving.value = true;
  errorMessage.value = null;
  try {
    const saved = await apiRequest<StudentPathwayProfile>(`/api/gaokao/students/${props.studentId}/pathway-profile`, {
      method: "PUT",
      body: JSON.stringify(buildStudentPathwayProfilePayload(form)),
    });
    applyPathwayProfileToForm(form, saved);
    ElMessage.success("升学画像已保存");
    await refreshEvaluations();
  } catch (error) {
    errorMessage.value = formatUserActionError("保存学生升学画像", error, "检查必填事实和材料备注后重试。");
  } finally {
    saving.value = false;
  }
}

async function refreshEvaluations(): Promise<void> {
  if (!props.studentId) return;
  evaluating.value = true;
  errorMessage.value = null;
  try {
    const payload = await apiRequest<StudentPathwayEvaluationResponse>(
      `/api/gaokao/students/${props.studentId}/pathway-evaluations/preview?target_year=${targetYear.value}&province=${encodeURIComponent(form.province || "山东")}`,
      { method: "POST" },
    );
    evaluations.value = payload.evaluations;
  } catch (error) {
    errorMessage.value = formatUserActionError("刷新升学路径评估", error, "先保存画像，确认路径规则已完成装载后再刷新。");
  } finally {
    evaluating.value = false;
  }
}

watch(() => props.studentId, loadProfile);
onMounted(loadProfile);
</script>

<style scoped>
.pathway-profile-panel {
  display: grid;
  gap: 16px;
}

.pathway-alert {
  margin-top: -4px;
}

.pathway-status-strip,
.pathway-summary-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.pathway-readiness-chip,
.pathway-summary-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid rgba(120, 138, 156, 0.18);
  background: rgba(246, 248, 250, 0.86);
  color: #5f7387;
  font-size: 13px;
}

.pathway-readiness-chip.ready {
  border-color: rgba(69, 141, 105, 0.28);
  background: rgba(237, 248, 242, 0.94);
  color: #2f6e50;
}

.pathway-readiness-chip strong,
.pathway-summary-chip strong {
  color: #26394d;
}

.pathway-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.8fr);
  gap: 18px;
}

.pathway-form-block,
.pathway-result-block {
  min-width: 0;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid rgba(120, 138, 156, 0.14);
  background: rgba(255, 255, 255, 0.86);
}

.subsection-head {
  margin-top: 22px;
}

.pathway-field-grid,
.pathway-bool-grid,
.pathway-note-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.pathway-bool-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.pathway-note-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 16px;
}

.pathway-field {
  display: grid;
  gap: 8px;
}

.pathway-field.wide {
  grid-column: span 2;
}

.pathway-field span,
.pathway-material-item span {
  color: #53697e;
  font-size: 13px;
  font-weight: 700;
}

.pathway-field small,
.pathway-material-item small {
  color: #718599;
  line-height: 1.5;
}

.pathway-material-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.pathway-material-item {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(120, 138, 156, 0.14);
  background: rgba(247, 250, 253, 0.78);
}

.pathway-gap-box {
  margin-top: 16px;
  padding: 16px;
  border-radius: 8px;
  background: rgba(247, 250, 253, 0.86);
}

.pathway-gap-box h4 {
  margin: 0 0 12px;
  color: #25384b;
}

.pathway-gap-list,
.pathway-evaluation-list {
  display: grid;
  gap: 12px;
}

.pathway-gap-item,
.pathway-evaluation-item {
  padding: 14px;
  border-radius: 8px;
  border: 1px solid rgba(120, 138, 156, 0.14);
  background: #fff;
}

.pathway-gap-item strong,
.pathway-evaluation-item strong {
  display: block;
  color: #22364a;
}

.pathway-gap-item span,
.pathway-evaluation-head span {
  display: block;
  margin-top: 5px;
  color: #687d91;
  font-size: 13px;
  line-height: 1.5;
}

.pathway-gap-item p,
.pathway-evaluation-item p {
  margin: 10px 0 0;
  color: #5f7387;
  line-height: 1.6;
}

.pathway-evaluation-list {
  margin-top: 16px;
  max-height: 720px;
  overflow: auto;
  padding-right: 4px;
}

.pathway-evaluation-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.pathway-action-list {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #5f7387;
  line-height: 1.6;
}

@media (max-width: 1180px) {
  .pathway-layout,
  .pathway-field-grid,
  .pathway-bool-grid,
  .pathway-material-grid,
  .pathway-note-grid {
    grid-template-columns: 1fr;
  }

  .pathway-field.wide {
    grid-column: auto;
  }
}
</style>
