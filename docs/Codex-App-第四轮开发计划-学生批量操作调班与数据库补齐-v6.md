# Codex App 第四轮开发计划：学生管理批量操作、批量调班与数据库补齐

版本：v6  
适用仓库：`gaoboguang/Academic-Affairs-System`  
主开发环境：macOS / Codex App / 本地仓库  
上传方式：用户通过 GitHub Desktop 手动上传，Codex 不执行 `git push`  
本轮定位：在第三轮“山东升学方案中心 + 多路径规则引擎”完成后，继续补强本地教务系统的基础学生管理能力和数据底座。

---

## 0. 给 Codex 的最高优先级说明

你是本项目的开发代理。用户本人不懂编程，不能替你判断技术细节。你需要直接读取仓库、理解当前代码、修改代码、运行测试、提交本地 commit，并用中文汇报。

本轮开发不要依赖旧聊天窗口。开始任何任务前，必须先读取：

```text
README.md
AGENTS.md
memory-bank/handoff.md
memory-bank/active-context.md
docs/round3-shandong-pathway-final-report.md
docs/round3-shandong-pathway-user-guide.md
docs/round3-shandong-pathway-rules.md
docs/round2-gaokao-recommendation-final-report.md
docs/gaokao-data-coverage-after-round2.md
```

本轮必须遵守：

```text
1. 不执行 git push。
2. 不要求用户手动改代码。
3. 不把资格初筛包装成录取概率。
4. 不伪造官方高考数据。
5. 不做无保护的物理删除。
6. 不大范围重构已通过验收的高考志愿、升学路径和报表模块。
7. 所有批量操作必须有预检、确认、审计、可追溯记录。
8. 修改完成后必须运行与任务相关的测试。
9. 完成后用中文说明改了什么、涉及哪些文件、运行了哪些命令、是否通过、下一步怎么办。
```

---

## 1. 当前仓库真实状态摘要

第三轮已经进入 `main`，项目已经具备以下能力：

```text
官方来源登记
升学路径字典
学生升学画像
三态规则评估
路径卡片
材料缺口
普通类推荐入口
打印 / Excel 路径规划报告
```

当前系统已有 `/gaokao-pathways` 升学方案中心，并能处理山东生源地学生的多路径初筛，包括普通类常规批、普通类提前批 A/B、普通类特殊类型批、春季高考、高职单招、高职综评、艺术类、体育类、体育单招和高水平运动队。

第三轮最终验收中已经通过：

```text
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
npm run check
npm run check:all
git diff --check
```

第三轮仍保留 6 条 P0 数据缺口：

```text
1. 特殊类型已有招生计划但缺专门录取结果。
2. 山东招生计划 2024 年数量偏少。
3. 一分一段缺少 2020、2021、2022。
4. 省控线 / 批次线缺少 2020、2021、2022。
5. 政策参考数量偏少。
6. 招生章程限制链仍有大量待人工复核。
```

本轮开发要在这个基础上继续推进，不要回头重做第二轮和第三轮已经完成的功能。

---

## 2. 本轮核心目标

本轮目标分为三个主线。

### 主线 A：学生批量删除

用户反馈：学生信息界面没有找到批量删除学生的按钮。需要增加一个安全可控的批量删除功能。

成熟教务系统一般不会直接物理删除学生，而是采用：

```text
选择学生
批量操作
删除预检
显示影响范围
二次确认
软删除 / 停用
写入操作日志
保留恢复或审计依据
```

本项目应采用“软删除优先”的方式，不允许直接把学生及其成绩、成长档案、推荐记录、升学画像、附件等数据物理删除。

### 主线 B：学生批量调班与调班历史

用户希望增加批量调班功能，并且调班历史要能在学生成长档案中展示。

成熟学籍系统通常把调班视为“学籍/班级流转事件”，而不是简单覆盖学生当前班级。正确做法是：

```text
创建调班批次
记录来源班级和目标班级
记录生效日期
记录调班原因
记录操作人和操作时间
更新学生当前班级
保留历史流转记录
在学生详情和成长档案时间线展示
```

本轮需要实现批量调班，并把调班历史作为系统事件展示到学生成长档案或学生详情时间线中。

