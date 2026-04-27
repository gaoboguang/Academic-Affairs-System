# Codex App 第三轮开发执行文档：山东升学方案库与多路径规则引擎 v5

> 项目：`gaoboguang/Academic-Affairs-System` / 本地教务工具  
> 开发环境：Mac 本机为主  
> 开发方式：继续交给 Codex App 执行  
> GitHub 上传方式：用户使用 GitHub Desktop 手动上传，Codex 不要执行 `git push`  
> 当前轮次目标：在第二轮“山东普通类冲稳保推荐”基础上，补齐山东生源地多升学方式、规则、要求、数据结构和可解释推荐入口。

---

## 0. 给 Codex 的最高优先级指令

你是本项目的全权开发执行者。用户不具备编程基础，所以你不能把技术判断、合并冲突、测试失败、依赖安装等问题丢给用户处理。你需要自己读取仓库、判断现状、修改代码、运行测试、提交本地 commit，并用中文给用户汇报。

本轮有一个特殊要求：

**不要执行 `git push`。**

用户会通过 GitHub Desktop 手动上传。你完成每个窗口任务后，只需要做到：

1. 本地分支开发完成；
2. 本地 commit 完成；
3. `git status` 干净；
4. 测试命令通过；
5. 用中文提醒用户：“请用 GitHub Desktop 上传本分支或 main”。

禁止事项：

- 不要执行 `git push`。
- 不要要求用户手动改代码。
- 不要伪造 2026 未公开数据。
- 不要把特殊类型、单招、综评、艺体、春考包装成完整录取概率。
- 不要把校内考试年级名次直接当成山东全省位次。
- 不要爬取或复制商业志愿填报平台的数据库。
- 不要大范围重构已有推荐中心；本轮要小步扩展。
- 不要删除既有测试来制造通过结果。
- 不要改 `AGENTS.md`，除非明确确认它不是由规则同步工具生成，且必须说明原因。

---

## 1. 本轮开发背景

第二轮开发已经完成并推送到 GitHub 远程 `main`。当前远程 `main` 已包含山东高考志愿推荐相关能力，包括：

- 山东高考官方来源登记与导入框架；
- 2023、2024、2025 山东普通类投档表、一分一段、省控线导入；
- 2026 数据发布状态追踪；
- 学生高考成绩 / 位次预估快照；
- 山东普通类“冲 / 稳 / 保 / 仅关注”推荐引擎；
- `/recommendations` 中的“山东普通类推荐”工作台；
- 推荐结果打印页和 Excel 导出；
- 数据健康检查增强；
- 第二轮最终报告和交接记忆。

第二轮报告显示当前已经形成：

```text
官方来源登记 -> 最近三年核心数据导入 -> 数据健康看板 -> 学生分数/位次预估 -> 山东普通类冲稳保预览 -> 页面展示 -> 打印和 Excel 输出
```

但是当前仍然存在重要边界：

1. 当前主要做好了“山东普通类常规批”推荐。
2. 升学方式太少。
3. 2026 普通类正式招生计划、一分一段、省控线仍需等待官方发布后导入。
4. 2023 招生计划缺失、2024 招生计划偏少。
5. 政策参考仍偏少。
6. 招生章程限制链仍有大量待人工复核。
7. 校内考试估算缺少本校历届高考校准表，只能作为低 / 中置信预估。
8. 特殊类型仍只能做资格初筛，不能作为完整录取判断。

第三轮不是推倒重做，而是在现有基础上继续扩展：

```text
从“一个山东普通类推荐工具”
升级为
“山东生源地多升学路径规划工具”
```

---

## 2. 本轮总目标

本轮目标是搭建“山东升学方案库”和“多路径规则引擎”。

要解决的问题：

1. 学生除了普通类常规批，还有哪些可考虑升学路径？
2. 每条升学路径需要满足什么报名条件、分数条件、选科条件、身份条件、体检条件、专业类别条件、章程条件？
3. 当前学生适合哪些路径，不适合哪些路径，缺什么材料？
4. 每条路径能不能推荐院校？如果不能，为什么不能？
5. 当前数据是否足够？不足时应该显示什么风险？
6. 未来 2026 官方数据发布后，应该如何增量导入和更新推荐？

本轮最终应该形成：

- 一个“山东升学方案中心”页面；
- 一套后端升学路径数据模型；
- 一套规则引擎：硬性门槛、软性风险、人工复核；
- 一套学生升学画像；
- 一套升学路径卡片；
- 普通类推荐进一步加固；
- 单招、综评、春考、艺体、体育、提前批、专项等路径的规则框架；
- 每条路径的“能推荐 / 只能初筛 / 需人工核验 / 当前不适用”状态；
- 打印和导出一份学生升学路径建议报告。

---

## 3. 成熟方案借鉴原则

