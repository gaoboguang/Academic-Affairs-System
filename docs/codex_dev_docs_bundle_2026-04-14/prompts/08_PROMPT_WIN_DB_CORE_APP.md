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
