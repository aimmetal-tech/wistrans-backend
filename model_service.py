import os
import httpx
from typing import List
from schemas import Segment
import json
from dotenv import load_dotenv
import re
from langchain.prompts import PromptTemplate

# 加载环境变量
load_dotenv()

# 模型配置
MODEL_CONFIGS = {
    "deepseek-chat": {
        "url": "https://api.deepseek.com/chat/completions",
        "api_key_env": "DEEPSEEK_API_KEY"
    },
    "qwen-turbo-latest": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "api_key_env": "QWEN_API_KEY"
    },
    "gpt-4o": {
        "url": "https://api.openai.com/v1/chat/completions",
        "api_key_env": "OPENAI_API_KEY"
    },
    "kimi-k2-0711-preview": {
        "url": "https://api.moonshot.cn/v1/chat/completions",
        "api_key_env": "KIMI_API_KEY"
    }
}

# 定义翻译提示词模板
translation_prompt = PromptTemplate.from_template("""你是一个专业的翻译AI，请将以下文本翻译为{target_language}。

原始文本：
{text}

请严格按照以下格式输出，不要添加任何额外说明：
<translated_text>
[在此处输出翻译结果]
</translated_text>

{extra_instructions}""")

async def translate_text(text: str, target_language: str, model_name: str = "deepseek-chat", extra_args: dict = None) -> str:
    """
    调用大模型API进行文本翻译
    
    Args:
        text: 要翻译的文本
        target_language: 目标语言
        model_name: 使用的模型名称
        extra_args: 额外的翻译要求
    
    Returns:
        翻译后的文本
    """
    # 获取模型配置
    config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["deepseek-chat"])
    
    # 获取API密钥
    api_key = os.getenv(config["api_key_env"])
    if not api_key:
        raise ValueError(f"API密钥未配置: {config['api_key_env']}")
    
    # 构造额外说明
    extra_instructions = ""
    if extra_args and "style" in extra_args:
        extra_instructions = f"翻译风格要求: {extra_args['style']}"
    
    # 使用PromptTemplate生成提示词
    prompt = translation_prompt.format(
        target_language=target_language,
        text=text,
        extra_instructions=extra_instructions
    )
    
    # 构造请求头
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构造请求体
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    # 发送请求
    async with httpx.AsyncClient() as client:
        response = await client.post(config["url"], headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        
        result = response.json()
        translated_text = result["choices"][0]["message"]["content"]
        
        # 使用正则表达式提取标签内的内容
        match = re.search(r"<translated_text>(.*?)</translated_text>", translated_text, re.DOTALL)
        if match:
            # 提取标签内的内容并去除首尾空白
            return match.group(1).strip()
        else:
            # 如果没有找到标签，返回原始响应（向后兼容）
            return translated_text

async def translate_segments(segments: List[Segment], target_language: str, extra_args: dict = None) -> List[dict]:
    """
    批量翻译文本片段
    
    Args:
        segments: 文本片段列表
        target_language: 目标语言
        extra_args: 额外的翻译要求
    
    Returns:
        翻译结果列表
    """
    results = []
    
    for segment in segments:
        try:
            model_name = segment.model or "deepseek-chat"
            translated_text = await translate_text(segment.text, target_language, model_name, extra_args)
            results.append({
                "id": segment.id,
                "text": translated_text
            })
        except Exception as e:
            results.append({
                "id": segment.id,
                "text": f"翻译错误: {str(e)}"
            })
    
    return results