可以参考成熟高考志愿产品的常见做法，但只能借鉴产品思路，不能复制商业数据。

可借鉴的成熟做法：

1. **多路径入口**  
   不只做普通类常规批，还要把提前批、专项、综合评价、单招、春考、艺体、体育等路径做成可选择的“路径卡”。

2. **用户画像优先**  
   成熟系统一般不会只问分数，而会收集生源地、选科、成绩、位次、体检、兴趣、专业偏好、地域偏好、家庭约束、是否接受民办 / 中外合作 / 专科 / 单招等信息。

3. **规则先行**  
   不是所有路径都能用分数位次推荐。很多路径先看资格、报名时间、专业类别、体检、章程、面试、校测、综合素质评价。系统必须先判断“是否具备资格”。

4. **位次优先，分数辅助**  
   山东普通类推荐继续以位次为核心，不跨年直接比较裸分。

5. **风险显式化**  
   推荐结果必须说明为什么是冲 / 稳 / 保，缺哪些数据，哪些要求必须人工核验。

6. **志愿表模拟**  
   普通类常规批后续应支持模拟 96 个“专业（专业类）+学校”志愿，但本轮可以先做“路径建议 + 候选池 + 风险解释”，不要一次性做复杂保存系统。

7. **来源追溯**  
   每条政策、计划、投档线、分数线、选科要求都要能追溯来源，不要只在代码里硬编码。

8. **人工复核闭环**  
   成熟系统也不能完全替代招生章程核验。系统要有“待人工核验 / 已人工核验 / 不适用”的状态。

本项目的边界：

- 只做自用；
- 只做山东生源地；
- 优先服务本地学校内部规划；
- 不做公开商业平台；
- 不承诺录取概率；
- 不把系统建议当成最终填报结论。

---

## 4. 本轮需要新增或增强的升学方式

当前系统重点在山东普通类常规批。本轮要增加“升学方式”体系，但不同路径的推荐深度不同。

### 4.1 普通类常规批

当前已有，是主链路。继续加固。

支持能力：

- 手动预估分；
- 手动全省位次；
- 学生校内考试估算；
- 2023-2025 历史投档位次；
- 冲 / 稳 / 保 / 仅关注；
- 选科要求过滤；
- 数据风险提示；
- 打印和 Excel。

下一步增强：

- 统一分数换位次逻辑；
- 加强选科规则解析；
- 提示 2026 正式计划未发布或未导入；
- 为 96 志愿模拟做基础结构；
- 增加“本科 / 专科 / 民办 / 中外合作 / 省内 / 省外 / 专业优先 / 学校优先”等偏好。

### 4.2 普通类提前批 A 类

包括但不限于：

- 军事类；
- 公安政法类；
- 飞行技术；
- 航海类；
- 消防救援；
- 综合评价；
- 高水平运动队；
- 定向培养军士生等。

本轮目标不是给完整录取概率，而是做资格筛查和路径提醒。

需要规则：

- 是否需要政审；
- 是否需要体检；
- 是否需要面试 / 体能测试；
- 是否有性别、年龄、应届、身体条件要求；
- 是否学校志愿模式；
- 是否专业服从调剂；
- 是否需要提前报名或校测；
- 是否需要查看招生章程。

输出状态：

```text
适合关注 / 可能适合但缺材料 / 不建议 / 当前无法判断
```

### 4.3 普通类提前批 B 类

包括但不限于：

- 国家公费师范生；
- 省属公费生；
- 部分高校马克思主义理论专业；
- 紧缺涉农试点专业等。

需要规则：

- 是否达到相应分数线；
- 是否接受定向就业或服务年限；
- 是否接受就业地区限制；
- 志愿数量规则；
- 专业（专业类）+学校模式；
- 是否需签约；
- 是否需提前了解就业约束。

本轮输出：路径卡 + 规则说明 + 风险提示。

### 4.4 普通类特殊类型批

包括：

- 教育部高校专项计划；
- 其他需资格审核的特殊类型。

注意：不要把所有特殊类型都混成一种。强基计划、高校专项、高水平运动队、综合评价等流程不同。

需要规则：

- 是否达到特殊类型招生控制线；
- 是否具有对应资格；
- 志愿必须与资格高校一致；
- 是否已完成前置报名；
- 是否存在高校测试或资格名单；
- 当前学生是否有资格材料。

本轮目标：资格提醒，不做完整概率预测。

### 4.5 春季高考

山东春季高考路径需要独立于夏季普通类。

需要规则：

- 学生是否为春季高考考生；
- 专业类别是否一致；
- 本科 / 专科批次；
- 技能拔尖人才规则；
- 春季高考类别分数线；
- 专业类别不能混报；
- 若缺专门录取结果，只能初筛。

本轮目标：建立规则和路径卡，不要求立即完整推荐。

### 4.6 高职单独招生

