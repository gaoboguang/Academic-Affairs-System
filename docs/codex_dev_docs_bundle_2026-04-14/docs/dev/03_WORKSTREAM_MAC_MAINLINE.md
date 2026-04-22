# 子开发文档：MAC_MAINLINE

- 设备：Mac
- 表面：Codex CLI
- 项目路径：`/Users/gao/local-edu-tool`
- 角色：唯一主应用开发会话
- 文档目的：让 Mac 会话稳定推进应用主线，同时不与 Windows 数据库权威线冲突

---

## 1. 你的任务边界

### 1.1 你负责什么
你负责以下五类工作：

1. **安全与边界修复**
   - 上传 `category` 路径边界校验
   - 下载路径安全校验
   - 统一安全文件解析逻辑
   - 重复路由清理
   - 对应自动化测试补齐

2. **高考志愿 Stage B 应用层深化**
   - 候选解释、规则差异、风险提示继续统一
   - 工作台、打印页、导出页摘要一致性继续收口
   - 缺少年份规则、模式兼容、边界说明的应用层呈现继续打磨

3. **分析引擎与报表模板统一**
   - 学生 / 班级 / 年级 / 教师分析摘要结构继续归一
   - 打印 / 导出 / 报表中心摘要逻辑统一

4. **复杂度第二轮拆分**
   - recommendations 相关高复杂模块继续拆分
   - evaluation / workload 高复杂模块继续拆分
   - 保持行为不变前提下做结构收口

5. **文档与测试同步**
   - README
   - tests/README
   - memory-bank
   - docs/dev 中交接说明

### 1.2 你不负责什么
你不负责：

- Windows 主库正式写入
- `E:\shandong_admissions_2020_2025` 主战场的 B/C 数据收口
- 章程人工复核
- 主库 patch 合并
- 数据库冻结流程

---

## 2. Owned paths

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

说明：
- 允许改后端接口和服务层，因为安全边界修复、摘要统一、解释字段统一可能会涉及后端
- 但任何数据库结构变化都必须走“提出请求 -> Windows 评估”的方式

---

## 3. No-touch paths

在本轮默认情况下，你不要主动改：

```text
apps/backend/alembic/**
apps/backend/app/importers/**
apps/backend/scripts/** 里数据库主库审计/回写主线脚本
data/local_edu_tool/**
data/gaokao_staging/**
```

如果确实发现需要改数据库结构：
1. 不要直接改
2. 先把变更需求写成 `docs/dev/mac_db_contract_request.md`
3. 在同步板写清楚影响范围
4. 等 `WIN_DB_CORE` 接手

---

## 4. 本轮优先级顺序

## P0：先做高收益工程修正
目标：
- 在不依赖数据库冻结的情况下，先把明显的工程风险修掉

建议先做：
1. 上传目录边界校验
2. 下载路径安全收口
3. 重复路由清理
4. 相关测试补齐

完成标志：
- 非法路径和绝对路径被拒绝
- 正常上传/下载流程不被破坏
- 自动化测试补齐

## P1：继续推进 Stage B 应用层
目标：
- 让结果解释、规则差异、候选说明更稳定一致

建议先做：
1. 推荐工作台摘要统一
2. 打印页摘要统一
3. 导出前摘要统一
4. 历史方案 / 报表中心摘要统一
5. 错误态、空状态、边界说明补齐

完成标志：
- 同一候选在工作台、打印、导出三处的关键信息一致
- 缺少年份规则、模式兼容回退的说明一致

## P2：统一分析与报表模板
目标：
- 让分析类输出更像“一个系统”，而不是多处各写一套

建议做：
1. 提炼共享摘要 helper
2. 统一学生 / 班级 / 年级 / 教师分析的摘要字段
3. 收口导出模板中的公共结构

## P3：做第二轮复杂度拆分
优先关注：
- `apps/backend/app/services/_recommendations_result_builder.py`
- `apps/backend/app/services/_evaluation_batches.py`
- `apps/frontend/src/components/recommendations/`
- `apps/frontend/src/components/workload/useTimetableWorkloadPage.ts`
- `apps/frontend/src/components/evaluation/useEvaluationQuantPage.ts`

原则：
- 不重做
- 不改业务口径
- 先拆边界，再拆实现

## P4：文档与测试同步
至少同步：
- README 当前已完成功能
- 测试数量 / 覆盖范围说明
- 当前阶段已知限制
- 与 Windows 数据库线的交接说明

---

## 5. 你与 Windows 的协作方式

### 5.1 你可以依赖什么
你可以依赖：
- 当前已有稳定数据
- 已冻结的 DB release candidate
- `WIN_DB_CORE` 在同步板写清楚的 schema / 状态码变更

### 5.2 你暂时不要依赖什么
你不要依赖：
- 尚未冻结的 B/C 主库临时状态
- 正在人工复核中的章程 URL
- 尚未在同步板说明的数据库结构变化

---

## 6. 建议工作节奏

建议每次只做一个小闭环：

1. 读取文档
2. 输出计划
3. 实现
4. 跑相关测试
5. 更新 README 或 docs
6. 更新同步板

不要一口气跨多个大模块。

---

## 7. 完成定义

本流完成，不要求“一次做完全部愿望”，而是满足：

1. 高收益安全/边界问题已收口一轮
2. Stage B 应用层解释与摘要一致性明显提升
3. 分析和导出模板更统一
4. 高复杂模块继续拆散
5. 文档和测试说明已同步
6. 没有与 Windows 数据库线产生冲突

---

## 8. 建议你开工前先输出的内容

启动后先输出：

1. 你读取了哪些指令来源
2. 当前任务的 Goal / Context / Constraints / Done when
3. 本次只改哪些路径
4. 本次绝不碰哪些路径
5. 4~8 步执行计划
6. 需要补哪些测试
