import uuid
from pathlib import Path

import gradio as gr
from PIL import Image, ImageEnhance


# =========================================================
# 基础配置
# =========================================================

APP_NAME = "奶龙奇幻冒险之旅"

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
# 临时功能函数：后续替换为后端真实接口
# =========================================================

def generate_nailong_mock(image, style):
    if image is None:
        raise gr.Error("请先上传一张清晰的人物照片。")

    task_id = str(uuid.uuid4())[:8]
    avatar_path = AVATAR_DIR / f"avatar_{task_id}.png"
    background_path = BACKGROUND_DIR / f"background_{task_id}.png"

    avatar = image.convert("RGB")
    avatar.thumbnail((720, 720))

    canvas = Image.new("RGB", (720, 720), color=(255, 242, 193))
    x = (720 - avatar.width) // 2
    y = (720 - avatar.height) // 2
    canvas.paste(avatar, (x, y))
    canvas = ImageEnhance.Color(canvas).enhance(1.35)
    canvas.save(str(avatar_path), format="PNG")

    background = image.convert("RGB")
    background = background.resize((1100, 650))
    background = ImageEnhance.Color(background).enhance(1.45)
    background.save(str(background_path), format="PNG")

    status = f"""
<div class="success-box">
    <div class="success-title">✨ 形象生成完成</div>
    <div>当前风格：{style}</div>
    <div class="success-note">
        当前为前端模拟结果。接入后端后，
        这里将显示真正生成的奶龙卡通形象。
    </div>
</div>
"""

    return (
        str(avatar_path.resolve()),
        str(background_path.resolve()),
        str(avatar_path.resolve()),
        str(background_path.resolve()),
        status,
    )


def refresh_ranking_mock(ranking_type):
    return [
        [1, "奶龙勇士", 9800, "森林冒险", "58秒"],
        [2, "小星星", 9250, "校园历险", "63秒"],
        [3, "云朵玩家", 8760, "奇幻城堡", "71秒"],
        [4, "橙子奶龙", 8210, "云端世界", "75秒"],
    ]


def switch_page(page_index):
    return tuple(
        gr.update(visible=(index == page_index))
        for index in range(4)
    )


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
    <div class="logo-title">奶龙冒险</div>
    <div class="logo-subtitle">Nailong Adventure</div>
</div>
""")

            home_nav = gr.Button(
                "🏠　首页",
                elem_classes=["nav-button", "home-nav"],
            )
            avatar_nav = gr.Button(
                "👤　形象生成",
                elem_classes="nav-button",
            )
            game_nav = gr.Button(
                "🎮　冒险游戏",
                elem_classes="nav-button",
            )
            ranking_nav = gr.Button(
                "🏆　排行榜",
                elem_classes="nav-button",
            )

        with gr.Column(elem_classes="content-column"):
            # 首页
            with gr.Column(
                visible=True,
                elem_classes="page-shell",
            ) as home_page:
                gr.HTML("""
<div class="hero-banner">
    <div class="hero-text">
        <div class="hero-title">奶龙奇幻冒险之旅</div>
        <div class="hero-tag">AI 个性化奶龙创作平台</div>
        <div class="hero-description">
            上传照片，生成你的专属奶龙形象，
            开启换装、冒险游戏和动画故事创作。
        </div>
    </div>
</div>
""")

                with gr.Row(elem_classes="home-intro"):
                    for icon, title, text in [
                        ("🎨", "个性形象", "根据人物照片生成奶龙形象"),
                        ("🎮", "冒险游戏", "使用专属角色进入卡通关卡"),
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
                        "🎮 进入冒险世界",
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
            ) as avatar_page:
                gr.HTML("""
<div class="page-title">👤 奶龙形象生成</div>
<div class="page-description">
    上传清晰人物照片，选择奶龙风格。
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
                        character_style = gr.Radio(
                            choices=[
                                "经典奶龙",
                                "可爱奶龙",
                                "校园奶龙",
                                "旅行奶龙",
                                "奇幻奶龙",
                            ],
                            value="经典奶龙",
                            label="选择生成风格",
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
                    fn=generate_nailong_mock,
                    inputs=[input_image, character_style],
                    outputs=[
                        avatar_output,
                        background_output,
                        avatar_state,
                        background_state,
                        generation_status,
                    ],
                )
                generate_event.then(
                    fn=lambda path: path,
                    inputs=avatar_state,
                    outputs=download_avatar_button,
                )

            # 冒险游戏
            with gr.Column(
                visible=False,
                elem_classes="page-shell",
            ) as game_page:
                gr.HTML("""
<div class="page-title">🎮 奶龙冒险游戏</div>
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
                    gr.HTML("""
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

            # 排行榜
            with gr.Column(
                visible=False,
                elem_classes="page-shell",
            ) as ranking_page:
                gr.HTML("""
<div class="page-title">🏆 奶龙冒险排行榜</div>
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
                        value=refresh_ranking_mock("总排行榜"),
                        interactive=False,
                    )

                refresh_ranking_button.click(
                    fn=refresh_ranking_mock,
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
        button.click(
            fn=lambda i=index: switch_page(i),
            outputs=page_outputs,
        )


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