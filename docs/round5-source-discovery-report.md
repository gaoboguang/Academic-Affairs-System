# 第五轮阶段 1 官方来源发现报告

- 日期：2026-04-26
- 执行阶段：阶段 1，官方来源发现和登记
- 主库：`data/app.db`
- 边界：本报告只记录已发现和已登记的官方来源；已登记不等于已结构化导入。不能自动下载或解析的来源仍需进入人工下载 / 复核清单。

## 1. 来源登记结果

阶段 0 基线：

| 项目 | 基线数量 |
| --- | ---: |
| `gaokao_source_document` | 29 |
| `gaokao_import_run` | 15 |

本阶段后：

| 项目 | 当前数量 | 增量 |
| --- | ---: | ---: |
| `gaokao_source_document` | 67 | +38 |
| `gaokao_import_run` | 21 | +6 |

其中：

- 新增 6 个普通类常规批第 2/3 次志愿投档来源，并下载官方 XLS 文件，登记 SHA256。
- 新增 32 个艺术、体育、春考、政策、百问百答和招生计划补充信息来源，状态为 `registered`，后续再决定下载、解析和写表方式。

## 2. 普通类常规批投档来源

2023-2025 普通类常规批第 1/2/3 次志愿投档情况表均已可追溯到 `source_document_id`。

