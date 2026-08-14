import io
import os
import uuid
from pathlib import Path
from urllib.parse import urlencode

import gradio as gr
import httpx
from PIL import Image


# =========================================================
# 基础配置
# =========================================================

APP_NAME = "萌萌趣味格斗"
BACKEND_URL = os.getenv("NAILONG_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
GAME_URL = os.getenv("NAILONG_GAME_URL", "http://127.0.0.1:5173").rstrip("/")

BASE_DIR = Path(__file__).parent

ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "outputs"
AVATAR_DIR = OUTPUT_DIR / "avatars"
BACKGROUND_DIR = OUTPUT_DIR / "backgrounds"
VIDEO_DIR = OUTPUT_DIR / "videos"

for folder in [ASSETS_DIR, AVATAR_DIR, BACKGROUND_DIR, VIDEO_DIR]:
    if folder.exists() and not folder.is_dir():
        raise RuntimeError(
            f"{folder} 已存在，但它是文件而不是文件夹。"
            "请删除或重命名该文件后重新运行。"
        )
    folder.mkdir(parents=True, exist_ok=True)


# =========================================================
# 检查前端资源
# =========================================================
REQUIRED_ASSETS = [
    "logo.png",
    "hero_banner.png",
    "sidebar_character.png",
    "default_avatar.png",
]

for asset in REQUIRED_ASSETS:
    asset_path = ASSETS_DIR / asset
    if not asset_path.exists():
        print(f"⚠️ 缺少资源: {asset_path}")


# =========================================================
# 后端接口集成
# =========================================================

STYLE_PROMPTS = {
    "经典奶龙": "阳光草地与远山，经典治愈卡通风格，适合横版格斗游戏",
    "可爱奶龙": "糖果色梦幻乐园，可爱萌系卡通风格，适合横版格斗游戏",
    "校园奶龙": "明亮校园操场、教学楼和跑道，青春卡通风格",
    "旅行奶龙": "蓝天、山野和旅行营地，清新卡通冒险风格",
    "奇幻奶龙": "魔法森林、发光植物和远处城堡，奇幻卡通风格",
}


def _absolute_backend_url(path):
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path
    return f"{BACKEND_URL}/{path.lstrip('/')}"


def _save_remote_image(client, url, folder, prefix):
    response = client.get(url)
    response.raise_for_status()
    suffix = ".png" if "png" in response.headers.get("content-type", "") else ".jpg"
    path = folder / f"{prefix}_{uuid.uuid4().hex[:10]}{suffix}"
    path.write_bytes(response.content)
    return str(path.resolve())


def generate_nailong(image, background_image):
    if image is None:
        raise gr.Error("请先上传一张清晰的人物照片。")
    if background_image is None:
        raise gr.Error("请上传一张需要卡通化的场景照片。")
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=94)
    photo = buffer.getvalue()
    background_buffer = io.BytesIO()
    background_image.convert("RGB").save(background_buffer, format="JPEG", quality=94)
    background_photo = background_buffer.getvalue()

    try:
        with httpx.Client(timeout=300.0) as client:
            health = client.get(f"{BACKEND_URL}/api/health")
            health.raise_for_status()
            analyzed_response = client.post(
                f"{BACKEND_URL}/api/v1/avatars/analyze",
                files={"file": ("portrait.jpg", photo, "image/jpeg")},
            )
            analyzed_response.raise_for_status()
            analyzed = analyzed_response.json()

            composed_response = client.post(
                f"{BACKEND_URL}/api/v1/avatars/compose",
                json={
                    "avatar_id": analyzed["avatar_id"],
                    "features": analyzed["features"],
                },
            )
            composed_response.raise_for_status()
            composed = composed_response.json()

            background_response = client.post(
                f"{BACKEND_URL}/api/v1/backgrounds/cartoonize-photo",
                files={"file": ("scene.jpg", background_photo, "image/jpeg")},
            )
            background_response.raise_for_status()
            background = background_response.json()

            avatar_url = _absolute_backend_url(composed["image"]["url"])
            background_url = _absolute_backend_url(background["image"]["url"])
            avatar_path = _save_remote_image(client, avatar_url, AVATAR_DIR, "avatar")
            background_path = _save_remote_image(client, background_url, BACKGROUND_DIR, "background")
    except httpx.HTTPStatusError as exc:
        detail = ""
        try:
            detail = exc.response.json().get("detail", "")
        except Exception:
            pass
        raise gr.Error(f"后端生成失败：{detail or exc.response.status_code}") from exc
    except Exception as exc:
        raise gr.Error(f"无法连接生成服务：{exc}") from exc

    status = f"""
<div class="success-box">
    <div class="success-title">✨ 形象生成完成</div>
    <div>人物形象和上传场景均已完成卡通化。</div>
    <div class="success-note">
        已通过后端完成头像分析、透明动漫头像生成和卡通场景生成，
        可以进入格斗游戏使用当前角色。
    </div>
</div>
"""

    return (
        avatar_path,
        background_path,
        {"local_path": avatar_path, "url": avatar_url, "avatar_id": analyzed["avatar_id"]},
        {"local_path": background_path, "url": background_url, "background_id": background["background_id"]},
        status,
    )


