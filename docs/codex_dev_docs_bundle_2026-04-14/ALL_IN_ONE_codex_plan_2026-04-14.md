# 文件：README.md

# Codex 开发文档与提示词交付包（2026-04-14）

这套交付物按“1 份主文档 + 1 份同步板 + 每个窗口 1 份子文档 + 每个窗口 1 份提示词”的方式组织，方便你直接复制到项目里使用。

## 推荐使用顺序

1. 先下载 `codex_dev_docs_bundle_2026-04-14.zip`
2. 如果你只想下载 1 个文件，优先下载 `ALL_IN_ONE_codex_plan_2026-04-14.md`
3. 如果你想分文件使用，再单独下载 `docs/dev/*.md` 和 `prompts/*.md`

## 推荐放置路径

### Mac 主项目
项目路径：`/Users/gao/local-edu-tool`

建议把以下文件放入：
- `docs/dev/01_MASTER_PLAN_2026-04-14.md`
- `docs/dev/02_SYNC_BOARD_2026-04-14.md`
- `docs/dev/03_WORKSTREAM_MAC_MAINLINE.md`

如果你也想在 Mac 仓库里保留全部资料，可以把 `docs/dev/04~06` 和 `prompts/` 一并放进去。

### Windows 数据库主战场
项目路径：`E:\shandong_admissions_2020_2025`

建议把以下文件放入：
- `docs/dev/01_MASTER_PLAN_2026-04-14.md`
- `docs/dev/02_SYNC_BOARD_2026-04-14.md`
- `docs/dev/04_WORKSTREAM_WIN_DB_CORE.md`
- `docs/dev/05_WORKSTREAM_WIN_DATA_CURATION_A.md`
- `docs/dev/06_WORKSTREAM_WIN_DATA_CURATION_B.md`

提示词文件建议放在：
- `docs/dev/prompts/`
或
- 项目外单独保存，随时复制粘贴即可

## 这份包里有什么

### 文档
- `docs/dev/01_MASTER_PLAN_2026-04-14.md`
- `docs/dev/02_SYNC_BOARD_2026-04-14.md`
- `docs/dev/03_WORKSTREAM_MAC_MAINLINE.md`
- `docs/dev/04_WORKSTREAM_WIN_DB_CORE.md`
- `docs/dev/05_WORKSTREAM_WIN_DATA_CURATION_A.md`
- `docs/dev/06_WORKSTREAM_WIN_DATA_CURATION_B.md`

### 提示词
- `prompts/07_PROMPT_MAC_CLI.md`
- `prompts/08_PROMPT_WIN_DB_CORE_APP.md`
- `prompts/09_PROMPT_WIN_DATA_CURATION_A_APP.md`
- `prompts/10_PROMPT_WIN_DATA_CURATION_B_APP.md`
- `prompts/11_PROMPT_WIN_BURST_OPTIONAL_APP.md`

### 单文件总汇
- `ALL_IN_ONE_codex_plan_2026-04-14.md`

## 你现在的建议启动方式

- Mac：1 个 Codex CLI 会话，负责主应用主线
- Windows：3 个 Codex app 线程，分别负责
  - DB_CORE
  - DATA_CURATION_A
  - DATA_CURATION_B

只有在 **Git worktree 已经就位**，并且你确认不会多人同时改同一批文件时，Windows 才临时增加第 4 个冲刺线程。

## 使用提醒

1. 先把文档放进项目，再复制提示词给 Codex。
2. 每个会话启动后先让 Codex **只读文档并输出计划**，不要一上来就改代码或写库。
3. Windows 侧只有 `DB_CORE` 线程允许写主库。
4. 其他线程只允许产出 patch、audit、unresolved 三类结果。
5. 同步时只更新自己的行，不要整页重写同步板。

## 下载稳定性建议

为了尽量避开你之前遇到的下载失败问题，我这次做了三层兜底：

1. 所有导出文件名都使用 **ASCII 文件名**
2. 同时提供 **单文件总汇** 和 **ZIP 压缩包**
3. 也保留了单独 Markdown 文件，方便你只取其中一份


---

# 文件：docs/dev/01_MASTER_PLAN_2026-04-14.md

# 主开发文档（2026-04-14）

- 文档名称：Mac 主应用主线 + Windows 数据库权威线协作文档
- 适用对象：项目负责人、Mac 侧 Codex CLI、Windows 侧 Codex app
- 适用时间点：基于 2026-04-14 当前项目状态
- 文档定位：下一步开发计划、任务分工、冲突规避、冻结与回迁规则

---

## 1. 当前判断

项目当前不是“从零搭建”，也不是“补骨架阶段”，而是：

- Mac 主项目已经进入“高考志愿 Stage B 深化 + 分析/推荐引擎深化 + 产品化收口”阶段
- Windows 数据库主战场已经形成稳定目录、主库和分层数据目录
- A 已完成
- B 主体完成，但 `recruit_site` 仍需差异审计收口
- C 候选池与人工复核队列已成型，但正式章程 URL 仍是数据库线当前最大瓶颈

因此，下一步不应采用“Mac 和 Windows 双方都同时随意改一切”的方式，而应采用：

**Mac = 主应用主线**
**Windows = 数据库权威线**
**数据库冻结后单向回迁到 Mac 做联调和运行**

---

## 2. 本轮核心决策

### 2.1 设备分工

#### Mac
- 设备角色：主应用开发阵地
- Codex 形式：Codex CLI
- 会话数：1
- 主要任务：应用层、解释层、导出层、测试层、产品化层

#### Windows
- 设备角色：数据库权威阵地
- Codex 形式：Codex app
- 线程数：稳态 3 个，冲刺态最多 4 个
- 主要任务：数据库建模、导入器、审计、候选复核、数据库收口、发布候选包

