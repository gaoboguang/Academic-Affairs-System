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
