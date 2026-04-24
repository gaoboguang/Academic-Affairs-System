# 项目上下文

## 项目定位

- 项目名称：本地教务工具
- 目标场景：高中学校的本地单机教务决策台
- 核心特征：本地运行、单用户、离线优先、中文后台

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router、ECharts
- 后端：FastAPI、SQLAlchemy、Alembic、Pydantic、pandas、openpyxl
- 数据库：SQLite

## 关键目录

- `apps/frontend`：前端应用
- `apps/backend`：后端应用
- `data/`：数据库、上传、导出、模板、日志、备份
- `data/local_edu_tool/`：高考主线库 handoff / fallback 入口，当前保留 `local_edu.sqlite3`
- `docs/`：规格文档和开发建议
- `handoffs/`：外部数据库接管包与相关审计/说明材料
- `scripts/`：本地启动和初始化脚本

## 长期约束

- 不引入必须联网才能运行的在线依赖
- 关键业务规则必须配置化
- 附件只保存本地路径和元信息，不直接入库
- 2026-04-22 起优先采用“`data/app.db` 嵌入 handoff 原始高考表”的单库运行形态；`data/local_edu_tool/local_edu.sqlite3` 保留为同步来源和 fallback
- 2026-04-22 起继续采用“两层数据库”思路：`gaokao_*` raw 表保留原始事实，项目业务表负责面向页面与推荐的结构化消费，不直接把所有特殊考生类型硬塞进现有普通类模型
- 默认监听 `127.0.0.1`
- 目标运行环境优先兼容 Windows