### 2.2 文档组织方式

本轮采用：

- `AGENTS.md`：根规则，只保留长期稳定约束
- `01_MASTER_PLAN_2026-04-14.md`：总目标、分工、冻结点、协作规则
- `02_SYNC_BOARD_2026-04-14.md`：当前状态、阻塞、交接、更新时间
- `03~06_WORKSTREAM_*.md`：每个会话一个子文档
- `07~11_PROMPT_*.md`：每个会话一个专用启动提示词

**结论：采用“1 份主文档 + 每窗口 1 份子文档 + 1 份同步板”最合适。**
不建议把所有细任务继续堆进一个大开发文档里。

---

## 3. 项目路径口径

### 3.1 Mac 主项目
- 路径：`/Users/gao/local-edu-tool`

### 3.2 Windows 数据库主战场
- 路径：`E:\shandong_admissions_2020_2025`

### 3.3 Windows 主库
- 路径：`E:\shandong_admissions_2020_2025\data\local_edu_tool\local_edu.sqlite3`

---

## 4. 当前阶段目标

本轮总目标不是推倒重做，而是做四件事：

1. 让 Mac 继续沿 **Stage B 应用层主线** 往前推进
2. 让 Windows 把数据库做成 **可冻结、可审计、可回迁** 的发布候选
3. 把应用层与数据库层之间的边界固定下来，避免互相污染
4. 为最终“数据库回迁到 Mac 并运行”建立明确的冻结与交接流程

---

## 5. 会话分工总览

## 5.1 Mac：1 个会话

### MAC_MAINLINE
负责：
- 高考志愿 Stage B 的应用层深化
- 解释、摘要、工作台、打印、导出一致性
- 高风险大文件的第二轮拆分
- README / tests / memory-bank / 文档同步
- 独立于数据库正式收口之外的工程修复

不负责：
- Windows 主库正式写入
- 章程人工复核
- B/C 主库 patch 合并
- Windows 主战场目录整理

---

## 5.2 Windows：3 个线程

### WIN_DB_CORE
负责：
- 主库单写
- 迁移、导入器、审计脚本
- 接收和合并 A/B 线程产出的 patch
- 生成数据库发布候选包
- 冻结后的最终审计与交接说明

### WIN_DATA_CURATION_A
负责：
- `recruit_site` 尾差审计的 A 分片
- 章程复核队列的 A 分片
- 产出 patch / audit / unresolved，不直接写主库

### WIN_DATA_CURATION_B
负责：
- `recruit_site` 尾差审计的 B 分片
- 章程复核队列的 B 分片
- 产出 patch / audit / unresolved，不直接写主库

---

## 6. Windows 线程数建议

### 6.1 默认建议：3 个线程
这是当前最稳的方案。

原因：
- 一个线程专门做主库写入和合并
- 另外两个线程专门做人工复核与候选收口
- 数据与代码冲突面最小
- 工作量也相对均衡

### 6.2 什么时候可以临时开第 4 个线程
只有满足以下条件时，才建议临时开第 4 个冲刺线程：

1. 项目已在 Git 下
2. 线程运行在独立 worktree 或明确隔离的子目录
3. 不会和另外 3 个线程同时改同一批文件
4. 第 4 个线程只做“C 队列再切半”或“冻结后的打包验证”

不满足这些条件，就不要开第 4 个。

---

## 7. 硬规则

## 7.1 主库单写规则
任何时刻，只有 `WIN_DB_CORE` 可以写：
- `data/local_edu_tool/local_edu.sqlite3`

`WIN_DATA_CURATION_A/B` 只允许输出：
- `patch.csv`
- `audit.md`
- `unresolved.csv`

## 7.2 同文件单线程规则
同一时刻，同一份：
- CSV
- queue
- review doc
- 临时 patch

只能由 1 个线程负责。

## 7.3 分片必须确定性
A/B 分片必须按确定规则切，不允许口头划分。

本轮统一分片规则：

1. 首选 `college_id`
2. 若 `college_id` 为整数：
   - A 处理奇数
   - B 处理偶数
3. 若没有 `college_id`：
   - 使用 `college_code` 最后一位奇偶
4. 若还没有：
   - 先按学校名称排序，再按奇偶行号分片

## 7.4 Schema 变更握手规则
凡是数据库表、字段、状态码、规则码有变化，必须：

1. 由 `WIN_DB_CORE` 记录到同步板
2. 给出变更摘要
3. 标明是否影响 Mac 侧应用
4. 等冻结交接时同步到 Mac

## 7.5 冻结后单向回迁
不是边写边拷贝，而是：

1. 停止写入
2. 审计快照
3. 生成发布候选包
4. 再迁回 Mac 联调

---

## 8. 文档体系建议

建议在两个项目里都形成如下结构：

```text
docs/dev/
  01_MASTER_PLAN_2026-04-14.md
  02_SYNC_BOARD_2026-04-14.md
  03_WORKSTREAM_MAC_MAINLINE.md
  04_WORKSTREAM_WIN_DB_CORE.md
  05_WORKSTREAM_WIN_DATA_CURATION_A.md
  06_WORKSTREAM_WIN_DATA_CURATION_B.md
  prompts/
    07_PROMPT_MAC_CLI.md
    08_PROMPT_WIN_DB_CORE_APP.md
    09_PROMPT_WIN_DATA_CURATION_A_APP.md
    10_PROMPT_WIN_DATA_CURATION_B_APP.md
```

`AGENTS.md` 仍保持短小，不要把全部计划再塞进去。
只需在 `AGENTS.md` 里补一句：复杂任务先读 `docs/dev/01_MASTER_PLAN_2026-04-14.md` 与对应 `WORKSTREAM` 文档。

