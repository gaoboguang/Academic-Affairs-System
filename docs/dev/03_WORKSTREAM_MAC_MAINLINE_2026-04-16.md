# 子开发文档：`MAC_MAINLINE`（2026-04-16）

- 设备：Mac
- 表面：Codex CLI
- 项目路径：`/Users/gao/local-edu-tool`
- 角色：唯一主应用开发会话
- 当前定位：主应用主线 + 高考数据只读驾驶舱 + Stage B 解释链收口
- 你的工作目标：**让你自己能在系统里直观看到数据库做到了什么程度，同时不和 Windows 数据库线互相打架**

---

## 1. 你当前的上下文

当前主应用不是缺页面，而是到了下面这个阶段：

1. 推荐工作台已经是主线
2. 打印 / 导出 / 报表摘要链已经在收口
3. 现在更需要的是：
   - 统一解释口径
   - 提供只读可视化驾驶舱
   - 保持测试和文档同步
   - 不让复杂逻辑重新堆回超大文件

因此，你本轮的重点不是“继续乱补新功能”，而是：

> **做一版真正能给项目负责人看懂的只读数据驾驶舱，并继续把 Stage B 解释链统一掉。**

---

## 2. 你的任务边界

## 2.1 你负责什么
你负责以下 5 类工作。

### A. 高收益工程修正
先做：

1. 上传路径边界校验
2. 下载路径安全校验
3. 重复路由清理
4. 对应自动化测试补齐

### B. 高考数据只读驾驶舱
你要优先做第一版，只读即可。

至少包含 4 个页面或 4 个主要视图：

1. **高考数据总览页**
   - 看总量
   - 看覆盖率
   - 看 RC 版本
   - 看最近更新时间
   - 看核心表统计

2. **数据审阅页**
   - 看待复核项
   - 看 unresolved
   - 看 duplicate / same-name
   - 看 `chapter_url` 覆盖率
   - 能按状态筛选

3. **推荐解释证据页**
   - 点开某学校能看到：
     - 学校主档关键字段
     - `official_site`
     - `recruit_site`
     - `chapter_url`
     - `fallback_url`
     - `source_url`
     - review 状态
   - 先做只读展示，不做编辑

4. **山东首期数据监控页**
   - 看山东相关数据包是否齐
   - 看 admission plans / results / subject requirements / score segments / province rules 的覆盖和最近批次
   - 能用于你后续演示

### C. Stage B 解释链统一
继续收口这 4 条链：

1. 工作台内解释
2. 打印页解释
3. Excel 导出解释
4. 报表中心导出前摘要

要求：

- 同一条推荐结果，不要 4 个地方写出 4 套不同口径
- 历史对照、跨省差异、跨年份差异、参考年份偏旧等提示要统一

### D. 分析输出统一
把这些输出尽量统一成“同一个系统”的风格：

- 学生分析
- 班级分析
- 年级分析
- 教师分析
- 推荐摘要
- 打印摘要
- 导出摘要

### E. 文档和测试同步
至少同步：

- `README.md`
- `memory-bank/**`
- `docs/**`
- 与本轮功能相关的前后端测试

---

## 2.2 你不负责什么
你不负责：

- Windows 主库正式写入
- `chapter_url` 人工复核主劳动量
- Windows patch 合并
- `E:\shandong_admissions_2020_2025` 下的数据库线脚本主线
- 大范围 schema 变更

---

## 3. Owned paths

你优先工作的目录：

```text
apps/frontend/**
apps/backend/app/api/**
apps/backend/app/services/**
apps/backend/tests/**
tests/e2e/**
docs/**
memory-bank/**
README.md
```

---

## 4. No-touch paths

默认不要主动改：

```text
apps/backend/alembic/**
apps/backend/app/importers/**
apps/backend/scripts/** 中数据库主库导入/回写主线脚本
data/local_edu_tool/**
data/gaokao_staging/**
```

如果确实发现需要新增 DB 字段或状态码：

1. 先不要直接改
2. 新建：
   - `docs/dev/mac_db_contract_request.md`
3. 写清楚：
   - 为什么需要改
   - 影响哪些接口 / 页面 / 导出
   - 是否可以先用只读 fallback 解决
4. 交给 `WIN_DB_CORE` 评估

---

## 5. 本轮优先级顺序

## P0：先修高收益工程边界
完成标志：

- 路径穿越和非法下载被拒绝
- 上传类别边界更稳
- 正常功能不被破坏
- 测试补齐

---

## P1：做第一版高考数据只读驾驶舱
### 目标
让项目负责人不用碰数据库工具，也能直接看懂当前数据库搭建到哪一步。

