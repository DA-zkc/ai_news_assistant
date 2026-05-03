# AI 要闻助手

一个基于多模型 AI 流水线的新闻摘要生成项目。该项目自动从 `GNews API` 采集 AI 相关新闻，使用 `DeepSeek` 和 `Qwen` 进行质量筛选、事实/观点提取与核心事件分析，最后生成规范的 Markdown 新闻摘要。

## 项目特点

- 支持自动获取 AI 相关新闻
- 使用多模型进行质量评分与事实/观点解析
- 提取核心事件并进行相似事件合并
- 生成可直接发布的中文 Markdown 报告
- 提供可配置的命令行入口

## 目录结构

```text
ai_news_assistant/
├── main.py             # 项目入口
├── modules/            # 核心处理模块
│   ├── fetcher.py      # 新闻抓取
│   ├── filter.py       # DeepSeek 质量筛选
│   ├── fact_opinion.py # Qwen 事实/观点提取
│   ├── core_event.py   # 核心事件提取
│   ├── merger.py       # 相似事件合并与可信度评分
│   ├── output.py       # Markdown 输出生成
│   └── __init__.py
├── requirements.txt    # Python 依赖
├── .gitignore          # Git 忽略规则
├── .env                # API 密钥配置（不提交）
├── tests/              # 测试文件
└── utils/              # 辅助工具模块
```

## 环境要求

- Python 3.10+
- 建议使用虚拟环境（`venv` / `.venv`）

## 安装依赖

```bash
python -m pip install -r requirements.txt
```

## 配置 API 密钥

在项目根目录创建 `.env` 文件，填写如下内容：

```text
GNEWS_API_KEY=your_gnews_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key
```

> 注意：`.env` 已加入 `.gitignore`，请勿将真实密钥提交到版本库。

## 使用方式

### 运行默认流程

```bash
python main.py
```

### 运行指定输出文件

```bash
python main.py --out ai_news_today.md
```

### 运行指定日期

```bash
python main.py --date 2026-05-02
```

### 启用调试模式

```bash
python main.py --debug
```

### 禁用 Qwen 描述生成（加快速度）

```bash
python main.py --no-qwen
```

### 参考参数说明

- `--date`：指定输出日期，格式为 `YYYY-MM-DD`
- `--out`：Markdown 输出文件名
- `--eps`：DBSCAN 聚类参数，值越小聚类越严格
- `--debug`：打印更详细日志
- `--no-qwen`：不调用 Qwen 生成聚类描述

## 提交前建议

- 确保 `.env` 不被提交
- 确认 `requirements.txt` 与当前环境一致
- 运行一次 `python main.py --no-qwen --debug` 验证项目可用

## 代码说明

- `modules/fetcher.py`：负责从 `GNews API` 拉取新闻并做初步数据清洗
- `modules/filter.py`：调用 `DeepSeek` 对新闻进行质量筛选
- `modules/fact_opinion.py`：使用 `Qwen` 提取事实和观点结构
- `modules/core_event.py`：提取新闻中的核心事件并计算接受度
- `modules/merger.py`：对相似事件进行合并与可信度评分
- `modules/output.py`：生成最终 Markdown 报告

## 贡献与扩展

如果需要进一步完善项目，可以考虑：

- 增加本地单元测试与 CI 验证
- 支持更多新闻源
- 提供 Web 或桌面可视化界面
- 添加语言切换、摘要风格配置等功能
