# 本地升学规划任务中心说明

日期：2026-04-28

## 定位

本轮新增“升学规划任务中心”，用于把学生升学画像、路径初筛、材料缺口、志愿草稿复核、阶段复盘和输出报表连成一条本地跟进线。功能仍保持单用户、本地 SQLite、无公网同步、无学生端或家长端。

## 数据结构

新增 Alembic 迁移 `20260428_0021_student_planning_schema.py`，包含三张表：

- `student_planning_goal`：学生目标路径、目标院校/专业、目标分数/位次、备选路径、状态和优先级。
- `student_planning_task`：材料补齐、成绩复核、志愿草稿、章程核对、家校沟通、阶段复盘等任务。
- `student_planning_note`：围绕学生、目标或任务的复盘记录。

任务状态固定为：未开始、进行中、待复核、已完成、暂缓。任务提醒只在首页、学生详情和相关页面内显示，不做系统通知。

## 主要入口

- 学生详情新增“升学规划”页签，可创建目标、手工新增任务、从升学方案生成任务、完成任务、写复盘记录、导出跟进表。
- 山东升学方案中心新增“生成规划任务”按钮，会从路径材料缺口、人工复核项和志愿草稿生成待办。
- 输出中心新增“学生升学规划跟进表”，支持 Excel 和打印预览。
- 首页“下一步建议”接入规划提醒：逾期任务、志愿草稿未复核、材料任务缺截止日期。

## 后端接口

- `GET /api/planning/students/{student_id}`
- `POST /api/planning/goals`
- `PUT /api/planning/goals/{goal_id}`
- `POST /api/planning/tasks`
- `PUT /api/planning/tasks/{task_id}`
- `POST /api/planning/tasks/bulk-create-from-pathway`
- `POST /api/planning/notes`
- `POST /api/reports/planning-followup/export`

通用报表接口 `/api/reports/export` 也支持 `report_type=planning_followup`。

## 使用顺序

1. 在学生详情维护“升学画像”，刷新路径初筛。
2. 打开“升学规划”页签，创建目标路径。
3. 在“升学方案中心”点击“生成规划任务”，把材料缺口和复核项转为待办。
4. 在学生详情完成任务、补复盘记录。
5. 在输出中心导出“学生升学规划跟进表”。

## 验证记录

- 后端新增测试：`apps/backend/tests/test_student_planning.py`
- 前端新增测试：`apps/frontend/tests/student-planning.test.ts`
- E2E 新增测试：`tests/e2e/planning.spec.ts`
- 已确认干净 SQLite 可执行 `alembic upgrade head` 到 `20260428_0021`

## 边界

- 规划任务只做目标、材料、行动和复盘管理，不输出录取承诺。
- 单招、综评、春考、艺体、体育、提前批和特殊类型仍按资格初筛和人工复核理解。
- 不新增账号、权限、云同步、消息推送、学生端或家长端。
