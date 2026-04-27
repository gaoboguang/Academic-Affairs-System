# 第五轮章程限制链机器预审错误清单

- 日期：2026-04-27
- 主库：`data/app.db`
- 范围：已机器预审的 500 条候选链接中非可访问记录。

## 1. 错误汇总

| 状态 | 数量 | 后续处理 |
| --- | ---: | --- |
| `round5_machine_timeout` | 463 | 稳定网络后复跑，或人工打开核对 |
| `round5_machine_error` | 13 | 人工打开核对链接格式、跳转和官网入口 |
| `round5_machine_not_found` | 4 | 人工搜索高校新招生网或章程栏目 |
| `round5_machine_http_444` | 1 | 可能被站点拒绝，人工浏览器复核 |
| `round5_machine_http_502` | 1 | 站点临时错误，稍后复跑 |

## 2. 明确 HTTP 错误和访问异常

| 状态 | ID | 院校 | 候选链接 |
| --- | ---: | --- | --- |
| `round5_machine_error` | 151 | 云南国土资源职业学院 | http://www.yngtxy.net/yngtxy/default.html;jsessionid=A98BABEEFC0722CB9A10D8205957F13E/zsb/ |
| `round5_machine_error` | 369 | 南昌应用技术师范学院 | http://www.jxstnupi.cn/zsb/ |
| `round5_machine_error` | 592 | 天津工业职业学院 | http://zs.tjmvti.cn/ |
| `round5_machine_error` | 617 | 太原幼儿师范高等专科学校 | http://www.tyyouzhuan.com/zsb/ |
| `round5_machine_error` | 643 | 安徽交通职业技术学院 | http://www.ahctc.com/zsb/ |
| `round5_machine_error` | 717 | 山东工业职业学院 | http://www.sdivc.net.cn/zsb/ |
| `round5_machine_error` | 759 | 山西信息职业技术学院 | https://www.vcit.cn/col.jsp?id=119 |
| `round5_machine_error` | 780 | 山西能源学院 | https://zs.sxmtxy.net/ |
| `round5_machine_error` | 920 | 成都锦城学院 | http://www.scujcc.com.cn/zsb/ |
| `round5_machine_error` | 997 | 景德镇艺术职业大学 | https://zs.jci-ky.cn/ |
| `round5_machine_error` | 1097 | 江苏安全技术职业学院 | http://www.jsvist.com/zsb/ |
| `round5_machine_error` | 1137 | 江西建设职业技术学院 | http://www.jxjsxy.com/index_v.aspx/zsb/ |
| `round5_machine_error` | 1175 | 沈阳师范大学 | https://zs.synu.edu.cn/ |
| `round5_machine_http_444` | 1067 | 武汉航海职业技术学院 | http://zs.2hhxy.com/ |
| `round5_machine_http_502` | 800 | 广东东软学院 | https://www.nuit.edu.cn/zsxxw |
| `round5_machine_not_found` | 817 | 广东茂名幼儿师范专科学校 | http://www.gdgzsf.cn/zsb/ |
| `round5_machine_not_found` | 900 | 忻州职业技术学院 | http://www.xzvtc.net/bkzs/ |
| `round5_machine_not_found` | 1183 | 沧州交通学院 | http://zsb.bjtuhbxy.cn/ |
| `round5_machine_not_found` | 1214 | 河北旅游职业学院 | http://www.cdtvc.com/zsb/ |

## 3. 超时记录处理原则

463 条超时记录未逐条展开到本文，完整机器明细保留在 `docs/round5-chapter-machine-preaudit.md` 和主库 `chapter_fallback_note` 中。超时不等于官网不存在，不得直接清空候选链接或关闭人工复核状态。