### 主线 C：数据库补齐

用户希望“数据库里的信息一次补齐”。这里需要分清楚：

```text
可以一次补齐的：已有官方来源、可下载、可解析、可追溯的数据。
不能伪造补齐的：官方尚未发布、需要人工核验、需要学校内部真实数据的数据。
```

本轮要做的是“数据库补齐框架 + 可补数据的一次性补齐 + 不可补数据的缺口登记”。尤其要继续补：

```text
2020-2022 山东一分一段
2020-2022 山东省控线 / 批次线
2023 山东招生计划缺口
2024 山东招生计划偏少问题
2025 招生计划完整性复核
2026 已公开政策、单招/综评、路径规则、计划限额、后续正式计划发布状态
山东政策参考
高校章程限制链待复核项
```

---

## 3. 本轮不做什么

```text
1. 不做全国省份。
2. 不做公开商业平台。
3. 不做在线爬虫长期监控。
4. 不绕过官方来源。
5. 不把 2026 未发布数据伪造成已导入。
6. 不把单招、综评、春考、艺体、体育、提前批、特殊类型输出为录取概率。
7. 不把校内考试年级名次直接当作山东全省位次。
8. 不做无法审计的数据批量覆盖。
9. 不删除第三轮已经完成的升学路径体系。
```

---

## 4. 成熟方案借鉴原则

### 4.1 学生批量删除

参考成熟教务 / CRM / LMS 系统的做法，本项目应采用：

```text
批量选择 -> 预检 -> 影响清单 -> 二次确认 -> 软删除 -> 审计记录 -> 可查询历史
```

删除前要显示：

```text
学生数量
涉及班级
是否有成绩
是否有成长档案
是否有附件
是否有升学画像
是否有推荐 / 志愿草稿
是否有关联调班记录
是否有关联报表或导入批次
```

不建议提供“强制物理删除”。如果必须保留物理删除入口，也只能作为系统管理员隐藏功能，并且本轮不实现。

### 4.2 批量调班

参考成熟学籍系统，本项目应采用：

```text
批次号
调出班级
调入班级
生效日期
调班原因
备注
操作人
操作时间
每个学生独立调班结果
```

同一个调班批次内，某些学生可以成功，某些学生可以被阻断。必须显示失败原因。

常见阻断条件：

```text
学生不存在
学生已删除 / 已停用
目标班级不存在
目标班级已停用
学生已经在目标班级
跨年级调班但未确认
目标班级学年学期不匹配
```

### 4.3 成长档案展示调班历史

不要把调班历史只存在数据库里。老师打开学生成长档案时，应能看到类似：

```text
2026-04-25 班级调整：高二 1 班 -> 高二 3 班
原因：文理方向调整
操作：批量调班
备注：按年级统一调班方案执行
```

实现方式建议：

```text
权威记录：student_class_transfer 或 student_class_transfer_item
展示来源：成长档案时间线聚合该记录
可选：生成 system 类型成长事件，但不要把它当作老师手写成长记录
```

优先推荐“成长档案时间线聚合调班记录”，因为这样不会把系统事件和人工成长记录混在一张表里。如果现有成长档案已经有系统事件机制，可以复用。

### 4.4 数据库补齐

成熟数据平台通常采用：

```text
source_document 来源登记
import_run 导入批次
file_sha256 文件校验
parser_version 解析器版本
coverage_matrix 覆盖矩阵
data_health 健康检查
gap_register 缺口登记
manual_review 人工复核状态
```

当前项目已经有官方来源登记和导入运行表。本轮必须复用这些能力，不要另起炉灶。

---

## 5. 建议数据库模型

Codex 必须先检查现有模型，能复用就复用。下面是建议，不是强制新建。

### 5.1 学生批量删除

建议新增或复用：

```text
student_bulk_operation_batch
student_bulk_operation_item
```

字段建议：

```text
student_bulk_operation_batch
- id
- operation_type: bulk_delete / bulk_restore / bulk_transfer
- status: pending / success / partially_failed / failed
- requested_count
- success_count
- failed_count
- reason
- confirm_text
- operator_name / operator_id
- created_at
- finished_at
- note
- is_active

student_bulk_operation_item
- id
- batch_id
- student_id
- student_no_snapshot
- student_name_snapshot
- source_class_id_snapshot
- source_class_name_snapshot
- target_class_id_snapshot
- target_class_name_snapshot
- status
- error_message
- warning_json
- before_snapshot_json
- after_snapshot_json
- created_at
```

