import base64
import io
import logging
from typing import Dict, List, Any
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建控制台处理器（如果还没有的话）
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 初始化PaddleOCR
# use_angle_cls=True表示使用方向分类器
# lang="ch"表示使用中英文模型
# 注意：新版本中use_angle_cls已弃用，应使用use_textline_orientation
ocr = PaddleOCR(use_textline_orientation=True, lang="ch")

def process_image_from_base64(image_base64: str) -> Dict[str, Any]:
    """
    处理base64编码的图片并进行OCR识别
    
    Args:
        image_base64 (str): base64编码的图片数据
        
    Returns:
        Dict[str, Any]: 包含检测到的文本和完整文本的字典
    """
    try:
        logger.info("开始处理图片OCR识别")
        
        # 移除base64字符串中的前缀（如果有）
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]
        
        # 将base64字符串解码为字节
        image_bytes = base64.b64decode(image_base64)
        
        # 将字节数据转换为PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # 转换为numpy数组供PaddleOCR使用
        image_np = np.array(image)
        
        # 使用PaddleOCR进行文字识别
        # 注意：在新版本中，返回结果的格式已更改
        result = ocr.ocr(image_np)
        
        # 处理识别结果
        detected_text = []
        full_text = ""
        
        # 新版本返回的是包含字典的列表
        if result is not None and len(result) > 0:
            # 获取第一个结果（通常只有一个结果）
            ocr_result = result[0] if isinstance(result, list) else result
            
            # 从新格式中提取文本和置信度
            if 'rec_texts' in ocr_result and 'rec_scores' in ocr_result and 'rec_polys' in ocr_result:
                # 新版本格式
                texts = ocr_result['rec_texts']
                scores = ocr_result['rec_scores']
                polys = ocr_result['rec_polys']
                
                for i in range(len(texts)):
                    text_info = {
                        "text": texts[i],
                        "confidence": float(scores[i]) if i < len(scores) else 0.0,
                        "coordinates": polys[i].tolist() if i < len(polys) else []
                    }
                    detected_text.append(text_info)
                    full_text += texts[i] + "\n"
            elif 'dt_polys' in ocr_result:
                # 如果检测到了文本框但没有识别文本，则可能是空结果
                pass
            else:
                # 尝试处理旧版本格式（以防万一）
                if isinstance(ocr_result, list):
                    for res in ocr_result:
                        if res is not None:
                            for line in res:
                                # 兼容旧版本格式
                                # line[0] 是文本框的坐标
                                # line[1][0] 是识别的文本
                                # line[1][1] 是置信度
                                try:
                                    text_info = {
                                        "text": line[1][0],
                                        "confidence": float(line[1][1]),
                                        "coordinates": line[0]  # 文本框坐标
                                    }
                                    detected_text.append(text_info)
                                    full_text += line[1][0] + "\n"
                                except (IndexError, TypeError) as e:
                                    # 如果格式不匹配，则跳过该项
                                    logger.warning("跳过无法解析的OCR结果项: %s", str(e))
        
        logger.info("OCR识别完成，共识别到 %d 条文本", len(detected_text))
        
        return {
            "detected_text": detected_text,
            "full_text": full_text.strip()
        }
        
    except Exception as e:
        logger.error("OCR处理过程中发生错误: %s", str(e))
        raise Exception(f"OCR处理失败: {str(e)}")