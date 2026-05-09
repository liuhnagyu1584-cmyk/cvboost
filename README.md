# cvboost-agent-slim

简历优化专家 API 服务 — 基于 DeepSeek LLM，支持流式输出和文件上传。

## 项目结构

```
cvboost-agent-slim/
├── main.py                    # FastAPI 入口，路由定义
├── run.py                     # CLI 测试脚本（无需启动服务）
├── requirements.txt           # Python 依赖
├── .env                       # 环境变量（DEEPSEEK_API_KEY）
├── static/
│   └── index.html             # 前端 Demo（上传 + 流式展示）
├── agent/
│   ├── agent.py               # LLM 调用封装（同步 + 流式）
│   ├── config.py              # 配置常量
│   ├── parse_resume.py        # PDF / DOCX 文件解析
│   ├── system_prompt.py       # 系统提示词加载器
│   └── system_prompt.md       # 系统提示词正文
└── tests/
    ├── conftest.py            # 测试 fixture
    ├── test_agent.py          # Agent 单元测试
    └── test_system_prompt.py  # 提示词加载测试
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

在 `.env` 中填入 DeepSeek API Key：

```
DEEPSEEK_API_KEY = sk-xxxxxxxx
```

### 3. 启动服务

```bash
python main.py
```

服务运行在 `http://127.0.0.1:8000`，打开浏览器即可使用前端 Demo。

## API 接口

### `GET /health`

健康检查，返回服务状态和 SLA 配置。

```json
{
  "status": "ok",
  "model": "deepseek-v4-pro",
  "sla": { "accuracy": 0.90, "latency_ms": 3000, "concurrent_users": 10 }
}
```

### `POST /api/v1/optimize`

文本优化（非流式），返回完整优化报告。

**Request** (JSON)
```json
{
  "resume_text": "简历文本内容（必填）",
  "modules": ["工作经历", "项目经历"],
  "job_description": "目标岗位 JD（可选）",
  "industry": "目标行业（可选）"
}
```

**Response** (JSON)
```json
{
  "success": true,
  "report": "优化报告全文..."
}
```

### `POST /api/v1/optimize/stream`

文本优化（流式），SSE 方式逐字返回优化结果。

Request 格式同上，Response 为 `text/plain` 流，每个 chunk 是 LLM 生成的一个 token 文本。

### `POST /api/v1/optimize/file`

文件上传优化（非流式），支持 `.pdf` `.docx` `.doc`。

Request 为 `multipart/form-data`，字段名 `file`。Response 同 `/api/v1/optimize`。

### `POST /api/v1/optimize/file/stream`

文件上传优化（流式），上传后逐字返回优化结果。

## CLI 测试

不启动服务，直接在终端测试：

```bash
python run.py stream   # 流式输出（默认）
python run.py normal   # 完整输出
```

## 运行测试

```bash
pytest tests/ -v
```

## 配置说明

所有配置项见 [agent/config.py](agent/config.py)：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MODEL_NAME` | `deepseek-v4-pro` | 模型名称 |
| `MODEL_BASE_URL` | `https://api.deepseek.com` | API 地址 |
| `MODEL_API_KEY` | 从环境变量 `DEEPSEEK_API_KEY` 读取 | API Key |
| `LLM_TIMEOUT_SECONDS` | `60` | 请求超时 |
| `LLM_MAX_RETRIES` | `3` | 失败重试次数 |
| `THINKING_ENABLED` | `False` | 是否开启思考模式 |