2026 单独招生面向中职应届毕业生和社会人员等，不等同于夏季普通类常规批。

需要规则：

- 是否已参加山东 2026 普通高校招生考试报名；
- 是否为中职应届或社会人员；
- 社会人员是否有高中阶段毕业证书或同等学力；
- 报名时间；
- 文化素质考试；
- 专业技能测试；
- 退役士兵考生是否走素质测试或面试；
- 专业类别是否匹配；
- 招生章程是否已核验。

本轮目标：路径卡 + 报名提醒 + 规则说明 + 材料缺口。

### 4.7 高职综合评价招生

2026 高职综合评价招生面向普通高中应届毕业生。

需要规则：

- 是否为普通高中应届毕业生；
- 是否完成 2026 普通高校招生考试报名；
- 是否有综合素质评价信息；
- 是否需要素质测试或面试；
- 高中综合素质评价信息截止时间；
- 院校章程和测试方式；
- 是否普通类考生可考虑。

本轮目标：对普通高中学生显示此路径，给出“可关注 / 缺测试信息 / 需章程核验”。

### 4.8 艺术类

当前特殊类型只能初筛。本轮可以做路径卡和资格校验。

需要规则：

- 艺术类别；
- 统考 / 校考；
- 文化控制线；
- 专业成绩；
- 综合分规则；
- 不同院校录取原则不同；
- 身高、色觉、单科、语种等章程要求；
- 与普通类、体育类同批次不得兼报的边界。

本轮目标：不做完整概率预测，只做路径卡和人工复核清单。

### 4.9 体育类

需要规则：

- 体育专业成绩；
- 综合分；
- 体育类一段 / 二段；
- 体育类常规批；
- 与普通类、艺术类兼报限制；
- 高水平运动队和体育单招不要混淆。

本轮目标：路径卡 + 初筛 + 人工复核。

### 4.10 体育单招 / 高水平运动队

这是特殊路径，不是普通体育类常规批。

需要规则：

- 运动员等级；
- 专项报名系统；
- 院校招生简章；
- 文化考试 / 体育专项考试；
- 高水平运动队资格条件；
- 报名、资格审查和校测材料。

本轮目标：只做路径提醒和材料清单，不给录取概率。

---

## 5. 建议新增的数据模型

请 Codex 先检查现有模型，避免重复建表。如果已有近似表，优先扩展已有表。

### 5.1 `gaokao_pathway`

用于定义山东升学路径。

建议字段：

```text
id
province
pathway_code
pathway_name
pathway_group
student_type
exam_type
batch_name
volunteer_mode
max_volunteer_count
recommendation_depth
status
source_document_id
summary
risk_level
notes_json
created_at
updated_at
is_active
```

示例：

```text
summer_general_regular        普通类常规批
summer_general_early_a        普通类提前批A类
summer_general_early_b        普通类提前批B类
summer_special_type           普通类特殊类型批
spring_exam_undergrad         春季高考本科批
spring_exam_junior            春季高考专科批
vocational_single_exam        高职单独招生
vocational_comprehensive      高职综合评价招生
art_undergrad                 艺术类本科批
art_junior                    艺术类专科批
sports_regular                体育类常规批
sports_single_exam            体育单招
high_level_sports             高水平运动队
```

`recommendation_depth` 建议枚举：

```text
full_rank_recommendation      可以做位次型推荐
eligibility_screening         只能资格初筛
policy_notice                 只做政策提醒
manual_review_required        必须人工复核
not_supported                 当前不支持
```

### 5.2 `gaokao_pathway_rule`

用于存放路径规则。

建议字段：

```text
id
pathway_id
rule_code
rule_name
rule_type
severity
condition_json
message_template
source_document_id
manual_review_required
valid_from_year
valid_to_year
created_at
updated_at
is_active
```

`rule_type` 建议：

```text
hard_gate          硬门槛，不满足则不推荐
soft_warning       软风险，提示但不排除
material_required  材料要求
time_window        报名/考试/填报时间
score_line         分数线要求
subject_required   选科要求
category_match     专业类别要求
chapter_check      章程核验
manual_check       人工复核
```

### 5.3 `student_pathway_profile`

用于记录学生升学画像。

建议字段：

```text
id
student_id
province
candidate_type
exam_type
subject_combination
spring_exam_category
art_track
sports_track
has_gaokao_registration
is_fresh_graduate
is_vocational_student
is_social_candidate
has_high_school_equivalent
accept_private_college
accept_sino_foreign
accept_junior_college
accept_outside_province
accept_early_batch
accept_service_commitment
accept_interview_or_physical_test
career_preferences_json
region_preferences_json
family_constraints_json
known_body_limitations_json
materials_json
note
created_at
updated_at
is_active
```

说明：

