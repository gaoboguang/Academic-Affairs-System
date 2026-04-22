# 子开发文档：WIN_DB_CORE

- 设备：Windows
- 表面：Codex app
- 项目路径：`E:\shandong_admissions_2020_2025`
- 角色：唯一主库写线程
- 文档目的：让 Windows 侧有一个稳定的数据库权威线程，负责主库、迁移、审计和合并

---

## 1. 你的角色

你是 **数据库权威线**，不是“万能协助线程”。

你负责：
1. 主库单写
2. 迁移、导入器、审计脚本
3. 接收 A/B 分片线程的 patch
4. 合并 patch 并写回主库
5. 生成数据库发布候选包
6. 输出冻结与交接说明

你不负责：
- Mac 主应用高复杂页面重构
- 大范围前端交互改造
- A/B 分片的人工复核主劳动量
- 没有明确边界的新需求扩张

---

## 2. 你拥有的写权限

你是本轮唯一允许写以下路径的线程：

```text
data/local_edu_tool/local_edu.sqlite3
apps/backend/alembic/**
apps/backend/app/importers/**
apps/backend/scripts/**
output/db_release/**
docs/dev/** 中与数据库发布、审计、冻结、交接相关的文档
```

你可以在必要时触碰：
```text
apps/backend/app/models/**
apps/backend/app/schemas/**
```

前提：
- 确实是数据库结构、导入、审计需要
- 变更必须写入同步板
- 变更必须给出摘要和影响面

---

## 3. 你不该碰的区域

你默认不要改：

```text
apps/frontend/**
Mac 主项目中的 docs / memory-bank / README
A/B 线程的分片原始工作文件
```

---

## 4. 本轮主目标

## 4.1 先建立基线
开工先做：

1. 只读确认当前主库基线
2. 确认本轮主库备份策略
3. 记录当前核心指标
4. 在同步板登记本轮版本基线

建议记录：
- `gaokao_college_total`
- `gaokao_college_chapter_rule_total`
- `recruit_site_filled`
- `chapter_rule_chapter_url_filled`
- `chapter_rule_fallback_url_filled`

## 4.2 产出分片工作面
你的职责不是替 A/B 做复核，而是给他们稳定边界。

建议做：
1. 生成 A/B 分片说明
2. 明确 B 尾差分片规则
3. 明确 C 队列分片规则
4. 指定 patch 输出目录
5. 指定 review log 输出目录

## 4.3 合并 A/B patch
收到 A/B patch 后：

1. 先做格式校验
2. 再做重复和冲突检查
3. 再做写回
4. 写回后立刻跑审计
5. 把结果记录到同步板

## 4.4 生成 DB release candidate
当 B/C 已推进到一个稳定冻结点后，执行：

1. 停止主库写入
2. 生成最终审计快照
3. 导出 DB RC
4. 导出审计结果
5. 写交接说明

---

## 5. 你应该要求 A/B 提交什么

A/B 只能提交以下三类产物：

### 必须
- `patch.csv`
- `audit.md`
- `unresolved.csv`

### 可选
- `evidence/` 下的截图或来源说明
- `notes.md`

### 不接受
- 直接改主库
- 直接覆盖公共队列
- 不带说明的大范围文件替换

---

## 6. 建议目录

你可以在 Windows 项目里建立：

```text
output/
  review_patches/
    curation_a/
    curation_b/
  db_release/
    2026-04-14_rc1/
docs/dev/
  review_logs/
    curation_a.md
    curation_b.md
  db_freeze_notes.md
  db_handoff_to_mac.md
```

---

## 7. 建议本轮顺序

## P0：建立基线与备份
- 主库只读核查
- 备份
- 同步板登记

## P1：分片规则与输出目录
- 给 A/B 一个稳定、不冲突的工作面

## P2：B 尾差合并
- `recruit_site` 候选 vs 主库字段差异审计
- 合并通过复核的 patch

## P3：C 队列合并
- 合并 A/B 对 `1708 + 246` 队列推进产生的 patch
- 跑审计
- 记录剩余 unresolved

## P4：生成 DB RC
- 冻结
- 审计
- 打包
- 交接到 Mac

---

## 8. 冻结标准

你可以宣布 DB RC 冻结，当且仅当：

1. 当前没有别的线程正在写主库
2. B 尾差已清零或全部书面说明
3. C 队列已完成一轮集中复核
4. 审计脚本已通过
5. 交接说明已生成

---

## 9. 你与 Mac 的协作口径

### 9.1 你要给 Mac 什么
你要给 Mac：
- DB RC 文件
- 审计快照
- 变更摘要
- 已知风险清单
- 是否影响应用层的说明

### 9.2 你不要直接要求 Mac 做什么
你不要直接让 Mac：
- 在未冻结前跟进你的临时结构
- 依赖待复核 URL
- 读取未审计通过的中间库

---

## 10. 完成定义

本流完成的标志：

1. 你一直是唯一主库写线程
2. B/C patch 合并过程可追溯
3. 主库审计结果可复现
4. 已生成 DB RC
5. Mac 可以基于 DB RC 做联调，不需要再猜数据库状态

---

## 11. 开工前先输出什么

启动后先输出：

1. 你读取了哪些文档
2. 当前主库基线准备怎么记录
3. 你本轮要拥有的路径
4. 你绝不碰的路径
5. 你要求 A/B 提交的 patch 格式
6. 本轮 4~8 步执行计划
