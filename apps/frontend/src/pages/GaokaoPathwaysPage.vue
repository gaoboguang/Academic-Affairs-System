<template>
  <AppPage
    class="pathway-center-page"
    eyebrow="升学方案 / 山东路径初筛"
    title="山东升学方案中心"
    description="汇总学生画像、升学路径状态、材料缺口和数据风险。这里先做资格初筛和人工复核提示，不承诺录取概率。"
    :meta="pageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button :loading="loading" @click="reloadAll"
          >刷新方案中心</el-button
        >
        <el-button @click="router.push('/gaokao-data')">查看高考数据</el-button>
        <el-button
          :disabled="!selectedStudentId"
          :loading="generatingPlanningTasks"
          @click="generatePlanningTasks"
        >
          生成规划任务
        </el-button>
        <el-button
          :disabled="!cards.length"
          @click="openPathwayReportPrintPreview"
          >打印报告</el-button
        >
        <el-button
          :disabled="!cards.length"
          :loading="exportingReport"
          @click="exportPathwayReport"
          >导出 Excel</el-button
        >
        <el-button
          type="primary"
          :disabled="!selectedStudentId"
          @click="openRecommendationWorkbench"
        >
          山东普通类推荐
        </el-button>
      </div>
    </template>

    <AppFilterBar
      title="全局筛选"
      description="选择学生和目标年份后，统一刷新画像、路径卡和材料缺口。"
      sticky
    >
      <div class="pathway-filter-grid">
        <div class="pathway-filter-field">
          <span>选择学生</span>
          <el-select
            v-model="selectedStudentId"
            filterable
            placeholder="选择要评估的学生"
            @change="handleStudentChange"
          >
            <el-option
              v-for="student in studentOptions"
              :key="student.id"
              :label="formatPathwayStudentOption(student)"
              :value="student.id"
            />
          </el-select>
        </div>
        <div class="pathway-filter-field year-field">
          <span>目标年份</span>
          <el-input-number
            v-model="targetYear"
            :min="2020"
            :max="2100"
            @change="refreshEvaluations"
          />
        </div>
        <div class="pathway-filter-copy">
          <strong>当前口径</strong>
          <span>山东生源地；特殊类型只做资格初筛与材料核验。</span>
        </div>
      </div>
    </AppFilterBar>

    <AppStatGrid :items="pageStatCards" :columns="4" />

    <el-alert
      v-if="errorMessage"
      type="error"
      show-icon
      :closable="false"
      :title="errorMessage"
    />

    <section class="pathway-overview-grid" v-loading="loading">
      <article class="soft-card panel-block">
        <div class="section-head compact">
          <div>
            <h3>学生升学画像摘要</h3>
            <p>来自学生详情页“升学画像”，缺项会直接影响路径初筛。</p>
          </div>
          <el-button v-if="selectedStudentId" @click="openStudentProfile"
            >编辑画像</el-button
          >
        </div>
        <div v-if="profileSummary.length" class="pathway-profile-grid">
          <div
            v-for="item in profileSummary"
            :key="item.key"
            class="pathway-profile-item"
            :class="{ filled: item.filled }"
          >
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
        <el-empty v-else description="请选择学生后查看升学画像摘要" />
      </article>

      <article class="soft-card panel-block">
        <div class="section-head compact">
          <div>
            <h3>材料缺口</h3>
            <p>按影响路径数量排序，先补影响面最大的材料或画像字段。</p>
          </div>
        </div>
        <div v-if="aggregatedGaps.length" class="pathway-gap-list">
          <article
            v-for="gap in aggregatedGaps.slice(0, 5)"
            :key="gap.key"
            class="pathway-gap-row"
          >
            <div>
              <strong>{{ gap.label }}</strong>
              <span>影响 {{ gap.count }} 条路径</span>
            </div>
            <p>{{ gap.nextAction }}</p>
          </article>
        </div>
        <p v-else class="muted-copy">
          暂无集中材料缺口。仍需在正式报名前逐校核对官方公告、招生章程和报名时间。
        </p>
      </article>
    </section>

    <section class="pathway-card-section" v-loading="evaluating">
      <div class="section-head">
        <div>
          <h3>升学路径卡片</h3>
          <p>
            每张卡片只说明“能不能继续关注、缺什么、下一步做什么”。只有普通类常规批接入完整位次推荐。
          </p>
        </div>
      </div>
      <div v-if="cards.length" class="pathway-card-grid">
        <article
          v-for="card in cards"
          :key="card.pathwayId"
          class="pathway-card"
        >
          <div class="pathway-card-head">
            <div>
              <span>{{ card.group }}</span>
              <h3>{{ card.name }}</h3>
            </div>
            <el-tag :type="card.statusType" effect="light">{{
              card.statusLabel
            }}</el-tag>
          </div>
          <p class="pathway-card-summary">{{ card.summary }}</p>
          <div class="pathway-card-meta">
            <span><strong>适用对象</strong>{{ card.applicableObject }}</span>
            <span><strong>推荐深度</strong>{{ card.depthLabel }}</span>
            <span><strong>置信程度</strong>{{ card.confidenceLabel }}</span>
          </div>
          <div class="pathway-card-body">
            <div>
              <h4>关键要求</h4>
              <ul>
                <li
                  v-for="item in card.keyRequirements.slice(0, 3)"
                  :key="item"
                >
                  {{ item }}
                </li>
              </ul>
            </div>
            <div>
              <h4>缺失材料</h4>
              <ul v-if="card.missingMaterials.length">
                <li
                  v-for="item in card.missingMaterials.slice(0, 3)"
                  :key="item"
                >
                  {{ item }}
                </li>
              </ul>
              <p v-else class="muted-copy">当前没有系统识别到的材料缺口。</p>
            </div>
          </div>
          <el-alert
            v-if="card.riskMessages.length"
            class="pathway-card-alert"
            type="warning"
            :closable="false"
            :title="card.riskMessages[0]"
          />
          <div class="pathway-card-actions">
            <el-button @click="openPathwayDetail(card)">查看详情</el-button>
            <el-button
              v-if="card.canOpenRecommendation"
              type="primary"
              @click="openRecommendationWorkbench"
            >
              进入普通类推荐
            </el-button>
          </div>
        </article>
      </div>
      <el-empty v-else description="暂无路径评估结果，请先选择学生并刷新。" />
    </section>

    <section class="pathway-bottom-grid">
      <article class="soft-card panel-block">
        <div class="section-head compact">
          <div>
            <h3>下一步行动</h3>
            <p>按当前评估结果自动汇总，优先处理会影响多个路径的事项。</p>
          </div>
        </div>
        <div class="pathway-action-list">
          <article
            v-for="item in nextActions"
            :key="item.key"
            class="pathway-action-card"
          >
            <el-tag :type="formatPathwayStatusTone(item.tone)" effect="light">{{
              item.title
            }}</el-tag>
            <p>{{ item.detail }}</p>
          </article>
        </div>
      </article>

      <article class="soft-card panel-block">
        <div class="section-head compact">
          <div>
            <h3>2026 数据发布与 P0 风险</h3>
            <p>
              普通类正式计划、一分一段、省控线和投档结果要按官方发布状态理解。
            </p>
          </div>
          <el-tag
            :type="dataHealth?.gaps.length ? 'warning' : 'success'"
            effect="light"
          >
            {{ dataHealth?.summary || "待检查" }}
          </el-tag>
        </div>
        <div class="table-shell compact-table">
          <el-table :data="publicationHighlights" stripe>
            <el-table-column label="数据项" prop="label" min-width="160" />
            <el-table-column label="状态" width="140">
              <template #default="{ row }">
                <el-tag :type="publicationTagType(row.status)" effect="light">{{
                  row.status_label
                }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="下一步"
              prop="action_label"
              min-width="220"
            />
          </el-table>
        </div>
        <ul v-if="dataHealth?.gaps.length" class="pathway-risk-list">
          <li v-for="gap in dataHealth.gaps.slice(0, 5)" :key="gap">
            {{ gap }}
          </li>
        </ul>
      </article>
    </section>

    <el-drawer
      v-model="detailDrawerVisible"
      :title="selectedCard?.name || '路径详情'"
      size="560px"
      destroy-on-close
    >
      <div v-if="selectedCard" class="pathway-detail-drawer">
        <div class="pathway-detail-head">
          <el-tag :type="selectedCard.statusType" effect="light">{{
            selectedCard.statusLabel
          }}</el-tag>
          <el-tag effect="plain">{{ selectedCard.depthLabel }}</el-tag>
        </div>
        <p>{{ selectedCard.depthHelp }}</p>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="适用对象">{{
            selectedCard.applicableObject
          }}</el-descriptions-item>
          <el-descriptions-item label="志愿方式">{{
            selectedCard.volunteerMode
          }}</el-descriptions-item>
          <el-descriptions-item label="评估分">{{
            selectedCard.score ?? "-"
          }}</el-descriptions-item>
          <el-descriptions-item label="来源编号">{{
            selectedCard.pathway?.source_document_id ?? "待追溯"
          }}</el-descriptions-item>
        </el-descriptions>

        <section class="pathway-detail-section">
          <h4>规则命中情况</h4>
          <div class="pathway-rule-group">
            <strong>已满足</strong>
            <p
              v-if="!selectedCard.evaluation.matched_rules_json.length"
              class="muted-copy"
            >
              暂无已满足规则。
            </p>
            <ul>
              <li
                v-for="rule in selectedCard.evaluation.matched_rules_json"
                :key="rule.rule_code"
              >
                {{ formatRuleLine(rule) }}
              </li>
            </ul>
          </div>
          <div class="pathway-rule-group">
            <strong>不满足或信息不足</strong>
            <p
              v-if="
                !selectedCard.evaluation.failed_rules_json.length &&
                !selectedCard.evaluation.warning_rules_json.length
              "
              class="muted-copy"
            >
              暂无硬性不满足项。
            </p>
            <ul>
              <li
                v-for="rule in [
                  ...selectedCard.evaluation.failed_rules_json,
                  ...selectedCard.evaluation.warning_rules_json,
                ]"
                :key="rule.rule_code"
              >
                {{ formatRuleLine(rule) }}
              </li>
            </ul>
          </div>
        </section>

        <section class="pathway-detail-section">
          <h4>材料缺口</h4>
          <ul v-if="selectedCard.evaluation.missing_materials_json.length">
            <li
              v-for="item in selectedCard.evaluation.missing_materials_json"
              :key="`${item.rule_code}-${item.material_key}`"
            >
              {{
                item.material_label ||
                formatPathwayMaterialKey(item.material_key || item.rule_code)
              }}：{{ item.next_action || item.message || "补齐后重新评估。" }}
            </li>
          </ul>
          <p v-else class="muted-copy">当前没有系统识别到的材料缺口。</p>
        </section>

        <section class="pathway-detail-section">
          <h4>下一步</h4>
          <ul>
            <li v-for="action in selectedCard.nextActions" :key="action">
              {{ action }}
            </li>
          </ul>
        </section>
      </div>
    </el-drawer>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import { useRoute, useRouter } from "vue-router";