如果已有 import job 或 audit log 框架可复用，也可以不新建批次表，但必须保证批量操作可追溯。

### 5.2 学生调班

建议新增：

```text
student_class_transfer_batch
student_class_transfer_item
```

或者与上面的批量操作表合并。更清晰的做法是调班单独建表：

```text
student_class_transfer_batch
- id
- source_class_id nullable
- target_class_id
- target_grade_id
- effective_on
- reason
- note
- status
- requested_count
- success_count
- failed_count
- operator
- created_at
- finished_at

student_class_transfer_item
- id
- batch_id
- student_id
- from_class_id
- from_class_name_snapshot
- to_class_id
- to_class_name_snapshot
- before_snapshot_json
- after_snapshot_json
- status
- error_message
- created_at
```

如果项目已有“学籍历史”表，应优先把调班写入既有学籍历史；如果没有，则新建调班历史表，并在学生详情中展示。

### 5.3 成长档案聚合

建议后端提供统一时间线接口，或扩展已有成长档案接口：

```text
GET /api/students/{student_id}/growth-timeline
```

返回内容包含：

```text
人工成长记录
附件记录
班级调动记录
学籍变更记录
升学画像重要变更
```

如果现有成长档案页面已经有接口，则直接扩展现有接口，不要新增重复页面。

---

## 6. API 设计建议

### 6.1 批量删除

```text
POST /api/students/bulk-delete/preview
POST /api/students/bulk-delete
```

#### preview payload

```json
{
  "student_ids": [1, 2, 3],
  "mode": "soft_delete",
  "reason": "误导入重复学生"
}
```

#### preview response

```json
{
  "total": 3,
  "deletable_count": 2,
  "blocked_count": 1,
  "warnings": [
    {
      "student_id": 1,
      "student_name": "张三",
      "score_count": 12,
      "growth_record_count": 3,
      "attachment_count": 1,
      "recommendation_count": 2,
      "pathway_profile_count": 1,
      "message": "该学生有关联成绩和升学画像，删除后仅停用主档，不清除历史数据。"
    }
  ],
  "blocked": [
    {
      "student_id": 3,
      "reason": "学生不存在或已删除"
    }
  ],
  "confirm_token": "..."
}
```

#### execute payload

```json
{
  "student_ids": [1, 2, 3],
  "mode": "soft_delete",
  "reason": "误导入重复学生",
  "confirm_token": "...",
  "confirm_text": "确认删除 3 名学生"
}
```

### 6.2 批量调班

```text
POST /api/students/class-transfer/preview
POST /api/students/class-transfer
GET /api/students/{student_id}/class-transfer-history
```

#### preview payload

```json
{
  "student_ids": [1, 2, 3],
  "target_class_id": 8,
  "effective_on": "2026-04-25",
  "reason": "文理方向调整",
  "note": "高二年级统一调班"
}
```

#### execute payload

```json
{
  "student_ids": [1, 2, 3],
  "target_class_id": 8,
  "effective_on": "2026-04-25",
  "reason": "文理方向调整",
  "note": "高二年级统一调班",
  "confirm_token": "...",
  "confirm_text": "确认调班 3 名学生"
}
```

### 6.3 数据补齐

建议新增命令：

```bash
npm run backend:gaokao-data-complete
```

或在现有脚本下新增子命令：

```bash
npm run backend:gaokao-import-official
npm run backend:gaokao-import-shandong-core
npm run backend:data-health -- --json
```

如果要新增统一补齐命令，必须支持：

```text
--dry-run
--years 2020 2021 2022 2023 2024 2025 2026
--source-types score_rank_segment score_line admission_plan policy chapter
--download
--no-download
--json
```

---

## 7. 前端页面设计

### 7.1 学生列表页

在学生信息 / 学生中心列表中增加：

```text
表格多选框
批量操作按钮
批量删除
批量调班
```

批量删除弹窗必须包括：

