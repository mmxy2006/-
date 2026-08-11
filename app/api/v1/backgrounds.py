"""背景生成（真实实现）：CogView-3-Flash 按 prompt 生图 + GLM-4-Flash 场景标签"""
from fastapi import APIRouter, File, HTTPException, UploadFile

from ...schemas.background import (
    BackgroundPromptRequest, CartoonizeResponse, CartoonStyle, SceneTags, SceneType, TimeOfDay,
)
from ...schemas.common import ImageRef
from ...services import cartoon as cartoon_service
from ...services import image_gen, store, vlm

router = APIRouter()


def _default_scene() -> SceneTags:
    return SceneTags(
        scene_type=SceneType.other, indoor=False, time_of_day=TimeOfDay.day,
        main_elements=["未知场景"], color_tone="暖色",
        suggested_theme="卡通大冒险", obstacle_hints=["石头", "树桩"],
    )


@router.post("/backgrounds/cartoonize", response_model=CartoonizeResponse,
             summary="文本 prompt → 卡通背景 + 场景标签（CogView 生图）")
def cartoonize(req: BackgroundPromptRequest) -> CartoonizeResponse:
    prompt = (req.prompt or "").strip()
    if not prompt:
        raise HTTPException(400, "prompt 不能为空")

    # 1. CogView 生背景（失败直接报错，无 AnimeGAN 兜底）
    png_bytes = image_gen.cogview_background(prompt)
    if not png_bytes:
        raise HTTPException(502, "背景生成失败：CogView 未返回有效结果")

    # 2. GLM-4 从 prompt 文本提取场景标签（供游戏挑障碍物；失败降级默认）
    try:
        scene = vlm.analyze_scene_from_text(prompt)
    except Exception:
        scene = _default_scene()

    # 3. 落盘
    bg_id = store.new_id()
    png_path = store.output_dir("backgrounds") / f"{bg_id}.png"
    png_path.write_bytes(png_bytes)
    store.save_json(png_path.with_suffix(".json"), scene)

    return CartoonizeResponse(
        background_id=bg_id,
        image=ImageRef(id=bg_id, url=store.url_of(png_path)),
        scene=scene,
    )


@router.post("/backgrounds/cartoonize-photo", response_model=CartoonizeResponse,
             summary="上传场景照片 → 保留构图的卡通背景 + 场景标签")
async def cartoonize_photo(file: UploadFile = File(...)) -> CartoonizeResponse:
    if file.content_type not in {"image/jpeg", "image/png", "image/webp", "image/bmp"}:
        raise HTTPException(400, f"不支持的图片类型: {file.content_type}")
    data = await file.read()
    if not data:
        raise HTTPException(400, "空文件")
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(400, "图片超过 20MB 限制")

    # cartoonize 内部依次尝试照片描述重绘、AnimeGAN 与 OpenCV，确保始终有结果。
    png_bytes = cartoon_service.cartoonize(data, CartoonStyle.paprika)
    try:
        scene = vlm.analyze_scene(data)
    except Exception:
        scene = _default_scene()

    bg_id = store.new_id()
    png_path = store.output_dir("backgrounds") / f"{bg_id}.png"
    png_path.write_bytes(png_bytes)
    store.save_json(png_path.with_suffix(".json"), scene)
    return CartoonizeResponse(
        background_id=bg_id,
        image=ImageRef(id=bg_id, url=store.url_of(png_path)),
        scene=scene,
    )
