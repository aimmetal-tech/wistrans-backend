api.md
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
| extra_args | object | 否   | 翻译的额外要求，如风格、身份等   |

#### segments 参数说明

| 参数名 | 类型   | 必填 | 说明                                        |
| ------ | ------ | ---- | ------------------------------------------- |
| id     | string | 是   | 片段 ID，用于标识片段以便返回到前端相应位置 |
| text   | string | 是   | 要翻译的文本内容                            |
| model  | string | 否   | 模型名称，默认为 "qwen-turbo-latest"            |

#### extra_args 参数说明

| 参数名   | 类型   | 必填 | 说明                                                                 |
| -------- | ------ | ---- | -------------------------------------------------------------------- |
| style    | string | 否   | 翻译的风格要求，如"每句开头加上`😭`，在每句翻译后加上`😊`"          |
| identity | string | 否   | 翻译专家的身份，可选值："通用专家"、"学术论文翻译师"、"意译作家"、"程序专家"、"古今中外翻译师" |

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
    "style": "每句开头加上`😭`，在每句翻译后加上`😊`",
    "identity": "意译作家"
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
  ]
}
```

### 2. OCR文字识别接口

#### 接口说明

用于识别图片中的文字内容，支持多语言文字识别

#### 接口地址

```
POST /ocr
```

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
| ------ | ------ | ---- | ---- |
| image | file | 是 | 图片文件，支持常见图片格式（JPG、PNG等） |

注意：该接口使用form-data格式上传文件

#### 请求示例

使用curl命令示例：
```bash
curl -X POST "http://localhost:8000/ocr" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@example.jpg"
```

#### 响应结果

| 参数名 | 类型 | 说明 |
| ------ | ------ | ---- |
| detected_text | array | 检测到的文本列表，包括文本内容、置信度和位置信息 |
| full_text | string | 完整的识别文本，每行文本以换行符分隔 |

##### detected_text元素说明

| 参数名 | 类型 | 说明 |
| ------ | ------ | ---- |
| text | string | 识别的文本内容 |
| confidence | float | 识别置信度，范围0-1，越接近1表示置信度越高 |
| coordinates | array | 文本框坐标，包含四个点的坐标信息 |

#### 响应示例

```json
{
  "detected_text": [
    {
      "text": "示例文本",
      "confidence": 0.9875345,
      "coordinates": [
        [10.0, 20.0],
        [100.0, 20.0],
        [100.0, 50.0],
        [10.0, 50.0]
      ]
    }
  ],
  "full_text": "示例文本"
}
```

### 3. 单词翻译接口

#### 接口说明

专门用于单词或短语翻译的接口，支持批量翻译多个单词

#### 接口地址

```
POST /trans-word
```

#### 请求参数

| 参数名     | 类型   | 必填 | 说明                             |
| ---------- | ------ | ---- | -------------------------------- |
| word       | array  | 是   | 要翻译的单词或短语列表           |
| target     | string | 否   | 目标语言，默认为"中文"           |
| model      | string | 否   | 模型名称，默认为"qwen-turbo-latest" |
| extra_args | object | 否   | 翻译的额外要求，如风格、身份等   |

#### word 参数说明

| 参数名 | 类型   | 必填 | 说明                                        |
| ------ | ------ | ---- | ------------------------------------------- |
| id     | string | 是   | 单词 ID，用于标识单词以便返回到前端相应位置 |
| word   | string | 是   | 要翻译的单词或短语内容                      |

#### extra_args 参数说明

| 参数名   | 类型   | 必填 | 说明                                                                 |
| -------- | ------ | ---- | -------------------------------------------------------------------- |
| style    | string | 否   | 翻译的风格要求，如"每句开头加上`😭`，在每句翻译后加上`😊`"          |
| identity | string | 否   | 翻译专家的身份，可选值："通用专家"、"学术论文翻译师"、"意译作家"、"程序专家"、"古今中外翻译师" |

#### 请求体示例

```json
{
  "word": [
    {
      "id": "word1",
      "word": "hello"
    },
    {
      "id": "word2",
      "word": "world"
    }
  ],
  "target": "中文",
  "extra_args": {
    "identity": "通用专家"
  }
}
```

#### 响应结果

```json
{
  "translated_word": [
    {
      "id": "word1",
      "word": "你好"
    },
    {
      "id": "word2",
      "word": "世界"
    }
  ]
}
```