```text
已选学生数量
影响范围预检
不可删除 / 已阻断学生
有关联数据的提示
删除原因输入
二次确认输入
```

批量调班弹窗必须包括：

```text
已选学生数量
目标班级选择
生效日期
调班原因
备注
预检结果
确认执行
```

### 7.2 学生详情页

增加或补强：

```text
当前班级
班级历史
调班记录
升学画像入口
成长档案入口
```

### 7.3 成长档案页

在时间线中展示调班历史：

```text
系统事件：班级调整
调出班级
调入班级
生效日期
调班原因
操作批次
备注
```

可筛选类型：

```text
全部
成长记录
附件
班级调整
学籍变化
升学画像
```

### 7.4 高考数据页

继续展示数据库补齐结果：

```text
2020-2026 覆盖矩阵
最近三年核心数据
2026 发布状态
官方来源登记
导入批次
P0 缺口
人工复核队列
```

---

## 8. 本轮窗口分工

建议不要一次开太多。推荐顺序：

```text
先开 E0、E1、E3、E5
再开 E2、E4、E6
最后开 E7、E8
```

其中：

```text
E0：第四轮基线审计
E1：学生批量删除后端
E2：学生批量删除前端
E3：批量调班后端与历史记录
E4：批量调班前端与成长档案展示
E5：数据库补齐审计与数据源计划
E6：数据库补齐导入执行
E7：数据健康、报表和使用说明
E8：最终集成、测试、交接
```

---

# 9. Codex 窗口提示词

下面每个窗口都可以直接复制给 Codex App。

---

## 窗口 E0：第四轮基线审计

### 分支名

```text
codex/r4-e0-baseline-audit
```

### 提示词

```text
你是 Codex，本窗口是第四轮开发的基线审计窗口。

重要要求：
1. 不执行 git push。
2. 不开发新功能。
3. 不改动业务代码，除非只是补审计文档。
4. 用户通过 GitHub Desktop 手动上传。
5. 用户不懂编程，请用中文汇报。

请先阅读：
- README.md
- AGENTS.md
- memory-bank/handoff.md
- memory-bank/active-context.md
- docs/round3-shandong-pathway-final-report.md
- docs/round3-shandong-pathway-user-guide.md
- docs/round3-shandong-pathway-rules.md
- docs/round2-gaokao-recommendation-final-report.md
- docs/gaokao-data-coverage-after-round2.md

然后重点审计：
1. 学生列表页是否已有批量选择、批量删除、批量调班能力。
2. 后端学生接口是否已有单个删除、软删除、学籍历史或班级历史能力。
3. 学生详情页是否已有学籍历史、成长档案、升学画像。
4. 成长档案接口是否可聚合系统事件。
5. 当前数据库补齐缺口，尤其是：
   - 2020-2022 一分一段
   - 2020-2022 省控线
   - 2023 招生计划
   - 2024 招生计划偏少
   - 政策参考数量偏少
   - 章程限制链待复核
6. 第三轮升学路径功能是否已经在 main 中稳定。

请生成：
- docs/round4-baseline-audit.md

文档必须包含：
- 当前真实文件路径
- 已有能力
- 缺失能力
- 本轮建议修改范围
- 不建议修改的模块
- 后续窗口 E1-E8 的依赖关系
- 推荐测试命令

最后运行：
git status
npm run backend:data-health -- --json
git diff --check

完成后中文汇报。
```

### 验收标准

```text
docs/round4-baseline-audit.md 已生成
没有误改业务代码
git diff --check 通过
清楚列出 E1-E8 的真实代码入口
```

---

## 窗口 E1：学生批量删除后端

### 分支名

```text
codex/r4-e1-student-bulk-delete-backend
```

### 提示词

