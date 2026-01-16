# 八字智能体 API

基于 Flask 的八字命理计算 API 服务，支持计算八字命盘、起运信息和大运。

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py

# 或使用 Gunicorn（生产环境）
gunicorn -c gunicorn.conf.py app:app
```

### Docker 运行

```bash
# 构建镜像
docker build -t bazi-api .

# 运行容器
docker run -p 8000:8000 bazi-api
```

## API 使用

### 健康检查

```bash
GET /health
```

响应：
```json
{
  "status": "healthy",
  "data_loaded": true
}
```

### 计算八字

```bash
POST /bazi
Content-Type: application/json

{
  "birth_time": "1990-01-15 08:30",
  "gender": "男"
}
```

响应示例：
```json
{
  "基本信息": {
    "公历生日": "1990-01-15 08:30",
    "性别": "男"
  },
  "八字命盘": {
    "年柱": "己巳",
    "月柱": "丁丑",
    "日柱": "甲寅",
    "时柱": "戊辰"
  },
  "起运信息": {
    "方向": "顺行",
    "起运岁数": "2岁 8个月 15天后"
  },
  "大运（前九步）": {
    "2岁": "戊寅",
    "12岁": "己卯",
    "22岁": "庚辰",
    ...
  }
}
```

## Zeabur 部署

详细部署指南请查看：
- [DEPLOYMENT.md](DEPLOYMENT.md) - 完整部署指南
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 故障排查指南

### 快速部署

1. 推送代码到 Git 仓库
2. 在 Zeabur 导入项目
3. 等待自动构建和部署
4. 访问分配的域名

### 关键配置

确保以下文件存在：
- ✅ `Dockerfile` - Docker 镜像配置  
- ✅ `gunicorn.conf.py` - Gunicorn 配置（动态端口）
- ✅ `zeabur.json` - Zeabur 平台配置
- ✅ `data.csv` - 八字数据文件

## 性能优化

### 当前方案
- ✅ 应用启动时预加载数据到内存
- ✅ 单 Worker 模式避免重复加载
- ✅ 动态端口绑定（适配云平台）

### 可选优化（如遇内存问题）
```bash
# 转换 CSV 为 SQLite 数据库
python convert_to_sqlite.py
```

详见 `convert_to_sqlite.py` 脚本。

## 项目结构

```
八字智能体/
├── app.py                    # Flask 主应用
├── gunicorn.conf.py          # Gunicorn 配置
├── start.py                  # 启动脚本（调试用）
├── Dockerfile                # Docker 配置
├── requirements.txt          # Python 依赖
├── zeabur.json              # Zeabur 配置
├── Procfile                 # 启动命令
├── data.csv                 # 八字数据（必需）
├── convert_to_sqlite.py     # CSV 转 SQLite 工具
├── DEPLOYMENT.md            # 部署指南
├── TROUBLESHOOTING.md       # 故障排查
└── README.md                # 本文件
```

## 依赖

- Python 3.9+
- Flask 2.3+
- Pandas 2.0+
- Gunicorn 21.0+

## 许可

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
