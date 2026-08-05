"""人脸分析：MediaPipe Face Landmarker（Tasks API，纯 CPU，离线可用）

模型文件：app/assets/weights/face_landmarker.task（~3.6MB，随项目分发，本地部署无需下载）

输出：
- 人脸裁剪图（带边距，供 VLM 分析与展示）
- 可解释量化信号 MediapipeSignals：
  - smile_score：官方 blendshapes 的 mouthSmileLeft/Right 均值（模型直出，非启发式）
  - eye_open_ratio：1 - eyeBlinkLeft/Right 均值
  - face_width_height_ratio：关键点几何计算的脸宽/脸长

这些"本地可解释特征"与 VLM 语义特征做融合/交叉验证（refine_features），
是报告里"多模态特征工程"的亮点。
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from ..config import settings
from ..schemas.avatar import MediapipeSignals

log = logging.getLogger(__name__)

_MODEL_PATH = settings.assets_dir / "weights" / "face_landmarker.task"

# Face Mesh 关键点索引（mediapipe 标准拓扑）
_L_CHEEK, _R_CHEEK = 234, 454        # 左右脸颊（脸宽）
_FOREHEAD, _CHIN = 10, 152           # 额头、下巴（脸长）

_landmarker = None


def crop_face_opencv(image_bytes: bytes) -> bytes:
    """无需 MediaPipe 的安全人脸裁剪，供 Mac 环境和头像生成使用。"""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    rgb = np.array(img)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path) if Path(cascade_path).exists() else None
    faces = [] if cascade is None or cascade.empty() else cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5,
        minSize=(max(40, img.width // 12), max(40, img.height // 12)),
    )
    if len(faces):
        x, y, w, h = max(faces, key=lambda item: item[2] * item[3])
        # 头发、耳朵和少量颈部一起保留，避免只剩五官。
        x0, y0 = max(0, x - int(w * .35)), max(0, y - int(h * .55))
        x1, y1 = min(img.width, x + w + int(w * .35)), min(img.height, y + h + int(h * .30))
        img = img.crop((x0, y0, x1, y1))
    else:
        # OpenCV 精简包可能不带分类器：根据抠图主体顶部估算头像区域。
        try:
            from rembg import remove
            foreground = Image.open(io.BytesIO(remove(image_bytes))).convert("RGBA")
            bbox = foreground.getbbox()
        except Exception:
            bbox = None
        if bbox:
            x0, y0, x1, y1 = bbox
            person_w = x1 - x0
            side = max(96, int(person_w * .68))
            cx = (x0 + x1) // 2
            img = img.crop((max(0, cx - side // 2), max(0, y0),
                            min(img.width, cx + side // 2), min(img.height, y0 + side)))
        else:
            side = min(img.width, img.height)
            cx = img.width // 2
            top = max(0, int(img.height * .08))
            img = img.crop((max(0, cx - side // 2), top,
                            min(img.width, cx + side // 2), min(img.height, top + side)))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=92)
    return buf.getvalue()


def _get_landmarker():
    """加载（并缓存）Face Landmarker；模型缺失时抛 ZhipuError 外的明确异常"""
    global _landmarker
    if _landmarker is None:
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(
                f"人脸模型缺失: {_MODEL_PATH}（从 HuggingFace 搜 face_landmarker.task 下载放入）"
            )
        import mediapipe as mp  # 延迟导入：未装时让调用方捕获 ImportError
        base_options = mp.tasks.BaseOptions(model_asset_path=str(_MODEL_PATH))
        options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            num_faces=1,
            min_face_detection_confidence=0.5,
        )
        _landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(options)
    return _landmarker


def _blendscore(blendshapes, name: str) -> float:
    for cat in blendshapes:
        if cat.category_name == name:
            return float(cat.score)
    return 0.0


def analyze_face(image_bytes: bytes) -> tuple[bytes, MediapipeSignals]:
    """返回 (人脸裁剪图 jpeg bytes, 量化信号)。检测不到人脸时 face_detected=False，
    裁剪图退化为整图缩放。"""
    import mediapipe as mp

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    rgb = np.array(img)
    h, w = rgb.shape[:2]

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = _get_landmarker().detect(mp_image)

    if not result.face_landmarks:
        log.warning("未检测到人脸，返回整图")
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=90)
        return buf.getvalue(), MediapipeSignals(
            face_detected=False, smile_score=0.5, eye_open_ratio=1.0,
            face_width_height_ratio=0.8,
        )

    lm = result.face_landmarks[0]
    pts = np.array([[p.x * w, p.y * h] for p in lm])

    # 人脸裁剪（关键点 bbox + 25% 边距）
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    mx, my = (x1 - x0) * 0.25, (y1 - y0) * 0.25
    box = (max(0, int(x0 - mx)), max(0, int(y0 - my)),
           min(w, int(x1 + mx)), min(h, int(y1 + my)))
    buf = io.BytesIO()
    img.crop(box).save(buf, "JPEG", quality=90)

    # 量化信号：blendshapes 优先，几何比例兜底
    face_w = float(np.linalg.norm(pts[_L_CHEEK] - pts[_R_CHEEK]))
    face_h = float(np.linalg.norm(pts[_FOREHEAD] - pts[_CHIN]))

    if result.face_blendshapes:
        bs = result.face_blendshapes[0]
        smile = (_blendscore(bs, "mouthSmileLeft") + _blendscore(bs, "mouthSmileRight")) / 2
        blink = (_blendscore(bs, "eyeBlinkLeft") + _blendscore(bs, "eyeBlinkRight")) / 2
        smile_score, eye_open = smile, 1.0 - blink
    else:
        log.warning("模型未输出 blendshapes，信号用默认值")
        smile_score, eye_open = 0.5, 1.0

    return buf.getvalue(), MediapipeSignals(
        face_detected=True,
        smile_score=round(float(np.clip(smile_score, 0, 1)), 3),
        eye_open_ratio=round(float(np.clip(eye_open, 0, 1)), 3),
        face_width_height_ratio=round(face_w / max(face_h, 1e-6), 3),
    )


def refine_features(features, signals: MediapipeSignals):
    """本地信号对 VLM 特征的轻量交叉修正（VLM 为主，信号只纠明显矛盾）"""
    f = features.model_copy()
    if signals.face_detected:
        from ..schemas.avatar import Expression, FaceShape
        if signals.smile_score >= 0.6 and f.expression == Expression.neutral:
            f.expression = Expression.happy
        if signals.smile_score <= 0.1 and f.expression == Expression.happy:
            f.expression = Expression.neutral
        r = signals.face_width_height_ratio
        if r >= 0.95 and f.face_shape in (FaceShape.long, FaceShape.heart):
            f.face_shape = FaceShape.round
        elif r <= 0.68 and f.face_shape == FaceShape.round:
            f.face_shape = FaceShape.long
    return f