```text
你是 Codex，本窗口负责实现学生批量删除后端。

重要要求：
1. 不执行 git push。
2. 不做物理删除。
3. 不清空学生成绩、成长档案、附件、推荐记录、升学画像。
4. 删除采用软删除 / 停用主档。
5. 批量删除必须有预检、二次确认、审计记录。
6. 不大改学生模块现有结构。

请先阅读 E0 审计文档：
- docs/round4-baseline-audit.md

然后读取真实代码入口，通常包括但不限于：
- apps/backend/app/api/routes/students.py
- apps/backend/app/services/students.py
- apps/backend/app/repositories/students.py
- apps/backend/app/models/
- apps/backend/app/schemas/
- apps/backend/tests/

任务：
1. 检查现有学生删除逻辑。
2. 如果已有单个删除，复用其软删除策略。
3. 新增批量删除预检接口：
   POST /api/students/bulk-delete/preview
4. 新增批量删除执行接口：
   POST /api/students/bulk-delete
5. 预检必须统计每个学生的关联数据：
   - 成绩
   - 成长档案
   - 附件
   - 学籍 / 班级历史
   - 推荐记录
   - 志愿草稿
   - 升学画像
   - 路径评估
6. 执行时必须：
   - 校验 confirm_token 或等价确认机制
   - 写入操作日志
   - 返回成功 / 失败 / 被阻断学生清单
   - 不删除关联历史数据
7. 如需要新增批量操作表，请新增 Alembic 迁移。
8. 补后端测试。

建议接口返回中文可读提示，方便前端直接展示。

运行：
npm run backend:migrate
npm run backend:test -- apps/backend/tests -q
git diff --check

完成后中文汇报：
- 新增了哪些接口
- 是否软删除
- 影响了哪些文件
- 测试是否通过
- 前端 E2 需要如何调用
```

### 验收标准

```text
批量删除 preview 可用
批量删除 execute 可用
不会物理删除学生历史数据
后端测试通过
```

---

## 窗口 E2：学生批量删除前端

### 分支名

```text
codex/r4-e2-student-bulk-delete-frontend
```

### 提示词

```text
你是 Codex，本窗口负责学生批量删除前端。

重要要求：
1. 不执行 git push。
2. 不改后端，除非只是对接字段名小修。
3. 不做无确认删除。
4. 用户不懂编程，界面文案必须清楚。

请先阅读：
- docs/round4-baseline-audit.md
- E1 的中文汇报或相关 commit
- 学生列表页面代码

任务：
1. 在学生列表页增加多选功能。
2. 增加“批量操作”按钮。
3. 增加“批量删除学生”功能。
4. 删除前先调用后端 preview。
5. 弹窗展示：
   - 选中学生数量
   - 可删除数量
   - 被阻断数量
   - 每个学生的关联数据风险
   - 删除后保留历史数据的说明
6. 必须要求输入确认文字，例如：
   确认删除 X 名学生
7. 删除成功后刷新列表。
8. 如果部分失败，显示失败原因。
9. 增加前端单测或组件测试。
10. 不要影响学生详情、升学画像和成长档案页面。

运行：
npm run frontend:test
npm run frontend:build
git diff --check

完成后中文汇报。
```

### 验收标准

```text
学生列表可多选
可批量删除
删除前有预检
删除前有二次确认
删除后刷新
前端测试和构建通过
```

---

## 窗口 E3：批量调班后端与历史记录

### 分支名

```text
codex/r4-e3-student-bulk-class-transfer-backend
```

### 提示词

```text
你是 Codex，本窗口负责批量调班后端和班级历史记录。

重要要求：
1. 不执行 git push。
2. 不直接覆盖学生班级而不留历史。
3. 调班必须有批次、明细、生效日期、原因、来源班级、目标班级。
4. 调班历史必须能被学生详情和成长档案读取。
5. 不大改已有学生、班级、成长档案结构。

请先阅读：
- docs/round4-baseline-audit.md
- 当前学生模型、班级模型、学籍历史、成长档案相关代码

任务：
1. 检查是否已有学籍历史 / 班级历史表。
2. 如果已有，优先复用。
3. 如果没有，新增：
   - student_class_transfer_batch
   - student_class_transfer_item
4. 新增批量调班预检接口：
   POST /api/students/class-transfer/preview
5. 新增批量调班执行接口：
   POST /api/students/class-transfer
6. 新增学生调班历史接口：
   GET /api/students/{student_id}/class-transfer-history
7. 调班执行必须：
   - 记录 from_class / to_class
   - 更新学生当前班级
   - 记录生效日期
   - 记录原因和备注
   - 写审计日志
   - 返回逐学生结果
8. 补后端测试：
   - 正常批量调班
   - 学生已在目标班级
   - 目标班级不存在
   - 调班后历史可查
   - 学生当前班级被更新

运行：
npm run backend:migrate
npm run backend:test -- apps/backend/tests -q
git diff --check

完成后中文汇报。
```

