<template>
  <AppPage
    title="知识库"
    eyebrow="教学业务 / 知识库"
    description="维护题分明细归一所需的标准知识点、阅卷平台别名和错因标签。"
    :meta="pageMeta"
  >
    <template #actions>
      <div class="action-row">
        <ElButton @click="openFile('/api/system/templates/knowledge_base_import_template.xlsx/download')">
          模板下载
        </ElButton>
        <ElUpload
          :show-file-list="false"
          :auto-upload="false"
          :disabled="importing"
          :on-change="handleImport"
          accept=".xlsx,.xls"
        >
          <ElButton type="primary" :loading="importing" :disabled="importing">导入知识库</ElButton>
        </ElUpload>
      </div>
    </template>

    <AppStatGrid :items="cards" :columns="4" />

    <section v-if="referenceLoadError || loadError" class="knowledge-status-stack">
      <ElAlert
        v-if="referenceLoadError"
        type="warning"
        title="知识库基础选项加载失败"
        show-icon
        :closable="false"
      >
        <template #default>
          <div class="knowledge-alert-body">
            <span>{{ referenceLoadError }}</span>
            <ElButton link type="primary" :loading="referenceLoading" @click="loadReferenceOptions">
              重新加载基础选项
            </ElButton>
          </div>
        </template>
      </ElAlert>
      <ElAlert
        v-if="loadError"
        type="error"
        title="知识库数据加载失败"
        show-icon
        :closable="false"
      >
        <template #default>
          <div class="knowledge-alert-body">
            <span>{{ loadError }}</span>
            <ElButton link type="primary" :loading="loading" @click="loadKnowledgeBase">
              重新加载知识库
            </ElButton>
          </div>
        </template>
      </ElAlert>
    </section>

    <AppFilterBar
      title="筛选与维护"
      description="按学科查看标准知识点和平台别名；错因标签为全局口径，供题分导入和补弱任务复用。"
      sticky
    >
      <div class="knowledge-filter-grid">
        <ElSelect
          v-model="selectedSubjectId"
          clearable
          filterable
          placeholder="全部学科"
          :loading="referenceLoading"
          :disabled="referenceLoading"
        >
          <ElOption
            v-for="subject in referenceStore.subjects"
            :key="subject.id"
            :label="subject.name"
            :value="subject.id"
          />
        </ElSelect>
      </div>
      <template #actions>
        <ElButton :loading="loading" @click="loadKnowledgeBase">刷新</ElButton>
        <ElButton type="primary" :disabled="referenceLoading" @click="openPointDialog()">新增知识点</ElButton>
        <ElButton :disabled="referenceLoading || !points.length" @click="openAliasDialog()">新增别名</ElButton>
        <ElButton @click="openErrorTagDialog()">新增错因标签</ElButton>
      </template>
      <ImportFeedbackPanel :result="importResult" />
    </AppFilterBar>

    <ElTabs v-model="activeTab" class="knowledge-tabs">
      <ElTabPane label="标准知识点" name="points">
        <AppTableShell
          title="知识点树"
          description="路径使用“模块 > 子模块 > 知识点”口径，题分导入会优先归一到这里。"
        >
          <template #actions>
            <span class="panel-caption">共 {{ points.length }} 条</span>
          </template>
          <ElTable :data="points" stripe v-loading="loading" row-key="id">
            <ElTableColumn prop="path" label="知识点路径" min-width="240" />
            <ElTableColumn label="学科" width="110">
              <template #default="{ row }">
                {{ subjectName(row.subject_id) }}
              </template>
            </ElTableColumn>
            <ElTableColumn prop="code" label="编码" width="120" />
            <ElTableColumn label="来源" width="110">
              <template #default="{ row }">
                <ElTag effect="light">{{ sourceTypeLabel(row.source_type) }}</ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="description" label="说明" min-width="180" show-overflow-tooltip />
            <ElTableColumn label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <ElButton link type="primary" @click="openPointDialog(row)">编辑</ElButton>
                <ElButton
                  link
                  type="danger"
                  :loading="deletingPointId === row.id"
                  @click="deletePoint(row)"
                >
                  停用
                </ElButton>
              </template>
            </ElTableColumn>
            <template #empty>
              <ElEmpty :description="pointsEmptyDescription">
                <ElButton v-if="loadError" type="primary" plain :loading="loading" @click="loadKnowledgeBase">
                  重新加载知识点
                </ElButton>
              </ElEmpty>
            </template>
          </ElTable>
        </AppTableShell>
      </ElTabPane>

      <ElTabPane label="平台别名" name="aliases">
        <AppTableShell
          title="别名映射"
          description="把阅卷平台导出的不同写法归一到标准知识点，减少重复诊断。"
        >
          <template #actions>
            <span class="panel-caption">共 {{ aliases.length }} 条</span>
          </template>
          <ElTable :data="aliases" stripe v-loading="loading" row-key="id">
            <ElTableColumn prop="alias_name" label="平台别名" min-width="160" />
            <ElTableColumn prop="knowledge_point_path" label="标准知识点" min-width="240" />
            <ElTableColumn prop="subject_name" label="学科" width="110" />
            <ElTableColumn prop="note" label="说明" min-width="160" show-overflow-tooltip />
            <ElTableColumn label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <ElButton link type="primary" @click="openAliasDialog(row)">编辑</ElButton>
                <ElButton
                  link
                  type="danger"
                  :loading="deletingAliasId === row.id"
                  @click="deleteAlias(row)"
                >
                  停用
                </ElButton>
              </template>
            </ElTableColumn>
            <template #empty>
              <ElEmpty :description="aliasesEmptyDescription">
                <ElButton v-if="loadError" type="primary" plain :loading="loading" @click="loadKnowledgeBase">
                  重新加载别名
                </ElButton>
              </ElEmpty>
            </template>
          </ElTable>
        </AppTableShell>
      </ElTabPane>

      <ElTabPane label="错因标签" name="errorTags">
        <AppTableShell
          title="错因标签"
          description="用于题分明细导入后的错因聚合，可维护学校自己的补弱分类。"
        >
          <template #actions>
            <span class="panel-caption">共 {{ errorTags.length }} 条</span>
          </template>
          <ElTable :data="errorTags" stripe v-loading="loading" row-key="id">
            <ElTableColumn prop="name" label="标签" min-width="140" />
            <ElTableColumn prop="description" label="说明" min-width="240" show-overflow-tooltip />
            <ElTableColumn label="类型" width="100">
              <template #default="{ row }">
                <ElTag :type="row.is_builtin ? 'info' : 'success'" effect="light">
                  {{ row.is_builtin ? "内置" : "自定义" }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="sort_order" label="排序" width="90" />
            <ElTableColumn label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <ElButton link type="primary" @click="openErrorTagDialog(row)">编辑</ElButton>
                <ElButton
                  link
                  type="danger"
                  :disabled="row.is_builtin"
                  :loading="deletingErrorTagId === row.id"
                  @click="deleteErrorTag(row)"
                >
                  停用
                </ElButton>
              </template>
            </ElTableColumn>
            <template #empty>
              <ElEmpty :description="errorTagsEmptyDescription">
                <ElButton v-if="loadError" type="primary" plain :loading="loading" @click="loadKnowledgeBase">
                  重新加载错因标签
                </ElButton>
              </ElEmpty>
            </template>
          </ElTable>
        </AppTableShell>
      </ElTabPane>
    </ElTabs>

    <ElDialog
      v-model="pointDialogVisible"
      :title="editingPointId ? '编辑知识点' : '新增知识点'"
      width="620px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <ElForm label-position="top">
        <div class="knowledge-form-grid">
          <ElFormItem label="学科">
            <ElSelect
              v-model="pointForm.subject_id"
              filterable
              :loading="referenceLoading"
              :disabled="referenceLoading"
              @change="handlePointSubjectChanged"
            >
              <ElOption
                v-for="subject in referenceStore.subjects"
                :key="subject.id"
                :label="subject.name"
                :value="subject.id"
              />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="父级知识点">
            <ElSelect v-model="pointForm.parent_id" clearable filterable :disabled="loading">
              <ElOption
                v-for="point in pointParentOptions"
                :key="point.id"
                :label="point.path ?? point.name"
                :value="point.id"
              />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="知识点名称">
            <ElInput v-model="pointForm.name" />
          </ElFormItem>
          <ElFormItem label="编码">
            <ElInput v-model="pointForm.code" />
          </ElFormItem>
          <ElFormItem label="排序">
            <ElInputNumber v-model="pointForm.sort_order" :min="0" :max="9999" style="width: 100%" />
          </ElFormItem>
          <ElFormItem label="来源">
            <ElInput v-model="pointForm.source_type" />
          </ElFormItem>
        </div>
        <ElFormItem label="说明">
          <ElInput v-model="pointForm.description" type="textarea" :rows="3" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="pointDialogVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="saving" @click="savePoint">保存</ElButton>
      </template>
    </ElDialog>

    <ElDialog
      v-model="aliasDialogVisible"
      :title="editingAliasId ? '编辑别名' : '新增别名'"
      width="620px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <ElForm label-position="top">
        <ElFormItem label="学科">
          <ElSelect
            v-model="aliasForm.subject_id"
            filterable
            :loading="referenceLoading"
            :disabled="referenceLoading"
            @change="handleAliasSubjectChanged"
          >
            <ElOption
              v-for="subject in referenceStore.subjects"
              :key="subject.id"
              :label="subject.name"
              :value="subject.id"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="标准知识点">
          <ElSelect v-model="aliasForm.knowledge_point_id" filterable :disabled="loading || !aliasPointOptions.length">
            <ElOption
              v-for="point in aliasPointOptions"
              :key="point.id"
              :label="point.path ?? point.name"
              :value="point.id"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="平台别名">
          <ElInput v-model="aliasForm.alias_name" />
        </ElFormItem>
        <ElFormItem label="说明">
          <ElInput v-model="aliasForm.note" type="textarea" :rows="3" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="aliasDialogVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="saving" @click="saveAlias">保存</ElButton>
      </template>
    </ElDialog>

    <ElDialog
      v-model="errorTagDialogVisible"
      :title="editingErrorTagId ? '编辑错因标签' : '新增错因标签'"
      width="540px"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <ElForm label-position="top">
        <ElFormItem label="标签名称">
          <ElInput v-model="errorTagForm.name" />
        </ElFormItem>
        <ElFormItem label="说明">
          <ElInput v-model="errorTagForm.description" type="textarea" :rows="3" />
        </ElFormItem>
        <ElFormItem label="排序">
          <ElInputNumber v-model="errorTagForm.sort_order" :min="0" :max="9999" style="width: 100%" />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="errorTagDialogVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="saving" @click="saveErrorTag">保存</ElButton>
      </template>
    </ElDialog>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { UploadFile } from "element-plus";

import { apiRequest, openFile, uploadFile } from "../api/client";
import ImportFeedbackPanel from "../components/common/ImportFeedbackPanel.vue";
import {
  AppFilterBar,
  AppPage,
  AppStatGrid,
  AppTableShell,
  type PageMetaItem,
  type StatCardItem,
} from "../components/ui";
import { useReferenceStore } from "../stores/reference";
import type { ImportFeedbackResult } from "../utils/importFeedback";
import { formatUserActionError } from "../utils/userFeedback";

interface KnowledgePoint {
  id: number;
  subject_id: number;
  parent_id?: number | null;
  name: string;
  code?: string | null;
  description?: string | null;
  sort_order: number;
  source_type: string;
  is_active: boolean;
  path?: string | null;
}

interface KnowledgeAlias {
  id: number;
  subject_id: number;
  subject_name?: string | null;
  knowledge_point_id: number;
  knowledge_point_name?: string | null;
  knowledge_point_path?: string | null;
  alias_name: string;
  source_type: string;
  note?: string | null;
  is_active: boolean;
}

interface ErrorReasonTag {
  id: number;
  name: string;
  description?: string | null;
  sort_order: number;
  is_builtin: boolean;
  is_active: boolean;
}

interface KnowledgeImportResult extends ImportFeedbackResult {
  point_count?: number;
  alias_count?: number;
  error_tag_count?: number;
}

const referenceStore = useReferenceStore();
const activeTab = ref("points");
const selectedSubjectId = ref<number | null>(null);
const points = ref<KnowledgePoint[]>([]);
const aliases = ref<KnowledgeAlias[]>([]);
const errorTags = ref<ErrorReasonTag[]>([]);
const loading = ref(false);
const loadError = ref("");
const referenceLoading = ref(false);
const referenceLoadError = ref("");
const saving = ref(false);
const importing = ref(false);
const deletingPointId = ref<number | null>(null);
const deletingAliasId = ref<number | null>(null);
const deletingErrorTagId = ref<number | null>(null);
const importResult = ref<KnowledgeImportResult | null>(null);

const pointDialogVisible = ref(false);
const aliasDialogVisible = ref(false);
const errorTagDialogVisible = ref(false);
const editingPointId = ref<number | null>(null);
const editingAliasId = ref<number | null>(null);
const editingErrorTagId = ref<number | null>(null);

const pointForm = reactive({
  subject_id: null as number | null,
  parent_id: null as number | null,
  name: "",
  code: "",
  description: "",
  sort_order: 0,
  source_type: "manual",
  is_active: true,
});

const aliasForm = reactive({
  subject_id: null as number | null,
  knowledge_point_id: null as number | null,
  alias_name: "",
  source_type: "manual",
  note: "",
  is_active: true,
});

const errorTagForm = reactive({
  name: "",
  description: "",
  sort_order: 0,
  is_builtin: false,
  is_active: true,
});

const selectedSubjectName = computed(() => {
  if (!selectedSubjectId.value) return "全部学科";
  return subjectName(selectedSubjectId.value);
});

const pointParentOptions = computed(() =>
  points.value.filter(
    (point) => point.subject_id === pointForm.subject_id && point.id !== editingPointId.value,
  ),
);

const aliasPointOptions = computed(() =>
  points.value.filter((point) => point.subject_id === aliasForm.subject_id),
);

const pageMeta = computed<PageMetaItem[]>(() => [
  { label: "当前学科", value: selectedSubjectName.value },
  { label: "知识点", value: points.value.length },
  { label: "别名", value: aliases.value.length },
  { label: "错因标签", value: errorTags.value.length },
]);

const cards = computed<StatCardItem[]>(() => [
  {
    label: "标准知识点",
    value: points.value.length,
    help: "题分明细和补弱任务使用的标准路径。",
    tone: "primary",
  },
  {
    label: "平台别名",
    value: aliases.value.length,
    help: "把阅卷平台不同写法归一到标准知识点。",
    tone: "success",
  },
  {
    label: "错因标签",
    value: errorTags.value.length,
    help: "用于聚合概念、审题、计算等失分原因。",
    tone: "warning",
  },
  {
    label: "内置标签",
    value: errorTags.value.filter((item) => item.is_builtin).length,
    help: "系统默认提供，避免题分导入后没有基础分类。",
    tone: "neutral",
  },
]);

const pointsEmptyDescription = computed(() => {
  if (loading.value) return "正在加载知识点";
  if (loadError.value) return "知识点加载失败，请重新加载。";
  return selectedSubjectId.value ? "当前学科暂无知识点" : "暂无知识点";
});

const aliasesEmptyDescription = computed(() => {
  if (loading.value) return "正在加载平台别名";
  if (loadError.value) return "平台别名加载失败，请重新加载。";
  return selectedSubjectId.value ? "当前学科暂无平台别名" : "暂无平台别名";
});

const errorTagsEmptyDescription = computed(() => {
  if (loading.value) return "正在加载错因标签";
  if (loadError.value) return "错因标签加载失败，请重新加载。";
  return "暂无错因标签";
});

function subjectName(subjectId?: number | null): string {
  if (!subjectId) return "-";
  return referenceStore.subjects.find((subject) => subject.id === subjectId)?.name ?? String(subjectId);
}

function sourceTypeLabel(sourceType?: string | null): string {
  const mapping: Record<string, string> = {
    manual: "手工",
    knowledge_import: "导入",
    import_path: "路径导入",
    import_flat: "自动归类",
    system: "系统",
  };
  return mapping[sourceType ?? ""] ?? (sourceType || "-");
}

function defaultSubjectId(): number | null {
  return selectedSubjectId.value ?? referenceStore.subjects[0]?.id ?? null;
}

async function loadReferenceOptions(): Promise<void> {
  referenceLoading.value = true;
  referenceLoadError.value = "";
  try {
    await referenceStore.loadCore();
  } catch (error) {
    referenceLoadError.value = formatUserActionError("加载知识库基础选项", error, "请重新加载基础选项后再维护知识点。");
  } finally {
    referenceLoading.value = false;
  }
}

async function loadKnowledgeBase(): Promise<void> {
  loading.value = true;
  loadError.value = "";
  try {
    const subjectQuery = selectedSubjectId.value ? `?subject_id=${selectedSubjectId.value}` : "";
    const [pointPayload, aliasPayload, errorTagPayload] = await Promise.all([
      apiRequest<KnowledgePoint[]>(`/api/knowledge/points${subjectQuery}`),
      apiRequest<KnowledgeAlias[]>(`/api/knowledge/aliases${subjectQuery}`),
      apiRequest<ErrorReasonTag[]>("/api/knowledge/error-tags"),
    ]);
    points.value = pointPayload;
    aliases.value = aliasPayload;
    errorTags.value = errorTagPayload;
  } catch (error) {
    const message = formatUserActionError("加载知识库", error, "请重新加载知识库或调整学科筛选后重试。");
    points.value = [];
    aliases.value = [];
    errorTags.value = [];
    loadError.value = message;
    ElMessage.error(message);
  } finally {
    loading.value = false;
  }
}

function resetPointForm(): void {
  Object.assign(pointForm, {
    subject_id: defaultSubjectId(),
    parent_id: null,
    name: "",
    code: "",
    description: "",
    sort_order: 0,
    source_type: "manual",
    is_active: true,
  });
}

function resetAliasForm(): void {
  const subjectId = defaultSubjectId();
  Object.assign(aliasForm, {
    subject_id: subjectId,
    knowledge_point_id: points.value.find((point) => point.subject_id === subjectId)?.id ?? null,
    alias_name: "",
    source_type: "manual",
    note: "",
    is_active: true,
  });
}

function resetErrorTagForm(): void {
  Object.assign(errorTagForm, {
    name: "",
    description: "",
    sort_order: errorTags.value.length + 1,
    is_builtin: false,
    is_active: true,
  });
}

function openPointDialog(point?: KnowledgePoint): void {
  editingPointId.value = point?.id ?? null;
  resetPointForm();
  if (point) {
    Object.assign(pointForm, {
      subject_id: point.subject_id,
      parent_id: point.parent_id ?? null,
      name: point.name,
      code: point.code ?? "",
      description: point.description ?? "",
      sort_order: point.sort_order,
      source_type: point.source_type,
      is_active: point.is_active,
    });
  }
  pointDialogVisible.value = true;
}

function openAliasDialog(alias?: KnowledgeAlias): void {
  editingAliasId.value = alias?.id ?? null;
  resetAliasForm();
  if (alias) {
    Object.assign(aliasForm, {
      subject_id: alias.subject_id,
      knowledge_point_id: alias.knowledge_point_id,
      alias_name: alias.alias_name,
      source_type: alias.source_type,
      note: alias.note ?? "",
      is_active: alias.is_active,
    });
  }
  aliasDialogVisible.value = true;
}

function openErrorTagDialog(tag?: ErrorReasonTag): void {
  editingErrorTagId.value = tag?.id ?? null;
  resetErrorTagForm();
  if (tag) {
    Object.assign(errorTagForm, {
      name: tag.name,
      description: tag.description ?? "",
      sort_order: tag.sort_order,
      is_builtin: tag.is_builtin,
      is_active: tag.is_active,
    });
  }
  errorTagDialogVisible.value = true;
}

function handlePointSubjectChanged(): void {
  if (!pointParentOptions.value.some((point) => point.id === pointForm.parent_id)) {
    pointForm.parent_id = null;
  }
}

function handleAliasSubjectChanged(): void {
  aliasForm.knowledge_point_id = aliasPointOptions.value[0]?.id ?? null;
}

async function savePoint(): Promise<void> {
  if (!pointForm.subject_id || !pointForm.name.trim()) {
    ElMessage.warning("学科和知识点名称不能为空");
    return;
  }
  saving.value = true;
  try {
    const payload = {
      ...pointForm,
      code: pointForm.code.trim() || null,
      description: pointForm.description.trim() || null,
      source_type: pointForm.source_type.trim() || "manual",
    };
    const path = editingPointId.value ? `/api/knowledge/points/${editingPointId.value}` : "/api/knowledge/points";
    await apiRequest<KnowledgePoint>(path, {
      method: editingPointId.value ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    ElMessage.success("知识点已保存");
    pointDialogVisible.value = false;
    await loadKnowledgeBase();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

async function saveAlias(): Promise<void> {
  if (!aliasForm.subject_id || !aliasForm.knowledge_point_id || !aliasForm.alias_name.trim()) {
    ElMessage.warning("学科、标准知识点和平台别名不能为空");
    return;
  }
  saving.value = true;
  try {
    const payload = {
      ...aliasForm,
      alias_name: aliasForm.alias_name.trim(),
      source_type: aliasForm.source_type.trim() || "manual",
      note: aliasForm.note.trim() || null,
    };
    const path = editingAliasId.value ? `/api/knowledge/aliases/${editingAliasId.value}` : "/api/knowledge/aliases";
    await apiRequest<KnowledgeAlias>(path, {
      method: editingAliasId.value ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    ElMessage.success("别名已保存");
    aliasDialogVisible.value = false;
    await loadKnowledgeBase();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

async function saveErrorTag(): Promise<void> {
  if (!errorTagForm.name.trim()) {
    ElMessage.warning("错因标签名称不能为空");
    return;
  }
  saving.value = true;
  try {
    const payload = {
      ...errorTagForm,
      name: errorTagForm.name.trim(),
      description: errorTagForm.description.trim() || null,
    };
    const path = editingErrorTagId.value
      ? `/api/knowledge/error-tags/${editingErrorTagId.value}`
      : "/api/knowledge/error-tags";
    await apiRequest<ErrorReasonTag>(path, {
      method: editingErrorTagId.value ? "PUT" : "POST",
      body: JSON.stringify(payload),
    });
    ElMessage.success("错因标签已保存");
    errorTagDialogVisible.value = false;
    await loadKnowledgeBase();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

async function confirmDisable(message: string): Promise<boolean> {
  try {
    await ElMessageBox.confirm(message, "确认停用", {
      type: "warning",
      confirmButtonText: "停用",
      cancelButtonText: "取消",
    });
    return true;
  } catch {
    return false;
  }
}

async function deletePoint(point: KnowledgePoint): Promise<void> {
  if (!(await confirmDisable(`确认停用知识点“${point.path ?? point.name}”？`))) return;
  deletingPointId.value = point.id;
  try {
    await apiRequest(`/api/knowledge/points/${point.id}`, { method: "DELETE" });
    ElMessage.success("知识点已停用");
    await loadKnowledgeBase();
  } catch (error) {
    ElMessage.error(formatUserActionError("停用知识点", error, "请稍后重试。"));
  } finally {
    deletingPointId.value = null;
  }
}

async function deleteAlias(alias: KnowledgeAlias): Promise<void> {
  if (!(await confirmDisable(`确认停用别名“${alias.alias_name}”？`))) return;
  deletingAliasId.value = alias.id;
  try {
    await apiRequest(`/api/knowledge/aliases/${alias.id}`, { method: "DELETE" });
    ElMessage.success("别名已停用");
    await loadKnowledgeBase();
  } catch (error) {
    ElMessage.error(formatUserActionError("停用别名", error, "请稍后重试。"));
  } finally {
    deletingAliasId.value = null;
  }
}

async function deleteErrorTag(tag: ErrorReasonTag): Promise<void> {
  if (tag.is_builtin) return;
  if (!(await confirmDisable(`确认停用错因标签“${tag.name}”？`))) return;
  deletingErrorTagId.value = tag.id;
  try {
    await apiRequest(`/api/knowledge/error-tags/${tag.id}`, { method: "DELETE" });
    ElMessage.success("错因标签已停用");
    await loadKnowledgeBase();
  } catch (error) {
    ElMessage.error(formatUserActionError("停用错因标签", error, "请稍后重试。"));
  } finally {
    deletingErrorTagId.value = null;
  }
}

async function handleImport(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw || importing.value) return;
  importing.value = true;
  importResult.value = null;
  try {
    importResult.value = await uploadFile<KnowledgeImportResult>("/api/knowledge/import", uploadFileItem.raw);
    ElMessage({
      type: importResult.value.failed_rows ? "warning" : "success",
      message: importResult.value.message,
    });
    await loadKnowledgeBase();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "导入失败");
  } finally {
    importing.value = false;
  }
}

onMounted(async () => {
  await Promise.all([loadReferenceOptions(), loadKnowledgeBase()]);
});

watch(selectedSubjectId, () => {
  void loadKnowledgeBase();
});
</script>

<style scoped>
.knowledge-filter-grid {
  display: grid;
  grid-template-columns: minmax(220px, 320px);
  gap: 12px;
}

.knowledge-tabs {
  margin-top: 18px;
}

.knowledge-status-stack {
  display: grid;
  gap: 12px;
}

.knowledge-alert-body {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  align-items: center;
}

.panel-caption {
  color: #6d8194;
  font-size: 13px;
}

.knowledge-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

@media (max-width: 900px) {
  .knowledge-form-grid,
  .knowledge-filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
