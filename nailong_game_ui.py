"""奶龙奇趣大冒险——独立 Gradio 小游戏界面演示。

运行：python nailong_game_ui.py
说明：当前实现完整界面与前端模拟交互，后续可对接 game_generator.py。
"""
from __future__ import annotations

import random
import time
from typing import Any

import gradio as gr


TITLE = "奶龙奇趣大冒险"
VERSION = "v1.0.0-ui"

CSS = r"""
:root{--ink:#563822;--cream:#fff9e9;--yellow:#ffd85c;--orange:#ff914d;--coral:#ff7058;--green:#74c98b;--line:#efcf91}
body{background:radial-gradient(circle at 10% 10%,#fff3bf 0,transparent 25%),linear-gradient(180deg,#fffdf5,#fff5d9)!important}
.gradio-container{max-width:1450px!important;margin:auto!important;padding:22px!important;color:var(--ink)}
.game-hero{position:relative;overflow:hidden;padding:26px 32px;border-radius:28px;background:linear-gradient(125deg,#ffe778,#ffc45f 58%,#ff9c58);border:2px solid #eeb44d;box-shadow:0 15px 38px rgba(123,73,23,.16)}
.game-hero:after{content:'☁️  ⭐  ☁️';position:absolute;right:35px;top:22px;font-size:35px;opacity:.85}.game-hero h1{margin:3px 0!important;font-size:35px!important;color:#663813!important}.game-hero p{margin:6px 0 0;color:#875025;font-weight:600}
.badge{display:inline-block;padding:5px 11px;border-radius:99px;background:#fff8d9;border:1px solid #e8b649;font-size:12px;font-weight:900;letter-spacing:1px}
.status-strip{margin:14px 0!important;padding:11px 16px!important;border-radius:14px!important;background:#fff!important;border:1px solid var(--line)!important;box-shadow:0 5px 16px rgba(100,65,24,.06)}
.card{background:rgba(255,255,255,.94)!important;border:1px solid var(--line)!important;border-radius:21px!important;padding:17px!important;box-shadow:0 9px 25px rgba(104,65,19,.08)}
.card h3{color:#74451f!important;margin-top:0!important}.side{height:fit-content}.screen-shell{padding:12px!important;background:#6d4226!important;border:5px solid #4e301e!important;border-radius:25px!important;box-shadow:inset 0 0 0 2px #9a6843,0 13px 28px rgba(63,37,19,.22)}
.game-screen{position:relative;min-height:460px;border-radius:15px;overflow:hidden;background:linear-gradient(#74d7ff 0 52%,#b8e87d 52% 73%,#a66b3f 73%);font-family:ui-rounded,'PingFang SC',sans-serif}
.game-screen:before{content:'☁️　　　　☁️　　　　　　　　☁️';position:absolute;top:42px;left:4%;font-size:40px;opacity:.92}.game-screen .mountains{position:absolute;bottom:27%;left:0;width:100%;font-size:92px;white-space:nowrap;opacity:.7}.game-screen .hud{position:absolute;z-index:3;left:16px;right:16px;top:14px;display:flex;justify-content:space-between;gap:8px}.hud span{padding:7px 11px;border-radius:10px;background:rgba(255,250,224,.92);border:2px solid #80502c;font-weight:900;color:#603719}.game-screen .player{position:absolute;z-index:4;left:18%;bottom:19%;font-size:78px;filter:drop-shadow(0 8px 4px rgba(68,45,24,.25));animation:bob 1.8s ease-in-out infinite}.game-screen .goal{position:absolute;right:8%;bottom:22%;font-size:74px}.game-screen .monster{position:absolute;right:38%;bottom:20%;font-size:60px}.game-screen .coin{position:absolute;left:46%;bottom:39%;font-size:35px;animation:spin 1.8s linear infinite}.game-screen .platform{position:absolute;left:36%;bottom:33%;font-size:70px}.game-screen .hint{position:absolute;left:50%;bottom:8px;transform:translateX(-50%);white-space:nowrap;padding:6px 13px;border-radius:10px;background:rgba(77,44,25,.78);color:white;font-size:13px}
@keyframes bob{50%{transform:translateY(-10px)}}@keyframes spin{50%{transform:rotateY(180deg)}}
.main-btn{background:linear-gradient(135deg,var(--orange),var(--coral))!important;color:white!important;border:0!important;font-size:16px!important;font-weight:900!important;min-height:47px!important}.green-btn{background:linear-gradient(135deg,#80d89a,#51b978)!important;color:white!important;border:0!important;font-weight:800!important}button{border-radius:13px!important}
.control-key{display:grid;grid-template-columns:repeat(3,44px);gap:7px;justify-content:center;margin:5px auto 10px}.key{display:grid;place-items:center;height:40px;border-radius:9px;background:#fff7da;border:2px solid #c78b45;box-shadow:0 4px 0 #a76c34;font-weight:900}.empty{visibility:hidden}
.result-box{padding:14px 16px;border-radius:14px;background:#fff9e8;border:1px dashed #e2ad54}.footer{margin-top:18px;padding:15px 20px;border-radius:15px;background:#fff8e5;border:1px solid var(--line);color:#8a623d}
@media(max-width:800px){.gradio-container{padding:10px!important}.game-hero{padding:21px}.game-hero h1{font-size:27px!important}.game-hero:after{display:none}.game-screen{min-height:370px}.game-screen .player{font-size:62px}}
"""