### 验收标准

```text
批量调班预检可用
批量调班执行可用
学生当前班级会更新
调班历史会保存
后端测试通过
```

---

## 窗口 E4：批量调班前端与成长档案展示

### 分支名

```text
codex/r4-e4-class-transfer-frontend-growth-archive
```

### 提示词

```text
你是 Codex，本窗口负责批量调班前端和成长档案展示。

重要要求：
1. 不执行 git push。
2. 不重复实现后端逻辑。
3. 不把调班记录伪装成人工成长记录。
4. 调班历史应作为系统事件展示。

请先阅读：
- docs/round4-baseline-audit.md
- E3 的中文汇报或相关 commit
- 学生列表页
- 学生详情页
- 成长档案页 / 成长档案组件

任务：
1. 学生列表页增加“批量调班”入口。
2. 弹窗支持：
   - 选择目标班级
   - 选择生效日期
   - 输入调班原因
   - 输入备注
   - 调用预检接口
   - 展示可调班 / 被阻断 / 风险提示
   - 二次确认后执行
3. 执行成功后刷新学生列表。
4. 学生详情页展示班级历史 / 调班历史。
5. 成长档案时间线展示调班系统事件。
6. 调班事件文案示例：
   2026-04-25 班级调整：高二 1 班 -> 高二 3 班，原因：文理方向调整。
7. 增加筛选或标签：
   - 全部
   - 成长记录
   - 班级调整
8. 补前端测试。

运行：
npm run frontend:test
npm run frontend:build
git diff --check

完成后中文汇报。
```

### 验收标准

```text
学生列表可批量调班
学生详情可看到调班历史
成长档案可看到调班系统事件
测试和构建通过
```

---

## 窗口 E5：数据库补齐审计与数据源计划

### 分支名

```text
codex/r4-e5-data-completion-audit-plan
```

### 提示词

```text
你是 Codex，本窗口负责数据库补齐审计和数据源计划。

重要要求：
1. 不执行 git push。
2. 不伪造数据。
3. 不把未发布数据写成已导入。
4. 不直接替换 data/app.db。
5. 所有可补数据必须有官方来源登记、文件校验和导入批次。
6. 本窗口以审计和计划为主，可补少量脚本，但不要大规模导入。

请先阅读：
- docs/round3-shandong-pathway-final-report.md
- docs/round2-gaokao-recommendation-final-report.md
- docs/gaokao-data-coverage-after-round2.md
- apps/backend/app/services/gaokao_imports.py
- apps/backend/app/services/gaokao_official_importers.py
- apps/backend/app/utils/data_health.py
- scripts/import_gaokao_official.py
- scripts/import_shandong_gaokao_core_data.py
- scripts/manage_gaokao_sources.py

任务：
1. 运行或读取 data-health，确认当前缺口。
2. 生成数据库补齐计划：
   - 2020-2022 一分一段
   - 2020-2022 省控线
   - 2023 招生计划
   - 2024 招生计划完整性
   - 2025 招生计划完整性
   - 2026 已公开政策 / 单招综评 / 路径规则
   - 2026 普通类正式计划：如果官方未发布，只登记待发布
   - 政策参考
   - 招生章程限制链
3. 对每一项标记：
   - 可自动导入
   - 需人工下载
   - 需人工复核
   - 官方未发布
   - 本轮不适用
4. 生成：
   - docs/round4-data-completion-plan.md
   - docs/round4-official-source-checklist.md
5. 如需要，补充 source registry seed，但不要伪造文件。
6. 设计下一窗口 E6 的导入任务清单。

运行：
npm run backend:data-health -- --json
git diff --check

完成后中文汇报。
```

### 验收标准

```text
补齐计划清晰
每个数据缺口都有处理方式
没有伪造数据
E6 可以按计划执行导入
```

---

## 窗口 E6：数据库补齐导入执行

### 分支名

