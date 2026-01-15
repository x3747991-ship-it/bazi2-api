# 使用一个轻量级的官方 Python 镜像作为基础
FROM python:3.9-slim

# 在容器内创建一个工作目录
WORKDIR /app

# 将您本地文件夹的所有文件，复制到容器的 /app 目录中
# 这会把 app.py, data.csv, requirements.txt 都包含进来
COPY . .

# 安装 requirements.txt 中指定的所有 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 告诉外界，我们的应用在容器内会监听 8000 端口
EXPOSE 8000

# 容器启动时，执行的最终命令
# 使用 gunicorn 这个专业的服务器来启动我们的 Flask 应用
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "app:app"]
