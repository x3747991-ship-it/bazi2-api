# 使用一个轻量级的官方 Python 镜像作为基础
FROM python:3.9-slim

# 在容器内创建一个工作目录
WORKDIR /app

# 1. 首先，只复制依赖文件，这样可以利用Docker的缓存机制
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. 【关键修正】明确地、独立地复制每一个需要的文件和文件夹
# 这确保了没有任何东西会被意外地忽略
COPY app.py .
COPY bazi_data_split ./bazi_data_split/

# 告诉外界，我们的应用在容器内会监听 8000 端口
EXPOSE 8000

# 容器启动时，执行的最终命令
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8000", "app:app"]
