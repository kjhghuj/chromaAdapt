import os
import json
import base64
import requests
from io import BytesIO
from typing import List, Optional
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys from .env
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ARK_ENDPOINT_ID = os.getenv("ARK_ENDPOINT_ID", "") # Doubao-Seedream-4.5 Endpoint
ARK_ENDPOINT_ID_SEEDREAM_5_LITE = os.getenv("ARK_ENDPOINT_ID_SEEDREAM_5_LITE", "") # Doubao-Seedream-5.0-lite Endpoint
ARK_ANALYSIS_ENDPOINT_ID = os.getenv("ARK_ANALYSIS_ENDPOINT_ID", "") # Doubao-Seed-2-0-lite
ARK_ANALYSIS_ENDPOINT_ID_SEED_2_MINI = os.getenv("ARK_ANALYSIS_ENDPOINT_ID_SEED_2_MINI", "") # Doubao-Seed-2-0-mini
ARK_ANALYSIS_ENDPOINT_ID_SEED_2_PRO = os.getenv("ARK_ANALYSIS_ENDPOINT_ID_SEED_2_PRO", "") # Doubao-Seed-2-0-pro

def get_image_dimensions_from_base64(base64_str: str) -> tuple:
    """Extract image dimensions from base64 encoded image data."""
    try:
        clean_base64 = base64_str.strip().replace("\n", "").replace("\r", "")
        if clean_base64.startswith("data:"):
            clean_base64 = clean_base64.split(",")[1]
        image_data = base64.b64decode(clean_base64)
        image = Image.open(BytesIO(image_data))
        return image.size  # (width, height)
    except Exception as e:
        print(f"Error getting image dimensions: {e}")
        return (1024, 1024)  # Default fallback

def calculate_size_for_aspect_ratio(width: int, height: int) -> str:
    """Calculate optimal size string maintaining aspect ratio for Seedream 5.0.
    Seedream 5.0 requires total pixels >= 3,686,400 (minimum 2K resolution)
    and aspect ratio between 1/16 and 16.
    """
    MIN_PIXELS = 3686400  # Minimum required pixels (2560x1440)
    MAX_PIXELS = 16777216  # Maximum allowed pixels (4096x4096)
    
    aspect_ratio = width / height
    print(f"Original image aspect ratio: {aspect_ratio:.2f} (W:{width} x H:{height})")
    
    # Calculate dimensions that satisfy minimum pixel requirement while maintaining aspect ratio
    if aspect_ratio >= 1:
        # Landscape or square: start with width, calculate height
        target_width = 2048
        target_height = int(target_width / aspect_ratio)
        
        # Ensure minimum pixels
        if target_width * target_height < MIN_PIXELS:
            target_height = int(MIN_PIXELS / target_width)
            target_width = int(target_height * aspect_ratio)
        
        # Ensure within aspect ratio limits
        target_width = max(1152, min(target_width, 4096))
        target_height = max(1152, min(target_height, 4096))
        
        # Final check and adjustment for maximum pixels
        total_pixels = target_width * target_height
        if total_pixels > MAX_PIXELS:
            scale = (MAX_PIXELS / total_pixels) ** 0.5
            target_width = int(target_width * scale)
            target_height = int(target_height * scale)
        
        return f"{target_width}x{target_height}"
    else:
        # Portrait: start with height, calculate width
        target_height = 2048
        target_width = int(target_height * aspect_ratio)
        
        # Ensure minimum pixels
        if target_width * target_height < MIN_PIXELS:
            target_width = int(MIN_PIXELS / target_height)
            target_height = int(target_width / aspect_ratio)
        
        # Ensure within aspect ratio limits
        target_width = max(1152, min(target_width, 4096))
        target_height = max(1152, min(target_height, 4096))
        
        # Final check and adjustment for maximum pixels
        total_pixels = target_width * target_height
        if total_pixels > MAX_PIXELS:
            scale = (MAX_PIXELS / total_pixels) ** 0.5
            target_width = int(target_width * scale)
            target_height = int(target_height * scale)
        
        return f"{target_width}x{target_height}"

