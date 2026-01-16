# -*- coding: utf-8 -*-
"""
Gunicorn 配置文件 - 专为 Zeabur 部署优化
"""

import multiprocessing
import os

# 绑定地址和端口
bind = "0.0.0.0:8000"

# Worker 配置
# NOTE: 使用 1-2 个 worker，避免多个 worker 同时加载大文件导致内存溢出
workers = 1
worker_class = "sync"

# 超时配置
# NOTE: 增加超时时间以应对数据加载
timeout = 120  # 请求超时时间（秒）
graceful_timeout = 30  # 优雅关闭超时时间（秒）
keepalive = 5  # Keep-Alive 连接保持时间（秒）

# 内存管理
max_requests = 1000  # Worker 处理请求数量上限，之后自动重启（防止内存泄漏）
max_requests_jitter = 50  # 随机增加重启请求数（避免所有 worker 同时重启）

# 日志配置
accesslog = "-"  # 访问日志输出到 stdout
errorlog = "-"   # 错误日志输出到 stderr
loglevel = "info"  # 日志级别

# 进程名称
proc_name = "bazi-api"

# 预加载应用
# NOTE: 在 fork worker 之前加载应用代码，所有 worker 共享内存
preload_app = True

# 启动时打印配置信息
def on_starting(server):
    server.log.info("=" * 60)
    server.log.info("八字 API 服务启动中...")
    server.log.info(f"Workers: {workers}")
    server.log.info(f"Timeout: {timeout}s")
    server.log.info(f"Bind: {bind}")
    server.log.info("=" * 60)

# Worker 启动后回调
def post_worker_init(worker):
    worker.log.info(f"Worker {worker.pid} 已启动")
