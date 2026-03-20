from dataclasses import dataclass, field
from typing import Optional
from .services.ark_client import ApiError


def _required(data: dict, key: str):
    value = data.get(key)
    if value is None:
        raise ApiError(400, f"Missing required field: {key}")
    return value


@dataclass
class AnalyzeRequest:
    image: str
    prompt: str = "分析这张图片的色彩、构图和主要内容，并以JSON格式返回色盘（包含一个名为 'palette' 的数组，内含5个十六进制颜色）。"
    model: str = "doubao-seed-2-0-lite"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(image=_required(data, "image"), prompt=data.get("prompt", cls.prompt), model=data.get("model", cls.model))


@dataclass
class AnalyzeEditRequest:
    image: str
    user_instruction: str
    model: str = "doubao-seed-2-0-lite"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(image=_required(data, "image"), user_instruction=_required(data, "user_instruction"), model=data.get("model", cls.model))


@dataclass
class SecondaryPlanRequest:
    image: str
    model: str = "doubao-seed-2-0-lite"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(image=_required(data, "image"), model=data.get("model", cls.model))


@dataclass
class ColorMappingRequest:
    poster_image: str
    reference_image: str
    model: str = "doubao-seed-2-0-lite"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            poster_image=_required(data, "poster_image"),
            reference_image=_required(data, "reference_image"),
            model=data.get("model", cls.model),
        )


@dataclass
class ColorAdaptRequest:
    poster_image: str
    reference_image: str
    palette: list[str]
    style_config: Optional[dict] = None
    color_mapping_plan: Optional[str] = None
    model: str = "doubao-seedream-4.5"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            poster_image=_required(data, "poster_image"),
            reference_image=_required(data, "reference_image"),
            palette=data.get("palette", []),
            style_config=data.get("style_config"),
            color_mapping_plan=data.get("color_mapping_plan"),
            model=data.get("model", cls.model),
        )


@dataclass
class GenerateRequest:
    prompt: str
    image_urls: Optional[list[str]] = field(default=None)
    size: str = "2048x2048"
    model: str = "doubao-seedream-4.5"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            prompt=_required(data, "prompt"),
            image_urls=data.get("image_urls"),
            size=data.get("size", cls.size),
            model=data.get("model", cls.model),
        )


@dataclass
class EditRequest:
    image: str
    prompt: str
    model: str = "doubao-seedream-4.5"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(image=_required(data, "image"), prompt=_required(data, "prompt"), model=data.get("model", cls.model))


@dataclass
class TranslateRequest:
    image: str
    target_lang: str
    target_font: str = "original"
    model: str = "doubao-seedream-4.5"

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            image=_required(data, "image"),
            target_lang=_required(data, "target_lang"),
            target_font=data.get("target_font", cls.target_font),
            model=data.get("model", cls.model),
        )
