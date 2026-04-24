<template>
  <section class="soft-card panel-block">
    <div class="section-head">
      <div>
        <h3>学生志愿工作台</h3>
        <p>先按学生、考试、批次和选科条件刷新候选池，再把可报计划整理到志愿表草稿中。</p>
      </div>
      <div class="action-row">
        <el-button @click="emit('sync-from-recommendation')">沿用推荐条件</el-button>
        <el-button @click="emit('reset')">清空工作台</el-button>
        <el-button type="primary" :loading="loading" @click="emit('load-preview')">刷新候选池</el-button>
      </div>
    </div>

    <section class="draft-toolbar-card">
      <div class="draft-toolbar-copy">
        <strong>草稿持久化</strong>
        <p>当前志愿表可保存为命名草稿，后续可再次载入继续排序、打印和导出。</p>
      </div>
      <div class="draft-toolbar-actions">
        <el-input v-model="draftName" placeholder="草稿名称，例如：张三-本科批第一版" />
        <div class="draft-toolbar-buttons">
          <el-button type="primary" :loading="savingDraft" @click="emit('save-draft')">保存草稿</el-button>
          <el-button :loading="savingDraft" @click="emit('save-draft-as')">另存为新草稿</el-button>
          <el-button :disabled="!currentDraftId" @click="emit('print-draft')">打印预览</el-button>
          <el-button
            :disabled="!currentDraftId"
            :loading="exportingDraftId === currentDraftId"
            @click="emit('export-draft')"
          >
            导出 Excel
          </el-button>
        </div>
        <p class="draft-toolbar-status">
          {{ currentDraftId ? "当前已保存草稿，可直接打印或导出。" : "需先保存草稿后才能打印或导出。" }}
        </p>
      </div>
    </section>

    <div class="filter-grid">
      <el-select v-model="form.student_id" filterable placeholder="选择学生">
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
      <el-select v-model="form.province" filterable placeholder="省份">
        <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
      </el-select>
      <el-select v-model="form.target_year" filterable placeholder="目标年份">
        <el-option v-for="year in yearOptions" :key="year" :label="String(year)" :value="year" />
      </el-select>
      <el-select v-model="form.batch" clearable filterable placeholder="批次，可选">
        <el-option v-for="batch in batchOptions" :key="batch" :label="batch" :value="batch" />
      </el-select>
      <el-select v-model="form.exam_mode" clearable filterable placeholder="科类/模式，可选">
        <el-option v-for="mode in examModeOptions" :key="mode" :label="mode" :value="mode" />
      </el-select>
      <el-select v-model="form.candidate_type" clearable filterable placeholder="考生类别，可选">
        <el-option label="按学生档案判断" value="" />
        <el-option v-for="item in gaokaoCandidateTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="form.score_input_mode" placeholder="分数模式">
        <el-option v-for="item in scoreInputModeOptions" :key="item.value" :label="item.label" :value="item.value" />
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
      <el-input v-model="form.subject_combination" placeholder="选科组合，可选" />
      <el-input v-model="form.reference_exam_name" placeholder="参考考试说明，可选" />
      <el-input-number
        v-if="showRankInput"
        v-model="form.student_rank_override"
        :min="1"
        :max="999999"
        controls-position="right"
        style="width: 100%"
        :placeholder="rankInputPlaceholder"
      />
      <el-input-number
        v-if="showScoreInput"
        v-model="form.comprehensive_score"
        :min="0"
        :max="1000"
        controls-position="right"
        style="width: 100%"
        :placeholder="scoreInputPlaceholder"
      />
      <el-input-number
        v-if="showScoreRangeInput"
        v-model="form.score_range_min"
        :min="0"
        :max="1000"
        controls-position="right"
        style="width: 100%"
        placeholder="分数区间下限"
      />
      <el-input-number
        v-if="showScoreRangeInput"
        v-model="form.score_range_max"
        :min="0"
        :max="1000"
        controls-position="right"
        style="width: 100%"
        placeholder="分数区间上限"
      />
      <el-input-number
        v-if="showRankRangeInput"
        v-model="form.rank_range_min"
        :min="1"
        :max="999999"
        controls-position="right"
        style="width: 100%"
        placeholder="位次区间下限"
      />
      <el-input-number
        v-if="showRankRangeInput"
        v-model="form.rank_range_max"
        :min="1"
        :max="999999"
        controls-position="right"
        style="width: 100%"
        placeholder="位次区间上限"
      />
      <el-select v-if="showRiskPreference" v-model="form.risk_preference" placeholder="结果风险偏好">
        <el-option v-for="item in riskPreferenceOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <div v-if="showHistoricalMappingToggle" class="inline-switch-card">
        <span class="inline-switch-label">历年映射估算</span>
        <el-switch v-model="form.use_historical_mapping" inline-prompt active-text="开启" inactive-text="关闭" />
      </div>
    </div>

    <section class="career-preference-card">
      <div class="section-head compact">
        <div>
          <h3>职业意向输入</h3>
          <p>先记录 1~3 个目标就业方向、行业/岗位偏好和可接受路径，后续排序增强会直接复用这里的参数。</p>
        </div>
        <div class="action-row">
          <el-button
            :disabled="!studentCareerPreference"
            :loading="loadingStudentCareerPreference"
            @click="emit('apply-student-career-preference')"
          >
            载入学生偏好
          </el-button>
          <el-button
            type="primary"
            :disabled="!form.student_id"
            :loading="savingStudentCareerPreference"
            @click="emit('save-student-career-preference')"
          >
            保存为学生偏好
          </el-button>
        </div>
      </div>

      <p class="career-preference-status">{{ careerPreferenceStatusCopy }}</p>

      <div class="career-grid">
        <el-select v-model="form.primary_direction_id" clearable filterable placeholder="首选就业方向">
          <el-option
            v-for="item in careerDirectionOptions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
            :disabled="!item.is_active"
          />
        </el-select>
        <el-select v-model="form.secondary_direction_id" clearable filterable placeholder="次选就业方向">
          <el-option
            v-for="item in careerDirectionOptions"
            :key="`secondary-${item.id}`"
            :label="item.name"
            :value="item.id"
            :disabled="!item.is_active"
          />
        </el-select>
        <el-select v-model="form.alternative_direction_id" clearable filterable placeholder="可接受替代方向">
          <el-option
            v-for="item in careerDirectionOptions"
            :key="`alternative-${item.id}`"
            :label="item.name"
            :value="item.id"
            :disabled="!item.is_active"
          />
        </el-select>
      </div>

      <div class="career-priority-block">
        <span class="career-label">偏好重点</span>
        <el-checkbox-group v-model="form.priority_focuses_json" class="draft-column-options">
          <el-checkbox-button v-for="item in careerPriorityFocusOptions" :key="item.value" :label="item.value">
            {{ item.label }}
          </el-checkbox-button>
        </el-checkbox-group>
      </div>

      <div class="career-grid">
        <el-select
          v-model="form.preferred_industries_json"
          multiple
          filterable
          allow-create
          default-first-option
          collapse-tags
          placeholder="目标行业偏好，可选"
        >
          <el-option v-for="item in careerIndustryOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select
          v-model="form.preferred_job_types_json"
          multiple
          filterable
          allow-create
          default-first-option
          collapse-tags
          placeholder="目标岗位偏好，可选"
        >
          <el-option v-for="item in careerJobTypeOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select
          v-model="form.target_employment_cities_json"
          multiple
          filterable
          allow-create
          default-first-option
          collapse-tags
          placeholder="目标就业城市，可选"
        >
          <el-option v-for="item in provinceOptions" :key="`career-city-${item}`" :label="item" :value="item" />
        </el-select>
      </div>

      <div class="career-path-grid">
        <label class="career-check">
          <el-checkbox v-model="form.accepts_postgraduate">接受读研路径</el-checkbox>
        </label>
        <label class="career-check">
          <el-checkbox v-model="form.accepts_public_service">接受考公/考编路径</el-checkbox>
        </label>
        <label class="career-check">
          <el-checkbox v-model="form.accepts_certificate">接受资格证路径</el-checkbox>
        </label>
        <label class="career-check">
          <el-checkbox v-model="form.accepts_long_training">接受长培养周期</el-checkbox>
        </label>
      </div>
    </section>

    <el-input
      v-model="form.note"
      class="note-box"
      type="textarea"
      :rows="2"
      placeholder="补充说明，例如职业方向、地域偏好或需要重点规避的情况"
    />

    <el-alert
      v-if="preview"
      class="result-alert"
      type="info"
      show-icon
      :closable="false"
      :title="`${preview.student_name} · ${formatStudentType(preview.student_type)} · ${preview.exam_name}`"
    >
      <template #default>
        当前总分 {{ preview.total_score }}，考试位次 {{ preview.snapshot_rank ?? "暂无" }}，生效位次
        {{ preview.effective_rank ?? "暂无" }}，当前按“{{ preview.score_input_label }}”计算。已匹配
        {{ preview.candidate_count }} 条候选计划，{{ preview.applicable_rule_count }} 条省份规则。
        <div v-if="preview.input_notes.length" class="preview-note-list">
          <div v-for="item in preview.input_notes" :key="item">{{ item }}</div>
        </div>
      </template>
    </el-alert>

    <section v-if="preview?.rule_alerts.length" class="rule-alert-grid">
      <article
        v-for="alert in preview.rule_alerts"
        :key="`${alert.code}-${alert.detail}`"
        class="rule-alert-card"
        :class="`level-${normalizeAlertLevel(alert.level)}`"
      >
        <div class="rule-alert-head">
          <strong>{{ alert.title }}</strong>
          <el-tag :type="alertTagType(alert.level)" effect="plain">{{ alertLevelLabel(alert.level) }}</el-tag>
        </div>
        <p>{{ alert.detail }}</p>
      </article>
    </section>

    <section class="insight-grid">
      <article class="insight-panel">
        <div class="section-head compact">
          <div>
            <h3>筛选解释</h3>
            <p>把当前筛选条件、命中的规则和候选生成依据集中展示，避免只看到结果看不到过程。</p>
          </div>
        </div>
        <div class="insight-chip-list">
          <span v-for="item in workbenchExplanation.items" :key="`${item.label}-${item.value}`" class="page-chip">
            <strong>{{ item.label }}</strong>{{ item.value }}
          </span>
        </div>
        <ul class="insight-notes">
          <li v-for="note in workbenchExplanation.notes" :key="note">{{ note }}</li>
        </ul>
      </article>

      <article class="insight-panel">
        <div class="section-head compact">
          <div>
            <h3>风险校验</h3>
            <p>先看志愿位、保底项和选科复核，再决定是否保存、打印或导出草稿。</p>
          </div>
        </div>
        <div class="check-list">
          <article
            v-for="item in draftChecks"
            :key="`${item.level}-${item.title}`"
            class="check-item"
            :class="`level-${item.level}`"
          >
            <strong>{{ item.title }}</strong>
            <p>{{ item.detail }}</p>
          </article>
        </div>
      </article>
    </section>

    <section class="insight-panel rule-insight-panel">
      <div class="section-head compact">
        <div>
          <h3>规则差异摘要</h3>
          <p>把当前选中的规则和兼容命中的规则并排列出，便于判断模式回退、志愿结构和口径差异。</p>
        </div>
      </div>
      <div v-if="ruleInsightCards.length" class="rule-card-grid">
        <article
          v-for="card in ruleInsightCards"
          :key="card.key"
          class="rule-card"
          :class="{ selected: card.isSelected }"
        >
          <div class="rule-card-head">
            <div>
              <strong>{{ card.title }}</strong>
              <p>{{ card.subtitle }}</p>
            </div>
            <el-tag :type="card.isSelected ? 'success' : 'info'" effect="plain">
              {{ card.isSelected ? "当前控制规则" : "兼容预览规则" }}
            </el-tag>
          </div>
          <div class="insight-chip-list">
            <span v-for="fact in card.facts" :key="`${card.key}-${fact.label}`" class="page-chip">
              <strong>{{ fact.label }}</strong>{{ fact.value }}
            </span>
          </div>
          <ul v-if="card.notes.length" class="insight-notes rule-notes">
            <li v-for="note in card.notes" :key="`${card.key}-${note}`">{{ note }}</li>
          </ul>
        </article>
      </div>
      <div v-else class="comparison-placeholder inner">
        刷新候选池后，这里会展示当前命中的省份规则和兼容规则差异。
      </div>
    </section>

    <section v-if="boundaryInsightCards.length" class="insight-panel boundary-insight-panel">
      <div class="section-head compact">
        <div>
          <h3>边界概览</h3>
          <p>把规则提醒和候选池真实命中情况合并展示，先看清哪些结果是基线、回退或待复核，再决定是否直接排草稿。</p>
        </div>
      </div>
      <div class="boundary-card-grid">
        <article
          v-for="card in boundaryInsightCards"
          :key="card.key"
          class="boundary-card"
          :class="`tone-${card.tone}`"
        >
          <strong>{{ card.title }}</strong>
          <p class="boundary-summary">{{ card.summary }}</p>
          <p class="boundary-detail">{{ card.detail }}</p>
        </article>
      </div>
    </section>

    <div class="workbench-grid">
      <section class="nested-panel">
        <div class="section-head compact">
          <div>
            <h3>候选池</h3>
            <p>候选池会优先使用专业线，缺少专业线时回退到院校基线，并给出风险提示。</p>
          </div>
          <div class="candidate-stats" v-if="preview">
            <span class="page-chip"><strong>候选</strong>{{ preview.candidate_count }}</span>
            <span class="page-chip"><strong>规则</strong>{{ preview.applicable_rule_count }}</span>
          </div>
        </div>

        <div v-if="preview?.candidates.length">
          <el-table :data="preview.candidates" stripe>
            <el-table-column label="分层" width="90">
              <template #default="{ row }">
                <el-tag :type="resultTagType(row.result_type)" effect="dark">
                  {{ resultTypeLabel(row.result_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="院校 / 专业" min-width="220">
              <template #default="{ row }">
                <div class="candidate-title">
                  <strong>{{ row.college_name }}</strong>
                  <span>{{ row.major_name || row.major_group_code || "院校级计划" }}</span>
                  <small v-if="buildCodeMeta(row)">{{ buildCodeMeta(row) }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="批次 / 模式" width="150">
              <template #default="{ row }">
                {{ row.batch }} / {{ row.exam_mode }}
              </template>
            </el-table-column>
            <el-table-column label="计划数" prop="plan_count" width="80" />
            <el-table-column label="参考位次" width="120">
              <template #default="{ row }">
                {{ row.reference_rank ?? row.latest_min_rank ?? "暂无" }}
              </template>
            </el-table-column>
            <el-table-column label="风险提示" min-width="200">
              <template #default="{ row }">
                <div class="risk-tag-list">
                  <el-tag
                    v-for="flag in row.risk_flags_json"
                    :key="`${row.plan_id}-${flag}`"
                    size="small"
                    type="warning"
                    effect="plain"
                  >
                    {{ formatRiskFlag(flag) }}
                  </el-tag>
                  <span v-if="!row.risk_flags_json.length" class="muted-copy">无额外提示</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="依据" min-width="260">
              <template #default="{ row }">
                <div class="match-tag-list" v-if="row.match_tags_json.length">
                  <el-tag
                    v-for="tag in row.match_tags_json"
                    :key="`${row.plan_id}-${tag}`"
                    size="small"
                    type="info"
                    effect="plain"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
                <div v-if="buildVolunteerCandidateRuleCopy(row)" class="match-rule-copy">
                  {{ buildVolunteerCandidateRuleCopy(row) }}
                </div>
                <div v-if="buildVolunteerCandidateReferenceCopy(row)" class="match-reference-copy">
                  {{ buildVolunteerCandidateReferenceCopy(row) }}
                </div>
                <div v-if="row.fallback_priority_label" class="match-reference-copy">
                  初筛优先级：{{ row.fallback_priority_label }}
                  <span v-if="row.fallback_priority_score !== null && row.fallback_priority_score !== undefined">
                    · {{ row.fallback_priority_score }}
                  </span>
                  <span v-if="row.fallback_priority_notes_json?.length">
                    · {{ row.fallback_priority_notes_json.join("；") }}
                  </span>
                  <span v-if="row.fallback_category_label"> · {{ row.fallback_category_label }}</span>
                  <span v-if="row.fallback_review_notes_json?.length">
                    · 核对：{{ row.fallback_review_notes_json.join("；") }}
                  </span>
                </div>
                <div v-if="row.chapter_url || row.chapter_campus_note || row.chapter_review_status" class="match-reference-copy">
                  <a v-if="row.chapter_url" :href="row.chapter_url" target="_blank" rel="noreferrer">查看招生章程</a>
                  <span v-else>招生章程待补链</span>
                  <span v-if="row.chapter_campus_note"> · {{ row.chapter_campus_note }}</span>
                </div>
                <div class="match-layering-copy">
                  {{ buildVolunteerCandidateLayeringCopy(row) }}
                </div>
                <div class="reason-copy">{{ row.reason_text }}</div>
                <div v-if="buildVolunteerCandidateExplanationNotes(row).length" class="candidate-explanation-list">
                  <div
                    v-for="note in buildVolunteerCandidateExplanationNotes(row)"
                    :key="`${row.plan_id}-${note}`"
                    class="candidate-explanation-item"
                  >
                    {{ note }}
                  </div>
                </div>
                <div v-if="row.match_notes_json.length" class="match-note-list">
                  <div v-for="note in row.match_notes_json" :key="`${row.plan_id}-${note}`">{{ note }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  :disabled="selectedPlanIds.has(row.plan_id)"
                  @click="emit('add-candidate', row)"
                >
                  {{ selectedPlanIds.has(row.plan_id) ? "已加入" : "加入" }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-else class="comparison-placeholder">
          {{ preview ? "当前条件下暂无可加入志愿表的候选计划。" : "选择学生与考试后刷新候选池，这里会显示可报计划。" }}
        </div>
      </section>

      <section class="nested-panel">
        <div class="section-head compact">
          <div>
            <h3>志愿表草稿</h3>
            <p>
              {{ selectedRule ? `当前按 ${selectedRule.batch} · ${selectedRule.volunteer_unit_type} 规则控制上限。` : "当前还没匹配到明确的省份规则，上限暂不做硬限制。" }}
            </p>
          </div>
          <div class="draft-head-actions">
            <el-radio-group v-model="draftViewMode" size="small" class="draft-view-switch">
              <el-radio-button label="batch">批次顺序</el-radio-button>
              <el-radio-button label="risk">冲稳保视图</el-radio-button>
            </el-radio-group>
            <div class="draft-metrics">
              <span class="page-chip"><strong>已选</strong>{{ draft.length }}</span>
              <span class="page-chip" v-if="volunteerLimit !== undefined">
                <strong>上限</strong>{{ volunteerLimit }}
              </span>
              <span class="page-chip" v-if="remainingSlots !== null">
                <strong>剩余</strong>{{ remainingSlots }}
              </span>
            </div>
          </div>
        </div>

        <el-alert
          v-if="selectedRule"
          class="draft-alert"
          type="success"
          show-icon
          :closable="false"
          :title="`${selectedRule.province} ${selectedRule.year} ${selectedRule.exam_mode} · ${selectedRule.batch}`"
        >
          <template #default>
            志愿单位：{{ selectedRule.volunteer_unit_type }}；平行志愿：{{ selectedRule.is_parallel ? "是" : "否" }}；
            服从调剂：{{ selectedRule.allow_adjustment ? "允许" : "不允许" }}。
          </template>
        </el-alert>

        <el-alert
          v-if="draft.length && draftViewMode === 'batch'"
          class="draft-view-alert"
          type="info"
          show-icon
          :closable="false"
          title="批次顺序视图支持拖拽排序"
        >
          <template #default>
            拖拽“拖拽”手柄到目标志愿上即可调整顺序；上移 / 下移按钮仍保留，便于精调。
          </template>
        </el-alert>

        <el-alert
          v-if="draft.length && draftViewMode === 'risk'"
          class="draft-view-alert"
          type="info"
          show-icon
          :closable="false"
          title="冲稳保视图只改变查看方式，不改变全表顺序"
        >
          <template #default>
            当前会按冲刺、稳妥、保底分组展示，但顺序编号仍以整张草稿的全局顺序为准。
          </template>
        </el-alert>

        <div v-if="draft.length" class="draft-column-controls">
          <div>
            <strong>就业增强列</strong>
            <p>基于专业画像中的方向、就业去向和备注推断；未维护画像时会显示“待维护”。</p>
          </div>
          <el-checkbox-group v-model="selectedEmploymentColumns" class="draft-column-options">
            <el-checkbox-button
              v-for="item in employmentColumnOptions"
              :key="item.key"
              :label="item.key"
            >
              {{ item.label }}
            </el-checkbox-button>
          </el-checkbox-group>
        </div>

        <div v-if="draft.length && draftViewMode === 'batch'">
          <el-table :data="draft" stripe>
            <el-table-column label="拖拽" width="84">
              <template #default="{ row }">
                <button
                  type="button"
                  class="drag-handle"
                  :class="{
                    dragging: draggingPlanId === row.plan_id,
                    'drop-target': dragTargetPlanId === row.plan_id && draggingPlanId !== row.plan_id,
                  }"
                  draggable="true"
                  @dragstart="handleDraftDragStart($event, row.plan_id)"
                  @dragover.prevent="handleDraftDragOver(row.plan_id)"
                  @drop.prevent="handleDraftDrop(row.plan_id)"
                  @dragend="clearDraftDragState"
                >
                  拖拽
                </button>
              </template>
            </el-table-column>
            <el-table-column label="顺序" width="70">
              <template #default="{ row }">
                {{ row.order }}
              </template>
            </el-table-column>
            <el-table-column label="志愿" min-width="220">
              <template #default="{ row }">
                <div class="candidate-title">
                  <strong>{{ row.candidate.college_name }}</strong>
                  <span>{{ row.candidate.major_name || row.candidate.major_group_code || "院校级计划" }}</span>
                  <small v-if="buildCodeMeta(row.candidate)">{{ buildCodeMeta(row.candidate) }}</small>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="分层" width="90">
              <template #default="{ row }">
                <el-tag :type="resultTagType(row.candidate.result_type)" effect="plain">
                  {{ resultTypeLabel(row.candidate.result_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="参考" width="120">
              <template #default="{ row }">
                {{ row.candidate.reference_rank ?? row.candidate.latest_min_rank ?? "暂无" }}
              </template>
            </el-table-column>
            <el-table-column v-if="hasEmploymentColumn('target_direction')" label="对应就业方向" min-width="180">
              <template #default="{ row }">
                <div class="employment-copy">
                  <strong>{{ employmentProfile(row.candidate).targetDirection }}</strong>
                </div>
              </template>
            </el-table-column>
            <el-table-column v-if="hasEmploymentColumn('match_strength')" label="匹配强度" width="120">
              <template #default="{ row }">
                <el-tag :type="employmentMatchTagType(employmentProfile(row.candidate).matchStrength)" effect="plain">
                  {{ formatEmploymentMatchStrength(employmentProfile(row.candidate).matchStrength) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column v-if="hasEmploymentColumn('needs_postgraduate')" label="需读研" width="120">
              <template #default="{ row }">
                <el-tag :type="employmentHintTagType(employmentProfile(row.candidate).needsPostgraduate)" effect="plain">
                  {{ formatEmploymentHintStatus(employmentProfile(row.candidate).needsPostgraduate) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column v-if="hasEmploymentColumn('needs_certificate')" label="需资格证" width="120">
              <template #default="{ row }">
                <el-tag :type="employmentHintTagType(employmentProfile(row.candidate).needsCertificate)" effect="plain">
                  {{ formatEmploymentHintStatus(employmentProfile(row.candidate).needsCertificate) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column v-if="hasEmploymentColumn('summary')" label="说明摘要" min-width="240">
              <template #default="{ row }">
                <div class="employment-copy">
                  {{ employmentProfile(row.candidate).summary }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <div class="draft-actions">
                  <el-button size="small" :disabled="row.order === 1" @click="emit('move-candidate', row.plan_id, 'up')">
                    上移
                  </el-button>
                  <el-button
                    size="small"
                    :disabled="row.order === draft.length"
                    @click="emit('move-candidate', row.plan_id, 'down')"
                  >
                    下移
                  </el-button>
                  <el-button size="small" type="danger" plain @click="emit('remove-candidate', row.plan_id)">
                    移除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-else-if="draft.length" class="draft-group-stack">
          <article v-for="section in draftViewSections" :key="section.key" class="draft-group-card">
            <div class="draft-group-head">
              <div>
                <h4>{{ section.label }}</h4>
                <p>{{ section.description }}</p>
              </div>
              <el-tag :type="section.tagType" effect="plain">{{ section.items.length }} 条</el-tag>
            </div>

            <div v-if="section.items.length">
              <el-table :data="section.items" stripe>
                <el-table-column label="顺序" width="70">
                  <template #default="{ row }">
                    {{ row.order }}
                  </template>
                </el-table-column>
                <el-table-column label="志愿" min-width="220">
                  <template #default="{ row }">
                    <div class="candidate-title">
                      <strong>{{ row.candidate.college_name }}</strong>
                      <span>{{ row.candidate.major_name || row.candidate.major_group_code || "院校级计划" }}</span>
                      <small v-if="buildCodeMeta(row.candidate)">{{ buildCodeMeta(row.candidate) }}</small>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="参考" width="120">
                  <template #default="{ row }">
                    {{ row.candidate.reference_rank ?? row.candidate.latest_min_rank ?? "暂无" }}
                  </template>
                </el-table-column>
                <el-table-column v-if="hasEmploymentColumn('target_direction')" label="对应就业方向" min-width="180">
                  <template #default="{ row }">
                    <div class="employment-copy">
                      <strong>{{ employmentProfile(row.candidate).targetDirection }}</strong>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column v-if="hasEmploymentColumn('match_strength')" label="匹配强度" width="120">
                  <template #default="{ row }">
                    <el-tag :type="employmentMatchTagType(employmentProfile(row.candidate).matchStrength)" effect="plain">
                      {{ formatEmploymentMatchStrength(employmentProfile(row.candidate).matchStrength) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column v-if="hasEmploymentColumn('needs_postgraduate')" label="需读研" width="120">
                  <template #default="{ row }">
                    <el-tag :type="employmentHintTagType(employmentProfile(row.candidate).needsPostgraduate)" effect="plain">
                      {{ formatEmploymentHintStatus(employmentProfile(row.candidate).needsPostgraduate) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column v-if="hasEmploymentColumn('needs_certificate')" label="需资格证" width="120">
                  <template #default="{ row }">
                    <el-tag :type="employmentHintTagType(employmentProfile(row.candidate).needsCertificate)" effect="plain">
                      {{ formatEmploymentHintStatus(employmentProfile(row.candidate).needsCertificate) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column v-if="hasEmploymentColumn('summary')" label="说明摘要" min-width="240">
                  <template #default="{ row }">
                    <div class="employment-copy">
                      {{ employmentProfile(row.candidate).summary }}
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="150" fixed="right">
                  <template #default="{ row }">
                    <div class="draft-actions">
                      <el-button
                        size="small"
                        :disabled="row.order === 1"
                        @click="emit('move-candidate', row.plan_id, 'up')"
                      >
                        上移
                      </el-button>
                      <el-button
                        size="small"
                        :disabled="row.order === draft.length"
                        @click="emit('move-candidate', row.plan_id, 'down')"
                      >
                        下移
                      </el-button>
                      <el-button size="small" type="danger" plain @click="emit('remove-candidate', row.plan_id)">
                        移除
                      </el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div v-else class="comparison-placeholder inner">
              {{ emptyResultGroupCopy(section.label) }}
            </div>
          </article>
        </div>
        <div v-else class="comparison-placeholder">从左侧候选池加入计划后，这里会形成可排序的志愿表草稿。</div>

        <div class="saved-drafts-panel">
          <div class="section-head compact">
            <div>
              <h3>已保存草稿</h3>
              <p>按当前学生和考试过滤，便于回到历史版本继续编辑。</p>
            </div>
            <el-button text :loading="loadingSavedDrafts" @click="emit('reload-drafts')">刷新</el-button>
          </div>

          <div v-if="savedDrafts.length" class="saved-draft-list">
            <article
              v-for="item in savedDrafts"
              :key="item.id"
              class="saved-draft-card"
              :class="{ active: currentDraftId === item.id }"
            >
              <div>
                <strong>{{ item.name }}</strong>
                <p>
                  {{ item.batch || "未设批次" }} · {{ item.exam_mode || "未设模式" }} · {{ item.item_count }} 条志愿
                </p>
                <span>更新时间 {{ item.updated_at }}</span>
              </div>
              <div class="draft-card-actions">
                <el-button size="small" @click="emit('load-draft', item.id)">加载</el-button>
                <el-button
                  size="small"
                  type="danger"
                  plain
                  :loading="deletingDraftId === item.id"
                  @click="emit('delete-draft', item.id)"
                >
                  删除
                </el-button>
              </div>
            </article>
          </div>
          <div v-else class="comparison-placeholder inner">当前学生/考试下还没有保存过草稿。</div>
        </div>

        <div class="draft-comparison-panel">
          <div class="section-head compact">
            <div>
              <h3>草稿对比</h3>
              <p>把当前草稿和历史版本并排对照，快速看新增、移除、顺序变化和分层变化。</p>
            </div>
            <div class="comparison-controls">
              <el-select
                v-model="compareDraftIdModel"
                clearable
                filterable
                placeholder="选择历史草稿对比"
              >
                <el-option
                  v-for="item in compareableSavedDrafts"
                  :key="item.id"
                  :label="`${item.name} · ${item.updated_at}`"
                  :value="item.id"
                />
              </el-select>
            </div>
          </div>

          <div v-if="compareDraftLoading" class="comparison-placeholder inner">正在加载对比草稿...</div>
          <template v-else-if="selectedCompareDraft && draftComparison">
            <div class="comparison-summary-grid">
              <article class="comparison-summary-card tone-blue">
                <span>新增志愿</span>
                <strong>{{ draftComparison.added.length }}</strong>
                <p>当前草稿里新增的志愿条目。</p>
              </article>
              <article class="comparison-summary-card tone-slate">
                <span>移除旧志愿</span>
                <strong>{{ draftComparison.removed.length }}</strong>
                <p>历史草稿里有、当前草稿里已去掉的条目。</p>
              </article>
              <article class="comparison-summary-card tone-amber">
                <span>顺序变化</span>
                <strong>{{ draftComparison.reordered.length }}</strong>
                <p>同一条志愿仍保留，但顺序已经调整。</p>
              </article>
              <article class="comparison-summary-card tone-green">
                <span>分层变化</span>
                <strong>{{ draftComparison.regrouped.length }}</strong>
                <p>同一条志愿仍保留，但冲稳保分层发生变化。</p>
              </article>
              <article class="comparison-summary-card tone-ink">
                <span>共同志愿</span>
                <strong>{{ draftComparison.commonCount }}</strong>
                <p>{{ selectedCompareDraft.name }} 和当前草稿的共同条目。</p>
              </article>
            </div>

            <div class="comparison-column-grid">
              <article class="comparison-column">
                <header>
                  <h4>新增</h4>
                  <span>{{ draftComparison.added.length }} 条</span>
                </header>
                <div v-if="draftComparison.added.length" class="comparison-item-list">
                  <div v-for="item in draftComparison.added" :key="`added-${item.key}`" class="comparison-item">
                    <strong>{{ item.label }}</strong>
                    <span>{{ formatComparisonType(item.currentType) }}</span>
                  </div>
                </div>
                <div v-else class="comparison-empty">当前草稿没有新增志愿。</div>
              </article>

              <article class="comparison-column">
                <header>
                  <h4>移除</h4>
                  <span>{{ draftComparison.removed.length }} 条</span>
                </header>
                <div v-if="draftComparison.removed.length" class="comparison-item-list">
                  <div v-for="item in draftComparison.removed" :key="`removed-${item.key}`" class="comparison-item">
                    <strong>{{ item.label }}</strong>
                    <span>{{ formatComparisonType(item.compareType) }}</span>
                  </div>
                </div>
                <div v-else class="comparison-empty">当前草稿没有移除旧志愿。</div>
              </article>

              <article class="comparison-column">
                <header>
                  <h4>顺序变化</h4>
                  <span>{{ draftComparison.reordered.length }} 条</span>
                </header>
                <div v-if="draftComparison.reordered.length" class="comparison-item-list">
                  <div v-for="item in draftComparison.reordered" :key="`reordered-${item.key}`" class="comparison-item">
                    <strong>{{ item.label }}</strong>
                    <span>{{ formatComparisonOrderChange(item) }}</span>
                  </div>
                </div>
                <div v-else class="comparison-empty">当前草稿和历史草稿的顺序一致。</div>
              </article>

              <article class="comparison-column">
                <header>
                  <h4>分层变化</h4>
                  <span>{{ draftComparison.regrouped.length }} 条</span>
                </header>
                <div v-if="draftComparison.regrouped.length" class="comparison-item-list">
                  <div v-for="item in draftComparison.regrouped" :key="`regrouped-${item.key}`" class="comparison-item">
                    <strong>{{ item.label }}</strong>
                    <span>{{ formatComparisonTypeChange(item) }}</span>
                  </div>
                </div>
                <div v-else class="comparison-empty">当前草稿和历史草稿的冲稳保分层一致。</div>
              </article>
            </div>
          </template>
          <div v-else class="comparison-placeholder inner">
            选择一个历史草稿后，这里会显示新增、移除、顺序变化和分层变化。
          </div>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

import {
  careerPriorityFocusOptions,
  gaokaoCandidateTypeOptions,
  riskPreferenceOptions,
  scoreInputModeOptions,
} from "./helpers";
import {
  buildVolunteerBoundaryInsightCards,
  buildVolunteerCandidateExplanationNotes,
  buildVolunteerCandidateLayeringCopy,
  buildVolunteerCandidateReferenceCopy,
  buildVolunteerCandidateRuleCopy,
  buildVolunteerDraftViewSections,
  buildVolunteerEmploymentProfile,
  buildVolunteerRuleInsightCards,
} from "./volunteerWorkbench";

import type {
  EmploymentDirectionItem,
  ExamOption,
  ProvinceVolunteerRule,
  StudentOption,
  StudentCareerPreference,
  VolunteerDraftComparisonEntry,
  VolunteerDraftComparisonSummary,
  VolunteerEmploymentColumnKey,
  VolunteerDraftCheckItem,
  VolunteerDraftSummary,
  VolunteerDraftItem,
  VolunteerDraftViewMode,
  VolunteerBoundaryInsightCard,
  VolunteerWorkbenchExplanation,
  VolunteerWorkbenchCandidate,
  VolunteerWorkbenchFormState,
  VolunteerWorkbenchPreviewResponse,
  VolunteerWorkbenchRuleAlert,
  VolunteerRuleInsightCard,
} from "./types";

const props = defineProps<{
  form: VolunteerWorkbenchFormState;
  studentOptions: StudentOption[];
  examOptions: ExamOption[];
  yearOptions: number[];
  batchOptions: string[];
  examModeOptions: string[];
  employmentDirections: EmploymentDirectionItem[];
  careerIndustryOptions: string[];
  careerJobTypeOptions: string[];
  studentCareerPreference: StudentCareerPreference | null;
  loadingStudentCareerPreference: boolean;
  savingStudentCareerPreference: boolean;
  provinceOptions: string[];
  targetRegionOptions: string[];
  schoolLevelOptions: string[];
  preview: VolunteerWorkbenchPreviewResponse | null;
  draft: VolunteerDraftItem[];
  draftName: string;
  loading: boolean;
  savingDraft: boolean;
  exportingDraftId: number | null;
  loadingSavedDrafts: boolean;
  deletingDraftId: number | null;
  currentDraftId?: number;
  savedDrafts: VolunteerDraftSummary[];
  compareDraftId?: number;
  compareDraftLoading: boolean;
  draftComparison: VolunteerDraftComparisonSummary | null;
  selectedPlanIds: Set<number>;
  selectedRule: ProvinceVolunteerRule | null;
  workbenchExplanation: VolunteerWorkbenchExplanation;
  draftChecks: VolunteerDraftCheckItem[];
  volunteerLimit?: number;
  remainingSlots: number | null;
}>();

const emit = defineEmits<{
  "load-preview": [];
  reset: [];
  "sync-from-recommendation": [];
  "update:draftName": [value: string];
  "save-draft": [];
  "save-draft-as": [];
  "print-draft": [];
  "export-draft": [];
  "reload-drafts": [];
  "compare-draft-change": [draftId: number | undefined];
  "load-draft": [draftId: number];
  "delete-draft": [draftId: number];
  "apply-student-career-preference": [];
  "save-student-career-preference": [];
  "add-candidate": [value: VolunteerWorkbenchCandidate];
  "remove-candidate": [planId: number];
  "move-candidate": [planId: number, direction: "up" | "down"];
  "reorder-candidate": [planId: number, targetPlanId: number];
}>();

const draftName = computed({
  get: () => props.draftName,
  set: (value: string) => emit("update:draftName", value),
});
const compareDraftIdModel = computed<number | undefined>({
  get: () => props.compareDraftId,
  set: (value) => emit("compare-draft-change", value),
});
const draftViewMode = ref<VolunteerDraftViewMode>("batch");
const showRankInput = computed(() => ["actual_rank", "estimated_score_and_rank"].includes(props.form.score_input_mode));
const showScoreInput = computed(() =>
  ["actual_score", "estimated_score", "estimated_score_and_rank"].includes(props.form.score_input_mode),
);
const showScoreRangeInput = computed(() => props.form.score_input_mode === "score_range");
const showRankRangeInput = computed(() => props.form.score_input_mode === "rank_range");
const showHistoricalMappingToggle = computed(() =>
  ["actual_score", "estimated_score", "score_range", "rank_range"].includes(props.form.score_input_mode),
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
const draftViewSections = computed(() => buildVolunteerDraftViewSections(props.draft));
const ruleInsightCards = computed<VolunteerRuleInsightCard[]>(() =>
  buildVolunteerRuleInsightCards(props.preview, props.selectedRule),
);
const boundaryInsightCards = computed<VolunteerBoundaryInsightCard[]>(() =>
  buildVolunteerBoundaryInsightCards(props.preview),
);
const draggingPlanId = ref<number | null>(null);
const dragTargetPlanId = ref<number | null>(null);
const selectedEmploymentColumns = ref<VolunteerEmploymentColumnKey[]>(["target_direction", "match_strength"]);
const compareableSavedDrafts = computed(() => props.savedDrafts.filter((item) => item.id !== props.currentDraftId));
const selectedCompareDraft = computed(
  () => compareableSavedDrafts.value.find((item) => item.id === props.compareDraftId) ?? null,
);
const selectedDirectionIds = computed(() =>
  [props.form.primary_direction_id, props.form.secondary_direction_id, props.form.alternative_direction_id].filter(
    (item): item is number => typeof item === "number",
  ),
);
const careerDirectionOptions = computed(() =>
  props.employmentDirections.filter((item) => item.is_active || selectedDirectionIds.value.includes(item.id)),
);
const employmentColumnOptions: Array<{ key: VolunteerEmploymentColumnKey; label: string }> = [
  { key: "target_direction", label: "就业方向" },
  { key: "match_strength", label: "匹配强度" },
  { key: "needs_postgraduate", label: "需读研" },
  { key: "needs_certificate", label: "需资格证" },
  { key: "summary", label: "说明摘要" },
];
const employmentColumnSet = computed(() => new Set(selectedEmploymentColumns.value));
const careerPreferenceStatusCopy = computed(() => {
  if (!props.form.student_id) {
    return "先选择学生，再读取或保存职业意向。";
  }
  if (props.loadingStudentCareerPreference) {
    return "正在读取该学生已保存的职业意向。";
  }
  if (!props.studentCareerPreference) {
    return "当前学生还没有已保存的职业意向，可直接填写后保存为学生偏好。";
  }
  return `已存在学生级职业意向，最近更新于 ${formatDateTime(props.studentCareerPreference.updated_at)}。`;
});

function resultTypeLabel(value: string): string {
  const mapping: Record<string, string> = {
    challenge: "冲刺",
    steady: "稳妥",
    safe: "保底",
  };
  return mapping[value] ?? value;
}

function resultTagType(value: string): "danger" | "warning" | "success" | "info" {
  const mapping: Record<string, "danger" | "warning" | "success" | "info"> = {
    challenge: "danger",
    steady: "warning",
    safe: "success",
  };
  return mapping[value] ?? "info";
}

function formatStudentType(value?: string | null): string {
  if (!value) return "-";
  const mapping: Record<string, string> = {
    general: "普通生",
    repeat: "复读生",
    art: "艺体生",
    sports: "体育生",
  };
  return mapping[value] ?? value;
}

function formatRiskFlag(value: string): string {
  const mapping: Record<string, string> = {
    sample_insufficient: "样本不足",
    rank_missing: "缺少位次，分数参考",
    general_reference_fallback: "缺少专门录取结果，按普通类参考",
    score_line_reference_only: "缺少专门录取结果，按省控线初筛",
    cross_year_score_line_reference: "省控线按跨年份参考",
    plan_only_reference: "缺少专门结果，仅按计划清单初筛",
    art_recommendation: "艺体推荐",
    track_unconfirmed: "艺体方向待确认",
    manual_formula_check: "需人工核对招生章程",
    chapter_pending_review: "章程待补链",
    chapter_special_requirement: "章程限制已提取",
    whitelist_override: "白名单放宽",
    major_baseline_missing: "专业线缺失，按院校线参考",
    subject_requirement_check: "需复核选科要求",
    career_mapping_pending: "职业路径映射待维护",
    postgraduate_path_mismatch: "与读研接受度不匹配",
    certificate_path_mismatch: "与资格证接受度不匹配",
    long_training_path_mismatch: "与长培养周期接受度不匹配",
    public_service_path_mismatch: "与考公考编接受度不匹配",
  };
  return mapping[value] ?? value;
}

function emptyResultGroupCopy(label: string): string {
  return `当前草稿里还没有${label}。`;
}

function handleDraftDragStart(event: DragEvent, planId: number): void {
  draggingPlanId.value = planId;
  dragTargetPlanId.value = null;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(planId));
  }
}

function handleDraftDragOver(planId: number): void {
  if (draggingPlanId.value === null || draggingPlanId.value === planId) return;
  dragTargetPlanId.value = planId;
}

function handleDraftDrop(planId: number): void {
  const sourcePlanId = draggingPlanId.value;
  if (sourcePlanId === null || sourcePlanId === planId) {
    clearDraftDragState();
    return;
  }
  emit("reorder-candidate", sourcePlanId, planId);
  clearDraftDragState();
}

function clearDraftDragState(): void {
  draggingPlanId.value = null;
  dragTargetPlanId.value = null;
}

function buildCodeMeta(
  candidate: Pick<VolunteerWorkbenchCandidate, "college_code_snapshot" | "major_code_snapshot" | "major_group_code">,
): string {
  const segments: string[] = [];
  if (candidate.college_code_snapshot) {
    segments.push(`院校代码 ${candidate.college_code_snapshot}`);
  }
  if (candidate.major_code_snapshot) {
    segments.push(`专业代码 ${candidate.major_code_snapshot}`);
  }
  if (candidate.major_group_code) {
    segments.push(`专业组 ${candidate.major_group_code}`);
  }
  return segments.join(" / ");
}

function hasEmploymentColumn(key: VolunteerEmploymentColumnKey): boolean {
  return employmentColumnSet.value.has(key);
}

function employmentProfile(candidate: VolunteerWorkbenchCandidate) {
  return buildVolunteerEmploymentProfile(candidate);
}

function formatComparisonType(value?: VolunteerDraftComparisonEntry["currentType"]): string {
  if (!value) return "-";
  return resultTypeLabel(value);
}

function formatComparisonOrderChange(entry: VolunteerDraftComparisonEntry): string {
  return `当前第 ${entry.currentOrder ?? "-"} 位，对比稿第 ${entry.compareOrder ?? "-"} 位`;
}

function formatComparisonTypeChange(entry: VolunteerDraftComparisonEntry): string {
  return `${formatComparisonType(entry.currentType)} / 对比稿 ${formatComparisonType(entry.compareType)}`;
}

function formatEmploymentMatchStrength(value: ReturnType<typeof buildVolunteerEmploymentProfile>["matchStrength"]): string {
  const mapping = {
    core: "核心相关",
    high: "强相关",
    medium: "一般相关",
    transferable: "可转化相关",
    pending: "待维护",
  } as const;
  return mapping[value];
}

function employmentMatchTagType(
  value: ReturnType<typeof buildVolunteerEmploymentProfile>["matchStrength"],
): "success" | "warning" | "info" {
  const mapping = {
    core: "success",
    high: "success",
    medium: "warning",
    transferable: "warning",
    pending: "info",
  } as const;
  return mapping[value];
}

function formatEmploymentHintStatus(value: ReturnType<typeof buildVolunteerEmploymentProfile>["needsPostgraduate"]): string {
  const mapping = {
    yes: "建议关注",
    not_explicit: "未见明确提示",
    pending: "待维护",
  } as const;
  return mapping[value];
}

function employmentHintTagType(
  value: ReturnType<typeof buildVolunteerEmploymentProfile>["needsPostgraduate"],
): "warning" | "info" {
  const mapping = {
    yes: "warning",
    not_explicit: "info",
    pending: "info",
  } as const;
  return mapping[value];
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", { hour12: false });
}

function normalizeAlertLevel(value: string): "warning" | "info" {
  return value === "warning" ? "warning" : "info";
}

function alertTagType(value: string): "warning" | "info" {
  return normalizeAlertLevel(value);
}

function alertLevelLabel(value: VolunteerWorkbenchRuleAlert["level"]): string {
  return value === "warning" ? "需人工复核" : "已自动回退";
}
</script>

<style scoped>
.panel-block {
  padding: 24px;
}

.career-preference-card {
  margin-top: 16px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(248, 250, 252, 0.96);
  border: 1px solid rgba(126, 143, 158, 0.14);
}

.career-preference-status {
  margin: 0 0 14px;
  color: #5b7083;
  line-height: 1.6;
}

.career-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.career-priority-block {
  margin: 14px 0;
}

.career-label {
  display: block;
  margin-bottom: 10px;
  color: #33465a;
  font-weight: 600;
}

.career-path-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.career-check {
  display: flex;
  align-items: center;
  min-height: 44px;
  padding: 0 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(126, 143, 158, 0.14);
}

.note-box {
  margin-top: 4px;
}

.inline-switch-card {
  min-height: 40px;
  border: 1px solid #d7e2ea;
  border-radius: 12px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8fbfd;
}

.inline-switch-label {
  color: #425466;
  font-size: 13px;
}

.result-alert {
  margin-top: 16px;
}

.preview-note-list {
  margin-top: 8px;
  display: grid;
  gap: 4px;
}

.rule-alert-grid {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.rule-alert-card {
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(126, 143, 158, 0.14);
  background: rgba(247, 250, 253, 0.94);
}

.rule-alert-card.level-warning {
  border-color: rgba(194, 136, 47, 0.2);
  background: rgba(255, 249, 239, 0.96);
}

.rule-alert-card.level-info {
  border-color: rgba(78, 123, 186, 0.16);
  background: rgba(244, 248, 255, 0.94);
}

.rule-alert-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.rule-alert-head strong {
  color: #20364b;
}

.rule-alert-card p {
  margin: 8px 0 0;
  color: #5f7487;
  line-height: 1.6;
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.insight-panel {
  padding: 18px;
  border-radius: 22px;
  background: rgba(244, 248, 251, 0.94);
  border: 1px solid rgba(126, 143, 158, 0.12);
}

.rule-insight-panel {
  margin-top: 16px;
}

.insight-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.insight-notes {
  margin: 14px 0 0;
  padding-left: 18px;
  color: #4f6578;
  line-height: 1.7;
}

.rule-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.rule-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(126, 143, 158, 0.12);
}

.rule-card.selected {
  border-color: rgba(58, 134, 87, 0.22);
  background: rgba(245, 252, 247, 0.96);
  box-shadow: 0 10px 20px rgba(52, 118, 78, 0.08);
}

.rule-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.rule-card-head strong {
  display: block;
  color: #20364b;
}

.rule-card-head p {
  margin: 6px 0 0;
  color: #63798d;
  font-size: 13px;
  line-height: 1.6;
}

.rule-notes {
  margin-top: 12px;
}

.boundary-insight-panel {
  margin-top: 16px;
}

.boundary-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.boundary-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(126, 143, 158, 0.14);
  background: rgba(255, 255, 255, 0.92);
}

.boundary-card.tone-warning {
  border-color: rgba(186, 127, 38, 0.22);
  background: rgba(255, 249, 240, 0.96);
}

.boundary-card.tone-info {
  border-color: rgba(74, 111, 165, 0.2);
  background: rgba(245, 249, 255, 0.96);
}

.boundary-card.tone-success {
  border-color: rgba(58, 134, 87, 0.2);
  background: rgba(244, 251, 246, 0.96);
}

.boundary-card strong {
  display: block;
  color: #20364b;
}

.boundary-summary {
  margin: 8px 0 0;
  color: #34506a;
  font-weight: 600;
  line-height: 1.6;
}

.boundary-detail {
  margin: 8px 0 0;
  color: #5f7487;
  line-height: 1.6;
}

.check-list {
  display: grid;
  gap: 10px;
}

.check-item {
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid rgba(126, 143, 158, 0.14);
  background: rgba(255, 255, 255, 0.88);
}

.check-item strong {
  display: block;
  color: #20364b;
}

.check-item p {
  margin: 6px 0 0;
  color: #5f7487;
  line-height: 1.6;
}

.check-item.level-success {
  border-color: rgba(60, 138, 88, 0.18);
  background: rgba(244, 251, 246, 0.95);
}

.check-item.level-warning {
  border-color: rgba(189, 123, 36, 0.2);
  background: rgba(255, 249, 240, 0.96);
}

.check-item.level-info {
  border-color: rgba(66, 124, 189, 0.16);
  background: rgba(244, 248, 255, 0.94);
}

.draft-toolbar-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 16px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(247, 250, 253, 0.92);
  border: 1px solid rgba(124, 139, 154, 0.12);
}

.draft-toolbar-copy strong {
  color: #20364b;
  font-size: 15px;
}

.draft-toolbar-copy p {
  margin: 6px 0 0;
  color: #6a8094;
  line-height: 1.6;
}

.draft-toolbar-actions {
  display: grid;
  gap: 10px;
  width: min(520px, 100%);
}

.draft-toolbar-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.draft-toolbar-status {
  margin: 0;
  color: #6a8094;
  font-size: 13px;
  text-align: right;
}

.workbench-grid {
  display: grid;
  grid-template-columns: 1.45fr 1fr;
  gap: 18px;
  margin-top: 18px;
}

.nested-panel {
  padding: 18px;
  border-radius: 22px;
  background: rgba(245, 249, 252, 0.9);
  border: 1px solid rgba(126, 143, 158, 0.12);
}

.candidate-stats,
.draft-metrics {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.draft-head-actions {
  display: grid;
  gap: 10px;
  justify-items: end;
}

.draft-view-switch {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.candidate-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.candidate-title strong {
  color: #20364b;
}

.candidate-title span {
  color: #6a8094;
  font-size: 13px;
}

.candidate-title small {
  color: #8b9caf;
  font-size: 12px;
  line-height: 1.5;
}

.risk-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.reason-copy {
  color: #4f6578;
  line-height: 1.6;
}

.match-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.match-note-list {
  margin-top: 8px;
  display: grid;
  gap: 4px;
  color: #6a8094;
  font-size: 12px;
  line-height: 1.6;
}

.match-rule-copy {
  margin-bottom: 8px;
  color: #35526b;
  font-size: 12px;
  line-height: 1.6;
  font-weight: 600;
}

.match-reference-copy {
  margin-bottom: 8px;
  color: #5a7388;
  font-size: 12px;
  line-height: 1.6;
}

.candidate-explanation-list {
  margin-bottom: 8px;
  display: grid;
  gap: 4px;
}

.candidate-explanation-item {
  color: #5c6875;
  font-size: 12px;
  line-height: 1.6;
}

.match-layering-copy {
  margin-bottom: 8px;
  color: #40617b;
  font-size: 12px;
  line-height: 1.6;
}

.draft-alert {
  margin-bottom: 12px;
}

.draft-view-alert {
  margin-bottom: 12px;
}

.draft-column-controls {
  display: grid;
  gap: 10px;
  margin-bottom: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(246, 249, 252, 0.92);
  border: 1px solid rgba(126, 143, 158, 0.12);
}

.draft-column-controls strong {
  color: #20364b;
}

.draft-column-controls p {
  margin: 6px 0 0;
  color: #667d91;
  font-size: 13px;
  line-height: 1.6;
}

.draft-column-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.employment-copy {
  color: #4f6578;
  line-height: 1.6;
}

.employment-copy strong {
  color: #20364b;
}

.drag-handle {
  width: 100%;
  min-height: 32px;
  border: 1px dashed rgba(99, 122, 146, 0.32);
  border-radius: 10px;
  background: rgba(247, 250, 253, 0.94);
  color: #587189;
  font-size: 12px;
  cursor: grab;
  transition: border-color 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.drag-handle.dragging {
  cursor: grabbing;
  border-color: rgba(59, 112, 177, 0.42);
  background: rgba(236, 245, 255, 0.96);
  color: #1d4f8f;
}

.drag-handle.drop-target {
  border-color: rgba(56, 143, 94, 0.42);
  background: rgba(241, 250, 244, 0.98);
  color: #226443;
}

.draft-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.draft-group-stack {
  display: grid;
  gap: 14px;
}

.draft-group-card {
  padding: 14px;
  border-radius: 18px;
  border: 1px solid rgba(126, 143, 158, 0.12);
  background: rgba(255, 255, 255, 0.86);
}

.draft-group-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.draft-group-head h4 {
  margin: 0;
  color: #20364b;
  font-size: 15px;
}

.draft-group-head p {
  margin: 6px 0 0;
  color: #6a8094;
  font-size: 13px;
  line-height: 1.6;
}

.saved-drafts-panel {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(126, 143, 158, 0.12);
}

.draft-comparison-panel {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(126, 143, 158, 0.12);
}

.saved-draft-list {
  display: grid;
  gap: 10px;
}

.saved-draft-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(126, 143, 158, 0.12);
}

.saved-draft-card.active {
  border-color: rgba(50, 109, 177, 0.28);
  box-shadow: 0 10px 20px rgba(46, 90, 138, 0.08);
}

.saved-draft-card strong {
  color: #20364b;
}

.saved-draft-card p {
  margin: 6px 0 0;
  color: #6a8094;
  font-size: 13px;
}

.saved-draft-card span {
  display: block;
  margin-top: 6px;
  color: #8498aa;
  font-size: 12px;
}

.draft-card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.comparison-controls {
  width: min(320px, 100%);
}

.comparison-controls :deep(.el-select) {
  width: 100%;
}

.comparison-summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.comparison-summary-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(126, 143, 158, 0.12);
  background: rgba(255, 255, 255, 0.88);
}

.comparison-summary-card span {
  display: block;
  color: #647b8f;
  font-size: 13px;
}

.comparison-summary-card strong {
  display: block;
  margin-top: 10px;
  color: #20364b;
  font-size: 24px;
  line-height: 1.1;
}

.comparison-summary-card p {
  margin: 8px 0 0;
  color: #6a8094;
  font-size: 12px;
  line-height: 1.6;
}

.comparison-summary-card.tone-blue {
  background: rgba(242, 248, 255, 0.94);
  border-color: rgba(78, 123, 186, 0.18);
}

.comparison-summary-card.tone-slate {
  background: rgba(247, 249, 252, 0.95);
  border-color: rgba(116, 132, 148, 0.16);
}

.comparison-summary-card.tone-amber {
  background: rgba(255, 249, 239, 0.96);
  border-color: rgba(194, 136, 47, 0.18);
}

.comparison-summary-card.tone-green {
  background: rgba(243, 251, 246, 0.95);
  border-color: rgba(68, 143, 92, 0.18);
}

.comparison-summary-card.tone-ink {
  background: rgba(244, 247, 251, 0.96);
  border-color: rgba(80, 102, 125, 0.16);
}

.comparison-column-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 14px;
}

.comparison-column {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(126, 143, 158, 0.12);
  background: rgba(255, 255, 255, 0.88);
}

.comparison-column header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.comparison-column h4 {
  margin: 0;
  color: #20364b;
  font-size: 15px;
}

.comparison-column header span {
  color: #6a8094;
  font-size: 12px;
}

.comparison-item-list {
  display: grid;
  gap: 10px;
}

.comparison-item {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(246, 249, 252, 0.95);
  border: 1px solid rgba(126, 143, 158, 0.1);
}

.comparison-item strong {
  display: block;
  color: #20364b;
  line-height: 1.5;
}

.comparison-item span {
  display: block;
  margin-top: 6px;
  color: #607588;
  font-size: 12px;
  line-height: 1.5;
}

.comparison-empty {
  padding: 14px;
  border-radius: 14px;
  color: #7a8ea1;
  font-size: 13px;
  line-height: 1.6;
  background: rgba(247, 250, 253, 0.92);
}

.comparison-placeholder.inner {
  margin-top: 8px;
}

@media (max-width: 1080px) {
  .draft-toolbar-card {
    flex-direction: column;
    align-items: stretch;
  }

  .draft-toolbar-actions {
    grid-template-columns: 1fr;
    width: 100%;
  }

  .career-grid,
  .career-path-grid,
  .insight-grid,
  .workbench-grid {
    grid-template-columns: 1fr;
  }

  .saved-draft-card {
    flex-direction: column;
    align-items: stretch;
  }

  .comparison-summary-grid,
  .comparison-column-grid {
    grid-template-columns: 1fr;
  }

  .comparison-controls {
    width: 100%;
  }
}
</style>
