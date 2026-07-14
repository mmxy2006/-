import gradio as gr

# 图片处理空函数，后续再加卡通转换逻辑
def process_image(input_img):
    return input_img

# 网页整体界面
with gr.Blocks(title="照片转奶龙卡通闯关小游戏系统") as demo:
    gr.Markdown("# 照片转奶龙卡通闯关小游戏系统")
    # 左右分栏：上传区 + 结果区
    with gr.Row():
        img_input = gr.Image(type="pil", label="上传实拍照片", height=420)
        img_output = gr.Image(label="卡通生成结果", height=420)
    # 生成按钮
    generate_btn = gr.Button("一键生成卡通画面", variant="primary")
    # 绑定按钮点击事件
    generate_btn.click(fn=process_image, inputs=img_input, outputs=img_output)

# 启动本地网页
if __name__ == "__main__":
    demo.launch()