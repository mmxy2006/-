"""OpenAI 图片编辑：直接以用户照片为参考，只转换成 2D 卡通画风。"""
from __future__ import annotations

import base64
import logging

import httpx
from PIL import Image
import io

from ..config import settings

log = logging.getLogger(__name__)

CARTOONIZE_PROMPT = """
把输入照片中的脸和发型转换成忠实的二维日系动漫头像，只生成头部、头发、耳朵和少量颈部，不生成身体。
保持同一个人的身份、实际年龄、脸型、五官间距、发型、发色、肤色和可见耳饰。
使用干净流畅的二维线稿、自然的赛璐璐上色、柔和阴影、清新配色和适度动漫化五官；
人物仍应明显可辨认是原照片中的本人，不要幼儿化，不要夸张放大眼睛，不要改变脸型。
正面或接近正面的游戏头像，头部完整、居中，背景透明，不要肩膀、手臂、躯干和衣服主体。
无文字、无水印、无边框、无多余人物、无畸形肢体、无重复五官。
""".strip()


def cartoonize_portrait(image_bytes: bytes, filename: str = "portrait.png") -> bytes | None:
    """调用 Images Edits，以高参考保真度把原照片转换成透明背景卡通图。"""
    if not settings.openai_api_key:
        return None

    url = f"{settings.openai_base_url.rstrip('/')}/images/edits"
    try:
        image_format = Image.open(io.BytesIO(image_bytes)).format.lower()
    except Exception:
        image_format = "jpeg"
    mime = "image/jpeg" if image_format in ("jpg", "jpeg") else f"image/{image_format}"
    models = [settings.openai_image_model]
    if settings.openai_image_model != "gpt-image-1":
        models.append("gpt-image-1")

    for model in models:
        try:
            response = httpx.post(
                url,
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                files={"image": (filename, image_bytes, mime)},
                data={
                    "model": model,
                    "prompt": CARTOONIZE_PROMPT,
                    "size": "1024x1024",
                    "quality": "high",
                    "background": "transparent",
                    "output_format": "png",
                    "input_fidelity": "high",
                },
                timeout=180.0,
            )
            if response.status_code >= 400:
                log.warning("OpenAI 卡通化失败 model=%s status=%s", model, response.status_code)
                continue
            item = response.json()["data"][0]
            if item.get("b64_json"):
                return base64.b64decode(item["b64_json"])
            if item.get("url"):
                image_response = httpx.get(item["url"], timeout=90.0)
                image_response.raise_for_status()
                return image_response.content
        except Exception as exc:
            log.warning("OpenAI 卡通化调用异常 model=%s: %s", model, exc)
    return None