- 这是本轮很关键的模型。
- 不能只靠学生表判断路径。
- 后续每条升学路径都应基于该画像进行资格筛查。

### 5.4 `student_pathway_evaluation`

用于保存某学生某路径的评估结果。

建议字段：

```text
id
student_id
pathway_id
target_year
status
status_label
score
confidence_level
matched_rules_json
failed_rules_json
warning_rules_json
missing_materials_json
recommendation_depth
summary
next_actions_json
created_at
updated_at
is_active
```

`status` 建议：

```text
suitable             适合关注
possible             可能适合
not_recommended      不建议
insufficient_data    信息不足
manual_review        需人工复核
not_applicable       当前不适用
```

### 5.5 `student_pathway_plan`

本轮可选。如果时间允许，用于保存学生规划方案。

建议字段：

```text
id
student_id
target_year
plan_name
primary_pathway_id
backup_pathway_ids_json
summary
risk_notes_json
created_at
updated_at
is_active
```

本轮若来不及，可以先不做持久化，只做预览和报告。

---

## 6. 后端核心能力设计

### 6.1 路径规则评估服务

新增或扩展服务：

```text
apps/backend/app/services/gaokao_pathways.py
apps/backend/app/services/_gaokao_pathway_rules.py
apps/backend/app/services/_gaokao_student_pathway_profile.py
```

建议提供函数：

```text
list_pathways(session, province="山东", target_year=2026)
get_student_pathway_profile(session, student_id)
upsert_student_pathway_profile(session, payload)
evaluate_student_pathways(session, student_id, target_year)
evaluate_single_pathway(session, student_id, pathway_id, target_year)
bootstrap_shandong_pathways(session, target_year=2026)
```

### 6.2 API 设计

建议新增：

```text
GET    /api/gaokao/pathways
POST   /api/gaokao/pathways/bootstrap-shandong
GET    /api/students/{student_id}/pathway-profile
PUT    /api/students/{student_id}/pathway-profile
POST   /api/students/{student_id}/pathway-evaluations/preview
POST   /api/students/{student_id}/pathway-plans
GET    /api/students/{student_id}/pathway-plans
```

或如果当前推荐相关路由更适合，也可以放到：

```text
/api/recommendations/pathways/*
```

Codex 需要根据现有路由风格判断，避免 API 命名混乱。

### 6.3 规则引擎要求

每条规则要有三类结果：

```text
passed
failed
unknown
```

不要只有 true / false，因为很多路径需要人工确认。

每条路径输出：

```json
{
  "pathway_code": "vocational_comprehensive",
  "pathway_name": "高职综合评价招生",
  "status": "possible",
  "recommendation_depth": "eligibility_screening",
  "matched_rules": [],
  "failed_rules": [],
  "warning_rules": [],
  "missing_materials": [],
  "next_actions": []
}
```

### 6.4 与山东普通类推荐的关系

当前山东普通类冲稳保推荐不要被废弃。

新的“升学方案中心”应该把普通类常规批作为其中一张主路径卡：

```text
普通类常规批
状态：可做完整位次推荐
入口：进入山东普通类推荐工作台
```

其他路径如果只能初筛，就显示：

```text
只能做资格初筛，不能给完整录取判断
```

---

## 7. 前端页面设计

### 7.1 新增页面：山东升学方案中心

建议路径：

```text
/gaokao-pathways
```

或集成到现有 `/recommendations` 的新页签：

```text
升学方案
```

如果现有推荐页已经很大，优先新增独立页面。

页面结构：

1. 学生选择区；
2. 学生升学画像表单；
3. 升学路径卡片区；
4. 路径详情抽屉；
5. 推荐入口区；
6. 材料缺口清单；
7. 下一步行动清单；
8. 打印 / 导出报告。

### 7.2 路径卡片内容

每张卡片至少显示：

```text
路径名称
适用对象
当前状态
推荐深度
关键要求
缺失材料
风险提示
下一步动作
是否可以进入推荐
```

示例：

```text
高职综合评价招生
状态：可能适合
适用对象：普通高中应届毕业生
推荐深度：资格初筛
缺失材料：综合素质评价信息、目标院校章程
下一步：确认是否参加 2026 高考报名；关注 2月25-27日选报；核验目标高校面试要求
```

### 7.3 学生升学画像表单

字段建议：

```text
生源地：山东
考生类型：普通类 / 春考 / 艺术 / 体育 / 中职 / 社会人员
是否应届
是否中职学生
是否社会人员
是否普通高中应届
是否已完成高考报名
选科组合
春考专业类别
艺术类别
体育专项
是否接受专科
是否接受民办
是否接受中外合作
是否接受省外
是否接受提前批
是否接受定向服务
是否接受面试/体测/政审
身体限制：色盲、色弱、身高、视力、体检结论等
家庭/地域偏好
职业方向偏好
备注
```

### 7.4 报告输出

