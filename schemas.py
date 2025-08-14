from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Segment(BaseModel):
    id: str
    text: str
    model: Optional[str] = "deepseek-chat"

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