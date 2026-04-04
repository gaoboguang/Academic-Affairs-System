<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">升学中心 / 推荐方案</div>
        <h2 class="page-title">升学推荐</h2>
        <p class="page-subtitle">
          把院校库、专业库、历年录取库和推荐结果放在同一个工作流里，先维护数据，再生成普通生或艺体生推荐，并保留历史方案与导出入口。
        </p>
        <div class="page-chip-row recommendation-chip-row">
          <span v-for="item in summaryCards" :key="item.label" class="page-chip">
            <strong>{{ item.label }}</strong>{{ item.value }}
          </span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="downloadAdmissionTemplate">录取模板下载</el-button>
        <el-button @click="activeTab = 'admissions'">查看录取库</el-button>
        <el-button type="primary" @click="activeTab = 'recommendations'">生成推荐</el-button>
      </div>
    </header>

    <section class="hero-grid">
      <div class="soft-card summary-panel">
        <div class="summary-copy">
          <div class="summary-badge">位次优先 · 分数补位 · 风险显式</div>
          <h3>把“冲 / 稳 / 保”从静态表格变成可追溯方案</h3>
          <p>
            院校库、专业库、历年录取数据、推荐方案、历史记录和报告导出都在同一页处理。推荐结果始终附带依据与风险提示，便于班主任、年级组和家长共同核对。
          </p>
        </div>
        <div class="summary-metrics">
          <article v-for="item in summaryCards" :key="item.label" class="summary-metric" :class="item.tone">
            <div class="summary-metric-label">{{ item.label }}</div>
            <div class="summary-metric-value">{{ item.value }}</div>
            <div class="summary-metric-help">{{ item.help }}</div>
          </article>
        </div>
      </div>

      <div class="soft-card workflow-panel">
        <div class="section-head compact">
          <div>
            <h3>推荐闭环</h3>
            <p>先保证数据质量，再做推荐解释与导出。</p>
          </div>
        </div>
        <div class="workflow-list">
          <div class="workflow-item">
            <span>01</span>
            <div>
              <strong>维护院校与专业</strong>
              <p>支持层级标签、艺体招生标记和院校别名。</p>
            </div>
          </div>
          <div class="workflow-item">
            <span>02</span>
            <div>
              <strong>导入历年录取数据</strong>
              <p>按年份、省份、院校、专业和学生类别长期累积。</p>
            </div>
          </div>
          <div class="workflow-item">
            <span>03</span>
            <div>
              <strong>生成并保存推荐方案</strong>
              <p>普通生和艺体生共用入口，但保留不同的评分依据。</p>
            </div>
          </div>
          <div class="workflow-item">
            <span>04</span>
            <div>
              <strong>查看历史与导出报告</strong>
              <p>支持历史方案回看和单个学生推荐单导出。</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <el-tabs v-model="activeTab" class="recommendation-tabs">
      <el-tab-pane label="院校库" name="colleges">
        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>院校库</h3>
              <p>维护基础院校信息、层级标签、艺体招生标记和别名，为录取清洗与推荐筛选提供基底。</p>
            </div>
            <div class="action-row">
              <el-button @click="loadColleges">刷新</el-button>
              <el-button type="primary" @click="openCreateCollege">新增院校</el-button>
            </div>
          </div>

          <div class="filter-grid">
            <el-input v-model="collegeFilters.keyword" placeholder="按院校名称或别名筛选" />
            <el-select v-model="collegeFilters.province" clearable filterable placeholder="省份">
              <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
            </el-select>
            <el-select v-model="collegeFilters.supports_art" placeholder="艺体招生">
              <el-option label="全部" value="all" />
              <el-option label="支持艺体" value="true" />
              <el-option label="仅普通招生" value="false" />
            </el-select>
          </div>

          <div class="action-row toolbar-row">
            <el-button type="primary" @click="loadColleges">查询</el-button>
            <el-button @click="resetCollegeFilters">重置</el-button>
          </div>

          <el-table :data="colleges" stripe>
            <el-table-column label="院校" min-width="220">
              <template #default="{ row }">
                <div class="name-stack">
                  <strong>{{ row.name }}</strong>
                  <span v-if="row.college_code">{{ row.college_code }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="地区" min-width="130">
              <template #default="{ row }">
                {{ [row.province, row.city].filter(Boolean).join(" / ") || "-" }}
              </template>
            </el-table-column>
            <el-table-column label="类型" prop="school_type" min-width="110" />
            <el-table-column label="层级标签" min-width="180">
              <template #default="{ row }">
                <div class="tag-cluster">
                  <el-tag v-for="tag in row.school_level_tags_json ?? []" :key="tag" size="small">{{ tag }}</el-tag>
                  <span v-if="!(row.school_level_tags_json ?? []).length" class="muted-copy">未标注</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="艺体" width="100">
              <template #default="{ row }">
                <el-tag :type="row.supports_art ? 'warning' : 'info'" effect="light">
                  {{ row.supports_art ? "支持" : "否" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="别名" min-width="180">
              <template #default="{ row }">
                <div class="tag-cluster">
                  <el-tag v-for="item in row.alias_names ?? []" :key="item" size="small" effect="plain">
                    {{ item }}
                  </el-tag>
                  <span v-if="!(row.alias_names ?? []).length" class="muted-copy">无</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" effect="light">
                  {{ row.is_active ? "启用" : "停用" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEditCollege(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!colleges.length" description="暂无院校数据" />
        </section>
      </el-tab-pane>

      <el-tab-pane label="专业库" name="majors">
        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>专业库</h3>
              <p>维护专业方向、门类、就业去向和艺体相关标记，供录取数据清洗和专业偏好筛选复用。</p>
            </div>
            <div class="action-row">
              <el-button @click="loadMajors">刷新</el-button>
              <el-button type="primary" @click="openCreateMajor">新增专业</el-button>
            </div>
          </div>

          <div class="filter-grid">
            <el-input v-model="majorFilters.keyword" placeholder="按专业名称筛选" />
            <el-select v-model="majorFilters.is_art_related" placeholder="艺体相关">
              <el-option label="全部" value="all" />
              <el-option label="艺体相关" value="true" />
              <el-option label="非艺体" value="false" />
            </el-select>
          </div>

          <div class="action-row toolbar-row">
            <el-button type="primary" @click="loadMajors">查询</el-button>
            <el-button @click="resetMajorFilters">重置</el-button>
          </div>

          <el-table :data="majors" stripe>
            <el-table-column label="专业" min-width="220">
              <template #default="{ row }">
                <div class="name-stack">
                  <strong>{{ row.name }}</strong>
                  <span v-if="row.major_code">{{ row.major_code }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="门类" prop="category" min-width="140" />
            <el-table-column label="方向" prop="direction" min-width="160" />
            <el-table-column label="就业去向" prop="career_path" min-width="200" />
            <el-table-column label="艺体" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_art_related ? 'warning' : 'info'" effect="light">
                  {{ row.is_art_related ? "相关" : "否" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" effect="light">
                  {{ row.is_active ? "启用" : "停用" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openEditMajor(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!majors.length" description="暂无专业数据" />
        </section>
      </el-tab-pane>

      <el-tab-pane label="录取库" name="admissions">
        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>历年录取数据</h3>
              <p>按年份、省份、院校、专业和学生类别维护录取基线，为推荐引擎提供近三年参考数据。</p>
            </div>
            <div class="action-row">
              <el-button @click="downloadAdmissionTemplate">模板下载</el-button>
              <el-upload :show-file-list="false" :auto-upload="false" :on-change="handleAdmissionImport">
                <el-button type="primary">导入录取数据</el-button>
              </el-upload>
            </div>
          </div>

          <el-alert
            v-if="admissionImportResult"
            class="result-alert"
            :title="admissionImportResult.message"
            type="success"
            show-icon
            :closable="false"
          >
            <template #default>
              成功 {{ admissionImportResult.success_rows }} 行，失败 {{ admissionImportResult.failed_rows }} 行，
              新增院校 {{ admissionImportResult.created_college_count }} 所，新增专业
              {{ admissionImportResult.created_major_count }} 个。
            </template>
          </el-alert>

          <div class="filter-grid">
            <el-select v-model="admissionFilters.year" clearable placeholder="年份">
              <el-option v-for="year in admissionYearOptions" :key="year" :label="String(year)" :value="year" />
            </el-select>
            <el-select v-model="admissionFilters.province" clearable filterable placeholder="省份">
              <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
            </el-select>
            <el-select v-model="admissionFilters.college_id" clearable filterable placeholder="院校">
              <el-option v-for="college in collegeDirectory" :key="college.id" :label="college.name" :value="college.id" />
            </el-select>
          </div>

          <div class="action-row toolbar-row">
            <el-button type="primary" @click="loadAdmissions">查询</el-button>
            <el-button @click="resetAdmissionFilters">重置</el-button>
          </div>

          <el-table :data="admissions" stripe>
            <el-table-column label="年份" prop="year" width="90" />
            <el-table-column label="省份" prop="province" width="110" />
            <el-table-column label="批次" prop="batch" min-width="110" />
            <el-table-column label="院校" prop="college_name" min-width="180" />
            <el-table-column label="专业" prop="major_name" min-width="180" />
            <el-table-column label="学生类别" prop="student_type" width="110" />
            <el-table-column label="最低分" prop="min_score" width="100" />
            <el-table-column label="最低位次" prop="min_rank" width="110" />
            <el-table-column label="选科要求" prop="subject_requirement" min-width="120" />
            <el-table-column label="数据来源" prop="source_note" min-width="180" />
          </el-table>
          <el-empty v-if="!admissions.length" description="暂无录取数据" />
        </section>
      </el-tab-pane>

      <el-tab-pane label="推荐中心" name="recommendations">
        <div class="recommend-layout">
          <section class="soft-card panel-block">
            <div class="section-head">
              <div>
                <h3>生成推荐方案</h3>
                <p>单个学生支持位次覆盖、综合分输入和艺体辅助参数，批量模式则复用统一筛选条件。</p>
              </div>
              <el-radio-group v-model="generationMode" size="default">
                <el-radio-button label="single">单个学生</el-radio-button>
                <el-radio-button label="batch">批量学生</el-radio-button>
              </el-radio-group>
            </div>

            <div class="filter-grid">
              <el-select
                v-if="!isBatchMode"
                v-model="recommendationForm.student_id"
                filterable
                placeholder="选择学生"
              >
                <el-option
                  v-for="student in studentOptions"
                  :key="student.id"
                  :label="`${student.student_no} - ${student.name}`"
                  :value="student.id"
                />
              </el-select>
              <el-select
                v-else
                v-model="recommendationForm.student_ids"
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
              <el-select v-model="recommendationForm.exam_id" filterable placeholder="参考考试">
                <el-option v-for="exam in examOptions" :key="exam.id" :label="exam.name" :value="exam.id" />
              </el-select>
              <el-select v-model="recommendationForm.province" filterable placeholder="省份">
                <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
              </el-select>
              <el-input v-model="recommendationForm.name" placeholder="方案名称，可选" />
              <el-input v-model="recommendationForm.subject_combination" placeholder="选科组合，可选" />
              <el-select
                v-model="recommendationForm.target_regions_json"
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
                v-model="recommendationForm.school_level_tags_json"
                multiple
                filterable
                allow-create
                default-first-option
                collapse-tags
                placeholder="院校层级偏好"
              >
                <el-option
                  v-for="item in schoolLevelOptions"
                  :key="item"
                  :label="item"
                  :value="item"
                />
              </el-select>
              <el-input v-model="recommendationForm.major_keyword" placeholder="专业方向关键词，可选" />
              <el-switch v-model="recommendationForm.obey_adjustment" inline-prompt active-text="服从" inactive-text="不服从" />
              <el-input-number
                v-if="!isBatchMode"
                v-model="recommendationForm.student_rank_override"
                :min="1"
                :max="999999"
                controls-position="right"
                style="width: 100%"
                placeholder="位次覆盖"
              />
              <el-input-number
                v-if="!isBatchMode"
                v-model="recommendationForm.comprehensive_score"
                :min="0"
                :max="1000"
                controls-position="right"
                style="width: 100%"
                placeholder="综合分"
              />
              <el-input-number
                v-if="!isBatchMode"
                v-model="recommendationForm.culture_score"
                :min="0"
                :max="1000"
                controls-position="right"
                style="width: 100%"
                placeholder="文化分"
              />
              <el-input-number
                v-if="!isBatchMode"
                v-model="recommendationForm.professional_score"
                :min="0"
                :max="1000"
                controls-position="right"
                style="width: 100%"
                placeholder="专业分"
              />
            </div>

            <el-input
              v-model="recommendationForm.note"
              class="note-box"
              type="textarea"
              :rows="3"
              placeholder="补充说明、人工判断依据或特别关注项"
            />

            <div class="action-row toolbar-row">
              <el-button type="primary" :loading="generating" @click="submitRecommendation">
                {{ isBatchMode ? "批量生成" : "生成推荐" }}
              </el-button>
              <el-button @click="resetRecommendationForm">重置参数</el-button>
            </div>

            <el-alert
              v-if="latestGenerationMessage"
              class="result-alert"
              :title="latestGenerationMessage"
              :type="latestGeneration ? 'success' : 'info'"
              show-icon
              :closable="false"
            />
          </section>

          <div class="recommend-side-stack">
            <section class="soft-card panel-block">
              <div class="section-head">
                <div>
                  <h3>推荐策略</h3>
                  <p>把冲稳保阈值、白名单和黑名单做成可调配置，避免每次都靠临时人工备注修正。</p>
                </div>
                <div class="action-row">
                  <el-button @click="loadRecommendationSettings">重载</el-button>
                  <el-button type="primary" :loading="savingSettings" @click="saveRecommendationSettings">
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
                  v-model="recommendationSettings.safe_ratio_max"
                  :precision="2"
                  :step="0.01"
                  :min="0.1"
                  :max="2"
                  controls-position="right"
                  style="width: 100%"
                  placeholder="保底阈值"
                />
                <el-input-number
                  v-model="recommendationSettings.steady_ratio_max"
                  :precision="2"
                  :step="0.01"
                  :min="0.1"
                  :max="2"
                  controls-position="right"
                  style="width: 100%"
                  placeholder="稳妥阈值"
                />
                <el-input-number
                  v-model="recommendationSettings.rush_ratio_max"
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
                  v-model="recommendationSettings.whitelist_college_ids"
                  multiple
                  collapse-tags
                  clearable
                  filterable
                  placeholder="白名单院校"
                >
                  <el-option
                    v-for="college in collegeDirectory"
                    :key="college.id"
                    :label="college.name"
                    :value="college.id"
                  />
                </el-select>
                <el-select
                  v-model="recommendationSettings.blacklist_college_ids"
                  multiple
                  collapse-tags
                  clearable
                  filterable
                  placeholder="黑名单院校"
                >
                  <el-option
                    v-for="college in collegeDirectory"
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
                    v-model="selectedStrategyPresetId"
                    clearable
                    filterable
                    placeholder="选择已有模板"
                  >
                    <el-option
                      v-for="preset in recommendationSettings.strategy_presets"
                      :key="preset.id"
                      :label="preset.name"
                      :value="preset.id"
                    />
                  </el-select>
                  <el-input v-model="strategyPresetForm.name" placeholder="模板名称" />
                  <el-input v-model="strategyPresetForm.note" placeholder="模板说明，可选" />
                </div>

                <div class="action-row toolbar-row">
                  <el-button :disabled="!selectedStrategyPreset" @click="applyStrategyPreset">应用模板</el-button>
                  <el-button
                    :disabled="!selectedStrategyPreset"
                    :loading="deletingPresetId === selectedStrategyPresetId"
                    @click="deleteStrategyPreset"
                  >
                    删除模板
                  </el-button>
                  <el-button type="primary" :loading="savingPreset" @click="saveStrategyPreset">保存为模板</el-button>
                </div>

                <div v-if="recommendationSettings.strategy_presets.length" class="preset-grid">
                  <article
                    v-for="preset in recommendationSettings.strategy_presets"
                    :key="preset.id"
                    class="preset-card"
                    :class="{ selected: preset.id === selectedStrategyPresetId }"
                    @click="selectedStrategyPresetId = preset.id"
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

            <section class="soft-card panel-block">
              <div class="section-head">
                <div>
                  <h3>推荐历史</h3>
                  <p>按学生查看历史方案，支持再次查看结果与导出推荐报告。</p>
                </div>
              </div>

              <div class="filter-grid">
                <el-select v-model="historyFilters.student_id" clearable filterable placeholder="按学生筛选历史">
                  <el-option
                    v-for="student in studentOptions"
                    :key="student.id"
                    :label="`${student.student_no} - ${student.name}`"
                    :value="student.id"
                  />
                </el-select>
              </div>

              <div class="action-row toolbar-row">
                <el-button type="primary" @click="loadHistory">查询历史</el-button>
                <el-button @click="resetHistoryFilters">重置</el-button>
              </div>

              <el-table :data="historyItems" stripe max-height="360">
                <el-table-column label="方案" prop="scheme_name" min-width="180" />
                <el-table-column label="学生" prop="student_name" min-width="110" />
                <el-table-column label="省份" prop="province" width="90" />
                <el-table-column label="类别" prop="student_type" width="90" />
                <el-table-column label="结果数" prop="result_count" width="80" />
                <el-table-column label="生成时间" prop="generated_at" min-width="170" />
                <el-table-column label="操作" width="150" fixed="right">
                  <template #default="{ row }">
                    <div class="action-row compact-actions">
                      <el-button link type="primary" @click="viewScheme(row)">查看</el-button>
                      <el-button link type="primary" @click="exportScheme(row)">导出</el-button>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-if="!historyItems.length" description="暂无推荐历史" />
            </section>
          </div>
        </div>

        <section v-if="selectedSchemeMeta" class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>方案结果</h3>
              <p>
                {{ selectedSchemeMeta.scheme_name }} · {{ selectedSchemeMeta.student_name }} ·
                {{ selectedSchemeMeta.province }}
              </p>
            </div>
            <div class="action-row">
              <el-tag type="danger" effect="light">冲 {{ groupedResults.challenge.length }}</el-tag>
              <el-tag type="warning" effect="light">稳 {{ groupedResults.steady.length }}</el-tag>
              <el-tag type="success" effect="light">保 {{ groupedResults.safe.length }}</el-tag>
              <el-button
                type="primary"
                plain
                :loading="exportingScheme === selectedSchemeMeta.scheme_id"
                @click="exportScheme(selectedSchemeMeta)"
              >
                导出推荐单
              </el-button>
            </div>
          </div>

          <div class="comparison-toolbar">
            <div class="comparison-copy">
              <strong>方案对比</strong>
              <p>
                和同一学生的历史方案做差异对比，直接看新增、移除和冲稳保分组变化。
              </p>
            </div>
            <div class="comparison-controls">
              <el-select
                v-model="compareSchemeId"
                clearable
                filterable
                placeholder="选择历史方案对比"
                @change="handleCompareSchemeChange"
              >
                <el-option
                  v-for="item in compareHistoryOptions"
                  :key="item.scheme_id"
                  :label="`${item.scheme_name} · ${item.generated_at}`"
                  :value="item.scheme_id"
                />
              </el-select>
            </div>
          </div>

          <div class="result-board-grid">
            <article
              v-for="column in resultColumns"
              :key="column.key"
              class="result-column"
              :class="column.key"
            >
              <header class="result-column-head">
                <div>
                  <span class="result-pill">{{ column.label }}</span>
                  <h4>{{ groupedResults[column.key].length }} 条结果</h4>
                </div>
                <span class="result-tip">{{ column.tip }}</span>
              </header>

              <div v-if="groupedResults[column.key].length" class="result-card-list">
                <article v-for="item in groupedResults[column.key]" :key="item.id" class="result-card">
                  <div class="result-card-head">
                    <div>
                      <h5>{{ item.college_name }}</h5>
                      <p>{{ item.major_name || "院校级推荐" }}</p>
                    </div>
                    <span class="ratio-badge">
                      {{ item.ratio !== null && item.ratio !== undefined ? `比值 ${item.ratio}` : item.score_basis }}
                    </span>
                  </div>
                  <dl class="detail-grid">
                    <div>
                      <dt>参考位次</dt>
                      <dd>{{ item.reference_rank ?? "-" }}</dd>
                    </div>
                    <div>
                      <dt>学生位次</dt>
                      <dd>{{ item.student_rank ?? "-" }}</dd>
                    </div>
                    <div>
                      <dt>依据</dt>
                      <dd>{{ item.score_basis }}</dd>
                    </div>
                    <div>
                      <dt>近年数据</dt>
                      <dd>{{ formatReferenceYears(item.snapshot_json) }}</dd>
                    </div>
                  </dl>
                  <p class="reason-copy">{{ item.reason_text || "暂无理由说明" }}</p>
                  <div class="tag-cluster">
                    <el-tag
                      v-for="flag in item.risk_flags_json ?? []"
                      :key="flag"
                      size="small"
                      type="warning"
                      effect="light"
                    >
                      {{ riskFlagText(flag) }}
                    </el-tag>
                    <span v-if="!(item.risk_flags_json ?? []).length" class="muted-copy">无额外风险提示</span>
                  </div>
                </article>
              </div>
              <el-empty v-else description="暂无结果" />
            </article>
          </div>

          <section class="comparison-panel">
            <div v-if="comparingScheme" class="comparison-placeholder">
              正在加载对比方案...
            </div>
            <template v-else-if="selectedCompareSchemeMeta && schemeComparison">
              <div class="comparison-summary-grid">
                <article class="comparison-summary-card tone-blue">
                  <span>新增志愿</span>
                  <strong>{{ schemeComparison.added.length }}</strong>
                  <p>当前方案新增但旧方案没有的院校/专业。</p>
                </article>
                <article class="comparison-summary-card tone-slate">
                  <span>移除志愿</span>
                  <strong>{{ schemeComparison.removed.length }}</strong>
                  <p>旧方案存在但当前方案已经移除的院校/专业。</p>
                </article>
                <article class="comparison-summary-card tone-amber">
                  <span>分组变化</span>
                  <strong>{{ schemeComparison.changed.length }}</strong>
                  <p>同一院校/专业仍在，但冲稳保分组已变化。</p>
                </article>
                <article class="comparison-summary-card tone-green">
                  <span>稳定保留</span>
                  <strong>{{ schemeComparison.commonCount }}</strong>
                  <p>院校/专业及分组均保持一致。</p>
                </article>
              </div>

              <div class="comparison-delta-grid">
                <article
                  v-for="item in schemeComparison.deltaByGroup"
                  :key="item.key"
                  class="comparison-delta-card"
                >
                  <div>
                    <span>{{ item.label }}</span>
                    <strong>{{ item.current }}</strong>
                  </div>
                  <p>
                    对比 {{ item.compare }} 条，
                    <span :class="item.delta > 0 ? 'delta-up' : item.delta < 0 ? 'delta-down' : 'delta-flat'">
                      {{ formatSignedDelta(item.delta) }}
                    </span>
                  </p>
                </article>
              </div>

              <div class="comparison-column-grid">
                <article class="comparison-column">
                  <header>
                    <h4>新增</h4>
                    <span>{{ schemeComparison.added.length }} 条</span>
                  </header>
                  <div v-if="schemeComparison.added.length" class="comparison-item-list">
                    <div v-for="item in schemeComparison.added" :key="item.key" class="comparison-item">
                      <strong>{{ item.label }}</strong>
                      <span>{{ resultGroupLabel(item.currentType) }}</span>
                    </div>
                  </div>
                  <div v-else class="comparison-empty">当前方案没有新增志愿。</div>
                </article>

                <article class="comparison-column">
                  <header>
                    <h4>移除</h4>
                    <span>{{ schemeComparison.removed.length }} 条</span>
                  </header>
                  <div v-if="schemeComparison.removed.length" class="comparison-item-list">
                    <div v-for="item in schemeComparison.removed" :key="item.key" class="comparison-item">
                      <strong>{{ item.label }}</strong>
                      <span>{{ resultGroupLabel(item.compareType) }}</span>
                    </div>
                  </div>
                  <div v-else class="comparison-empty">当前方案没有移除旧志愿。</div>
                </article>

                <article class="comparison-column">
                  <header>
                    <h4>分组变化</h4>
                    <span>{{ schemeComparison.changed.length }} 条</span>
                  </header>
                  <div v-if="schemeComparison.changed.length" class="comparison-item-list">
                    <div v-for="item in schemeComparison.changed" :key="item.key" class="comparison-item">
                      <strong>{{ item.label }}</strong>
                      <span>{{ resultGroupLabel(item.compareType) }} → {{ resultGroupLabel(item.currentType) }}</span>
                    </div>
                  </div>
                  <div v-else class="comparison-empty">当前方案的分组结构没有变化。</div>
                </article>
              </div>
            </template>
            <div v-else class="comparison-placeholder">
              {{ compareHistoryOptions.length ? "选择同一学生的历史方案即可查看差异。" : "当前学生暂无可对比的历史方案。" }}
            </div>

            <div class="comparison-divider"></div>

            <div class="comparison-toolbar">
              <div class="comparison-copy">
                <strong>批量对照</strong>
                <p>
                  一次选择多份历史方案，快速看每一版与当前方案之间的新增、移除和分组变化。
                </p>
              </div>
              <div class="comparison-controls">
                <el-select
                  v-model="multiCompareSchemeIds"
                  multiple
                  collapse-tags
                  clearable
                  filterable
                  placeholder="选择多个历史方案"
                  @change="handleMultiCompareChange"
                >
                  <el-option
                    v-for="item in compareHistoryOptions"
                    :key="item.scheme_id"
                    :label="`${item.scheme_name} · ${item.generated_at}`"
                    :value="item.scheme_id"
                  />
                </el-select>
              </div>
            </div>

            <el-table v-if="multiSchemeComparisonRows.length" :data="multiSchemeComparisonRows" stripe style="margin-top: 16px">
              <el-table-column label="方案" prop="scheme_name" min-width="180" />
              <el-table-column label="生成时间" prop="generated_at" min-width="170" />
              <el-table-column label="结果数" prop="result_count" width="80" />
              <el-table-column label="冲/稳/保" min-width="120">
                <template #default="{ row }">
                  {{ row.challenge_count }} / {{ row.steady_count }} / {{ row.safe_count }}
                </template>
              </el-table-column>
              <el-table-column label="新增" prop="added_count" width="80" />
              <el-table-column label="移除" prop="removed_count" width="80" />
              <el-table-column label="变化" prop="changed_count" width="80" />
              <el-table-column label="稳定保留" prop="common_count" width="90" />
              <el-table-column label="差异总量" width="100">
                <template #default="{ row }">
                  {{ row.added_count + row.removed_count + row.changed_count }}
                </template>
              </el-table-column>
            </el-table>
            <div v-else class="comparison-placeholder">
              {{ multiCompareSchemeIds.length ? "正在整理多方案差异..." : "选择多个历史方案后，这里会出现批量对照表。" }}
            </div>
          </section>

          <el-table :data="selectedSchemeResults" stripe style="margin-top: 18px">
            <el-table-column label="分组" prop="result_type" width="90" />
            <el-table-column label="院校" prop="college_name" min-width="180" />
            <el-table-column label="专业" prop="major_name" min-width="180" />
            <el-table-column label="参考位次" prop="reference_rank" width="100" />
            <el-table-column label="学生位次" prop="student_rank" width="100" />
            <el-table-column label="依据" prop="score_basis" width="120" />
            <el-table-column label="理由" prop="reason_text" min-width="280" />
          </el-table>
        </section>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="collegeDialogVisible"
      :title="collegeDialogTitle"
      width="760px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleCollegeDialogClosed"
    >
      <el-form label-width="92px">
        <div class="form-grid">
          <el-form-item label="院校名称">
            <el-input v-model="collegeForm.name" />
          </el-form-item>
          <el-form-item label="院校代码">
            <el-input v-model="collegeForm.college_code" />
          </el-form-item>
          <el-form-item label="省份">
            <el-select v-model="collegeForm.province" clearable filterable style="width: 100%">
              <el-option v-for="province in provinceOptions" :key="province" :label="province" :value="province" />
            </el-select>
          </el-form-item>
          <el-form-item label="城市">
            <el-input v-model="collegeForm.city" />
          </el-form-item>
          <el-form-item label="院校类型">
            <el-input v-model="collegeForm.school_type" />
          </el-form-item>
          <el-form-item label="官网">
            <el-input v-model="collegeForm.website" />
          </el-form-item>
          <el-form-item label="层级标签" class="span-two">
            <el-select
              v-model="collegeForm.school_level_tags_json"
              multiple
              filterable
              allow-create
              default-first-option
              collapse-tags
              style="width: 100%"
            >
              <el-option v-for="item in schoolLevelOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="院校别名" class="span-two">
            <el-select
              v-model="collegeForm.alias_names"
              multiple
              filterable
              allow-create
              default-first-option
              collapse-tags
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="支持艺体">
            <el-switch v-model="collegeForm.supports_art" />
          </el-form-item>
          <el-form-item label="启用">
            <el-switch v-model="collegeForm.is_active" />
          </el-form-item>
          <el-form-item label="简介" class="span-two">
            <el-input v-model="collegeForm.intro" type="textarea" :rows="3" />
          </el-form-item>
          <el-form-item label="备注" class="span-two">
            <el-input v-model="collegeForm.note" type="textarea" :rows="3" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="collegeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingCollege" @click="submitCollege">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="majorDialogVisible"
      :title="majorDialogTitle"
      width="720px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleMajorDialogClosed"
    >
      <el-form label-width="92px">
        <div class="form-grid">
          <el-form-item label="专业名称">
            <el-input v-model="majorForm.name" />
          </el-form-item>
          <el-form-item label="专业代码">
            <el-input v-model="majorForm.major_code" />
          </el-form-item>
          <el-form-item label="专业门类">
            <el-input v-model="majorForm.category" />
          </el-form-item>
          <el-form-item label="专业方向">
            <el-input v-model="majorForm.direction" />
          </el-form-item>
          <el-form-item label="就业去向" class="span-two">
            <el-input v-model="majorForm.career_path" />
          </el-form-item>
          <el-form-item label="艺体相关">
            <el-switch v-model="majorForm.is_art_related" />
          </el-form-item>
          <el-form-item label="启用">
            <el-switch v-model="majorForm.is_active" />
          </el-form-item>
          <el-form-item label="备注" class="span-two">
            <el-input v-model="majorForm.note" type="textarea" :rows="3" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="majorDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingMajor" @click="submitMajor">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import type { UploadFile } from "element-plus";

import { apiRequest, openFile, uploadFile } from "../api/client";
import { useReferenceStore } from "../stores/reference";

type BoolFilter = "all" | "true" | "false";
type ResultGroupKey = "challenge" | "steady" | "safe";

interface ExamOption {
  id: number;
  name: string;
}

interface StudentOption {
  id: number;
  student_no: string;
  name: string;
}

interface CollegeItem {
  id: number;
  name: string;
  college_code?: string | null;
  province?: string | null;
  city?: string | null;
  school_type?: string | null;
  school_level_tags_json?: string[] | null;
  intro?: string | null;
  website?: string | null;
  supports_art: boolean;
  note?: string | null;
  alias_names?: string[] | null;
  is_active: boolean;
}

interface CollegePayload {
  name: string;
  college_code: string | null;
  province: string | null;
  city: string | null;
  school_type: string | null;
  school_level_tags_json: string[];
  intro: string | null;
  website: string | null;
  supports_art: boolean;
  note: string | null;
  alias_names: string[];
  is_active: boolean;
}

interface MajorItem {
  id: number;
  name: string;
  major_code?: string | null;
  category?: string | null;
  direction?: string | null;
  career_path?: string | null;
  is_art_related: boolean;
  note?: string | null;
  is_active: boolean;
}

interface MajorPayload {
  name: string;
  major_code: string | null;
  category: string | null;
  direction: string | null;
  career_path: string | null;
  is_art_related: boolean;
  note: string | null;
  is_active: boolean;
}

interface AdmissionRecord {
  id: number;
  year: number;
  province: string;
  batch: string;
  college_id: number;
  college_name?: string | null;
  major_id?: number | null;
  major_name?: string | null;
  student_type: string;
  art_track?: string | null;
  subject_requirement?: string | null;
  min_score?: number | null;
  min_rank?: number | null;
  avg_score?: number | null;
  max_score?: number | null;
  plan_count?: number | null;
  source_note?: string | null;
  is_active: boolean;
}

interface AdmissionImportResponse {
  message: string;
  success_rows: number;
  failed_rows: number;
  created_college_count: number;
  created_major_count: number;
}

interface RecommendationHistoryItem {
  scheme_id: number;
  scheme_name: string;
  student_id: number;
  student_name: string;
  exam_id: number;
  province: string;
  student_type: string;
  generated_at: string;
  result_count: number;
  challenge_count: number;
  steady_count: number;
  safe_count: number;
}

interface RecommendationResult {
  id: number;
  student_id: number;
  student_name?: string | null;
  exam_id: number;
  scheme_id: number;
  scheme_name?: string | null;
  result_type: ResultGroupKey;
  college_id: number;
  college_name?: string | null;
  major_id?: number | null;
  major_name?: string | null;
  reference_rank?: number | null;
  student_rank?: number | null;
  score_basis: string;
  ratio?: number | null;
  reason_text?: string | null;
  risk_flags_json?: string[] | null;
  snapshot_json?: Record<string, unknown> | null;
  generated_at: string;
  is_active: boolean;
}

interface RecommendationGenerateResponse {
  scheme_id: number;
  scheme_name: string;
  student_id: number;
  result_count: number;
  challenge: RecommendationResult[];
  steady: RecommendationResult[];
  safe: RecommendationResult[];
}

interface BatchGenerateResponse {
  message: string;
  scheme_ids: number[];
  result_count: number;
}

interface ExportRecord {
  download_url: string;
}

interface RecommendationCollegeOption {
  id: number;
  name: string;
}

interface RecommendationSettings {
  safe_ratio_max: number;
  steady_ratio_max: number;
  rush_ratio_max: number;
  whitelist_college_ids: number[];
  blacklist_college_ids: number[];
  whitelist_colleges: RecommendationCollegeOption[];
  blacklist_colleges: RecommendationCollegeOption[];
  strategy_presets: RecommendationStrategyPreset[];
}

interface RecommendationStrategyPreset {
  id: string;
  name: string;
  note?: string | null;
  safe_ratio_max: number;
  steady_ratio_max: number;
  rush_ratio_max: number;
  whitelist_college_ids: number[];
  blacklist_college_ids: number[];
  whitelist_colleges: RecommendationCollegeOption[];
  blacklist_colleges: RecommendationCollegeOption[];
  created_at: string;
}

interface ComparisonEntry {
  key: string;
  label: string;
  currentType?: ResultGroupKey;
  compareType?: ResultGroupKey;
}

interface MultiSchemeComparisonRow {
  scheme_id: number;
  scheme_name: string;
  generated_at: string;
  result_count: number;
  challenge_count: number;
  steady_count: number;
  safe_count: number;
  added_count: number;
  removed_count: number;
  changed_count: number;
  common_count: number;
}

const provinceOptions = [
  "北京",
  "天津",
  "河北",
  "山西",
  "内蒙古",
  "辽宁",
  "吉林",
  "黑龙江",
  "上海",
  "江苏",
  "浙江",
  "安徽",
  "福建",
  "江西",
  "山东",
  "河南",
  "湖北",
  "湖南",
  "广东",
  "广西",
  "海南",
  "重庆",
  "四川",
  "贵州",
  "云南",
  "西藏",
  "陕西",
  "甘肃",
  "青海",
  "宁夏",
  "新疆",
];

const baseSchoolLevelOptions = ["985", "211", "双一流", "省重点", "市重点", "公办", "民办", "艺体类"];

const resultColumns: Array<{ key: ResultGroupKey; label: string; tip: string }> = [
  { key: "challenge", label: "冲刺", tip: "略高于当前位次，需接受风险" },
  { key: "steady", label: "稳妥", tip: "与历史基线接近，适合作为主干" },
  { key: "safe", label: "保底", tip: "优于历史基线较多，风险相对更低" },
];

const referenceStore = useReferenceStore();

const activeTab = ref("recommendations");
const generationMode = ref<"single" | "batch">("single");

const studentOptions = ref<StudentOption[]>([]);
const examOptions = ref<ExamOption[]>([]);
const collegeDirectory = ref<CollegeItem[]>([]);
const majorDirectory = ref<MajorItem[]>([]);
const colleges = ref<CollegeItem[]>([]);
const majors = ref<MajorItem[]>([]);
const admissions = ref<AdmissionRecord[]>([]);
const historyItems = ref<RecommendationHistoryItem[]>([]);
const selectedSchemeResults = ref<RecommendationResult[]>([]);
const selectedSchemeMeta = ref<RecommendationHistoryItem | null>(null);
const admissionImportResult = ref<AdmissionImportResponse | null>(null);
const latestGeneration = ref<RecommendationGenerateResponse | null>(null);
const batchGeneration = ref<BatchGenerateResponse | null>(null);
const compareSchemeResults = ref<RecommendationResult[]>([]);
const multiCompareSchemeResults = ref<Record<number, RecommendationResult[]>>({});

const collegeDialogVisible = ref(false);
const majorDialogVisible = ref(false);
const editingCollegeId = ref<number | null>(null);
const editingMajorId = ref<number | null>(null);
const savingCollege = ref(false);
const savingMajor = ref(false);
const savingSettings = ref(false);
const savingPreset = ref(false);
const generating = ref(false);
const exportingScheme = ref<number | null>(null);
const compareSchemeId = ref<number | undefined>(undefined);
const comparingScheme = ref(false);
const selectedStrategyPresetId = ref<string | undefined>(undefined);
const deletingPresetId = ref<string | null>(null);
const multiCompareSchemeIds = ref<number[]>([]);

const collegeFilters = reactive({
  keyword: "",
  province: "",
  supports_art: "all" as BoolFilter,
});

const majorFilters = reactive({
  keyword: "",
  is_art_related: "all" as BoolFilter,
});

const admissionFilters = reactive({
  year: undefined as number | undefined,
  province: "",
  college_id: undefined as number | undefined,
});

const historyFilters = reactive({
  student_id: undefined as number | undefined,
});

const recommendationForm = reactive({
  name: "",
  student_id: undefined as number | undefined,
  student_ids: [] as number[],
  exam_id: undefined as number | undefined,
  province: "广东",
  target_regions_json: [] as string[],
  school_level_tags_json: [] as string[],
  major_keyword: "",
  subject_combination: "",
  obey_adjustment: false,
  student_rank_override: undefined as number | undefined,
  comprehensive_score: undefined as number | undefined,
  professional_score: undefined as number | undefined,
  culture_score: undefined as number | undefined,
  note: "",
});

const recommendationSettings = reactive<RecommendationSettings>({
  safe_ratio_max: 0.85,
  steady_ratio_max: 1.0,
  rush_ratio_max: 1.15,
  whitelist_college_ids: [],
  blacklist_college_ids: [],
  whitelist_colleges: [],
  blacklist_colleges: [],
  strategy_presets: [],
});

const strategyPresetForm = reactive({
  name: "",
  note: "",
});

const collegeForm = reactive<CollegePayload>(createCollegeForm());
const majorForm = reactive<MajorPayload>(createMajorForm());

const isBatchMode = computed(() => generationMode.value === "batch");

const schoolLevelOptions = computed(() =>
  uniqueStrings([
    ...baseSchoolLevelOptions,
    ...collegeDirectory.value.flatMap((item) => item.school_level_tags_json ?? []),
  ]),
);

const targetRegionOptions = computed(() =>
  uniqueStrings([
    ...provinceOptions,
    ...collegeDirectory.value.map((item) => item.province).filter((item): item is string => Boolean(item)),
    ...collegeDirectory.value.map((item) => item.city).filter((item): item is string => Boolean(item)),
  ]),
);

const admissionYearOptions = computed(() => {
  const years = new Set<number>();
  for (let year = 2026; year >= 2020; year -= 1) years.add(year);
  admissions.value.forEach((item) => years.add(item.year));
  return Array.from(years).sort((left, right) => right - left);
});

const summaryCards = computed(() => [
  {
    label: "院校库",
    value: collegeDirectory.value.length,
    help: `${collegeDirectory.value.filter((item) => item.supports_art).length} 所支持艺体招生`,
    tone: "tone-blue",
  },
  {
    label: "专业库",
    value: majorDirectory.value.length,
    help: `${majorDirectory.value.filter((item) => item.is_art_related).length} 个艺体相关专业`,
    tone: "tone-amber",
  },
  {
    label: "录取库",
    value: admissions.value.length,
    help: `${new Set(admissions.value.map((item) => item.year)).size} 个年度样本`,
    tone: "tone-slate",
  },
  {
    label: "历史方案",
    value: historyItems.value.length,
    help: "保留推荐生成时间、方案名称与结果分组",
    tone: "tone-green",
  },
]);

const strategyCards = computed(() => [
  {
    label: "保底阈值",
    value: `≤ ${recommendationSettings.safe_ratio_max.toFixed(2)}`,
    help: "位次比进入这一段后优先归入保底池。",
    tone: "tone-green",
  },
  {
    label: "稳妥阈值",
    value: `≤ ${recommendationSettings.steady_ratio_max.toFixed(2)}`,
    help: "控制主干志愿的密度，不让稳妥区间过宽。",
    tone: "tone-amber",
  },
  {
    label: "冲刺阈值",
    value: `≤ ${recommendationSettings.rush_ratio_max.toFixed(2)}`,
    help: "超过这一阈值的候选会被排除，不直接展示。",
    tone: "tone-blue",
  },
  {
    label: "白 / 黑名单",
    value: `${recommendationSettings.whitelist_college_ids.length} / ${recommendationSettings.blacklist_college_ids.length}`,
    help: "白名单放宽限制，黑名单直接剔除。",
    tone: "tone-slate",
  },
]);

const groupedResults = computed<Record<ResultGroupKey, RecommendationResult[]>>(() => ({
  challenge: selectedSchemeResults.value.filter((item) => item.result_type === "challenge"),
  steady: selectedSchemeResults.value.filter((item) => item.result_type === "steady"),
  safe: selectedSchemeResults.value.filter((item) => item.result_type === "safe"),
}));

const compareHistoryOptions = computed(() =>
  selectedSchemeMeta.value
    ? historyItems.value.filter(
        (item) =>
          item.student_id === selectedSchemeMeta.value?.student_id &&
          item.scheme_id !== selectedSchemeMeta.value?.scheme_id,
      )
    : [],
);

const selectedCompareSchemeMeta = computed(
  () => compareHistoryOptions.value.find((item) => item.scheme_id === compareSchemeId.value) ?? null,
);

const selectedStrategyPreset = computed(
  () => recommendationSettings.strategy_presets.find((item) => item.id === selectedStrategyPresetId.value) ?? null,
);

const schemeComparison = computed(() => {
  if (!selectedCompareSchemeMeta.value) return null;
  return buildSchemeComparison(compareSchemeResults.value);
});

const multiSchemeComparisonRows = computed<MultiSchemeComparisonRow[]>(() =>
  multiCompareSchemeIds.value
    .map((schemeId) => {
      const meta = compareHistoryOptions.value.find((item) => item.scheme_id === schemeId);
      const results = multiCompareSchemeResults.value[schemeId];
      if (!meta || !results) return null;
      const summary = buildSchemeComparison(results);
      return {
        scheme_id: meta.scheme_id,
        scheme_name: meta.scheme_name,
        generated_at: meta.generated_at,
        result_count: meta.result_count,
        challenge_count: meta.challenge_count,
        steady_count: meta.steady_count,
        safe_count: meta.safe_count,
        added_count: summary.added.length,
        removed_count: summary.removed.length,
        changed_count: summary.changed.length,
        common_count: summary.commonCount,
      };
    })
    .filter((item): item is MultiSchemeComparisonRow => Boolean(item))
    .sort((left, right) => {
      const leftDiff = left.added_count + left.removed_count + left.changed_count;
      const rightDiff = right.added_count + right.removed_count + right.changed_count;
      return leftDiff - rightDiff;
    }),
);

const latestGenerationMessage = computed(() => {
  if (latestGeneration.value) {
    return `已生成方案 ${latestGeneration.value.scheme_name}，共 ${latestGeneration.value.result_count} 条推荐结果。`;
  }
  if (batchGeneration.value) {
    return `${batchGeneration.value.message}，共生成 ${batchGeneration.value.scheme_ids.length} 个方案，累计 ${batchGeneration.value.result_count} 条结果。`;
  }
  return "";
});

const collegeDialogTitle = computed(() => (editingCollegeId.value ? "编辑院校" : "新增院校"));
const majorDialogTitle = computed(() => (editingMajorId.value ? "编辑专业" : "新增专业"));

function createCollegeForm(): CollegePayload {
  return {
    name: "",
    college_code: null,
    province: null,
    city: null,
    school_type: null,
    school_level_tags_json: [],
    intro: null,
    website: null,
    supports_art: false,
    note: null,
    alias_names: [],
    is_active: true,
  };
}

function createMajorForm(): MajorPayload {
  return {
    name: "",
    major_code: null,
    category: null,
    direction: null,
    career_path: null,
    is_art_related: false,
    note: null,
    is_active: true,
  };
}

function uniqueStrings(items: Array<string | null | undefined>): string[] {
  return Array.from(
    new Set(
      items
        .map((item) => item?.trim())
        .filter((item): item is string => Boolean(item)),
    ),
  );
}

function formatReferenceYears(snapshot?: Record<string, unknown> | null): string {
  const years = Array.isArray(snapshot?.reference_years) ? snapshot?.reference_years : [];
  return years.length ? years.join(" / ") : "-";
}

function recommendationKey(item: RecommendationResult): string {
  return `${item.college_id}-${item.major_id ?? 0}`;
}

function recommendationLabel(item: RecommendationResult): string {
  return [item.college_name, item.major_name || "院校级推荐"].filter(Boolean).join(" / ");
}

function resultGroupLabel(resultType?: ResultGroupKey): string {
  if (!resultType) return "-";
  return resultColumns.find((column) => column.key === resultType)?.label ?? resultType;
}

function formatSignedDelta(value: number): string {
  if (value > 0) return `+${value}`;
  return String(value);
}

function buildSchemeComparison(compareResults: RecommendationResult[]) {
  const currentMap = new Map<string, RecommendationResult>();
  const compareMap = new Map<string, RecommendationResult>();
  for (const item of selectedSchemeResults.value) currentMap.set(recommendationKey(item), item);
  for (const item of compareResults) compareMap.set(recommendationKey(item), item);

  const added: ComparisonEntry[] = [];
  const removed: ComparisonEntry[] = [];
  const changed: ComparisonEntry[] = [];
  let commonCount = 0;

  currentMap.forEach((currentItem, key) => {
    const compareItem = compareMap.get(key);
    if (!compareItem) {
      added.push({ key, label: recommendationLabel(currentItem), currentType: currentItem.result_type });
      return;
    }
    if (compareItem.result_type !== currentItem.result_type) {
      changed.push({
        key,
        label: recommendationLabel(currentItem),
        currentType: currentItem.result_type,
        compareType: compareItem.result_type,
      });
      return;
    }
    commonCount += 1;
  });

  compareMap.forEach((compareItem, key) => {
    if (!currentMap.has(key)) {
      removed.push({ key, label: recommendationLabel(compareItem), compareType: compareItem.result_type });
    }
  });

  const compareGroupCounts = compareResults.reduce<Record<ResultGroupKey, number>>(
    (accumulator, item) => {
      accumulator[item.result_type] += 1;
      return accumulator;
    },
    { challenge: 0, steady: 0, safe: 0 },
  );

  return {
    added,
    removed,
    changed,
    commonCount,
    deltaByGroup: resultColumns.map((column) => ({
      key: column.key,
      label: column.label,
      current: groupedResults.value[column.key].length,
      compare: compareGroupCounts[column.key],
      delta: groupedResults.value[column.key].length - compareGroupCounts[column.key],
    })),
  };
}

function riskFlagText(flag: string): string {
  const mapping: Record<string, string> = {
    sample_insufficient: "样本不足",
    rank_missing: "缺少位次，分数参考",
    art_recommendation: "艺体推荐",
    track_unconfirmed: "艺体方向待确认",
    manual_formula_check: "需人工核对招生章程",
    whitelist_override: "白名单放宽",
  };
  return mapping[flag] ?? flag;
}

function downloadAdmissionTemplate(): void {
  openFile(`/api/system/files?path=${encodeURIComponent("data/templates/admission_records_import_template.xlsx")}`);
}

async function loadStudentAndExamOptions(): Promise<void> {
  await referenceStore.loadCore();
  const [studentPayload, examPayload] = await Promise.all([
    apiRequest<{ items: StudentOption[] }>("/api/students?page=1&page_size=200"),
    apiRequest<{ items: ExamOption[] }>("/api/exams?page=1&page_size=200"),
  ]);
  studentOptions.value = studentPayload.items;
  examOptions.value = examPayload.items;
}

async function loadCollegeDirectory(): Promise<void> {
  collegeDirectory.value = await apiRequest<CollegeItem[]>("/api/colleges");
}

async function loadMajorDirectory(): Promise<void> {
  majorDirectory.value = await apiRequest<MajorItem[]>("/api/majors");
}

async function loadColleges(): Promise<void> {
  try {
    const query = new URLSearchParams();
    if (collegeFilters.keyword) query.set("keyword", collegeFilters.keyword);
    if (collegeFilters.province) query.set("province", collegeFilters.province);
    if (collegeFilters.supports_art !== "all") query.set("supports_art", String(collegeFilters.supports_art === "true"));
    colleges.value = await apiRequest<CollegeItem[]>(`/api/colleges?${query.toString()}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadMajors(): Promise<void> {
  try {
    const query = new URLSearchParams();
    if (majorFilters.keyword) query.set("keyword", majorFilters.keyword);
    if (majorFilters.is_art_related !== "all") query.set("is_art_related", String(majorFilters.is_art_related === "true"));
    majors.value = await apiRequest<MajorItem[]>(`/api/majors?${query.toString()}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadAdmissions(): Promise<void> {
  try {
    const query = new URLSearchParams();
    if (admissionFilters.year) query.set("year", String(admissionFilters.year));
    if (admissionFilters.province) query.set("province", admissionFilters.province);
    if (admissionFilters.college_id) query.set("college_id", String(admissionFilters.college_id));
    admissions.value = await apiRequest<AdmissionRecord[]>(`/api/admissions?${query.toString()}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadHistory(): Promise<void> {
  try {
    const query = new URLSearchParams();
    if (historyFilters.student_id) query.set("student_id", String(historyFilters.student_id));
    historyItems.value = await apiRequest<RecommendationHistoryItem[]>(`/api/recommendations/history?${query.toString()}`);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function loadRecommendationSettings(): Promise<void> {
  try {
    const previousPresetId = selectedStrategyPresetId.value;
    const payload = await apiRequest<RecommendationSettings>("/api/recommendations/settings");
    Object.assign(recommendationSettings, payload);
    selectedStrategyPresetId.value = payload.strategy_presets.some((item) => item.id === previousPresetId)
      ? previousPresetId
      : undefined;
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function resetCollegeFilters(): void {
  collegeFilters.keyword = "";
  collegeFilters.province = "";
  collegeFilters.supports_art = "all";
  void loadColleges();
}

function resetMajorFilters(): void {
  majorFilters.keyword = "";
  majorFilters.is_art_related = "all";
  void loadMajors();
}

function resetAdmissionFilters(): void {
  admissionFilters.year = undefined;
  admissionFilters.province = "";
  admissionFilters.college_id = undefined;
  void loadAdmissions();
}

function resetHistoryFilters(): void {
  historyFilters.student_id = undefined;
  void loadHistory();
}

function resetRecommendationForm(): void {
  Object.assign(recommendationForm, {
    name: "",
    student_id: undefined,
    student_ids: [],
    exam_id: undefined,
    province: recommendationForm.province || "广东",
    target_regions_json: [],
    school_level_tags_json: [],
    major_keyword: "",
    subject_combination: "",
    obey_adjustment: false,
    student_rank_override: undefined,
    comprehensive_score: undefined,
    professional_score: undefined,
    culture_score: undefined,
    note: "",
  });
  latestGeneration.value = null;
  batchGeneration.value = null;
}

async function saveRecommendationSettings(): Promise<void> {
  const safeRatioMax = Number(recommendationSettings.safe_ratio_max);
  const steadyRatioMax = Number(recommendationSettings.steady_ratio_max);
  const rushRatioMax = Number(recommendationSettings.rush_ratio_max);
  if (!(safeRatioMax > 0 && safeRatioMax <= steadyRatioMax && steadyRatioMax <= rushRatioMax)) {
    ElMessage.warning("推荐阈值需要满足 保底 <= 稳妥 <= 冲刺");
    return;
  }
  const whitelistCollegeIds = Array.from(new Set(recommendationSettings.whitelist_college_ids));
  const blacklistCollegeIds = Array.from(new Set(recommendationSettings.blacklist_college_ids));
  if (whitelistCollegeIds.some((item) => blacklistCollegeIds.includes(item))) {
    ElMessage.warning("同一院校不能同时存在于白名单和黑名单");
    return;
  }
  try {
    savingSettings.value = true;
    const payload = await apiRequest<RecommendationSettings>("/api/recommendations/settings", {
      method: "PUT",
      body: JSON.stringify({
        safe_ratio_max: safeRatioMax,
        steady_ratio_max: steadyRatioMax,
        rush_ratio_max: rushRatioMax,
        whitelist_college_ids: whitelistCollegeIds,
        blacklist_college_ids: blacklistCollegeIds,
      }),
    });
    Object.assign(recommendationSettings, payload);
    ElMessage.success("推荐策略已保存");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingSettings.value = false;
  }
}

function applyStrategyPreset(): void {
  if (!selectedStrategyPreset.value) return;
  Object.assign(recommendationSettings, {
    safe_ratio_max: selectedStrategyPreset.value.safe_ratio_max,
    steady_ratio_max: selectedStrategyPreset.value.steady_ratio_max,
    rush_ratio_max: selectedStrategyPreset.value.rush_ratio_max,
    whitelist_college_ids: [...selectedStrategyPreset.value.whitelist_college_ids],
    blacklist_college_ids: [...selectedStrategyPreset.value.blacklist_college_ids],
  });
  strategyPresetForm.name = selectedStrategyPreset.value.name;
  strategyPresetForm.note = selectedStrategyPreset.value.note ?? "";
  ElMessage.success(`已应用模板：${selectedStrategyPreset.value.name}`);
}

async function saveStrategyPreset(): Promise<void> {
  if (!strategyPresetForm.name.trim()) {
    ElMessage.warning("请先填写模板名称");
    return;
  }
  try {
    savingPreset.value = true;
    const payload = await apiRequest<RecommendationSettings>("/api/recommendations/strategy-presets", {
      method: "POST",
      body: JSON.stringify({
        name: strategyPresetForm.name.trim(),
        note: strategyPresetForm.note.trim() || undefined,
        safe_ratio_max: recommendationSettings.safe_ratio_max,
        steady_ratio_max: recommendationSettings.steady_ratio_max,
        rush_ratio_max: recommendationSettings.rush_ratio_max,
        whitelist_college_ids: recommendationSettings.whitelist_college_ids,
        blacklist_college_ids: recommendationSettings.blacklist_college_ids,
      }),
    });
    Object.assign(recommendationSettings, payload);
    selectedStrategyPresetId.value = payload.strategy_presets[0]?.id;
    ElMessage.success("策略模板已保存");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingPreset.value = false;
  }
}

async function deleteStrategyPreset(): Promise<void> {
  if (!selectedStrategyPreset.value) return;
  try {
    deletingPresetId.value = selectedStrategyPreset.value.id;
    const payload = await apiRequest<RecommendationSettings>(
      `/api/recommendations/strategy-presets/${selectedStrategyPreset.value.id}`,
      { method: "DELETE" },
    );
    Object.assign(recommendationSettings, payload);
    selectedStrategyPresetId.value = undefined;
    ElMessage.success("策略模板已删除");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    deletingPresetId.value = null;
  }
}

function openCreateCollege(): void {
  editingCollegeId.value = null;
  Object.assign(collegeForm, createCollegeForm());
  collegeDialogVisible.value = true;
}

function openEditCollege(row: CollegeItem): void {
  editingCollegeId.value = row.id;
  Object.assign(collegeForm, {
    name: row.name,
    college_code: row.college_code ?? null,
    province: row.province ?? null,
    city: row.city ?? null,
    school_type: row.school_type ?? null,
    school_level_tags_json: [...(row.school_level_tags_json ?? [])],
    intro: row.intro ?? null,
    website: row.website ?? null,
    supports_art: row.supports_art,
    note: row.note ?? null,
    alias_names: [...(row.alias_names ?? [])],
    is_active: row.is_active,
  });
  collegeDialogVisible.value = true;
}

async function submitCollege(): Promise<void> {
  if (!collegeForm.name.trim()) {
    ElMessage.warning("院校名称不能为空");
    return;
  }
  try {
    savingCollege.value = true;
    const payload: CollegePayload = {
      ...collegeForm,
      school_level_tags_json: uniqueStrings(collegeForm.school_level_tags_json),
      alias_names: uniqueStrings(collegeForm.alias_names),
    };
    const path = editingCollegeId.value ? `/api/colleges/${editingCollegeId.value}` : "/api/colleges";
    const method = editingCollegeId.value ? "PUT" : "POST";
    await apiRequest(path, { method, body: JSON.stringify(payload) });
    collegeDialogVisible.value = false;
    await Promise.all([loadCollegeDirectory(), loadColleges()]);
    ElMessage.success("院校保存成功");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingCollege.value = false;
  }
}

function openCreateMajor(): void {
  editingMajorId.value = null;
  Object.assign(majorForm, createMajorForm());
  majorDialogVisible.value = true;
}

function openEditMajor(row: MajorItem): void {
  editingMajorId.value = row.id;
  Object.assign(majorForm, {
    name: row.name,
    major_code: row.major_code ?? null,
    category: row.category ?? null,
    direction: row.direction ?? null,
    career_path: row.career_path ?? null,
    is_art_related: row.is_art_related,
    note: row.note ?? null,
    is_active: row.is_active,
  });
  majorDialogVisible.value = true;
}

async function submitMajor(): Promise<void> {
  if (!majorForm.name.trim()) {
    ElMessage.warning("专业名称不能为空");
    return;
  }
  try {
    savingMajor.value = true;
    const path = editingMajorId.value ? `/api/majors/${editingMajorId.value}` : "/api/majors";
    const method = editingMajorId.value ? "PUT" : "POST";
    await apiRequest(path, { method, body: JSON.stringify(majorForm) });
    majorDialogVisible.value = false;
    await Promise.all([loadMajorDirectory(), loadMajors()]);
    ElMessage.success("专业保存成功");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingMajor.value = false;
  }
}

function handleCollegeDialogClosed(): void {
  editingCollegeId.value = null;
  Object.assign(collegeForm, createCollegeForm());
}

function handleMajorDialogClosed(): void {
  editingMajorId.value = null;
  Object.assign(majorForm, createMajorForm());
}

async function handleAdmissionImport(uploadFileItem: UploadFile): Promise<void> {
  if (!uploadFileItem.raw) return;
  try {
    admissionImportResult.value = await uploadFile<AdmissionImportResponse>("/api/admissions/import", uploadFileItem.raw);
    await Promise.all([loadCollegeDirectory(), loadMajorDirectory(), loadAdmissions()]);
    ElMessage.success(admissionImportResult.value.message);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function submitRecommendation(): Promise<void> {
  try {
    generating.value = true;
    latestGeneration.value = null;
    batchGeneration.value = null;

    if (isBatchMode.value) {
      if (!recommendationForm.student_ids.length || !recommendationForm.exam_id) {
        ElMessage.warning("批量推荐至少需要学生列表和考试");
        return;
      }
      batchGeneration.value = await apiRequest<BatchGenerateResponse>("/api/recommendations/batch-generate", {
        method: "POST",
        body: JSON.stringify({
          student_ids: recommendationForm.student_ids,
          exam_id: recommendationForm.exam_id,
          name: recommendationForm.name || undefined,
          province: recommendationForm.province,
          target_regions_json: uniqueStrings(recommendationForm.target_regions_json),
          school_level_tags_json: uniqueStrings(recommendationForm.school_level_tags_json),
          major_keyword: recommendationForm.major_keyword || undefined,
          subject_combination: recommendationForm.subject_combination || undefined,
          obey_adjustment: recommendationForm.obey_adjustment,
          note: recommendationForm.note || undefined,
        }),
      });
      await loadHistory();
      ElMessage.success(batchGeneration.value.message);
      return;
    }

    if (!recommendationForm.student_id || !recommendationForm.exam_id) {
      ElMessage.warning("单个学生推荐需要学生和考试");
      return;
    }

    latestGeneration.value = await apiRequest<RecommendationGenerateResponse>("/api/recommendations/generate", {
      method: "POST",
      body: JSON.stringify({
        student_id: recommendationForm.student_id,
        exam_id: recommendationForm.exam_id,
        name: recommendationForm.name || undefined,
        province: recommendationForm.province,
        target_regions_json: uniqueStrings(recommendationForm.target_regions_json),
        school_level_tags_json: uniqueStrings(recommendationForm.school_level_tags_json),
        major_keyword: recommendationForm.major_keyword || undefined,
        subject_combination: recommendationForm.subject_combination || undefined,
        obey_adjustment: recommendationForm.obey_adjustment,
        student_rank_override: recommendationForm.student_rank_override,
        comprehensive_score: recommendationForm.comprehensive_score,
        professional_score: recommendationForm.professional_score,
        culture_score: recommendationForm.culture_score,
        note: recommendationForm.note || undefined,
      }),
    });

    activeTab.value = "recommendations";
    await loadHistory();
    const generated = historyItems.value.find((item) => item.scheme_id === latestGeneration.value?.scheme_id);
    if (generated) {
      await viewScheme(generated);
    }
    ElMessage.success("推荐方案生成成功");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    generating.value = false;
  }
}

async function viewScheme(item: RecommendationHistoryItem): Promise<void> {
  try {
    selectedSchemeMeta.value = item;
    compareSchemeId.value = undefined;
    multiCompareSchemeIds.value = [];
    multiCompareSchemeResults.value = {};
    compareSchemeResults.value = [];
    selectedSchemeResults.value = await apiRequest<RecommendationResult[]>(
      `/api/recommendations/history/${item.scheme_id}/results?student_id=${item.student_id}`,
    );
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function handleCompareSchemeChange(value: number | string | undefined | null): Promise<void> {
  if (!value || !selectedSchemeMeta.value) {
    compareSchemeId.value = undefined;
    compareSchemeResults.value = [];
    return;
  }
  const target = compareHistoryOptions.value.find((item) => item.scheme_id === Number(value));
  if (!target) {
    compareSchemeResults.value = [];
    return;
  }
  try {
    comparingScheme.value = true;
    compareSchemeResults.value = await apiRequest<RecommendationResult[]>(
      `/api/recommendations/history/${target.scheme_id}/results?student_id=${target.student_id}`,
    );
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    comparingScheme.value = false;
  }
}

async function handleMultiCompareChange(value: number[] | string[] | undefined | null): Promise<void> {
  const targetIds = (value ?? []).map((item) => Number(item));
  if (!targetIds.length || !selectedSchemeMeta.value) {
    multiCompareSchemeResults.value = {};
    return;
  }
  const nextResults = { ...multiCompareSchemeResults.value };
  const missingIds = targetIds.filter((item) => !nextResults[item]);
  if (!missingIds.length) {
    multiCompareSchemeResults.value = nextResults;
    return;
  }
  try {
    const loaded = await Promise.all(
      missingIds.map(async (schemeId) => {
        const meta = compareHistoryOptions.value.find((item) => item.scheme_id === schemeId);
        if (!meta) return null;
        const results = await apiRequest<RecommendationResult[]>(
          `/api/recommendations/history/${schemeId}/results?student_id=${meta.student_id}`,
        );
        return { schemeId, results };
      }),
    );
    for (const item of loaded) {
      if (item) nextResults[item.schemeId] = item.results;
    }
    multiCompareSchemeResults.value = nextResults;
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function exportScheme(item: RecommendationHistoryItem): Promise<void> {
  try {
    exportingScheme.value = item.scheme_id;
    const result = await apiRequest<ExportRecord>("/api/reports/export", {
      method: "POST",
      body: JSON.stringify({
        report_type: "recommendation_summary",
        scheme_id: item.scheme_id,
        student_id: item.student_id,
      }),
    });
    openFile(result.download_url);
    ElMessage.success("推荐报告已生成");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    exportingScheme.value = null;
  }
}

onMounted(async () => {
  try {
    await loadStudentAndExamOptions();
    await Promise.all([
      loadCollegeDirectory(),
      loadMajorDirectory(),
      loadRecommendationSettings(),
      loadColleges(),
      loadMajors(),
      loadAdmissions(),
      loadHistory(),
    ]);
    if (historyItems.value.length) {
      await viewScheme(historyItems.value[0]);
    }
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
});
</script>

<style scoped>
.page-eyebrow {
  color: #7b8d9c;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.9fr);
  gap: 20px;
}

.summary-panel,
.workflow-panel,
.panel-block {
  padding: 24px;
}

.summary-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(300px, 0.95fr);
  gap: 22px;
  background:
    radial-gradient(circle at top left, rgba(180, 219, 243, 0.34), transparent 26%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(244, 248, 252, 0.94));
}

.recommendation-chip-row {
  max-width: 760px;
}

.summary-copy h3 {
  margin: 12px 0 0;
  color: #203549;
  font-size: 30px;
  line-height: 1.2;
}

.summary-copy p {
  margin: 12px 0 0;
  color: #5f7387;
  line-height: 1.7;
}

.summary-badge {
  display: inline-flex;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f6c98;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.summary-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-content: start;
  gap: 14px;
}

.summary-metric {
  padding: 18px;
  border-radius: 20px;
  background: rgba(248, 251, 254, 0.96);
  border: 1px solid rgba(123, 142, 161, 0.12);
}

.summary-metric-label {
  color: #688095;
  font-size: 13px;
}

.summary-metric-value {
  margin-top: 10px;
  font-size: 28px;
  font-weight: 760;
  color: #1e3348;
}

.summary-metric-help {
  margin-top: 8px;
  color: #72879b;
  font-size: 13px;
  line-height: 1.5;
}

.tone-blue {
  box-shadow: inset 0 4px 0 rgba(31, 108, 152, 0.85);
}

.tone-amber {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.88);
}

.tone-slate {
  box-shadow: inset 0 4px 0 rgba(79, 101, 122, 0.72);
}

.tone-green {
  box-shadow: inset 0 4px 0 rgba(67, 142, 110, 0.78);
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-head.compact {
  margin-bottom: 10px;
}

.section-head h3 {
  margin: 0;
  font-size: 19px;
}

.section-head p {
  margin: 6px 0 0;
  color: #62788d;
  line-height: 1.6;
}

.workflow-list {
  display: grid;
  gap: 12px;
}

.workflow-panel {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 249, 252, 0.94));
}

.workflow-item {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
  padding: 16px;
  border-radius: 20px;
  background: rgba(248, 251, 254, 0.88);
  border: 1px solid rgba(121, 138, 154, 0.14);
}

.workflow-item span {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(31, 108, 152, 0.14), rgba(209, 141, 72, 0.14));
  color: #26425d;
  font-size: 13px;
  font-weight: 800;
}

.workflow-item strong {
  display: block;
  color: #20354a;
}

.workflow-item p {
  margin: 6px 0 0;
  color: #6a7f92;
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

.muted-copy {
  color: #7d8f9d;
  font-size: 13px;
}

.name-stack {
  display: grid;
  gap: 4px;
}

.name-stack strong {
  color: #203449;
}

.name-stack span {
  color: #7b8d9c;
  font-size: 13px;
}

.recommend-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
  gap: 18px;
}

.recommend-side-stack {
  display: grid;
  gap: 18px;
}

.note-box {
  margin-top: 4px;
}

.result-alert {
  margin-top: 16px;
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

.compact-actions {
  gap: 4px;
}

.comparison-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin: 20px 0 0;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(247, 250, 253, 0.92);
  border: 1px solid rgba(124, 139, 154, 0.12);
}

.comparison-copy strong {
  color: #20364b;
  font-size: 15px;
}

.comparison-copy p {
  margin: 6px 0 0;
  color: #6a8094;
  line-height: 1.6;
}

.comparison-controls {
  width: min(320px, 100%);
}

.comparison-panel {
  margin-top: 18px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(245, 249, 252, 0.88);
  border: 1px solid rgba(126, 143, 158, 0.12);
}

.comparison-divider {
  height: 1px;
  margin: 20px 0;
  background: rgba(126, 143, 158, 0.12);
}

.comparison-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.comparison-summary-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(123, 142, 161, 0.1);
}

.comparison-summary-card span {
  color: #6d8194;
  font-size: 13px;
}

.comparison-summary-card strong {
  display: block;
  margin-top: 8px;
  color: #1f3348;
  font-size: 24px;
  font-weight: 760;
}

.comparison-summary-card p {
  margin: 8px 0 0;
  color: #73879b;
  font-size: 13px;
  line-height: 1.5;
}

.comparison-delta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.comparison-delta-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(124, 140, 155, 0.12);
}

.comparison-delta-card div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.comparison-delta-card span {
  color: #6b8093;
  font-size: 13px;
}

.comparison-delta-card strong {
  color: #21364a;
  font-size: 24px;
}

.comparison-delta-card p {
  margin: 8px 0 0;
  color: #6d8195;
}

.comparison-column-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 16px;
}

.comparison-column {
  padding: 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(125, 141, 156, 0.12);
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
  color: #1f3448;
  font-size: 16px;
}

.comparison-column header span {
  color: #6f8397;
  font-size: 13px;
}

.comparison-item-list {
  display: grid;
  gap: 10px;
}

.comparison-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 12px;
  border-radius: 16px;
  background: rgba(247, 250, 253, 0.96);
}

.comparison-item strong {
  color: #23374b;
  line-height: 1.5;
}

.comparison-item span {
  color: #688095;
  font-size: 13px;
  white-space: nowrap;
}

.comparison-empty,
.comparison-placeholder {
  color: #72869a;
  line-height: 1.7;
}

.delta-up {
  color: #1f7a4b;
  font-weight: 700;
}

.delta-down {
  color: #b4523f;
  font-weight: 700;
}

.delta-flat {
  color: #6d8295;
  font-weight: 700;
}

.result-board-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 18px;
}

.result-column {
  padding: 16px;
  border-radius: 22px;
  border: 1px solid rgba(118, 136, 154, 0.14);
  background: rgba(249, 252, 255, 0.92);
}

.result-column.challenge {
  box-shadow: inset 0 4px 0 rgba(210, 92, 73, 0.82);
}

.result-column.steady {
  box-shadow: inset 0 4px 0 rgba(209, 141, 72, 0.88);
}

.result-column.safe {
  box-shadow: inset 0 4px 0 rgba(69, 141, 105, 0.8);
}

.result-column-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.result-column-head h4 {
  margin: 8px 0 0;
  font-size: 20px;
  color: #20364b;
}

.result-tip {
  color: #7a8d9d;
  font-size: 12px;
  line-height: 1.5;
  text-align: right;
}

.result-pill {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(31, 108, 152, 0.1);
  color: #1f6c98;
  font-size: 12px;
  font-weight: 700;
}

.result-card-list {
  display: grid;
  gap: 12px;
}

.result-card {
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(126, 142, 158, 0.12);
}

.result-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.result-card-head h5 {
  margin: 0;
  font-size: 16px;
  color: #21364a;
}

.result-card-head p {
  margin: 4px 0 0;
  color: #70859a;
  line-height: 1.5;
}

.ratio-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(237, 243, 248, 0.95);
  color: #52697f;
  font-size: 12px;
  white-space: nowrap;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
  margin: 14px 0 0;
}

.detail-grid dt {
  color: #7b8f9f;
  font-size: 12px;
}

.detail-grid dd {
  margin: 4px 0 0;
  color: #24384d;
  font-weight: 600;
}

.reason-copy {
  margin: 14px 0 12px;
  color: #5f768a;
  line-height: 1.6;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.span-two {
  grid-column: span 2;
}

:deep(.recommendation-tabs .el-tabs__content) {
  overflow: visible;
}

@media (max-width: 1280px) {
  .summary-metrics,
  .result-board-grid,
  .comparison-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1080px) {
  .hero-grid,
  .recommend-layout,
  .result-board-grid,
  .summary-metrics,
  .comparison-column-grid,
  .comparison-delta-grid,
  .comparison-summary-grid,
  .strategy-card-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .form-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .span-two {
    grid-column: span 1;
  }

  .section-head,
  .result-card-head,
  .result-column-head,
  .comparison-toolbar,
  .comparison-column header,
  .comparison-item,
  .comparison-delta-card div {
    flex-direction: column;
  }

  .result-tip {
    text-align: left;
  }

  .comparison-controls {
    width: 100%;
  }

  .comparison-item span {
    white-space: normal;
  }
}
</style>
