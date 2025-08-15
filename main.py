from fastapi import FastAPI
from schemas import TranslateRequest, TranslateResponse, TranslatedSegment, WordTranslateRequest, WordTranslateResponse
from model_service import translate_segments, translate_word
import uvicorn

app = FastAPI()

# 智慧译项目根路由
@app.get("/")
def wistrans():
    return {"message": "欢迎来到wistrans智慧译"}

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