# --- Models ---
class AnalyzeRequest(BaseModel):
    image: str # base64
    prompt: str = "分析这张图片的色彩、构图和主要内容，并以JSON格式返回色盘（包含一个名为 'palette' 的数组，内含5个十六进制颜色）。"
    model: Optional[str] = "doubao-seed-2-0-lite"

class AnalyzeEditRequest(BaseModel):
    image: str # base64
    user_instruction: str
    model: Optional[str] = "doubao-seed-2-0-lite"

class SecondaryPlanRequest(BaseModel):
    image: str # base64
    model: Optional[str] = "doubao-seed-2-0-lite"

class ColorMappingRequest(BaseModel):
    poster_image: str # base64
    reference_image: str # base64
    model: Optional[str] = "doubao-seed-2-0-lite"

class ColorAdaptRequest(BaseModel):
    poster_image: str # base64
    reference_image: str # base64
    palette: List[str] # target color palette
    style_config: Optional[dict] = None
    color_mapping_plan: Optional[str] = None
    model: Optional[str] = "doubao-seedream-4.5"

class GenerateRequest(BaseModel):
    prompt: str
    image_urls: Optional[List[str]] = None
    size: str = "2048x2048"
    model: Optional[str] = "doubao-seedream-4.5"

class EditRequest(BaseModel):
    image: str # base64
    prompt: str
    model: Optional[str] = "doubao-seedream-4.5"

class TranslateRequest(BaseModel):
    image: str # base64
    target_lang: str
    target_font: Optional[str] = "original"
    model: Optional[str] = "doubao-seedream-4.5"

# --- Endpoints ---