新增报告：

```text
学生山东升学路径规划报告
```

内容：

1. 学生画像摘要；
2. 推荐路径排序；
3. 普通类冲稳保入口；
4. 单招 / 综评 / 春考 / 艺体 / 体育 / 提前批 / 专项路径状态；
5. 缺失材料清单；
6. 2026 数据发布状态；
7. 风险说明；
8. 人工复核项。

---

## 8. 本轮优先级

### P0：必须完成

1. 新建山东升学路径基础字典。
2. 新建或扩展学生升学画像。
3. 新建路径规则评估服务。
4. 新增升学方案中心页面或页签。
5. 普通类常规批接入路径卡。
6. 单招、综评、春考、艺体、体育、提前批、特殊类型至少能显示路径卡、要求、风险和材料缺口。
7. 明确哪些路径只能资格初筛，不能推荐录取概率。
8. 本地测试通过。
9. 本地 commit 完成。

### P1：强烈建议完成

1. 统一分数换位次逻辑。
2. 加强选科要求解析测试。
3. 增加学生路径规划报告打印 / Excel。
4. 将 2026 数据发布状态接入路径中心。
5. 给普通类推荐增加“进入路径中心”的互通入口。

### P2：后续再做

1. 完整 96 志愿自动编排。
2. 升学方案保存、对比、版本历史。
3. 本校历届高考校准模型。
4. 2026 普通类正式计划发布后的增量导入。
5. 章程限制链大规模人工复核工具。
6. 单招 / 综评院校分专业计划解析。

---

## 9. 多 Codex 窗口安排

本轮不要一次性开太多窗口。推荐节奏：

```text
第一批：D0、D1
第二批：D2、D3
第三批：D4、D5
第四批：D6、D7
最后：D8
```

### 窗口 D0：当前代码复核与第三轮基线锁定

分支名：

```text
codex/r3-d0-pathway-baseline-audit
```

任务：

1. 阅读：
   - `README.md`
   - `AGENTS.md`
   - `memory-bank/handoff.md`
   - `docs/round2-gaokao-recommendation-final-report.md`
   - `docs/gaokao-data-coverage-after-round2.md`
   - `apps/backend/app/services/_recommendations_shandong_rush_stable_safe.py`
   - `apps/backend/app/services/_recommendations_score_projection.py`
2. 确认第二轮山东普通类推荐现状。
3. 列出当前适合扩展升学路径的文件位置。
4. 写入：
   - `docs/round3-pathway-baseline-audit.md`
5. 不做业务大改。
6. 本地 commit。

提示词：

```text
你是 Codex 第三轮 D0 窗口：山东升学方案库基线审计。

请先不要开发大功能。请读取 README.md、AGENTS.md、memory-bank/handoff.md、docs/round2-gaokao-recommendation-final-report.md、docs/gaokao-data-coverage-after-round2.md，以及山东推荐相关后端/前端文件。

目标：基于当前真实仓库，写一份 docs/round3-pathway-baseline-audit.md，说明：
1. 第二轮已经完成了什么；
2. 当前普通类推荐的入口、服务、测试在哪里；
3. 当前数据库和 P0 缺口；
4. 本轮要扩展多升学路径时，哪些现有文件可以复用；
5. 哪些地方不能大改；
6. 下一步 D1-D8 各窗口应注意的冲突点。

要求：
- 不要执行 git push。
- 完成后本地 commit。
- 用中文汇报测试和 commit 信息，并提醒用户用 GitHub Desktop 上传。
```

验收命令：

```bash
git diff --check
npm run backend:data-health -- --json
```

---

### 窗口 D1：山东升学路径数据模型与规则引擎

分支名：

```text
codex/r3-d1-gaokao-pathway-schema-rule-engine
```

任务：

1. 新增或扩展数据模型：
   - `gaokao_pathway`
   - `gaokao_pathway_rule`
   - `student_pathway_profile`
   - `student_pathway_evaluation` 或等价结构
2. 新增 Alembic 迁移。
3. 新增 Pydantic schema。
4. 新增 service / repository。
5. 新增基础 API。
6. 新增后端测试。
7. 不改前端大页面。

提示词：

```text
你是 Codex 第三轮 D1 窗口：山东升学路径数据模型与规则引擎。

请基于当前仓库真实结构新增山东升学路径模型。不要推翻已有推荐中心，不要重构普通类推荐，只做数据模型和规则评估底座。

需要支持：
- 山东普通类常规批；
- 普通类提前批A类；
- 普通类提前批B类；
- 普通类特殊类型批；
- 春季高考本科/专科；
- 高职单独招生；
- 高职综合评价招生；
- 艺术类；
- 体育类；
- 体育单招 / 高水平运动队。

请新增或复用表：gaokao_pathway、gaokao_pathway_rule、student_pathway_profile、student_pathway_evaluation。规则引擎必须区分 passed / failed / unknown，不能只做 true / false。

要求：
1. 新增 Alembic 迁移；
2. 新增 schema；
3. 新增 service；
4. 新增 API；
5. 新增后端测试；
6. 不执行 git push；
7. 本地 commit。

完成后用中文汇报：改了哪些文件、迁移版本、测试结果、commit hash，并提醒用户用 GitHub Desktop 上传。
```

