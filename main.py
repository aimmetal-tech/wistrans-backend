from fastapi import FastAPI, UploadFile, File
from utils.schemas import TranslateRequest, TranslateResponse, TranslatedSegment, WordTranslateRequest, WordTranslateResponse, OCRResponse
from services.model_service import translate_segments, translate_word
from services.ocr_service import process_image_from_base64
import uvicorn
import logging
import base64

# 创建logger实例
logger = logging.getLogger(__name__)

app = FastAPI()

# 智慧译项目根路由
@app.get("/")
def wistrans():
    return {"message": "欢迎来到wistrans智慧译"}

# OCR接口
@app.post("/ocr", response_model=OCRResponse)
async def ocr_endpoint(image: UploadFile = File(...)):
    """
    OCR文字识别接口
    
    Args:
        image: 上传的图片文件
        
    Returns:
        OCR识别结果，包括检测到的文本列表和完整文本
    """
    try:
        logger.info("收到OCR请求")
        # 读取上传的图片文件并转换为base64
        image_bytes = await image.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        result = process_image_from_base64(image_base64)
        return OCRResponse(
            detected_text=result["detected_text"],
            full_text=result["full_text"]
        )
    except Exception as e:
        logger.error("OCR处理失败: %s", str(e))
        raise Exception(f"OCR处理失败: {str(e)}")

# 翻译接口
@app.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """
    网页翻译接口
    
    Args:
        request: 翻译请求参数
        
    Returns:
        翻译结果
    """
    try:
        translated_segments = await translate_segments(
            segments=request.segments,
            target_language=request.target,
            extra_args=request.extra_args
        )
        
        return TranslateResponse(
            translated=request.target,
            segments=translated_segments
        )
    except Exception as e:
        # 发生错误时也返回符合规范的响应格式
        error_segments = [
            TranslatedSegment(
                id=segment.id,
                text=f"翻译错误: {str(e)}"
            ) for segment in request.segments
        ]
        
        return TranslateResponse(
            translated=request.target,
            segments=error_segments
        )

# 单词翻译接口
@app.post("/trans-word", response_model=WordTranslateResponse)
async def trans_word(request: WordTranslateRequest):
    """
    单词翻译接口
    
    Args:
        request: 单词翻译请求参数
        
    Returns:
        单词翻译结果
    """
    try:
        translated_words = []
        target_language = request.target or "中文"
        model_name = request.model or "qwen-turbo-latest"
        
        for word_item in request.word:
            try:
                translated_word = await translate_word(
                    word=word_item.word,
                    target_language=target_language,
                    model_name=model_name,
                    extra_args=request.extra_args
                )
                translated_words.append({
                    "id": word_item.id,
                    "word": translated_word
                })
            except Exception as e:
                translated_words.append({
                    "id": word_item.id,
                    "word": f"翻译错误: {str(e)}"
                })
        
        return WordTranslateResponse(
            translated_word=translated_words
        )
    except Exception as e:
        # 发生错误时也返回符合规范的响应格式
        error_words = [
            {
                "id": word_item.id,
                "word": f"翻译错误: {str(e)}"
            } for word_item in request.word
        ]
        
        return WordTranslateResponse(
            translated_word=error_words
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)