---

## 9. 本轮执行顺序

## 9.1 第一步：建立协作边界
- 把本套文档放入项目
- 建立同步板
- 让每个会话先读取文档并输出计划
- 不要一上来就改代码或写库

## 9.2 第二步：Mac 与 Windows 同步开工
### Mac
优先做：
1. 路径安全 / 下载边界 / 重复路由等高收益工程修正
2. Stage B 解释与结果呈现一致性
3. 打印 / 导出 / 摘要统一

### Windows
优先做：
1. B `recruit_site` 尾差审计
2. C 队列 A/B 分片复核
3. DB_CORE 负责主库合并与审计

## 9.3 第三步：收口与交接
- Windows 先形成 DB release candidate
- Mac 暂不依赖尚未冻结的正式库
- 冻结后再把 DB RC 迁回 Mac 做联调
- 联调通过后再进入桌面体验、安装体验和最终运行收口

---

## 10. Mac 本轮任务摘要

Mac 本轮重点不是补数据库，而是五件事：

1. **安全与边界修复**
   - 上传 category 路径边界校验
   - 下载路径安全校验
   - 重复路由清理
   - 配套测试补齐

2. **Stage B 应用层深化**
   - 结果解释组件继续统一
   - 风险提示 / 规则差异 / 候选解释继续收口
   - 工作台、打印页、导出页摘要一致

3. **统一分析与报表模板**
   - 学生 / 班级 / 年级 / 教师分析摘要结构继续归一
   - 打印与导出字段统一

4. **复杂度第二轮拆分**
   - recommendations / evaluation / workload 高复杂模块继续拆分

5. **文档与测试同步**
   - README
   - tests/README
   - memory-bank
   - 同步板交接说明

---

## 11. Windows 本轮任务摘要

Windows 本轮重点不是“再铺新范围”，而是把数据库线做扎实：

1. **B 任务差异审计**
   - `recruit_site` 候选 vs 主库正式字段
   - 尾差收口
   - 形成 patch

2. **C 任务人工复核**
   - `1708` 条“已有官方候选”复核推进
   - `246` 条“待官方补查”推进
   - 分片处理、集中合并

3. **DB 结果正式化**
   - 迁移
   - 审计
   - 发布候选包
   - 交接说明

---

## 12. 冻结点定义

进入“数据库回迁到 Mac”之前，必须同时满足：

1. `WIN_DB_CORE` 已停止对主库写入
2. 主库已完成最终审计快照
3. B 尾差已清零或全部有书面说明
4. C 队列已完成一轮集中人工复核
5. 已生成数据库发布候选包
6. 同步板已记录版本号、时间、已知问题

---

## 13. Mac 接收 DB RC 后的动作

Mac 在拿到 DB RC 之后，按以下顺序推进：

1. 只读接入，不立即改 schema
2. 做应用层联调
3. 验证：
   - 工作台
   - 查询
   - 推荐工作台
   - 打印 / 导出
4. 记录兼容问题
5. 只在必要时再发起 schema 变更请求给 Windows 数据库线

---

## 14. 完成定义

本轮完成，不是“所有愿望都做完”，而是满足以下条件：

### Mac 侧
- 应用主线继续推进且不与数据库线冲突
- Stage B 解释与展示更稳
- 关键安全与边界问题修掉
- 文档与测试同步更新

### Windows 侧
- 主库成为唯一可信数据源
- B 尾差和 C 队列完成一轮实质收口
- 生成 DB 发布候选包
- 可单向回迁到 Mac

---

## 15. 给人的一句话操作口令

**Mac 只做主应用；Windows 只做数据库权威线；只有冻结后，数据库才单向回迁到 Mac。**


---

# 文件：docs/dev/02_SYNC_BOARD_2026-04-14.md

# 同步板（2026-04-14 初始版）

> 使用规则：
> 1. 每个会话只改自己的那一行和自己的日志段落
> 2. 时间统一写 `UTC+08`
> 3. 不要整页重写
> 4. 发现会影响别的会话的事，先写到 `影响说明`，再继续

---

## 1. 当前全局状态

- 总策略：Mac 主应用主线，Windows 数据库权威线
- 主库写权限：仅 `WIN_DB_CORE`
- 数据库冻结后才能回迁到 Mac
- 当前重点：
  - Mac：Stage B 应用层深化 + 安全与导出边界修复
  - Windows：B 尾差收口 + C 人工复核推进

---

## 2. 工作流总表

| Stream | Device | Surface | 当前目标 | Owned paths | No-touch | 当前状态 | 阻塞 | 最后更新 |
|---|---|---|---|---|---|---|---|---|
| MAC_MAINLINE | Mac | Codex CLI | Stage B 应用层、导出/打印/摘要统一、安全边界修复 | `apps/frontend/**`, `apps/backend/app/api/**`, `apps/backend/app/services/**`, `apps/backend/tests/**`, `docs/**`, `README.md`, `memory-bank/**` | Windows 主库、Windows C 队列、Windows patch 合并 | 待启动 | 无 |  |
| WIN_DB_CORE | Windows | Codex app | 主库单写、迁移、审计、patch 合并、DB RC | `data/local_edu_tool/**`, `apps/backend/alembic/**`, `apps/backend/app/importers/**`, `apps/backend/scripts/**`, `docs/dev/**`, `output/db_release/**` | Mac 主应用大页面重构；A/B 分片原始任务区 | 待启动 | 无 |  |
| WIN_DATA_CURATION_A | Windows | Codex app | B 尾差 A 分片 + C 队列 A 分片 | `data/gaokao_staging/**` 中 A 分片工作文件，`output/review_patches/curation_a/**`, `docs/dev/review_logs/curation_a.md` | 主库、B 分片、Mac repo | 待启动 | 无 |  |
| WIN_DATA_CURATION_B | Windows | Codex app | B 尾差 B 分片 + C 队列 B 分片 | `data/gaokao_staging/**` 中 B 分片工作文件，`output/review_patches/curation_b/**`, `docs/dev/review_logs/curation_b.md` | 主库、A 分片、Mac repo | 待启动 | 无 |  |

