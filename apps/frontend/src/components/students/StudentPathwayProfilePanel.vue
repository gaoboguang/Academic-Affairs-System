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
            <el-select v-model="form.art_track" clearable filterable placeholder="选择艺术类别">
              <el-option v-for="item in pathwayArtTrackOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </label>
          <label class="pathway-field">
            <span>艺术专业分</span>
            <el-input-number
              v-model="form.art_professional_score"
              :min="0"
              :max="300"
              controls-position="right"
              style="width: 100%"
              placeholder="省统考专业分"
            />
          </label>
          <label class="pathway-field">
            <span>艺术专业满分</span>
            <el-input-number
              v-model="form.art_professional_full_score"
              :min="1"
              :max="750"
              controls-position="right"
              style="width: 100%"
              placeholder="默认 300"
            />
          </label>
          <label class="pathway-field">
            <span>艺术成绩来源</span>
            <el-input v-model="form.art_score_source" placeholder="如：山东音乐类统考" />
          </label>
          <label class="pathway-field wide">
            <span>艺术成绩备注</span>
            <el-input v-model="form.art_score_note" placeholder="校考、省际联考或需人工复核的说明" />
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
            <h3>意向偏好</h3>
            <p>这些字段会直接带入志愿工作台「意向偏好」区，不必再二次维护。</p>
          </div>
        </div>
        <div class="pathway-field-grid">
          <label class="pathway-field wide">
            <span>目标地区偏好</span>
            <el-select
              v-model="targetRegions"
              multiple
              filterable
              allow-create
              default-first-option
              collapse-tags
              placeholder="可选多个：山东、江苏…"
            >
              <el-option v-for="item in regionPresetOptions" :key="`region-${item}`" :label="item" :value="item" />
            </el-select>
          </label>
          <label class="pathway-field wide">
            <span>院校层级偏好</span>
            <el-select
              v-model="schoolLevelTags"
              multiple
              filterable
              allow-create
              default-first-option
              collapse-tags
              placeholder="可选多个：双一流、公办本科…"
            >
              <el-option v-for="item in schoolLevelPresetOptions" :key="`level-${item}`" :label="item" :value="item" />
            </el-select>
          </label>
          <label class="pathway-field wide">
            <span>专业方向关键词</span>
            <el-input v-model="majorKeyword" placeholder="如：计算机、护理、机械" />
          </label>
          <label class="pathway-field">
            <span>首选就业方向</span>
            <el-select v-model="primaryDirectionId" clearable filterable placeholder="选择就业方向">
              <el-option
                v-for="item in directionOptions"
                :key="`primary-${item.id}`"
                :label="item.name"
                :value="item.id"
                :disabled="!item.is_active"
              />
            </el-select>
          </label>
          <label class="pathway-field">
            <span>次选就业方向</span>
            <el-select v-model="secondaryDirectionId" clearable filterable placeholder="选择就业方向">
              <el-option
                v-for="item in directionOptions"
                :key="`secondary-${item.id}`"
                :label="item.name"
                :value="item.id"
                :disabled="!item.is_active"
              />
            </el-select>
          </label>
          <label class="pathway-field">
            <span>可接受替代方向</span>
            <el-select v-model="alternativeDirectionId" clearable filterable placeholder="选择就业方向">
              <el-option
                v-for="item in directionOptions"
                :key="`alternative-${item.id}`"
                :label="item.name"
                :value="item.id"
                :disabled="!item.is_active"
              />
            </el-select>
          </label>
          <label class="pathway-field wide">
            <span>偏好重点</span>
            <el-checkbox-group v-model="priorityFocuses">
              <el-checkbox-button v-for="item in focusOptions" :key="item.value" :label="item.value">
                {{ item.label }}
              </el-checkbox-button>
            </el-checkbox-group>
          </label>
          <label class="pathway-field wide">
            <span>目标行业偏好</span>
            <el-select
              v-model="preferredIndustries"
              multiple
              filterable
              allow-create
              default-first-option
              collapse-tags
              placeholder="如：互联网、人工智能、智能制造"
            >
              <el-option v-for="item in industryPresetOptions" :key="`ind-${item}`" :label="item" :value="item" />
            </el-select>
          </label>
          <label class="pathway-field wide">
            <span>目标岗位偏好</span>
            <el-select
              v-model="preferredJobTypes"
              multiple
              filterable
              allow-create
              default-first-option
              collapse-tags
              placeholder="如：算法工程师、产品经理"
            >
              <el-option v-for="item in jobTypePresetOptions" :key="`job-${item}`" :label="item" :value="item" />
            </el-select>
          </label>
          <label class="pathway-field wide">
            <span>目标就业城市</span>
            <el-select
              v-model="targetEmploymentCities"
              multiple
              filterable
              allow-create
              default-first-option
              collapse-tags
              placeholder="如：济南、青岛、北京"
            >
              <el-option v-for="item in regionPresetOptions" :key="`city-${item}`" :label="item" :value="item" />
            </el-select>
          </label>
          <label class="pathway-field">
            <span>可接受深造路径</span>
            <el-switch v-model="acceptsPostgraduate" inline-prompt active-text="是" inactive-text="否" />
          </label>
          <label class="pathway-field">
            <span>可接受公考路径</span>
            <el-switch v-model="acceptsPublicService" inline-prompt active-text="是" inactive-text="否" />
          </label>
          <label class="pathway-field">
            <span>可接受证书路径</span>
            <el-switch v-model="acceptsCertificate" inline-prompt active-text="是" inactive-text="否" />
          </label>
          <label class="pathway-field">
            <span>可接受长周期培养</span>
            <el-switch v-model="acceptsLongTraining" inline-prompt active-text="是" inactive-text="否" />
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
            <span>备注</span>
            <el-input
              v-model="form.note"
              type="textarea"
              :rows="3"
              placeholder="记录已联系家长、仍待确认的问题等"
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
  buildPathwayProfileReadiness,
  buildStudentPathwayProfilePayload,
  createStudentPathwayProfileForm,
  pathwayArtTrackOptions,
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

