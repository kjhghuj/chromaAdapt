import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .schemas import (
    AnalyzeRequest,
    AnalyzeEditRequest,
    SecondaryPlanRequest,
    ColorMappingRequest,
    ColorAdaptRequest,
    GenerateRequest,
    EditRequest,
    TranslateRequest,
)
from .services.ark_client import chat_with_images, generate_image, ApiError
from .services.image_utils import (
    clean_base64_image,
    get_image_dimensions_from_base64,
    calculate_size_for_aspect_ratio,
    download_image_as_data_url,
)
from .services.prompts import (
    SECONDARY_PLAN_PROMPT,
    COLOR_MAPPING_PROMPT,
    build_edit_analysis_prompt,
    build_color_adaptation_prompt,
    build_translation_prompt,
)


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        raise ApiError(400, "Invalid JSON body")


def _error_response(error: Exception):
    if isinstance(error, ApiError):
        return JsonResponse({"detail": error.detail}, status=error.status_code)
    return JsonResponse({"detail": str(error)}, status=500)


def _analyze_single_image(image: str, prompt: str, model: str):
    base64_data = clean_base64_image(image)
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}},
    ]
    return chat_with_images(model=model, content=content)


@csrf_exempt
def analyze_image(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        req = AnalyzeRequest.from_dict(_json_body(request))
        return JsonResponse(_analyze_single_image(req.image, req.prompt, req.model))
    except Exception as error:
        return _error_response(error)


@csrf_exempt
def analyze_edit_image(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        req = AnalyzeEditRequest.from_dict(_json_body(request))
        prompt = build_edit_analysis_prompt(req.user_instruction)
        return JsonResponse(_analyze_single_image(req.image, prompt, req.model))
    except Exception as error:
        return _error_response(error)


@csrf_exempt
def generate_secondary_plan(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        req = SecondaryPlanRequest.from_dict(_json_body(request))
        return JsonResponse(_analyze_single_image(req.image, SECONDARY_PLAN_PROMPT, req.model))
    except Exception as error:
        return _error_response(error)


@csrf_exempt
def create_color_mapping(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        req = ColorMappingRequest.from_dict(_json_body(request))
        poster_clean = clean_base64_image(req.poster_image)
        ref_clean = clean_base64_image(req.reference_image)
        content = [
            {"type": "text", "text": f"{COLOR_MAPPING_PROMPT}\n\n下面是原始海报图片："},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{poster_clean}"}},
            {"type": "text", "text": "\n\n下面是参考图片："},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{ref_clean}"}},
        ]
        return JsonResponse(chat_with_images(model=req.model, content=content))
    except Exception as error:
        return _error_response(error)


def _generate_image(req: GenerateRequest):
    return generate_image(model=req.model, prompt=req.prompt, size=req.size, image_urls=req.image_urls)


@csrf_exempt
def generate_image_view(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        req = GenerateRequest.from_dict(_json_body(request))
        return JsonResponse(_generate_image(req))
    except Exception as error:
        return _error_response(error)


@csrf_exempt
def edit_image(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        req = EditRequest.from_dict(_json_body(request))
        generated = generate_image(
            model=req.model,
            prompt=req.prompt,
            image_urls=[f"data:image/jpeg;base64,{clean_base64_image(req.image)}"],
        )
        return JsonResponse(generated)
    except Exception as error:
        return _error_response(error)


@csrf_exempt
def color_adaptation(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        req = ColorAdaptRequest.from_dict(_json_body(request))
        width, height = get_image_dimensions_from_base64(req.poster_image)
        size = calculate_size_for_aspect_ratio(width, height)
        prompt = build_color_adaptation_prompt(req.palette, req.style_config, req.color_mapping_plan)
        generated = generate_image(
            model=req.model,
            prompt=prompt,
            size=size,
            image_urls=[
                f"data:image/jpeg;base64,{clean_base64_image(req.poster_image)}",
                f"data:image/jpeg;base64,{clean_base64_image(req.reference_image)}",
            ],
        )
        image_url = generated.get("data", [{}])[0].get("url", "")
        image_data_url = download_image_as_data_url(image_url, req.poster_image)
        return JsonResponse({"data": [{"url": image_data_url}]})
    except Exception as error:
        return _error_response(error)


@csrf_exempt
def translate_image(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    try:
        req = TranslateRequest.from_dict(_json_body(request))
        width, height = get_image_dimensions_from_base64(req.image)
        size = calculate_size_for_aspect_ratio(width, height)
        prompt = build_translation_prompt(req.target_lang, req.target_font)
        generated = generate_image(
            model=req.model,
            prompt=prompt,
            size=size,
            image_urls=[f"data:image/jpeg;base64,{clean_base64_image(req.image)}"],
        )
        image_url = generated.get("data", [{}])[0].get("url", "")
        image_data_url = download_image_as_data_url(image_url, req.image)
        return JsonResponse(
            {
                "translation_instructions": {
                    "translations": [],
                    "visual_context": "直接翻译模式",
                    "gen_prompt": prompt,
                    "size": size,
                    "original_dimensions": {"width": width, "height": height},
                },
                "result": {"data": [{"url": image_data_url}]},
            }
        )
    except Exception as error:
        return _error_response(error)


def root(request):
    return JsonResponse({"status": "ok", "message": "ChromaAdapt AI Backend (Django) Running"})