import { apiRequest, openFile } from "../api/client";
import AppFilterBar from "../components/ui/AppFilterBar.vue";
import AppPage from "../components/ui/AppPage.vue";
import AppStatGrid from "../components/ui/AppStatGrid.vue";
import type { PageMetaItem, StatCardItem } from "../components/ui/types";
import {
  GAOKAO_PATHWAY_PRINT_STORAGE_PREFIX,
  buildGaokaoPathwayReportName,
  buildGaokaoPathwayReportPayload,
  buildPathwayCenterActions,
  buildPathwayCenterCards,
  buildPathwayProfileSummary,
  buildPublicationStatusHighlights,
  buildStatusSummaryCopy,
  formatPathwayStatusTone,
  formatPathwayStudentOption,
  type GaokaoPathwayRead,
  type PathwayCenterCard,
  type PathwayCenterStudentOption,
} from "../components/gaokao-pathways/pathwayCenter";
import {
  collectStudentPathwayGaps,
  formatPathwayMaterialKey,
  summarizePathwayStatuses,
  type StudentPathwayEvaluation,
  type StudentPathwayEvaluationResponse,
  type StudentPathwayProfile,
  type StudentPathwayRuleEvaluation,
} from "../components/students/studentPathwayProfile";
import type { ShandongRecommendationDataHealth } from "../components/recommendations/types";
import type { ExportRecord } from "../components/recommendations/types";
import { gaokaoPathwayPrintPreviewPath } from "../utils/print";
import { formatUserActionError } from "../utils/userFeedback";