SCENES = {
    "糖果森林": ("🍭", "棉花糖怪", "寻找丢失的星星糖"),
    "云朵城堡": ("🏰", "雷云精灵", "登上天空城堡顶层"),
    "海底乐园": ("🪸", "泡泡章鱼", "收集七颗珍珠"),
    "火山秘境": ("🌋", "熔岩小怪", "取回勇气水晶"),
}


def render_screen(scene: str, character: str, difficulty: str, hearts: int, coins: int, props: int, message: str) -> str:
    icon, monster, mission = SCENES[scene]
    face = {"经典奶龙": "🐲", "草莓奶龙": "🐉", "薄荷奶龙": "🦕"}[character]
    return f"""
    <div class="game-screen">
      <div class="hud"><span>❤️ {hearts}</span><span>⭐ {coins}</span><span>🎒 {props}</span><span>{difficulty}</span></div>
      <div class="mountains">🌲　🌳　{icon}　🌲　🌳</div>
      <div class="player">{face}</div><div class="platform">🪵</div><div class="coin">🪙</div>
      <div class="monster">👾</div><div class="goal">🚩</div>
      <div class="hint">任务：{mission}　·　对手：{monster}　·　{message}</div>
    </div>"""


def new_game(scene: str, character: str, difficulty: str, duration: int):
    state = {"scene": scene, "character": character, "difficulty": difficulty,
             "hearts": 3, "coins": 0, "props": 1, "score": 0,
             "duration": duration, "started": time.time(), "running": True}
    screen = render_screen(scene, character, difficulty, 3, 0, 1, "冒险开始，向终点出发！")
    return state, screen, "### 🎉 新冒险已开始\n使用操作按钮帮助奶龙收集金币并到达终点。", gr.update(interactive=True)


def take_action(action: str, state: dict[str, Any] | None):
    if not state or not state.get("running"):
        return state or {}, gr.skip(), "### 请先点击“开始新冒险”"
    event = random.random()
    if action == "跳跃":
        if event < .72:
            state["coins"] += 1; state["score"] += 120; message = "漂亮的跳跃！获得一枚金币"
        else:
            state["hearts"] -= 1; message = "碰到了障碍，失去一颗爱心"
    elif action == "使用道具":
        if state["props"] > 0:
            state["props"] -= 1; state["score"] += 200; message = "无敌星生效，击退前方小怪"
        else:
            message = "背包空空，继续寻找道具吧"
    else:
        gain = random.randint(40, 100); state["score"] += gain; message = f"向{action}前进，获得 {gain} 分"
        if event < .25: state["props"] += 1; message += "，还发现了一个道具"
    elapsed = int(time.time() - state["started"])
    if state["hearts"] <= 0:
        state["running"] = False; message = "爱心用完啦，点击重新开始再次挑战"
    elif state["coins"] >= 5:
        state["running"] = False; state["score"] += 1000; message = "闯关成功！奶龙顺利抵达终点"
    elif elapsed >= state["duration"]:
        state["running"] = False; message = "本轮时间结束，再试一次吧"
    screen = render_screen(state["scene"], state["character"], state["difficulty"], state["hearts"], state["coins"], state["props"], message)
    status = f"### 当前得分：{state['score']}\n爱心 {state['hearts']}　·　金币 {state['coins']}/5　·　道具 {state['props']}"
    return state, screen, status


def reset_game():
    return {}, render_screen("糖果森林", "经典奶龙", "简单", 3, 0, 1, "点击开始新冒险"), "### 等待开始\n先在左侧选择角色和关卡。", gr.update(interactive=False)