| 年份 | 轮次 | source_document_id | import_run_id | raw 行数 | 来源 |
| --- | --- | ---: | ---: | ---: | --- |
| 2023 | 第 1 次 | 3 | 3 | 19230 | [山东省2023年普通类常规批第1次志愿投档情况表](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6279) |
| 2023 | 第 2 次 | 30 | 16 | 10355 | [山东省2023年普通类常规批第2次志愿投档情况表](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6313) |
| 2023 | 第 3 次 | 31 | 17 | 175 | [山东省2023年普通类常规批第3次志愿投档情况表](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6321) |
| 2024 | 第 1 次 | 2 | 2 | 20300 | [山东省2024年普通类常规批第1次志愿投档情况表](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6656) |
| 2024 | 第 2 次 | 32 | 18 | 11319 | [山东省2024年普通类常规批第2次志愿投档情况表](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6670) |
| 2024 | 第 3 次 | 33 | 19 | 136 | [山东省2024年普通类常规批第3次志愿投档情况表](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6682) |
| 2025 | 第 1 次 | 1 | 1 | 21381 | [山东省2025年普通类常规批第1次志愿投档情况表](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6996) |
| 2025 | 第 2 次 | 34 | 20 | 12160 | [山东省2025年普通类常规批第2次志愿投档情况表](https://www.sdzk.cn/NewsInfo.aspx?NewsID=7010) |
| 2025 | 第 3 次 | 35 | 21 | 762 | [山东省2025年普通类常规批第3次志愿投档情况表](https://www.sdzk.cn/NewsInfo.aspx?NewsID=7019) |

本阶段只挂接既有 raw 投档行来源，不重算应用侧 `admission_record`。原因是应用侧 `admission_record` 没有 `round_no` 字段，不能同时表达第 1/2/3 次投档来源；全轮次追溯应以 `gaokao_admission_result` raw 表为准。

## 3. 艺术、体育、春考投档来源

已登记以下山东省教育招生考试院官方页面，后续优先下载附件并评估是否新增 `gaokao_admission_min_score` 等辅助表。

| 年份 | 类型 | 来源 |
| --- | --- | --- |
| 2025 | 艺术类本科批第 1 次投档 | [NewsID=6986](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6986) |
| 2025 | 艺术类专科批第 1 次投档 | [NewsID=7009](https://www.sdzk.cn/NewsInfo.aspx?NewsID=7009) |
| 2025 | 体育类常规批第 1 次投档 | [NewsID=6985](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6985) |
| 2025 | 春季高考本科批第 1 次投档 | [NewsID=6984](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6984) |
| 2025 | 春季高考专科批第 1 次投档 | [NewsID=7007](https://www.sdzk.cn/NewsInfo.aspx?NewsID=7007) |
| 2024 | 艺术类本科批第 1 次投档 | [NewsID=6652](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6652) |
| 2024 | 艺术类专科批第 1 次投档 | [NewsID=6672](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6672) |
| 2024 | 体育类常规批第 1 次投档 | [NewsID=6651](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6651) |
| 2024 | 春季高考本科批第 1 次投档 | [NewsID=6650](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6650) |
| 2024 | 春季高考专科批第 1 次投档 | [NewsID=6669](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6669) |
| 2023 | 艺术本科批统考第 1 次投档 | [NewsID=6278](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6278) |
| 2023 | 艺术类专科批第 1 次投档 | [NewsID=6315](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6315) |
| 2023 | 体育类常规批第 1 次投档 | [NewsID=6276](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6276) |
| 2023 | 春季高考本科批第 1 次投档 | [NewsID=6277](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6277) |
| 2023 | 春季高考专科批第 1 次投档 | [NewsID=6312](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6312) |

## 4. 录取情况表 / 录取最低分来源

官网检索当前明确命中的“录取情况表”集中在 2025 年：

| 年份 | 类型 | 来源 |
| --- | --- | --- |
| 2025 | 艺术类本科批第 1 次志愿录取情况表 | [NewsID=6989](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6989) |
| 2025 | 体育类常规批第 1 次志愿录取情况表 | [NewsID=6987](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6987) |
| 2025 | 春季高考本科批第 1 次志愿录取情况表 | [NewsID=6988](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6988) |

2023 / 2024 同名“艺术类本科批第1次志愿录取情况表”“体育类常规批第1次志愿录取情况表”“春季高考本科批第1次志愿录取情况表”未在本轮官网检索结果中命中，暂列为待进一步人工复核，不伪造为已发布。

## 5. 政策参考来源

已登记 2023-2025 录取工作意见、志愿填报百问百答和考试政策百问百答，并已通过 `scripts/round5_import_policy_references.py` 写入 `gaokao_policy_reference`。当前政策参考总数为 13 条，`backend:data-health` 不再把政策参考数量列为 P0 缺口。

| 年份 | 来源类型 | 来源 |
| --- | --- | --- |
| 2025 | 录取工作意见 | [NewsID=6928](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6928) |
| 2024 | 录取工作意见 | [NewsID=6547](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6547) |
| 2023 | 录取工作意见 | [NewsID=6205](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6205) |
| 2025 | 志愿填报百问百答 | [NewsID=6956](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6956) |
| 2025 | 招生考试政策百问百答 | [NewsID=6871](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6871) |
| 2024 | 志愿填报百问百答 | [NewsID=6591](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6591) |
| 2024 | 招生考试政策百问百答 | [NewsID=6503](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6503) |
| 2023 | 志愿填报百问百答 | [NewsID=6229](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6229) |
| 2023 | 招生考试政策百问百答 | [NewsID=6099](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6099) |

## 6. 招生计划来源

本轮官网检索未发现可直接公开下载的完整《填报志愿指南》本科 / 专科原始附件，只发现计划补充信息、专科层次补充信息和后续志愿计划页面。

已登记的计划补充信息：

| 年份 | 来源 |
| --- | --- |
| 2025 | [山东省2025年普通高等学校分专业招生计划补充信息](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6955) |
| 2025 | [山东省2025年普通高等学校专科层次分专业招生计划补充信息](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6990) |
| 2024 | [山东省2024年普通高等学校分专业招生计划补充信息](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6611) |
| 2024 | [山东省2024年普通高等学校专科层次分专业招生计划补充信息](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6661) |
| 2023 | [山东省2023年普通高等学校分专业招生计划补充信息](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6222) |

注意：补充信息不是完整招生计划，不能直接用于关闭 2023 缺计划或 2024 计划偏少告警。完整计划仍需用户提供官方《填报志愿指南》、志愿填报辅助系统导出或可核验官方完整附件。
