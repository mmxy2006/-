import os
import json
import time
import random
import pandas as pd
import dashscope
from dashscope import MultiModalConversation, ImageSynthesis

# ================= 配置与路径区域 =================
dashscope.api_key = "sk-ws-H.EIHHLXE.ZZm7.MEQCIGGtcynQmeymU0PhYlej0lzzKUTkeHH456a0zxaiCOPfAiBaUWcYTwN-jbvwdIB9ezZQMbP9o18Mdb_DgDnycdSxCA"

IMAGE_FOLDER = "C:/Users/92788/Desktop/视觉语言处理大作业/数据集与训练集/Train" 
OUTPUT_FOLDER = "C:/Users/92788/Desktop/视觉语言处理大作业/游戏背景/output_universal_pixel"
PROMPT_TXT_FOLDER = "C:/Users/92788/Desktop/视觉语言处理大作业/游戏背景/background prompt"
CSV_PATH = "C:/Users/92788/Desktop/视觉语言处理大作业/游戏背景/data classification.csv"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PROMPT_TXT_FOLDER, exist_ok=True)

def extract_pure_text(content):
    if isinstance(content, str): return content
    if isinstance(content, list):
        texts = [item['text'] for item in content if isinstance(item, dict) and 'text' in item]
        if texts: return " ".join(texts)
    return str(content)

def get_random_scenery_samples(csv_path, n=5):
    """从 CSV 中筛选出【风景建筑类】的图片，并随机抽取 n 张进行测试"""
    if not os.path.exists(csv_path):
        all_files = [f.replace('.jpg', '') for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith('.jpg')]
        return random.sample(all_files, min(n, len(all_files)))
        
    df = pd.read_csv(csv_path)
    df['clean_id'] = df['编号'].astype(str).str.replace('.jpg', '', regex=False)
    
    category_col = '类别' if '类别' in df.columns else df.columns[1]
    scenery_df = df[df[category_col] == '风景建筑类']
    
    if scenery_df.empty: scenery_df = df
    all_ids = scenery_df['clean_id'].tolist()
    return random.sample(all_ids, min(n, len(all_ids)))

def generate_with_universal_prompt(scene_id):
    """核心逻辑：Qwen-VL 提取原图景物 + 通用高精度像素风模板"""
    scene_img_path = os.path.join(IMAGE_FOLDER, f"{scene_id}.jpg")
    if not os.path.exists(scene_img_path):
        print(f" -> 警告: 找不到本地图片 {scene_img_path}")
        return

    # 1. 极简任务：让多模态大模型“只提取画面的核心景物与主体色彩”
    analysis_prompt = """
    【任务】：用最简洁的英文短语描述这张风景照片的核心景物与构图主体（例如：a red barn in a green farm field / a quiet classroom with desks / snowy village houses）。
    要求：只输出景物的英文短语，绝对不要包含任何风格词（如pixel art等），字数控制在15个单词以内。
    """

    messages = [{'role': 'user', 'content': [{'image': scene_img_path}, {'text': analysis_prompt}]}]

    try:
        print(f" -> 正在提取编号 [{scene_id}] 的核心景物...")
        vl_response = MultiModalConversation.call(model='qwen-vl-plus', messages=messages)
        core_scenery = extract_pure_text(vl_response.output.choices[0].message.content).strip()
        
        # 2. 核心：套用我们精心调优的【通用精细像素风 Prompt 模板】
        universal_refined_prompt = (
            f"A 16-bit pixel art game level background of {core_scenery}, "
            "Stardew Valley style, retro video game aesthetic, crisp pixel edges, "
            "high detail pixel art, intricate environment details, vibrant and rich pixel colors, "
            "clean composition suitable for a 2D game background, masterclass indie game art, 8k resolution, sharp focus."
        )
        print(f"    [通用精细像素 Prompt]: {universal_refined_prompt[:90]}...")

        # 3. 保存该图对应的通用 Prompt 到 TXT
        txt_path = os.path.join(PROMPT_TXT_FOLDER, f"universal_pixel_{scene_id}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(universal_refined_prompt)

        # 4. 调用万相生图模型渲染
        rsp = ImageSynthesis.call(
            model='wanx2.1-t2i-turbo',  
            prompt=universal_refined_prompt,
            size='1024*1024',
            n=1
        )
        
        if rsp.status_code == 200:
            import urllib.request
            save_path = os.path.join(OUTPUT_FOLDER, f"universal_pixel_bg_{scene_id}.jpg")
            image_url = rsp.output.results[0].url
            urllib.request.urlretrieve(image_url, save_path)
            print(f"    [√] 通用精细像素背景生成成功！已保存至: {save_path}")
        else:
            print(f"    [×] 生成失败: {rsp.message}")
            
    except Exception as e:
        print(f"    [×] 运行报错: {e}")

def main():
    print("1. 正在随机抽取 5 张风景建筑类图片进行通用模板测试...")
    selected_ids = get_random_scenery_samples(CSV_PATH, n=5)
    print(f" -> 选中的风景建筑类编号为: {selected_ids}")
    
    for sid in selected_ids:
        generate_with_universal_prompt(sid)
        time.sleep(2)

    print("\n" + "="*40)
    print("【通用像素风流水线运行完毕】")
    print(f"图片保存在：{OUTPUT_FOLDER}")
    print(f"通用 Prompt 描述文件保存在：{PROMPT_TXT_FOLDER}")
    print("="*40)

if __name__ == "__main__":
    main()