<template>
  <section class="soft-card crud-section">
    <div class="crud-head">
      <div>
        <h3>{{ title }}</h3>
        <p>{{ description }}</p>
      </div>
      <el-button type="primary" :disabled="crudActionsDisabled" @click="openCreate">新增</el-button>
    </div>

    <el-alert
      v-if="disabledReason"
      class="crud-alert"
      type="warning"
      show-icon
      :closable="false"
      :title="disabledReason"
    />

    <el-alert
      v-if="loadError"
      class="crud-alert"
      type="error"
      show-icon
      :closable="false"
      :title="loadError"
    >
      <template #default>
        <el-button size="small" type="danger" plain :loading="loading" @click="loadData(true)">
          重新加载
        </el-button>
      </template>
    </el-alert>

    <div class="table-shell">
      <el-table :data="items" stripe v-loading="loading">
        <el-table-column
          v-for="column in columns"
          :key="column.prop"
          :label="column.label"
          :prop="column.prop"
          min-width="120"
        />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="crudActionsDisabled" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :description="emptyDescription">
            <el-button v-if="loadError" type="primary" plain :loading="loading" @click="loadData(true)">
              重新加载
            </el-button>
          </el-empty>
        </template>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="620px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form label-width="110px" :disabled="submitting">
        <el-alert
          v-if="formActionError"
          class="crud-alert"
          type="error"
          show-icon
          :closable="false"
          :title="formActionError"
        />
        <el-form-item
          v-for="field in fields"
          :key="field.prop"
          :label="field.label"
          :required="field.required"
        >
          <el-input
            v-if="field.type === 'text'"
            v-model="formState[field.prop]"
            :placeholder="field.placeholder"
            :disabled="submitting"
          />
          <el-input-number
            v-else-if="field.type === 'number'"
            v-model="formState[field.prop]"
            :min="field.min ?? 0"
            :max="field.max ?? 9999"
            :disabled="submitting"
            style="width: 100%"
          />
          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="formState[field.prop]"
            type="date"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            placeholder="请选择日期"
            :disabled="submitting"
            style="width: 100%"
          />
          <el-select
            v-else-if="field.type === 'select'"
            v-model="formState[field.prop]"
            clearable
            filterable
            :disabled="submitting"
            style="width: 100%"
          >
            <el-option
              v-for="option in field.options ?? []"
              :key="String(option.value)"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-switch
            v-else-if="field.type === 'switch'"
            v-model="formState[field.prop]"
            :disabled="submitting"
          />
          <el-input
            v-else
            v-model="formState[field.prop]"
            :placeholder="field.placeholder"
            :disabled="submitting"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button :disabled="submitting" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          保存
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest } from "../api/client";
import { formatUserActionError } from "../utils/userFeedback";

interface CrudColumn {
  label: string;
  prop: string;
}

interface CrudFieldOption {
  label: string;
  value: string | number | boolean;
}

interface CrudField {
  label: string;
  prop: string;
  type: "text" | "number" | "date" | "select" | "switch";
  placeholder?: string;
  options?: CrudFieldOption[];
  min?: number;
  max?: number;
  defaultValue?: string | number | boolean | null;
  required?: boolean;
}

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    endpoint: string;
    updateEndpoint?: string;
    columns: CrudColumn[];
    fields: CrudField[];
    disabled?: boolean;
    disabledReason?: string;
  }>(),
  {
    description: "",
    updateEndpoint: "",
    disabled: false,
    disabledReason: "",
  },
);

const emit = defineEmits<{
  saved: [];
}>();

const items = ref<Record<string, unknown>[]>([]);
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const loading = ref(false);
const loadError = ref("");
const submitting = ref(false);
const formActionError = ref("");
const formState = reactive<Record<string, unknown>>({});

const dialogTitle = computed(() => (editingId.value ? `编辑${props.title}` : `新增${props.title}`));
const effectiveUpdateEndpoint = computed(() => props.updateEndpoint || props.endpoint);
const crudActionsDisabled = computed(() => loading.value || submitting.value || props.disabled);
const emptyDescription = computed(() => {
  if (loading.value) return `正在加载${props.title}`;
  if (loadError.value) return `${props.title}加载失败，请重新加载。`;
  return "暂无数据";
});

async function loadData(showToast = false): Promise<void> {
  if (!props.endpoint) {
    items.value = [];
    return;
  }
  loading.value = true;
  loadError.value = "";
  formActionError.value = "";
  try {
    items.value = await apiRequest<Record<string, unknown>[]>(props.endpoint);
  } catch (error) {
    items.value = [];
    loadError.value = formatUserActionError(`加载${props.title}`, error, "检查本地服务状态后重新加载");
    if (showToast) {
      ElMessage.error(loadError.value);
    }
  } finally {
    loading.value = false;
  }
}

function resetForm(): void {
  props.fields.forEach((field) => {
    if (field.defaultValue !== undefined) {
      formState[field.prop] = field.defaultValue;
      return;
    }
    formState[field.prop] = field.type === "switch" ? false : null;
  });
}

function openCreate(): void {
  if (props.disabled) return;
  formActionError.value = "";
  editingId.value = null;
  resetForm();
  dialogVisible.value = true;
}

function openEdit(row: Record<string, unknown>): void {
  if (props.disabled) return;
  formActionError.value = "";
  editingId.value = Number(row.id);
  resetForm();
  props.fields.forEach((field) => {
    formState[field.prop] = row[field.prop] ?? null;
  });
  dialogVisible.value = true;
}

function handleDialogClosed(): void {
  editingId.value = null;
  formActionError.value = "";
  resetForm();
}

async function submitForm(): Promise<void> {
  formActionError.value = "";
  const missingField = props.fields.find((field) => {
    if (!field.required) return false;
    const value = formState[field.prop];
    return value == null || (typeof value === "string" && !value.trim());
  });
  if (missingField) {
    formActionError.value = `${missingField.label}不能为空`;
    ElMessage.warning(formActionError.value);
    return;
  }
  try {
    submitting.value = true;
    const payload = Object.fromEntries(
      Object.entries(formState).map(([key, value]) => [key, value ?? null]),
    );

    if (editingId.value) {
      await apiRequest(`${effectiveUpdateEndpoint.value}/${editingId.value}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } else {
      await apiRequest(props.endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
    ElMessage.success("保存成功");
    dialogVisible.value = false;
    await loadData(true);
    emit("saved");
  } catch (error) {
    formActionError.value = formatUserActionError(
      `保存${props.title}`,
      error,
      "检查填写内容是否完整并确认没有重复编码后重试",
    );
    ElMessage.error(formActionError.value);
  } finally {
    submitting.value = false;
  }
}

watch(
  () => props.endpoint,
  async () => {
    await loadData(false);
  },
  { immediate: true },
);

defineExpose({ loadData });
</script>

<style scoped>
.crud-section {
  padding: 22px;
}

.crud-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.crud-head h3 {
  margin: 0;
  font-size: 20px;
  color: #203549;
}

.crud-head p {
  margin: 8px 0 0;
  color: #6d8093;
  line-height: 1.6;
}

.crud-alert {
  margin-bottom: 14px;
}

@media (max-width: 900px) {
  .crud-head {
    flex-direction: column;
  }
}
</style>
