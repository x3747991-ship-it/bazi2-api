# 八字 API - Zeabur 部署故障排查

## 当前问题分析

从日志看到：
```
[2026-01-16 00:50:08 +0000] [14] [INFO] Booting worker with pid: 14
[2026-01-16 00:50:08 +0000] [15] [INFO] Booting worker with pid: 15
```

### 发现的问题

1. ✅ **应用启动成功** - 数据加载完成（51135 条记录）
2. ⚠️ **启动了 2 个 worker** - 配置文件设置是 1 个，但实际启动了 2 个
3. ❌ **502 错误** - Zeabur 无法访问应用

### 根本原因

**端口不匹配**：Zeabur 使用动态端口（通过 `PORT` 环境变量），而应用可能监听在固定端口 8000。

## 修复方案

### 已完成的优化

1. ✅ **动态端口绑定** - `gunicorn.conf.py` 现在从 `PORT` 环境变量读取端口
2. ✅ **移除固定端口的健康检查** - Docker 健康检查使用固定端口会失败
3. ✅ **添加启动日志** - 显示实际使用的端口和环境变量
4. ✅ **简化配置** - 移除可能冲突的 zeabur.json 配置

### 文件变更清单

| 文件 | 变更 |
|------|------|
| `gunicorn.conf.py` | ✏️ 使用 `PORT` 环境变量 |
| `Dockerfile` | ✏️ 移除健康检查，使用启动脚本 |
| `start.py` | ✨ 新增：启动脚本，显示调试信息 |
| `zeabur.json` | ✏️ 简化配置 |
| `Procfile` | ✨ 新增：明确启动命令 |

## 立即部署步骤

### 方式 1：Git Push（推荐）

```bash
cd "c:\Users\hfcb\Desktop\八字智能体"

# 提交所有更改
git add .
git commit -m "修复: 使用动态端口解决 502 错误"
git push

# Zeabur 会自动检测并重新部署
```

### 方式 2：手动上传

1. 在 Zeabur Dashboard 中删除当前服务
2. 创建新服务并上传以下文件：
   - `app.py`
   - `gunicorn.conf.py`
   - `start.py`
   - `Dockerfile`
   - `requirements.txt`
   - `data.csv`
   - `zeabur.json`
   - `Procfile`

## 部署后验证

### 1. 查看日志

重点关注以下信息：

```
[启动] 使用端口: XXXX
PORT 环境变量: XXXX
```

**如果看到**：
- `PORT 环境变量: 未设置` ❌ **有问题**
- `PORT 环境变量: 8080` ✅ **正常**（或其他端口号）

### 2. 测试健康检查

部署成功后，访问：
```
https://your-app.zeabur.app/health
```

应该返回：
```json
{
  "status": "healthy",
  "data_loaded": true
}
```

### 3. 测试 API

```bash
curl -X POST https://your-app.zeabur.app/bazi \
  -H "Content-Type: application/json" \
  -d '{"birth_time": "1990-01-15 08:30", "gender": "男"}'
```

## 如果仍然 502

### 检查项 1：Worker 数量

如果日志显示启动了多个 worker，说明 Zeabur 可能覆盖了配置。

**解决方案**：在 Zeabur Dashboard 设置环境变量
```
WEB_CONCURRENCY=1
```

### 检查项 2：端口环境变量

查看日志中的 `PORT 环境变量` 输出。

**如果是"未设置"**：
- Zeabur 可能没有设置 PORT
- 尝试在 Zeabur Dashboard 手动添加环境变量 `PORT=8000`

### 检查项 3：内存限制

51135 条记录 + Pandas 可能仍然占用较多内存。

**解决方案**：
1. 升级 Zeabur 套餐（增加内存限制）
2. 或使用数据库替代 CSV 文件

## 终极解决方案：使用 SQLite

如果上述方案仍然失败，建议将 CSV 转为 SQLite：

### 优势
- ✅ 内存占用极低（按需加载）
- ✅ 查询速度更快
- ✅ 无需预加载所有数据

### 简单实现
```python
import sqlite3
# 启动时创建数据库连接
conn = sqlite3.connect('bazi.db')
# 查询时直接使用 SQL
cursor.execute("SELECT * FROM bazi WHERE date = ?", (birth_date,))
```

**需要帮助实现？告诉我，我可以为你转换！**

## 调试技巧

### 查看完整启动日志

在 Zeabur Dashboard：
1. 进入项目 → 选择服务
2. 点击 "Logs" 标签
3. 确认看到：
   ```
   数据加载成功，共 51135 条记录
   八字 API 服务启动中...
   PORT 环境变量: XXXX
   Worker XX 已启动
   ```

### 本地模拟 Zeabur 环境

```bash
# Windows PowerShell
$env:PORT="3000"
python start.py

# 测试
curl http://localhost:3000/health
```

## 需要立即帮助？

如果部署后仍然失败，请提供：
1. ✅ 完整的启动日志（前 50 行）
2. ✅ Zeabur 的错误页面截图
3. ✅ 确认是否设置了 PORT 环境变量

我会根据具体情况进一步诊断！