```text
codex/r4-e6-data-completion-imports
```

### 提示词

```text
你是 Codex，本窗口负责按 E5 计划执行数据库补齐导入。

重要要求：
1. 不执行 git push。
2. 不伪造官方数据。
3. 不跳过 source_document 和 import_run。
4. 不直接覆盖主库，导入前必须备份。
5. 如果官方文件无法自动下载，登记为 manual_required，不要硬编假数据。
6. 用户通过 GitHub Desktop 手动上传。

请先阅读：
- docs/round4-data-completion-plan.md
- docs/round4-official-source-checklist.md
- 当前 gaokao import 相关脚本

任务：
1. 对可自动导入的数据执行导入。
2. 对需人工下载的数据，生成清晰说明：
   - 文件名
   - 应放置目录
   - 对应 source_document
   - 导入命令
3. 优先补：
   - 2020-2022 一分一段
   - 2020-2022 省控线
   - 2023 招生计划
   - 2024 招生计划完整性
4. 导入后更新覆盖报告：
   - docs/round4-data-completion-result.md
5. data-health 必须能展示补齐前后变化。
6. 如果某些数据无法补齐，必须明确说明原因：
   - 官方未发布
   - 页面无法访问
   - 文件需人工下载
   - 字段无法解析
   - 需人工复核

运行：
npm run backend:migrate
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
npm run backend:test -- apps/backend/tests -q
git diff --check

完成后中文汇报。
```

### 验收标准

```text
可补数据已导入或登记
不可补数据已记录原因
data-health 有补齐前后结果
不伪造任何数据
```

---

## 窗口 E7：数据健康、报表和使用说明

### 分支名

```text
codex/r4-e7-data-health-reports-docs
```

### 提示词

```text
你是 Codex，本窗口负责数据健康展示、报表和使用说明。

重要要求：
1. 不执行 git push。
2. 不新增复杂业务算法。
3. 不改变 E6 的数据导入逻辑。
4. 重点让非程序员看懂数据库是否补齐、还差什么。

请先阅读：
- docs/round4-data-completion-plan.md
- docs/round4-data-completion-result.md
- apps/backend/app/utils/data_health.py
- apps/frontend/src/pages/GaokaoDataPage.vue
- docs/round3-shandong-pathway-user-guide.md

任务：
1. 高考数据页继续增强：
   - 2020-2026 年份覆盖矩阵
   - 一分一段覆盖
   - 省控线覆盖
   - 招生计划覆盖
   - 政策参考覆盖
   - 章程复核进度
2. 增加“数据库补齐结果说明”区域。
3. 增加或完善导出：
   - 数据覆盖报告 Excel 或可打印页面
4. 文档：
   - docs/round4-user-guide-student-bulk-actions.md
   - docs/round4-user-guide-data-completion.md
5. 文案要适合非程序员：
   - 已补齐
   - 部分补齐
   - 官方未发布
   - 需人工下载
   - 需人工复核

运行：
npm run frontend:test
npm run frontend:build
npm run backend:data-health -- --json
git diff --check

完成后中文汇报。
```

### 验收标准

```text
数据补齐状态可视化
文档清楚
前端构建通过
用户能看懂还差什么
```

---

## 窗口 E8：第四轮最终集成、测试、交接

### 分支名

```text
codex/r4-e8-final-integration
```

### 提示词

```text
你是 Codex，本窗口负责第四轮最终集成、测试和交接。

重要要求：
1. 不执行 git push。
2. 不继续新增功能。
3. 不跳过失败测试。
4. 不只写总结，必须检查代码状态。
5. 用户通过 GitHub Desktop 手动上传。

请整合和检查 E0-E7 的成果。

重点确认：
1. 学生批量删除是否安全可用。
2. 批量调班是否安全可用。
3. 调班历史是否进入学生详情和成长档案。
4. 数据库补齐是否完成可补部分。
5. 不可补数据是否明确标记原因。
6. 第三轮升学方案中心是否未被破坏。
7. 山东普通类冲稳保推荐是否未被破坏。
8. 所有新功能是否有中文说明和测试。

请运行：
git status
npm run backend:migrate
npm run backend:data-health -- --json
npm run backend:p0-check -- --json
npm run check
npm run check:all
git diff --check

生成：
- docs/round4-final-acceptance-report.md

更新：
- memory-bank/active-context.md
- memory-bank/handoff.md
- memory-bank/progress.md
- docs/README.md

最终报告必须包含：
- 本轮完成内容
- 批量删除能力说明
- 批量调班能力说明
- 成长档案展示说明
- 数据库补齐结果
- 仍未补齐原因
- 测试结果
- 是否可以进入下一轮
- 用户用 GitHub Desktop 上传的提醒

完成后中文汇报：
1. 当前分支
2. 最新 commit hash
3. 是否可以合并 main
4. 所有测试是否通过
5. 是否需要用户用 GitHub Desktop 上传
```