---

## 3. 关键交接约定

### 3.1 数据库相关
- 只有 `WIN_DB_CORE` 可以写 `data/local_edu_tool/local_edu.sqlite3`
- `WIN_DATA_CURATION_A/B` 只能提交：
  - `patch.csv`
  - `audit.md`
  - `unresolved.csv`

### 3.2 应用相关
- Mac 侧在 DB RC 冻结前，不依赖尚未冻结的正式数据库结构
- 如果 Mac 侧需要新增 DB 字段或状态码，先写“变更请求”，由 `WIN_DB_CORE` 评估

### 3.3 文档相关
- 每个流只改自己的：
  - `WORKSTREAM` 文档
  - `review log`
  - `sync board row`
- 不得顺手改别的流的说明

---

## 4. 分片规则

### B 任务 `recruit_site` 尾差
- 首选 `college_id` 奇偶分片
- A 处理奇数
- B 处理偶数

### C 任务章程复核
- 同样使用 `college_id` 奇偶分片
- A 处理奇数
- B 处理偶数

### 兜底
若原始文件没有可用整数 ID：
1. 按学校名称排序
2. 交替分片
3. 第 1 行给 A，第 2 行给 B，以此类推

---

## 5. 每次更新模板

请按以下格式追加到自己的日志段落：

```text
[UTC+08 YYYY-MM-DD HH:MM]
- 本次完成：
- 新产物：
- 影响别人的点：
- 当前阻塞：
- 下一步：
```

---

## 6. 各流日志

### MAC_MAINLINE
- 待填写

### WIN_DB_CORE
- 待填写

### WIN_DATA_CURATION_A
- 待填写

### WIN_DATA_CURATION_B
- 待填写


---

# 文件：docs/dev/03_WORKSTREAM_MAC_MAINLINE.md

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


---

# 文件：docs/dev/04_WORKSTREAM_WIN_DB_CORE.md

# 子开发文档：WIN_DB_CORE

- 设备：Windows
- 表面：Codex app
- 项目路径：`E:\shandong_admissions_2020_2025`
- 角色：唯一主库写线程
- 文档目的：让 Windows 侧有一个稳定的数据库权威线程，负责主库、迁移、审计和合并

---

## 1. 你的角色

你是 **数据库权威线**，不是“万能协助线程”。

你负责：
1. 主库单写
2. 迁移、导入器、审计脚本
3. 接收 A/B 分片线程的 patch
4. 合并 patch 并写回主库
5. 生成数据库发布候选包
6. 输出冻结与交接说明

你不负责：
- Mac 主应用高复杂页面重构
- 大范围前端交互改造
- A/B 分片的人工复核主劳动量
- 没有明确边界的新需求扩张

---

## 2. 你拥有的写权限

你是本轮唯一允许写以下路径的线程：

```text
data/local_edu_tool/local_edu.sqlite3
apps/backend/alembic/**
apps/backend/app/importers/**
apps/backend/scripts/**
output/db_release/**
docs/dev/** 中与数据库发布、审计、冻结、交接相关的文档
```

你可以在必要时触碰：
```text
apps/backend/app/models/**
apps/backend/app/schemas/**
```

前提：
- 确实是数据库结构、导入、审计需要
- 变更必须写入同步板
- 变更必须给出摘要和影响面

---

## 3. 你不该碰的区域

你默认不要改：

```text
apps/frontend/**
Mac 主项目中的 docs / memory-bank / README
A/B 线程的分片原始工作文件
```

---

## 4. 本轮主目标

## 4.1 先建立基线
开工先做：

1. 只读确认当前主库基线
2. 确认本轮主库备份策略
3. 记录当前核心指标
4. 在同步板登记本轮版本基线

建议记录：
- `gaokao_college_total`
- `gaokao_college_chapter_rule_total`
- `recruit_site_filled`
- `chapter_rule_chapter_url_filled`
- `chapter_rule_fallback_url_filled`

## 4.2 产出分片工作面
你的职责不是替 A/B 做复核，而是给他们稳定边界。

建议做：
1. 生成 A/B 分片说明
2. 明确 B 尾差分片规则
3. 明确 C 队列分片规则
4. 指定 patch 输出目录
5. 指定 review log 输出目录

## 4.3 合并 A/B patch
收到 A/B patch 后：

1. 先做格式校验
2. 再做重复和冲突检查
3. 再做写回
4. 写回后立刻跑审计
5. 把结果记录到同步板

## 4.4 生成 DB release candidate
当 B/C 已推进到一个稳定冻结点后，执行：

1. 停止主库写入
2. 生成最终审计快照
3. 导出 DB RC
4. 导出审计结果
5. 写交接说明

---

## 5. 你应该要求 A/B 提交什么

A/B 只能提交以下三类产物：

### 必须
- `patch.csv`
- `audit.md`
- `unresolved.csv`

### 可选
- `evidence/` 下的截图或来源说明
- `notes.md`

### 不接受
- 直接改主库
- 直接覆盖公共队列
- 不带说明的大范围文件替换

---

## 6. 建议目录

你可以在 Windows 项目里建立：

