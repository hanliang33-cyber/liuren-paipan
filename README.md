# 大六壬在线排盘系统

基于 Flask API + HTML 前端的六壬占卜排盘工具，支持单事占卜、终身论命、八字排盘三种模式。

## 项目结构

```
liuren-paipan/
├── frontend.html          # 前端页面（独立HTML，可部署到任意静态托管）
├── flask-api/
│   ├── app.py              # Flask API 服务
│   ├── liuren_core.py      # 核心排盘逻辑
│   ├── jieqi.json          # 节气数据
│   ├── pylib/              # 依赖库
│   ├── templates/          # Jinja2 模板（与flask-api集成时使用）
│   └── Dockerfile          # 容器化部署
└── README.md
```

## 快速部署

### 本地运行（Docker）

```bash
cd flask-api
docker build -t liuren-paipan .
docker run -d -p 19130:5000 --name liuren-paipan liuren-paipan
```

访问 http://localhost:19130

### 软路由部署（iStoreOS/OpenWrt）

已在 iStoreOS Docker 中验证通过，配置文件在 `/etc/config/dockerd`，容器管理通过 1Panel。

## 前端独立使用

`frontend.html` 是纯前端版本，可以直接在任何静态托管服务（GitHub Pages、Vercel、Netlify 等）上部署，通过 CORS 调用远程 API。

默认 API 地址为 `/api/paipan`，如需更换后端地址，修改 `frontend.html` 中的 `fetch('/api/paipan', ...)` 为完整 URL。

## Bug 修复说明（2026-05-14）

**已知问题**：时间选择下拉框点击无响应、起课/现在时辰按钮点击无效

**可能原因**：初始化逻辑缺失。页面底部直接调用 `doCalc()` 但年/月/日/时的 `<select>` 选项从未通过 JS 填充，导致 `.value` 为空，操作卡死。

**排查建议**：
1. 浏览器 DevTools Console 有无 JS 报错？
2. `<select id="year">` 内是否有 `<option>` 元素？（检查浏览器 Elements 面板）
3. `toggleMode()` 是否正常触发？
4. 若使用浏览器缓存，尝试 Ctrl+Shift+R 强制刷新

## API 接口

### 占卜排盘
```
POST /api/paipan
Content-Type: application/json
{
  "year": 2026,
  "month": 5,
  "day": 14,
  "hour": 9,
  "yuejiang": "auto",
  "zhanshi": "学业",
  "guiren": "auto",
  "shunni": "auto"
}
```

### 终身论命
```
POST /api/zhongshen
{
  "year": 1983,
  "month": 1,
  "day": 23,
  "hour": 13,
  "minute": 45,
  "name": "韩亮"
}
```

### 八字排盘
```
POST /api/bazi
{
  "year": 2026,
  "month": 5,
  "day": 14,
  "hour": 14,
  "gender": "男"
}
```

## 技术栈

- **前端**：原生 HTML + CSS + JavaScript，无框架依赖
- **后端**：Flask (Python 3.11)
- **核心逻辑**：liuren_core.py（大六壬排盘引擎）
- **节气计算**：ephem（天文计算）+ 预计算 jieqi.json
- **部署**：Docker（支持 ARM64/x86_64）

## License

MIT