# 第五轮章程限制链机器预审

- 生成时间：2026-04-27 09:07:00
- 主库：`data/app.db`
- 边界：机器预审只记录候选链接连通性，不把待人工复核项改为人工已确认。

## 1. 汇总

- 本批处理：450 条
- `round5_machine_error`：12 条
- `round5_machine_http_444`：1 条
- `round5_machine_http_502`：1 条
- `round5_machine_not_found`：4 条
- `round5_machine_reachable`：16 条
- `round5_machine_timeout`：416 条

## 2. 明细

| ID | 院校 | 原状态 | 候选来源 | 机器状态 | HTTP | 候选链接 |
| ---: | --- | --- | --- | --- | ---: | --- |
| 165 | 云南艺术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.ynart.edu.cn |
| 167 | 云南财经大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.ynufe.edu.cn/jgsz/zsdw.htm |
| 169 | 井冈山大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://xkjs.jgsu.edu.cn/zsjy/tzgg.htm |
| 170 | 亳州学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.bzuu.edu.cn/zzxx/ |
| 173 | 伊春职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.ycvc.com.cn/zsjy1.htm |
| 175 | 伊犁职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.ylzyjs.cn/zsw/ |
| 178 | 佳木斯职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.jmszy.org.cn/e/action/ShowInfo.php?classid=4&id=11914 |
| 187 | 信阳涉外职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.xyswxy.com/ |
| 192 | 六安职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsw.lvtc.edu.cn |
| 195 | 六盘水职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.lpszy.cn/zsjy1/zsxx.htm |
| 196 | 兰州交通大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.lzjtu.edu.cn/ |
| 199 | 兰州城市学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.lzcu.edu.cn/ |
| 200 | 兰州外语职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.lzwyedu.com/zsxx/ |
| 208 | 兰州科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.lzkjedu.com/ |
| 209 | 兰州职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://admission.lvu.edu.cn/ |
| 214 | 冀中职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.jzhxy.com/zsb/ |
| 217 | 内江职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.njvtc.edu.cn |
| 220 | 内蒙古北方职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.nmbfxy.com/channels/29.html |
| 221 | 内蒙古医科大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.immu.edu.cn/zsjy.htm |
| 223 | 内蒙古大学创业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.imuchuangye.cn/zhaosheng/ |
| 225 | 内蒙古师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.imnu.edu.cn/sy.htm |
| 226 | 内蒙古民族大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.imun.edu.cn/xxgk1/zsks.htm |
| 229 | 内蒙古科技大学包头师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsw.bttc.edu.cn/ |
| 230 | 内蒙古艺术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://fz.imac.edu.cn/html-fz/zsgz/ |
| 232 | 凯里学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.kluniv.edu.cn/xxfwdh1/zsfw.htm |
| 233 | 包头职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zhaosheng.btvtc.cn/ |
| 239 | 北京交通职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.jtxy.com.cn/zsjy1/zsxx.htm |
| 240 | 北京京北职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://jbzy.com.cn/lists/23.html |
| 243 | 北京信息职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.bitc.edu.cn/zsxx/ |
| 247 | 北京北大方正软件职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.pfc.edu.cn/Awebsite/Index.aspx/zsb/ |
| 251 | 北京培黎职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.bjpldx.edu.cn/zhaoshengwang |
| 256 | 北京工业大学耿丹学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.gengdan.cn |
| 260 | 北京师范大学(珠海校区) | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.bnuz.edu.cn/ |
| 261 | 北京建筑大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.bucea.edu.cn/ |
| 269 | 北京石油化工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.bipt.edu.cn/ |
| 271 | 北京科技大学天津学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://tj.ustb.edu.cn/zsw/ |
| 274 | 北京科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsw.5aaa.com/zsbm.html |
| 279 | 北京经贸职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.csuedu.com/zsb/ |
| 280 | 北京网络职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.bjwlxy.org.cn/zhaoshengg/#/pages/index/index |
| 282 | 北京舞蹈学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.bda.edu.cn/zsjy/bkzsxx/index.htm |
| 285 | 北京语言大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.blcu.edu.cn/zsjy.htm |
| 286 | 北京财贸职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.bjczy.edu.cn/folder26 |
| 288 | 北华大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.beihua.edu.cn/zzjg/zsdw.htm |
| 289 | 北华航天工业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zb.nciae.edu.cn/ |
| 294 | 北海职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.bhzyxy.edu.cn/zjc/ |
| 295 | 北海艺术设计学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sszss.com/bkzs/index.htm?site_id=2 |
| 297 | 华东交通大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zjc.ecjtu.edu.cn |
| 306 | 华北理工大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsjyc.ncst.edu.cn/ |
| 307 | 华北理工大学轻工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.qgxy.cn/contents/755/7623.html |
| 310 | 华北科技学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsjy.ncist.edu.cn/ |
| 315 | 南京交通职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.njitt.edu.cn |
| 319 | 南京信息职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.njcit.cn/ |
| 323 | 南京城市职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.ncc.edu.cn/zsksxx/list.htm |
| 325 | 南京审计大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.nau.edu.cn/ |
| 329 | 南京工业职业技术大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.niit.edu.cn |
| 330 | 南京工程学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.njit.edu.cn/ |
| 333 | 南京师范大学泰州学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://bkzs.nnutc.edu.cn/ |
| 335 | 南京晓庄学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.njxzc.edu.cn |
| 340 | 南京理工大学泰州科技学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.nustti.edu.cn/default/ |
| 350 | 南京邮电大学通达学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.tdxy.com.cn/zsb/ |
| 351 | 南京铁道职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://ntyzs.njrts.edu.cn |
| 354 | 南华大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://csxy.usc.edu.cn/zsjy.htm |
| 355 | 南华大学船山学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://csxy.usc.edu.cn/zsjy.htm |
| 358 | 南宁理工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsc.bwgl.cn:443/ |
| 369 | 南昌应用技术师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | http://www.jxstnupi.cn/zsb/ |
| 371 | 南昌理工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.nut.edu.cn |
| 374 | 南昌航空大学科技学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.nckjxy.cn/zsb/ |
| 377 | 南通师范高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zjc.ntnc.edu.cn/ |
| 379 | 南通科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.ntst.edu.cn/ |
| 389 | 厦门兴才职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.xmxc.com/ |
| 391 | 厦门华厦学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.hxxy.edu.cn |
| 393 | 厦门南洋职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsjy.ny2000.com/ |
| 396 | 厦门大学嘉庚学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.xujc.com/2025/0615/c2245a160590/page.htm |
| 397 | 厦门安防科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.xmafkj.com/zsw |
| 405 | 合肥城市学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.ahjzu.edu.cn/cjxy/zsb/main.psp |
| 412 | 合肥通用职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hftyxy.com/zs/www/index.asp |
| 415 | 吉安职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://swzx.japt.com.cn/zswz/#/index |
| 417 | 吉林体育学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsjy.jlsu.edu.cn/zsgz.htm |
| 418 | 吉林农业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.jlau.edu.cn:443/zsjy.htm |
| 422 | 吉林医药学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.jlmu.cn/zsjy1.htm |
| 427 | 吉林工商学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsxxw.jlbtc.edu.cn/ |
| 435 | 吉林科技职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zb.jilinkj.com/ |
| 436 | 吉林职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.jlhtedu.com/zsjy/jzzs/gzjx.htm |
| 447 | 周口师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.zknu.edu.cn/ |
| 449 | 呼伦贝尔学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsjy.hlbec.edu.cn |
| 450 | 呼伦贝尔职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.hlbrzy.com |
| 451 | 呼和浩特民族学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.imnc.edu.cn/zs/ |
| 455 | 咸宁职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaoban.xnec.cn/ |
| 458 | 哈尔滨传媒职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hrbmcc.com/zhaoshengxinxi/ |
| 460 | 哈尔滨信息工程学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zb.greathiit.com/ |
| 464 | 哈尔滨商业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hrbcu.edu.cn/zsjy.htm |
| 470 | 哈尔滨师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hrbnu.edu.cn/xxgk/xxjj.htm |
| 471 | 哈尔滨应用职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hyyzy.com/zsw/ |
| 475 | 哈尔滨科学技术职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hrbkjzy.org.cn/qsxxw |
| 478 | 哈尔滨铁道职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.htxy.net/zsjy/zsxx.htm |
| 481 | 唐山师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.tstc.edu.cn/zskzslhjxzqzjgxxjy.htm |
| 495 | 嘉应学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.jyu.edu.cn/ |
| 497 | 四川交通职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsjyc.svtcc.edu.cn/ |
| 498 | 四川传媒学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zb.scmc.edu.cn/ |
| 500 | 四川化工职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sccc.edu.cn/zsjy1.htm |
| 501 | 四川华新现代职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.schxmvc.com.cn/zs.htm |
| 502 | 四川国际标榜职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://admission.polus.edu.cn |
| 503 | 四川城市职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.scuvc.com/ |
| 507 | 四川工商学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.stbu.edu.cn |
| 508 | 四川工商职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sctbc.net/zsjy1.htm |
| 510 | 四川师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.sicnu.edu.cn/ |
| 511 | 四川希望汽车职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.qicheedu.com/profession/zsc/index.html |
| 514 | 四川托普信息技术职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.scetop.com/html/zsc/list/4989 |
| 515 | 四川文化产业职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.svcci.cn/zsjy2.htm |
| 516 | 四川文化传媒职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.svccc.net/html/zsw/index.html |
| 519 | 四川文轩职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsbgs.scwxzyxy.cn/ |
| 520 | 四川旅游学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.sctu.edu.cn/zsjy1.htm |
| 521 | 四川水利职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.swcvc.net.cn/zsb/ |
| 522 | 四川汽车职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.scavtc.com/jiuye/list.aspx?categoryid=17 |
| 523 | 四川现代职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.scmvc.cn/ |
| 524 | 四川电子机械职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.scemvtc.com/subweb/zs/content/?550.html |
| 525 | 四川电影电视学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.sfc.edu.cn/ |
| 526 | 四川科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.scstc.cn/ |
| 530 | 四川西南航空职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.xnhkxy.edu.cn/ |
| 531 | 四川轻化工大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zjc.suse.edu.cn/ |
| 532 | 四川长江职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.sccvc.com/ |
| 542 | 大兴安岭职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.dxalu.org.cn/RecruitStudents/index.html |
| 544 | 大庆医学高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.dqygz.com/zsw/ |
| 545 | 大庆师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.dqsy.net/zsjy.htm |
| 549 | 大连东软信息学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.neusoft.edu.cn/ |
| 550 | 大连交通大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.djtu.edu.cn/Redirect?mid=53 |
| 554 | 大连工业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.dlpu.edu.cn/zsb/ |
| 559 | 大连海洋大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.dlou.edu.cn/2026/0408/c89a204498/page.htm |
| 562 | 大连理工大学城市学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.dl-city.com/zsb/ |
| 563 | 大连职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.dlvtc.edu.cn |
| 572 | 天津交通职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zhaosheng.tttc.edu.cn/ |
| 577 | 天津医学高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.tjyzh.cn/zsgz/zszc.htm |
| 579 | 天津医科大学临床医学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.tmucmc.edu.cn/zsxxw |
| 581 | 天津商业大学宝德学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.boustead.edu.cn |
| 582 | 天津商务职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.tcc1955.edu.cn/ |
| 588 | 天津外国语大学滨海外事学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://bhws.tjfsu.edu.cn/zsxx |
| 590 | 天津天狮学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | https://www.tianshi.edu.cn/zsjy1.htm |
| 592 | 天津工业职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | http://zs.tjmvti.cn/ |
| 594 | 天津师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://fxy.tjnu.edu.cn/zsjy/zsxx.htm |
| 595 | 天津机电职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsjy.suoyuan.com.cn/ |
| 596 | 天津海运职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.tjmc.edu.cn/zsjyzx/zsxx.htm |
| 598 | 天津滨海汽车工程职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.tqzyxy.com/app/school/intro.html?id=308 |
| 599 | 天津滨海职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.tjbpi.com/ |
| 600 | 天津现代职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsjy.tjmvtc.edu.cn/ |
| 603 | 天津生物工程职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.tjbio.cn/zhaosheng/zhaosheng.jsp |
| 604 | 天津电子信息职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.tjdz.edu.cn/a/recruit/?pageId=440850&wfwfid=142445&websiteId=152925 |
| 606 | 天津科技大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.tust.edu.cn/ |
| 607 | 天津美术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.tjarts.edu.cn/zsjy.htm |
| 609 | 天津艺术职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://enroll.arttj.cn |
| 610 | 天津财经大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.tjufe.edu.cn/info/1023/24061.htm |
| 611 | 天津财经大学珠江学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhujiang.tjufe.edu.cn/zsxjgl/main.htm |
| 612 | 天津轻工职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.tjlivtc.edu.cn/ |
| 615 | 太原工业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsxx.tit.edu.cn/ |
| 616 | 太原师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.tynu.edu.cn/zsgz.htm |
| 617 | 太原幼儿师范高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | http://www.tyyouzhuan.com/zsb/ |
| 629 | 宁夏建设职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.nxjy.edu.cn/zsjy1.htm |
| 630 | 宁夏理工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.nxist.com/zsw/ |
| 638 | 安康学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.aku.edu.cn |
| 639 | 安康职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.akvtc.cn/zsc/index.htm |
| 642 | 安徽中医药高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.ahzyygz.edu.cn:443/second/zsw |
| 643 | 安徽交通职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | http://www.ahctc.com/zsb/ |
| 644 | 安徽信息工程学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsxx.aiit.edu.cn/ |
| 646 | 安徽医科大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.ahmu.edu.cn/zsfsyy/list.htm |
| 648 | 安徽商贸职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.abc.edu.cn/zhaoshengxx/ |
| 649 | 安徽国防科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.acdt.edu.cn/zs/ |
| 650 | 安徽国际商务职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.ahiib.edu.cn/ |
| 653 | 安徽审计职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.ahsjxy.cn/ |
| 654 | 安徽工业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.ahut.edu.cn/ |
| 658 | 安徽建筑大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.ahjzu.edu.cn/zsw/ |
| 661 | 安徽新闻出版职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.ahcbxy.cn/ |
| 664 | 安徽科技学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.ahstu.edu.cn/zsc/ |
| 668 | 安徽财经大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsjy.aufe.edu.cn/ |
| 671 | 安阳师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.aynu.edu.cn/ |
| 674 | 安顺学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.asu.edu.cn/xxgk/zsks.htm |
| 679 | 宜春职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.ycvc.jx.cn/ |
| 688 | 宿迁职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sqzyxy.com/zs/ |
| 693 | 山东交通职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.sdjtzyxy.edu.cn |
| 699 | 山东力明科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://edu.6789.com.cn/zsjy/ |
| 700 | 山东劳动职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.sdlvtc.cn:8443 |
| 701 | 山东化工职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.sdhg.edu.cn/xxgk/zsks.htm |
| 702 | 山东医学高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsbgs.sdmc.edu.cn/ |
| 703 | 山东华宇工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.huayu.edu.cn |
| 704 | 山东协和学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sdxiehe.edu.cn/zs/ |
| 707 | 山东商务职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.sdbi.edu.cn |
| 713 | 山东外贸职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.sdwm.edu.cn/ |
| 717 | 山东工业职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | http://www.sdivc.net.cn/zsb/ |
| 720 | 山东工艺美术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.sdada.edu.cn/ |
| 724 | 山东文化产业职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.sdcivc.com/zsb/ |
| 728 | 山东水利职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.sdwcvc.cn/zs/ |
| 729 | 山东海事职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.sdmvc.edu.cn |
| 730 | 山东特殊教育职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.sdse.cn/zsjy/ |
| 734 | 山东电力高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sepc.edu.cn/html/dzwz/zsks.html |
| 735 | 山东电子职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.sdcet.edu.cn/zsxxw/main.htm |
| 736 | 山东畜牧兽医职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.sdmyxy.cn/zsb/ |
| 739 | 山东科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sdvcst.edu.cn/zsjy.htm |
| 742 | 山东管理学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.sdmu.edu.cn/ |
| 743 | 山东经贸职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.sdecu.com/zsc |
| 745 | 山东胜利职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.sdslvc.cn/ |
| 747 | 山东艺术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sdca.edu.cn:443/zsjy/zsxx.htm |
| 749 | 山东英才学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsw.sdycu.edu.cn/ |
| 752 | 山东财经大学东方学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.sdor.cn |
| 755 | 山东铝业职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://slxy.chinalco.com.cn/zsjy/ |
| 758 | 山西传媒学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.arft.net/zsb/ |
| 759 | 山西信息职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | https://www.vcit.cn/col.jsp?id=119 |
| 760 | 山西农业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.sxau.edu.cn/bkszs/sy.htm |
| 762 | 山西同文职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsjyc.sxtwedu.com/ |
| 763 | 山西大同大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.sxdtdx.edu.cn/news-list-zhaoshengjiuye1.html |
| 765 | 山西工商学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sxtbu.edu.cn/department/zsb/ |
| 767 | 山西工程技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sxit.edu.cn/zsjyc/ |
| 768 | 山西工程科技职业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.sxdxswxy.com/zsb/ |
| 774 | 山西水利职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsjy.sxsy.com.cn/ |
| 777 | 山西管理职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.sxglzyxy.com.cn/zsjyc |
| 778 | 山西老区职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsjy.sxlqzy.cn |
| 780 | 山西能源学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | https://zs.sxmtxy.net/ |
| 792 | 常州大学怀德学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://hdzs.cczu.edu.cn/ |
| 793 | 常州工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.czu.cn/zsb/main.psp |
| 794 | 常州工程职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsjy.czie.edu.cn/ |
| 796 | 常州纺织服装职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.cztgi.edu.cn |
| 797 | 常德职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.cdzy.cn/zsb/ |
| 798 | 平顶山学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.pdsu.edu.cn/jgsz1/zsjf.htm |
| 799 | 平顶山工业职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.pzxy.edu.cn/ |
| 800 | 广东东软学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_http_502` | 502 | https://www.nuit.edu.cn/zsxxw |
| 806 | 广东外语外贸大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.gdufs.edu.cn/index/zszx.htm |
| 807 | 广东工业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://wsc.gdut.edu.cn/zssxjy/xmjs.htm |
| 809 | 广东技术师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://kyc.gpnu.edu.cn/kycg/zscq.htm |
| 810 | 广东文理职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.gdwlxy.edu.cn/Html/Article/list_533.html |
| 811 | 广东海洋大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://iod.gdou.edu.cn/gatsw/zs.htm |
| 814 | 广东省外语艺术职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.gtcfla.edu.cn |
| 817 | 广东茂名幼儿师范专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_not_found` | 404 | http://www.gdgzsf.cn/zsb/ |
| 825 | 广州华立学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hualixy.com/zsb/ |
| 826 | 广州华立科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hlxy.net/cszs/ |
| 827 | 广州南方学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.nfu.edu.cn |
| 828 | 广州卫生职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.gzws.edu.cn/zs |
| 830 | 广州城市理工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.gcut.edu.cn/ |
| 833 | 广州康大职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.kdvtc.edu.cn/ |
| 834 | 广州新华学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.xhsysu.edu.cn/zsxx.htm |
| 835 | 广州民航职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.caac.net/zsb/ |
| 838 | 广州科技贸易职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.gzkmu.edu.cn/zsw/ |
| 840 | 广州软件学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.sise.com.cn/zsb/ |
| 842 | 广西中医药大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.gxtcmu.edu.cn/bzkzsw |
| 843 | 广西中医药大学赛恩斯新医药学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.gxzyxysy.com/ |
| 845 | 广西体育高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.gxtznn.com/zsw2021/ |
| 848 | 广西医科大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.gxmu.edu.cn/zsjy/ |
| 854 | 广西工业职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.gxgy.edu.cn/zsxx |
| 855 | 广西工程职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.gxgcedu.com/zsjy/zsb/ |
| 856 | 广西师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.gxnu.edu.cn/1385/list.htm |
| 857 | 广西幼儿师范高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsw.gxyesf.edu.cn |
| 858 | 广西建设职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.gxjsxy.cn/zsxx |
| 859 | 广西机电职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.gxcme.edu.cn/ |
| 861 | 广西水利电力职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.gxsdxy.cn/zjc/index/zs1/shouy.htm |
| 863 | 广西电力职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsjy2006.gxdlxy.com/ |
| 866 | 广西科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.gxkjzy.com/defaultky.aspx?type=newslist&id=328 |
| 870 | 广西英华国际职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.gxtic.edu.cn/zsw/ |
| 871 | 广西财经学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.gxufe.cn/www/myweb/home.cdi/zsb/ |
| 872 | 广西金融职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.gxjrxy.com/zsw/ |
| 873 | 庆阳职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.qyvtc.cn/zsjy |
| 880 | 延边职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.ybvtc.com/zsb/ |
| 881 | 建东职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.czjdu.com/html/node48.html |
| 882 | 开封大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www2.kfu.edu.cn/zs/ |
| 884 | 张家口学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.zjku.edu.cn/index.html/zsb/ |
| 885 | 张家界学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.zjjc.edu.cn/ |
| 888 | 徐州工业职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.xzcit.cn/ |
| 889 | 徐州工程学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zjc.xzit.edu.cn/zhaosheng/ |
| 890 | 徐州幼儿师范高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.xzyz.edu.cn/xxgk/jgsz/zsdw.htm |
| 894 | 德州科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.sddzkj.com/zsb/ |
| 897 | 德阳城市轨道交通职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.dcurt.cn/list_27/ |
| 900 | 忻州职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_not_found` | 404 | http://www.xzvtc.net/bkzs/ |
| 901 | 怀化学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.hhtc.edu.cn |
| 902 | 恩施职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsxx.eszy.edu.cn/ |
| 906 | 成都体育学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.cdsu.edu.cn/zsb/ |
| 909 | 成都外国语学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.cdisu.edu.cn/ |
| 913 | 成都师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.cdnu.edu.cn/zjc/zsgz.htm |
| 915 | 成都理工大学工程技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.cdutetc.cn/ |
| 920 | 成都锦城学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | http://www.scujcc.com.cn/zsb/ |
| 925 | 扬州工业职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zjc.ypi.edu.cn/main.htm |
| 927 | 承德医学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.cdmc.edu.cn/ |
| 928 | 承德护理职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.cdwx.cn/zsb/ |
| 931 | 攀枝花学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.pzhu.edu.cn/ |
| 933 | 文华学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zhaosheng.hustwenhua.net |
| 934 | 文山学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.wsu.edu.cn/xwgk/zsksxx.htm |
| 935 | 新乡学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://recruit.xxu.edu.cn/zsxt/zsxt/kslqxx/kslqxx.do |
| 936 | 新乡职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.xxvtc.edu.cn/ |
| 937 | 新余学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zb.xyc.edu.cn |
| 940 | 新疆农业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.xjau.edu.cn |
| 942 | 新疆医科大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.xjmu.edu.cn/zsjy.htm |
| 946 | 新疆天山职业技术大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.xjtsxy.cn/news/46 |
| 948 | 新疆工程学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.xjie.edu.cn/zsjy/zsjy.htm |
| 950 | 新疆应用职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.xjyyedu.cn/_redirect?siteId=4&columnId=30&articleId=71 |
| 953 | 新疆生产建设兵团兴新职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://btc.edu.cn/list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1039 |
| 957 | 新疆科技职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.xjkjzyjsxy.com/page149 |
| 961 | 新疆艺术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://bkzs.xjart.edu.cn/ |
| 965 | 新疆铁道职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.xjtzy.net/zsjyzdzxx/ |
| 966 | 无锡南洋职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.wsoc.edu.cn |
| 967 | 无锡商业职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.wxic.edu.cn/ |
| 968 | 无锡城市职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsjyc.wxcu.edu.cn/ |
| 972 | 无锡科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.wxit.edu.cn/ |
| 977 | 日照职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://gotorzu.rzpt.cn/ |
| 978 | 日照航海工程职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.rzmevc.com/ |
| 979 | 昆山登云科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsfw.dyc.edu.cn/ |
| 981 | 昆明冶金高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.kmyz.edu.cn/zsw |
| 982 | 昆明医科大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.kmmc.cn/zsb |
| 983 | 昆明医科大学海源学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.kyhyxy.com/ |
| 985 | 昆明城市学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.ynnubs.com/ |
| 986 | 昆明学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://bkzs.kmu.edu.cn/ |
| 987 | 昆明理工大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.kmust.edu.cn/zsjy/bkszs.htm |
| 990 | 昌吉学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.cjc.edu.cn/cjzsw |
| 992 | 星海音乐学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.xhcom.edu.cn/ |
| 994 | 晋中学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.jzxy.edu.cn/ |
| 997 | 景德镇艺术职业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | https://zs.jci-ky.cn/ |
| 998 | 景德镇陶瓷大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.jci.edu.cn/ |
| 999 | 景德镇陶瓷职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.jcivt.com |
| 1002 | 曲阜远东职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.fareast-edu.net/news/6533.html |
| 1003 | 曲靖师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.qjnu.edu.cn/zsxt-web/index.do |
| 1004 | 曹妃甸职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://old.cct.edu.cn/zsxxxx |
| 1006 | 朔州职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sxszvtc.cn/c32 |
| 1008 | 杭州师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hznu.edu.cn/zsjy/ |
| 1010 | 松原职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.sypt.cn/zsb/ |
| 1012 | 枣庄学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.uzz.edu.cn/ |
| 1014 | 枣庄科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://other.zzkjxy.edu.cn/zsjy/ |
| 1024 | 桂林旅游学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.gltu.edu.cn/zsjy.htm |
| 1025 | 桂林理工大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.glut.edu.cn/jgsz/zsdw.htm |
| 1028 | 桂林航天工业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsw.guat.edu.cn |
| 1029 | 梧州学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsw.gxuwz.edu.cn/ |
| 1032 | 楚雄师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.cxtc.edu.cn |
| 1035 | 正德职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.zdxy.cn |
| 1036 | 武夷学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.wuyiu.edu.cn/3216/main.htm |
| 1037 | 武昌工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.wuit.cn/ |
| 1038 | 武昌理工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.wut.edu.cn/ |
| 1040 | 武昌首义学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://jwc.wsyu.edu.cn/zsbbm/124988.htm |
| 1041 | 武汉东湖学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.wdu.edu.cn/ |
| 1042 | 武汉交通职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.whjzy.net/jgsz/zsdw.htm |
| 1043 | 武汉传媒学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsw.whmc.edu.cn/ |
| 1044 | 武汉体育学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.whsu.edu.cn/ |
| 1045 | 武汉体育学院体育科技学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://kjxy.whsu.edu.cn/zsjy.htm |
| 1046 | 武汉信息传播职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.whinfo.cn/zhaoshengwangzhan/index.php?c=category&id=13 |
| 1047 | 武汉光谷职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.whggvc.net/ |
| 1049 | 武汉商学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.wbu.edu.cn/ |
| 1050 | 武汉商贸职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.whicu.com/ |
| 1054 | 武汉学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.whxy.edu.cn/ |
| 1055 | 武汉工商学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://goto.wtbu.edu.cn/ |
| 1056 | 武汉工程大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.wit.edu.cn/zsjy.htm |
| 1057 | 武汉工程大学邮电与信息工程学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsjy.witpt.edu.cn |
| 1058 | 武汉工程科技学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.wuhues.com/ |
| 1059 | 武汉晴川学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.qcuwh.edu.cn |
| 1061 | 武汉生物工程学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.whsw.cn/zsjyc/ |
| 1062 | 武汉科技大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.wust.edu.cn/#/index |
| 1064 | 武汉纺织大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.wtu.edu.cn/zsjy.htm |
| 1067 | 武汉航海职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_http_444` | 444 | http://zs.2hhxy.com/ |
| 1068 | 武汉船舶职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsw.wspc.edu.cn/ |
| 1069 | 武汉警官职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.whpa.edu.cn |
| 1070 | 武汉软件工程职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.whvcse.edu.cn/ztzl1/zskzslhjxzqzjgxxjy.htm |
| 1071 | 武汉轻工大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.whpu.edu.cn/zsjy/zsgz.htm |
| 1076 | 永城职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.ycvc.edu.cn/zsjy.htm |
| 1077 | 永州职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.yongzhouzhiyuan.cn/zsjy.htm |
| 1078 | 汉中职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.2249716.com |
| 1079 | 汉口学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.hkxy.edu.cn/ |
| 1084 | 江南影视艺术职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.jnys.cn/zsxxw/ |
| 1085 | 江汉大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://news.jhun.edu.cn/75/ff/c2710a226815/page.htm |
| 1086 | 江汉艺术职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hbjhart.edu.cn/zsxx_new |
| 1087 | 江海职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.jhu.cn/B07ZSC/ |
| 1088 | 江苏信息职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsxx.jsit.edu.cn/ |
| 1089 | 江苏农林职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsw.jsafc.edu.cn/ |
| 1090 | 江苏农牧科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.jsahvc.edu.cn/zsxx/main.htm |
| 1094 | 江苏城乡建设职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsw.jscc.edu.cn/ |
| 1096 | 江苏大学京江学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://jjxy.ujs.edu.cn/zsjy/zs.htm |
| 1097 | 江苏安全技术职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | http://www.jsvist.com/zsb/ |
| 1098 | 江苏工程职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://xlxy.ntu.edu.cn/zsjy/list.htm |
| 1101 | 江苏建筑职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.jsjzi.edu.cn/_t2415/zsxx/list.htm |
| 1102 | 江苏旅游职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.jstc.edu.cn/zs/ |
| 1103 | 江苏海事职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.jmi.edu.cn/ |
| 1109 | 江苏第二师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.jssnu.edu.cn/ |
| 1110 | 江苏经贸职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zb.jvic.edu.cn/ |
| 1111 | 江苏航空职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.jatc.edu.cn/ |
| 1113 | 江苏财会职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.jscfa.edu.cn/zsjy/ |
| 1115 | 江苏食品药品职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.jsfpc.edu.cn/ |
| 1116 | 江西中医药大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsxxw.jxutcm.edu.cn/ |
| 1118 | 江西信息应用职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.jxcia.com/zsjygzc.htm |
| 1119 | 江西农业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.jxau.edu.cn/info/1044/108411.htm |
| 1121 | 江西冶金职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.jxyjxy.com |
| 1123 | 江西医学高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsjy.jxyxgz.cn/ |
| 1124 | 江西司法警官职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.jxsfjy.cn/ |
| 1125 | 江西外语外贸职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.jxcfs.com |
| 1126 | 江西婺源茶业职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://jxtvc.com/Item/list.asp?id=1735 |
| 1128 | 江西工业贸易职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsc.jxgmxy.com/ |
| 1131 | 江西师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.jxnu.edu.cn/zsjy/list.htm |
| 1133 | 江西师范高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.jxsfgz.com/zsb/ |
| 1134 | 江西应用工程职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsc.jxatei.net/ |
| 1137 | 江西建设职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | http://www.jxjsxy.com/index_v.aspx/zsb/ |
| 1138 | 江西新能源科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.tynxy.com/ |
| 1139 | 江西旅游商贸职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.jxlsxy.edu.cn |
| 1140 | 江西服装学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.jift.edu.cn/ |
| 1142 | 江西枫林涉外经贸职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_reachable` | 200 | http://www.fenglin.org/zsb/ |
| 1145 | 江西水利职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.jxslsd.com/zsjy/ |
| 1147 | 江西环境工程职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.jxhjxy.com/zsc |
| 1148 | 江西现代职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsw.jxxdxy.edu.cn/ |
| 1150 | 江西生物科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsw.jxswkj.com |
| 1153 | 江西科技师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.jxstnu.edu.cn/rcpy/zsbbmw.htm |
| 1154 | 江西科技职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.jxkeda.com/zsb |
| 1158 | 江西财经大学现代经济管理学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsjy.jcxjg.edu.cn |
| 1159 | 江西财经职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.jxvc.jx.cn/index/zsjy.htm |
| 1164 | 池州学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.czu.edu.cn/ |
| 1166 | 沈阳农业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.syau.edu.cn/ |
| 1168 | 沈阳北软信息职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://nsi-soft.com/nsi/zsgz |
| 1171 | 沈阳大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.syu.edu.cn:443/zsjy.htm |
| 1172 | 沈阳工业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sut.edu.cn/zsjy.htm |
| 1173 | 沈阳工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsxx.situ.edu.cn/ |
| 1174 | 沈阳工程学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.sie.edu.cn/ |
| 1175 | 沈阳师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_error` |  | https://zs.synu.edu.cn/ |
| 1176 | 沈阳建筑大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.sjzu.edu.cn/index.htm |
| 1177 | 沈阳理工大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.sylu.edu.cn/ |
| 1178 | 沈阳职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.vtcsy.com:9994/szzs/ |
| 1180 | 沈阳药科大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.syphu.edu.cn/zsjy2.htm |
| 1181 | 沈阳音乐学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.sycm.edu.cn/info.aspx?DWid=66 |
| 1182 | 沙洲职业工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.szit.edu.cn |
| 1183 | 沧州交通学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_not_found` | 404 | http://zsb.bjtuhbxy.cn/ |
| 1184 | 沧州医学高等专科学校 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.czmc.cn |
| 1185 | 沧州师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.caztc.edu.cn/zsjy.htm |
| 1187 | 沧州职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.czvtc.cn/zsxx |
| 1189 | 河北东方学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hbdfxy.cn/zsb/ |
| 1191 | 河北交通职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hejtxy.edu.cn/zsb/ |
| 1192 | 河北传媒学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.hebic.cn/#/dashboard |
| 1193 | 河北农业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hebau.edu.cn/zsjy.htm |
| 1194 | 河北化工医药职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hebcpc.cn/zsw/ |
| 1196 | 河北医科大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.hebmu.edu.cn |
| 1197 | 河北医科大学临床学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsb.hebmu.edu.cn |
| 1198 | 河北司法警官职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsjy.jjgxy.com.cn |
| 1199 | 河北地质大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hgu.edu.cn/zzjg/zsdw.htm |
| 1200 | 河北地质大学华信学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.sjzuehx.cn/%5Chome/Recruitwork/index.html?cid=24 |
| 1201 | 河北外国语学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hisu.edu.cn/channel/zhaoshengxinxiwang.html |
| 1202 | 河北大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hbu.edu.cn/zsjy1.htm |
| 1204 | 河北对外经贸职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hbiibe.edu.cn/zsb/ |
| 1207 | 河北工程大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.hebeu.edu.cn/ |
| 1208 | 河北工程大学科信学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://kexin.hebeu.edu.cn/zsjy/zsxx/xwgg.htm |
| 1210 | 河北师范大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hebtu.edu.cn/a/zsjy/bkszs/index.html |
| 1212 | 河北建筑工程学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.hebiace.edu.cn/ |
| 1214 | 河北旅游职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_not_found` | 404 | http://www.cdtvc.com/zsb/ |
| 1216 | 河北水利电力学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsb.hbwe.edu.cn/ |
| 1219 | 河北科技大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://bkzs.hebust.edu.cn/ |
| 1222 | 河北科技师范学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zhaosheng.hevttc.edu.cn/ |
| 1226 | 河北能源职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zsw.hbnyxy.cn/zs/col/1420597365283/index.html |
| 1228 | 河北轨道运输职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hbgdys.cn/zsjy/index.htm |
| 1229 | 河北软件职业技术学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.hbsi.edu.cn/ |
| 1230 | 河北金融学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.hbfu.edu.cn/info?id=19 |
| 1232 | 河南农业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://www.henau.edu.cn/jgsz/zsjg.htm |
| 1236 | 河南地矿职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.hagmc.edu.cn/ |
| 1239 | 河南工业和信息化职业学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://www.hciit.edu.cn/zsxx/ |
| 1240 | 河南工业大学 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://zs.haut.edu.cn/ |
| 1243 | 河南工学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zsxx.hait.edu.cn |
| 1244 | 河南工程学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | http://hauezs.university-hr.com/ |
| 1247 | 河南开封科技传媒学院 | `pending_manual_review_with_official_candidate` | `school_official_recruit_site_route_auto` | `round5_machine_timeout` |  | https://zs.humc.edu.cn/ |

## 3. 后续建议

1. 对 `round5_machine_reachable` 的记录，下一步仍需人工打开页面并确认是否为招生章程或招生官网入口。
2. 对超时、SSL 错误或访问异常的记录，不应改为已确认；可在网络环境更稳定时复跑本脚本。
3. 只有找到明确招生章程页面、PDF 或高校招生网对应章程栏目后，才能进入人工确认状态。
