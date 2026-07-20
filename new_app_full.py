"""照片转奶龙卡通闯关小游戏系统——独立、可直接运行的 Gradio 完整前端。

当前实现页面交互和占位接口，不修改 app.py、不使用数据库。
后续算法可接入 face_analysis.py、background_cartoon.py、game_generator.py。
"""
from __future__ import annotations

import json
import os
import tempfile
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import gradio as gr

TITLE = "照片转奶龙卡通闯关小游戏系统"
VERSION = "v1.0.0-frontend"
IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTS = {".mp4"}
MAX_VIDEO_SECONDS = 60
CSS = """
:root{--cream:#fffaf0;--milk:#fff4d7;--orange:#ff9f43;--orange2:#ff7c42;--brown:#5f3b24;--line:#f2d6a2}
body{background:linear-gradient(180deg,#fffdf7 0%,#fff8e8 100%)!important}
.gradio-container{max-width:1480px!important;margin:auto!important;padding:24px!important;color:var(--brown)}
.hero{position:relative;overflow:hidden;padding:34px 38px;border-radius:28px;background:linear-gradient(125deg,#fff7d6 0%,#ffe4a8 55%,#ffc97a 100%);border:1px solid #efc66f;box-shadow:0 14px 38px rgba(139,83,26,.12)}
.hero:after{content:'🐲';position:absolute;right:42px;top:10px;font-size:92px;filter:drop-shadow(0 10px 10px rgba(123,66,22,.14));transform:rotate(7deg)}
.hero .eyebrow{font-size:13px;font-weight:800;letter-spacing:2px;color:#b56a1e}.hero h1{margin:6px 0 8px!important;color:#673813!important;font-size:34px!important}.hero p{margin:0;max-width:760px;font-size:16px;color:#87572d}
.guide{margin:16px 0!important;padding:14px 18px!important;border:1px dashed #e8ba60!important;border-radius:14px!important;background:rgba(255,255,255,.7)!important}
.nav-title{text-align:center;margin:28px 0 4px!important}.nav-sub{text-align:center;color:#9b714b;margin-bottom:14px!important}
.nav-card{border:1px solid var(--line)!important;border-radius:20px!important;padding:8px!important;background:#fff!important;box-shadow:0 7px 20px rgba(112,70,28,.07);transition:.2s ease}
.nav-card:hover{transform:translateY(-3px);box-shadow:0 12px 25px rgba(112,70,28,.14)}
.nav-card .prose{text-align:center}.nav-card h3{font-size:17px!important;margin:5px 0!important}.nav-card p{font-size:13px;color:#9a7655;min-height:40px}
.nav-card button{min-height:44px!important;border-radius:13px!important;background:linear-gradient(135deg,var(--orange),var(--orange2))!important;color:#fff!important;border:0!important;font-weight:800!important}
.workspace{margin-top:22px!important}.side{position:sticky;top:12px;background:rgba(255,250,240,.94)!important;border:1px solid var(--line)!important;border-radius:20px!important;padding:16px!important;height:fit-content;box-shadow:0 8px 24px rgba(112,70,28,.07)}
.side h3{color:#794619!important}.panel{background:#fff!important;border:1px solid #f1dfbc!important;border-radius:20px!important;padding:18px!important;box-shadow:0 8px 24px rgba(112,70,28,.06)}
.section-head{padding:18px 22px!important;border-radius:18px!important;background:linear-gradient(100deg,#fff8df,#fff0c8)!important;border-left:6px solid var(--orange)!important;margin-bottom:14px!important}
.section-head h2{color:#704018!important;margin:0 0 5px!important}.section-head p{color:#98704d;margin:0!important}
.primary{background:linear-gradient(135deg,var(--orange),var(--orange2))!important;color:white!important;border:0!important;font-weight:800!important}
button{border-radius:12px!important}.footer{margin-top:22px;padding:18px 22px;border-radius:16px;background:#fff8e7;border:1px solid var(--line);color:#81572f}
@media(max-width:800px){.hero:after{display:none}.gradio-container{padding:12px!important}.hero{padding:24px}.hero h1{font-size:25px!important}.side{position:relative}}
"""