### 验收标准

```text
最终报告完成
memory-bank 更新
check:all 通过
工作区干净
不执行 git push
```

---

## 10. 本轮合并建议

用户使用 GitHub Desktop 手动上传，因此 Codex 不需要也不允许 `git push`。

建议流程：

```text
E0 完成
↓
E1 + E3 + E5
↓
E2 + E4 + E6
↓
E7
↓
E8
↓
用户用 GitHub Desktop 合并到 main 并上传
↓
让我重新扫描 GitHub main
```

合并前用户可以让 Codex 执行：

```bash
git status
npm run check:all
npm run backend:p0-check -- --json
git diff --check
```

合并后 main 再执行：

```bash
npm run backend:data-health -- --json
npm run check:all
```

---

## 11. 本轮完成后的理想状态

### 学生管理

```text
学生列表支持多选
支持批量删除
删除前有预检
删除时是软删除
删除后有关联数据说明
操作可审计
```

### 学生调班

```text
学生列表支持批量调班
调班前有预检
调班后学生当前班级更新
调班批次和明细可查
学生详情显示班级历史
成长档案显示班级调整系统事件
```

### 数据库

```text
2020-2022 一分一段尽量补齐
2020-2022 省控线尽量补齐
2023 招生计划缺口有处理
2024 招生计划偏少有处理
2025 招生计划完整性有复核
2026 已公开内容有登记
官方未发布内容不伪造
政策参考和章程复核继续推进
data-health 能看出补齐前后变化
```

### 文档

```text
round4-baseline-audit.md
round4-data-completion-plan.md
round4-data-completion-result.md
round4-user-guide-student-bulk-actions.md
round4-user-guide-data-completion.md
round4-final-acceptance-report.md
memory-bank/handoff.md 已更新
```

---

## 12. 重要提醒

本轮用户最关心的是：

```text
批量删除学生
批量调班
调班历史能在成长档案看到
数据库尽量一次补齐
```

开发时不要被高考志愿算法继续吸走全部精力。高考数据库补齐很重要，但学生基础管理能力同样是本轮核心。

如果时间或冲突导致任务无法全部完成，优先级如下：

```text
P0：批量调班后端 + 历史记录
P0：批量调班前端 + 成长档案展示
P0：批量删除安全软删除
P0：数据库补齐计划和可补项导入
P1：数据健康页面增强
P1：批量操作文档
P2：更多数据源自动下载
P2：更复杂的章程自动解析
```

---

## 13. 给用户的固定回复模板

如果 Codex 问用户技术问题，用户可以直接复制：

```text
我不懂编程，请你根据当前仓库真实代码和最佳实践自行判断。只要不违背以下原则即可：
1. 不执行 git push；
2. 不物理删除学生历史数据；
3. 批量操作必须可预检、可确认、可审计；
4. 调班必须保留历史，并能在成长档案看到；
5. 数据不能伪造，官方未发布就标记为待发布；
6. 完成后运行测试并用中文汇报。
```

如果 Codex 只写方案不开发，用户可以复制：

```text
请不要只写方案。请直接读取仓库、修改代码、运行测试并提交本地 commit。完成后用中文告诉我改了什么、测试是否通过。不要执行 git push。
```

如果 Codex 让用户手动处理错误，用户可以复制：

```text
我不懂编程，请你自己分析错误原因并修复。如果确实无法修复，请用中文说明具体原因、影响范围和下一步该让哪个窗口处理。
```