验收命令：

```bash
npm run backend:migrate
npm run backend:test -- apps/backend/tests -q
npm run backend:data-health -- --json
git diff --check
```

---

### 窗口 D2：山东升学路径官方规则字典与 bootstrap

分支名：

```text
codex/r3-d2-shandong-pathway-rule-bootstrap
```

任务：

1. 基于官方政策建立山东路径基础字典。
2. 做 `bootstrap_shandong_pathways` 脚本或 API。
3. 将路径规则以数据形式落库，而不是散落在前端。
4. 不做复杂推荐算法。
5. 记录官方来源。

需要覆盖：

- 普通类常规批；
- 普通类提前批 A / B；
- 普通类特殊类型批；
- 春季高考；
- 高职单独招生；
- 高职综合评价招生；
- 艺术类；
- 体育类；
- 体育单招 / 高水平运动队。

提示词：

```text
你是 Codex 第三轮 D2 窗口：山东升学路径官方规则字典与 bootstrap。

请在 D1 数据模型基础上，为山东 2026 建立升学路径基础字典和规则 bootstrap。所有规则必须可追溯来源，不能只写在前端页面里。

重点：
1. 普通类常规批：可做完整位次推荐；
2. 提前批A/B、特殊类型批：做资格提醒和人工复核；
3. 春季高考：强调专业类别一致；
4. 高职单招：强调中职/社会人员、报名、文化素质、专业技能测试；
5. 高职综评：强调普通高中应届、综合素质评价、素质测试或面试；
6. 艺体、体育：强调统考/综合分/文化线/章程要求；
7. 体育单招、高水平运动队：强调专项报名和资格审查。

要求：
- 不伪造政策；
- 缺官方数据时标记 pending_official_release 或 manual_review_required；
- 新增 docs/round3-shandong-pathway-rules.md；
- 新增测试；
- 不执行 git push；
- 本地 commit。
```

验收命令：

```bash
npm run backend:test -- apps/backend/tests -q
npm run backend:data-health -- --json
git diff --check
```

---

### 窗口 D3：学生升学画像与资格材料缺口

分支名：

```text
codex/r3-d3-student-pathway-profile
```

任务：

1. 新增学生升学画像接口。
2. 支持查看和更新学生画像。
3. 与学生详情或升学方案中心对接。
4. 画像字段用于规则引擎评估。
5. 输出缺失材料清单。

提示词：

```text
你是 Codex 第三轮 D3 窗口：学生升学画像与资格材料缺口。

请基于 D1 的 student_pathway_profile 模型，实现学生升学画像能力。用户不懂编程，所以页面文案必须清晰。

画像至少包含：
- 山东生源地；
- 考生类型；
- 选科组合；
- 是否普通高中应届；
- 是否中职学生；
- 是否社会人员；
- 是否已完成高考报名；
- 春考专业类别；
- 艺术/体育类别；
- 是否接受专科、民办、中外合作、省外、提前批、定向服务；
- 是否接受面试/体检/政审；
- 体检限制和材料备注。

要求：
1. 新增后端 API；
2. 新增或接入前端表单；
3. 和规则评估服务联动；
4. 新增测试；
5. 不执行 git push；
6. 本地 commit。
```

验收命令：

```bash
npm run backend:test -- apps/backend/tests -q
npm run frontend:test
npm run frontend:build
git diff --check
```

---

### 窗口 D4：山东升学方案中心页面

分支名：

```text
codex/r3-d4-gaokao-pathway-center-ui
```

任务：

1. 新增页面或推荐中心页签：山东升学方案中心。
2. 展示学生画像。
3. 展示升学路径卡片。
4. 展示适合 / 可能 / 不建议 / 信息不足 / 需人工复核状态。
5. 接入普通类推荐入口。
6. 显示 2026 数据发布状态和 P0 数据风险。

提示词：

```text
你是 Codex 第三轮 D4 窗口：山东升学方案中心前端。

请新增或接入一个“山东升学方案中心”页面。页面要面向非程序员用户，不能出现大量数据库术语。它应该帮助用户看到：这个学生有哪些升学路径可以关注、哪些路径不适合、哪些材料缺失、哪些规则必须人工核验。

页面至少包括：
1. 学生选择；
2. 学生升学画像摘要；
3. 升学路径卡片；
4. 路径详情抽屉；
5. 普通类常规批进入“山东普通类推荐”按钮；
6. 单招/综评/春考/艺体/体育/提前批等路径卡；
7. 数据风险说明；
8. 下一步行动清单。

要求：
- 文案清晰；
- 不夸大系统能力；
- 不能把初筛说成录取概率；
- 不执行 git push；
- 本地 commit。
```