def path_of(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("path") or value.get("name")
    return getattr(value, "path", None) or getattr(value, "name", None)


def validate_image(value: Any, name: str) -> tuple[bool, str]:
    path = path_of(value)
    if not path:
        return False, f"{name}为空，请先上传图片。"
    if Path(path).suffix.lower() not in IMAGE_EXTS:
        return False, f"{name}格式错误，仅支持 JPG/PNG。"
    return True, ""


def notice(text: str, level: str = "info") -> str:
    {"error": gr.Error, "warning": gr.Warning}.get(level, gr.Info)(text)
    return text


def portrait_generate(image, size, color, local_style, strength, clarity, saturation):
    ok, error = validate_image(image, "人像照片")
    if not ok:
        return None, notice(error, "error")
    # TODO: 调用 face_analysis.py 分析五官并生成奶龙人物。
    msg = f"占位预览生成成功：大小{size}%｜{color}｜{local_style}｜全局参数{strength}/{clarity}/{saturation}"
    return image, notice(msg)


def game_generate(image, difficulty, monsters, props, duration, strength, clarity, saturation):
    ok, error = validate_image(image, "背景图片")
    if not ok:
        return None, notice(error, "error")
    # TODO: 调用 background_cartoon.py 与 game_generator.py。
    msg = f"占位场景生成成功：{difficulty}｜怪物{monsters}｜道具{props}｜{duration}秒｜全局参数{strength}/{clarity}/{saturation}"
    return image, notice(msg)


def make_zip(prefix: str, files: list[tuple[str, Any]], metadata: dict) -> str:
    target = os.path.join(tempfile.gettempdir(), f"{prefix}_{uuid.uuid4().hex[:8]}.zip")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(metadata, ensure_ascii=False, indent=2))
        for name, value in files:
            path = path_of(value)
            if path and os.path.isfile(path):
                zf.write(path, f"assets/{name}{Path(path).suffix.lower()}")
    return target


def game_export(image, difficulty, monsters, props, duration):
    ok, error = validate_image(image, "游戏场景")
    if not ok:
        return None, notice(error, "error")
    file = make_zip("nailong_game", [("scene", image)], {
        "project": TITLE, "type": "game_assets_placeholder", "difficulty": difficulty,
        "monster_count": monsters, "prop_count": props, "duration": duration,
        "created_at": datetime.now().isoformat(timespec="seconds")})
    return file, notice("游戏素材包导出成功。")


def animation_generate(portrait, scene, duration, video_filter, music, strength, clarity, saturation):
    for value, name in ((portrait, "奶龙形象"), (scene, "卡通背景")):
        ok, error = validate_image(value, name)
        if not ok:
            return None, None, notice(error, "error")
    # TODO: 接入视频合成与 MP4 编码模块。
    msg = f"动画请求已接收（占位接口）：{duration}秒｜{video_filter}｜{music}｜全局参数{strength}/{clarity}/{saturation}"
    return None, None, notice(msg)


def community_rows(works):
    return [[w["id"], w["title"], w["author"], w["type"], w["likes"], len(w["comments"]), w["time"]]
            for w in sorted(works or [], key=lambda x: x["likes"], reverse=True)]


def choices(works):
    return [f'{w["id"]}｜{w["title"]}' for w in works or []]


