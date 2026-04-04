<template>
  <section class="soft-card crud-section">
    <div class="crud-head">
      <div>
        <h3>{{ title }}</h3>
        <p>{{ description }}</p>
      </div>
      <el-button type="primary" @click="openCreate">新增</el-button>
    </div>

    <div class="table-shell">
      <el-table :data="items" stripe>
        <el-table-column
          v-for="column in columns"
          :key="column.prop"
          :label="column.label"
          :prop="column.prop"
          min-width="120"
        />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-empty v-if="!items.length" description="暂无数据" />

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="620px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form label-width="110px">
        <el-form-item
          v-for="field in fields"
          :key="field.prop"
          :label="field.label"
        >
          <el-input
            v-if="field.type === 'text'"
            v-model="formState[field.prop]"
            :placeholder="field.placeholder"
          />
          <el-input-number
            v-else-if="field.type === 'number'"
            v-model="formState[field.prop]"
            :min="field.min ?? 0"
            :max="field.max ?? 9999"
            style="width: 100%"
          />
          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="formState[field.prop]"
            type="date"
            value-format="YYYY-MM-DD"
            format="YYYY-MM-DD"
            placeholder="请选择日期"
            style="width: 100%"
          />
          <el-select
            v-else-if="field.type === 'select'"
            v-model="formState[field.prop]"
            clearable
            filterable
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
          />
          <el-input
            v-else
            v-model="formState[field.prop]"
            :placeholder="field.placeholder"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
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
}

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    endpoint: string;
    updateEndpoint?: string;
    columns: CrudColumn[];
    fields: CrudField[];
  }>(),
  {
    description: "",
    updateEndpoint: "",
  },
);

const items = ref<Record<string, unknown>[]>([]);
const dialogVisible = ref(false);
const editingId = ref<number | null>(null);
const submitting = ref(false);
const formState = reactive<Record<string, unknown>>({});

const dialogTitle = computed(() => (editingId.value ? `编辑${props.title}` : `新增${props.title}`));
const effectiveUpdateEndpoint = computed(() => props.updateEndpoint || props.endpoint);

async function loadData(): Promise<void> {
  if (!props.endpoint) {
    items.value = [];
    return;
  }
  items.value = await apiRequest<Record<string, unknown>[]>(props.endpoint);
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
  editingId.value = null;
  resetForm();
  dialogVisible.value = true;
}

function openEdit(row: Record<string, unknown>): void {
  editingId.value = Number(row.id);
  resetForm();
  props.fields.forEach((field) => {
    formState[field.prop] = row[field.prop] ?? null;
  });
  dialogVisible.value = true;
}

function handleDialogClosed(): void {
  editingId.value = null;
  resetForm();
}

async function submitForm(): Promise<void> {
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
    await loadData();
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    submitting.value = false;
  }
}

watch(
  () => props.endpoint,
  async () => {
    await loadData();
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

@media (max-width: 900px) {
  .crud-head {
    flex-direction: column;
  }
}
</style>