```text
output/
  review_patches/
    curation_a/
    curation_b/
  db_release/
    2026-04-14_rc1/
docs/dev/
  review_logs/
    curation_a.md
    curation_b.md
  db_freeze_notes.md
  db_handoff_to_mac.md
```

---

## 7. 建议本轮顺序

## P0：建立基线与备份
- 主库只读核查
- 备份
- 同步板登记

## P1：分片规则与输出目录
- 给 A/B 一个稳定、不冲突的工作面

## P2：B 尾差合并
- `recruit_site` 候选 vs 主库字段差异审计
- 合并通过复核的 patch

## P3：C 队列合并
- 合并 A/B 对 `1708 + 246` 队列推进产生的 patch
- 跑审计
- 记录剩余 unresolved

## P4：生成 DB RC
- 冻结
- 审计
- 打包
- 交接到 Mac

---

## 8. 冻结标准

你可以宣布 DB RC 冻结，当且仅当：

1. 当前没有别的线程正在写主库
2. B 尾差已清零或全部书面说明
3. C 队列已完成一轮集中复核
4. 审计脚本已通过
5. 交接说明已生成

---

## 9. 你与 Mac 的协作口径

### 9.1 你要给 Mac 什么
你要给 Mac：
- DB RC 文件
- 审计快照
- 变更摘要
- 已知风险清单
- 是否影响应用层的说明

### 9.2 你不要直接要求 Mac 做什么
你不要直接让 Mac：
- 在未冻结前跟进你的临时结构
- 依赖待复核 URL
- 读取未审计通过的中间库

---

## 10. 完成定义

本流完成的标志：

1. 你一直是唯一主库写线程
2. B/C patch 合并过程可追溯
3. 主库审计结果可复现
4. 已生成 DB RC
5. Mac 可以基于 DB RC 做联调，不需要再猜数据库状态

---

## 11. 开工前先输出什么

启动后先输出：

1. 你读取了哪些文档
2. 当前主库基线准备怎么记录
3. 你本轮要拥有的路径
4. 你绝不碰的路径
5. 你要求 A/B 提交的 patch 格式
6. 本轮 4~8 步执行计划


---

# 文件：docs/dev/05_WORKSTREAM_WIN_DATA_CURATION_A.md

# 子开发文档：WIN_DATA_CURATION_A

- 设备：Windows
- 表面：Codex app
- 项目路径：`E:\shandong_admissions_2020_2025`
- 角色：数据库人工复核 A 分片线程
- 文档目的：负责 B 尾差和 C 队列的 A 分片，不碰主库

---

## 1. 你的角色

你是 **人工复核 A 分片线程**，不是主库线程。

你负责：

1. `recruit_site` 尾差的 A 分片
2. 章程复核队列的 A 分片
3. 形成 patch / audit / unresolved
4. 把结果交给 `WIN_DB_CORE`

你不负责：
- 写主库
- 合并别人的 patch
- 大范围修改数据库脚本
- Mac 主应用开发

---

## 2. 分片规则

### 默认规则
优先使用整数 `college_id`：

- A 处理奇数
- B 处理偶数

### 若没有 `college_id`
退化为：

1. 用 `college_code` 最后一位奇偶分片
2. 若还不行，按学校名称排序后按奇偶行号分片

### 原则
你的分片必须是确定性的，别人能复现你的筛选逻辑。

---

## 3. 你处理哪些内容

## 3.1 B 任务：`recruit_site` 尾差 A 分片
你的目标：
- 对候选数据与主库正式字段的差异做 A 分片核对
- 只处理属于 A 分片的记录
- 形成可写回 patch

建议产物：
- `output/review_patches/curation_a/recruit_site_patch_a.csv`
- `output/review_patches/curation_a/recruit_site_unresolved_a.csv`
- `docs/dev/review_logs/curation_a.md`

## 3.2 C 任务：章程复核 A 分片
你的目标：
- 推进 A 分片的 `pending_manual_review_with_official_candidate`
- 推进 A 分片的 `pending_manual_review`
- 能确认正式入口就确认，不能确认就明确 unresolved 原因

建议产物：
- `output/review_patches/curation_a/chapter_patch_a.csv`
- `output/review_patches/curation_a/chapter_unresolved_a.csv`
- `docs/dev/review_logs/curation_a.md`

---

## 4. 你只能写哪些地方

你可以写：

```text
output/review_patches/curation_a/**
docs/dev/review_logs/curation_a.md
自己分片的临时工作文件
```

你不要写：

```text
data/local_edu_tool/local_edu.sqlite3
curation_b/**
主库合并脚本
Mac 项目
```

---

## 5. 你的工作方法

## P0：先确认分片范围
先输出：
- 你使用的分片规则
- 你的 owned rows 如何筛
- 你的输出目录

## P1：做 B 尾差 A 分片
建议动作：
1. 读取 `recruit_site` 候选与正式字段差异
2. 只取 A 分片
3. 确认可回写项
4. 形成 patch 和 unresolved

## P2：做 C 队列 A 分片
建议动作：
1. 读取官方候选入口
2. 优先确认“已有候选”的 A 分片
3. 再推进“待官方补查”的 A 分片
4. 保留证据与来源说明

## P3：交付给 DB_CORE
你交付的不是“我改完了”，而是：
- patch
- unresolved
- audit 说明

---

## 6. 产物格式建议

### patch.csv 最少字段
- `college_id`
- `field_name`
- `old_value`
- `new_value`
- `source_url`
- `review_status`
- `review_note`

### unresolved.csv 最少字段
- `college_id`
- `field_name`
- `current_value`
- `candidate_value`
- `reason`
- `next_action`

### audit.md 建议写
- 本次处理范围
- 已确认条数
- 未确认条数
- 高风险情况
- 是否影响别的线程

---

## 7. 你的完成定义

