# 第五轮章程限制链机器预审

- 生成时间：2026-04-27 08:52:30
- 主库：`data/app.db`
- 边界：机器预审只记录候选链接连通性，不把待人工复核项改为人工已确认。

## 1. 汇总

- 本批处理：50 条
- `round5_machine_error`：1 条
- `round5_machine_reachable`：2 条
- `round5_machine_timeout`：47 条

## 2. 明细

| ID | 院校 | 原状态 | 候选来源 | 机器状态 | HTTP | 候选链接 |
| ---: | --- | --- | --- | --- | ---: | --- |
| 3 | 三亚城市职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sycsxy.cn/col.jsp?id=110 |
| 4 | 三亚学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.sanyau.edu.cn/ |
| 6 | 三亚理工职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.ucsanya.com/zsjy.asp?did=66&id=69 |
| 7 | 三亚航空旅游职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.hnasatc.edu.cn/ |
| 8 | 三峡大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://zs.ctgu.edu.cn/ |
| 9 | 三峡大学科技学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://kjxy.ctgu.edu.cn/zs_zz_/sy.htm |
| 12 | 三明学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zjc.fjsmu.edu.cn/main.htm |
| 15 | 三门峡职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsw.smxpt.edu.cn |
| 21 | 上海交通职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.scp.edu.cn/list.aspx?nid=292&cid=476 |
| 25 | 上海出版印刷高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sppc.edu.cn/zs/ |
| 28 | 上海城建职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.succ.edu.cn/zsxx/ |
| 30 | 上海外国语大学贤达经济人文学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaoban.xdsisu.edu.cn/ |
| 32 | 上海对外经贸大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.suibe.edu.cn/ |
| 33 | 上海工商外国语职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.sicfl.edu.cn/ |
| 36 | 上海工艺美术职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sada.edu.cn/ch/zsjy_2503/list.htm |
| 37 | 上海师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.shnu.edu.cn/43/list.htm |
| 38 | 上海师范大学天华学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sthu.cn/zsrydsz/list.htm |
| 43 | 上海戏剧学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.sta.edu.cn/ |
| 44 | 上海政法学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.shupl.edu.cn/ |
| 46 | 上海杉达学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sandau.edu.cn:443/zsjy/ |
| 48 | 上海民远职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://azs.shmy.edu.cn/ |
| 49 | 上海济光职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.shjgu.edu.cn/ |
| 57 | 上海电子信息职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.stiei.edu.cn/zsb/main.psp |
| 61 | 上海科学技术职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.scst.edu.cn/zsb/main.psp |
| 62 | 上海立信会计金融学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.lixin.edu.cn/zsdw.htm |
| 64 | 上海第二工业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sspu.edu.cn/2025/1212/c3024a166805/page.htm |
| 65 | 上海行健职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.shxj.edu.cn/zsxxw/main.htm |
| 71 | 上海震旦职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.aurora-college.cn/580/list.htm |
| 75 | 上饶职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.srzy.cn/ |
| 83 | 东北财经大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.dufe.edu.cn/ |
| 87 | 东南大学成贤学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.cxxy.seu.edu.cn/ |
| 88 | 东莞城市学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsw.dgcu.edu.cn/newslist.php?catid=151 |
| 89 | 东莞理工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.dgut.edu.cn/ |
| 91 | 东营职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | https://www.dyxy.net/zsb/ |
| 111 | 中国民用航空飞行学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.cafuc.edu.cn/zsjy.htm |
| 112 | 中国民航大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.cauc.edu.cn/zhv5/zsjy.htm |
| 119 | 中国矿业大学徐海学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://xhxy.cumt.edu.cn/zsjy/list.htm |
| 137 | 丽水学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsw.lsu.edu.cn/ |
| 139 | 丽江文化旅游学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.lywhxy.com/ |
| 140 | 乌鲁木齐职业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.uvu.edu.cn |
| 145 | 九江职业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.jjvu.jx.cn/ |
| 149 | 云南农业职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.ynavc.com/ |
| 150 | 云南医药健康职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsw.ynmhc.com/ |
| 151 | 云南国土资源职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | http://www.yngtxy.net/yngtxy/default.html;jsessionid=A98BABEEFC0722CB9A10D8205957F13E/zsb/ |
| 152 | 云南城市建设职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://gzkz.yncjxy.edu.cn |
| 153 | 云南外事外语职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsjy.fafl.cn |
| 155 | 云南工商学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.ytbu.edu.cn/ |
| 156 | 云南工程职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.ynenc.cn/zskx/888.html |
| 158 | 云南新兴职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.ynxzy.com/view/mainzsb/5/65/view/11018.html |
| 159 | 云南林业职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.ynftc.edu.cn/zsxxw |

## 3. 后续建议

1. 对 `round5_machine_reachable` 的记录，下一步仍需人工打开页面并确认是否为招生章程或招生官网入口。
2. 对超时、SSL 错误或访问异常的记录，不应改为已确认；可在网络环境更稳定时复跑本脚本。
3. 只有找到明确招生章程页面、PDF 或高校招生网对应章程栏目后，才能进入人工确认状态。
