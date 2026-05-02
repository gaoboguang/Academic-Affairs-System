<template>
  <AppPage
    eyebrow="高考数据 / 只读驾驶舱"
    title="高考数据"
    description="先看数据来源、待审阅项、单校证据链和山东覆盖情况，再决定下一步优先补哪些数据。"
    :meta="pageMeta"
  >
    <template #actions>
      <div class="action-row">
        <el-button @click="reloadAll">刷新驾驶舱</el-button>
        <el-button @click="openDataCoverageReportPrintPreview"
          >打印覆盖报告</el-button
        >
        <el-button type="primary" @click="activeTab = 'evidence'"
          >查看证据页</el-button
        >
      </div>
    </template>

    <el-tabs v-model="activeTab" class="gaokao-tabs">
      <el-tab-pane label="总览" name="overview">
        <AppStatGrid :items="overviewStatCards" :columns="6" />

        <section class="dashboard-grid">
          <article class="soft-card panel-block">
            <div class="section-head compact">
              <div>
                <h3>当前口径</h3>
                <p>
                  先说明这页数字来自哪里，避免把冻结基线、只读库和应用侧数据混在一起理解。
                </p>
              </div>
            </div>
            <div class="overview-copy">
              <div class="overview-highlight">
                <strong>{{ overview.data_version || "待确认" }}</strong>
                <span>{{ formatSourceMode(overview.source_mode) }}</span>
              </div>
              <p>
                最近更新时间：{{ overview.last_updated_at || "待同步" }}；
                最近批次：{{ overview.recent_batch_label || "待同步" }}；
                文档冻结时间：{{ overview.generated_at || "待确认" }}
              </p>
            </div>
            <el-alert
              v-for="note in overview.notes"
              :key="note"
              class="gaokao-alert"
              type="info"
              :closable="false"
              :title="note"
            />
          </article>

          <article class="soft-card panel-block">
            <div class="section-head compact">
              <div>
                <h3>最近批次</h3>
                <p>
                  优先展示高考相关导入或冻结基线，帮助快速判断当前应用看到的是哪一波材料。
                </p>
              </div>
            </div>
            <div class="table-shell">
              <el-table :data="importBatches" stripe>
                <el-table-column
                  label="批次"
                  prop="batch_name"
                  min-width="180"
                />
                <el-table-column label="来源" prop="source_type" width="120" />
                <el-table-column
                  label="文件"
                  prop="source_filename"
                  min-width="180"
                />
                <el-table-column label="状态" width="110">
                  <template #default="{ row }">
                    <el-tag :type="statusTagType(row.status)" effect="light">{{
                      formatStatus(row.status)
                    }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column
                  label="完成时间"
                  prop="finished_at"
                  min-width="180"
                />
              </el-table>
            </div>
            <el-empty
              v-if="!importBatches.length"
              description="暂无高考相关批次记录"
            />
          </article>
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>2026 数据发布状态</h3>
              <p>
                把已公开、已导入、待官方发布和需人工核验的数据分开看，避免把单招/综评材料误当成普通类正式计划。
              </p>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="dataHealth.publication_status" stripe>
              <el-table-column label="数据项" min-width="220">
                <template #default="{ row }">
                  <div class="table-strong">{{ row.label }}</div>
                  <div class="table-muted">
                    {{ row.category }} · {{ row.target_year }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="150">
                <template #default="{ row }">
                  <el-tag :type="statusTagType(row.status)" effect="light">{{
                    row.status_label
                  }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column
                label="当前记录"
                width="110"
                prop="record_count"
              />
              <el-table-column label="已登记来源" min-width="300">
                <template #default="{ row }">
                  <div
                    v-if="row.source_documents.length"
                    class="source-doc-list"
                  >
                    <a
                      v-for="source in row.source_documents"
                      :key="source.id"
                      :href="source.url || undefined"
                      target="_blank"
                      rel="noreferrer"
                    >
                      {{ source.title }}
                    </a>
                  </div>
                  <span v-else class="table-muted">暂无单独来源</span>
                </template>
              </el-table-column>
              <el-table-column label="下一步" min-width="360">
                <template #default="{ row }">
                  <p class="risk-explanation">{{ row.action_label }}</p>
                  <p class="table-muted">{{ row.explanation }}</p>
                  <ul v-if="row.notes?.length" class="audit-note-list">
                    <li v-for="note in row.notes" :key="note">{{ note }}</li>
                  </ul>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty
            v-if="!dataHealth.publication_status.length"
            description="暂无 2026 数据发布状态"
          />
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>核心表统计</h3>
              <p>
                当前把高考只读库指标和应用侧可复用表放在一起看，方便区分“原始数据已到位”和“页面已能直接使用”。
              </p>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="overview.core_tables" stripe>
              <el-table-column label="表/视图" prop="label" min-width="160" />
              <el-table-column label="记录数" prop="record_total" width="120" />
              <el-table-column label="覆盖数" width="120">
                <template #default="{ row }">
                  {{ row.covered_total ?? "-" }}
                </template>
              </el-table-column>
              <el-table-column label="覆盖率" width="120">
                <template #default="{ row }">
                  {{
                    row.coverage_rate === null ||
                    row.coverage_rate === undefined
                      ? "-"
                      : `${row.coverage_rate}%`
                  }}
                </template>
              </el-table-column>
              <el-table-column
                label="最近时间"
                prop="latest_updated_at"
                min-width="180"
              />
              <el-table-column
                label="批次/说明"
                prop="latest_batch_label"
                min-width="160"
              />
              <el-table-column label="状态" width="110">
                <template #default="{ row }">
                  <el-tag :type="statusTagType(row.status)" effect="light">{{
                    formatMonitorStatus(row.status)
                  }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div v-if="overviewGapCards.length" class="overview-gap-grid">
            <article
              v-for="item in overviewGapCards"
              :key="item.key"
              class="overview-gap-card"
            >
              <div class="monitor-card-head">
                <div>
                  <div class="table-strong">{{ item.label }}</div>
                  <p>{{ item.summary }}</p>
                </div>
                <el-tag :type="statusTagType(item.status)" effect="light">{{
                  formatMonitorStatus(item.status)
                }}</el-tag>
              </div>
              <div class="review-filter-summary">
                <span>应用侧记录：{{ item.record_total }}</span>
                <span>最近时间：{{ item.latest_updated_at || "未导入" }}</span>
                <span
                  >批次/说明：{{ item.latest_batch_label || "待确认" }}</span
                >
              </div>
              <ul v-if="item.notes.length" class="note-list compact">
                <li v-for="note in item.notes" :key="note">{{ note }}</li>
              </ul>
            </article>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="山东覆盖" name="coverage">
        <AppStatGrid :items="coverageStatCards" :columns="4" />

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>数据库补齐结果说明</h3>
              <p>
                把 E6
                已补齐、仍部分补齐、官方未发布和需人工复核的数据拆开显示，避免只看记录数误判。
              </p>
            </div>
            <el-button @click="openDataCoverageReportPrintPreview"
              >打印覆盖报告</el-button
            >
          </div>
          <div class="completion-card-grid">
            <article
              v-for="item in dataCompletionCards"
              :key="item.key"
              class="completion-card"
              :class="`tone-${item.tone}`"
            >
              <div class="completion-card-head">
                <strong>{{ item.title }}</strong>
                <el-tag :type="coverageToneTagType(item.tone)" effect="light">{{
                  item.statusLabel
                }}</el-tag>
              </div>
              <p>{{ item.summary }}</p>
              <span>{{ item.detail }}</span>
            </article>
          </div>
        </section>

        <section class="dashboard-grid">
          <article class="soft-card panel-block">
            <div class="section-head compact">
              <div>
                <h3>健康检查摘要</h3>
                <p>
                  直接复用本地命令 `backend:data-health`
                  的结构化结果，方便补数据前后对照。
                </p>
              </div>
              <el-tag
                :type="dataHealth.gaps.length ? 'warning' : 'success'"
                effect="light"
              >
                {{ dataHealth.summary || "待检查" }}
              </el-tag>
            </div>
            <div class="overview-copy">
              <div class="overview-highlight">
                <strong>{{ dataHealth.schema_version || "未迁移" }}</strong>
                <span>{{ dataHealth.generated_at || "待检查" }}</span>
              </div>
              <p>主库：{{ dataHealth.db_path || "待确认" }}</p>
              <div
                v-if="dataHealth.delivery_assessment"
                class="delivery-assessment"
              >
                <el-tag
                  :type="deliveryTagType(dataHealth.delivery_assessment.status)"
                  effect="light"
                >
                  {{ dataHealth.delivery_assessment.label }}
                </el-tag>
                <span>{{ dataHealth.delivery_assessment.summary }}</span>
              </div>
            </div>
            <ul v-if="dataHealth.gaps.length" class="health-gap-list">
              <li v-for="gap in dataHealth.gaps" :key="gap">{{ gap }}</li>
            </ul>
            <el-empty v-else description="当前未发现 P0 规则内的明显缺口" />
          </article>

          <article class="soft-card panel-block">
            <div class="section-head compact">
              <div>
                <h3>核心表状态</h3>
                <p>
                  先看哪些表已经有数据，哪些表虽然有数据但仍不足以支撑交付。
                </p>
              </div>
            </div>
            <div class="table-shell">
              <el-table :data="dataHealth.tables" stripe>
                <el-table-column label="表" prop="label" min-width="180" />
                <el-table-column label="记录数" prop="count" width="110" />
                <el-table-column label="状态" width="110">
                  <template #default="{ row }">
                    <el-tag :type="statusTagType(row.status)" effect="light">{{
                      formatMonitorStatus(row.status)
                    }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="说明" min-width="240">
                  <template #default="{ row }">
                    {{ formatTableNotes(row) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </article>
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>考生类型可用性</h3>
              <p>
                把普通类、春考、艺术、体育、单招、综评分开看，避免把“有计划”误解成“有录取把握”。
              </p>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="dataHealth.special_type_risks" stripe>
              <el-table-column label="考生类型" min-width="150">
                <template #default="{ row }">
                  <div class="table-strong">{{ row.label }}</div>
                  <div class="table-muted">{{ row.key }}</div>
                </template>
              </el-table-column>
              <el-table-column label="可用性" min-width="170">
                <template #default="{ row }">
                  <el-tag
                    :type="riskLevelTagType(row.risk_level)"
                    effect="light"
                  >
                    {{ row.readiness_label }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="当前数据" min-width="260">
                <template #default="{ row }">
                  <div class="risk-count-grid">
                    <span>计划 {{ row.plan_count || row.raw_plan_count }}</span>
                    <span
                      >录取
                      {{ row.admission_count || row.raw_admission_count }}</span
                    >
                    <span>省控线 {{ row.score_line_count }}</span>
                    <span
                      >规则 {{ row.volunteer_rule_count }} /
                      {{ row.special_rule_count }}</span
                    >
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="初筛方式" min-width="220">
                <template #default="{ row }">
                  {{ formatFallbackLabels(row.fallback_labels) }}
                </template>
              </el-table-column>
              <el-table-column label="说明" min-width="360">
                <template #default="{ row }">
                  <p class="risk-explanation">{{ row.explanation }}</p>
                  <ul v-if="row.notes?.length" class="audit-note-list">
                    <li v-for="note in row.notes" :key="note">{{ note }}</li>
                  </ul>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>2020-2026 年份覆盖矩阵</h3>
              <p>
                横向查看一分一段、省控线、招生计划、政策参考和章程复核进度；2026
                未发布项单独标为待发布。
              </p>
            </div>
          </div>
          <div class="coverage-matrix-shell">
            <table class="coverage-matrix-table">
              <thead>
                <tr>
                  <th>数据域</th>
                  <th v-for="year in dataHealth.expected_years" :key="year">
                    {{ year }}
                  </th>
                  <th>当前记录</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in coverageMatrixRows" :key="row.key">
                  <td>
                    <strong>{{ row.label }}</strong>
                    <span>{{ row.readinessLabel }}</span>
                  </td>
                  <td
                    v-for="cell in row.cells"
                    :key="`${row.key}_${cell.year}`"
                  >
                    <el-tooltip :content="cell.detail" placement="top">
                      <el-tag
                        :type="coverageToneTagType(cell.tone)"
                        effect="light"
                        >{{ cell.label }}</el-tag
                      >
                    </el-tooltip>
                  </td>
                  <td>{{ row.total }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <el-empty
            v-if="!coverageMatrixRows.length"
            description="暂无覆盖矩阵，请刷新数据健康检查"
          />
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>山东年份与类型覆盖</h3>
              <p>按年份、数据域和考生类型查看当前主库能支撑哪些推荐口径。</p>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="dataHealth.coverage" stripe>
              <el-table-column type="expand" width="44">
                <template #default="{ row }">
                  <div class="coverage-detail-table">
                    <el-table :data="row.year_breakdown" size="small" stripe>
                      <el-table-column label="年份" prop="year" width="90" />
                      <el-table-column label="总量" prop="total" width="100" />
                      <el-table-column label="类型 / 状态" min-width="220">
                        <template #default="{ row: yearRow }">
                          {{
                            formatDistribution(yearRow.student_types, "无分类")
                          }}
                        </template>
                      </el-table-column>
                      <el-table-column label="批次 / 口径" min-width="220">
                        <template #default="{ row: yearRow }">
                          {{ formatDistribution(yearRow.batches, "无批次") }}
                        </template>
                      </el-table-column>
                      <el-table-column label="状态" width="110">
                        <template #default="{ row: yearRow }">
                          <el-tag
                            :type="statusTagType(yearRow.status)"
                            effect="light"
                          >
                            {{ formatMonitorStatus(yearRow.status) }}
                          </el-tag>
                        </template>
                      </el-table-column>
                    </el-table>
                    <el-empty
                      v-if="!row.year_breakdown.length"
                      description="暂无按年明细"
                    />
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="数据域" prop="label" min-width="180" />
              <el-table-column label="总量" prop="total" width="110" />
              <el-table-column label="年份覆盖" min-width="180">
                <template #default="{ row }">
                  {{ formatYearList(row.years) }}
                </template>
              </el-table-column>
              <el-table-column label="缺少年份" min-width="160">
                <template #default="{ row }">
                  {{ formatYearList(row.missing_years) }}
                </template>
              </el-table-column>
              <el-table-column label="考生类型 / 状态分布" min-width="320">
                <template #default="{ row }">
                  <div class="health-type-tags">
                    <el-tag
                      v-for="item in row.student_types"
                      :key="`${row.key}_${item.key}`"
                      size="small"
                      effect="light"
                    >
                      {{ item.label || item.key }}：{{ item.count }}
                    </el-tag>
                    <span v-if="!row.student_types.length" class="table-muted"
                      >无分类</span
                    >
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="批次 / 口径分布" min-width="260">
                <template #default="{ row }">
                  {{ formatDistribution(row.batch_distribution, "无批次") }}
                </template>
              </el-table-column>
              <el-table-column label="状态" width="110">
                <template #default="{ row }">
                  <el-tag :type="statusTagType(row.status)" effect="light">{{
                    formatMonitorStatus(row.status)
                  }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="可用性说明" min-width="320">
                <template #default="{ row }">
                  <div class="coverage-readiness">
                    <el-tag
                      :type="riskLevelTagType(row.risk_level)"
                      size="small"
                      effect="light"
                    >
                      {{
                        row.readiness_label || formatMonitorStatus(row.status)
                      }}
                    </el-tag>
                    <span>{{ row.explanation }}</span>
                  </div>
                  <ul v-if="row.notes?.length" class="audit-note-list">
                    <li v-for="note in row.notes" :key="note">{{ note }}</li>
                  </ul>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>数据导入审计摘要</h3>
              <p>
                覆盖阶段一要求的新增、更新、重复、冲突与待复核摘要，补数据前后可直接对照。
              </p>
            </div>
          </div>
          <div class="table-shell">
            <el-table :data="dataHealth.audit_summary" stripe>
              <el-table-column label="数据域" prop="label" min-width="180" />
              <el-table-column label="状态" width="110">
                <template #default="{ row }">
                  <el-tag :type="statusTagType(row.status)" effect="light">{{
                    formatMonitorStatus(row.status)
                  }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="新增" prop="created" width="90" />
              <el-table-column label="更新/当前" prop="updated" width="110" />
              <el-table-column label="重复" prop="duplicates" width="90" />
              <el-table-column label="冲突" prop="conflicts" width="90" />
              <el-table-column
                label="待复核"
                prop="pending_review"
                width="100"
              />
              <el-table-column label="说明" min-width="280">
                <template #default="{ row }">
                  <ul v-if="row.notes?.length" class="audit-note-list">
                    <li v-for="note in row.notes" :key="note">{{ note }}</li>
                  </ul>
                  <span v-else class="table-muted">无</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-empty
            v-if="!dataHealth.audit_summary.length"
            description="暂无审计摘要"
          />
        </section>
      </el-tab-pane>

      <el-tab-pane label="数据审阅" name="review">
        <section class="soft-card panel-block">
          <div class="section-head compact">
            <div>
              <h3>审阅队列</h3>
              <p>
                先看哪类问题还在队列里，再决定是等待下一批数据同步，还是先在文档层记录跟进。
              </p>
            </div>
            <div class="action-row">
              <el-select
                v-model="reviewFilter"
                class="review-filter"
                placeholder="审阅状态"
                @change="loadReviewSummary"
              >
                <el-option label="全部" value="all" />
                <el-option label="待人工复核" value="pending_manual_review" />
                <el-option
                  label="待人工复核（已有官方候选）"
                  value="pending_manual_review_with_official_candidate"
                />
                <el-option label="仍未解决" value="unresolved" />
              </el-select>
              <el-select
                v-model="reviewSort"
                class="review-filter"
                placeholder="排序方式"
                @change="loadReviewSummary"
              >
                <el-option label="优先级优先" value="priority_desc" />
                <el-option label="最近更新时间" value="updated_desc" />
              </el-select>
              <el-input
                v-model="reviewKeyword"
                class="review-filter"
                clearable
                placeholder="按学校名 / 学校代码 / 省份 / 招生网关键词检索"
                @keyup.enter="loadReviewSummary"
              />
              <el-button @click="loadReviewSummary">刷新</el-button>
            </div>
          </div>
          <div class="review-metrics">
            <article
              v-for="item in reviewSummary.counts"
              :key="item.code"
              class="review-metric-card"
            >
              <span>{{ item.title }}</span>
              <strong>{{ item.count ?? "待同步" }}</strong>
              <p>{{ item.description }}</p>
            </article>
          </div>
          <div
            v-if="reviewSummary.quick_filters.length"
            class="review-quick-filters"
          >
            <el-button
              v-for="item in reviewSummary.quick_filters"
              :key="item.code"
              size="small"
              :type="reviewFocus === item.code ? 'primary' : undefined"
              :plain="reviewFocus !== item.code"
              @click="applyReviewFocus(item.code)"
            >
              {{ item.title }}（{{ item.count }}）
            </el-button>
          </div>
          <p v-if="activeReviewQuickFilter" class="review-quick-filter-copy">
            {{ activeReviewQuickFilter.description }}
          </p>
          <div class="review-filter-summary">
            <span
              >当前过滤：{{
                formatReviewFilter(reviewSummary.active_filter)
              }}</span
            >
            <span
              >优先视图：{{
                formatReviewFocus(reviewSummary.active_focus)
              }}</span
            >
            <span>排序：{{ formatReviewSort(reviewSummary.active_sort) }}</span>
            <span>队列：{{ reviewSummary.queue_total }}</span>
            <span>关键字：{{ reviewSummary.active_keyword || "未输入" }}</span>
            <span v-if="reviewSummary.matched_total !== null"
              >命中：{{ reviewSummary.matched_total }}</span
            >
          </div>
          <el-alert
            v-for="highlight in reviewSummary.highlights"
            :key="highlight"
            class="gaokao-alert"
            type="info"
            :closable="false"
            :title="highlight"
          />
          <el-alert
            v-for="note in reviewSummary.notes"
            :key="note"
            class="gaokao-alert"
            type="warning"
            :closable="false"
            :title="note"
          />
        </section>

        <section class="dashboard-grid">
          <article class="soft-card panel-block">
            <div class="section-head compact">
              <div>
                <h3>待审阅学校</h3>
                <p>
                  当前过滤：{{
                    formatReviewFilter(reviewSummary.active_filter)
                  }}。
                </p>
              </div>
            </div>
            <div class="table-shell">
              <el-table :data="reviewSummary.items" stripe>
                <el-table-column label="学校" min-width="180">
                  <template #default="{ row }">
                    <div class="table-strong">
                      {{ row.college_name || "-" }}
                    </div>
                    <div class="table-muted">
                      学校 ID {{ row.college_id ?? "-" }} /
                      {{ row.college_code || "无学校代码" }}
                    </div>
                    <div
                      v-if="row.duplicate_group_key || row.same_name_group_key"
                      class="inline-tag-row"
                    >
                      <el-tag
                        v-if="row.duplicate_group_key"
                        size="small"
                        effect="light"
                        type="warning"
                        >重复组</el-tag
                      >
                      <el-tag
                        v-if="row.same_name_group_key"
                        size="small"
                        effect="light"
                        type="info"
                        >同名组</el-tag
                      >
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="优先级" min-width="220">
                  <template #default="{ row }">
                    <el-tag
                      :type="reviewPriorityTagType(row.priority_code)"
                      effect="light"
                    >
                      {{ row.priority_label || "待分层" }}
                    </el-tag>
                    <div
                      v-if="row.priority_reasons?.length"
                      class="priority-reason-list"
                    >
                      <span
                        v-for="reason in row.priority_reasons"
                        :key="reason"
                        >{{ reason }}</span
                      >
                    </div>
                  </template>
                </el-table-column>
                <el-table-column
                  label="审阅状态"
                  prop="review_status"
                  min-width="160"
                />
                <el-table-column
                  label="抓取状态"
                  prop="retrieval_status"
                  min-width="140"
                />
                <el-table-column label="招生网" min-width="220">
                  <template #default="{ row }">
                    <span class="mono-text">{{ row.recruit_site || "-" }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="章程" min-width="220">
                  <template #default="{ row }">
                    <span class="mono-text">{{
                      row.chapter_url || row.fallback_url || "-"
                    }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="110" fixed="right">
                  <template #default="{ row }">
                    <el-button
                      link
                      type="primary"
                      :disabled="!row.college_id"
                      @click="openEvidenceForCollege(row.college_id, row)"
                    >
                      查看证据
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <el-empty
              v-if="!reviewSummary.items.length"
              description="当前过滤条件下暂无学校明细"
            />
          </article>

          <article class="soft-card panel-block">
            <div class="section-head compact">
              <div>
                <h3>重复 / 同名组</h3>
                <p>
                  这两类组最适合用来判断还要不要继续催 Windows 线做语义裁决。
                </p>
              </div>
            </div>
            <div
              v-if="reviewSummary.priority_groups.length"
              class="group-priority-strip"
            >
              <article
                v-for="item in reviewSummary.priority_groups"
                :key="`priority_${item.group_type}_${item.key}`"
                class="group-priority-card"
              >
                <div class="group-priority-head">
                  <div>
                    <strong>{{ item.title }}</strong>
                    <p>
                      {{ formatGroupType(item.group_type) }} ·
                      {{ item.item_count }} 条记录
                    </p>
                  </div>
                  <el-tag
                    :type="reviewPriorityTagType(item.priority_code)"
                    effect="light"
                  >
                    {{ item.priority_label || "待分层" }}
                  </el-tag>
                </div>
                <p class="group-action-copy">
                  {{ item.suggested_action || "先打开组内证据链核对来源。" }}
                </p>
                <div
                  v-if="item.priority_reasons?.length"
                  class="priority-reason-list"
                >
                  <span v-for="reason in item.priority_reasons" :key="reason">{{
                    reason
                  }}</span>
                </div>
                <div
                  v-if="item.comparison_fields?.length"
                  class="group-compare-summary"
                >
                  <el-tag
                    v-for="field in item.comparison_fields"
                    :key="`priority_${item.key}_${field.key}`"
                    size="small"
                    :type="comparisonFieldTagType(field.status)"
                    effect="light"
                  >
                    {{ field.title }} · {{ field.summary }}
                  </el-tag>
                </div>
                <div v-if="item.member_items?.length" class="group-member-list">
                  <el-button
                    v-for="member in item.member_items"
                    :key="`priority_${item.key}_${member.college_id}`"
                    link
                    type="primary"
                    @click="openEvidenceForCollege(member.college_id, member)"
                  >
                    {{ formatGroupMemberLabel(member) }}
                  </el-button>
                </div>
              </article>
            </div>
            <div class="group-section">
              <div>
                <strong
                  >重复组（命中 {{ reviewSummary.duplicate_groups.length }} /
                  全量
                  {{
                    reviewSummary.duplicate_group_total ?? "待同步"
                  }}）</strong
                >
                <ul class="group-list">
                  <li
                    v-for="item in reviewSummary.duplicate_groups"
                    :key="`duplicate_${item.key}`"
                  >
                    <div class="group-item-copy">
                      <div class="group-item-head">
                        <span>{{ item.title }}</span>
                        <el-tag
                          :type="reviewPriorityTagType(item.priority_code)"
                          effect="light"
                        >
                          {{ item.priority_label || "待分层" }}
                        </el-tag>
                      </div>
                      <small>
                        {{ item.item_count }} 条 · 高优先
                        {{ item.high_priority_member_total }} · unresolved
                        {{ item.unresolved_total }}
                      </small>
                      <p class="group-action-copy">
                        {{ item.suggested_action || "先核对组内证据链。" }}
                      </p>
                      <div
                        v-if="item.priority_reasons?.length"
                        class="priority-reason-list"
                      >
                        <span
                          v-for="reason in item.priority_reasons"
                          :key="reason"
                          >{{ reason }}</span
                        >
                      </div>
                      <div
                        v-if="item.comparison_fields?.length"
                        class="group-compare-summary"
                      >
                        <el-tag
                          v-for="field in item.comparison_fields"
                          :key="`duplicate_${item.key}_${field.key}`"
                          size="small"
                          :type="comparisonFieldTagType(field.status)"
                          effect="light"
                        >
                          {{ field.title }} · {{ field.summary }}
                        </el-tag>
                      </div>
                      <div
                        v-if="item.member_items?.length"
                        class="group-compare-shell"
                      >
                        <table class="group-compare-table">
                          <thead>
                            <tr>
                              <th>学校</th>
                              <th>省份</th>
                              <th>代码</th>
                              <th>官方站</th>
                              <th>招生网</th>
                              <th>章程</th>
                              <th>来源</th>
                              <th>更新</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr
                              v-for="member in item.member_items"
                              :key="`duplicate_row_${item.key}_${member.college_id}`"
                            >
                              <td>
                                <el-button
                                  link
                                  type="primary"
                                  @click="
                                    openEvidenceForCollege(
                                      member.college_id,
                                      member,
                                    )
                                  "
                                >
                                  {{
                                    member.college_name ||
                                    `学校 ${member.college_id}`
                                  }}
                                </el-button>
                                <div class="table-muted">
                                  {{ member.review_status || "状态待确认" }} ·
                                  {{ member.priority_label || "待分层" }}
                                </div>
                              </td>
                              <td>{{ member.province || "待补齐" }}</td>
                              <td>{{ member.college_code || "待补齐" }}</td>
                              <td>
                                {{
                                  formatGroupCompareCell(member.official_site)
                                }}
                              </td>
                              <td>
                                {{
                                  formatGroupCompareCell(member.recruit_site)
                                }}
                              </td>
                              <td>{{ formatGroupChapterCell(member) }}</td>
                              <td>
                                <div class="group-source-cell">
                                  <strong>{{
                                    member.source_title || "待补齐"
                                  }}</strong>
                                  <span class="mono-text">{{
                                    formatGroupSourceUrlCell(member.source_url)
                                  }}</span>
                                </div>
                              </td>
                              <td>{{ member.updated_at || "待补齐" }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div
                        v-if="item.member_items?.length"
                        class="group-member-list"
                      >
                        <el-button
                          v-for="member in item.member_items"
                          :key="`duplicate_${item.key}_${member.college_id}`"
                          link
                          type="primary"
                          @click="
                            openEvidenceForCollege(member.college_id, member)
                          "
                        >
                          {{ formatGroupMemberLabel(member) }}
                        </el-button>
                      </div>
                    </div>
                  </li>
                </ul>
                <el-empty
                  v-if="!reviewSummary.duplicate_groups.length"
                  description="暂无重复组明细"
                />
              </div>
              <div>
                <strong
                  >同名跨站组（命中
                  {{ reviewSummary.same_name_groups.length }} / 全量
                  {{
                    reviewSummary.same_name_cross_site_group_total ?? "待同步"
                  }}）</strong
                >
                <ul class="group-list">
                  <li
                    v-for="item in reviewSummary.same_name_groups"
                    :key="`same_${item.key}`"
                  >
                    <div class="group-item-copy">
                      <div class="group-item-head">
                        <span>{{ item.title }}</span>
                        <el-tag
                          :type="reviewPriorityTagType(item.priority_code)"
                          effect="light"
                        >
                          {{ item.priority_label || "待分层" }}
                        </el-tag>
                      </div>
                      <small>
                        {{ item.item_count }} 条 · 高优先
                        {{ item.high_priority_member_total }} · unresolved
                        {{ item.unresolved_total }}
                      </small>
                      <p class="group-action-copy">
                        {{ item.suggested_action || "先核对组内证据链。" }}
                      </p>
                      <div
                        v-if="item.priority_reasons?.length"
                        class="priority-reason-list"
                      >
                        <span
                          v-for="reason in item.priority_reasons"
                          :key="reason"
                          >{{ reason }}</span
                        >
                      </div>
                      <div
                        v-if="item.comparison_fields?.length"
                        class="group-compare-summary"
                      >
                        <el-tag
                          v-for="field in item.comparison_fields"
                          :key="`same_${item.key}_${field.key}`"
                          size="small"
                          :type="comparisonFieldTagType(field.status)"
                          effect="light"
                        >
                          {{ field.title }} · {{ field.summary }}
                        </el-tag>
                      </div>
                      <div
                        v-if="item.member_items?.length"
                        class="group-compare-shell"
                      >
                        <table class="group-compare-table">
                          <thead>
                            <tr>
                              <th>学校</th>
                              <th>省份</th>
                              <th>代码</th>
                              <th>官方站</th>
                              <th>招生网</th>
                              <th>章程</th>
                              <th>来源</th>
                              <th>更新</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr
                              v-for="member in item.member_items"
                              :key="`same_row_${item.key}_${member.college_id}`"
                            >
                              <td>
                                <el-button
                                  link
                                  type="primary"
                                  @click="
                                    openEvidenceForCollege(
                                      member.college_id,
                                      member,
                                    )
                                  "
                                >
                                  {{
                                    member.college_name ||
                                    `学校 ${member.college_id}`
                                  }}
                                </el-button>
                                <div class="table-muted">
                                  {{ member.review_status || "状态待确认" }} ·
                                  {{ member.priority_label || "待分层" }}
                                </div>
                              </td>
                              <td>{{ member.province || "待补齐" }}</td>
                              <td>{{ member.college_code || "待补齐" }}</td>
                              <td>
                                {{
                                  formatGroupCompareCell(member.official_site)
                                }}
                              </td>
                              <td>
                                {{
                                  formatGroupCompareCell(member.recruit_site)
                                }}
                              </td>
                              <td>{{ formatGroupChapterCell(member) }}</td>
                              <td>
                                <div class="group-source-cell">
                                  <strong>{{
                                    member.source_title || "待补齐"
                                  }}</strong>
                                  <span class="mono-text">{{
                                    formatGroupSourceUrlCell(member.source_url)
                                  }}</span>
                                </div>
                              </td>
                              <td>{{ member.updated_at || "待补齐" }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div
                        v-if="item.member_items?.length"
                        class="group-member-list"
                      >
                        <el-button
                          v-for="member in item.member_items"
                          :key="`same_${item.key}_${member.college_id}`"
                          link
                          type="primary"
                          @click="
                            openEvidenceForCollege(member.college_id, member)
                          "
                        >
                          {{ formatGroupMemberLabel(member) }}
                        </el-button>
                      </div>
                    </div>
                  </li>
                </ul>
                <el-empty
                  v-if="!reviewSummary.same_name_groups.length"
                  description="暂无同名组明细"
                />
              </div>
            </div>
          </article>
        </section>
      </el-tab-pane>

      <el-tab-pane label="证据页" name="evidence">
        <section class="soft-card panel-block">
          <div class="section-head compact">
            <div>
              <h3>单校证据链</h3>
              <p>
                按学校名、学校代码或学校 ID
                搜索，也可以从审阅表和重复组里直接跳转到单校证据链。
              </p>
            </div>
            <div class="action-row">
              <el-autocomplete
                v-model="evidenceKeyword"
                class="evidence-input"
                clearable
                :fetch-suggestions="fetchEvidenceSuggestions"
                :loading="evidenceSearchLoading"
                :trigger-on-focus="true"
                placeholder="输入学校名 / 学校代码 / 学校 ID，例如 山东示例大学 或 101"
                @input="handleEvidenceKeywordInput"
                @select="handleEvidenceSuggestionSelect"
              >
                <template #default="{ item }">
                  <div class="evidence-suggestion">
                    <div class="table-strong">
                      {{ item.college_name || `学校 ${item.college_id}` }}
                    </div>
                    <div class="table-muted">
                      学校 ID {{ item.college_id }} /
                      {{ item.college_code || "无学校代码" }} /
                      {{ item.province || "省份待确认" }}
                    </div>
                  </div>
                </template>
              </el-autocomplete>
              <el-button
                type="primary"
                :loading="evidenceLoading"
                @click="loadEvidence"
                >查看</el-button
              >
            </div>
          </div>
          <el-alert
            v-if="evidenceError"
            class="gaokao-alert"
            type="warning"
            :closable="false"
            :title="evidenceError"
          />
          <el-empty
            v-if="!evidence && !evidenceLoading && !evidenceError"
            description="输入学校名、学校代码或学校 ID 后可查看证据链；如果当前只有应用侧主档，也会明确提示哪些字段仍待同步。"
          />
          <article v-else-if="evidence" class="evidence-panel">
            <div class="evidence-head">
              <div>
                <h3>
                  {{ evidence.college_name || `学校 ${evidence.college_id}` }}
                </h3>
                <p>
                  {{ evidence.college_code || "无学校代码" }} ·
                  {{ evidence.province || "省份待确认" }}
                </p>
              </div>
              <el-tag
                :type="evidence.source_available ? 'success' : 'warning'"
                effect="light"
              >
                {{
                  evidence.source_available
                    ? formatSourceMode(evidence.source_mode)
                    : "应用侧补充数据"
                }}
              </el-tag>
            </div>
            <el-alert
              v-if="evidence.message"
              class="gaokao-alert"
              type="info"
              :closable="false"
              :title="evidence.message"
            />
            <div class="evidence-grid">
              <div class="evidence-item">
                <span>官方站</span>
                <strong>{{ evidence.official_site || "待同步" }}</strong>
              </div>
              <div class="evidence-item">
                <span>招生网</span>
                <strong>{{ evidence.recruit_site || "待同步" }}</strong>
              </div>
              <div class="evidence-item">
                <span>章程入口</span>
                <strong>{{ evidence.chapter_url || "待同步" }}</strong>
              </div>
              <div class="evidence-item">
                <span>备用链接</span>
                <strong>{{ evidence.fallback_url || "待同步" }}</strong>
              </div>
              <div class="evidence-item">
                <span>来源链接</span>
                <strong>{{ evidence.source_url || "待同步" }}</strong>
              </div>
              <div class="evidence-item">
                <span>来源标题</span>
                <strong>{{ evidence.source_title || "待同步" }}</strong>
              </div>
              <div class="evidence-item">
                <span>审阅状态</span>
                <strong>{{ evidence.review_status || "待同步" }}</strong>
              </div>
              <div class="evidence-item">
                <span>抓取状态</span>
                <strong>{{ evidence.retrieval_status || "待同步" }}</strong>
              </div>
            </div>
            <ul v-if="evidence.notes.length" class="note-list">
              <li v-for="note in evidence.notes" :key="note">{{ note }}</li>
            </ul>
          </article>
        </section>
      </el-tab-pane>

      <el-tab-pane label="山东监控" name="shandong">
        <section class="soft-card panel-block">
          <div class="section-head compact">
            <div>
              <h3>山东首期数据监控</h3>
              <p>
                优先确认规则、分数线/赋分、一分一段、选科要求、投档录取和招生计划这
                6 类材料是否齐。
              </p>
            </div>
            <el-tag effect="light">{{
              shandongMonitor.data_version || "待确认"
            }}</el-tag>
          </div>
          <div class="review-metrics">
            <article class="review-metric-card">
              <span>已接入板块</span>
              <strong>{{ shandongMonitor.ready_section_total }}</strong>
              <p>当前可直接展示或已有应用侧补充口径的山东板块数。</p>
            </article>
            <article class="review-metric-card">
              <span>待补齐板块</span>
              <strong>{{ shandongMonitor.gap_section_total }}</strong>
              <p>仍处于 waiting / partial / empty 的山东板块数。</p>
            </article>
          </div>
          <el-alert
            v-for="note in shandongMonitor.priority_notes"
            :key="note"
            class="gaokao-alert"
            type="warning"
            :closable="false"
            :title="note"
          />
          <div class="monitor-grid">
            <article
              v-for="item in shandongMonitor.sections"
              :key="item.key"
              class="monitor-card"
            >
              <div class="monitor-card-head">
                <strong>{{ item.label }}</strong>
                <el-tag :type="statusTagType(item.status)" effect="light">{{
                  formatMonitorStatus(item.status)
                }}</el-tag>
              </div>
              <div class="monitor-card-value">{{ item.record_total }}</div>
              <p>最近时间：{{ item.latest_updated_at || "待同步" }}</p>
              <p>批次：{{ item.latest_batch_label || "待同步" }}</p>
              <ul v-if="item.notes.length" class="note-list compact">
                <li v-for="note in item.notes" :key="note">{{ note }}</li>
              </ul>
            </article>
          </div>
          <el-alert
            v-for="note in shandongMonitor.notes"
            :key="note"
            class="gaokao-alert"
            type="info"
            :closable="false"
            :title="note"
          />
        </section>
      </el-tab-pane>
    </el-tabs>
  </AppPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest, openFile } from "../api/client";
import AppPage from "../components/ui/AppPage.vue";
import AppStatGrid from "../components/ui/AppStatGrid.vue";
import type { PageMetaItem, StatCardItem } from "../components/ui/types";
import {
  buildCoverageMatrixRows,
  buildDataCompletionPrintPayload,
  buildDataCompletionResultCards,
  GAOKAO_DATA_COVERAGE_PRINT_STORAGE_PREFIX,
  type CoverageMatrixRow,
  type DataCompletionCard,
} from "../components/gaokao-data/dataCompletionReport";
import {
  comparisonFieldTagType,
  coverageToneTagType,
  deliveryTagType,
  formatCoverage,
  formatDistribution,
  formatFallbackLabels,
  formatGroupChapterCell,
  formatGroupCompareCell,
  formatGroupMemberLabel,
  formatGroupSourceUrlCell,
  formatGroupType,
  formatMonitorStatus,
  formatReviewFilter,
  formatReviewFocus,
  formatReviewSort,
  formatSourceMode,
  formatStatus,
  formatTableNotes,
  formatYearList,
  reviewPriorityTagType,
  riskLevelTagType,
  statusTagType,
} from "../components/gaokao-data/gaokaoDataFormatters";
import type {
  GaokaoCollegeEvidence,
  GaokaoCollegeOption,
  GaokaoDataHealth,
  GaokaoDataOverview,
  GaokaoImportBatch,
  GaokaoReviewSummary,
  GaokaoShandongMonitor,
} from "../components/gaokao-data/gaokaoDataTypes";
import {
  formatGaokaoCollegeEvidenceOptionLabel,
  resolveGaokaoEvidenceCollegeId,
} from "../utils/gaokaoEvidence";
import {
  buildGaokaoOverviewGapCards,
  type GaokaoOverviewGapCard,
} from "../utils/gaokaoOverview";
import { gaokaoDataCoveragePrintPreviewPath } from "../utils/print";
import { formatUserActionError } from "../utils/userFeedback";

const activeTab = ref("overview");
const reviewFilter = ref("all");
const reviewFocus = ref("all");
const reviewSort = ref("priority_desc");
const reviewKeyword = ref("");
const evidenceKeyword = ref("");
const evidenceSelectedCollegeId = ref<number | null>(null);
const evidenceCollegeOptions = ref<GaokaoCollegeOption[]>([]);
const evidenceLoading = ref(false);
const evidenceSearchLoading = ref(false);
const evidenceError = ref("");
const evidence = ref<GaokaoCollegeEvidence | null>(null);

const overview = reactive<GaokaoDataOverview>({
  source_mode: "doc_baseline",
  data_version: null,
  generated_at: null,
  school_total: 0,
  recruit_site_covered: 0,
  recruit_site_coverage_rate: null,
  chapter_url_covered: 0,
  chapter_url_coverage_rate: null,
  fallback_url_covered: 0,
  duplicate_group_total: null,
  same_name_cross_site_group_total: null,
  recent_batch_label: null,
  last_updated_at: null,
  notes: [],
  core_tables: [],
});

const importBatches = ref<GaokaoImportBatch[]>([]);
const dataHealth = reactive<GaokaoDataHealth>({
  db_path: "",
  exists: false,
  generated_at: "",
  schema_version: null,
  province: "山东",
  expected_years: [],
  field_explanations: [],
  delivery_assessment: null,
  tables: [],
  coverage: [],
  publication_status: [],
  special_type_risks: [],
  audit_summary: [],
  gaps: [],
  summary: "",
});
const reviewSummary = reactive<GaokaoReviewSummary>({
  source_available: false,
  source_mode: "doc_baseline",
  active_filter: "all",
  active_focus: "all",
  active_sort: "priority_desc",
  active_keyword: null,
  matched_total: null,
  queue_total: 0,
  duplicate_group_total: null,
  same_name_cross_site_group_total: null,
  counts: [],
  quick_filters: [],
  items: [],
  priority_groups: [],
  duplicate_groups: [],
  same_name_groups: [],
  highlights: [],
  notes: [],
});
const shandongMonitor = reactive<GaokaoShandongMonitor>({
  province: "山东",
  data_version: null,
  ready_section_total: 0,
  gap_section_total: 0,
  priority_notes: [],
  sections: [],
  notes: [],
});

const activeReviewQuickFilter = computed(() => {
  return (
    reviewSummary.quick_filters.find(
      (item) => item.code === reviewSummary.active_focus,
    ) ?? null
  );
});
const overviewGapCards = computed<GaokaoOverviewGapCard[]>(() =>
  buildGaokaoOverviewGapCards(overview.core_tables),
);
const dataHealthSummary = computed(() => {
  return dataHealth.tables.reduce(
    (summary, item) => {
      if (item.status === "missing") summary.missing += 1;
      if (item.status === "empty") summary.empty += 1;
      if (item.status === "gap") summary.gap += 1;
      return summary;
    },
    { missing: 0, empty: 0, gap: 0 },
  );
});
const dataCompletionCards = computed<DataCompletionCard[]>(() =>
  buildDataCompletionResultCards(dataHealth),
);
const coverageMatrixRows = computed<CoverageMatrixRow[]>(() =>
  buildCoverageMatrixRows(dataHealth),
);
const pageMeta = computed<PageMetaItem[]>(() => [
  { label: "当前版本", value: overview.data_version || "待确认" },
  { label: "数据来源", value: formatSourceMode(overview.source_mode) },
  { label: "学校总数", value: overview.school_total || "-" },
  { label: "山东监控", value: shandongMonitor.sections.length },
  { label: "P0 缺口", value: dataHealth.gaps.length },
]);
const overviewStatCards = computed<StatCardItem[]>(() => [
  {
    label: "学校总数",
    value: overview.school_total || 0,
    help: "当前高考高校主档总量。",
    tone: "primary",
  },
  {
    label: "招生网覆盖",
    value: formatCoverage(
      overview.recruit_site_covered,
      overview.recruit_site_coverage_rate,
    ),
    help: "已确认 recruit_site 的学校数与覆盖率。",
    tone: "success",
  },
  {
    label: "章程链接覆盖",
    value: formatCoverage(
      overview.chapter_url_covered,
      overview.chapter_url_coverage_rate,
    ),
    help: "已确认 chapter_url 的学校数与覆盖率。",
    tone: "info",
  },
  {
    label: "备用链接覆盖",
    value: overview.fallback_url_covered || 0,
    help: "没有正式章程入口时可用于只读兜底的链接数。",
    tone: "neutral",
  },
  {
    label: "重复组",
    value: overview.duplicate_group_total ?? "待同步",
    help: "需要进一步人工裁决的重复院校组。",
    tone: overview.duplicate_group_total ? "warning" : "neutral",
  },
  {
    label: "同名跨站组",
    value: overview.same_name_cross_site_group_total ?? "待同步",
    help: "学校名称相同但来源站点不同的组数。",
    tone: overview.same_name_cross_site_group_total ? "warning" : "neutral",
  },
]);
const coverageStatCards = computed<StatCardItem[]>(() => [
  {
    label: "核心表缺失",
    value: dataHealthSummary.value.missing,
    help: "健康检查里未找到的核心表数量。",
    tone: dataHealthSummary.value.missing ? "danger" : "success",
  },
  {
    label: "空表",
    value: dataHealthSummary.value.empty,
    help: "核心表存在但当前没有记录的数量。",
    tone: dataHealthSummary.value.empty ? "warning" : "success",
  },
  {
    label: "需关注表",
    value: dataHealthSummary.value.gap,
    help: "有数据但明显存在交付缺口的表。",
    tone: dataHealthSummary.value.gap ? "warning" : "success",
  },
  {
    label: "P0 缺口",
    value: dataHealth.gaps.length,
    help: "按交付计划 P0 规则自动识别出的数据缺口。",
    tone: dataHealth.gaps.length ? "warning" : "success",
  },
]);

async function reloadAll(): Promise<void> {
  await Promise.all([
    loadOverview(),
    loadDataHealth(),
    loadImportBatches(),
    loadReviewSummary(),
    loadShandongMonitor(),
  ]);
}

async function loadOverview(): Promise<void> {
  const payload = await apiRequest<GaokaoDataOverview>(
    "/api/gaokao/data-overview",
  );
  Object.assign(overview, payload);
}

async function loadImportBatches(): Promise<void> {
  importBatches.value = await apiRequest<GaokaoImportBatch[]>(
    "/api/gaokao/import-batches",
  );
}

async function loadDataHealth(): Promise<void> {
  const payload = await apiRequest<GaokaoDataHealth>("/api/gaokao/data-health");
  Object.assign(dataHealth, payload);
}

function openDataCoverageReportPrintPreview(): void {
  if (!dataHealth.exists || !dataHealth.coverage.length) {
    ElMessage.warning("请先刷新高考数据健康检查后再打印覆盖报告。");
    return;
  }
  const storageKey = `${GAOKAO_DATA_COVERAGE_PRINT_STORAGE_PREFIX}${Date.now()}`;
  window.localStorage.setItem(
    storageKey,
    JSON.stringify(buildDataCompletionPrintPayload(dataHealth)),
  );
  openFile(gaokaoDataCoveragePrintPreviewPath(storageKey));
}

async function loadReviewSummary(): Promise<void> {
  const params = new URLSearchParams({ status: reviewFilter.value });
  params.set("focus", reviewFocus.value);
  params.set("sort", reviewSort.value);
  if (reviewKeyword.value.trim()) {
    params.set("keyword", reviewKeyword.value.trim());
  }
  const payload = await apiRequest<GaokaoReviewSummary>(
    `/api/gaokao/review-summary?${params.toString()}`,
  );
  Object.assign(reviewSummary, payload);
  reviewFilter.value = payload.active_filter;
  reviewFocus.value = payload.active_focus;
  reviewSort.value = payload.active_sort;
}

async function applyReviewFocus(focusCode: string): Promise<void> {
  reviewFocus.value = focusCode;
  await loadReviewSummary();
}

async function loadShandongMonitor(): Promise<void> {
  const payload = await apiRequest<GaokaoShandongMonitor>(
    "/api/gaokao/shandong-monitor",
  );
  Object.assign(shandongMonitor, payload);
}

async function searchEvidenceColleges(
  query: string,
): Promise<GaokaoCollegeOption[]> {
  evidenceSearchLoading.value = true;
  try {
    const suffix = query.trim()
      ? `?q=${encodeURIComponent(query.trim())}&limit=10`
      : "?limit=10";
    const payload = await apiRequest<GaokaoCollegeOption[]>(
      `/api/gaokao/college-options${suffix}`,
    );
    evidenceCollegeOptions.value = payload;
    return payload;
  } catch (error) {
    ElMessage.error(
      formatUserActionError(
        "搜索学校候选",
        error,
        "请减少关键词长度，或直接输入学校 ID 后查看。",
      ),
    );
    evidenceCollegeOptions.value = [];
    return [];
  } finally {
    evidenceSearchLoading.value = false;
  }
}

async function fetchEvidenceSuggestions(
  queryString: string,
  callback: (items: GaokaoCollegeOption[]) => void,
): Promise<void> {
  callback(await searchEvidenceColleges(queryString));
}

function handleEvidenceSuggestionSelect(option: GaokaoCollegeOption): void {
  evidenceSelectedCollegeId.value = option.college_id;
  evidenceKeyword.value = formatGaokaoCollegeEvidenceOptionLabel(option);
}

function handleEvidenceKeywordInput(): void {
  evidenceSelectedCollegeId.value = null;
  if (!evidenceKeyword.value.trim()) {
    evidenceCollegeOptions.value = [];
  }
}

async function loadEvidence(): Promise<void> {
  let collegeId = resolveGaokaoEvidenceCollegeId({
    keyword: evidenceKeyword.value,
    selectedCollegeId: evidenceSelectedCollegeId.value,
    candidates: evidenceCollegeOptions.value,
  });

  if (!collegeId) {
    const matchedOptions = await searchEvidenceColleges(evidenceKeyword.value);
    collegeId = resolveGaokaoEvidenceCollegeId({
      keyword: evidenceKeyword.value,
      selectedCollegeId: evidenceSelectedCollegeId.value,
      candidates: matchedOptions,
    });
    if (!collegeId) {
      evidenceError.value = evidenceKeyword.value.trim()
        ? "请输入学校 ID，或从候选列表中选择学校。"
        : "请输入学校名、学校代码或学校 ID。";
      evidence.value = null;
      return;
    }
  }

  evidenceLoading.value = true;
  evidenceError.value = "";
  try {
    evidence.value = await apiRequest<GaokaoCollegeEvidence>(
      `/api/gaokao/college-evidence/${collegeId}`,
    );
    evidenceSelectedCollegeId.value = collegeId;
    if (evidence.value) {
      evidenceKeyword.value = formatGaokaoCollegeEvidenceOptionLabel({
        college_id: evidence.value.college_id,
        college_name: evidence.value.college_name,
        college_code: evidence.value.college_code,
        province: evidence.value.province,
        review_status: evidence.value.review_status,
        source_mode: evidence.value.source_mode,
      });
    }
  } catch (error) {
    evidence.value = null;
    evidenceError.value = formatUserActionError(
      "加载单校证据链",
      error,
      "请换用学校代码或从候选列表选择学校后重试。",
    );
  } finally {
    evidenceLoading.value = false;
  }
}

async function openEvidenceForCollege(
  collegeId?: number | null,
  option?: {
    college_name?: string | null;
    college_code?: string | null;
    province?: string | null;
    review_status?: string | null;
    source_mode?: string | null;
  },
): Promise<void> {
  if (!collegeId) {
    ElMessage.warning("当前记录没有学校 ID，无法打开证据页。");
    return;
  }
  activeTab.value = "evidence";
  evidenceSelectedCollegeId.value = collegeId;
  evidenceKeyword.value = formatGaokaoCollegeEvidenceOptionLabel({
    college_id: collegeId,
    college_name: option?.college_name,
    college_code: option?.college_code,
    province: option?.province,
    review_status: option?.review_status,
    source_mode: option?.source_mode,
  });
  evidenceCollegeOptions.value = [];
  await loadEvidence();
}

onMounted(async () => {
  try {
    await reloadAll();
  } catch (error) {
    ElMessage.error(
      formatUserActionError(
        "加载高考数据驾驶舱",
        error,
        "确认本地服务已启动后点击“刷新驾驶舱”。",
      ),
    );
  }
});
</script>

<style scoped>
.gaokao-tabs {
  display: grid;
  gap: 18px;
}

.gaokao-alert {
  margin-top: 14px;
}

.overview-copy {
  display: grid;
  gap: 10px;
}

.overview-highlight {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.overview-highlight strong {
  font-size: 28px;
  color: #1d3147;
}

.overview-highlight span {
  color: #6b7f92;
  font-size: 13px;
}

.completion-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.completion-card {
  display: grid;
  gap: 8px;
  min-height: 142px;
  padding: 14px;
  border: 1px solid #d8e1ea;
  border-radius: 8px;
  background: #ffffff;
}

.completion-card.tone-success {
  border-color: #9ed6b6;
  background: #f3fbf6;
}

.completion-card.tone-warning {
  border-color: #f0d39a;
  background: #fffaf0;
}

.completion-card.tone-danger {
  border-color: #f2b5b5;
  background: #fff5f5;
}

.completion-card.tone-info {
  border-color: #b7d1ef;
  background: #f4f8ff;
}

.completion-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.completion-card p,
.completion-card span {
  margin: 0;
  color: #4f6275;
  line-height: 1.6;
}

.completion-card span {
  font-size: 13px;
}

.coverage-matrix-shell {
  overflow-x: auto;
}

.coverage-matrix-table {
  width: 100%;
  min-width: 960px;
  border-collapse: collapse;
  font-size: 13px;
}

.coverage-matrix-table th,
.coverage-matrix-table td {
  padding: 11px 10px;
  border-bottom: 1px solid #e5edf5;
  text-align: left;
  vertical-align: top;
}

.coverage-matrix-table th {
  color: #5f7386;
  font-weight: 700;
  background: #f7fafc;
}

.coverage-matrix-table td:first-child {
  min-width: 180px;
}

.coverage-matrix-table td:first-child strong,
.coverage-matrix-table td:first-child span {
  display: block;
}

.coverage-matrix-table td:first-child span {
  margin-top: 4px;
  color: #6b7f92;
}

.review-filter,
.evidence-input {
  width: 260px;
}

.review-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.review-metric-card {
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(111, 129, 145, 0.14);
  background: rgba(255, 255, 255, 0.7);
}

.review-metric-card span {
  display: block;
  color: #6a7e91;
  font-size: 13px;
}

.review-metric-card strong {
  display: block;
  margin-top: 10px;
  color: #1f354a;
  font-size: 28px;
}

.review-metric-card p {
  margin: 10px 0 0;
  color: #798b9b;
  line-height: 1.55;
}

.review-filter-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 14px;
  color: #6c8194;
  font-size: 13px;
}

.review-quick-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.review-quick-filter-copy {
  margin: 12px 0 0;
  color: #6e8295;
  font-size: 13px;
  line-height: 1.6;
}

.group-section {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.group-priority-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.group-priority-card {
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(111, 129, 145, 0.14);
  background: linear-gradient(
    180deg,
    rgba(255, 250, 244, 0.95),
    rgba(250, 245, 239, 0.9)
  );
}

.group-priority-head,
.group-item-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.group-priority-head strong {
  color: #1d3348;
}

.group-priority-head p,
.group-action-copy {
  margin: 8px 0 0;
  color: #6f8396;
  line-height: 1.55;
}

.group-list {
  display: grid;
  gap: 10px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.group-list li {
  display: block;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(244, 247, 250, 0.92);
}

.group-item-copy {
  display: grid;
  gap: 8px;
}

.group-list small {
  color: #72889c;
}

.group-member-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.priority-reason-list,
.inline-tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.priority-reason-list span {
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(235, 241, 246, 0.92);
  color: #597085;
  font-size: 12px;
  line-height: 1.4;
}

.group-compare-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.group-compare-shell {
  overflow-x: auto;
}

.group-compare-table {
  width: 100%;
  min-width: 760px;
  border-collapse: collapse;
  font-size: 13px;
}

.group-compare-table th,
.group-compare-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(111, 129, 145, 0.14);
  text-align: left;
  vertical-align: top;
  color: #5e7588;
}

.group-compare-table th {
  color: #1d3348;
  font-weight: 700;
  white-space: nowrap;
}

.group-source-cell {
  display: grid;
  gap: 4px;
}

.group-source-cell strong {
  color: #1f354a;
  font-weight: 600;
  line-height: 1.5;
}

.evidence-panel {
  display: grid;
  gap: 18px;
}

.evidence-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.evidence-head h3 {
  margin: 0;
  color: #1d3349;
}

.evidence-head p {
  margin: 6px 0 0;
  color: #72879b;
}

.evidence-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.evidence-item {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(244, 247, 250, 0.94);
  border: 1px solid rgba(111, 129, 145, 0.12);
}

.evidence-item span {
  display: block;
  color: #6e8295;
  font-size: 12px;
  letter-spacing: 0.04em;
}

.evidence-item strong {
  display: block;
  margin-top: 8px;
  color: #1f354a;
  line-height: 1.55;
  word-break: break-all;
}

.evidence-suggestion {
  display: grid;
  gap: 4px;
  padding: 4px 0;
}

.monitor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.monitor-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(111, 129, 145, 0.14);
  background: rgba(255, 255, 255, 0.75);
}

.overview-gap-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.overview-gap-card {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(204, 174, 96, 0.28);
  background: linear-gradient(
    180deg,
    rgba(255, 250, 240, 0.96),
    rgba(255, 255, 255, 0.92)
  );
}

.health-gap-list {
  display: grid;
  gap: 10px;
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
}

.health-gap-list li {
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 246, 232, 0.95);
  color: #775d2c;
  line-height: 1.55;
}

.health-type-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.delivery-assessment,
.coverage-readiness {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: #667c90;
  line-height: 1.55;
}

.coverage-readiness {
  margin-bottom: 6px;
}

.risk-count-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 12px;
  color: #5f768a;
  font-size: 13px;
}

.risk-explanation {
  margin: 0 0 8px;
  color: #526a7f;
  line-height: 1.55;
}

.source-doc-list {
  display: grid;
  gap: 6px;
}

.source-doc-list a {
  color: #2b6cb0;
  line-height: 1.45;
  text-decoration: none;
}

.source-doc-list a:hover {
  text-decoration: underline;
}

.coverage-detail-table {
  padding: 12px 18px;
  background: rgba(247, 250, 252, 0.9);
}

.audit-note-list {
  display: grid;
  gap: 4px;
  margin: 0;
  padding-left: 18px;
  color: #667c90;
  line-height: 1.5;
}

.monitor-card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.monitor-card-value {
  margin-top: 16px;
  font-size: 34px;
  font-weight: 780;
  color: #1d3348;
}

.monitor-card p {
  margin: 8px 0 0;
  color: #73879a;
  line-height: 1.5;
}

.note-list {
  margin: 0;
  padding-left: 18px;
  color: #72879b;
  line-height: 1.6;
}

.note-list.compact {
  margin-top: 10px;
}

.table-strong {
  color: #1d3348;
  font-weight: 700;
}

.table-muted,
.mono-text {
  color: #72889c;
  font-size: 12px;
}

.mono-text {
  word-break: break-all;
}

@media (max-width: 960px) {
  .group-section,
  .evidence-grid {
    grid-template-columns: 1fr;
  }

  .review-filter,
  .evidence-input {
    width: 100%;
  }
}
</style>
