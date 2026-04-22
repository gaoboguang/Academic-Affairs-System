<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>推荐策略</h3>
        <p>把冲稳保阈值、白名单和黑名单做成可调配置，避免每次都靠临时人工备注修正。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('reload')">重载</el-button>
        <el-button type="primary" :loading="savingSettings" @click="emit('save-settings')">
          保存策略
        </el-button>
      </div>
    </div>

    <div class="strategy-card-grid">
      <article v-for="item in strategyCards" :key="item.label" class="strategy-card" :class="item.tone">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <p>{{ item.help }}</p>
      </article>
    </div>

    <div class="filter-grid strategy-filter-grid">
      <el-input-number
        v-model="settings.safe_ratio_max"
        :precision="2"
        :step="0.01"
        :min="0.1"
        :max="2"
        controls-position="right"
        style="width: 100%"
        placeholder="保底阈值"
      />
      <el-input-number
        v-model="settings.steady_ratio_max"
        :precision="2"
        :step="0.01"
        :min="0.1"
        :max="2"
        controls-position="right"
        style="width: 100%"
        placeholder="稳妥阈值"
      />
      <el-input-number
        v-model="settings.rush_ratio_max"
        :precision="2"
        :step="0.01"
        :min="0.1"
        :max="2.5"
        controls-position="right"
        style="width: 100%"
        placeholder="冲刺阈值"
      />
    </div>

    <div class="filter-grid strategy-filter-grid">
      <el-select
        v-model="settings.whitelist_college_ids"
        multiple
        collapse-tags
        clearable
        filterable
        placeholder="白名单院校"
      >
        <el-option
          v-for="college in collegeOptions"
          :key="college.id"
          :label="college.name"
          :value="college.id"
        />
      </el-select>
      <el-select
        v-model="settings.blacklist_college_ids"
        multiple
        collapse-tags
        clearable
        filterable
        placeholder="黑名单院校"
      >
        <el-option
          v-for="college in collegeOptions"
          :key="college.id"
          :label="college.name"
          :value="college.id"
        />
      </el-select>
    </div>

    <el-alert
      class="strategy-alert"
      title="白名单可突破地区和层级偏好限制，黑名单会被直接排除；同一院校不能同时存在于两个列表。"
      type="info"
      show-icon
      :closable="false"
    />

    <section class="strategy-preset-shell">
      <div class="section-head compact">
        <div>
          <h4>策略模板</h4>
          <p>把当前阈值和院校名单保存成模板，后面换学生或换考试时可以一键复用。</p>
        </div>
      </div>

      <div class="filter-grid strategy-filter-grid">
        <el-select
          v-model="selectedStrategyPresetIdModel"
          clearable
          filterable
          placeholder="选择已有模板"
        >
          <el-option
            v-for="preset in settings.strategy_presets"
            :key="preset.id"
            :label="preset.name"
            :value="preset.id"
          />
        </el-select>
        <el-input v-model="strategyPresetForm.name" placeholder="模板名称" />
        <el-input v-model="strategyPresetForm.note" placeholder="模板说明，可选" />
      </div>

      <div class="action-row toolbar-row">
        <el-button :disabled="!selectedPreset" @click="emit('apply-preset')">应用模板</el-button>
        <el-button
          :disabled="!selectedPreset"
          :loading="deletingPresetId === selectedStrategyPresetId"
          @click="emit('delete-preset')"
        >
          删除模板
        </el-button>
        <el-button type="primary" :loading="savingPreset" @click="emit('save-preset')">保存为模板</el-button>
      </div>

      <div v-if="settings.strategy_presets.length" class="preset-grid">
        <article
          v-for="preset in settings.strategy_presets"
          :key="preset.id"
          class="preset-card"
          :class="{ selected: preset.id === selectedStrategyPresetId }"
          @click="selectedStrategyPresetIdModel = preset.id"
        >
          <div class="preset-card-head">
            <strong>{{ preset.name }}</strong>
            <span>{{ preset.created_at.slice(0, 10) }}</span>
          </div>
          <p>{{ preset.note || "未填写说明" }}</p>
          <div class="tag-cluster">
            <el-tag size="small" effect="light">保 {{ preset.safe_ratio_max }}</el-tag>
            <el-tag size="small" effect="light" type="warning">稳 {{ preset.steady_ratio_max }}</el-tag>
            <el-tag size="small" effect="light" type="danger">冲 {{ preset.rush_ratio_max }}</el-tag>
          </div>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { RecommendationSettings } from "./types";

interface StrategyCard {
  label: string;
  value: string | number;
  help: string;
  tone: string;
}

interface CollegeOption {
  id: number;
  name: string;
}

interface StrategyPresetFormState {
  name: string;
  note: string;
}

const props = defineProps<{
  settings: RecommendationSettings;
  strategyCards: StrategyCard[];
  collegeOptions: CollegeOption[];
  selectedStrategyPresetId?: string;
  strategyPresetForm: StrategyPresetFormState;
  savingSettings: boolean;
  savingPreset: boolean;
  deletingPresetId: string | null;
}>();

const emit = defineEmits<{
  reload: [];
  "save-settings": [];
  "update:selectedStrategyPresetId": [value: string | undefined];
  "apply-preset": [];
  "delete-preset": [];
  "save-preset": [];
}>();

const selectedStrategyPresetIdModel = computed<string | undefined>({
  get: () => props.selectedStrategyPresetId,
  set: (value) => emit("update:selectedStrategyPresetId", value),
});

const selectedPreset = computed(
  () => props.settings.strategy_presets.find((item) => item.id === props.selectedStrategyPresetId) ?? null,
);
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.strategy-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.strategy-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(248, 251, 254, 0.96);
  border: 1px solid rgba(123, 142, 161, 0.12);
}

.strategy-card span {
  color: #6d8194;
  font-size: 13px;
}

.strategy-card strong {
  display: block;
  margin-top: 8px;
  color: #1e3348;
  font-size: 24px;
  font-weight: 760;
}

.strategy-card p {
  margin: 8px 0 0;
  color: #72879b;
  font-size: 13px;
  line-height: 1.5;
}

.strategy-filter-grid {
  margin-bottom: 14px;
}

.strategy-alert {
  margin-top: 4px;
}

.strategy-preset-shell {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(126, 143, 158, 0.12);
}

.preset-grid {
  display: grid;
  gap: 12px;
  margin-top: 12px;
}

.preset-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(248, 251, 254, 0.96);
  border: 1px solid rgba(123, 142, 161, 0.12);
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.preset-card:hover {
  border-color: rgba(31, 108, 152, 0.28);
  transform: translateY(-1px);
}

.preset-card.selected {
  border-color: rgba(31, 108, 152, 0.45);
  box-shadow: inset 0 3px 0 rgba(31, 108, 152, 0.78);
}

.preset-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.preset-card-head strong {
  color: #21364a;
}

.preset-card-head span {
  color: #72869a;
  font-size: 12px;
}

.preset-card p {
  margin: 8px 0 10px;
  color: #687e92;
  line-height: 1.5;
}

.toolbar-row {
  margin-bottom: 16px;
}

.tag-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

@media (max-width: 1080px) {
  .strategy-card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
