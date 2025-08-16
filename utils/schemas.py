from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Segment(BaseModel):
    id: str
    text: str
    model: Optional[str] = "qwen-turbo-latest"

class TranslateRequest(BaseModel):
    target: str
    segments: List[Segment]
    extra_args: Optional[Dict[str, Any]] = None

class TranslatedSegment(BaseModel):
    id: str
    text: str

class TranslateResponse(BaseModel):
    translated: str
    segments: List[TranslatedSegment]

# 单词翻译相关模型
class WordItem(BaseModel):
    id: str
    word: str

class WordTranslateRequest(BaseModel):
    word: List[WordItem]
    target: Optional[str] = "中文"
    model: Optional[str] = "qwen-turbo-latest"
    extra_args: Optional[Dict[str, Any]] = None

class TranslatedWordItem(BaseModel):
    id: str
    word: str

class WordTranslateResponse(BaseModel):
    translated_word: List[TranslatedWordItem]

# OCR相关模型
class OCRRequest(BaseModel):
    image: str  # base64编码的图片数据

class OCRResponse(BaseModel):
    detected_text: List[Dict[str, Any]]  # 检测到的文本列表，包括文本内容和位置信息
    full_text: str  # 完整的识别文本