你完成，不是“把库改完”，而是：

1. A 分片的 B 尾差完成一轮核对
2. A 分片的 C 队列完成一轮复核
3. 所有结果都形成 patch / unresolved / audit
4. 没有直接写主库
5. 结果能被 `WIN_DB_CORE` 稳定合并

---

## 8. 你开工前先输出什么

启动后先输出：

1. 你读取了哪些文档
2. 你采用的分片规则
3. 你本轮只处理哪些记录
4. 你只会写哪些目录
5. 你绝不碰哪些目录
6. 4~8 步执行计划


---

# 文件：docs/dev/06_WORKSTREAM_WIN_DATA_CURATION_B.md

# 子开发文档：WIN_DATA_CURATION_B

- 设备：Windows
- 表面：Codex app
- 项目路径：`E:\shandong_admissions_2020_2025`
- 角色：数据库人工复核 B 分片线程
- 文档目的：负责 B 尾差和 C 队列的 B 分片，不碰主库

---

## 1. 你的角色

你是 **人工复核 B 分片线程**，不是主库线程。

你负责：

1. `recruit_site` 尾差的 B 分片
2. 章程复核队列的 B 分片
3. 形成 patch / audit / unresolved
4. 把结果交给 `WIN_DB_CORE`

你不负责：
- 写主库
- 合并别人的 patch
- 大范围修改数据库脚本
- Mac 主应用开发

---

## 2. 分片规则

### 默认规则
优先使用整数 `college_id`：

- A 处理奇数
- B 处理偶数

### 若没有 `college_id`
退化为：

1. 用 `college_code` 最后一位奇偶分片
2. 若还不行，按学校名称排序后按奇偶行号分片

### 原则
你的分片必须是确定性的，别人能复现你的筛选逻辑。

---

## 3. 你处理哪些内容

## 3.1 B 任务：`recruit_site` 尾差 B 分片
你的目标：
- 对候选数据与主库正式字段的差异做 B 分片核对
- 只处理属于 B 分片的记录
- 形成可写回 patch

建议产物：
- `output/review_patches/curation_b/recruit_site_patch_b.csv`
- `output/review_patches/curation_b/recruit_site_unresolved_b.csv`
- `docs/dev/review_logs/curation_b.md`

## 3.2 C 任务：章程复核 B 分片
你的目标：
- 推进 B 分片的 `pending_manual_review_with_official_candidate`
- 推进 B 分片的 `pending_manual_review`
- 能确认正式入口就确认，不能确认就明确 unresolved 原因

建议产物：
- `output/review_patches/curation_b/chapter_patch_b.csv`
- `output/review_patches/curation_b/chapter_unresolved_b.csv`
- `docs/dev/review_logs/curation_b.md`

---

## 4. 你只能写哪些地方

你可以写：

```text
output/review_patches/curation_b/**
docs/dev/review_logs/curation_b.md
自己分片的临时工作文件
```

你不要写：

```text
data/local_edu_tool/local_edu.sqlite3
curation_a/**
主库合并脚本
Mac 项目
```

---

## 5. 你的工作方法

## P0：先确认分片范围
先输出：
- 你使用的分片规则
- 你的 owned rows 如何筛
- 你的输出目录

## P1：做 B 尾差 B 分片
建议动作：
1. 读取 `recruit_site` 候选与正式字段差异
2. 只取 B 分片
3. 确认可回写项
4. 形成 patch 和 unresolved

## P2：做 C 队列 B 分片
建议动作：
1. 读取官方候选入口
2. 优先确认“已有候选”的 B 分片
3. 再推进“待官方补查”的 B 分片
4. 保留证据与来源说明

## P3：交付给 DB_CORE
你交付的不是“我改完了”，而是：
- patch
- unresolved
- audit 说明

---

## 6. 产物格式建议

### patch.csv 最少字段
- `college_id`
- `field_name`
- `old_value`
- `new_value`
- `source_url`
- `review_status`
- `review_note`

### unresolved.csv 最少字段
- `college_id`
- `field_name`
- `current_value`
- `candidate_value`
- `reason`
- `next_action`

### audit.md 建议写
- 本次处理范围
- 已确认条数
- 未确认条数
- 高风险情况
- 是否影响别的线程

---

## 7. 你的完成定义

你完成，不是“把库改完”，而是：

1. B 分片的 B 尾差完成一轮核对
2. B 分片的 C 队列完成一轮复核
3. 所有结果都形成 patch / unresolved / audit
4. 没有直接写主库
5. 结果能被 `WIN_DB_CORE` 稳定合并

---

## 8. 你开工前先输出什么

启动后先输出：

1. 你读取了哪些文档
2. 你采用的分片规则
3. 你本轮只处理哪些记录
4. 你只会写哪些目录
5. 你绝不碰哪些目录
6. 4~8 步执行计划


---

# 文件：prompts/07_PROMPT_MAC_CLI.md

# 提示词：Mac Codex CLI

## 使用方式

1. 把 `docs/dev/01~03` 放到 `/Users/gao/local-edu-tool/docs/dev/`
2. 在项目根目录启动 Codex CLI
3. 把下面整段提示词一次性粘贴进去

---

## 提示词正文

你现在是本项目在 Mac 上唯一的主应用开发 Codex，会话名是 `MAC_MAINLINE`。

先不要直接改代码，也不要先跑大范围命令。请先按下面顺序执行：

1. 先读取这些文件：
   - `AGENTS.md`
   - `docs/dev/01_MASTER_PLAN_2026-04-14.md`
   - `docs/dev/02_SYNC_BOARD_2026-04-14.md`
   - `docs/dev/03_WORKSTREAM_MAC_MAINLINE.md`
   - `README.md`
   - 与推荐 / Stage B / 分析 / 打印 / 导出相关的现有开发文档和当前代码入口