interface StudentListResponse {
  items: PathwayCenterStudentOption[];
  total: number;
  page: number;
  page_size: number;
}

const router = useRouter();
const route = useRoute();

const studentOptions = ref<PathwayCenterStudentOption[]>([]);
const selectedStudentId = ref<number | undefined>(undefined);
const targetYear = ref(2026);
const pathways = ref<GaokaoPathwayRead[]>([]);
const profile = ref<StudentPathwayProfile | null>(null);
const evaluations = ref<StudentPathwayEvaluation[]>([]);
const dataHealth = ref<ShandongRecommendationDataHealth | null>(null);
const loading = ref(false);
const evaluating = ref(false);
const errorMessage = ref<string | null>(null);
const detailDrawerVisible = ref(false);
const selectedCard = ref<PathwayCenterCard | null>(null);
const exportingReport = ref(false);
const generatingPlanningTasks = ref(false);

const selectedStudent = computed(
  () =>
    studentOptions.value.find((item) => item.id === selectedStudentId.value) ??
    null,
);
const cards = computed(() =>
  buildPathwayCenterCards(evaluations.value, pathways.value),
);
const profileSummary = computed(() =>
  buildPathwayProfileSummary(profile.value),
);
const aggregatedGaps = computed(() =>
  collectStudentPathwayGaps(evaluations.value),
);
const statusSummary = computed(() =>
  summarizePathwayStatuses(evaluations.value),
);
const statusSummaryCopy = computed(() =>
  buildStatusSummaryCopy(statusSummary.value),
);
const publicationHighlights = computed(() =>
  buildPublicationStatusHighlights(dataHealth.value),
);
const nextActions = computed(() =>
  buildPathwayCenterActions(
    cards.value,
    aggregatedGaps.value,
    dataHealth.value,
  ),
);
const pageMeta = computed<PageMetaItem[]>(() => [
  { label: "学生", value: selectedStudent.value?.name || "未选择" },
  { label: "目标年份", value: targetYear.value },
  { label: "路径卡", value: cards.value.length },
  { label: "P0 缺口", value: dataHealth.value?.gaps.length ?? "-" },
]);
const pageStatCards = computed<StatCardItem[]>(() => [
  {
    label: "路径卡",
    value: cards.value.length,
    help: statusSummaryCopy.value,
    tone: cards.value.length ? "primary" : "neutral",
  },
  {
    label: "材料缺口",
    value: aggregatedGaps.value.length,
    help: aggregatedGaps.value.length
      ? "优先处理影响路径最多的材料。"
      : "暂无集中材料缺口。",
    tone: aggregatedGaps.value.length ? "warning" : "success",
  },
  {
    label: "下一步行动",
    value: nextActions.value.length,
    help: "由路径评估、材料缺口和数据风险自动汇总。",
    tone: nextActions.value.length ? "info" : "neutral",
  },
  {
    label: "P0 缺口",
    value: dataHealth.value?.gaps.length ?? "-",
    help: dataHealth.value?.summary || "刷新后读取当前本地库状态。",
    tone: dataHealth.value?.gaps.length ? "warning" : "success",
  },
]);