def refresh_ranking(ranking_type):
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/v1/games/leaderboard",
            params={"difficulty": "normal", "limit": 20},
            timeout=20.0,
        )
        response.raise_for_status()
        entries = response.json().get("entries", [])
        if not entries:
            return [["-", "暂无成绩", 0, "普通", "-"]]
        return [
            [item["rank"], item["nickname"], item["score"], item["difficulty"], item["created_at"][:19]]
            for item in entries
        ]
    except Exception:
        return [["-", "排行榜服务暂不可用", 0, "-", "-"]]


def start_game(avatar, background):
    if not avatar or not background:
        raise gr.Error("请先在形象生成页面生成角色和背景。")
    params = urlencode({"player": avatar["url"], "background": background["url"]})
    src = f"{GAME_URL}/?{params}"
    return f"""
<div class="game-frame-wrap">
  <iframe src="{src}" title="AI 卡通格斗游戏" allow="autoplay; fullscreen" loading="eager"></iframe>
</div>
"""


def switch_page(page_index):
    return tuple(
        gr.update(visible=(index == page_index))
        for index in range(4)
    )


def navigation_js(page_index):
    """页面导航在浏览器端立即完成，避免本地代理影响 Gradio 事件队列。"""
    return f"""
() => {{
    const pages = ['home-page', 'avatar-page', 'game-page', 'ranking-page'];
    const navs = ['home-nav', 'avatar-nav', 'game-nav', 'ranking-nav'];
    pages.forEach((id, index) => {{
        const page = document.getElementById(id);
        if (page) page.style.display = index === {page_index} ? 'flex' : 'none';
    }});
    navs.forEach((id, index) => {{
        const nav = document.getElementById(id);
        if (nav) nav.classList.toggle('nav-current', index === {page_index});
    }});
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
    return [];
}}
"""


# =========================================================
# CSS
# =========================================================

