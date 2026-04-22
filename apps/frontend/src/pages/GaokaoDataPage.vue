<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">高考数据 / 只读驾驶舱</div>
        <h2 class="page-title">高考数据</h2>
        <p class="page-subtitle">
          先看冻结基线、待审阅项、单校证据链和山东首期监控，再决定是否需要向 Windows 数据库线发起 handoff 或 contract request。
        </p>
        <div class="page-chip-row">
          <span class="page-chip"><strong>当前版本</strong>{{ overview.data_version || "待确认" }}</span>
          <span class="page-chip"><strong>数据来源</strong>{{ formatSourceMode(overview.source_mode) }}</span>
          <span class="page-chip"><strong>学校总数</strong>{{ overview.school_total || "-" }}</span>
          <span class="page-chip"><strong>山东监控</strong>{{ shandongMonitor.sections.length }}</span>
        </div>
      </div>
      <div class="action-row">
        <el-button @click="reloadAll">刷新驾驶舱</el-button>
        <el-button type="primary" @click="activeTab = 'evidence'">查看证据页</el-button>
      </div>
    </header>

    <el-tabs v-model="activeTab" class="gaokao-tabs">
      <el-tab-pane label="总览" name="overview">
        <section class="metric-grid">
          <MetricCard label="学校总数" :value="overview.school_total || 0" help-text="当前高考高校主档总量。" />
          <MetricCard
            label="招生网覆盖"
            :value="formatCoverage(overview.recruit_site_covered, overview.recruit_site_coverage_rate)"
            help-text="已确认 recruit_site 的学校数与覆盖率。"
          />
          <MetricCard
            label="章程链接覆盖"
            :value="formatCoverage(overview.chapter_url_covered, overview.chapter_url_coverage_rate)"
            help-text="已确认 chapter_url 的学校数与覆盖率。"
          />
          <MetricCard
            label="fallback_url 覆盖"
            :value="overview.fallback_url_covered || 0"
            help-text="没有正式章程入口时可用于只读兜底的链接数。"
          />
          <MetricCard
            label="重复组"
            :value="overview.duplicate_group_total ?? '待 handoff'"
            help-text="需要进一步人工裁决的重复院校组。"
          />
          <MetricCard
            label="同名跨站组"
            :value="overview.same_name_cross_site_group_total ?? '待 handoff'"
            help-text="学校名称相同但来源站点不同的组数。"
          />
        </section>

        <section class="dashboard-grid">
          <article class="soft-card panel-block">
            <div class="section-head compact">
              <div>
                <h3>当前口径</h3>
                <p>先说明这页数字来自哪里，避免把文档基线、应用侧 fallback 和 live 表结果混在一起理解。</p>
              </div>
            </div>
            <div class="overview-copy">
              <div class="overview-highlight">
                <strong>{{ overview.data_version || "待确认" }}</strong>
                <span>{{ formatSourceMode(overview.source_mode) }}</span>
              </div>
              <p>
                最近更新时间：{{ overview.last_updated_at || "待 handoff" }}；
                最近批次：{{ overview.recent_batch_label || "待 handoff" }}；
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
                <p>优先展示高考相关导入或冻结基线，帮助快速判断当前应用看到的是哪一波材料。</p>
              </div>
            </div>
            <div class="table-shell">
              <el-table :data="importBatches" stripe>
                <el-table-column label="批次" prop="batch_name" min-width="180" />
                <el-table-column label="来源" prop="source_type" width="120" />
                <el-table-column label="文件" prop="source_filename" min-width="180" />
                <el-table-column label="状态" width="110">
                  <template #default="{ row }">
                    <el-tag :type="statusTagType(row.status)" effect="light">{{ formatStatus(row.status) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="完成时间" prop="finished_at" min-width="180" />
              </el-table>
            </div>
            <el-empty v-if="!importBatches.length" description="暂无高考相关批次记录" />
          </article>
        </section>

        <section class="soft-card panel-block">
          <div class="section-head">
            <div>
              <h3>核心表统计</h3>
              <p>当前把 DB RC1 handoff 指标和应用侧可复用表放在一起看，方便区分“正式只读基线”和“当前前端已接上的模型”。</p>
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
                  {{ row.coverage_rate === null || row.coverage_rate === undefined ? "-" : `${row.coverage_rate}%` }}
                </template>
              </el-table-column>
              <el-table-column label="最近时间" prop="latest_updated_at" min-width="180" />
              <el-table-column label="批次/说明" prop="latest_batch_label" min-width="160" />
              <el-table-column label="状态" width="110">
                <template #default="{ row }">
                  <el-tag :type="statusTagType(row.status)" effect="light">{{ formatMonitorStatus(row.status) }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div v-if="overviewGapCards.length" class="overview-gap-grid">
            <article v-for="item in overviewGapCards" :key="item.key" class="overview-gap-card">
              <div class="monitor-card-head">
                <div>
                  <div class="table-strong">{{ item.label }}</div>
                  <p>{{ item.summary }}</p>
                </div>
                <el-tag :type="statusTagType(item.status)" effect="light">{{ formatMonitorStatus(item.status) }}</el-tag>
              </div>
              <div class="review-filter-summary">
                <span>应用侧记录：{{ item.record_total }}</span>
                <span>最近时间：{{ item.latest_updated_at || "未导入" }}</span>
                <span>批次/说明：{{ item.latest_batch_label || "待确认" }}</span>
              </div>
              <ul v-if="item.notes.length" class="note-list compact">
                <li v-for="note in item.notes" :key="note">{{ note }}</li>
              </ul>
            </article>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="数据审阅" name="review">
        <section class="soft-card panel-block">
          <div class="section-head compact">
            <div>
              <h3>审阅队列</h3>
              <p>先看哪类问题还在队列里，再决定是等待 Windows handoff，还是只在文档层跟进。</p>
            </div>
            <div class="action-row">
              <el-select v-model="reviewFilter" class="review-filter" placeholder="审阅状态" @change="loadReviewSummary">
                <el-option label="全部" value="all" />
                <el-option label="待人工复核" value="pending_manual_review" />
                <el-option label="待人工复核（已有官方候选）" value="pending_manual_review_with_official_candidate" />
                <el-option label="仍未解决" value="unresolved" />
              </el-select>
              <el-select v-model="reviewSort" class="review-filter" placeholder="排序方式" @change="loadReviewSummary">
                <el-option label="优先级优先" value="priority_desc" />
                <el-option label="最近更新时间" value="updated_desc" />
              </el-select>
              <el-input
                v-model="reviewKeyword"
                class="review-filter"
                clearable
                placeholder="按学校名 / code / 省份 / 招生网关键词检索"
                @keyup.enter="loadReviewSummary"
              />
              <el-button @click="loadReviewSummary">刷新</el-button>
            </div>
          </div>
          <div class="review-metrics">
            <article v-for="item in reviewSummary.counts" :key="item.code" class="review-metric-card">
              <span>{{ item.title }}</span>
              <strong>{{ item.count ?? "待 handoff" }}</strong>
              <p>{{ item.description }}</p>
            </article>
          </div>
          <div v-if="reviewSummary.quick_filters.length" class="review-quick-filters">
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
            <span>当前过滤：{{ formatReviewFilter(reviewSummary.active_filter) }}</span>
            <span>优先视图：{{ formatReviewFocus(reviewSummary.active_focus) }}</span>
            <span>排序：{{ formatReviewSort(reviewSummary.active_sort) }}</span>
            <span>队列：{{ reviewSummary.queue_total }}</span>
            <span>关键字：{{ reviewSummary.active_keyword || "未输入" }}</span>
            <span v-if="reviewSummary.matched_total !== null">命中：{{ reviewSummary.matched_total }}</span>
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
                <p>当前过滤：{{ formatReviewFilter(reviewSummary.active_filter) }}。</p>
              </div>
            </div>
            <div class="table-shell">
              <el-table :data="reviewSummary.items" stripe>
                <el-table-column label="学校" min-width="180">
                  <template #default="{ row }">
                    <div class="table-strong">{{ row.college_name || "-" }}</div>
                    <div class="table-muted">ID {{ row.college_id ?? "-" }} / {{ row.college_code || "无 code" }}</div>
                    <div v-if="row.duplicate_group_key || row.same_name_group_key" class="inline-tag-row">
                      <el-tag v-if="row.duplicate_group_key" size="small" effect="light" type="warning">重复组</el-tag>
                      <el-tag v-if="row.same_name_group_key" size="small" effect="light" type="info">同名组</el-tag>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="优先级" min-width="220">
                  <template #default="{ row }">
                    <el-tag :type="reviewPriorityTagType(row.priority_code)" effect="light">
                      {{ row.priority_label || "待分层" }}
                    </el-tag>
                    <div v-if="row.priority_reasons?.length" class="priority-reason-list">
                      <span v-for="reason in row.priority_reasons" :key="reason">{{ reason }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="审阅状态" prop="review_status" min-width="160" />
                <el-table-column label="抓取状态" prop="retrieval_status" min-width="140" />
                <el-table-column label="招生网" min-width="220">
                  <template #default="{ row }">
                    <span class="mono-text">{{ row.recruit_site || "-" }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="章程" min-width="220">
                  <template #default="{ row }">
                    <span class="mono-text">{{ row.chapter_url || row.fallback_url || "-" }}</span>
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
            <el-empty v-if="!reviewSummary.items.length" description="当前过滤条件下暂无学校明细" />
          </article>

          <article class="soft-card panel-block">
            <div class="section-head compact">
              <div>
                <h3>重复 / 同名组</h3>
                <p>这两类组最适合用来判断还要不要继续催 Windows 线做语义裁决。</p>
              </div>
            </div>
            <div v-if="reviewSummary.priority_groups.length" class="group-priority-strip">
              <article
                v-for="item in reviewSummary.priority_groups"
                :key="`priority_${item.group_type}_${item.key}`"
                class="group-priority-card"
              >
                <div class="group-priority-head">
                  <div>
                    <strong>{{ item.title }}</strong>
                    <p>{{ formatGroupType(item.group_type) }} · {{ item.item_count }} 条记录</p>
                  </div>
                  <el-tag :type="reviewPriorityTagType(item.priority_code)" effect="light">
                    {{ item.priority_label || "待分层" }}
                  </el-tag>
                </div>
                <p class="group-action-copy">{{ item.suggested_action || "先打开组内证据链核对来源。" }}</p>
                <div v-if="item.priority_reasons?.length" class="priority-reason-list">
                  <span v-for="reason in item.priority_reasons" :key="reason">{{ reason }}</span>
                </div>
                <div v-if="item.comparison_fields?.length" class="group-compare-summary">
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
                <strong>重复组（命中 {{ reviewSummary.duplicate_groups.length }} / 全量 {{ reviewSummary.duplicate_group_total ?? "待 handoff" }}）</strong>
                <ul class="group-list">
                  <li v-for="item in reviewSummary.duplicate_groups" :key="`duplicate_${item.key}`">
                    <div class="group-item-copy">
                      <div class="group-item-head">
                        <span>{{ item.title }}</span>
                        <el-tag :type="reviewPriorityTagType(item.priority_code)" effect="light">
                          {{ item.priority_label || "待分层" }}
                        </el-tag>
                      </div>
                      <small>
                        {{ item.item_count }} 条 · 高优先 {{ item.high_priority_member_total }} · unresolved {{ item.unresolved_total }}
                      </small>
                      <p class="group-action-copy">{{ item.suggested_action || "先核对组内证据链。" }}</p>
                      <div v-if="item.priority_reasons?.length" class="priority-reason-list">
                        <span v-for="reason in item.priority_reasons" :key="reason">{{ reason }}</span>
                      </div>
                      <div v-if="item.comparison_fields?.length" class="group-compare-summary">
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
                      <div v-if="item.member_items?.length" class="group-compare-shell">
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
                            <tr v-for="member in item.member_items" :key="`duplicate_row_${item.key}_${member.college_id}`">
                              <td>
                                <el-button
                                  link
                                  type="primary"
                                  @click="openEvidenceForCollege(member.college_id, member)"
                                >
                                  {{ member.college_name || `学校 ${member.college_id}` }}
                                </el-button>
                                <div class="table-muted">
                                  {{ member.review_status || "状态待确认" }} · {{ member.priority_label || "待分层" }}
                                </div>
                              </td>
                              <td>{{ member.province || "待补齐" }}</td>
                              <td>{{ member.college_code || "待补齐" }}</td>
                              <td>{{ formatGroupCompareCell(member.official_site) }}</td>
                              <td>{{ formatGroupCompareCell(member.recruit_site) }}</td>
                              <td>{{ formatGroupChapterCell(member) }}</td>
                              <td>
                                <div class="group-source-cell">
                                  <strong>{{ member.source_title || "待补齐" }}</strong>
                                  <span class="mono-text">{{ formatGroupSourceUrlCell(member.source_url) }}</span>
                                </div>
                              </td>
                              <td>{{ member.updated_at || "待补齐" }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div v-if="item.member_items?.length" class="group-member-list">
                        <el-button
                          v-for="member in item.member_items"
                          :key="`duplicate_${item.key}_${member.college_id}`"
                          link
                          type="primary"
                          @click="openEvidenceForCollege(member.college_id, member)"
                        >
                          {{ formatGroupMemberLabel(member) }}
                        </el-button>
                      </div>
                    </div>
                  </li>
                </ul>
                <el-empty v-if="!reviewSummary.duplicate_groups.length" description="暂无重复组明细" />
              </div>
              <div>
                <strong>同名跨站组（命中 {{ reviewSummary.same_name_groups.length }} / 全量 {{ reviewSummary.same_name_cross_site_group_total ?? "待 handoff" }}）</strong>
                <ul class="group-list">
                  <li v-for="item in reviewSummary.same_name_groups" :key="`same_${item.key}`">
                    <div class="group-item-copy">
                      <div class="group-item-head">
                        <span>{{ item.title }}</span>
                        <el-tag :type="reviewPriorityTagType(item.priority_code)" effect="light">
                          {{ item.priority_label || "待分层" }}
                        </el-tag>
                      </div>
                      <small>
                        {{ item.item_count }} 条 · 高优先 {{ item.high_priority_member_total }} · unresolved {{ item.unresolved_total }}
                      </small>
                      <p class="group-action-copy">{{ item.suggested_action || "先核对组内证据链。" }}</p>
                      <div v-if="item.priority_reasons?.length" class="priority-reason-list">
                        <span v-for="reason in item.priority_reasons" :key="reason">{{ reason }}</span>
                      </div>
                      <div v-if="item.comparison_fields?.length" class="group-compare-summary">
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
                      <div v-if="item.member_items?.length" class="group-compare-shell">
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
                            <tr v-for="member in item.member_items" :key="`same_row_${item.key}_${member.college_id}`">
                              <td>
                                <el-button
                                  link
                                  type="primary"
                                  @click="openEvidenceForCollege(member.college_id, member)"
                                >
                                  {{ member.college_name || `学校 ${member.college_id}` }}
                                </el-button>
                                <div class="table-muted">
                                  {{ member.review_status || "状态待确认" }} · {{ member.priority_label || "待分层" }}
                                </div>
                              </td>
                              <td>{{ member.province || "待补齐" }}</td>
                              <td>{{ member.college_code || "待补齐" }}</td>
                              <td>{{ formatGroupCompareCell(member.official_site) }}</td>
                              <td>{{ formatGroupCompareCell(member.recruit_site) }}</td>
                              <td>{{ formatGroupChapterCell(member) }}</td>
                              <td>
                                <div class="group-source-cell">
                                  <strong>{{ member.source_title || "待补齐" }}</strong>
                                  <span class="mono-text">{{ formatGroupSourceUrlCell(member.source_url) }}</span>
                                </div>
                              </td>
                              <td>{{ member.updated_at || "待补齐" }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div v-if="item.member_items?.length" class="group-member-list">
                        <el-button
                          v-for="member in item.member_items"
                          :key="`same_${item.key}_${member.college_id}`"
                          link
                          type="primary"
                          @click="openEvidenceForCollege(member.college_id, member)"
                        >
                          {{ formatGroupMemberLabel(member) }}
                        </el-button>
                      </div>
                    </div>
                  </li>
                </ul>
                <el-empty v-if="!reviewSummary.same_name_groups.length" description="暂无同名组明细" />
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
              <p>按学校名、code 或 ID 搜索，也可以从审阅表和重复组里直接跳转到单校证据链。</p>
            </div>
            <div class="action-row">
              <el-autocomplete
                v-model="evidenceKeyword"
                class="evidence-input"
                clearable
                :fetch-suggestions="fetchEvidenceSuggestions"
                :loading="evidenceSearchLoading"
                :trigger-on-focus="true"
                placeholder="输入学校名 / code / ID，例如 山东示例大学 或 101"
                @input="handleEvidenceKeywordInput"
                @select="handleEvidenceSuggestionSelect"
              >
                <template #default="{ item }">
                  <div class="evidence-suggestion">
                    <div class="table-strong">{{ item.college_name || `学校 ${item.college_id}` }}</div>
                    <div class="table-muted">
                      ID {{ item.college_id }} / {{ item.college_code || "无 code" }} / {{ item.province || "省份待确认" }}
                    </div>
                  </div>
                </template>
              </el-autocomplete>
              <el-button type="primary" :loading="evidenceLoading" @click="loadEvidence">查看</el-button>
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
            description="输入学校名、code 或 ID 后可查看证据链；如果当前只有应用侧主档，也会明确提示哪些字段仍待 handoff。"
          />
          <article v-else-if="evidence" class="evidence-panel">
            <div class="evidence-head">
              <div>
                <h3>{{ evidence.college_name || `学校 ${evidence.college_id}` }}</h3>
                <p>{{ evidence.college_code || "无 code" }} · {{ evidence.province || "省份待确认" }}</p>
              </div>
              <el-tag :type="evidence.source_available ? 'success' : 'warning'" effect="light">
                {{ evidence.source_available ? formatSourceMode(evidence.source_mode) : "Fallback" }}
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
                <strong>{{ evidence.official_site || "待 handoff" }}</strong>
              </div>
              <div class="evidence-item">
                <span>招生网</span>
                <strong>{{ evidence.recruit_site || "待 handoff" }}</strong>
              </div>
              <div class="evidence-item">
                <span>章程入口</span>
                <strong>{{ evidence.chapter_url || "待 handoff" }}</strong>
              </div>
              <div class="evidence-item">
                <span>fallback_url</span>
                <strong>{{ evidence.fallback_url || "待 handoff" }}</strong>
              </div>
              <div class="evidence-item">
                <span>来源链接</span>
                <strong>{{ evidence.source_url || "待 handoff" }}</strong>
              </div>
              <div class="evidence-item">
                <span>来源标题</span>
                <strong>{{ evidence.source_title || "待 handoff" }}</strong>
              </div>
              <div class="evidence-item">
                <span>审阅状态</span>
                <strong>{{ evidence.review_status || "待 handoff" }}</strong>
              </div>
              <div class="evidence-item">
                <span>抓取状态</span>
                <strong>{{ evidence.retrieval_status || "待 handoff" }}</strong>
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
              <p>优先确认规则、分数线/赋分、一分一段、选科要求、投档录取和招生计划这 6 类材料是否齐。</p>
            </div>
            <el-tag effect="light">{{ shandongMonitor.data_version || "待确认" }}</el-tag>
          </div>
          <div class="review-metrics">
            <article class="review-metric-card">
              <span>已接入板块</span>
              <strong>{{ shandongMonitor.ready_section_total }}</strong>
              <p>当前可直接展示或已有应用侧 fallback 的山东板块数。</p>
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
            <article v-for="item in shandongMonitor.sections" :key="item.key" class="monitor-card">
              <div class="monitor-card-head">
                <strong>{{ item.label }}</strong>
                <el-tag :type="statusTagType(item.status)" effect="light">{{ formatMonitorStatus(item.status) }}</el-tag>
              </div>
              <div class="monitor-card-value">{{ item.record_total }}</div>
              <p>最近时间：{{ item.latest_updated_at || "待 handoff" }}</p>
              <p>批次：{{ item.latest_batch_label || "待 handoff" }}</p>
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
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";

import { apiRequest } from "../api/client";
import MetricCard from "../components/MetricCard.vue";
import {
  formatGaokaoCollegeEvidenceOptionLabel,
  resolveGaokaoEvidenceCollegeId,
  type GaokaoCollegeEvidenceOption,
} from "../utils/gaokaoEvidence";
import {
  buildGaokaoOverviewGapCards,
  type GaokaoOverviewGapCard,
  type GaokaoOverviewTableStat as GaokaoTableStat,
} from "../utils/gaokaoOverview";

interface GaokaoDataOverview {
  source_mode: string;
  data_version?: string | null;
  generated_at?: string | null;
  school_total: number;
  recruit_site_covered: number;
  recruit_site_coverage_rate?: number | null;
  chapter_url_covered: number;
  chapter_url_coverage_rate?: number | null;
  fallback_url_covered: number;
  duplicate_group_total?: number | null;
  same_name_cross_site_group_total?: number | null;
  recent_batch_label?: string | null;
  last_updated_at?: string | null;
  notes: string[];
  core_tables: GaokaoTableStat[];
}

interface GaokaoImportBatch {
  id: string;
  batch_name: string;
  source_type: string;
  source_filename?: string | null;
  status: string;
  finished_at?: string | null;
}

interface GaokaoReviewBucket {
  code: string;
  title: string;
  count?: number | null;
  description: string;
}

interface GaokaoReviewQuickFilter {
  code: string;
  title: string;
  count: number;
  description: string;
}

interface GaokaoReviewGroupComparisonField {
  key: string;
  title: string;
  status: string;
  distinct_total: number;
  missing_total: number;
  sample_values: string[];
  summary: string;
}

interface GaokaoReviewGroup {
  key: string;
  title: string;
  group_type?: string | null;
  item_count: number;
  comparison_fields?: GaokaoReviewGroupComparisonField[];
  priority_code?: string | null;
  priority_label?: string | null;
  priority_score?: number;
  priority_reasons?: string[];
  suggested_action?: string | null;
  high_priority_member_total: number;
  unresolved_total: number;
  missing_chapter_total: number;
  missing_recruit_site_total: number;
  member_items?: GaokaoReviewGroupMember[];
}

interface GaokaoReviewGroupMember {
  college_id?: number | null;
  college_name?: string | null;
  college_code?: string | null;
  review_status?: string | null;
  province?: string | null;
  official_site?: string | null;
  recruit_site?: string | null;
  chapter_url?: string | null;
  fallback_url?: string | null;
  effective_chapter_url?: string | null;
  source_title?: string | null;
  source_url?: string | null;
  updated_at?: string | null;
  priority_code?: string | null;
  priority_label?: string | null;
  priority_score?: number;
  priority_reasons?: string[];
}

interface GaokaoReviewItem {
  college_id?: number | null;
  college_name?: string | null;
  college_code?: string | null;
  duplicate_group_key?: string | null;
  same_name_group_key?: string | null;
  review_status?: string | null;
  retrieval_status?: string | null;
  recruit_site?: string | null;
  chapter_url?: string | null;
  fallback_url?: string | null;
  priority_code?: string | null;
  priority_label?: string | null;
  priority_score?: number;
  priority_reasons?: string[];
}

interface GaokaoCollegeOption extends GaokaoCollegeEvidenceOption {
  source_mode: string;
}

interface GaokaoReviewSummary {
  source_available: boolean;
  source_mode: string;
  active_filter: string;
  active_focus: string;
  active_sort: string;
  active_keyword?: string | null;
  matched_total?: number | null;
  queue_total: number;
  duplicate_group_total?: number | null;
  same_name_cross_site_group_total?: number | null;
  counts: GaokaoReviewBucket[];
  quick_filters: GaokaoReviewQuickFilter[];
  items: GaokaoReviewItem[];
  priority_groups: GaokaoReviewGroup[];
  duplicate_groups: GaokaoReviewGroup[];
  same_name_groups: GaokaoReviewGroup[];
  highlights: string[];
  notes: string[];
}

interface GaokaoCollegeEvidence {
  source_available: boolean;
  source_mode: string;
  college_id: number;
  college_name?: string | null;
  college_code?: string | null;
  province?: string | null;
  official_site?: string | null;
  recruit_site?: string | null;
  chapter_url?: string | null;
  fallback_url?: string | null;
  source_url?: string | null;
  source_title?: string | null;
  review_status?: string | null;
  retrieval_status?: string | null;
  message?: string | null;
  notes: string[];
}

interface GaokaoShandongMonitor {
  province: string;
  data_version?: string | null;
  ready_section_total: number;
  gap_section_total: number;
  priority_notes: string[];
  sections: GaokaoTableStat[];
  notes: string[];
}

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
  return reviewSummary.quick_filters.find((item) => item.code === reviewSummary.active_focus) ?? null;
});
const overviewGapCards = computed<GaokaoOverviewGapCard[]>(() => buildGaokaoOverviewGapCards(overview.core_tables));

async function reloadAll(): Promise<void> {
  await Promise.all([loadOverview(), loadImportBatches(), loadReviewSummary(), loadShandongMonitor()]);
}

async function loadOverview(): Promise<void> {
  const payload = await apiRequest<GaokaoDataOverview>("/api/gaokao/data-overview");
  Object.assign(overview, payload);
}

async function loadImportBatches(): Promise<void> {
  importBatches.value = await apiRequest<GaokaoImportBatch[]>("/api/gaokao/import-batches");
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
  const payload = await apiRequest<GaokaoShandongMonitor>("/api/gaokao/shandong-monitor");
  Object.assign(shandongMonitor, payload);
}

async function searchEvidenceColleges(query: string): Promise<GaokaoCollegeOption[]> {
  evidenceSearchLoading.value = true;
  try {
    const suffix = query.trim() ? `?q=${encodeURIComponent(query.trim())}&limit=10` : "?limit=10";
    const payload = await apiRequest<GaokaoCollegeOption[]>(`/api/gaokao/college-options${suffix}`);
    evidenceCollegeOptions.value = payload;
    return payload;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "学校候选加载失败");
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
        : "请输入学校名、code 或学校 ID。";
      evidence.value = null;
      return;
    }
  }

  evidenceLoading.value = true;
  evidenceError.value = "";
  try {
    evidence.value = await apiRequest<GaokaoCollegeEvidence>(`/api/gaokao/college-evidence/${collegeId}`);
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
    evidenceError.value = error instanceof Error ? error.message : "证据链加载失败";
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

function formatSourceMode(value?: string | null): string {
  const mapping: Record<string, string> = {
    doc_baseline: "同步板冻结基线",
    db_rc1_live: "本地 RC1 只读表",
    app_model_fallback: "应用侧主档 fallback",
    mixed_read_only: "混合只读视图",
  };
  return (value ? mapping[value] : null) ?? "待确认";
}

function formatCoverage(total: number, rate?: number | null): string {
  if (rate === null || rate === undefined) {
    return String(total);
  }
  return `${total} / ${rate}%`;
}

function formatStatus(value?: string | null): string {
  const mapping: Record<string, string> = {
    success: "成功",
    processing: "处理中",
    frozen: "冻结",
    failed: "失败",
  };
  return (value ? mapping[value] : null) ?? value ?? "未知";
}

function formatMonitorStatus(value?: string | null): string {
  const mapping: Record<string, string> = {
    ready: "已接入",
    partial: "部分可用",
    waiting: "待 handoff",
    empty: "暂无数据",
  };
  return (value ? mapping[value] : null) ?? "待确认";
}

function statusTagType(value?: string | null): "success" | "info" | "warning" | "danger" | undefined {
  if (["ready", "success"].includes(value ?? "")) return "success";
  if (["partial", "processing"].includes(value ?? "")) return "warning";
  if (["waiting", "frozen"].includes(value ?? "")) return "info";
  if (["failed"].includes(value ?? "")) return "danger";
  return undefined;
}

function formatReviewFilter(value?: string | null): string {
  const mapping: Record<string, string> = {
    all: "全部",
    pending_manual_review: "待人工复核",
    pending_manual_review_with_official_candidate: "待人工复核（已有官方候选）",
    unresolved: "仍未解决",
  };
  return (value ? mapping[value] : null) ?? "全部";
}

function formatReviewFocus(value?: string | null): string {
  const mapping: Record<string, string> = {
    all: "全部队列",
    high_priority: "高优先",
    missing_chapter: "缺章程",
    missing_recruit_site: "缺招生网",
    duplicate_or_same_name: "重复 / 同名组",
    unresolved: "仍未解决",
  };
  return (value ? mapping[value] : null) ?? "全部队列";
}

function formatReviewSort(value?: string | null): string {
  const mapping: Record<string, string> = {
    priority_desc: "优先级优先",
    updated_desc: "最近更新时间",
  };
  return (value ? mapping[value] : null) ?? "优先级优先";
}

function reviewPriorityTagType(value?: string | null): "success" | "warning" | "danger" | undefined {
  if (value === "high") return "danger";
  if (value === "medium") return "warning";
  if (value === "low") return "success";
  return undefined;
}

function comparisonFieldTagType(value?: string | null): "success" | "info" | "warning" | "danger" | undefined {
  if (value === "mixed") return "warning";
  if (value === "partial") return "info";
  if (value === "empty") return "danger";
  if (value === "same") return "success";
  return undefined;
}

function formatGroupMemberLabel(item: GaokaoReviewGroupMember): string {
  return formatGaokaoCollegeEvidenceOptionLabel({
    college_id: item.college_id ?? 0,
    college_name: item.college_name,
    college_code: item.college_code,
    province: item.province,
    review_status: item.review_status,
  });
}

function formatGroupType(value?: string | null): string {
  if (value === "duplicate") return "重复组";
  if (value === "same_name") return "同名跨站组";
  return "待确认分组";
}

function formatGroupCompareCell(value?: string | null): string {
  if (!value) return "待补齐";
  try {
    const parsed = new URL(value);
    return parsed.host || value;
  } catch {
    return value;
  }
}

function formatGroupSourceUrlCell(value?: string | null): string {
  if (!value) return "待补齐";
  try {
    const parsed = new URL(value);
    const pathname = parsed.pathname === "/" ? "" : parsed.pathname.replace(/\/$/, "");
    return `${parsed.host}${pathname}`;
  } catch {
    return value;
  }
}

function formatGroupChapterCell(member: GaokaoReviewGroupMember): string {
  const chapterValue = member.chapter_url || member.fallback_url || member.effective_chapter_url;
  if (!chapterValue) return "待补齐";
  const label = formatGroupCompareCell(chapterValue);
  if (!member.chapter_url && member.fallback_url) {
    return `${label}（fallback）`;
  }
  return label;
}

onMounted(async () => {
  try {
    await reloadAll();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "高考数据驾驶舱加载失败");
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
  background: linear-gradient(180deg, rgba(255, 250, 244, 0.95), rgba(250, 245, 239, 0.9));
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
  background: linear-gradient(180deg, rgba(255, 250, 240, 0.96), rgba(255, 255, 255, 0.92));
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
