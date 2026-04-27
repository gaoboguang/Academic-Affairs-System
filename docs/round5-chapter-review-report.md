# 第五轮章程限制链机器预审汇总报告

- 日期：2026-04-27
- 主库：`data/app.db`
- 脚本：`scripts/round5_chapter_machine_preaudit.py`
- 最新备份：`data/backups/app_before_round5_chapter_machine_preaudit_20260427_090600.db`
- 边界：本报告只记录机器连通性预审，不代表人工确认，也不把任何记录标记为 `confirmed_manual_review`。

## 1. 处理结果

本轮累计对 `gaokao_college_chapter_rule` 中已有候选招生官网链接的待复核记录预审 500 条。

| 机器状态 | 数量 | 含义 |
| --- | ---: | --- |
| `round5_machine_reachable` | 18 | 当前网络下 HTTP 可访问，仍需人工确认页面是否为招生官网或章程栏目 |
| `round5_machine_timeout` | 463 | 当前网络下超时或 SSL 握手超时，不能据此判断官网不存在 |
| `round5_machine_error` | 13 | 访问异常，需要人工或稳定网络复核 |
| `round5_machine_not_found` | 4 | HTTP 404，候选链接疑似失效 |
| `round5_machine_http_444` | 1 | 站点拒绝或关闭连接 |
| `round5_machine_http_502` | 1 | 网关错误 |

## 2. 可人工优先核对的记录

以下 18 条机器可访问，下一步应人工打开并确认是否为招生官网、招生信息网或招生章程栏目。确认前不得改 `review_status`。

| ID | 院校 | 候选链接 |
| ---: | --- | --- |
| 8 | 三峡大学 | http://zs.ctgu.edu.cn/ |
| 91 | 东营职业学院 | https://www.dyxy.net/zsb/ |
| 214 | 冀中职业学院 | http://www.jzhxy.com/zsb/ |
| 350 | 南京邮电大学通达学院 | http://www.tdxy.com.cn/zsb/ |
| 374 | 南昌航空大学科技学院 | http://www.nckjxy.cn/zsb/ |
| 521 | 四川水利职业技术学院 | http://www.swcvc.net.cn/zsb/ |
| 562 | 大连理工大学城市学院 | http://www.dl-city.com/zsb/ |
| 590 | 天津天狮学院 | https://www.tianshi.edu.cn/zsjy1.htm |
| 724 | 山东文化产业职业学院 | http://www.sdcivc.com/zsb/ |
| 736 | 山东畜牧兽医职业学院 | http://www.sdmyxy.cn/zsb/ |
| 758 | 山西传媒学院 | http://www.arft.net/zsb/ |
| 768 | 山西工程科技职业大学 | http://www.sxdxswxy.com/zsb/ |
| 835 | 广州民航职业技术学院 | http://www.caac.net/zsb/ |
| 840 | 广州软件学院 | http://www.sise.com.cn/zsb/ |
| 871 | 广西财经学院 | http://www.gxufe.cn/www/myweb/home.cdi/zsb/ |
| 894 | 德州科技职业学院 | http://www.sddzkj.com/zsb/ |
| 928 | 承德护理职业学院 | http://www.cdwx.cn/zsb/ |
| 1142 | 江西枫林涉外经贸职业学院 | http://www.fenglin.org/zsb/ |

## 3. 未关闭的缺口

- `review_status` 未做任何自动确认，仍有 1748 条章程记录待人工复核。
- 还有 949 条已有候选链接的待复核记录未机器预审。
- 超时和异常主要受高校网站响应慢、SSL 握手、反爬或当前网络环境影响，不能直接删除或判定无效。
- 后续人工确认时应补充证据 URL、页面标题、摘录文本、置信度和人工建议，再进入确认状态。

