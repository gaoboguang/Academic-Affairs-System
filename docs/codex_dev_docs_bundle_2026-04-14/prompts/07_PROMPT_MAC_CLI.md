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
