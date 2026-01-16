# 八字 API Zeabur 部署指南

## 问题诊断

之前部署失败的主要原因：

1. **内存溢出**：每次请求都加载 7.4MB 的 CSV 文件
2. **多 Worker 重复加载**：4 个 worker 同时加载数据，内存占用过高
3. **缺少健康检查**：zeabur 无法判断服务是否启动成功
4. **超时设置不当**：数据加载时间过长导致启动超时

## 优化内容

### 1. 应用层优化（app.py）

✅ **数据预加载机制**
- 应用启动时一次性加载数据到内存
- 所有请求共享同一份数据，避免重复加载

✅ **健康检查端点**
- `/health` - zeabur 用于监控服务状态
- `/` - 根路径欢迎页，提供 API 使用说明

✅ **改进日志**
- 详细记录数据加载过程
- 便于排查部署问题

### 2. Gunicorn 配置优化（gunicorn.conf.py）

✅ **单 Worker 模式**
```python
workers = 1  # 避免多进程重复加载大文件
```

✅ **预加载应用**
```python
preload_app = True  # Worker fork 前加载应用，共享内存
```

✅ **超时配置**
```python
timeout = 120  # 足够的启动时间
```

✅ **内存管理**
```python
max_requests = 1000  # 自动重启防止内存泄漏
```

### 3. Docker 配置优化

✅ **健康检查**
```dockerfile
HEALTHCHECK --start-period=60s
```
给予 60 秒的启动时间，确保数据加载完成

✅ **精简镜像**
- 使用 `.dockerignore` 排除无关文件
- 减小镜像体积，加快构建速度

### 4. Zeabur 配置（zeabur.json）

✅ **启动探针**
```json
"startupProbe": {
  "initialDelaySeconds": 30,
  "failureThreshold": 6
}
```
最多等待 60 秒（30 + 10×6）确保应用启动

## 部署步骤

### 方式一：通过 Zeabur Dashboard（推荐）

1. **登录 Zeabur**
   - 访问 https://zeabur.com
   - 连接你的 GitHub 账号

2. **创建新项目**
   - 点击 "New Project"
   - 选择你的代码仓库

3. **部署配置**
   - Zeabur 会自动检测 `Dockerfile` 和 `zeabur.json`
   - 等待自动构建和部署

4. **验证部署**
   - 访问分配的域名
   - 检查 `/health` 端点返回 `{"status": "healthy"}`

### 方式二：使用 Zeabur CLI

```bash
# 安装 Zeabur CLI
npm i -g @zeabur/cli

# 登录
zeabur auth login

# 部署
cd /path/to/八字智能体
zeabur deploy
```

## 测试 API

### 1. 健康检查
```bash
curl https://your-app.zeabur.app/health
```

预期响应：
```json
{
  "status": "healthy",
  "data_loaded": true
}
```

### 2. 八字计算
```bash
curl -X POST https://your-app.zeabur.app/bazi \
  -H "Content-Type: application/json" \
  -d '{
    "birth_time": "1990-01-15 08:30",
    "gender": "男"
  }'
```

## 本地测试

在部署前，可以先在本地测试：

```bash
# 安装依赖
pip install -r requirements.txt

# 方式1：使用 Flask 开发服务器
python app.py

# 方式2：使用 Gunicorn（推荐，与生产环境一致）
gunicorn -c gunicorn.conf.py app:app

# 测试健康检查
curl http://localhost:8000/health

# 测试八字计算
curl -X POST http://localhost:8000/bazi \
  -H "Content-Type: application/json" \
  -d '{"birth_time": "1990-01-15 08:30", "gender": "男"}'
```

## 性能优化建议

### 当前方案（已实现）
- ✅ 内存缓存，避免重复读取文件
- ✅ 单 Worker 模式，减少内存占用
- ✅ 合理的超时配置

### 未来可选优化
- 🔄 **使用数据库**：将 CSV 数据导入 SQLite/PostgreSQL
- 🔄 **Redis 缓存**：缓存常见查询结果
- 🔄 **多 Worker + 共享内存**：使用 Redis 或 Memcached 共享数据

## 监控和调试

### 查看日志
在 Zeabur Dashboard：
1. 进入项目页面
2. 点击 "Logs" 标签
3. 查看实时日志输出

### 常见错误排查

#### 502 Bad Gateway
- **原因**：应用启动失败或超时
- **解决**：检查日志，确认数据加载成功

#### 503 Service Unavailable
- **原因**：健康检查失败
- **解决**：访问 `/health` 端点检查状态

#### Out of Memory
- **原因**：内存不足
- **解决**：升级 Zeabur 套餐或进一步优化代码

## 文件清单

确保以下文件存在于项目根目录：

```
八字智能体/
├── app.py                 # 主应用（已优化）
├── gunicorn.conf.py       # Gunicorn 配置（新增）
├── Dockerfile             # Docker 镜像配置（已优化）
├── requirements.txt       # Python 依赖（已更新）
├── zeabur.json           # Zeabur 配置（新增）
├── .dockerignore         # Docker 忽略文件（新增）
└── data.csv              # 数据文件（必须）
```

## 注意事项

⚠️ **不要使用 bazi_data_split 文件夹**
- 已经通过内存优化解决了大文件问题
- 使用完整的 `data.csv` 文件
- 分拆数据会增加查询复杂度

⚠️ **确保 data.csv 编码为 GBK**
- 代码中使用 `encoding='gbk'` 读取
- 如果文件编码不对，会导致启动失败

⚠️ **Zeabur 免费套餐限制**
- 内存：512MB
- 如果仍然遇到内存问题，考虑升级套餐

## 支持

如果部署后仍有问题：
1. 检查 Zeabur 日志输出
2. 确认 `/health` 端点状态
3. 验证 `data.csv` 文件完整性
4. 查看是否有内存或超时错误
