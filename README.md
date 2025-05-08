# 🚀 GitHub Trending Agent

![preview](./assets/preview.png)

这是一个使用 FastAPI 和 SQLModel 构建的 GitHub Trending Agent 服务。它可以爬取 GitHub 热门仓库和开发者信息，使用 AI 生成总结，并提供 RSS feed。项目包含后端 API 服务和前端 Web 界面。

## ✨ 功能特点

-   🐙 支持爬取 GitHub 热门仓库和开发者信息
-   🤖 使用 OpenAI API 生成 AI 总结
-   🌍 支持多种语言（通过 summary_language 参数）
-   ⏰ 支持不同时间范围（daily、weekly、monthly）
-   💾 使用 SQLite 数据库存储数据，避免重复生成总结
-   📡 提供 RSS feed 输出
-   🎨 美观的 Web 界面，支持响应式设计
-   🔍 支持按语言筛选和搜索

## 🛠️ 技术栈

### 后端

-   FastAPI
-   SQLModel
-   OpenAI API
-   SQLite

### 前端

-   Tailwind CSS
-   Jinja2

## 📦 安装

1. 克隆仓库：

```bash
git clone https://github.com/timlzh/github-trending-agent.git
cd github-trending-agent
cp .env.example .env # 创建 .env 文件并按需设置环境变量
```

2. 安装依赖：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## 🚀 运行

1. 启动服务：

```bash
python3 -m app.main
```

服务将在 http://localhost:8000 启动。

## 📡 API 使用

### 获取热门仓库 RSS Feed

```
GET /api/trending/repositories/{since}
```

参数：

-   `since`: daily, weekly, 或 monthly

示例：

```
http://localhost:8000/api/trending/repositories/daily
```

## 📁 项目结构

```
.
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 应用入口
│   ├── models.py         # SQLModel 模型定义
│   ├── database.py       # 数据库配置
│   ├── static/          # 静态文件
│   │   ├── css/        # CSS 文件
│   │   └── js/         # JavaScript 文件
│   ├── templates/       # HTML 模板
│   ├── services/
│   │   ├── __init__.py
│   │   ├── github.py    # GitHub 爬虫服务
│   │   ├── ai.py        # AI 总结服务
│   │   └── rss.py       # RSS 生成服务
│   └── api/
│       ├── __init__.py
│       └── routes.py    # API 路由
├── requirements.txt     # Python 依赖
├── package.json        # Node.js 依赖
├── tailwind.config.js  # Tailwind 配置
└── README.md
```

## 🤝 贡献

欢迎提交 Pull Request 或创建 Issue！

## 📝 许可证

MIT
