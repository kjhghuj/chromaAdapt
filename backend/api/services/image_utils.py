import base64
import requests
from io import BytesIO
from PIL import Image


def clean_base64_image(base64_str: str) -> str:
    clean = (base64_str or "").strip().replace("\n", "").replace("\r", "")
    if clean.startswith("data:"):
        return clean.split(",", 1)[1]
    return clean


def get_image_dimensions_from_base64(base64_str: str) -> tuple[int, int]:
    try:
        image_data = base64.b64decode(clean_base64_image(base64_str))
        image = Image.open(BytesIO(image_data))
        return image.size
    except Exception:
        return (1024, 1024)


def calculate_size_for_aspect_ratio(width: int, height: int) -> str:
    min_pixels = 3686400
    max_pixels = 16777216
    aspect_ratio = width / height
    if aspect_ratio >= 1:
        target_width = 2048
        target_height = int(target_width / aspect_ratio)
        if target_width * target_height < min_pixels:
            target_height = int(min_pixels / target_width)
            target_width = int(target_height * aspect_ratio)
        target_width = max(1152, min(target_width, 4096))
        target_height = max(1152, min(target_height, 4096))
        total_pixels = target_width * target_height
        if total_pixels > max_pixels:
            scale = (max_pixels / total_pixels) ** 0.5
            target_width = int(target_width * scale)
            target_height = int(target_height * scale)
        return f"{target_width}x{target_height}"
    target_height = 2048
    target_width = int(target_height * aspect_ratio)
    if target_width * target_height < min_pixels:
        target_width = int(min_pixels / target_height)
        target_height = int(target_width / aspect_ratio)
    target_width = max(1152, min(target_width, 4096))
    target_height = max(1152, min(target_height, 4096))
    total_pixels = target_width * target_height
    if total_pixels > max_pixels:
        scale = (max_pixels / total_pixels) ** 0.5
        target_width = int(target_width * scale)
        target_height = int(target_height * scale)
    return f"{target_width}x{target_height}"


def download_image_as_data_url(image_url: str, fallback_data_url: str) -> str:
    if not image_url:
        return fallback_data_url
    img_response = requests.get(image_url, timeout=30)
    img_response.raise_for_status()
    img_base64 = base64.b64encode(img_response.content).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"