def build_app() -> gr.Blocks:
    with gr.Blocks(title=TITLE) as demo:
        game_state = gr.State({})
        gr.HTML('<div class="game-hero"><span class="badge">NAILONG ADVENTURE</span><h1>🐲 奶龙奇趣大冒险</h1><p>选择你的奶龙伙伴，穿越童话关卡，收集金币与星光宝物！</p></div>')
        gr.Markdown("🎯 **玩法目标**　收集 5 枚金币并安全抵达终点　　·　　💡 当前为界面与交互演示版", elem_classes="status-strip")

        with gr.Row():
            with gr.Column(scale=1, min_width=260, elem_classes=["card", "side"]):
                gr.Markdown("### 🗺️ 冒险配置")
                scene = gr.Dropdown(list(SCENES), value="糖果森林", label="选择关卡")
                character = gr.Radio(["经典奶龙", "草莓奶龙", "薄荷奶龙"], value="经典奶龙", label="选择角色")
                difficulty = gr.Radio(["简单", "中等", "困难"], value="简单", label="难度")
                duration = gr.Slider(30, 180, 60, step=15, label="挑战时间（秒）")
                start_btn = gr.Button("🚀 开始新冒险", elem_classes="main-btn")
                reset_btn = gr.Button("↻ 重新设置")
                gr.Markdown("### 🎮 操作说明")
                gr.HTML('<div class="control-key"><span class="empty"></span><span class="key">W</span><span class="empty"></span><span class="key">A</span><span class="key">S</span><span class="key">D</span></div>')
                gr.Markdown("使用方向按钮移动，点击跳跃越过障碍，合理使用背包道具。")

            with gr.Column(scale=3):
                with gr.Group(elem_classes="screen-shell"):
                    game_screen = gr.HTML(render_screen("糖果森林", "经典奶龙", "简单", 3, 0, 1, "点击开始新冒险"))
                with gr.Row():
                    left_btn = gr.Button("⬅️ 向左", interactive=False)
                    jump_btn = gr.Button("⬆️ 跳跃", elem_classes="main-btn", interactive=False)
                    right_btn = gr.Button("向右 ➡️", interactive=False)
                    prop_btn = gr.Button("⭐ 使用道具", elem_classes="green-btn", interactive=False)
                game_status = gr.Markdown("### 等待开始\n先在左侧选择角色和关卡。", elem_classes="result-box")

        with gr.Row():
            with gr.Column(elem_classes="card"):
                gr.Markdown("### 🏆 今日冒险榜")
                gr.Dataframe(headers=["排名", "冒险家", "关卡", "得分"],
                    value=[[1, "奶糖小队", "云朵城堡", 3280], [2, "星星收藏家", "糖果森林", 2960], [3, "薄荷汽水", "海底乐园", 2750]], interactive=False)
            with gr.Column(elem_classes="card"):
                gr.Markdown("### 🎒 本周挑战")
                gr.Markdown("- 收集 **20 枚金币**　`12 / 20`\n- 完成 **3 个不同关卡**　`1 / 3`\n- 无伤通过一次困难关卡　`未完成`")

        gr.HTML(f'<div class="footer"><b>{TITLE}</b> · {VERSION}　｜　后续可接入 game_generator.py、键盘控制、碰撞检测、关卡地图和成绩保存。</div>')

        controls = [left_btn, jump_btn, right_btn, prop_btn]
        start_btn.click(new_game, [scene, character, difficulty, duration], [game_state, game_screen, game_status, left_btn]).then(
            lambda: [gr.update(interactive=True)] * 3, outputs=[jump_btn, right_btn, prop_btn])
        reset_btn.click(reset_game, outputs=[game_state, game_screen, game_status, left_btn]).then(
            lambda: [gr.update(interactive=False)] * 3, outputs=[jump_btn, right_btn, prop_btn])
        left_btn.click(lambda s: take_action("左", s), game_state, [game_state, game_screen, game_status])
        right_btn.click(lambda s: take_action("右", s), game_state, [game_state, game_screen, game_status])
        jump_btn.click(lambda s: take_action("跳跃", s), game_state, [game_state, game_screen, game_status])
        prop_btn.click(lambda s: take_action("使用道具", s), game_state, [game_state, game_screen, game_status])
    return demo


if __name__ == "__main__":
    build_app().launch(theme=gr.themes.Soft(), css=CSS)
