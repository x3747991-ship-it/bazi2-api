# Zeabur 启动脚本
# NOTE: 确保使用正确的端口环境变量

import os
import subprocess
import sys

# 获取 Zeabur 分配的端口
port = os.environ.get('PORT', '8000')

print(f"[启动] 使用端口: {port}")
print(f"[启动] Python 版本: {sys.version}")
print(f"[启动] 工作目录: {os.getcwd()}")

# 启动 Gunicorn
cmd = [
    "gunicorn",
    "-c", "gunicorn.conf.py",
    "app:app"
]

print(f"[启动] 执行命令: {' '.join(cmd)}")
subprocess.run(cmd)
