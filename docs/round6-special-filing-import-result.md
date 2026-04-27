# 第六轮特殊类型投档表导入结果

- 生成时间：2026-04-27 09:48:32
- 数据范围：山东省 2023-2025 年艺术类、体育类、春季高考投档情况表官方附件。
- 写库边界：投档情况表只写 `gaokao_admission_result` raw 表和导入审计，不写 `admission_record`，避免把投档最低分包装成最终录取结果。

## 1. 执行摘要

- 已登记投档来源页面：15 个
- 成功解析附件：0 个
- raw 新增记录：0 条
- 应用侧录取结果新增：0 条
- 失败或待人工处理：15 项

## 2. 已导入附件

| 年份 | 类型 | 附件 | raw 行数 | 口径 | 本地文件 |
| --- | --- | --- | ---: | --- | --- |
| - | - | 本次没有成功导入附件 | 0 | - | - |

## 3. 失败或待处理清单

| 年份 | 类型 | 来源/附件 | URL | 原因 |
| --- | --- | --- | --- | --- |
| 2023 | art_filing_result | 山东省2023年艺术本科批统考第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6278 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2023 | art_filing_result | 山东省2023年艺术类专科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6315 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2023 | sports_filing_result | 山东省2023年体育类常规批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6276 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2023 | spring_exam_filing_result | 山东省2023年春季高考本科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6277 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2023 | spring_exam_filing_result | 山东省2023年春季高考专科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6312 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2024 | art_filing_result | 山东省2024年艺术类本科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6652 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2024 | art_filing_result | 山东省2024年艺术类专科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6672 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2024 | sports_filing_result | 山东省2024年体育类常规批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6651 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2024 | spring_exam_filing_result | 山东省2024年春季高考本科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6650 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2024 | spring_exam_filing_result | 山东省2024年春季高考专科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6669 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2025 | art_filing_result | 山东省2025年艺术类本科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6986 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2025 | art_filing_result | 山东省2025年艺术类专科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=7009 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2025 | sports_filing_result | 山东省2025年体育类常规批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6985 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2025 | spring_exam_filing_result | 山东省2025年春季高考本科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=6984 | 本地未找到已下载附件，且本次使用 --no-download。 |
| 2025 | spring_exam_filing_result | 山东省2025年春季高考专科批第1次志愿投档情况表 | https://www.sdzk.cn/NewsInfo.aspx?NewsID=7007 | 本地未找到已下载附件，且本次使用 --no-download。 |

## 4. 当前 raw 覆盖

| 年份 | 类型 | 批次 | raw 行数 |
| --- | --- | --- | ---: |
| 2023 | 普通类 | 常规批 | 29760 |
| 2024 | 普通类 | 常规批 | 31755 |
| 2025 | 体育类 | 体育类常规批 | 393 |
| 2025 | 春季高考 | 春季高考本科批 | 340 |
| 2025 | 普通类 | 常规批 | 34303 |
| 2025 | 艺术类 | 艺术类本科批 | 3403 |

## 5. 后续边界

1. 若本机无法访问 `sdzk.cn/Floadup`，需在网络恢复后复跑本脚本，或把官方附件放入 `data/imports/gaokao/official/{year}/` 后加 `--no-download` 复跑。
2. 2023/2024 艺术、体育、春考若仍只找到投档表而未找到录取情况表，不能关闭“专门录取结果缺口”。
3. 单独招生、综合评价招生缺专门录取结果的风险边界不因本脚本改变。
