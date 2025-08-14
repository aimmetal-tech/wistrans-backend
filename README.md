# 智慧译-后端 (Wistrans Backend)

智慧译是一个基于大语言模型的网页翻译服务，支持多种主流 AI 模型。

## 功能特性

- 支持多种大语言模型:
  - DeepSeek (deepseek-chat)
  - 阿里云百炼 (qwen-turbo-latest)
  - OpenAI (gpt-4o)
  - Moonshot Kimi (kimi-k2-0711-preview)
- 批量文本片段翻译
- 可自定义翻译风格
- RESTful API 接口

## 技术栈

- Python 3.8+
- FastAPI (Web 框架)
- Pydantic (数据验证)
- HTTPX (异步 HTTP 客户端)
- Uvicorn (ASGI 服务器)

## 安装与配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 .env.example 文件为 `.env` 并填入各平台的 API 密钥:

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入从各 AI 平台获取的 API 密钥。

### 3. 启动服务

```bash
python main.py
```

服务默认运行在 `http://localhost:8000`

## API 接口

### 翻译接口

```
POST /translate
```

#### 请求参数

| 参数名     | 类型   | 必填 | 说明                             |
| ---------- | ------ | ---- | -------------------------------- |
| target     | string | 是   | 目标语言，如 "en" 表示翻译为英语 |
| segments   | array  | 是   | 要翻译的文本片段列表             |
| extra_args | object | 否   | 翻译的额外要求，如风格等         |

#### segments 参数说明

| 参数名 | 类型   | 必填 | 说明                                        |
| ------ | ------ | ---- | ------------------------------------------- |
| id     | string | 是   | 片段 ID，用于标识片段以便返回到前端相应位置 |
| text   | string | 是   | 要翻译的文本内容                            |
| model  | string | 否   | 模型名称，默认为 "deepseek-chat"            |

#### 请求示例

```json
{
  "target": "en",
  "segments": [
    {
      "id": "segment1",
      "text": "这是要翻译的文本"
    },
    {
      "id": "segment2",
      "text": "这是另一段要翻译的文本",
      "model": "gpt-4o"
    }
  ],
  "extra_args": {
    "style": "每句开头加上`😭`，在每句翻译后加上`😊`"
  }
}
```

#### 响应示例

```json
{
  "translated": "en",
  "segments": [
    {
      "id": "segment1",
      "text": "😭This is the text to be translated😊"
    },
    {
      "id": "segment2",
      "text": "😭This is another text to be translated😊"
    }
  ]
}
```

## 支持的模型

| 模型名称             | 默认启用 | 提供商     |
| -------------------- | -------- | ---------- |
| deepseek-chat        | 是       | 深度求索   |
| qwen-turbo-latest    | 否       | 阿里云百炼 |
| gpt-4o               | 否       | OpenAI     |
| kimi-k2-0711-preview | 否       | 月之暗面   |

## 项目结构

```
.
├── main.py              # 主程序入口
├── schemas.py           # 数据模型定义
├── model_service.py     # 模型服务实现
├── requirements.txt     # 项目依赖
├── .env.example         # 环境变量示例
├── .env                 # 环境变量配置（需手动创建）
├── README.md            # 项目说明文档
└── docs/
    └── api.md           # API文档
```