CUSTOM_CSS = """
:root {
    --panel-height: clamp(790px, calc(100vh - 28px), 900px);
    --orange: #e58a2d;
    --deep-orange: #ca6d1c;
    --yellow: #ffd45e;
    --cream: #fff9e8;
    --brown: #74451f;
    --soft-brown: #9d7653;
    --card: rgba(255, 255, 255, 0.96);
}

body {
    margin: 0;
    background:
        linear-gradient(
            rgba(255, 251, 233, 0.97),
            rgba(255, 243, 204, 0.97)
        );
}

.gradio-container {
    width: 100% !important;
    max-width: 1600px !important;
    margin: 0 auto !important;
    padding: 14px !important;
    background: transparent !important;
}

.main-layout {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
    max-width: 100% !important;
    align-items: stretch !important;
    gap: 14px !important;
    box-sizing: border-box !important;
}

.sidebar {
    height: var(--panel-height) !important;
    min-height: var(--panel-height) !important;
    max-height: var(--panel-height) !important;
    width: 176px !important;
    min-width: 176px !important;
    max-width: 176px !important;
    flex: 0 0 176px !important;
    padding: 16px 10px !important;
    border: 1px solid rgba(223, 157, 51, 0.34) !important;
    border-radius: 25px !important;
    background:
        linear-gradient(
            180deg,
            rgba(255, 249, 218, 0.98),
            rgba(255, 238, 182, 0.96)
        ) !important;
    box-shadow:
        0 14px 34px rgba(113, 74, 25, 0.13) !important;
    box-sizing: border-box !important;
}

.logo-box {
    margin-bottom: 22px;
    text-align: center;
}

.logo-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 76px;
    height: 76px;
    margin: 0 auto 8px;
    border-radius: 22px;
    overflow: hidden;
    background: linear-gradient(145deg, #ffd85b, #ff9831);
    box-shadow: 0 9px 20px rgba(224, 124, 29, 0.24);
}


.logo-icon img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}
}

.logo-title {
    color: var(--brown);
    font-size: 19px;
    font-weight: 900;
}

.logo-subtitle {
    margin-top: 4px;
    color: #a77d54;
    font-size: 11px;
}

.nav-button {
    width: 100% !important;
    min-width: 0 !important;
    min-height: 43px !important;
    margin-bottom: 7px !important;
    padding: 7px 6px !important;
    border: 1px solid rgba(229, 184, 108, 0.35) !important;
    border-radius: 13px !important;
    color: #744b26 !important;
    background: rgba(255, 255, 255, 0.87) !important;
    font-size: 13px !important;
    font-weight: 800 !important;
}

.nav-button:hover,
.home-nav {
    color: white !important;
    background: linear-gradient(90deg, #efa03a, #d97a25) !important;
}

.content-column {
    width: auto !important;
    min-width: 0 !important;
    max-width: none !important;

    height: var(--panel-height) !important;
    min-height: var(--panel-height) !important;
    max-height: var(--panel-height) !important;

    flex: 1 1 0 !important;
    box-sizing: border-box !important;
    overflow: hidden !important;
}

/* 八个页面统一左右宽度 */
.page-shell {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;

    height: var(--panel-height) !important;
    min-height: var(--panel-height) !important;
    max-height: var(--panel-height) !important;

    margin: 0 !important;
    padding: 4px 6px 8px 4px !important;

    box-sizing: border-box !important;
    overflow-x: hidden !important;
    overflow-y: auto !important;

    scrollbar-width: thin;
    scrollbar-color: rgba(220, 151, 55, 0.55) transparent;
}

.page-shell::-webkit-scrollbar {
    width: 6px;
}

.page-shell::-webkit-scrollbar-track {
    background: transparent;
}

.page-shell::-webkit-scrollbar-thumb {
    border-radius: 999px;
    background: rgba(220, 151, 55, 0.55);
}

.page-shell > div,
.page-shell .gr-row,
.page-shell .form,
.page-shell .block,
.content-card,
.hero-banner,
.home-intro,
.game-main-card,
.animation-result-card,
.animation-settings,
.profile-wide-card,
.my-works-wide-card {
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
}

.page-shell img,
.page-shell video,
.page-shell table {
    max-width: 100% !important;
}

.content-card {
    padding: 20px !important;
    border: 1px solid rgba(226, 167, 72, 0.34) !important;
    border-radius: 22px !important;
    background: var(--card) !important;
    box-shadow: 0 12px 27px rgba(108, 74, 29, 0.10) !important;
}

.hero-banner {
    min-height: 330px;
    overflow: hidden;
    padding: 35px 42px;
    border-radius: 28px;
    background:
        linear-gradient(
            rgba(255, 240, 195, 0.08),
            rgba(255, 244, 207, 0.12)
        ),
        url('/gradio_api/file=assets/hero_banner.png');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    box-shadow: 0 16px 38px rgba(110, 75, 31, 0.16);
}

.hero-text {
    max-width: 650px;
    margin: 38px auto 0;
    text-align: center;
}

.hero-title {
    color: #e47b27;
    font-size: 48px;
    line-height: 1.2;
    font-weight: 950;
    text-shadow:
        3px 3px 0 white,
        -2px -2px 0 white,
        0 5px 14px rgba(117, 65, 21, 0.18);
}

.hero-tag {
    display: inline-block;
    margin-top: 12px;
    padding: 8px 18px;
    border-radius: 999px;
    color: white;
    background: linear-gradient(90deg, #f3a13c, #dc7625);
    font-weight: 850;
}

.hero-description {
    margin-top: 15px;
    color: #704a26;
    font-size: 15px;
    line-height: 1.8;
    font-weight: 650;
}

.home-intro {
    margin-top: 18px;
}

.home-card {
    min-height: 145px;
    padding: 16px;
    border-radius: 20px;
    color: #71461e;
    background: linear-gradient(145deg, #fffdf7, #fff4ce);
    border: 1px solid #f1d49d;
    text-align: center;
}

.home-card-icon {
    font-size: 39px;
}

.home-card-title {
    margin-top: 8px;
    font-size: 18px;
    font-weight: 900;
}

.home-card-text {
    margin-top: 7px;
    color: #9a7550;
    font-size: 13px;
    line-height: 1.6;
}

.page-title {
    margin-bottom: 5px;
    color: #72451e;
    font-size: 23px;
    font-weight: 950;
}

.page-description {
    margin-bottom: 17px;
    color: #9c7653;
    font-size: 14px;
    line-height: 1.7;
}

.section-title {
    margin-bottom: 9px;
    color: #75451f;
    font-size: 19px;
    font-weight: 900;
}

.section-tip {
    margin-bottom: 14px;
    padding: 11px 13px;
    border-left: 5px solid #e99a37;
    border-radius: 12px;
    color: #8d6944;
    background: #fff5d3;
    font-size: 13px;
    line-height: 1.6;
}

.image-box {
    overflow: hidden !important;
    border: 2px dashed #e8b65f !important;
    border-radius: 17px !important;
    background: linear-gradient(145deg, #fffefa, #fff7dd) !important;
}

.main-action {
    min-height: 50px !important;
    border: none !important;
    border-radius: 14px !important;
    color: white !important;
    background: linear-gradient(90deg, #e99a36, #d27322) !important;
    font-size: 16px !important;
    font-weight: 900 !important;
}

.secondary-action {
    min-height: 44px !important;
    border: 1px solid #eed3a5 !important;
    border-radius: 13px !important;
    color: #795028 !important;
    background: #fffaf0 !important;
    font-weight: 800 !important;
}

.success-box {
    padding: 12px 14px;
    border: 1px solid #b8e5ae;
    border-radius: 13px;
    color: #466d40;
    background: #effbea;
}

.success-title {
    margin-bottom: 4px;
    font-weight: 900;
}

.success-note {
    margin-top: 6px;
    color: #8f795e;
    font-size: 12px;
}

.dress-row,
.animation-row {
    width: 100% !important;
    gap: 16px !important;
}

.dress-column {
    min-width: 0 !important;
    flex: 1 1 0 !important;
    min-height: 640px;
}

.compact-rules {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin-bottom: 14px;
    padding: 13px;
    border: 1px solid rgba(226, 167, 72, 0.34);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.94);
}

.compact-rule {
    padding: 10px 8px;
    border-radius: 12px;
    color: #78502d;
    background: #fff7dc;
    text-align: center;
    font-size: 12px;
    line-height: 1.45;
}

.compact-rule b {
    display: block;
    margin-bottom: 3px;
    color: #70451e;
    font-size: 13px;
}

.compact-rule span {
    color: #9a7855;
    font-size: 11px;
}

.game-display {
    position: relative;
    overflow: hidden;
    height: 555px;
    border: 2px solid #e9b45d;
    border-radius: 22px;
    background:
        linear-gradient(
            rgba(255, 255, 255, 0.05),
            rgba(31, 97, 69, 0.08)
        ),
        url('/gradio_api/file=assets/game_background.png');
    background-size: cover;
    background-position: center;
}

.game-hud {
    position: absolute;
    top: 17px;
    left: 17px;
    right: 17px;
    display: flex;
    justify-content: space-between;
    padding: 11px 16px;
    border-radius: 14px;
    color: #71471f;
    background: rgba(255, 255, 255, 0.90);
    font-size: 15px;
    font-weight: 900;
}

.game-start {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    padding: 17px 30px;
    border-radius: 18px;
    color: white;
    background: linear-gradient(90deg, #ee9e38, #d77424);
    font-size: 21px;
    font-weight: 900;
}

.game-frame-wrap {
    width: 100%;
    overflow: hidden;
    border: 3px solid #e7a13f;
    border-radius: 20px;
    background: #14182f;
    box-shadow: 0 14px 30px rgba(91, 56, 20, 0.18);
}

.game-frame-wrap iframe {
    display: block;
    width: 100%;
    height: 640px;
    border: 0;
    background: #14182f;
}

.animation-settings {
    min-width: 0 !important;
    flex: 1 1 25% !important;
    min-height: 640px;
}

.animation-result-card {
    min-width: 0 !important;
    flex: 1 1 75% !important;
    min-height: 640px;
}

.large-video {
    min-height: 535px !important;
}

.large-video video {
    width: 100% !important;
    min-height: 515px !important;
    max-height: 515px !important;
    object-fit: contain !important;
    border-radius: 16px !important;
    background: #fffdf8 !important;
}

.profile-wide-card,
.my-works-wide-card {
    width: 100% !important;
}

.profile-wide {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    min-height: 125px;
    padding: 17px 24px;
    border-radius: 20px;
    background: linear-gradient(110deg, #fff7d8, #eaf7ff);
}

.profile-left {
    display: flex;
    align-items: center;
    gap: 22px;
}

.profile-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 82px;
    height: 82px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.72);
    font-size: 48px;
}

.profile-name {
    color: #70451e;
    font-size: 23px;
    font-weight: 900;
}

.profile-subtitle {
    margin-top: 8px;
    color: #967454;
    font-size: 14px;
}

.profile-stat-group {
    display: grid;
    grid-template-columns: repeat(4, 120px);
    gap: 12px;
}

.profile-stat {
    padding: 11px 8px;
    border-radius: 15px;
    background: rgba(255, 255, 255, 0.72);
    text-align: center;
}

.profile-stat b {
    display: block;
    color: #df7c25;
    font-size: 21px;
}

.profile-stat span {
    display: block;
    margin-top: 5px;
    color: #8b6c4d;
    font-size: 12px;
}

.profile-gallery {
    width: 100% !important;
    min-height: 300px !important;
}


/* =====================================================
   八个页面统一上下高度，并让内部内容适配同一画布
   ===================================================== */

.page-shell .page-title {
    margin-top: 2px !important;
    margin-bottom: 3px !important;
}

.page-shell .page-description {
    margin-bottom: 11px !important;
}

/* 形象生成页面 */
.page-shell .image-box {
    max-height: 520px;
}

/* 换装页面 */
.dress-row {
    min-height: 650px;
    align-items: stretch !important;
}

.dress-column {
    height: 650px !important;
    min-height: 650px !important;
    max-height: 650px !important;
    overflow: hidden !important;
}

.dress-column .image-box {
    max-height: 455px !important;
}

/* 游戏页面 */
.compact-rules {
    margin-bottom: 10px !important;
    padding: 9px !important;
}

.compact-rule {
    padding: 7px 6px !important;
}

.game-main-card {
    padding: 13px !important;
}

/* 动画页面 */
.animation-row {
    min-height: 650px;
    align-items: stretch !important;
}

.animation-settings,
.animation-result-card {
    height: 650px !important;
    min-height: 650px !important;
    max-height: 650px !important;
    overflow: hidden !important;
}

/* 社区和排行榜 */
.community-page-card,
.ranking-page-card {
    min-height: 680px;
}

/* 个人中心 */
.profile-wide-card {
    min-height: 205px !important;
    margin-bottom: 12px !important;
}

.my-works-wide-card {
    min-height: 455px !important;
}

.profile-gallery {
    min-height: 285px !important;
}


/* 修复Gradio图片显示 */
.gr-image,
.gr-image-container,
.image-container {
    overflow: visible !important;
}

.gr-image img {
    object-fit: contain !important;
}

.image-box {
    overflow: visible !important;
}

/* Fix image component */
.gr-image,
.gr-image-container,
.image-container {
    overflow: visible !important;
}

.gr-image img {
    object-fit: contain !important;
}

footer {
    display: none !important;
}

@media (max-width: 1100px) {
    .sidebar {
        width: 158px !important;
        min-width: 158px !important;
        max-width: 158px !important;
        flex-basis: 158px !important;
    }

    .nav-button {
        font-size: 12px !important;
        padding-left: 4px !important;
        padding-right: 4px !important;
    }

    .compact-rules {
        grid-template-columns: repeat(2, 1fr);
    }

    .profile-wide {
        flex-direction: column;
        align-items: flex-start;
        gap: 20px;
    }

    .profile-stat-group {
        width: 100%;
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 760px) {
    .main-layout {
        flex-direction: column !important;
    }

    .sidebar,
    .content-column,
    .page-shell {
        height: auto !important;
        min-height: auto !important;
        max-height: none !important;
    }

    .sidebar {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        min-height: auto !important;
        flex-basis: auto !important;
    }

    .content-column {
        width: 100% !important;
        max-width: 100% !important;
    }
}
"""


