# 学校服务器上线与账号权限说明

本说明面向“学校自有域名 + 服务器 + HTTPS”部署。当前系统仍保持本地优先和 SQLite 数据库，但已支持受控多人使用：管理员全权限，普通教师按任教 / 班主任班级范围使用。

## 部署形态

- 浏览器访问：`https://你的域名/`
- 前端与后端同域部署：前端走根路径 `/`，后端走 `/api`
- 后端仍建议只监听服务器本机 `127.0.0.1:8000`
- 由 Nginx 或同类反向代理对外提供 HTTPS
- 不开放教师自助注册；所有教师账号由管理员创建

## 角色与权限

| 角色 | 权限范围 |
| --- | --- |
| `admin` | 全部功能，包括账号管理、系统设置、备份恢复、基础数据、教师主档、高考数据、推荐规则和批量高风险操作 |
| `teacher` | 工作台、本人范围学生、学生教师评语、成绩导入、分析中心、报表中心、导入中心相关成绩批次 |

普通教师的数据范围来自三部分：

1. 教师作为班主任的班级。
2. 教师任教关系中的班级。
3. 管理员在账号管理中手动补充的可访问班级。

普通教师不能访问账号管理、系统设置、备份恢复、教师主档维护、高考数据维护、推荐规则维护、学生批量删除和批量调班。后端会统一返回 `403`，前端也会隐藏对应菜单。

学生详情中的“教师评语”用于调班和换教师后的交接。教师可查看本人范围内学生的历史评语；发布评语时必须关联教师档案，并且任教关系中存在该学生当前或历史班级的对应科目。管理员可查看评语，但未关联教师档案的管理员不能冒充任课教师发布。

## 初始化流程

1. 安装依赖并迁移数据库：

```bash
npm install
./.venv/bin/pip install -e './apps/backend[dev]'
npm run backend:migrate
```

2. 初始化管理员账号：

```bash
npm run backend:init-admin -- --username admin
```

如需非交互设置密码，可追加 `--password`。正式服务器建议交互输入，避免密码进入命令历史。

3. 启动后端：

```bash
npm run backend:dev
```

4. 管理员登录后进入“系统设置 / 账号管理”，创建教师账号并关联教师档案。系统只展示一次临时密码，教师首次登录必须修改密码。

## 关键环境变量

`.env` 示例：

```env
LOCAL_EDU_DEBUG=false
LOCAL_EDU_HOST=127.0.0.1
LOCAL_EDU_PORT=8000
LOCAL_EDU_AUTH_REQUIRED=true
LOCAL_EDU_AUTH_COOKIE_SECURE=true
LOCAL_EDU_ALLOWED_ORIGINS=https://你的域名
LOCAL_EDU_DATA_DIR=/srv/local-edu-tool/data
```

本地开发如使用 `http://127.0.0.1:5173`，`LOCAL_EDU_AUTH_COOKIE_SECURE` 可以保持 `false`。公网 HTTPS 部署必须设为 `true`。

## Nginx 示例

```nginx
server {
    listen 443 ssl http2;
    server_name 你的域名;

    ssl_certificate /etc/letsencrypt/live/你的域名/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/你的域名/privkey.pem;

    root /srv/local-edu-tool/apps/frontend/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 80;
    server_name 你的域名;
    return 301 https://$host$request_uri;
}
```

前端构建命令：

```bash
npm run frontend:build
```

## 安全与备份

- 登录会话保存在服务端，浏览器只保存 `HttpOnly + Secure + SameSite=Strict` Cookie。
- 会话 token 在数据库中只保存哈希；退出登录、禁用账号、重置密码会吊销相关会话。
- 写操作带 CSRF 请求头，后端会校验。
- 密码使用 Argon2 哈希；登录失败提示统一为“账号或密码错误”。
- 定期备份 `LOCAL_EDU_DATA_DIR`，重点是 `app.db`、`uploads/`、`exports/`、`templates/` 和 `backups/`。
- 服务器上线前建议先执行：

```bash
npm run backend:test
npm run frontend:lint
npm run frontend:test
npm run frontend:build
```

## 上线检查清单

- 域名已解析到服务器。
- HTTPS 证书已签发并自动续期。
- 后端只监听 `127.0.0.1`，公网只暴露 80 / 443。
- `LOCAL_EDU_AUTH_COOKIE_SECURE=true`。
- 已执行 `npm run backend:migrate`。
- 已初始化管理员账号，并妥善保存密码。
- 管理员已创建教师账号，教师首次登录已改初始密码。
- 已做一次数据库和上传目录备份。
