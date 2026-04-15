# FitScan 后端部署文档

## 环境要求

- Python 3.7+
- pip 3.6+

## 开发环境部署

### 步骤 1: 克隆代码

```bash
git clone <repository-url>
cd fitscan/backend
```

### 步骤 2: 创建虚拟环境

```bash
# Windows
python -m venv venv
# macOS/Linux
python3 -m venv venv
```

### 步骤 3: 激活虚拟环境

```bash
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 步骤 4: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 5: 配置环境变量

复制 `.env.example` 文件为 `.env` 并根据需要修改配置：

```bash
cp .env.example .env
```

### 步骤 6: 初始化数据库

```bash
python init_db.py
```

### 步骤 7: 启动开发服务器

```bash
python run.py
```

开发服务器将在 `http://localhost:5000` 上运行。

## 测试环境部署

### 步骤 1-6: 同开发环境部署

### 步骤 7: 运行测试

```bash
pytest
```

### 步骤 8: 检查测试覆盖率

```bash
coverage run -m pytest
coverage report
```

## 生产环境部署

### 步骤 1-6: 同开发环境部署

### 步骤 7: 修改配置

修改 `.env` 文件，将 `DEBUG` 设置为 `False`，并配置生产环境的数据库：

```
DEBUG=False
DATABASE_URI=postgresql://username:password@localhost:5432/fitscan
```

### 步骤 8: 使用 Gunicorn 启动服务

```bash
# 安装 Gunicorn（如果尚未安装）
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### 步骤 9: 配置 Nginx（可选）

```nginx
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:5000/api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker 部署

### 步骤 1: 创建 Dockerfile

```Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY .env.example .env

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

### 步骤 2: 构建 Docker 镜像

```bash
docker build -t fitscan-backend .
```

### 步骤 3: 运行 Docker 容器

```bash
docker run -p 5000:5000 --env-file .env fitscan-backend
```

## API 文档

部署完成后，可以通过以下地址访问 API 文档：

```
http://localhost:5000/api/docs
```

## 监控与维护

### 日志管理

日志文件存储在 `logs` 目录中，按日期命名。可以使用以下命令查看日志：

```bash
tail -f logs/$(date +%Y-%m-%d).log
```

### 数据库备份

定期备份数据库，以防止数据丢失：

```bash
# SQLite
cp fitscan.db fitscan.db.backup

# PostgreSQL
pg_dump -U username fitscan > fitscan.sql
```

### 性能监控

可以使用工具如 `top`、`htop` 或 `prometheus` 来监控系统性能。

## 常见问题

### 端口占用

如果端口 5000 被占用，可以修改 `.env` 文件中的 `PORT` 配置。

### 数据库连接失败

检查数据库配置是否正确，确保数据库服务正在运行。

### 权限问题

确保应用有足够的权限读写文件和目录。

## 故障排查

1. 查看日志文件
2. 检查环境变量配置
3. 验证数据库连接
4. 运行测试用例
5. 检查依赖是否正确安装
