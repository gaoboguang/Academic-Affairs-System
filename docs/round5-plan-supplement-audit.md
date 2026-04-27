# 第五轮招生计划补充信息附件审计

- 生成时间：2026-04-27 08:47:02
- 主库：`data/app.db`
- 边界：本报告记录山东省教育招生考试院补充信息附件的下载、登记和读取结果；补充信息不是完整《填报志愿指南》，本轮不据此关闭招生计划完整性缺口。

## 1. 附件登记结果

| 年份 | source_document_id | 附件 | 表格数 | 表格行数 | SHA256 |
| --- | ---: | --- | ---: | ---: | --- |

## 2. 下载失败或待人工处理

| 年份 | 附件 | 失败原因 | 下一步 |
| --- | --- | --- | --- |
| 2023 | [山东省2023年普通高等学校分专业招生计划补充信息](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6222) | <urlopen error _ssl.c:1063: The handshake operation timed out> | 人工下载 `https://www.sdzk.cn/Floadup/file/20230627/6382348029376827184337893.docx` 后复跑脚本 |
| 2024 | [山东省2024年普通高等学校分专业招生计划补充信息](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6611) | <urlopen error _ssl.c:1063: The handshake operation timed out> | 人工下载 `https://www.sdzk.cn/Floadup/file/20240627/6385516213636230688036970.docx` 后复跑脚本 |
| 2024 | [山东省2024年普通高等学校专科层次分专业招生计划补充信息](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6661) | <urlopen error _ssl.c:1063: The handshake operation timed out> | 人工下载 `https://www.sdzk.cn/Floadup/file/20240722/6385726159356393297171291.docx` 后复跑脚本 |
| 2025 | [山东省2025年普通高等学校分专业招生计划补充信息](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6955) | <urlopen error _ssl.c:1063: The handshake operation timed out> | 人工下载 `https://www.sdzk.cn/Floadup/file/20250627/6388661855703111824442516.docx` 后复跑脚本 |
| 2025 | [山东省2025年普通高等学校专科层次分专业招生计划补充信息](https://www.sdzk.cn/NewsInfo.aspx?NewsID=6990) | <urlopen error _ssl.c:1063: The handshake operation timed out> | 人工下载 `https://www.sdzk.cn/Floadup/file/20250719/6388854771364040035069196.docx` 后复跑脚本 |

## 3. 机器读取摘要

## 4. 后续建议

1. 继续寻找或由用户提供 2023-2025 完整《山东省普通高校招生填报志愿指南》或志愿填报辅助系统官方导出。
2. 若后续要把补充信息合并到计划表，应先和完整计划做差异合并，保留原始计划、补充项、变更原因和来源附件。
3. 当前 `2024 山东招生计划数量偏少` 告警不能因补充信息已登记而关闭。