async function loadStudents(): Promise<void> {
  const payload = await apiRequest<StudentListResponse>(
    "/api/students?page=1&page_size=1000",
  );
  studentOptions.value = payload.items;
  const queryStudentId = Number(route.query.student_id);
  if (
    queryStudentId &&
    payload.items.some((item) => item.id === queryStudentId)
  ) {
    selectedStudentId.value = queryStudentId;
  } else if (!selectedStudentId.value && payload.items.length) {
    selectedStudentId.value = payload.items[0].id;
  }
}

async function loadPathways(): Promise<void> {
  pathways.value = await apiRequest<GaokaoPathwayRead[]>(
    "/api/gaokao/pathways?province=山东",
  );
}

async function loadDataHealth(): Promise<void> {
  dataHealth.value = await apiRequest<ShandongRecommendationDataHealth>(
    "/api/gaokao/data-health",
  );
}

async function refreshEvaluations(): Promise<void> {
  if (!selectedStudentId.value) {
    profile.value = null;
    evaluations.value = [];
    return;
  }
  evaluating.value = true;
  errorMessage.value = null;
  try {
    const payload = await apiRequest<StudentPathwayEvaluationResponse>(
      `/api/gaokao/students/${selectedStudentId.value}/pathway-evaluations/preview?target_year=${targetYear.value}&province=山东`,
      { method: "POST" },
    );
    profile.value = payload.profile;
    evaluations.value = payload.evaluations;
  } catch (error) {
    errorMessage.value = formatUserActionError(
      "刷新山东升学路径评估",
      error,
      "先确认学生画像和路径规则已装载，再重新刷新。",
    );
  } finally {
    evaluating.value = false;
  }
}

