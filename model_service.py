import os
import httpx
from typing import List
from schemas import Segment
import json
from dotenv import load_dotenv
import re
from langchain.prompts import PromptTemplate
from cache_service import cache_service
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建控制台处理器（如果还没有的话）
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

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

# 定义身份角色描述
IDENTITY_DESCRIPTIONS = {
    "通用专家": "你是一个通用领域的翻译专家，擅长各种类型的文本翻译。",
    "学术论文翻译师": "你是一个专业的学术论文翻译师，擅长将学术论文准确翻译成目标语言，保持学术术语的准确性和语言的严谨性。",
    "意译作家": "你是一个专业的意译作家，擅长在翻译过程中保持原文的意境和风格，使译文更符合目标语言的文化背景和表达习惯。",
    "程序专家": "你是一个专业的程序专家，擅长翻译与编程、软件开发相关的技术文档，能够准确处理技术术语和代码注释。",
    "古今中外翻译师": "你是一个多语言的，阅读过古今中外名著的翻译专家，擅长将不同语言的文本翻译成目标语言，并熟悉中国谚语和中世纪英语或是谚语。"
}

# 定义翻译提示词模板
translation_prompt = PromptTemplate.from_template("""{identity_description}

请将以下文本翻译为{target_language}。

原始文本：
{text}

请严格按照以下格式输出，不要添加任何额外说明：
<translated_text>
[在此处输出翻译结果]
</translated_text>

{extra_instructions}""")

# 定义单词翻译提示词模板
word_translation_prompt = PromptTemplate.from_template("""{identity_description}

请将以下单词翻译为{target_language}。

原始单词：
{word}

请严格按照以下格式输出，不要添加任何额外说明：
<translated_word>
[在此处输出翻译结果]
</translated_word>

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
    # 首先检查句子级缓存
    cached_result = cache_service.get_sentence_cache(text, target_language, model_name, extra_args)
    if cached_result:
        logger.info(f"已在缓存中找到句子翻译结果: {text}")
        full_cache_key = cache_service._generate_cache_key("sentence", text, target_language, model_name, extra_args)
        logger.debug(f"命中句子级缓存: {full_cache_key}")
        return cached_result
    else:
        logger.info(f"未在缓存中找到句子翻译结果，将调用模型API: {text}")
        cache_key = cache_service._generate_cache_key("sentence", text, target_language, model_name, extra_args)
        logger.debug(f"生成缓存键: {cache_key} (类型: sentence)")
    
    # 获取模型配置
    config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["deepseek-chat"])
    
    # 获取API密钥
    api_key = os.getenv(config["api_key_env"])
    if not api_key:
        raise ValueError(f"API密钥未配置: {config['api_key_env']}")
    
    # 获取身份角色描述
    identity = extra_args.get("identity") if extra_args else None
    identity_description = IDENTITY_DESCRIPTIONS.get(identity, "你是一个专业的翻译AI")
    
    # 构造额外说明
    extra_instructions = ""
    if extra_args and "style" in extra_args:
        extra_instructions = f"翻译风格要求: {extra_args['style']}"
    
    # 使用PromptTemplate生成提示词
    prompt = translation_prompt.format(
        identity_description=identity_description,
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
            translated_text = match.group(1).strip()
        else:
            # 如果没有找到标签，返回原始响应（向后兼容）
            translated_text = translated_text
        
        # 将翻译结果存入句子级缓存
        cache_service.set_sentence_cache(text, target_language, model_name, translated_text, extra_args)
        # 日志已在cache_service中打印
        
        return translated_text

async def translate_word(word: str, target_language: str, model_name: str = "deepseek-chat", extra_args: dict = None) -> str:
    """
    调用大模型API进行单词翻译
    
    Args:
        word: 要翻译的单词
        target_language: 目标语言
        model_name: 使用的模型名称
        extra_args: 额外的翻译要求
    
    Returns:
        翻译后的单词
    """
    # 首先检查单词级缓存
    cached_result = cache_service.get_word_cache(word, target_language, model_name, extra_args)
    if cached_result:
        logger.info(f"已在缓存中找到单词翻译结果: {word}")
        full_cache_key = cache_service._generate_cache_key("word", word, target_language, model_name, extra_args)
        logger.debug(f"命中单词级缓存: {full_cache_key}")
        return cached_result
    else:
        logger.info(f"未在缓存中找到单词翻译结果，将调用模型API: {word}")
        cache_key = cache_service._generate_cache_key("word", word, target_language, model_name, extra_args)
        logger.debug(f"生成缓存键: {cache_key} (类型: word)")
    
    # 获取模型配置
    config = MODEL_CONFIGS.get(model_name, MODEL_CONFIGS["deepseek-chat"])
    
    # 获取API密钥
    api_key = os.getenv(config["api_key_env"])
    if not api_key:
        raise ValueError(f"API密钥未配置: {config['api_key_env']}")
    
    # 获取身份角色描述
    identity = extra_args.get("identity") if extra_args else None
    identity_description = IDENTITY_DESCRIPTIONS.get(identity, "你是一个专业的翻译AI")
    
    # 构造额外说明
    extra_instructions = ""
    if extra_args and "style" in extra_args:
        extra_instructions = f"翻译风格要求: {extra_args['style']}"
    
    # 使用PromptTemplate生成提示词
    prompt = word_translation_prompt.format(
        identity_description=identity_description,
        target_language=target_language,
        word=word,
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
        "temperature": 0.3  # 单词翻译使用较低的温度值以获得更一致的结果
    }
    
    # 发送请求
    async with httpx.AsyncClient() as client:
        response = await client.post(config["url"], headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
        
        result = response.json()
        translated_word = result["choices"][0]["message"]["content"]
        
        # 使用正则表达式提取标签内的内容
        match = re.search(r"<translated_word>(.*?)</translated_word>", translated_word, re.DOTALL)
        if match:
            # 提取标签内的内容并去除首尾空白
            translated_word = match.group(1).strip()
        else:
            # 如果没有找到标签，返回原始响应（向后兼容）
            translated_word = translated_word
        
        # 将翻译结果存入单词级缓存
        cache_service.set_word_cache(word, target_language, model_name, translated_word, extra_args)
        # 日志已在cache_service中打印
        
        return translated_word

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