interface EmploymentDirectionOption {
  id: number;
  name: string;
  is_active: boolean;
}

const directionOptions = ref<EmploymentDirectionOption[]>([]);

const regionPresetOptions = [
  "山东", "江苏", "河南", "河北", "广东", "浙江", "上海", "北京", "天津",
  "湖北", "湖南", "安徽", "福建", "江西", "辽宁", "黑龙江", "吉林",
  "济南", "青岛", "烟台", "潍坊",
];
const schoolLevelPresetOptions = [
  "双一流", "985", "211", "普通本科", "公办本科", "民办本科",
  "公办专科", "民办专科", "高职院校",
];
const industryPresetOptions = [
  "互联网", "人工智能", "智能制造", "教育", "医疗健康",
  "金融", "公共服务", "新能源", "文化传媒", "建筑工程",
];
const jobTypePresetOptions = [
  "算法工程师", "软件工程师", "产品经理", "数据分析师",
  "教师", "医生", "护士", "公务员", "工程师", "设计师",
];
const focusOptions: Array<{ value: string; label: string }> = [
  { value: "stability", label: "稳定" },
  { value: "salary", label: "薪酬" },
  { value: "interest", label: "兴趣" },
  { value: "long_term", label: "长远发展" },
];

function listFromJson(value: unknown): string[] {
  return Array.isArray(value)
    ? value.map((item) => (typeof item === "string" ? item : "")).filter((item): item is string => item.length > 0)
    : [];
}

function readNumber(value: unknown): number | undefined {
  return typeof value === "number" ? value : undefined;
}

function readBool(value: unknown): boolean {
  return typeof value === "boolean" ? value : false;
}

function regionGetSet<T>(key: string, fallback: () => T, parse: (raw: unknown) => T) {
  return computed<T>({
    get: () => parse((form.region_preferences_json ?? {})[key]),
    set: (value: T) => {
      const next = { ...(form.region_preferences_json ?? {}) };
      if (value == null || (Array.isArray(value) && value.length === 0) || value === "") {
        delete next[key];
      } else {
        next[key] = value as never;
      }
      form.region_preferences_json = next;
      void fallback;
    },
  });
}

function careerGetSet<T>(key: string, parse: (raw: unknown) => T) {
  return computed<T>({
    get: () => parse((form.career_preferences_json ?? {})[key]),
    set: (value: T) => {
      const next = { ...(form.career_preferences_json ?? {}) };
      if (value == null || (Array.isArray(value) && value.length === 0) || value === "") {
        delete next[key];
      } else {
        next[key] = value as never;
      }
      form.career_preferences_json = next;
    },
  });
}

const targetRegions = regionGetSet<string[]>("target_regions", () => [], listFromJson);
const schoolLevelTags = regionGetSet<string[]>("school_level_tags", () => [], listFromJson);
const majorKeyword = regionGetSet<string>("major_keyword", () => "", (raw) =>
  typeof raw === "string" ? raw : "",
);

const primaryDirectionId = careerGetSet<number | undefined>("primary_direction_id", readNumber);
const secondaryDirectionId = careerGetSet<number | undefined>("secondary_direction_id", readNumber);
const alternativeDirectionId = careerGetSet<number | undefined>("alternative_direction_id", readNumber);
const priorityFocuses = careerGetSet<string[]>("priority_focuses", listFromJson);
const preferredIndustries = careerGetSet<string[]>("preferred_industries", listFromJson);
const preferredJobTypes = careerGetSet<string[]>("preferred_job_types", listFromJson);
const targetEmploymentCities = careerGetSet<string[]>("target_employment_cities", listFromJson);
const acceptsPostgraduate = careerGetSet<boolean>("accepts_postgraduate", readBool);
const acceptsPublicService = careerGetSet<boolean>("accepts_public_service", readBool);
const acceptsCertificate = careerGetSet<boolean>("accepts_certificate", readBool);
const acceptsLongTraining = careerGetSet<boolean>("accepts_long_training", readBool);

async function loadDirectionOptions(): Promise<void> {
  try {
    directionOptions.value = await apiRequest<EmploymentDirectionOption[]>(
      "/api/employment-directions?page_size=500",
    );
  } catch (error) {
    // direction list is optional UX sugar; fall back silently.
    void error;
  }
}

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
onMounted(() => {
  void loadProfile();
  void loadDirectionOptions();
});
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
