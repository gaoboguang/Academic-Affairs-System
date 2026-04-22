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