def publish(file, title, author, works):
    works = list(works or [])
    path = path_of(file)
    if not path:
        return works, community_rows(works), gr.skip(), notice("作品为空。", "error"), None
    suffix = Path(path).suffix.lower()
    if suffix not in IMAGE_EXTS | VIDEO_EXTS:
        return works, community_rows(works), gr.skip(), notice("仅支持 JPG/PNG/MP4。", "error"), None
    if not title.strip():
        return works, community_rows(works), gr.skip(), notice("请填写作品标题。", "warning"), file
    works.append({"id": uuid.uuid4().hex[:6].upper(), "title": title.strip(),
                  "author": author.strip() or "匿名用户", "type": "视频" if suffix == ".mp4" else "图片",
                  "likes": 0, "comments": [], "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "path": path})
    opts = choices(works)
    return works, community_rows(works), gr.Dropdown(choices=opts, value=opts[-1]), notice("作品发布成功。"), None


def like(selected, works):
    works = list(works or [])
    if not selected:
        return works, community_rows(works), notice("请先选择作品。", "warning")
    work_id = selected.split("｜", 1)[0]
    for work in works:
        if work["id"] == work_id:
            work["likes"] += 1
            return works, community_rows(works), notice("点赞成功。")
    return works, community_rows(works), notice("作品不存在。", "error")


def comment(selected, text, works):
    works = list(works or [])
    if not selected or not text.strip():
        return works, community_rows(works), [], text, notice("请选择作品并填写评论。", "warning")
    work_id = selected.split("｜", 1)[0]
    for work in works:
        if work["id"] == work_id:
            work["comments"].append([datetime.now().strftime("%H:%M"), text.strip()])
            return works, community_rows(works), work["comments"], "", notice("评论成功。")
    return works, community_rows(works), [], text, notice("作品不存在。", "error")


def select_work(selected, works):
    if not selected:
        return None, None, [], "请选择作品。"
    work_id = selected.split("｜", 1)[0]
    for work in works or []:
        if work["id"] == work_id:
            return ((None, work["path"]) if work["type"] == "视频" else (work["path"], None)) + (work["comments"], f'正在查看：{work["title"]}')
    return None, None, [], "作品不存在。"


def export_all(portrait, game, video, works):
    files = [("portrait", portrait), ("game_scene", game), ("animation", video)]
    files += [(f'community_{i}_{w["id"]}', w["path"]) for i, w in enumerate(works or [], 1)]
    target = make_zip("nailong_all", files, {"project": TITLE, "version": VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"), "community_count": len(works or [])})
    return target, notice("全部可用素材已打包。")


def build_app():
    with gr.Blocks(title=TITLE) as demo:
        works = gr.State([])
        gr.HTML('<div class="hero"><span class="eyebrow">NAILONG CREATIVE STUDIO</span><h1>照片转奶龙卡通闯关小游戏系统</h1><p>把珍贵照片变成专属奶龙角色、冒险关卡和动画短片，再与大家分享你的奇妙作品。</p></div>')
        gr.Markdown("✨ **快速开始**　选择下方创作板块 → 上传素材 → 调整参数 → 生成预览 → 导出或发布　　·　仅支持 JPG/PNG，MP4 最长 60 秒", elem_classes="guide")
        gr.Markdown("## 选择你想进入的创作板块", elem_classes="nav-title")
        gr.Markdown("四个板块独立工作，点击卡片即可快速切换", elem_classes="nav-sub")
        with gr.Row(equal_height=True):
            with gr.Column(elem_classes="nav-card"):
                gr.Markdown("### 🐲 奶龙人像\n上传人物照片，匹配五官生成专属奶龙形象")
                nav_portrait = gr.Button("进入人像生成区 →")
            with gr.Column(elem_classes="nav-card"):
                gr.Markdown("### 🎮 闯关场景\n卡通化真实背景，配置怪物、道具与难度")
                nav_game = gr.Button("进入游戏场景区 →")
            with gr.Column(elem_classes="nav-card"):
                gr.Markdown("### 🎬 动画短片\n组合人物和场景，生成带音乐的动画视频")
                nav_animation = gr.Button("进入动画短片区 →")
            with gr.Column(elem_classes="nav-card"):
                gr.Markdown("### 💬 作品社区\n发布作品、收获点赞并参与文字评论互动")
                nav_community = gr.Button("进入作品社区 →")
        with gr.Row(elem_classes="workspace"):
            with gr.Column(scale=1, min_width=260, elem_classes="side"):
                gr.Markdown("### 🎛️ 全局参数调节栏")
                strength = gr.Slider(0, 100, 70, label="卡通画风强度")
                clarity = gr.Slider(0, 100, 85, label="画面清晰度")
                saturation = gr.Slider(0, 100, 75, label="色彩饱和度")
                clear_all = gr.Button("清空所有上传")
                reset_all = gr.Button("一键重置页面")
                export_btn = gr.Button("批量导出全部素材", elem_classes="primary")
                all_file = gr.File(label="全部素材导出包", interactive=False)
                global_status = gr.Markdown("状态：等待操作")
            with gr.Column(scale=5):
                with gr.Tabs(selected="portrait") as main_tabs:
                    with gr.Tab("🐲 奶龙人像", id="portrait"):
                        gr.Markdown("## 奶龙人像形象生成区\n上传单人或多人实拍照片，提取五官特征并生成高辨识度奶龙人物。", elem_classes="section-head")
                        with gr.Row():
                            with gr.Column(elem_classes="panel"):
                                p_in = gr.Image(type="filepath", label="单人/多人实拍照片")
                                p_size = gr.Slider(50, 150, 100, step=5, label="奶龙大小（%）")
                                p_color = gr.Dropdown(["经典奶黄色", "蜜桃粉", "薄荷绿", "天空蓝", "自动匹配原图"], value="经典奶黄色", label="配色")
                                p_style = gr.Radio(["软萌3D", "手绘蜡笔", "动画赛璐璐", "水彩童话"], value="软萌3D", label="画风")
                                with gr.Row():
                                    p_go = gr.Button("生成奶龙人像", elem_classes="primary"); p_clear = gr.Button("清空本区")
                            with gr.Column(elem_classes="panel"):
                                p_out = gr.Image(type="filepath", label="奶龙卡通人像预览", interactive=False)
                                p_status = gr.Markdown("状态：请上传人物照片")
                    with gr.Tab("🎮 闯关场景", id="game"):
                        gr.Markdown("## 卡通闯关游戏场景生成区\n将原图背景自动卡通化，搭建可以继续扩展为互动游戏的冒险空间。", elem_classes="section-head")
                        with gr.Row():
                            with gr.Column(elem_classes="panel"):
                                g_in = gr.Image(type="filepath", label="原始背景图片")
                                difficulty = gr.Radio(["简单", "中等", "困难"], value="中等", label="游戏难度")
                                monsters = gr.Slider(0, 20, 5, step=1, label="怪物数量")
                                props = gr.Slider(0, 30, 8, step=1, label="道具数量")
                                g_duration = gr.Slider(30, 600, 120, step=10, label="游戏时长（秒）")
                                with gr.Row():
                                    g_go = gr.Button("生成游戏场景", elem_classes="primary"); g_clear = gr.Button("清空本区")
                            with gr.Column(elem_classes="panel"):
                                g_out = gr.Image(type="filepath", label="游戏画面预览", interactive=False)
                                g_export = gr.Button("导出游戏素材包"); g_file = gr.File(label="游戏素材包", interactive=False)
                                g_status = gr.Markdown("状态：请上传背景图片")
                    with gr.Tab("🎬 动画短片", id="animation"):
                        gr.Markdown("## 卡通动画短片生成区\n将奶龙形象与游戏背景合成短视频，自由选择时长、滤镜和音乐。", elem_classes="section-head")
                        with gr.Row():
                            with gr.Column(elem_classes="panel"):
                                a_p = gr.Image(type="filepath", label="奶龙形象")
                                a_g = gr.Image(type="filepath", label="卡通游戏背景")
                                a_duration = gr.Slider(5, 60, 15, step=5, label="视频时长（秒）")
                                a_filter = gr.Dropdown(["清新明亮", "复古胶片", "梦幻柔光", "活力漫画", "无滤镜"], value="清新明亮", label="滤镜")
                                music = gr.Dropdown(["欢快冒险", "萌趣电子", "童话管弦", "轻松日常", "无背景音乐"], value="欢快冒险", label="背景音乐")
                                with gr.Row():
                                    a_go = gr.Button("生成动画短片", elem_classes="primary"); a_clear = gr.Button("清空本区")
                            with gr.Column(elem_classes="panel"):
                                a_out = gr.Video(label="动画预览", interactive=False)
                                a_file = gr.File(label="下载 MP4", interactive=False)
                                a_status = gr.Markdown("状态：请上传形象和背景")
                    with gr.Tab("💬 作品社区", id="community"):
                        gr.Markdown("## 作品社区互动分享区\n发布卡通图、游戏截图或动画视频；点赞和评论保存在当前网页会话。", elem_classes="section-head")
                        with gr.Row():
                            with gr.Column(elem_classes="panel"):
                                c_file = gr.File(label="上传 JPG/PNG/MP4", file_types=[".jpg", ".jpeg", ".png", ".mp4"])
                                c_title = gr.Textbox(label="作品标题"); c_author = gr.Textbox(label="作者昵称")
                                with gr.Row():
                                    c_publish = gr.Button("发布作品", elem_classes="primary"); c_clear = gr.Button("清空表单")
                                selector = gr.Dropdown(label="选择公开作品", choices=[])
                                c_like = gr.Button("👍 点赞"); c_text = gr.Textbox(label="文字评论", lines=3)
                                c_comment = gr.Button("发布评论", elem_classes="primary")
                            with gr.Column(scale=2, elem_classes="panel"):
                                table = gr.Dataframe(headers=["ID", "标题", "作者", "类型", "点赞", "评论", "发布时间"], value=[], interactive=False, label="公开作品（按点赞排序）")
                                with gr.Row():
                                    c_img = gr.Image(type="filepath", label="图片预览", interactive=False)
                                    c_video = gr.Video(label="视频预览", interactive=False)
                                comments = gr.Dataframe(headers=["时间", "评论内容"], value=[], interactive=False, label="评论列表")
                                c_status = gr.Markdown("状态：等待发布作品")
        gr.HTML(f'<div class="footer"><b>环境依赖：</b>Python 3.10、Gradio 6.20.0、Pillow<br><b>版本：</b>{VERSION}<br><b>拓展：</b>可接入人脸分析、背景卡通化、游戏引擎、视频编码、登录与数据库。</div>')

        # 顶部四张功能卡：点击后直接切换到对应的独立板块。
        nav_portrait.click(lambda: gr.Tabs(selected="portrait"), outputs=main_tabs)
        nav_game.click(lambda: gr.Tabs(selected="game"), outputs=main_tabs)
        nav_animation.click(lambda: gr.Tabs(selected="animation"), outputs=main_tabs)
        nav_community.click(lambda: gr.Tabs(selected="community"), outputs=main_tabs)

        p_go.click(portrait_generate, [p_in, p_size, p_color, p_style, strength, clarity, saturation], [p_out, p_status])
        p_clear.click(lambda: (None, None, "状态：本区已清空"), outputs=[p_in, p_out, p_status])
        g_go.click(game_generate, [g_in, difficulty, monsters, props, g_duration, strength, clarity, saturation], [g_out, g_status])
        g_export.click(game_export, [g_out, difficulty, monsters, props, g_duration], [g_file, g_status])
        g_clear.click(lambda: (None, None, None, "状态：本区已清空"), outputs=[g_in, g_out, g_file, g_status])
        a_go.click(animation_generate, [a_p, a_g, a_duration, a_filter, music, strength, clarity, saturation], [a_out, a_file, a_status])
        a_clear.click(lambda: (None, None, None, None, "状态：本区已清空"), outputs=[a_p, a_g, a_out, a_file, a_status])
        c_publish.click(publish, [c_file, c_title, c_author, works], [works, table, selector, c_status, c_file])
        c_like.click(like, [selector, works], [works, table, c_status])
        c_comment.click(comment, [selector, c_text, works], [works, table, comments, c_text, c_status])
        selector.change(select_work, [selector, works], [c_img, c_video, comments, c_status])
        c_clear.click(lambda: (None, "", "", "", "状态：表单已清空"), outputs=[c_file, c_title, c_author, c_text, c_status])

        upload_outputs = [p_in, p_out, g_in, g_out, g_file, a_p, a_g, a_out, a_file, c_file, c_img, c_video, all_file]
        clear_all.click(lambda: [None] * len(upload_outputs), outputs=upload_outputs).then(lambda: notice("所有上传和预览已清空。"), outputs=global_status)
        reset_outputs = [strength, clarity, saturation] + upload_outputs + [p_size, p_color, p_style, difficulty, monsters, props, g_duration, a_duration, a_filter, music, works, table, selector, comments, global_status]
        reset_all.click(lambda: [70, 85, 75] + [None] * len(upload_outputs) + [100, "经典奶黄色", "软萌3D", "中等", 5, 8, 120, 15, "清新明亮", "欢快冒险", [], [], gr.Dropdown(choices=[], value=None), [], notice("页面已恢复默认设置。")], outputs=reset_outputs)
        export_btn.click(export_all, [p_out, g_out, a_file, works], [all_file, global_status])
    return demo


if __name__ == "__main__":
    build_app().launch(theme=gr.themes.Soft(), css=CSS)