@app.post("/analyze")
async def analyze_image(req: AnalyzeRequest):
    """Uses Doubao-Seed-2.0 (Ark) for image analysis"""
    model = req.model or "doubao-seed-2-0-lite"

    if model == "doubao-seed-2-0-mini":
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID_SEED_2_MINI
    elif model == "doubao-seed-2-0-pro":
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID_SEED_2_PRO
    else:
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID

    if not ARK_API_KEY or not endpoint_id:
        raise HTTPException(status_code=500, detail="ARK_API_KEY or ARK_ANALYSIS_ENDPOINT_ID not configured")

    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }

    base64_data = req.image.strip().replace("\n", "").replace("\r", "")

    payload = {
        "model": endpoint_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": req.prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_data}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        print(f"Sending analysis request to model={model}, endpoint={endpoint_id}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if response.status_code != 200:
            print(f"Ark API Error Response: {response.text}")
            response.raise_for_status()
            
        return response.json()
    except Exception as e:
        print(f"Analysis Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Full Error Details: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Ark API Error: {e.response.text}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-edit")
async def analyze_edit_image(req: AnalyzeEditRequest):
    """Uses Doubao-Seed-2.0 model to deeply analyze image and generate professional edit prompt"""
    model = req.model or "doubao-seed-2-0-lite"

    if model == "doubao-seed-2-0-mini":
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID_SEED_2_MINI
    elif model == "doubao-seed-2-0-pro":
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID_SEED_2_PRO
    else:
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID

    if not ARK_API_KEY or not endpoint_id:
        raise HTTPException(status_code=500, detail="ARK_API_KEY or ARK_ANALYSIS_ENDPOINT_ID not configured")

    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }

    base64_data = req.image.strip().replace("\n", "").replace("\r", "")

    analysis_prompt = f"""你是一位专业的图像编辑专家和视觉设计师。请仔细分析这张图片，并结合用户的编辑指令，生成一个专业、详细的图像编辑提示词。

用户编辑指令：{req.user_instruction}

请从以下几个方面深度分析图片：
1. 主体内容：图片中的主要物体、人物或场景
2. 构图分析：画面布局、视觉焦点、景深效果
3. 色彩分析：整体色调、色彩层次、对比度
4. 光影分析：光源方向、阴影处理、光线氛围
5. 风格特征：设计风格、艺术流派、视觉语言
6. 技术细节：分辨率、清晰度、噪点、伪影
7. 背景环境：背景复杂度、边缘处理需求
8. 文字元素：是否有文字需要保留或移除

请生成一个专业的图像编辑提示词，包含：
- 详细的图像描述
- 具体的编辑指令
- 技术参数要求
- 风格参考
- 质量标准

提示词必须专业、精准、可执行性强，适合直接用于图像生成模型。"""

    payload = {
        "model": endpoint_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": analysis_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_data}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        print(f"Sending edit analysis request to model={model}, endpoint={endpoint_id}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            print(f"Ark API Error Response: {response.text}")
            response.raise_for_status()

        return response.json()
    except Exception as e:
        print(f"Edit Analysis Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Full Error Details: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Ark API Error: {e.response.text}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/secondary-plan")
async def generate_secondary_plan(req: SecondaryPlanRequest):
    """Uses Doubao-Seed-2.0 model to analyze image and generate secondary image plan"""
    model = req.model or "doubao-seed-2-0-lite"

    if model == "doubao-seed-2-0-mini":
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID_SEED_2_MINI
    elif model == "doubao-seed-2-0-pro":
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID_SEED_2_PRO
    else:
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID

    if not ARK_API_KEY or not endpoint_id:
        raise HTTPException(status_code=500, detail="ARK_API_KEY or ARK_ANALYSIS_ENDPOINT_ID not configured")

    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }

    base64_data = req.image.strip().replace("\n", "").replace("\r", "")

    plan_prompt = """你是一位专业的视觉设计师和创意策划专家。请分析这张图片，然后设计一个配套的"副图"方案。

副图是相对于主视觉海报的配套图片，通常用于：
- 社交媒体配图
- 详情页补充展示
- 广告投放的多尺寸素材
- 产品详情页的展示图

请从以下角度分析原图并生成副图规划：

1. **主体延续**：副图应保持与主图一致的主体元素或品牌调性
2. **构图变化**：提供不同构图方式的副图建议（如特写、全景、角度变化）
3. **尺寸适配**：针对不同用途（1:1方图、16:9横图、9:16竖图等）提供规划
4. **色彩风格**：副图应采用的色彩方案建议
5. **内容延展**：基于主图内容的创意延展方向

请生成一个JSON格式的副图规划，结构如下：
{
  "main_theme": "主图的核心主题或概念",
  "style": "整体风格描述",
  "suggestions": [
    {
      "type": "构图类型（如：product_closeup/broad_view/angle_variation等）",
      "description": "详细描述",
      "aspect_ratio": "建议尺寸比例（如1:1, 16:9, 9:16）",
      "prompt": "用于生成这张副图的详细提示词，包含主体、背景、构图、光线、色彩等所有细节"
    }
  ],
  "color_palette": ["主色调建议"],
  "notes": "其他注意事项或创意说明"
}

请确保生成的提示词具体、详细、可执行，适合直接用于图像生成模型。"""

    payload = {
        "model": endpoint_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": plan_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_data}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        print(f"Sending secondary plan request to model={model}, endpoint={endpoint_id}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            print(f"Ark API Error Response: {response.text}")
            response.raise_for_status()

        return response.json()
    except Exception as e:
        print(f"Secondary Plan Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Full Error Details: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Ark API Error: {e.response.text}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/color-mapping")
async def create_color_mapping(req: ColorMappingRequest):
    """Uses Doubao-Seed-2.0 model to analyze two images and create color mapping plan"""
    model = req.model or "doubao-seed-2-0-lite"

    if model == "doubao-seed-2-0-mini":
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID_SEED_2_MINI
    elif model == "doubao-seed-2-0-pro":
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID_SEED_2_PRO
    else:
        endpoint_id = ARK_ANALYSIS_ENDPOINT_ID

    if not ARK_API_KEY or not endpoint_id:
        raise HTTPException(status_code=500, detail="ARK_API_KEY or ARK_ANALYSIS_ENDPOINT_ID not configured")

    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }

    poster_clean = req.poster_image.strip().replace("\n", "").replace("\r", "")
    ref_clean = req.reference_image.strip().replace("\n", "").replace("\r", "")

    mapping_prompt = """你是一名顶级商业视觉设计师，擅长色彩理论与色彩迁移。
任务：分析两张图片（原始海报和参考图），生成专业的色彩映射方案。

请从以下角度进行深入分析：

1. **原图色彩分析**：
   - 主色调（5个主要颜色）
   - 色彩分布比例
   - 光影与对比度特征
   - 整体色调倾向（暖/冷/中性）

2. **参考图色彩分析**：
   - 主色调（5个主要颜色）
   - 色彩分布比例
   - 光影与对比度特征
   - 整体色调倾向

3. **色彩映射方案**：
   - 主体色彩的对应关系
   - 背景色彩的转换策略
   - 光影与高光的匹配方式
   - 整体氛围的迁移方法

请生成JSON格式的分析结果：
{
  "source_analysis": {
    "main_colors": ["#..."],
    "tone": "warm/cold/neutral",
    "contrast": "high/medium/low",
    "mood": "描述整体氛围"
  },
  "reference_analysis": {
    "main_colors": ["#..."],
    "tone": "warm/cold/neutral",
    "contrast": "high/medium/low",
    "mood": "描述整体氛围"
  },
  "color_mapping": [
    {"from": "#源色", "to": "#目标色", "area": "应用区域描述"}
  ],
  "style_notes": "风格迁移注意事项"
}"""

    payload = {
        "model": endpoint_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{mapping_prompt}\n\n下面是原始海报图片："},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{poster_clean}"}},
                    {"type": "text", "text": "\n\n下面是参考图片："},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{ref_clean}"}}
                ]
            }
        ]
    }

    try:
        print(f"Sending color mapping request to model={model}, endpoint={endpoint_id}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            print(f"Ark API Error Response: {response.text}")
            response.raise_for_status()

        return response.json()
    except Exception as e:
        print(f"Color Mapping Error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Full Error Details: {e.response.text}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Ark API Error: {e.response.text}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/color-adaptation")
async def color_adaptation(req: ColorAdaptRequest):
    """Color adaptation: adapt poster colors to match reference image style while preserving layout"""
    model = req.model or "doubao-seedream-4.5"
    if model == "doubao-seedream-5.0-lite":
        endpoint_id = ARK_ENDPOINT_ID_SEEDREAM_5_LITE
    else:
        endpoint_id = ARK_ENDPOINT_ID

    if not ARK_API_KEY or not endpoint_id:
        raise HTTPException(status_code=500, detail="Ark API Key or Endpoint ID not configured")

    try:
        width, height = get_image_dimensions_from_base64(req.poster_image)
        size = calculate_size_for_aspect_ratio(width, height)
        print(f"Color Adaptation - Using size: {size} (original: {width}x{height})")

        palette_text = ", ".join(req.palette) if isinstance(req.palette, list) else str(req.palette)

        style_rules = ""
        if req.style_config:
            rules = []
            if req.style_config.get("recolorTextOnly"):
                rules.append("仅迁移文字与UI颜色，产品、背景、材质、光影均保持原图")
            else:
                if req.style_config.get("replaceProduct"):
                    rules.append("产品区域同步迁移到参考图色调，保持产品形态与细节")
                else:
                    rules.append("产品区域尽量保持原色，仅做全局一致性微调")

                if req.style_config.get("keepLayout"):
                    rules.append("布局结构、元素位置、比例关系严格保持")
                else:
                    rules.append("允许轻微调整布局以增强与参考图色调匹配")

                if req.style_config.get("keepFonts"):
                    rules.append("字体字形、字重与排版层级保持不变，仅做必要颜色适配")
                else:
                    rules.append("允许字体视觉风格和颜色随参考图调性调整")

                if req.style_config.get("keepTexture"):
                    rules.append("材质纹理、颗粒感与表面细节保持原图风格")
                else:
                    rules.append("允许材质纹理色调向参考图风格迁移")

                if req.style_config.get("keepLighting"):
                    rules.append("光影方向、对比和高光关系保持原图")
                else:
                    rules.append("允许光影色温和强度向参考图风格迁移")

            style_rules = "元素迁移规则：" + "；".join(rules) if rules else ""

        mapping_guidance = f"参考色彩方案：[{palette_text}]。"
        if req.color_mapping_plan:
            mapping_guidance += f"\n工作流提示词：{req.color_mapping_plan}"

        gen_prompt = f"""你是一名顶级商业视觉设计师，擅长色彩迁移与风格适配。
任务：将原始海报的色彩方案转换为目标风格，同时完美保持原始布局、产品、文字等所有元素。
{mapping_guidance}
{style_rules}

严格遵守以下规则：
1、**色彩迁移**：将原图的整体色调、色彩关系、对比度等迁移到目标风格
2、**布局保真**：原始海报的布局、构图、文字位置、元素比例必须100%保持不变
3、**产品保真**：产品外观、形态、材质质感必须与原图完全一致，仅改变色彩
4、**文字保真**：所有文字必须保持原样（内容、字体、大小、位置）
5、**光影协调**：色彩转换后的光影效果必须自然协调，无生硬过渡
6、**边缘干净**：无色溢出、无halo效应、无明显合成痕迹
7、**质量标准**：高清细腻，色彩准确，视觉效果专业

输出：一张保持原始布局和内容的色彩适配版本海报。"""

        poster_clean = req.poster_image.strip().replace("\n", "").replace("\r", "")
        ref_clean = req.reference_image.strip().replace("\n", "").replace("\r", "")

        generation_result = await generate_image(GenerateRequest(
            prompt=gen_prompt,
            image_urls=[
                f"data:image/jpeg;base64,{poster_clean}",
                f"data:image/jpeg;base64,{ref_clean}"
            ],
            size=size,
            model=model
        ))

        image_url = generation_result.get("data", [{}])[0].get("url", "")
        if image_url:
            print(f"Downloading color adaptation result from: {image_url[:80]}...")
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            img_base64 = base64.b64encode(img_response.content).decode("utf-8")
            image_data_url = f"data:image/png;base64,{img_base64}"
            print("Color adaptation image downloaded successfully")
        else:
            image_data_url = req.poster_image
            print("No image URL in response, using original")

        return {"data": [{"url": image_data_url}]}

    except Exception as e:
        print(f"Color Adaptation Error: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/translate")
async def translate_image(req: TranslateRequest):
    """Direct translation using Doubao-Seedream model with original aspect ratio"""
    model = req.model or "doubao-seedream-4.5"
    print(f"--- Starting Direct Translation Flow for target: {req.target_lang} using model: {model} ---")

    if model == "doubao-seedream-5.0-lite":
        endpoint_id = ARK_ENDPOINT_ID_SEEDREAM_5_LITE
    else:
        endpoint_id = ARK_ENDPOINT_ID

    if not ARK_API_KEY or not endpoint_id:
        raise HTTPException(status_code=500, detail="Ark API Key or Endpoint ID not configured")

    try:
        width, height = get_image_dimensions_from_base64(req.image)
        size = calculate_size_for_aspect_ratio(width, height)
        print(f"Using size: {size} for translation")

        font_instruction = f"使用{req.target_font}风格字体" if req.target_font != "original" else "严格保持原图的字体风格"

        gen_prompt = (
            f"角色：你是一名顶级商业视觉设计师字体排版专家、专业的图像翻译专家、专业的图像编辑者、专业的语言翻译专家。"
            f"任务：将原图中的所有文字内容信达雅的翻译为{req.target_lang}，然后清除原有文字，再进行重绘。"
            f"严格遵守以下规则："
            f"1、完整识别与完整翻译：逐块扫描整张图片。所有可见文字 —— 包括标题、正文、角标、按钮、小字、半透明文字、水印及低对比度浅色文字 —— 必须完整翻译，不得遗漏。"
            f"2、无乱码：输出文字必须为规范、可识别的字符，拼写、含义与语法正确。严禁出现乱码、错别字、笔画残缺、重影、随机符号及无意义字符。"
            f"3、提升浅色文字可读性：针对原图中浅色或低对比度文字，在不改变整体视觉效果的前提下精细优化可读性。优先保留原有色相，仅调整亮度与边缘清晰度。必要时添加极细微描边、柔和阴影或局部对比度补偿，确保在 100% 缩放比例下清晰可辨。"
            f"4、字形与排版一致性：{font_instruction}。严格保留各文字元素相对于原图的位置、大小、字重、字间距、行间距、对齐方式、换行结构、倾斜角度及不透明度关系。"
            f"5、长文本处理：若翻译后文字长度发生变化，调整字间距与微缩比例以适配，避免溢出、遮挡或换行错误，保持原有版式层级。"
            f"6、背景零失真：所有非文字元素 —— 人物、产品、纹理、阴影、噪点、渐变及边缘细节 —— 必须保持原样，无涂抹痕迹或修复痕迹。"
            f"7、最终质量标准：所有翻译后文字边缘必须锐利，笔画完整，视觉效果如同原设计直接翻译而成。"
        )

        print(f"Sending direct translation request to {model}...")
        generation_result = await generate_image(GenerateRequest(
            prompt=gen_prompt,
            image_urls=[f"data:image/jpeg;base64,{req.image}"],
            size=size,
            model=model
        ))

        image_url = generation_result.get("data", [{}])[0].get("url", "")
        if image_url:
            print(f"Downloading generated image from: {image_url[:80]}...")
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            img_base64 = base64.b64encode(img_response.content).decode("utf-8")
            image_data_url = f"data:image/png;base64,{img_base64}"
            print("Image downloaded and converted to base64 successfully")
        else:
            image_data_url = req.image
            print("No image URL in response, using original")

        return {
            "translation_instructions": {
                "translations": [],
                "visual_context": "直接翻译模式",
                "gen_prompt": gen_prompt,
                "size": size,
                "original_dimensions": {"width": width, "height": height}
            },
            "result": {
                "data": [{"url": image_data_url}]
            }
        }

    except Exception as e:
        print(f"Translation Flow Error: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_image(req: GenerateRequest):
    """Uses Doubao-Seedream model (Ark) for image generation"""
    model = req.model or "doubao-seedream-4.5"
    if model == "doubao-seedream-5.0-lite":
        endpoint_id = ARK_ENDPOINT_ID_SEEDREAM_5_LITE
    else:
        endpoint_id = ARK_ENDPOINT_ID

    if not ARK_API_KEY or not endpoint_id:
        raise HTTPException(status_code=500, detail="Ark API Key or Endpoint ID not configured")

    url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": endpoint_id,
        "prompt": req.prompt,
        "size": req.size
    }

    if req.image_urls:
        payload["image"] = req.image_urls[0]

    try:
        print(f"Generating with model={model}, endpoint={endpoint_id}, size={payload['size']}, prompt_len={len(payload['prompt'])}")
        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            print(f"Ark API Error Response: {response.text}")
            response.raise_for_status()

        return response.json()
    except Exception as e:
        print(f"Generation Error: {str(e)}")
        if response.text:
            print(f"Error details: {response.text}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/edit")
async def edit_image(req: EditRequest):
    """Uses Doubao-Seedream model for image editing"""
    return await generate_image(GenerateRequest(
        prompt=req.prompt,
        image_urls=[f"data:image/jpeg;base64,{req.image}"],
        model=req.model
    ))

@app.get("/")
async def root():
    return {"status": "ok", "message": "ChromaAdapt AI Backend (Ark Version) Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
