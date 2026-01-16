FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY app.py .
COPY gunicorn.conf.py .
COPY start.py .
COPY data.csv .

# 暴露端口（仅作为文档说明，实际端口由 PORT 环境变量决定）
EXPOSE 8000

# 启动命令
CMD ["python", "start.py"]
