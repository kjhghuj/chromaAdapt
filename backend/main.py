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
ARK_ENDPOINT_ID = os.getenv("ARK_ENDPOINT_ID", "") # Image Generation Endpoint
ARK_ANALYSIS_ENDPOINT_ID = os.getenv("ARK_ANALYSIS_ENDPOINT_ID", "") # Image Analysis Endpoint (e.g., doubao-seed-2-0-lite)

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

class GenerateRequest(BaseModel):
    prompt: str
    image_urls: Optional[List[str]] = None
    size: str = "2048x2048"

class EditRequest(BaseModel):
    image: str # base64
    prompt: str

class TranslateRequest(BaseModel):
    image: str # base64
    target_lang: str
    target_font: Optional[str] = "original"

# --- Endpoints ---

@app.post("/analyze")
async def analyze_image(req: AnalyzeRequest):
    """Uses Doubao-Seed-2.0 (Ark) for image analysis"""
    if not ARK_API_KEY or not ARK_ANALYSIS_ENDPOINT_ID:
        raise HTTPException(status_code=500, detail="ARK_API_KEY or ARK_ANALYSIS_ENDPOINT_ID not configured")

    url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Clean image data: remove any potential whitespace/newlines from base64
    base64_data = req.image.strip().replace("\n", "").replace("\r", "")
    
    payload = {
        "model": ARK_ANALYSIS_ENDPOINT_ID,
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
        # Removed "response_format": {"type": "json_object"} as it often causes 400 errors on Ark
    }

    try:
        print(f"Sending request to Ark Analysis Endpoint: {ARK_ANALYSIS_ENDPOINT_ID}")
        # Increased timeout to 120s as visual analysis can be slow
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

@app.post("/translate")
async def translate_image(req: TranslateRequest):
    """Direct translation using Seedream-5.0-lite with original aspect ratio"""
    print(f"--- Starting Direct Translation Flow for target: {req.target_lang} ---")
    if not ARK_API_KEY or not ARK_ENDPOINT_ID:
        raise HTTPException(status_code=500, detail="Ark API Key or Endpoint ID not configured")

    try:
        width, height = get_image_dimensions_from_base64(req.image)
        size = calculate_size_for_aspect_ratio(width, height)
        print(f"Using size: {size} for translation")

        font_instruction = f"使用{req.target_font}风格字体" if req.target_font != "original" else "严格保持原图的字体风格"

        gen_prompt = (
            f"You are a top-tier commercial visual designer and multilingual typography expert. Task: Precisely translate all text in the original image into {req.target_lang} and perform seamless redrawing.\n"
            f"Strictly follow these rules:\n"
            f"1. Full recognition and full translation: Scan the entire image block by block. All visible text—including titles, body text, corner marks, buttons, small text, semi-transparent text, watermarks, and low-contrast light text—must be translated without omission.\n"
            f"2. No garbled characters: Output text must be standard, readable characters with correct spelling, meaning, and grammar. Garbled characters, typos, broken strokes, ghosting, random symbols, and meaningless characters are strictly prohibited.\n"
            f"3. Enhance readability of light text: For light or low-contrast text in the original image, finely enhance readability without altering the overall look. Prioritize keeping the original hue, only adjusting brightness and edge clarity. Add extremely subtle strokes, soft shadows, or local contrast compensation if necessary to ensure clear readability at 100% zoom.\n"
            f"4. Glyph and typography consistency: {font_instruction}. Strictly maintain the position, size, weight, kerning, line spacing, alignment, line break structure, slant angle, and opacity relationship of each text element with the original image.\n"
            f"5. Long text handling: If the translated text length changes, adjust the kerning and micro-scaling to fit without overflow, occlusion, or line break errors. Maintain the original layout hierarchy.\n"
            f"6. Background zero distortion: All non-text elements—people, products, textures, shadows, noise, gradients, and edge details—must remain unchanged, with no smudging or repair traces.\n"
            f"7. Final quality standard: All translated text edges must be sharp, strokes must be complete, and the visual appearance must look like the original design directly translated into {req.target_lang}.\n"
        )

        print("Sending direct translation request to Seedream-5.0-lite...")
        generation_result = await generate_image(GenerateRequest(
            prompt=gen_prompt,
            image_urls=[f"data:image/jpeg;base64,{req.image}"],
            size=size
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
    """Uses Doubao-Seedream-5.0-lite (Ark) for image generation"""
    if not ARK_API_KEY or not ARK_ENDPOINT_ID:
        raise HTTPException(status_code=500, detail="Ark API Key or Endpoint ID not configured")

    url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    headers = {
        "Authorization": f"Bearer {ARK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Doubao Ark API payload for Seedream 5.0
    payload = {
        "model": ARK_ENDPOINT_ID,
        "prompt": req.prompt,
        "size": req.size
    }
    
    # If reference images provided
    if req.image_urls:
        payload["image"] = req.image_urls[0]

    try:
        print(f"Generating with payload: model={payload['model']}, size={payload['size']}, prompt_len={len(payload['prompt'])}")
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
    """Uses Doubao-Seedream-5.0-lite for image editing"""
    return await generate_image(GenerateRequest(
        prompt=req.prompt,
        image_urls=[f"data:image/jpeg;base64,{req.image}"]
    ))

@app.get("/")
async def root():
    return {"status": "ok", "message": "ChromaAdapt AI Backend (Ark Version) Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
