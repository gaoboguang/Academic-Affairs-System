# Handoffs 导航

这个目录放的是外部接管包、数据库交接材料和随包工具，不是应用主源码目录。

## 当前接入包

- [`2026-04-21_mac_db_handoff/`](./2026-04-21_mac_db_handoff/)
  当前已经接入项目运行约定的一组高考数据库 handoff 材料。

## 使用前先知道

- 应用主库仍是 `data/app.db`。
- `data/local_edu_tool/local_edu.sqlite3` 当前仍可指向 handoff 包内快照，但从 2026-04-22 起，它更适合作为“同步来源 / fallback 输入”。
- 若已执行 `npm run backend:merge-handoff` 把 handoff 的 `gaokao_*` 原始表并入 `data/app.db`，应用会优先走单库，不再强依赖独立高考库。
- 不要把 handoff 包里的数据库直接当成应用主库替换；优先走“并入 app.db”而不是“替换 app.db”。

## 建议阅读顺序

1. 先看 handoff 包自己的 `README.md`
2. 再看根目录 `memory-bank/active-context.md` 和 `memory-bank/handoff.md`
3. 最后再决定是否进入 handoff 包的 `tools/`、`docs/`、`reference/`

## 目录边界

- `database/`
  交接数据库快照或相关文件。
- `docs/`
  接管说明和审计材料。
- `tools/`
  交接包附带工具，执行前先确认当前运行入口仍指向正确数据库。
- `metrics/`、`reference/`
  审计结果、参考输出或静态资料。

## 整理约定

- 新的 handoff 包继续按日期或批次单独建目录，不要把不同来源的交接材料混到一起。
- 运行入口、软链接或环境变量变化，优先回写到根目录 `README.md` 和 `memory-bank/`，不要只写在 handoff 包内部。