验收命令：

```bash
npm run frontend:lint
npm run frontend:test
npm run frontend:build
git diff --check
```

---

### 窗口 D5：普通类推荐算法加固

分支名：

```text
codex/r3-d5-shandong-general-recommendation-hardening
```

任务：

1. 统一分数换位次逻辑。
2. 加强选科要求解析测试。
3. 明确 2026 正式计划缺失提示。
4. 加强校内考试估算风险提示。
5. 不大改现有工作台。

提示词：

```text
你是 Codex 第三轮 D5 窗口：山东普通类推荐算法加固。

请不要扩新路径，不要重构推荐中心。只针对当前山东普通类冲稳保推荐做小步加固：

1. 检查 _recommendations_score_projection.py 和 _recommendations_shandong_rush_stable_safe.py 是否各自实现了分数换位次逻辑。如果是，请统一复用更完整的逻辑，避免 province / score_type / subject_group 过滤不一致。
2. 补充选科要求解析测试：不限、不提科目要求、物理、物理 化学、物理或化学、物理和化学均须选考。
3. 检查 2026 正式计划缺失时，页面、打印、Excel 是否都明确提示“当前主要参考 2023-2025 历史投档数据，正式填报前需导入 2026 官方计划”。
4. 检查校内考试估算是否明确提示“不能等同山东全省位次”。

要求：
- 小步修复；
- 新增测试；
- 不执行 git push；
- 本地 commit。
```

验收命令：

```bash
npm run backend:test -- apps/backend/tests/test_shandong_rush_stable_safe_recommendation.py apps/backend/tests/test_gaokao_score_projection.py -q
npm run frontend:test -- tests/shandong-recommendation-workbench.test.ts
npm run frontend:build
git diff --check
```

---

### 窗口 D6：单招、综评、春考路径初筛

分支名：

```text
codex/r3-d6-vocational-spring-pathways
```

任务：

1. 高职单招路径规则。
2. 高职综合评价路径规则。
3. 春季高考本科 / 专科路径规则。
4. 对应前端路径卡。
5. 输出报名、材料、类别匹配、人工复核要求。
6. 不做录取概率。

提示词：

```text
你是 Codex 第三轮 D6 窗口：单招、综评、春考路径初筛。

请基于已建立的路径规则引擎，实现高职单独招生、高职综合评价招生、春季高考本科/专科的初筛路径。

要求：
1. 单招要区分中职应届、社会人员、退役士兵等规则；
2. 综评要强调普通高中应届、综合素质评价、素质测试或面试；
3. 春考要强调专业类别一致；
4. 缺少院校章程或分专业计划时必须显示“需人工核验”；
5. 不能输出录取概率；
6. 新增后端和前端测试；
7. 不执行 git push；
8. 本地 commit。
```

验收命令：

```bash
npm run backend:test -- apps/backend/tests -q
npm run frontend:test
npm run frontend:build
git diff --check
```

---

### 窗口 D7：艺体、体育、提前批、专项路径初筛

分支名：

```text
codex/r3-d7-special-early-art-sports-pathways
```

任务：

1. 艺术类路径卡。
2. 体育类路径卡。
3. 普通类提前批 A / B 路径卡。
4. 普通类特殊类型批路径卡。
5. 体育单招 / 高水平运动队路径卡。
6. 展示章程、体检、政审、面试、专项资格等人工复核项。

提示词：

```text
你是 Codex 第三轮 D7 窗口：艺体、体育、提前批、专项路径初筛。

请基于路径规则引擎扩展以下路径：
- 艺术类本科/专科；
- 体育类常规批；
- 普通类提前批A类；
- 普通类提前批B类；
- 普通类特殊类型批；
- 体育单招；
- 高水平运动队。

要求：
1. 只做资格初筛和规则说明，不做完整录取概率；
2. 必须显示章程、体检、政审、面试、专项资格、单科/语种/身高/视力等人工复核项；
3. 艺体、体育和普通类同批次兼报限制要做提示；
4. 不要把高水平运动队、体育单招、体育类常规批混为一类；
5. 新增测试；
6. 不执行 git push；
7. 本地 commit。
```

验收命令：

```bash
npm run backend:test -- apps/backend/tests -q
npm run frontend:test
npm run frontend:build
git diff --check
```

---

### 窗口 D8：第三轮最终集成、报告、交接

分支名：

```text
codex/r3-d8-final-pathway-integration
```

任务：

1. 整合 D0-D7 成果。
2. 检查冲突。
3. 跑全量测试。
4. 写最终报告。
5. 更新 memory-bank。
6. 本地 commit。
7. 不执行 git push。