### 建议实现顺序
1. 先查现有高考相关路由、service、schema、页面入口
2. 先补后端只读接口
3. 再补前端页面
4. 先做 overview，再做 review，再做 evidence，再做 sd monitor
5. 页面能显示空态 / demo 态 / 无数据提示，不要直接报错

### 建议优先接口
优先检查和实现这些接口（如果已有，就复用；没有再补）：

- `GET /api/gaokao/data-overview`
- `GET /api/gaokao/import-batches`
- `GET /api/gaokao/review-summary`
- `GET /api/gaokao/college-evidence/{college_id}`
- `GET /api/gaokao/shandong-monitor`

### 页面命名建议
你可以按现有项目风格命名，不强制，但建议语义清楚：

- `GaokaoDataOverviewPage`
- `GaokaoReviewPage`
- `GaokaoEvidencePage`
- `GaokaoShandongMonitorPage`

### 驾驶舱第一版必须显示的字段
#### 总览页
- 当前数据版本（如 `DB RC1`）
- 学校总数
- `recruit_site` 已覆盖数
- `chapter_url` 已覆盖数
- duplicate 数
- same-name 数
- 最近同步时间
- 最近批次信息

#### 审阅页
- `pending_manual_review`
- `pending_manual_review_with_official_candidate`
- `unresolved`
- duplicate / same-name 列表
- 支持按状态筛选

#### 证据页
- 学校名称 / code / id
- `official_site`
- `recruit_site`
- `chapter_url`
- `fallback_url`
- `source_url`
- `source_title`
- `review_status`
- `retrieval_status`
- 简要说明

#### 山东监控页
- 山东规则包
- 山东分数线包
- 山东一分一段
- 山东选科要求
- 山东投档录取
- 山东招生计划
- 覆盖 / 批次 / 最近更新时间

---

## P2：继续推进 Stage B 解释链统一
### 目标
同一条推荐结论，在 4 个出口里口径尽量一致：

- 页面
- 打印
- Excel
- 报表摘要

### 本轮重点
优先继续统一：

- 历史方案差异
- 同省跨年份差异
- 跨省口径差异
- “参考年份偏旧”提示
- 边界概览 / 风险概览 / 规则差异摘要

### 原则
- 优先复用已有 helper / snapshot / exporter
- 不重新发明一套新的解释链
- 不把新规则堆回单一 service

---

## P3：分析与导出模板统一
### 建议动作
1. 提炼共享摘要 helper
2. 统一学生 / 班级 / 年级 / 教师摘要结构
3. 打印和导出字段尽量共用
4. 对齐字段命名和标题风格

---

## P4：高复杂模块第二轮拆分
### 优先关注
- recommendations 相关高复杂模块
- `useTimetableWorkloadPage.ts`
- `useEvaluationQuantPage.ts`
- 后端 exporter / result builder 组合逻辑

### 原则
- 不做大重构
- 行为尽量不变
- 一次只拆一个小闭环
- 先补测试，再继续拆

---

## P5：文档与测试同步
至少要做：

1. 同步 README 当前能力
2. 同步 `memory-bank`
3. 对本轮新增页面和接口补最少必要测试
4. 把交接说明写到同步板

---

## 6. 建议工作节奏

每次只做一个小闭环：

1. 先读文档
2. 输出本轮计划
3. 实现一个小块
4. 跑相关测试
5. 更新同步板
6. 再做下一块

不要一口气跨太多模块。

---

## 7. 你的完成定义

本流完成，不是把所有想法一次做完，而是满足下面 6 条：

1. 高收益安全 / 边界问题收口一轮
2. 驾驶舱第一版可用
3. Stage B 解释链更统一
4. 分析 / 打印 / 导出模板更统一
5. 文档和测试同步
6. 没有和 Windows 数据库线冲突

---

## 8. 你开工前必须先输出什么

启动后先输出，不要直接改文件：

1. 你读取了哪些文件
2. 当前任务的：
   - Goal
   - Context
   - Constraints
   - Done when
3. 本会话的 owned paths
4. 本会话的 no-touch paths
5. 你本轮最优先的 3~5 个任务
6. 4~8 步执行计划
7. 你准备补哪些测试

---

## 9. 额外提醒

### 9.1 如果 `DB RC1` 还没迁到 Mac
允许你先做：

- 路由
- 页面壳
- 只读接口契约
- 空态 / 演示态
- 前端结构

不要因为数据还没到位就把整条任务卡死。

### 9.2 本轮不是让你重写推荐引擎
本轮是：

- 只读驾驶舱
- 解释统一
- 安全边界
- 小步收口

### 9.3 给项目负责人的标准
你做出来的东西，应该让一个**不懂数据库的人**也能大概看懂：

- 现在有多少学校
- 哪些字段覆盖了
- 哪些还在待确认
- 哪些学校的证据链是什么
