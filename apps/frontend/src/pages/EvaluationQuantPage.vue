<template>
  <div class="page-shell">
    <header class="page-header">
      <div>
        <div class="page-eyebrow">教学评价 / 评教与量化</div>
        <h2 class="page-title">评教与班主任量化</h2>
        <p class="page-subtitle">
          统一维护评教模板、导入批次、量化规则版本、月度记录和学期汇总，让评价结果和过程依据放在同一条链路里。
        </p>
      </div>
      <div class="action-row">
        <el-button @click="downloadEvaluationTemplate">评教模板下载</el-button>
        <el-button @click="downloadQuantTemplate">量化模板下载</el-button>
        <el-button type="primary" @click="activeTab = 'evaluation'">进入评教</el-button>
      </div>
    </header>

    <section class="metric-grid">
      <div class="soft-card stat-card">
        <div class="metric-label">评教模板</div>
        <div class="metric-value">{{ templates.length }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">评教批次</div>
        <div class="metric-value">{{ batches.length }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">量化规则版本</div>
        <div class="metric-value">{{ ruleVersions.length }}</div>
      </div>
      <div class="soft-card stat-card">
        <div class="metric-label">量化记录</div>
        <div class="metric-value">{{ quantRecords.length }}</div>
      </div>
    </section>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="评教系统" name="evaluation">
        <div class="page-shell">
          <section class="soft-card panel-block">
            <div class="section-head">
              <div>
                <h3>评教模板</h3>
                <p>模板定义维度、题目、分值和题目权重。已有导入历史的模板不再原地改题，改版请新建模板。</p>
              </div>
              <div class="action-row">
                <el-button @click="loadTemplates">刷新</el-button>
                <el-button type="primary" @click="openCreateTemplate">新增模板</el-button>
              </div>
            </div>

            <el-table :data="templates" stripe>
              <el-table-column label="模板名称" prop="name" min-width="200" />
              <el-table-column label="对象" prop="target_type" width="120" />
              <el-table-column label="题目数" width="90">
                <template #default="{ row }">
                  {{ row.questions.length }}
                </template>
              </el-table-column>
              <el-table-column label="维度权重" min-width="220">
                <template #default="{ row }">
                  {{ formatWeight(row.weight_json) }}
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
                  <el-button link type="primary" @click="openEditTemplate(row)">编辑</el-button>
                </template>
              </el-table-column>
            </el-table>
          </section>

          <section class="soft-card panel-block">
            <div class="section-head">
              <div>
                <h3>导入与分析</h3>
                <p>导入 Excel 或 CSV 原始评教数据，按教师汇总综合得分、维度得分和题目表现。</p>
              </div>
            </div>

            <div class="filter-grid">
              <el-select v-model="evaluationImportForm.template_id" filterable placeholder="选择评教模板">
                <el-option
                  v-for="item in templates"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
              <el-select v-model="evaluationImportForm.semester_id" filterable placeholder="选择学期">
                <el-option
                  v-for="item in referenceStore.semesters"
                  :key="item.id"
                  :label="semesterLabel(item)"
                  :value="item.id"
                />
              </el-select>
              <el-upload :show-file-list="false" :auto-upload="false" :on-change="handleEvaluationImport">
                <el-button type="primary">导入评教数据</el-button>
              </el-upload>
              <el-button @click="loadBatches">刷新批次</el-button>
            </div>

            <el-alert
              v-if="evaluationImportResult"
              class="result-alert"
              :title="evaluationImportResult.message"
              type="success"
              show-icon
              :closable="false"
            />

            <el-table :data="batches" stripe style="margin-top: 16px">
              <el-table-column label="模板" prop="template_name" min-width="180" />
              <el-table-column label="学期" prop="semester_name" min-width="160" />
              <el-table-column label="来源文件" prop="source_filename" min-width="180" />
              <el-table-column label="响应数" prop="response_count" width="90" />
              <el-table-column label="教师数" prop="teacher_count" width="90" />
              <el-table-column label="状态" prop="status" width="120" />
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="selectBatch(row.id)">分析</el-button>
                </template>
              </el-table-column>
            </el-table>
          </section>

          <section v-if="evaluationOverview" class="soft-card panel-block">
            <div class="section-head">
              <div>
                <h3>批次总览</h3>
                <p>{{ evaluationOverview.template_name }} · {{ evaluationOverview.semester_name }}</p>
              </div>
            </div>

            <section class="metric-grid compact-metrics">
              <div class="soft-card stat-card">
                <div class="metric-label">教师数</div>
                <div class="metric-value">{{ evaluationOverview.teacher_count }}</div>
              </div>
              <div class="soft-card stat-card">
                <div class="metric-label">最高综合分</div>
                <div class="metric-value">{{ evaluationOverview.teacher_summaries[0]?.overall_avg_score ?? "-" }}</div>
              </div>
            </section>

            <div class="compare-toolbar">
              <div>
                <h4>批次对比</h4>
                <p>把当前批次和历史批次放在同一张表里，看教师整体是提升、回落还是持平。</p>
              </div>
              <div class="compare-selector">
                <el-select
                  v-model="selectedCompareBatchId"
                  clearable
                  filterable
                  placeholder="选择对比批次"
                  @change="handleCompareBatchChange"
                >
                  <el-option
                    v-for="item in compareBatchOptions"
                    :key="item.id"
                    :label="`${item.template_name} · ${item.semester_name} · ${item.import_time}`"
                    :value="item.id"
                  />
                </el-select>
              </div>
            </div>

            <section v-if="evaluationComparison" class="comparison-metric-grid">
              <div class="soft-card stat-card">
                <div class="metric-label">共同教师</div>
                <div class="metric-value">{{ evaluationComparison.overlap_teacher_count }}</div>
              </div>
              <div class="soft-card stat-card">
                <div class="metric-label">提升人数</div>
                <div class="metric-value comparison-up">{{ evaluationComparison.improved_count }}</div>
              </div>
              <div class="soft-card stat-card">
                <div class="metric-label">回落人数</div>
                <div class="metric-value comparison-down">{{ evaluationComparison.declined_count }}</div>
              </div>
              <div class="soft-card stat-card">
                <div class="metric-label">仅当前 / 仅历史</div>
                <div class="metric-value">
                  {{ evaluationComparison.only_current_count }} / {{ evaluationComparison.only_compare_count }}
                </div>
              </div>
            </section>

            <el-table v-if="evaluationComparison" :data="evaluationComparison.teacher_deltas" stripe style="margin-bottom: 16px">
              <el-table-column label="教师" prop="teacher_name" min-width="120" />
              <el-table-column label="当前分" prop="current_score" width="100" />
              <el-table-column label="对比分" prop="compare_score" width="100" />
              <el-table-column label="分数变化" min-width="110">
                <template #default="{ row }">
                  <span :class="deltaClass(row.score_delta)">{{ formatSignedValue(row.score_delta) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="名次变化" min-width="110">
                <template #default="{ row }">
                  <span :class="deltaClass(row.rank_delta)">
                    {{ formatRankDelta(row.rank_delta) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="样本变化" min-width="100">
                <template #default="{ row }">
                  {{ formatSignedValue(row.response_count_delta, 0) }}
                </template>
              </el-table-column>
            </el-table>

            <el-table :data="evaluationOverview.teacher_summaries" stripe>
              <el-table-column label="名次" prop="rank" width="80" />
              <el-table-column label="教师" prop="teacher_name" min-width="120" />
              <el-table-column label="综合得分" prop="overall_avg_score" width="110" />
              <el-table-column label="样本数" prop="response_count" width="90" />
              <el-table-column label="维度得分" min-width="260">
                <template #default="{ row }">
                  {{ formatWeight(row.dimension_scores_json) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="loadTeacherDetail(row.teacher_id)">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
          </section>

          <section v-if="evaluationDetail" class="soft-card panel-block">
            <div class="section-head">
              <div>
                <h3>教师评教详情</h3>
                <p>{{ evaluationDetail.teacher_name }} · 综合得分 {{ evaluationDetail.overall_avg_score }}</p>
              </div>
            </div>

            <section v-if="evaluationTeacherTrend?.points.length" class="trend-panel">
              <div class="section-head compact">
                <div>
                  <h4>历史趋势</h4>
                  <p>按同模板历史批次回看这位教师的综合得分和名次变化。</p>
                </div>
              </div>

              <div class="trend-metric-grid">
                <div class="soft-card stat-card">
                  <div class="metric-label">历史批次</div>
                  <div class="metric-value">{{ evaluationTeacherTrend.points.length }}</div>
                </div>
                <div class="soft-card stat-card">
                  <div class="metric-label">当前批次变化</div>
                  <div class="metric-value" :class="deltaClass(trendDeltaScore)">
                    {{ trendDeltaScore === null ? "-" : formatSignedValue(trendDeltaScore) }}
                  </div>
                </div>
                <div class="soft-card stat-card">
                  <div class="metric-label">历史最高分</div>
                  <div class="metric-value">{{ trendPeakScore }}</div>
                </div>
                <div class="soft-card stat-card">
                  <div class="metric-label">当前名次变化</div>
                  <div class="metric-value" :class="deltaClass(trendRankDelta)">
                    {{ formatRankDelta(trendRankDelta) }}
                  </div>
                </div>
              </div>

              <el-table :data="evaluationTeacherTrend.points" stripe style="margin-top: 16px">
                <el-table-column label="批次" min-width="220">
                  <template #default="{ row }">
                    {{ row.template_name }} · {{ row.semester_name || "-" }}
                  </template>
                </el-table-column>
                <el-table-column label="综合得分" prop="overall_avg_score" width="110" />
                <el-table-column label="名次" prop="rank" width="90" />
                <el-table-column label="样本数" prop="response_count" width="90" />
                <el-table-column label="导入时间" prop="import_time" min-width="170" />
              </el-table>
            </section>

            <div class="detail-grid-box">
              <div class="soft-card inner-card">
                <h4>维度得分</h4>
                <el-table :data="evaluationDetail.dimension_summaries" stripe>
                  <el-table-column label="维度" prop="dimension_name" min-width="140" />
                  <el-table-column label="平均分" prop="avg_score" width="100" />
                  <el-table-column label="样本数" prop="response_count" width="90" />
                </el-table>
              </div>
              <div class="soft-card inner-card">
                <h4>题目明细</h4>
                <el-table :data="evaluationDetail.question_stats" stripe>
                  <el-table-column label="维度" prop="dimension_name" width="120" />
                  <el-table-column label="题目" prop="question_text" min-width="220" />
                  <el-table-column label="平均分" prop="avg_score" width="100" />
                  <el-table-column label="样本数" prop="response_count" width="90" />
                </el-table>
              </div>
            </div>
          </section>
        </div>
      </el-tab-pane>

      <el-tab-pane label="班主任量化" name="quant">
        <div class="page-shell">
          <section class="soft-card panel-block">
            <div class="section-head">
              <div>
                <h3>量化规则版本</h3>
                <p>规则版本一旦产生记录就不能原地改规则项，避免历史得分被新规则覆盖。</p>
              </div>
              <div class="action-row">
                <el-button @click="loadRuleVersions">刷新</el-button>
                <el-button type="primary" @click="openCreateRuleVersion">新增规则版本</el-button>
              </div>
            </div>

            <div class="quant-shell">
              <div class="soft-card inner-card">
                <el-table :data="ruleVersions" stripe>
                  <el-table-column label="规则版本" prop="name" min-width="180" />
                  <el-table-column label="学期" prop="semester_name" min-width="160" />
                  <el-table-column label="默认" width="80">
                    <template #default="{ row }">
                      <el-tag :type="row.is_default ? 'success' : 'info'" effect="light">
                        {{ row.is_default ? "是" : "否" }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="状态" prop="status" width="100" />
                  <el-table-column label="操作" width="100" fixed="right">
                    <template #default="{ row }">
                      <el-button link type="primary" @click="selectRuleVersion(row.id)">规则项</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <div class="soft-card inner-card">
                <div class="section-head compact">
                  <div>
                    <h4>规则项</h4>
                    <p v-if="selectedRuleVersionMeta">
                      当前规则：{{ selectedRuleVersionMeta.name }}
                      {{ selectedRuleVersionMeta.semester_name ? ` · ${selectedRuleVersionMeta.semester_name}` : "" }}
                    </p>
                    <p v-else>先选择一个规则版本</p>
                  </div>
                  <div class="action-row">
                    <el-button :disabled="!selectedRuleVersionId" @click="addRuleItemRow">新增规则项</el-button>
                    <el-button
                      type="primary"
                      :disabled="!selectedRuleVersionId"
                      :loading="savingRuleItems"
                      @click="saveRuleItems"
                    >
                      保存规则项
                    </el-button>
                  </div>
                </div>

                <el-table :data="ruleItemRows" stripe>
                  <el-table-column label="量化项" min-width="160">
                    <template #default="{ row }">
                      <el-input v-model="row.item_name" />
                    </template>
                  </el-table-column>
                  <el-table-column label="类型" min-width="130">
                    <template #default="{ row }">
                      <el-input v-model="row.item_type" />
                    </template>
                  </el-table-column>
                  <el-table-column label="默认分值" width="110">
                    <template #default="{ row }">
                      <el-input-number v-model="row.default_score" :step="0.5" />
                    </template>
                  </el-table-column>
                  <el-table-column label="附件" width="90">
                    <template #default="{ row }">
                      <el-switch v-model="row.requires_attachment" />
                    </template>
                  </el-table-column>
                  <el-table-column label="排序" width="90">
                    <template #default="{ row }">
                      <el-input-number v-model="row.sort_order" :min="0" />
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="90">
                    <template #default="{ $index }">
                      <el-button link type="danger" @click="removeRuleItemRow($index)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </section>

          <section class="soft-card panel-block">
            <div class="section-head">
              <div>
                <h3>量化记录与汇总</h3>
                <p>按学期、教师查看量化明细和汇总，附件上传先于记录绑定。</p>
              </div>
              <div class="action-row">
                <el-button @click="reloadQuantData">刷新</el-button>
                <el-button type="primary" @click="openCreateQuantRecord">新增量化记录</el-button>
              </div>
            </div>

            <div class="filter-grid">
              <el-select v-model="quantFilters.semester_id" filterable placeholder="学期">
                <el-option
                  v-for="item in referenceStore.semesters"
                  :key="item.id"
                  :label="semesterLabel(item)"
                  :value="item.id"
                />
              </el-select>
              <el-select v-model="quantFilters.teacher_id" clearable filterable placeholder="教师">
                <el-option
                  v-for="teacher in teacherOptions"
                  :key="teacher.id"
                  :label="teacher.name"
                  :value="teacher.id"
                />
              </el-select>
              <el-select v-model="quantFilters.rule_version_id" clearable filterable placeholder="规则版本">
                <el-option
                  v-for="rule in ruleVersions"
                  :key="rule.id"
                  :label="rule.name"
                  :value="rule.id"
                />
              </el-select>
            </div>

            <div class="action-row toolbar-row">
              <el-button type="primary" @click="reloadQuantData">查询</el-button>
              <el-button @click="resetQuantFilters">重置</el-button>
            </div>

            <div class="detail-grid-box">
              <div class="soft-card inner-card">
                <h4>汇总</h4>
                <el-table :data="quantSummary" stripe>
                  <el-table-column label="教师" prop="teacher_name" min-width="120" />
                  <el-table-column label="总分" prop="total_score" width="90" />
                  <el-table-column label="加分" prop="positive_score" width="90" />
                  <el-table-column label="扣分" prop="negative_score" width="90" />
                  <el-table-column label="记录数" prop="record_count" width="90" />
                  <el-table-column label="班级" min-width="160">
                    <template #default="{ row }">
                      {{ (row.class_names ?? []).join(" / ") || "-" }}
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div class="soft-card inner-card">
                <h4>明细</h4>
                <el-table :data="quantRecords" stripe>
                  <el-table-column label="月份" prop="record_month" width="90" />
                  <el-table-column label="教师" prop="teacher_name" width="110" />
                  <el-table-column label="班级" prop="class_name" width="100" />
                  <el-table-column label="量化项" prop="item_name" min-width="160" />
                  <el-table-column label="分值" prop="score" width="80" />
                  <el-table-column label="附件" width="120">
                    <template #default="{ row }">
                      {{ row.attachments.length ? `${row.attachments.length} 个` : "-" }}
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="90" fixed="right">
                    <template #default="{ row }">
                      <el-button link type="primary" @click="openEditQuantRecord(row)">编辑</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </section>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="templateDialogVisible"
      :title="templateDialogTitle"
      width="880px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleTemplateDialogClosed"
    >
      <el-form label-width="92px">
        <div class="form-grid">
          <el-form-item label="模板名称">
            <el-input v-model="templateForm.name" />
          </el-form-item>
          <el-form-item label="对象类型">
            <el-input v-model="templateForm.target_type" />
          </el-form-item>
        </div>
      </el-form>

      <div class="section-head compact">
        <div>
          <h4>题目列表</h4>
          <p>维度权重会按题目权重自动汇总。</p>
        </div>
        <el-button @click="addTemplateQuestionRow">新增题目</el-button>
      </div>

      <el-table :data="templateQuestions" stripe>
        <el-table-column label="维度" min-width="130">
          <template #default="{ row }">
            <el-input v-model="row.dimension_name" />
          </template>
        </el-table-column>
        <el-table-column label="题目" min-width="240">
          <template #default="{ row }">
            <el-input v-model="row.question_text" />
          </template>
        </el-table-column>
        <el-table-column label="满分" width="100">
          <template #default="{ row }">
            <el-input-number v-model="row.score_max" :min="1" :max="100" />
          </template>
        </el-table-column>
        <el-table-column label="权重" width="100">
          <template #default="{ row }">
            <el-input-number v-model="row.weight" :min="0" :step="0.1" />
          </template>
        </el-table-column>
        <el-table-column label="排序" width="90">
          <template #default="{ row }">
            <el-input-number v-model="row.sort_order" :min="0" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ $index }">
            <el-button link type="danger" @click="removeTemplateQuestionRow($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="templateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingTemplate" @click="saveTemplate">保存模板</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="ruleVersionDialogVisible"
      :title="ruleVersionDialogTitle"
      width="620px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleRuleVersionDialogClosed"
    >
      <el-form label-width="92px">
        <div class="form-grid">
          <el-form-item label="版本名称">
            <el-input v-model="ruleVersionForm.name" />
          </el-form-item>
          <el-form-item label="学期">
            <el-select v-model="ruleVersionForm.semester_id" clearable filterable style="width: 100%">
              <el-option
                v-for="item in referenceStore.semesters"
                :key="item.id"
                :label="semesterLabel(item)"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="默认版本">
            <el-switch v-model="ruleVersionForm.is_default" />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="ruleVersionForm.status" style="width: 100%">
              <el-option label="active" value="active" />
              <el-option label="draft" value="draft" />
              <el-option label="archived" value="archived" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="备注">
          <el-input v-model="ruleVersionForm.note" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ruleVersionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingRuleVersion" @click="saveRuleVersion">保存版本</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="quantDialogVisible"
      :title="quantDialogTitle"
      width="760px"
      destroy-on-close
      :close-on-click-modal="false"
      @closed="handleQuantDialogClosed"
    >
      <el-form label-width="92px">
        <div class="form-grid">
          <el-form-item label="教师">
            <el-select v-model="quantForm.teacher_id" filterable style="width: 100%">
              <el-option
                v-for="teacher in teacherOptions"
                :key="teacher.id"
                :label="teacher.name"
                :value="teacher.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="班级">
            <el-select v-model="quantForm.class_id" clearable filterable style="width: 100%">
              <el-option
                v-for="item in referenceStore.classes"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="学期">
            <el-select v-model="quantForm.semester_id" filterable style="width: 100%">
              <el-option
                v-for="item in referenceStore.semesters"
                :key="item.id"
                :label="semesterLabel(item)"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="月份">
            <el-input v-model="quantForm.record_month" placeholder="YYYY-MM" />
          </el-form-item>
          <el-form-item label="规则项" class="span-two">
            <el-select v-model="quantForm.rule_item_id" filterable style="width: 100%">
              <el-option
                v-for="item in quantRuleItemOptions"
                :key="item.id"
                :label="`${item.item_name} / ${item.default_score}`"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="得分">
            <el-input-number v-model="quantForm.score" :step="0.5" />
          </el-form-item>
        </div>
        <el-form-item label="说明">
          <el-input v-model="quantForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>

      <div class="section-head compact">
        <div>
          <h4>附件</h4>
          <p>量化项要求附件时，这里必须至少上传一个文件。</p>
        </div>
      </div>
      <div class="action-row">
        <input
          ref="quantAttachmentInputRef"
          class="file-input"
          type="file"
          multiple
          @change="handleQuantAttachmentUpload"
        />
      </div>
      <div class="attachment-tags">
        <el-tag
          v-for="item in quantForm.attachments"
          :key="item.id"
          closable
          @close="removeQuantAttachment(item.id)"
        >
          {{ item.original_filename }}
        </el-tag>
        <span v-if="!quantForm.attachments.length" class="hint-text">暂无附件</span>
      </div>

      <template #footer>
        <el-button @click="quantDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingQuant" @click="saveQuantRecord">保存记录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import ElMessage from "element-plus/es/components/message/index";
import type { UploadFile } from "element-plus";

import { apiRequest, openFile, uploadFile } from "../api/client";
import { type OptionItem, useReferenceStore } from "../stores/reference";

interface TeacherOption {
  id: number;
  name: string;
}

interface UploadedAttachment {
  id: number;
  original_filename: string;
  download_url: string;
}

interface EvaluationQuestion {
  id?: number;
  dimension_name: string;
  question_text: string;
  score_max: number;
  weight: number;
  sort_order: number;
  is_active: boolean;
}

interface EvaluationTemplate {
  id: number;
  name: string;
  target_type: string;
  weight_json?: Record<string, number> | null;
  is_active: boolean;
  questions: EvaluationQuestion[];
}

interface EvaluationBatch {
  id: number;
  template_id: number;
  template_name?: string | null;
  semester_id: number;
  semester_name?: string | null;
  source_filename?: string | null;
  import_time: string;
  status: string;
  response_count: number;
  teacher_count: number;
}

interface EvaluationImportResponse {
  batch_id: number;
  message: string;
  success_rows: number;
  failed_rows: number;
}

interface EvaluationTeacherSummary {
  teacher_id: number;
  teacher_name: string;
  overall_avg_score: number;
  response_count: number;
  rank?: number | null;
  dimension_scores_json?: Record<string, number> | null;
}

interface EvaluationOverview {
  batch_id: number;
  template_name: string;
  semester_name?: string | null;
  teacher_count: number;
  teacher_summaries: EvaluationTeacherSummary[];
}

interface EvaluationBatchCompareTeacher {
  teacher_id: number;
  teacher_name: string;
  current_score: number;
  compare_score: number;
  score_delta: number;
  current_rank?: number | null;
  compare_rank?: number | null;
  rank_delta?: number | null;
  response_count_delta: number;
}

interface EvaluationBatchCompare {
  batch_id: number;
  compare_batch_id: number;
  batch_name: string;
  compare_batch_name: string;
  overlap_teacher_count: number;
  improved_count: number;
  declined_count: number;
  unchanged_count: number;
  only_current_count: number;
  only_compare_count: number;
  teacher_deltas: EvaluationBatchCompareTeacher[];
}

interface EvaluationDimensionSummary {
  dimension_name: string;
  avg_score: number;
  response_count: number;
}

interface EvaluationQuestionStat {
  question_text: string;
  dimension_name: string;
  avg_score: number;
  response_count: number;
}

interface EvaluationTeacherDetail {
  batch_id: number;
  teacher_id: number;
  teacher_name: string;
  overall_avg_score: number;
  response_count: number;
  dimension_summaries: EvaluationDimensionSummary[];
  question_stats: EvaluationQuestionStat[];
}

interface EvaluationTeacherTrendPoint {
  batch_id: number;
  template_name: string;
  semester_name?: string | null;
  overall_avg_score: number;
  response_count: number;
  rank?: number | null;
  import_time: string;
}

interface EvaluationTeacherTrend {
  teacher_id: number;
  teacher_name: string;
  points: EvaluationTeacherTrendPoint[];
}

interface RuleVersion {
  id: number;
  name: string;
  semester_id?: number | null;
  semester_name?: string | null;
  is_default: boolean;
  status: string;
  note?: string | null;
  is_active: boolean;
}

interface RuleItem {
  id?: number;
  rule_version_id?: number;
  item_name: string;
  item_type: string;
  default_score: number;
  requires_attachment: boolean;
  note?: string | null;
  sort_order: number;
  is_active: boolean;
}

interface QuantAttachment {
  id: number;
  stored_file_id: number;
  file: UploadedAttachment;
}

interface QuantRecord {
  id: number;
  teacher_id: number;
  teacher_name?: string | null;
  class_id?: number | null;
  class_name?: string | null;
  semester_id: number;
  semester_name?: string | null;
  rule_version_id: number;
  rule_version_name?: string | null;
  rule_item_id: number;
  item_name: string;
  item_type: string;
  record_month: string;
  score: number;
  requires_attachment: boolean;
  description?: string | null;
  recorded_at: string;
  attachments: QuantAttachment[];
}

interface QuantSummary {
  teacher_id: number;
  teacher_name: string;
  semester_id: number;
  semester_name?: string | null;
  rule_version_id?: number | null;
  rule_version_name?: string | null;
  total_score: number;
  positive_score: number;
  negative_score: number;
  record_count: number;
  class_names: string[];
  category_scores_json?: Record<string, number> | null;
}

const referenceStore = useReferenceStore();
const activeTab = ref("evaluation");

const templates = ref<EvaluationTemplate[]>([]);
const teacherOptions = ref<TeacherOption[]>([]);
const batches = ref<EvaluationBatch[]>([]);
const evaluationOverview = ref<EvaluationOverview | null>(null);
const evaluationComparison = ref<EvaluationBatchCompare | null>(null);
const evaluationDetail = ref<EvaluationTeacherDetail | null>(null);
const evaluationTeacherTrend = ref<EvaluationTeacherTrend | null>(null);
const evaluationImportResult = ref<EvaluationImportResponse | null>(null);

const ruleVersions = ref<RuleVersion[]>([]);
const ruleItemRows = ref<RuleItem[]>([]);
const quantRecords = ref<QuantRecord[]>([]);
const quantSummary = ref<QuantSummary[]>([]);

const selectedRuleVersionId = ref<number | null>(null);
const selectedBatchId = ref<number | null>(null);
const selectedCompareBatchId = ref<number | null>(null);
const selectedEvaluationTeacherId = ref<number | null>(null);

const templateDialogVisible = ref(false);
const ruleVersionDialogVisible = ref(false);
const quantDialogVisible = ref(false);

const editingTemplateId = ref<number | null>(null);
const editingRuleVersionId = ref<number | null>(null);
const editingQuantRecordId = ref<number | null>(null);

const savingTemplate = ref(false);
const savingRuleVersion = ref(false);
const savingRuleItems = ref(false);
const savingQuant = ref(false);
const quantAttachmentInputRef = ref<HTMLInputElement | null>(null);

const evaluationImportForm = reactive({
  template_id: undefined as number | undefined,
  semester_id: undefined as number | undefined,
});

const quantFilters = reactive({
  semester_id: undefined as number | undefined,
  teacher_id: undefined as number | undefined,
  rule_version_id: undefined as number | undefined,
});

const templateForm = reactive({
  name: "",
  target_type: "teacher",
});

const templateQuestions = ref<EvaluationQuestion[]>([]);

const ruleVersionForm = reactive({
  name: "",
  semester_id: undefined as number | undefined,
  is_default: false,
  status: "active",
  note: "",
  is_active: true,
});

const quantForm = reactive({
  teacher_id: undefined as number | undefined,
  class_id: undefined as number | undefined,
  semester_id: undefined as number | undefined,
  rule_item_id: undefined as number | undefined,
  record_month: "",
  score: undefined as number | undefined,
  description: "",
  attachments: [] as UploadedAttachment[],
});

const templateDialogTitle = computed(() => (editingTemplateId.value ? "编辑评教模板" : "新增评教模板"));
const ruleVersionDialogTitle = computed(() => (editingRuleVersionId.value ? "编辑规则版本" : "新增规则版本"));
const quantDialogTitle = computed(() => (editingQuantRecordId.value ? "编辑量化记录" : "新增量化记录"));

const quantRuleItemOptions = computed(() => ruleItemRows.value.filter((item) => item.id));
const selectedBatchMeta = computed(() => batches.value.find((item) => item.id === selectedBatchId.value) ?? null);
const selectedRuleVersionMeta = computed(
  () => ruleVersions.value.find((item) => item.id === selectedRuleVersionId.value) ?? null,
);
const compareBatchOptions = computed(() => {
  const currentBatch = selectedBatchMeta.value;
  return batches.value.filter(
    (item) => item.id !== selectedBatchId.value && (!currentBatch || item.template_id === currentBatch.template_id),
  );
});

const trendDeltaScore = computed(() => {
  const points = evaluationTeacherTrend.value?.points ?? [];
  if (points.length < 2) return null;
  return Number((points[points.length - 1].overall_avg_score - points[points.length - 2].overall_avg_score).toFixed(2));
});

const trendRankDelta = computed(() => {
  const points = evaluationTeacherTrend.value?.points ?? [];
  if (points.length < 2) return null;
  const currentRank = points[points.length - 1].rank;
  const previousRank = points[points.length - 2].rank;
  if (!currentRank || !previousRank) return null;
  return previousRank - currentRank;
});

const trendPeakScore = computed(() => {
  const points = evaluationTeacherTrend.value?.points ?? [];
  if (!points.length) return "-";
  return Math.max(...points.map((item) => item.overall_avg_score)).toFixed(2);
});

function semesterLabel(item: OptionItem): string {
  return item.academic_year_name ? `${item.academic_year_name} ${item.name}` : item.name;
}

function formatWeight(value?: Record<string, number> | null): string {
  if (!value || !Object.keys(value).length) return "-";
  return Object.entries(value)
    .map(([key, score]) => `${key}:${score}`)
    .join(" / ");
}

function formatSignedValue(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) return "-";
  const normalized = Number(value.toFixed(digits));
  if (normalized > 0) return `+${normalized}`;
  return String(normalized);
}

function formatRankDelta(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  if (value > 0) return `提升 ${value}`;
  if (value < 0) return `下降 ${Math.abs(value)}`;
  return "持平";
}

function deltaClass(value: number | null | undefined): string {
  if (value === null || value === undefined) return "comparison-flat";
  if (value > 0) return "comparison-up";
  if (value < 0) return "comparison-down";
  return "comparison-flat";
}

function buildTemplateWeightJson(): Record<string, number> | null {
  const bucket: Record<string, number> = {};
  for (const row of templateQuestions.value) {
    if (!row.dimension_name) continue;
    bucket[row.dimension_name] = Number(((bucket[row.dimension_name] ?? 0) + (row.weight ?? 0)).toFixed(2));
  }
  return Object.keys(bucket).length ? bucket : null;
}

function downloadEvaluationTemplate(): void {
  openFile(`/api/system/files?path=${encodeURIComponent("data/templates/evaluation_import_template.xlsx")}`);
}

function downloadQuantTemplate(): void {
  openFile(`/api/system/files?path=${encodeURIComponent("data/templates/adviser_quant_import_template.xlsx")}`);
}

function addTemplateQuestionRow(): void {
  templateQuestions.value.push({
    dimension_name: "",
    question_text: "",
    score_max: 5,
    weight: 1,
    sort_order: templateQuestions.value.length + 1,
    is_active: true,
  });
}

function removeTemplateQuestionRow(index: number): void {
  templateQuestions.value.splice(index, 1);
}

function resetTemplateForm(): void {
  editingTemplateId.value = null;
  templateForm.name = "";
  templateForm.target_type = "teacher";
  templateQuestions.value = [
    {
      dimension_name: "教学设计",
      question_text: "教学目标清晰，重难点明确",
      score_max: 5,
      weight: 1,
      sort_order: 1,
      is_active: true,
    },
  ];
}

function openCreateTemplate(): void {
  resetTemplateForm();
  templateDialogVisible.value = true;
}

function openEditTemplate(item: EvaluationTemplate): void {
  editingTemplateId.value = item.id;
  templateForm.name = item.name;
  templateForm.target_type = item.target_type;
  templateQuestions.value = item.questions.map((question) => ({ ...question }));
  templateDialogVisible.value = true;
}

async function saveTemplate(): Promise<void> {
  if (!templateForm.name.trim()) {
    ElMessage.warning("模板名称不能为空");
    return;
  }
  if (
    !templateQuestions.value.length
    || templateQuestions.value.some((item) => !item.dimension_name.trim() || !item.question_text.trim())
  ) {
    ElMessage.warning("请至少保留一条完整题目，且维度与题目不能为空");
    return;
  }
  try {
    savingTemplate.value = true;
    const payload = {
      name: templateForm.name,
      target_type: templateForm.target_type,
      is_active: true,
      weight_json: buildTemplateWeightJson(),
      questions: templateQuestions.value.map((item) => ({
        dimension_name: item.dimension_name,
        question_text: item.question_text,
        score_max: item.score_max,
        weight: item.weight,
        sort_order: item.sort_order,
        is_active: true,
      })),
    };
    const path = editingTemplateId.value
      ? `/api/evaluation/templates/${editingTemplateId.value}`
      : "/api/evaluation/templates";
    const method = editingTemplateId.value ? "PUT" : "POST";
    await apiRequest(path, { method, body: JSON.stringify(payload) });
    templateDialogVisible.value = false;
    await loadTemplates();
    ElMessage.success("评教模板已保存");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingTemplate.value = false;
  }
}

async function loadTemplates(): Promise<void> {
  templates.value = await apiRequest<EvaluationTemplate[]>("/api/evaluation/templates");
  if (!evaluationImportForm.template_id && templates.value.length) {
    evaluationImportForm.template_id = templates.value[0].id;
  }
}

async function loadBatches(): Promise<void> {
  const query = new URLSearchParams();
  if (evaluationImportForm.semester_id) query.set("semester_id", String(evaluationImportForm.semester_id));
  batches.value = await apiRequest<EvaluationBatch[]>(`/api/evaluation/batches?${query.toString()}`);
}

async function handleEvaluationImport(file: UploadFile): Promise<void> {
  if (!file.raw || !evaluationImportForm.template_id || !evaluationImportForm.semester_id) {
    ElMessage.warning("请先选择模板和学期");
    return;
  }
  try {
    evaluationImportResult.value = await uploadFile<EvaluationImportResponse>("/api/evaluation/import", file.raw, {
      template_id: String(evaluationImportForm.template_id),
      semester_id: String(evaluationImportForm.semester_id),
    });
    await loadBatches();
    await selectBatch(evaluationImportResult.value.batch_id);
    ElMessage.success(evaluationImportResult.value.message);
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

async function selectBatch(batchId: number): Promise<void> {
  selectedBatchId.value = batchId;
  selectedCompareBatchId.value = null;
  evaluationComparison.value = null;
  evaluationOverview.value = await apiRequest<EvaluationOverview>(`/api/evaluation/batches/${batchId}/overview`);
  const firstTeacher = evaluationOverview.value.teacher_summaries[0];
  if (firstTeacher) {
    await loadTeacherDetail(firstTeacher.teacher_id);
  } else {
    evaluationDetail.value = null;
    evaluationTeacherTrend.value = null;
  }
  const defaultCompareBatch = compareBatchOptions.value[0];
  if (defaultCompareBatch) {
    await loadEvaluationComparison(defaultCompareBatch.id);
  }
}

async function loadTeacherDetail(teacherId: number): Promise<void> {
  if (!selectedBatchId.value) return;
  selectedEvaluationTeacherId.value = teacherId;
  const templateId = selectedBatchMeta.value?.template_id;
  const [detail, trend] = await Promise.all([
    apiRequest<EvaluationTeacherDetail>(`/api/evaluation/batches/${selectedBatchId.value}/teachers/${teacherId}`),
    apiRequest<EvaluationTeacherTrend>(
      `/api/evaluation/teachers/${teacherId}/trend${templateId ? `?template_id=${templateId}` : ""}`,
    ),
  ]);
  evaluationDetail.value = detail;
  evaluationTeacherTrend.value = trend;
}

async function loadEvaluationComparison(compareBatchId: number | null): Promise<void> {
  if (!selectedBatchId.value || !compareBatchId) {
    evaluationComparison.value = null;
    return;
  }
  selectedCompareBatchId.value = compareBatchId;
  evaluationComparison.value = await apiRequest<EvaluationBatchCompare>(
    `/api/evaluation/batches/${selectedBatchId.value}/compare?compare_batch_id=${compareBatchId}`,
  );
}

async function handleCompareBatchChange(value: number | string | undefined | null): Promise<void> {
  await loadEvaluationComparison(value ? Number(value) : null);
}

function resetRuleVersionForm(): void {
  editingRuleVersionId.value = null;
  ruleVersionForm.name = "";
  ruleVersionForm.semester_id = quantFilters.semester_id ?? evaluationImportForm.semester_id;
  ruleVersionForm.is_default = false;
  ruleVersionForm.status = "active";
  ruleVersionForm.note = "";
  ruleVersionForm.is_active = true;
}

function openCreateRuleVersion(): void {
  resetRuleVersionForm();
  ruleVersionDialogVisible.value = true;
}

async function saveRuleVersion(): Promise<void> {
  if (!ruleVersionForm.name.trim()) {
    ElMessage.warning("规则版本名称不能为空");
    return;
  }
  try {
    savingRuleVersion.value = true;
    const path = editingRuleVersionId.value
      ? `/api/adviser-quant/rules/${editingRuleVersionId.value}`
      : "/api/adviser-quant/rules";
    const method = editingRuleVersionId.value ? "PUT" : "POST";
    const result = await apiRequest<RuleVersion>(path, {
      method,
      body: JSON.stringify(ruleVersionForm),
    });
    ruleVersionDialogVisible.value = false;
    await loadRuleVersions();
    await selectRuleVersion(result.id);
    ElMessage.success("规则版本已保存");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingRuleVersion.value = false;
  }
}

async function loadRuleVersions(): Promise<void> {
  ruleVersions.value = await apiRequest<RuleVersion[]>("/api/adviser-quant/rules");
  if (!selectedRuleVersionId.value && ruleVersions.value.length) {
    await selectRuleVersion(ruleVersions.value[0].id);
  }
  if (!quantFilters.rule_version_id) {
    const defaultRule = ruleVersions.value.find((item) => item.is_default) ?? ruleVersions.value[0];
    quantFilters.rule_version_id = defaultRule?.id;
  }
}

async function selectRuleVersion(ruleVersionId: number): Promise<void> {
  selectedRuleVersionId.value = ruleVersionId;
  ruleItemRows.value = await apiRequest<RuleItem[]>(`/api/adviser-quant/rules/${ruleVersionId}/items`);
}

function addRuleItemRow(): void {
  ruleItemRows.value.push({
    item_name: "",
    item_type: "",
    default_score: 0,
    requires_attachment: false,
    sort_order: ruleItemRows.value.length + 1,
    is_active: true,
  });
}

function removeRuleItemRow(index: number): void {
  ruleItemRows.value.splice(index, 1);
}

async function saveRuleItems(): Promise<void> {
  if (!selectedRuleVersionId.value) {
    ElMessage.warning("请先选择一个规则版本");
    return;
  }
  if (!ruleItemRows.value.length) {
    ElMessage.warning("请至少保留一条规则项");
    return;
  }
  if (ruleItemRows.value.some((item) => !item.item_name.trim() || !item.item_type.trim())) {
    ElMessage.warning("规则项名称和类型不能为空");
    return;
  }
  try {
    savingRuleItems.value = true;
    ruleItemRows.value = await apiRequest<RuleItem[]>(`/api/adviser-quant/rules/${selectedRuleVersionId.value}/items`, {
      method: "POST",
      body: JSON.stringify(
        ruleItemRows.value.map((item) => ({
          item_name: item.item_name,
          item_type: item.item_type,
          default_score: item.default_score,
          requires_attachment: item.requires_attachment,
          note: item.note,
          sort_order: item.sort_order,
          is_active: true,
        })),
      ),
    });
    ElMessage.success("规则项已保存");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingRuleItems.value = false;
  }
}

function resetQuantForm(): void {
  editingQuantRecordId.value = null;
  quantForm.teacher_id = undefined;
  quantForm.class_id = undefined;
  quantForm.semester_id = quantFilters.semester_id ?? evaluationImportForm.semester_id;
  quantForm.rule_item_id = undefined;
  quantForm.record_month = currentMonthValue();
  quantForm.score = undefined;
  quantForm.description = "";
  quantForm.attachments = [];
}

function openCreateQuantRecord(): void {
  if (!selectedRuleVersionId.value) {
    ElMessage.warning("请先选择一个规则版本");
    return;
  }
  if (!quantRuleItemOptions.value.length) {
    ElMessage.warning("请先为当前规则版本配置规则项");
    return;
  }
  resetQuantForm();
  quantDialogVisible.value = true;
}

function openEditQuantRecord(item: QuantRecord): void {
  editingQuantRecordId.value = item.id;
  quantForm.teacher_id = item.teacher_id;
  quantForm.class_id = item.class_id ?? undefined;
  quantForm.semester_id = item.semester_id;
  quantForm.rule_item_id = item.rule_item_id;
  quantForm.record_month = item.record_month;
  quantForm.score = item.score;
  quantForm.description = item.description ?? "";
  quantForm.attachments = item.attachments.map((attachment) => attachment.file);
  quantDialogVisible.value = true;
}

function handleTemplateDialogClosed(): void {
  resetTemplateForm();
}

function handleRuleVersionDialogClosed(): void {
  resetRuleVersionForm();
}

function handleQuantDialogClosed(): void {
  resetQuantForm();
  if (quantAttachmentInputRef.value) {
    quantAttachmentInputRef.value.value = "";
  }
}

async function handleQuantAttachmentUpload(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  if (!files.length) return;
  try {
    const uploaded = await Promise.all(
      files.map((file) => uploadFile<UploadedAttachment>("/api/files/upload", file, { category: "adviser_quant" })),
    );
    quantForm.attachments.push(...uploaded);
    ElMessage.success(`已上传 ${uploaded.length} 个附件`);
    if (input) input.value = "";
  } catch (error) {
    ElMessage.error((error as Error).message);
  }
}

function removeQuantAttachment(fileId: number): void {
  quantForm.attachments = quantForm.attachments.filter((item) => item.id !== fileId);
}

async function saveQuantRecord(): Promise<void> {
  if (!quantForm.teacher_id || !quantForm.semester_id || !quantForm.rule_item_id || !quantForm.record_month) {
    ElMessage.warning("教师、学期、量化项和月份不能为空");
    return;
  }
  if (quantForm.score === undefined || quantForm.score === null) {
    ElMessage.warning("请填写量化分值");
    return;
  }
  try {
    savingQuant.value = true;
    const path = editingQuantRecordId.value
      ? `/api/adviser-quant/records/${editingQuantRecordId.value}`
      : "/api/adviser-quant/records";
    const method = editingQuantRecordId.value ? "PUT" : "POST";
    await apiRequest(path, {
      method,
      body: JSON.stringify({
        teacher_id: quantForm.teacher_id,
        class_id: quantForm.class_id,
        semester_id: quantForm.semester_id,
        rule_item_id: quantForm.rule_item_id,
        record_month: quantForm.record_month,
        score: quantForm.score,
        description: quantForm.description || undefined,
        attachment_file_ids: quantForm.attachments.map((item) => item.id),
        is_active: true,
      }),
    });
    quantDialogVisible.value = false;
    await reloadQuantData();
    ElMessage.success("量化记录已保存");
  } catch (error) {
    ElMessage.error((error as Error).message);
  } finally {
    savingQuant.value = false;
  }
}

async function loadQuantRecords(): Promise<void> {
  const query = new URLSearchParams();
  if (quantFilters.semester_id) query.set("semester_id", String(quantFilters.semester_id));
  if (quantFilters.teacher_id) query.set("teacher_id", String(quantFilters.teacher_id));
  quantRecords.value = await apiRequest<QuantRecord[]>(`/api/adviser-quant/records?${query.toString()}`);
  if (quantFilters.rule_version_id) {
    quantRecords.value = quantRecords.value.filter((item) => item.rule_version_id === quantFilters.rule_version_id);
  }
}

async function loadQuantSummary(): Promise<void> {
  if (!quantFilters.semester_id) {
    quantSummary.value = [];
    return;
  }
  const query = new URLSearchParams({ semester_id: String(quantFilters.semester_id) });
  if (quantFilters.teacher_id) query.set("teacher_id", String(quantFilters.teacher_id));
  if (quantFilters.rule_version_id) query.set("rule_version_id", String(quantFilters.rule_version_id));
  quantSummary.value = await apiRequest<QuantSummary[]>(`/api/adviser-quant/summary?${query.toString()}`);
}

async function reloadQuantData(): Promise<void> {
  await Promise.all([loadQuantRecords(), loadQuantSummary()]);
}

function resetQuantFilters(): void {
  quantFilters.teacher_id = undefined;
  quantFilters.rule_version_id = ruleVersions.value.find((item) => item.is_default)?.id ?? ruleVersions.value[0]?.id;
  quantFilters.semester_id = evaluationImportForm.semester_id;
  void reloadQuantData();
}

function currentMonthValue(): string {
  return new Date().toISOString().slice(0, 7);
}

async function loadTeacherOptions(): Promise<void> {
  const payload = await apiRequest<{ items: TeacherOption[] }>("/api/teachers?page=1&page_size=200");
  teacherOptions.value = payload.items;
}

onMounted(async () => {
  try {
    await referenceStore.loadCore();
    const currentSemester = referenceStore.semesters.find((item) => item.is_current) ?? referenceStore.semesters[0];
    evaluationImportForm.semester_id = currentSemester?.id;
    quantFilters.semester_id = currentSemester?.id;
    await Promise.all([loadTeacherOptions(), loadTemplates(), loadRuleVersions()]);
    await Promise.all([loadBatches(), reloadQuantData()]);
    if (batches.value.length) {
      await selectBatch(batches.value[0].id);
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

.panel-block,
.stat-card {
  padding: 18px 20px;
}

.metric-label {
  color: #61778b;
  font-size: 13px;
}

.metric-value {
  margin-top: 10px;
  font-size: 30px;
  font-weight: 760;
  color: #21374b;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-head.compact {
  margin-bottom: 12px;
}

.section-head h3,
.section-head h4 {
  margin: 0;
}

.section-head p {
  margin: 6px 0 0;
  color: #647a8f;
  line-height: 1.6;
}

.result-alert {
  margin-top: 16px;
}

.compact-metrics {
  margin-bottom: 16px;
}

.compare-toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(247, 251, 254, 0.92);
  border: 1px solid rgba(117, 134, 152, 0.14);
}

.compare-toolbar h4 {
  margin: 0;
  color: #22384c;
}

.compare-toolbar p {
  margin: 6px 0 0;
  color: #657b8f;
  line-height: 1.6;
}

.compare-selector {
  width: min(320px, 100%);
}

.comparison-metric-grid,
.trend-metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.trend-panel {
  margin-bottom: 16px;
  padding: 18px;
  border-radius: 20px;
  background: rgba(246, 250, 253, 0.9);
  border: 1px solid rgba(116, 133, 151, 0.12);
}

.comparison-up {
  color: #1d7b4d;
}

.comparison-down {
  color: #ba5c43;
}

.comparison-flat {
  color: #72869a;
}

.detail-grid-box {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.quant-shell {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 16px;
}

.inner-card {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(116, 133, 151, 0.14);
  background: rgba(248, 252, 255, 0.92);
}

.inner-card h4 {
  margin: 0 0 12px;
  font-size: 16px;
  color: #22384b;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.span-two {
  grid-column: span 2;
}

.toolbar-row {
  margin-bottom: 16px;
}

.file-input {
  width: 100%;
  padding: 12px 14px;
  border: 1px dashed rgba(114, 132, 150, 0.36);
  border-radius: 16px;
  background: rgba(248, 252, 255, 0.7);
}

.attachment-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.hint-text {
  color: #7c8f9f;
  font-size: 13px;
}

@media (max-width: 1080px) {
  .detail-grid-box,
  .quant-shell,
  .comparison-metric-grid,
  .trend-metric-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .span-two {
    grid-column: span 1;
  }

  .section-head,
  .compare-toolbar {
    flex-direction: column;
  }

  .compare-selector {
    width: 100%;
  }
}
</style>