提示词：

```text
你是 Codex 第三轮 D8 窗口：最终集成、验收和交接。

请整合第三轮 D0-D7 的成果，确认所有改动进入当前分支，处理冲突，运行完整验收。

需要生成：
1. docs/round3-shandong-pathway-final-report.md
2. docs/round3-shandong-pathway-user-guide.md
3. 更新 memory-bank/active-context.md
4. 更新 memory-bank/progress.md
5. 更新 memory-bank/handoff.md

验收必须执行：
- npm run backend:data-health -- --json
- npm run backend:p0-check -- --json
- npm run check
- npm run check:all
- git diff --check

注意：
- 不执行 git push；
- 合并到 main 后也不 push；
- 最后提醒用户用 GitHub Desktop 上传。

完成后用中文汇报：
1. 当前分支；
2. main 最新 commit；
3. 测试结果；
4. 已完成能力；
5. 仍然不能承诺的边界；
6. 是否可以用 GitHub Desktop 上传。
```

---

## 10. 开发完成后的用户操作

Codex 不负责上传 GitHub。

每个窗口完成后，Codex 应该告诉用户：

```text
本窗口已经本地 commit，工作区干净。请打开 GitHub Desktop，确认本分支变更，然后点击 Push origin / Publish branch 上传。
```

如果最终已经合并回 `main`，Codex 应该告诉用户：

```text
第三轮已合并到本地 main，测试通过。请使用 GitHub Desktop 上传 main 分支。
```

不要在 Codex 里执行：

```bash
git push
git push origin main
git push --force
```

---

## 11. 本轮验收标准

第三轮完成后，应达到：

1. 用户可以选择一个学生；
2. 系统可以维护该学生的升学画像；
3. 系统可以展示该学生的山东升学路径卡；
4. 普通类常规批可以进入现有冲稳保推荐；
5. 单招、综评、春考、艺体、体育、提前批、专项等路径可以做资格初筛；
6. 每条路径都能说明：为什么适合、为什么不适合、缺什么资料、下一步做什么；
7. 所有路径都能区分“可推荐 / 只能初筛 / 需人工核验 / 不适用”；
8. 系统不伪造 2026 未公开数据；
9. 系统不夸大录取概率；
10. 有后端测试、前端测试和构建验证；
11. 有最终报告和交接文档；
12. 用户通过 GitHub Desktop 手动上传。

---

## 12. 推荐给 Codex 的统一开头提示词

每个窗口开始都可以先复制这段：

```text
这是本地教务系统第三轮开发。用户不懂编程，请你直接负责读取仓库、判断代码、修改代码、运行测试、本地提交和中文汇报。

当前项目只自用，只做山东生源地，不做商业公开产品。本轮重点是扩展“山东升学方案库”和“多路径规则引擎”，在已有山东普通类冲稳保推荐基础上，增加单招、综评、春考、艺体、体育、提前批、特殊类型等升学路径的规则、要求、资格初筛和材料缺口提示。

重要限制：
1. 不要执行 git push，用户会用 GitHub Desktop 手动上传。
2. 不要伪造 2026 未公开数据。
3. 不要把资格初筛说成录取概率。
4. 不要把校内考试年级名次当成山东全省位次。
5. 不要大范围重构已有推荐中心。
6. 每次完成后必须运行相关测试，并本地 commit。
7. 最终用中文告诉用户：改了什么、测试是否通过、commit 是什么、是否可以用 GitHub Desktop 上传。
```

---

## 13. 官方规则参考资料

Codex 在执行规则字典和文案时，应优先参考官方来源。可以通过网页搜索确认最新版本，但不要把来源不可确认的信息硬编码成规则。

当前已知参考方向：

1. 山东省教育招生考试院：普通类投档情况表、一分一段表、志愿填报注意事项、录取工作意见。
2. 山东省教育厅：2026 高职单独招生和综合评价招生通知。
3. 阳光高考 / 教育部相关渠道：特殊类型招生、高校专项、强基计划、高水平运动队等政策边界。
4. 各高校招生章程：体检、语种、单科成绩、性别、校区、专业限制等。

本系统中的所有路径都必须保留“最终以官方发布和高校章程为准”的说明。

---

## 14. 最终提醒

第三轮不要追求“一步到位完整预测所有升学方式”。

本轮真正目标是：

```text
把多升学路径的数据库、规则、学生画像、资格初筛和页面入口搭起来。
```

普通类常规批继续做完整推荐。

其他路径先做：

```text
规则说明 + 资格初筛 + 材料缺口 + 人工复核 + 下一步行动
```

这样既能借鉴成熟志愿系统的多路径规划思路，又不会偏离本项目“山东生源地、自用、本地教务系统”的初衷。
