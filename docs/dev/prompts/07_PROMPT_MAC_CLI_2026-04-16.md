# 提示词：Mac Codex CLI（2026-04-16）

## 使用方式

1. 把以下文件放进：
   - `/Users/gao/local-edu-tool/docs/dev/`
2. 确保这几个文件存在：
   - `AGENTS.md`
   - `docs/dev/01_MASTER_PLAN_2026-04-16.md`
   - `docs/dev/02_SYNC_BOARD_2026-04-16.md`
   - `docs/dev/03_WORKSTREAM_MAC_MAINLINE_2026-04-16.md`
3. 在项目根目录打开 Codex CLI
4. 把下面整段提示词一次性粘贴进去

---

## 提示词正文

你现在是本项目在 Mac 上唯一的主应用开发 Codex，会话名是 `MAC_MAINLINE`。

先不要直接改代码，也不要先跑大范围命令。请先按下面顺序执行：

### 1）先读取这些文件
- `AGENTS.md`
- `docs/dev/01_MASTER_PLAN_2026-04-16.md`
- `docs/dev/02_SYNC_BOARD_2026-04-16.md`
- `docs/dev/03_WORKSTREAM_MAC_MAINLINE_2026-04-16.md`
- `README.md`
- 与高考推荐 / Stage B / 打印 / 导出 / 报表中心 / 高考数据相关的现有代码入口和文档

### 2）读取后先输出，不要立刻动手
先输出以下内容：

1. 你加载到的指令来源
2. 当前任务的：
   - Goal
   - Context
   - Constraints
   - Done when
3. 本会话的 owned paths
4. 本会话的 no-touch paths
5. 你认为本轮最优先的 3~5 个任务
6. 一份 4~8 步执行计划
7. 你准备补哪些测试

### 3）然后按这个优先顺序推进
#### 第一优先：高收益工程修正
先处理：

- 上传路径边界校验
- 下载路径安全校验
- 重复路由清理
- 对应测试补齐

#### 第二优先：高考数据只读驾驶舱
做第一版只读驾驶舱，至少覆盖：

- 高考数据总览页
- 数据审阅页
- 推荐解释证据页
- 山东首期数据监控页

优先检查和实现这些只读接口（已有则复用，没有再补）：

- `GET /api/gaokao/data-overview`
- `GET /api/gaokao/import-batches`
- `GET /api/gaokao/review-summary`
- `GET /api/gaokao/college-evidence/{college_id}`
- `GET /api/gaokao/shandong-monitor`

要求：

- 先做只读，不做复杂编辑
- 没有数据时必须有空态 / 演示态 / 友好提示
- 页面要让不懂数据库的人也能看懂

#### 第三优先：继续推进 Stage B 解释链统一
继续收口：

- 页面解释
- 打印解释
- Excel 导出解释
- 报表中心摘要

优先统一：

- 历史方案差异
- 同省跨年份差异
- 跨省差异
- “参考年份偏旧”提示
- 风险概览 / 边界概览 / 规则差异摘要

#### 第四优先：分析与导出模板统一
- 统一学生 / 班级 / 年级 / 教师摘要结构
- 打印和导出尽量共用公共结构
- 不重新发明一套新口径

#### 第五优先：高复杂模块小步拆分
- recommendations 相关高复杂模块
- workload / evaluation 相关组合逻辑
- 原则是小步拆分，不做大重构

#### 第六优先：文档和测试同步
至少同步：

- `README.md`
- `memory-bank/**`
- `docs/**`
- 本轮涉及的测试说明

### 4）你的硬约束
- 不要主动改 `apps/backend/alembic/**`
- 不要主动改 `apps/backend/app/importers/**`
- 不要主动改 `data/local_edu_tool/**`
- 不要主动改 `data/gaokao_staging/**`
- 不要直接依赖 Windows 现场工作库瞬时状态
- 如果发现需要 DB 结构改动，先写 `docs/dev/mac_db_contract_request.md`，不要越界改库
- 每完成一个小闭环，说明改了什么、为什么、怎么验证的
- 最后只更新 `docs/dev/02_SYNC_BOARD_2026-04-16.md` 中 `MAC_MAINLINE` 这一行和对应日志段落

### 5）工作方式要求
- 先只读分析，再动手
- 每次只做一个小闭环
- 不要一次改动太散
- 如果遇到和 Windows 数据库线潜在冲突，先停在文档层提出，不要自行越界修改

现在先进入只读规划阶段，先输出计划，不要直接改文件。
