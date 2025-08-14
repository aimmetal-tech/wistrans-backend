# API 接口文档

## 基础信息

- 服务器地址: `http://localhost:8000`
- 数据格式: JSON
- 字符编码: UTF-8

## 接口列表

### 1. 网页翻译接口

#### 接口说明

专门用于网页内容翻译的接口，支持批量翻译多个文本片段

#### 接口地址

```
POST /translate
```

#### 请求参数

| 参数名     | 类型   | 必填 | 说明                             |
| ---------- | ------ | ---- | -------------------------------- |
| target     | string | 是   | 目标语言，如 "en" 表示翻译为英语 |
| segments   | array  | 是   | 要翻译的文本片段列表             |
| extra_args | string | 否   | 翻译的额外要求，如风格等         |

#### segments 参数说明

| 参数名 | 类型   | 必填 | 说明                                        |
| ------ | ------ | ---- | ------------------------------------------- |
| id     | string | 是   | 片段 ID，用于标识片段以便返回到前端相应位置 |
| text   | string | 是   | 要翻译的文本内容                            |
| model  | string | 否   | 模型名称，默认为 "deepseek-chat"            |

#### 请求体示例

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
      "text": "这是另一段要翻译的文本"
    }
  ],
  "extra_args": {
    "style": "每句开头加上`😭`，在每句翻译后加上`😊`"
  }
}
```

#### 响应结果

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
  ],
}
```
