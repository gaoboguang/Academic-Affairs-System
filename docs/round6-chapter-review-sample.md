# 第六轮章程限制链辅助预审样本

- 日期：2026-04-27
- 数据来源：`gaokao_college_chapter_rule`
- 边界：本报告只整理机器预审样本，不自动修改 `review_status`。

## 1. 当前状态

第五轮已对 500 条候选链接做机器连通性预审：

| 状态 | 数量 | 处理原则 |
| --- | ---: | --- |
| `round5_machine_reachable` | 18 | 人工优先打开确认是否为招生官网 / 章程栏目 |
| `round5_machine_timeout` | 463 | 网络稳定后复跑或人工打开，不可自动确认 |
| `round5_machine_error` | 13 | 保留错误原因，后续人工复核 |
| `round5_machine_not_found` | 4 | 人工确认前不关闭 |
| `round5_machine_http_444` | 1 | 视为站点阻断或异常，不自动确认 |
| `round5_machine_http_502` | 1 | 视为临时异常，不自动确认 |

`backend:data-health` 仍显示章程限制链待人工复核 1748 条。

## 2. 可优先人工复核样本

| rule_id | 院校 | 候选链接 | 当前机器状态 |
| ---: | --- | --- | --- |
| 8 | 三峡大学 | http://zs.ctgu.edu.cn/ | `round5_machine_reachable` |
| 91 | 东营职业学院 | https://www.dyxy.net/zsb/ | `round5_machine_reachable` |
| 214 | 冀中职业学院 | http://www.jzhxy.com/zsb/ | `round5_machine_reachable` |
| 350 | 南京邮电大学通达学院 | http://www.tdxy.com.cn/zsb/ | `round5_machine_reachable` |
| 374 | 南昌航空大学科技学院 | http://www.nckjxy.cn/zsb/ | `round5_machine_reachable` |
| 521 | 四川水利职业技术学院 | http://www.swcvc.net.cn/zsb/ | `round5_machine_reachable` |
| 562 | 大连理工大学城市学院 | http://www.dl-city.com/zsb/ | `round5_machine_reachable` |
| 590 | 天津天狮学院 | https://www.tianshi.edu.cn/zsjy1.htm | `round5_machine_reachable` |
| 724 | 山东文化产业职业学院 | http://www.sdcivc.com/zsb/ | `round5_machine_reachable` |
| 736 | 山东畜牧兽医职业学院 | http://www.sdmyxy.cn/zsb/ | `round5_machine_reachable` |

## 3. 第六轮建议

1. 先人工核对 18 条 `round5_machine_reachable`，确认是否确为招生官网入口、招生章程栏目或 2025 招生章程页面。
2. 对确认有效的记录，后续应由人工流程更新 `review_status`，并保留确认时间、确认人和证据 URL。
3. 超时、404、444、502、异常页面都不得自动改为已确认。

