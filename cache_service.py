import redis
import os
import json
import base64
import re
import logging
from typing import List, Dict, Optional, Union

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建控制台处理器（如果还没有的话）
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class CacheService:
    """
    Redis缓存服务类，用于处理翻译结果的缓存
    """
    
    def __init__(self):
        """
        初始化Redis连接
        """
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_db = int(os.getenv("REDIS_DB", 0))
        
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        
        # 句子级缓存TTL（30分钟）
        self.sentence_ttl = 30 * 60
        # 单词级缓存TTL（60分钟）
        self.word_ttl = 60 * 60
        
        logger.info(f"Redis缓存服务初始化完成，连接地址: {redis_host}:{redis_port}, 数据库: {redis_db}")
    
    def _generate_cache_key(self, key_type: str, text: str, target_language: str, 
                           model_name: str, extra_args: Optional[dict] = None) -> str:
        """
        生成缓存键
        
        Args:
            key_type: 键类型 ('sentence', 'word')
            text: 文本内容
            target_language: 目标语言
            model_name: 模型名称
            extra_args: 额外参数
            
        Returns:
            生成的缓存键
        """
        # 清理文本，移除非字母数字字符（保留中文、英文字母和数字）
        if key_type == "word":
            cleaned_text = re.sub(r'[^\w\u4e00-\u9fff]', '', text, flags=re.UNICODE)
            if not cleaned_text:
                # 如果清理后为空，使用原始文本
                logger.warning(f"单词清理后为空，使用原始文本生成缓存键: {text}")
                cleaned_text = text
            text = cleaned_text
        
        # 构造键数据
        key_data = f"{key_type}:{text}:{target_language}:{model_name}"
        if extra_args:
            extra_str = json.dumps(extra_args, sort_keys=True)
            key_data += f":{extra_str}"
            
        # 生成键名：可读部分 + 编码部分
        readable_part = text[:30].replace(' ', '_')
        encoded_part = base64.b64encode(key_data.encode()).decode()[:20]
        final_key = f"{readable_part}_{encoded_part}"
        
        return final_key
    
    def get_sentence_cache(self, text: str, target_language: str, model_name: str, 
                          extra_args: Optional[dict] = None) -> Optional[str]:
        """
        获取句子级缓存
        
        Args:
            text: 要翻译的句子
            target_language: 目标语言
            model_name: 模型名称
            extra_args: 额外参数
            
        Returns:
            缓存的翻译结果，如果没有则返回None
        """
        

        cache_key = self._generate_cache_key("sentence", text, target_language, model_name, extra_args)
        
        result = self.redis_client.get(cache_key)
        
        if result:
            # logger.info(f"已在缓存中找到句子翻译结果: {text}")
            # full_cache_key = self._generate_cache_key("sentence", text, target_language, model_name, extra_args)
            # logger.debug(f"命中句子级缓存: {full_cache_key}")
            pass
        else:
            # logger.info(f"未在缓存中找到句子翻译结果，将调用模型API: {text}")
            # logger.debug(f"生成缓存键: {cache_key} (类型: sentence)")
            pass
            
        return result
    
    def set_sentence_cache(self, text: str, target_language: str, model_name: str, 
                          translated_text: str, extra_args: Optional[dict] = None) -> bool:
        """
        设置句子级缓存
        
        Args:
            text: 原始句子
            target_language: 目标语言
            model_name: 模型名称
            translated_text: 翻译结果
            extra_args: 额外参数
            
        Returns:
            是否设置成功
        """
        cache_key = self._generate_cache_key("sentence", text, target_language, model_name, extra_args)
        result = self.redis_client.setex(cache_key, self.sentence_ttl, translated_text)
        
        if result:
            logger.debug(f"句子级缓存设置成功: {cache_key}")
        else:
            logger.error(f"句子级缓存设置失败: {cache_key}")
            
        return result
    
    def get_word_cache(self, word: str, target_language: str, model_name: str, 
                      extra_args: Optional[dict] = None) -> Optional[str]:
        """
        获取单词级缓存
        
        Args:
            word: 要翻译的单词
            target_language: 目标语言
            model_name: 模型名称
            extra_args: 额外参数
            
        Returns:
            缓存的翻译结果，如果没有则返回None
        """
        # 先检查缓存，避免不必要的缓存键生成
        key_type = "word"
        # 清理文本，移除非字母数字字符（保留中文、英文字母和数字）
        cleaned_text = re.sub(r'[^\w\u4e00-\u9fff]', '', word, flags=re.UNICODE)
        if not cleaned_text:
            # 如果清理后为空，使用原始文本
            logger.warning(f"单词清理后为空，使用原始文本生成缓存键: {word}")
            cleaned_text = word
        cache_text = cleaned_text
        
        # 构造初步的键数据用于检查缓存
        key_data = f"{key_type}:{cache_text}:{target_language}:{model_name}"
        if extra_args:
            extra_str = json.dumps(extra_args, sort_keys=True)
            key_data += f":{extra_str}"
            
        # 生成可读部分
        readable_part = cache_text[:30].replace(' ', '_')
        # 先使用部分数据生成初步键
        encoded_part = base64.b64encode(key_data[:50].encode()).decode()[:10]
        cache_key = f"{readable_part}_{encoded_part}"
        
        result = self.redis_client.get(cache_key)
        
        if result:
            # logger.info(f"已在缓存中找到单词翻译结果: {word}")
            # full_cache_key = self._generate_cache_key("word", cache_text, target_language, model_name, extra_args)
            # logger.debug(f"命中单词级缓存: {full_cache_key}")
            pass
        else:
            # logger.info(f"未在缓存中找到单词翻译结果，将调用模型API: {word}")
            # logger.debug(f"生成缓存键: {cache_key} (类型: word)")
            pass
            
        return result
    
    def set_word_cache(self, word: str, target_language: str, model_name: str, 
                      translated_word: str, extra_args: Optional[dict] = None) -> bool:
        """
        设置单词级缓存
        
        Args:
            word: 原始单词
            target_language: 目标语言
            model_name: 模型名称
            translated_word: 翻译结果
            extra_args: 额外参数
            
        Returns:
            是否设置成功
        """
        cache_key = self._generate_cache_key("word", word, target_language, model_name, extra_args)
        result = self.redis_client.setex(cache_key, self.word_ttl, translated_word)
        
        if result:
            logger.debug(f"单词级缓存设置成功: {cache_key}")
        else:
            logger.error(f"单词级缓存设置失败: {cache_key}")
            
        return result

# 创建全局缓存服务实例
cache_service = CacheService()