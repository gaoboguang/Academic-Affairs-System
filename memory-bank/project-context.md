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
- `data/local_edu_tool/`：高考主线库运行入口，默认读取 `local_edu.sqlite3`
- `docs/`：规格文档和开发建议
- `handoffs/`：外部数据库接管包与相关审计/说明材料
- `scripts/`：本地启动和初始化脚本

## 长期约束

- 不引入必须联网才能运行的在线依赖
- 关键业务规则必须配置化
- 附件只保存本地路径和元信息，不直接入库
- 默认监听 `127.0.0.1`
- 目标运行环境优先兼容 Windows