2. 读取后先输出，不要立刻动手：
   - 你加载到的指令来源
   - 当前任务的 Goal / Context / Constraints / Done when
   - 本会话的 owned paths
   - 本会话的 no-touch paths
   - 你认为本轮最优先的 3~5 个任务
   - 一份 4~8 步的执行计划
   - 你准备补哪些测试

3. 然后按以下顺序推进：
   - 先做高收益工程修正：上传路径边界、下载路径安全、重复路由与对应测试
   - 再做高考志愿 Stage B 应用层深化：规则差异、候选解释、风险提示、工作台/打印/导出摘要一致性
   - 再做分析摘要、打印摘要、导出摘要统一
   - 再做 recommendations / evaluation / workload 相关高复杂模块的第二轮拆分
   - 最后同步 README、tests 说明、memory-bank 与 docs/dev 交接说明

4. 你的硬约束：
   - 不要重做已完成的 M0-M6 主线
   - 不要主动改 Windows 数据库主战场
   - 不要在没有明确数据库交接的情况下直接改数据库结构
   - 若确实需要数据库字段/状态码变更，先写成文档请求，再等 Windows 数据库线处理
   - 保持本地、单用户、离线优先、中文界面、`127.0.0.1` 监听不变
   - 所有新增能力都要补最小自动化测试
   - 每做完一个小闭环，就更新相应文档，不要只改代码不改说明

5. 你的交付方式：
   - 每完成一个子任务，先总结改了什么、为什么这么改、怎么验证的
   - 如果发现与 Windows 数据库线有潜在冲突，先停在文档层提出，不要自行越界修改
   - 最后更新 `docs/dev/02_SYNC_BOARD_2026-04-14.md` 中 `MAC_MAINLINE` 这一行和对应日志段落

现在先进入只读分析阶段，先输出你的计划，不要直接改文件。


---

# 文件：prompts/08_PROMPT_WIN_DB_CORE_APP.md

# 提示词：Windows Codex app / WIN_DB_CORE

## 使用方式

1. 在 Codex app 中打开项目：`E:\shandong_admissions_2020_2025`
2. 如果项目已经在 Git 下并且 worktree 可用，优先让这个线程运行在独立 worktree
3. 默认保持 sandbox / default permissions，不要一开始就 full access
4. 把下面整段提示词粘贴到 `WIN_DB_CORE` 线程

---

## 提示词正文

你现在是 Windows 侧唯一允许写主库的 Codex 线程，会话名是 `WIN_DB_CORE`。

先不要直接写库，也不要先跑破坏性命令。请先按下面顺序执行：

1. 先读取这些文件：
   - `AGENTS.md`
   - `docs/dev/01_MASTER_PLAN_2026-04-14.md`
   - `docs/dev/02_SYNC_BOARD_2026-04-14.md`
   - `docs/dev/04_WORKSTREAM_WIN_DB_CORE.md`
   - 当前数据库相关 README、审计脚本、导入器、迁移和相关文档

2. 读取后先输出，不要立刻动手：
   - 你加载到的指令来源
   - 当前任务的 Goal / Context / Constraints / Done when
   - 本线程的 owned paths
   - 本线程的 no-touch paths
   - 主库基线准备怎么记录
   - 你要求 A/B 分片线程提交什么格式的 patch
   - 一份 4~8 步执行计划

3. 然后按以下顺序推进：
   - 先用只读方式确认主库基线
   - 建立备份与审计基线
   - 明确 A/B 分片规则与输出目录
   - 接收并合并 B `recruit_site` 尾差 patch
   - 接收并合并 C 章程复核 patch
   - 每次合并后跑审计并记录结果
   - 在冻结点生成 DB release candidate、审计快照和 handoff 文档

4. 你的硬约束：
   - 你是唯一允许写 `data/local_edu_tool/local_edu.sqlite3` 的线程
   - A/B 线程只能提交 patch / audit / unresolved，绝不能直接写主库
   - 不要主动去做 Mac 主应用层的大页面或复杂交互改造
   - 所有数据库结构或状态码变化都要写入同步板
   - 任何合并前先做格式校验、冲突检查、重复检查
   - 冻结后再交接给 Mac，不要边写边回迁

5. 你的交付方式：
   - 每一轮只做一个清晰闭环
   - 每完成一个闭环，说明：做了什么、动了哪些文件、如何审计、还剩什么
   - 最后只更新 `docs/dev/02_SYNC_BOARD_2026-04-14.md` 中 `WIN_DB_CORE` 这一行和对应日志段落

现在先进入只读规划阶段，先输出计划，不要直接写库。


---

# 文件：prompts/09_PROMPT_WIN_DATA_CURATION_A_APP.md

# 提示词：Windows Codex app / WIN_DATA_CURATION_A

## 使用方式

1. 在 Codex app 中打开项目：`E:\shandong_admissions_2020_2025`
2. 建议把这个线程作为人工复核线程，不要赋予 full access
3. 如果项目在 Git 下且 worktree 可用，优先用独立 worktree；否则严格只在自己目录和分片范围内工作
4. 把下面整段提示词粘贴到 `WIN_DATA_CURATION_A` 线程

---

## 提示词正文

你现在是 Windows 侧数据库人工复核 A 分片线程，会话名是 `WIN_DATA_CURATION_A`。

你不是主库线程，禁止直接写主库。先不要改文件，请先按下面顺序执行：

1. 先读取这些文件：
   - `AGENTS.md`
   - `docs/dev/01_MASTER_PLAN_2026-04-14.md`
   - `docs/dev/02_SYNC_BOARD_2026-04-14.md`
   - `docs/dev/05_WORKSTREAM_WIN_DATA_CURATION_A.md`
   - 本轮涉及的 B/C 数据文件、review queue 和相关说明