async function reloadAll(): Promise<void> {
  loading.value = true;
  errorMessage.value = null;
  try {
    await Promise.all([loadStudents(), loadPathways(), loadDataHealth()]);
    await refreshEvaluations();
  } catch (error) {
    errorMessage.value = formatUserActionError(
      "加载山东升学方案中心",
      error,
      "确认本地服务已启动，再刷新本页。",
    );
  } finally {
    loading.value = false;
  }
}

async function handleStudentChange(): Promise<void> {
  await refreshEvaluations();
}

function openStudentProfile(): void {
  if (!selectedStudentId.value) return;
  router.push(`/students/${selectedStudentId.value}`);
}

function openRecommendationWorkbench(): void {
  router.push("/recommendations");
  ElMessage.info(
    "进入高考志愿页后，请打开“山东普通类推荐”页签继续查看冲稳保候选。",
  );
}

function openPathwayDetail(card: PathwayCenterCard): void {
  selectedCard.value = card;
  detailDrawerVisible.value = true;
}

function buildCurrentReportPayload() {
  return buildGaokaoPathwayReportPayload({
    student: selectedStudent.value,
    targetYear: targetYear.value,
    profileSummary: profileSummary.value,
    cards: cards.value,
    materialGaps: aggregatedGaps.value,
    nextActions: nextActions.value,
    publicationStatus: publicationHighlights.value,
    dataHealth: dataHealth.value,
  });
}

function openPathwayReportPrintPreview(): void {
  if (!selectedStudentId.value || !cards.value.length) {
    ElMessage.warning("请先选择学生并刷新升学路径评估后再打印报告。");
    return;
  }
  const storageKey = `${GAOKAO_PATHWAY_PRINT_STORAGE_PREFIX}${Date.now()}`;
  window.localStorage.setItem(
    storageKey,
    JSON.stringify(buildCurrentReportPayload()),
  );
  openFile(gaokaoPathwayPrintPreviewPath(storageKey));
}

async function exportPathwayReport(): Promise<void> {
  if (!selectedStudentId.value || !cards.value.length) {
    ElMessage.warning("请先选择学生并刷新升学路径评估后再导出报告。");
    return;
  }
  try {
    exportingReport.value = true;
    const report = buildCurrentReportPayload();
    const result = await apiRequest<ExportRecord>(
      "/api/reports/gaokao-pathway/export",
      {
        method: "POST",
        body: JSON.stringify({
          report_name: buildGaokaoPathwayReportName(report),
          report,
        }),
      },
    );
    openFile(result.download_url);
    ElMessage.success("山东升学路径规划报告已生成");
  } catch (error) {
    ElMessage.error(
      formatUserActionError(
        "导出山东升学路径规划报告",
        error,
        "先确认路径评估结果仍在页面中，再重新点击导出。",
      ),
    );
  } finally {
    exportingReport.value = false;
  }
}

async function generatePlanningTasks(): Promise<void> {
  if (!selectedStudentId.value) {
    ElMessage.warning("请先选择学生后再生成规划任务。");
    return;
  }
  try {
    generatingPlanningTasks.value = true;
    const result = await apiRequest<{
      created_count: number;
      skipped_count: number;
    }>("/api/planning/tasks/bulk-create-from-pathway", {
      method: "POST",
      body: JSON.stringify({
        student_id: selectedStudentId.value,
        target_year: targetYear.value,
        include_material_gaps: true,
        include_review_tasks: true,
      }),
    });
    ElMessage.success(
      `已生成 ${result.created_count} 项规划任务，跳过 ${result.skipped_count} 项已有任务`,
    );
    router.push(`/students/${selectedStudentId.value}?tab=planning`);
  } catch (error) {
    ElMessage.error(
      formatUserActionError(
        "生成升学规划任务",
        error,
        "请先确认学生画像和路径评估已加载，再重新生成。",
      ),
    );
  } finally {
    generatingPlanningTasks.value = false;
  }
}

function formatRuleLine(rule: StudentPathwayRuleEvaluation): string {
  return rule.message ? `${rule.rule_name}：${rule.message}` : rule.rule_name;
}

