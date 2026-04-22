# 子开发文档：WIN_DATA_CURATION_A

- 设备：Windows
- 表面：Codex app
- 项目路径：`E:\shandong_admissions_2020_2025`
- 角色：数据库人工复核 A 分片线程
- 文档目的：负责 B 尾差和 C 队列的 A 分片，不碰主库

---

## 1. 你的角色

你是 **人工复核 A 分片线程**，不是主库线程。

你负责：

1. `recruit_site` 尾差的 A 分片
2. 章程复核队列的 A 分片
3. 形成 patch / audit / unresolved
4. 把结果交给 `WIN_DB_CORE`

你不负责：
- 写主库
- 合并别人的 patch
- 大范围修改数据库脚本
- Mac 主应用开发

---

## 2. 分片规则

### 默认规则
优先使用整数 `college_id`：

- A 处理奇数
- B 处理偶数

### 若没有 `college_id`
退化为：

1. 用 `college_code` 最后一位奇偶分片
2. 若还不行，按学校名称排序后按奇偶行号分片

### 原则
你的分片必须是确定性的，别人能复现你的筛选逻辑。

---

## 3. 你处理哪些内容

## 3.1 B 任务：`recruit_site` 尾差 A 分片
你的目标：
- 对候选数据与主库正式字段的差异做 A 分片核对
- 只处理属于 A 分片的记录
- 形成可写回 patch

建议产物：
- `output/review_patches/curation_a/recruit_site_patch_a.csv`
- `output/review_patches/curation_a/recruit_site_unresolved_a.csv`
- `docs/dev/review_logs/curation_a.md`

## 3.2 C 任务：章程复核 A 分片
你的目标：
- 推进 A 分片的 `pending_manual_review_with_official_candidate`
- 推进 A 分片的 `pending_manual_review`
- 能确认正式入口就确认，不能确认就明确 unresolved 原因

建议产物：
- `output/review_patches/curation_a/chapter_patch_a.csv`
- `output/review_patches/curation_a/chapter_unresolved_a.csv`
- `docs/dev/review_logs/curation_a.md`

---

## 4. 你只能写哪些地方

你可以写：

```text
output/review_patches/curation_a/**
docs/dev/review_logs/curation_a.md
自己分片的临时工作文件
```

你不要写：

```text
data/local_edu_tool/local_edu.sqlite3
curation_b/**
主库合并脚本
Mac 项目
```

---

## 5. 你的工作方法

## P0：先确认分片范围
先输出：
- 你使用的分片规则
- 你的 owned rows 如何筛
- 你的输出目录

## P1：做 B 尾差 A 分片
建议动作：
1. 读取 `recruit_site` 候选与正式字段差异
2. 只取 A 分片
3. 确认可回写项
4. 形成 patch 和 unresolved

## P2：做 C 队列 A 分片
建议动作：
1. 读取官方候选入口
2. 优先确认“已有候选”的 A 分片
3. 再推进“待官方补查”的 A 分片
4. 保留证据与来源说明

## P3：交付给 DB_CORE
你交付的不是“我改完了”，而是：
- patch
- unresolved
- audit 说明

---

## 6. 产物格式建议

### patch.csv 最少字段
- `college_id`
- `field_name`
- `old_value`
- `new_value`
- `source_url`
- `review_status`
- `review_note`

### unresolved.csv 最少字段
- `college_id`
- `field_name`
- `current_value`
- `candidate_value`
- `reason`
- `next_action`

### audit.md 建议写
- 本次处理范围
- 已确认条数
- 未确认条数
- 高风险情况
- 是否影响别的线程

---

## 7. 你的完成定义

你完成，不是“把库改完”，而是：

1. A 分片的 B 尾差完成一轮核对
2. A 分片的 C 队列完成一轮复核
3. 所有结果都形成 patch / unresolved / audit
4. 没有直接写主库
5. 结果能被 `WIN_DB_CORE` 稳定合并

---

## 8. 你开工前先输出什么

启动后先输出：

1. 你读取了哪些文档
2. 你采用的分片规则
3. 你本轮只处理哪些记录
4. 你只会写哪些目录
5. 你绝不碰哪些目录
6. 4~8 步执行计划