2. 读取后先输出，不要立刻动手：
   - 你加载到的指令来源
   - 当前任务的 Goal / Context / Constraints / Done when
   - 你使用的 A/B 分片规则
   - 你只处理哪些记录
   - 你只会写哪些目录
   - 你绝不碰哪些目录
   - 一份 4~8 步执行计划

3. 你的任务顺序：
   - 先做 B `recruit_site` 尾差的 A 分片核对
   - 再做 C 队列中“已有官方候选”的 A 分片复核
   - 再做 C 队列中“待官方补查”的 A 分片推进
   - 对每一轮结果输出 patch / unresolved / audit
   - 把结果交给 `WIN_DB_CORE`，不要自行写主库

4. 你的硬约束：
   - 禁止修改 `data/local_edu_tool/local_edu.sqlite3`
   - 禁止覆盖 B 分片文件
   - 禁止顺手改别的线程的文档
   - 分片规则必须可复现
   - 所有 patch 都要带来源说明和 review note
   - 不能确认的记录必须进 unresolved，不要硬写

5. 你的交付方式：
   - 对每一轮说明：处理范围、已确认条数、未确认条数、高风险项
   - 最后只更新 `docs/dev/02_SYNC_BOARD_2026-04-14.md` 中 `WIN_DATA_CURATION_A` 这一行和对应日志段落

现在先进入只读规划阶段，先输出计划，不要直接改文件。


---

# 文件：prompts/10_PROMPT_WIN_DATA_CURATION_B_APP.md

# 提示词：Windows Codex app / WIN_DATA_CURATION_B

## 使用方式

1. 在 Codex app 中打开项目：`E:\shandong_admissions_2020_2025`
2. 建议把这个线程作为人工复核线程，不要赋予 full access
3. 如果项目在 Git 下且 worktree 可用，优先用独立 worktree；否则严格只在自己目录和分片范围内工作
4. 把下面整段提示词粘贴到 `WIN_DATA_CURATION_B` 线程

---

## 提示词正文

你现在是 Windows 侧数据库人工复核 B 分片线程，会话名是 `WIN_DATA_CURATION_B`。

你不是主库线程，禁止直接写主库。先不要改文件，请先按下面顺序执行：

1. 先读取这些文件：
   - `AGENTS.md`
   - `docs/dev/01_MASTER_PLAN_2026-04-14.md`
   - `docs/dev/02_SYNC_BOARD_2026-04-14.md`
   - `docs/dev/06_WORKSTREAM_WIN_DATA_CURATION_B.md`
   - 本轮涉及的 B/C 数据文件、review queue 和相关说明

2. 读取后先输出，不要立刻动手：
   - 你加载到的指令来源
   - 当前任务的 Goal / Context / Constraints / Done when
   - 你使用的 A/B 分片规则
   - 你只处理哪些记录
   - 你只会写哪些目录
   - 你绝不碰哪些目录
   - 一份 4~8 步执行计划

3. 你的任务顺序：
   - 先做 B `recruit_site` 尾差的 B 分片核对
   - 再做 C 队列中“已有官方候选”的 B 分片复核
   - 再做 C 队列中“待官方补查”的 B 分片推进
   - 对每一轮结果输出 patch / unresolved / audit
   - 把结果交给 `WIN_DB_CORE`，不要自行写主库

4. 你的硬约束：
   - 禁止修改 `data/local_edu_tool/local_edu.sqlite3`
   - 禁止覆盖 A 分片文件
   - 禁止顺手改别的线程的文档
   - 分片规则必须可复现
   - 所有 patch 都要带来源说明和 review note
   - 不能确认的记录必须进 unresolved，不要硬写

5. 你的交付方式：
   - 对每一轮说明：处理范围、已确认条数、未确认条数、高风险项
   - 最后只更新 `docs/dev/02_SYNC_BOARD_2026-04-14.md` 中 `WIN_DATA_CURATION_B` 这一行和对应日志段落

现在先进入只读规划阶段，先输出计划，不要直接改文件。


---

# 文件：prompts/11_PROMPT_WIN_BURST_OPTIONAL_APP.md

# 可选提示词：Windows Codex app / WIN_BURST_OPTIONAL

> 只有在以下条件同时满足时才启用本提示词：
> 1. 项目在 Git 下
> 2. worktree 已经就位
> 3. 前 3 个线程边界清晰
> 4. 你确认不会与它们同时改同一批文件

---

## 推荐用途

这个额外线程只做一件事，二选一：

1. 把 C 人工复核队列再次切半，专门处理临时转移过来的一段
2. 在数据库冻结后，专门做 Windows 打包 / 审计复跑 / 交接整理

不要让它同时做多件事。

---

## 提示词正文

你现在是 Windows 侧可选冲刺线程，会话名是 `WIN_BURST_OPTIONAL`。

你的唯一原则是：**不碰主库，不碰别人的已拥有路径，只做一件已明确分配的事。**

先读取：
- `AGENTS.md`
- `docs/dev/01_MASTER_PLAN_2026-04-14.md`
- `docs/dev/02_SYNC_BOARD_2026-04-14.md`
- 负责你的那份临时分派说明

读取后先输出：
- 你加载到的指令来源
- 你被分到的唯一任务
- 你的 owned paths
- 你的 no-touch paths
- 4~6 步执行计划

硬约束：
- 禁止直接写主库
- 禁止顺手处理未明确分派的文件
- 禁止把自己变成新的“万能线程”
- 完成后只更新同步板自己的行

现在先输出计划，不要直接动手。


---