THEME = gr.themes.Soft(
    primary_hue="orange",
    secondary_hue="yellow",
    neutral_hue="stone",
    font=[
        gr.themes.GoogleFont("Noto Sans SC"),
        "Microsoft YaHei",
        "Arial",
        "sans-serif",
    ],
)


# =========================================================
# 页面构建
# =========================================================

with gr.Blocks(title=APP_NAME, fill_width=True) as demo:
    avatar_state = gr.State(None)
    background_state = gr.State(None)

    with gr.Row(elem_classes="main-layout"):
        with gr.Column(elem_classes="sidebar"):
            gr.HTML(f"""
<div class="logo-box">
    <div class="logo-icon">
        <img src="/gradio_api/file={ASSETS_DIR / 'default_avatar.png'}">
    </div>
    <div class="logo-title">萌萌趣味格斗</div>
    <div class="logo-subtitle">Cute Fun Fighter</div>
</div>
""")

            home_nav = gr.Button(
                "🏠　首页",
                elem_classes=["nav-button", "home-nav"],
                elem_id="home-nav",
            )
            avatar_nav = gr.Button(
                "👤　形象生成",
                elem_classes="nav-button",
                elem_id="avatar-nav",
            )
            game_nav = gr.Button(
                "🥊　格斗游戏",
                elem_classes="nav-button",
                elem_id="game-nav",
            )
            ranking_nav = gr.Button(
                "🏆　排行榜",
                elem_classes="nav-button",
                elem_id="ranking-nav",
            )

        with gr.Column(elem_classes="content-column"):
            # 首页
            with gr.Column(
                visible=True,
                elem_classes="page-shell",
                elem_id="home-page",
            ) as home_page:
                gr.HTML("""
<div class="hero-banner">
    <div class="hero-text">
        <div class="hero-title">萌萌趣味格斗</div>
        <div class="hero-tag">AI 个性化奶龙创作平台</div>
        <div class="hero-description">
            上传照片，生成你的专属奶龙形象，
            开启换装、格斗游戏和动画故事创作。
        </div>
    </div>
</div>
""")

                with gr.Row(elem_classes="home-intro"):
                    for icon, title, text in [
                        ("🎨", "个性形象", "根据人物照片生成奶龙形象"),
                        ("🥊", "格斗游戏", "使用专属角色进入卡通对战"),
                        ("🏆", "排行榜", "查看游戏成绩排行"),
                    ]:
                        gr.HTML(f"""
<div class="home-card">
    <div class="home-card-icon">{icon}</div>
    <div class="home-card-title">{title}</div>
    <div class="home-card-text">{text}</div>
</div>
""")

                with gr.Row():
                    enter_avatar_button = gr.Button(
                        "✨ 开始创建我的奶龙",
                        variant="primary",
                        elem_classes="main-action",
                    )
                    enter_game_button = gr.Button(
                        "🥊 进入格斗世界",
                        elem_classes="secondary-action",
                    )
                    enter_ranking_button = gr.Button(
                        "🏆 查看排行榜",
                        elem_classes="secondary-action",
                    )

            # 形象生成
            with gr.Column(
                visible=False,
                elem_classes="page-shell",
                elem_id="avatar-page",
            ) as avatar_page:
                gr.HTML("""
<div class="page-title">👤 卡通形象生成</div>
<div class="page-description">
    上传清晰人物照片和场景照片，分别生成卡通角色与卡通场景。
</div>
""")

                with gr.Row():
                    with gr.Column(
                        scale=1,
                        elem_classes="content-card",
                    ):
                        gr.HTML("""
<div class="section-title">上传人物照片</div>
<div class="section-tip">
    推荐使用正面、清晰、无遮挡的照片。
</div>
""")
                        input_image = gr.Image(
                            label="上传人物照片",
                            type="pil",
                            sources=["upload"],
                            height=350,
                            show_label=True,
                        )
                        background_image = gr.Image(
                            label="上传场景照片并卡通化",
                            type="pil",
                            sources=["upload"],
                            height=250,
                            show_label=True,
                        )
                        generate_button = gr.Button(
                            "✨ 生成奶龙形象",
                            variant="primary",
                            elem_classes="main-action",
                        )
                        generation_status = gr.HTML("""
<div class="section-tip">
    上传照片后点击生成。
</div>
""")

                    with gr.Column(
                        scale=1,
                        elem_classes="content-card",
                    ):
                        gr.HTML("""
<div class="section-title">生成结果</div>
""")
                        avatar_output = gr.Image(
                            label="奶龙角色",
                            type="filepath",
                            height=350,
                            show_label=True,
                        )
                        background_output = gr.Image(
                            label="卡通背景",
                            type="filepath",
                            height=180,
                            show_label=True,
                        )
                        with gr.Row():
                            download_avatar_button = gr.DownloadButton(
                                "⬇ 下载形象",
                                elem_classes="secondary-action",
                            )

                generate_event = generate_button.click(
                    fn=generate_nailong,
                    inputs=[input_image, background_image],
                    outputs=[
                        avatar_output,
                        background_output,
                        avatar_state,
                        background_state,
                        generation_status,
                    ],
                )
                generate_event.then(
                    fn=lambda data: data.get("local_path") if data else None,
                    inputs=avatar_state,
                    outputs=download_avatar_button,
                )

            # 格斗游戏
            with gr.Column(
                visible=False,
                elem_classes="page-shell",
                elem_id="game-page",
            ) as game_page:
                gr.HTML("""
<div class="page-title">🥊 格斗游戏</div>
<div class="page-description">
    游戏角色、背景、障碍物和关卡逻辑由后端生成。
</div>
""")

                gr.HTML("""
<div class="compact-rules">
    <div class="compact-rule"><b>← → 移动</b><span>控制角色左右前进</span></div>
    <div class="compact-rule"><b>空格跳跃</b><span>跳过障碍物和陷阱</span></div>
    <div class="compact-rule"><b>🪙 收集金币</b><span>金币可以增加分数</span></div>
    <div class="compact-rule"><b>❤️ 注意生命</b><span>碰撞会损失爱心</span></div>
    <div class="compact-rule"><b>🏁 到达终点</b><span>限时内抵达即可通关</span></div>
</div>
""")

                with gr.Column(elem_classes="content-card"):
                    game_frame = gr.HTML("""
<div class="game-display">
    <div class="game-hud">
        <span>❤️ 3</span>
        <span>🪙 0 / 20</span>
        <span>⏱ 90 秒</span>
        <span>🏆 0 分</span>
    </div>
    <div class="game-start">🎮 游戏将在此处运行</div>
</div>
""")
                    start_game_button = gr.Button(
                        "▶ 开始游戏",
                        variant="primary",
                        elem_classes="main-action",
                    )
                    start_game_button.click(
                        fn=start_game,
                        inputs=[avatar_state, background_state],
                        outputs=game_frame,
                    )

            # 排行榜
            with gr.Column(
                visible=False,
                elem_classes="page-shell",
                elem_id="ranking-page",
            ) as ranking_page:
                gr.HTML("""
<div class="page-title">🏆 萌萌趣味格斗排行榜</div>
<div class="page-description">
    排行榜成绩由后端记录并实时更新。
</div>
""")

                with gr.Column(elem_classes="content-card"):
                    with gr.Row():
                        ranking_type = gr.Dropdown(
                            choices=[
                                "总排行榜",
                                "本周排行榜",
                                "好友排行榜",
                            ],
                            value="总排行榜",
                            label="排行榜类型",
                        )
                        refresh_ranking_button = gr.Button(
                            "刷新排行榜",
                            elem_classes="secondary-action",
                        )

                    ranking_table = gr.Dataframe(
                        headers=[
                            "排名",
                            "玩家",
                            "分数",
                            "关卡",
                            "用时",
                        ],
                        datatype=[
                            "number",
                            "str",
                            "number",
                            "str",
                            "str",
                        ],
                        value=refresh_ranking("总排行榜"),
                        interactive=False,
                    )

                refresh_ranking_button.click(
                    fn=refresh_ranking,
                    inputs=ranking_type,
                    outputs=ranking_table,
                )

    page_outputs = [
        home_page,
        avatar_page,
        game_page,
        ranking_page,
    ]

    for button, index in [
        (home_nav, 0),
        (avatar_nav, 1),
        (game_nav, 2),
        (ranking_nav, 3),
        (enter_avatar_button, 1),
        (enter_game_button, 2),
        (enter_ranking_button, 3),
    ]:
        button.click(fn=None, js=navigation_js(index), queue=False)


if __name__ == "__main__":
    demo.queue().launch(
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True,
        allowed_paths=[
            str(ASSETS_DIR.resolve()),
            str(OUTPUT_DIR.resolve()),
        ],
        css=CUSTOM_CSS,
        theme=THEME,
    )