function publicationTagType(
  status: string,
): "success" | "warning" | "danger" | "info" | "primary" {
  if (status === "imported" || status === "published") return "success";
  if (
    status === "pending_official_release" ||
    status === "manual_review_required"
  )
    return "warning";
  if (status === "not_applicable") return "info";
  return "primary";
}

onMounted(reloadAll);
</script>

<style scoped>
.pathway-center-page {
  gap: 20px;
}

.pathway-filter-grid {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) 180px minmax(280px, 1.2fr);
  gap: 14px;
  align-items: end;
}

.pathway-filter-field,
.pathway-filter-copy {
  display: grid;
  gap: 8px;
}

.pathway-filter-field span,
.pathway-filter-copy strong {
  color: #31475a;
  font-size: 13px;
  font-weight: 700;
}

.pathway-filter-copy span {
  color: var(--text-muted);
  line-height: 1.6;
}

.year-field {
  min-width: 160px;
}

.pathway-overview-grid,
.pathway-bottom-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(360px, 0.9fr);
  gap: 18px;
}

.pathway-profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.pathway-profile-item {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border: 1px solid rgba(121, 139, 156, 0.16);
  border-radius: 8px;
  background: rgba(246, 249, 252, 0.82);
}

.pathway-profile-item.filled {
  border-color: rgba(48, 126, 104, 0.24);
  background: rgba(237, 248, 243, 0.88);
}

.pathway-profile-item span,
.pathway-card-head span,
.pathway-card-meta strong {
  color: var(--text-soft);
  font-size: 12px;
  font-weight: 700;
}

.pathway-profile-item strong {
  color: #25394d;
}

.pathway-gap-list,
.pathway-action-list {
  display: grid;
  gap: 10px;
}

.pathway-gap-row,
.pathway-action-card {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  border: 1px solid rgba(121, 139, 156, 0.14);
  border-radius: 8px;
  background: rgba(247, 250, 253, 0.84);
}

.pathway-gap-row div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.pathway-gap-row strong {
  color: #25394d;
}

.pathway-gap-row span {
  color: var(--text-muted);
  font-size: 12px;
}

.pathway-gap-row p,
.pathway-action-card p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.pathway-card-section {
  display: grid;
  gap: 14px;
}

.pathway-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.pathway-card {
  display: grid;
  gap: 14px;
  min-width: 0;
  padding: 20px;
  border: 1px solid rgba(121, 139, 156, 0.16);
  border-radius: 8px;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.98),
    rgba(247, 250, 253, 0.96)
  );
  box-shadow: var(--shadow-soft);
}

.pathway-card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.pathway-card-head h3 {
  margin: 4px 0 0;
  color: #203549;
  font-size: 19px;
}

.pathway-card-summary {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.6;
}

.pathway-card-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.pathway-card-meta span {
  display: grid;
  gap: 4px;
  min-width: 0;
  color: #30475c;
  font-size: 13px;
}

.pathway-card-body {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.pathway-card-body h4,
.pathway-detail-section h4 {
  margin: 0 0 8px;
  color: #23394d;
  font-size: 14px;
}

.pathway-card-body ul,
.pathway-detail-section ul,
.pathway-risk-list {
  margin: 0;
  padding-left: 18px;
  color: var(--text-muted);
  line-height: 1.7;
}

.pathway-card-alert {
  border-radius: 8px;
}

.pathway-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.compact-table {
  padding: 10px;
}

.pathway-risk-list {
  margin-top: 12px;
}

.pathway-detail-drawer {
  display: grid;
  gap: 18px;
}

.pathway-detail-head {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.pathway-detail-drawer p {
  margin: 0;
  color: var(--text-muted);
  line-height: 1.7;
}

.pathway-detail-section {
  display: grid;
  gap: 10px;
}

.pathway-rule-group {
  display: grid;
  gap: 8px;
  padding: 12px 14px;
  border: 1px solid rgba(121, 139, 156, 0.14);
  border-radius: 8px;
  background: rgba(247, 250, 253, 0.82);
}

.pathway-rule-group strong {
  color: #25394d;
}

@media (max-width: 960px) {
  .pathway-filter-grid,
  .pathway-overview-grid,
  .pathway-bottom-grid,
  .pathway-card-body,
  .pathway-card-meta {
    grid-template-columns: 1fr;
  }
}
</style>
