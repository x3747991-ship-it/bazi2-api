FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY app.py .
COPY gunicorn.conf.py .
COPY data.csv .

# 暴露端口
EXPOSE 8000

# 健康检查
# NOTE: zeabur 会使用此健康检查来确认服务启动成功
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# 启动命令
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
