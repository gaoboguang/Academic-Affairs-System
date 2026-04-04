# 本地教务工具后端

后端基于 `FastAPI + SQLAlchemy + SQLite + Alembic`。

启动前请先执行：

```bash
alembic upgrade head
python ../../scripts/init_data.py --demo
```

