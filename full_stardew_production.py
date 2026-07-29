import os
import json
import time
import pandas as pd
import dashscope
from dashscope import MultiModalConversation, ImageSynthesis

# ================= 专属配置与更新后的绝对路径 =================
dashscope.api_key = "sk-ws-H.EIHHLXE.ZZm7.MEQCIGGtcynQmeymU0PhYlej0lzzKUTkeHH456a0zxaiCOPfAiBaUWcYTwN-jbvwdIB9ezZQMbP9o18Mdb_DgDnycdSxCA"

IMAGE_FOLDER = "C:/Users/92788/Desktop/视觉语言处理大作业/数据集与训练集/Train" 
OUTPUT_FOLDER = "C:/Users/92788/Desktop/视觉语言处理大作业/游戏背景/output_universal_pixel"
PROMPT_TXT_FOLDER = "C:/Users/92788/Desktop/视觉语言处理大作业/游戏背景/background prompt"
CSV_PATH = "C:/Users/92788/Desktop/视觉语言处理大作业/游戏背景/landscape and architecture.csv"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PROMPT_TXT_FOLDER, exist_ok=True)

def extract_pure_text(content):
    if isinstance(content, str): return content
    if isinstance(content, list):
        texts = [item['text'] for item in content if isinstance(item, dict) and 'text' in item]
        if texts: return " ".join(texts)
    return str(content)

def get_all_scenery_samples(csv_path):
    """读取 CSV，精准提取出所有【风景建筑类】的图片编号"""
    if not os.path.exists(csv_path):
        print(f" -> 致命错误: 找不到 CSV 路径 {csv_path}，请检查文件是否存在！")
        return []
        
    df = pd.read_csv(csv_path)
    df['clean_id'] = df['编号'].astype(str).str.replace('.jpg', '', regex=False)
    
    category_col = '类别' if '类别' in df.columns else df.columns[1]
    scenery_df = df[df[category_col] == '风景建筑类']
    
    if scenery_df.empty:
        print(" -> 警告: 在 CSV 中没有匹配到‘风景建筑类’，请检查分类名称！")
        return []
        
    all_scenery_ids = scenery_df['clean_id'].tolist()
    return all_scenery_ids

def generate_with_universal_prompt(scene_id):
    """核心逻辑：Qwen-VL 提取原图景物 + 通用高精度像素风模板"""
    scene_img_path = os.path.join(IMAGE_FOLDER, f"{scene_id}.jpg")
    if not os.path.exists(scene_img_path):
        print(f" -> 警告: 找不到本地图片 {scene_img_path}")
        return False

    # 1. 动态提取景物短语
    analysis_prompt = """
    【任务】：用最简洁的英文短语描述这张风景照片的核心景物与构图主体（例如：a red barn in a green farm field / a quiet classroom with desks / snowy village houses）。
    要求：只输出景物的英文短语，绝对不要包含任何风格词（如pixel art等），字数控制在15个单词以内。
    """

    messages = [{'role': 'user', 'content': [{'image': scene_img_path}, {'text': analysis_prompt}]}]

    try:
        vl_response = MultiModalConversation.call(model='qwen-vl-plus', messages=messages)
        core_scenery = extract_pure_text(vl_response.output.choices[0].message.content).strip()
        
        # 2. 套用通用精细像素风 Prompt 模板
        universal_refined_prompt = (
            f"A 16-bit pixel art game level background of {core_scenery}, "
            "Stardew Valley style, retro video game aesthetic, crisp pixel edges, "
            "high detail pixel art, intricate environment details, vibrant and rich pixel colors, "
            "clean composition suitable for a 2D game background, masterclass indie game art, 8k resolution, sharp focus."
        )

        # 3. 保存 Prompt 到 TXT
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
            save_path = os.path.join(OUTPUT_FOLDER, f"true_pixel_bg_{scene_id}.jpg")
            image_url = rsp.output.results[0].url
            urllib.request.urlretrieve(image_url, save_path)
            print(f"    [√] 编号 [{scene_id}] 像素背景生成成功！")
            return True
        else:
            print(f"    [×] 编号 [{scene_id}] 生图失败: {rsp.message}")
            return False
            
    except Exception as e:
        print(f"    [×] 编号 [{scene_id}] 运行报错: {e}")
        return False

def main():
    print("1. 正在从 CSV 中提取所有【风景建筑类】图片...")
    all_scenery_ids = get_all_scenery_samples(CSV_PATH)
    total_count = len(all_scenery_ids)
    print(f" -> 共找到 {total_count} 张风景建筑类图片，准备开始全量生产！")
    
    if total_count == 0:
        return

    # 断点续传扫描：检查输出文件夹中已经有哪些图片，自动跳过
    already_done = set()
    if os.path.exists(OUTPUT_FOLDER):
        for f in os.listdir(OUTPUT_FOLDER):
            if f.startswith("true_pixel_bg_") and f.endswith(".jpg"):
                # 从文件名提取编号，例如 true_pixel_bg_124.jpg -> 124
                sid = f.replace("true_pixel_bg_", "").replace(".jpg", "")
                already_done.add(sid)

    print(f"【断点续传检查】已检测到本地已生成过 {len(already_done)} 张背景图，将自动跳过！\n" + "="*40)

    # 循环全量生成
    for index, sid in enumerate(all_scenery_ids):
        if sid in already_done:
            print(f"[{index + 1}/{total_count}] 编号 {sid} 已存在，跳过...")
            continue
            
        print(f"\n[{index + 1}/{total_count}] 正在全量处理编号: {sid}...")
        success = generate_with_universal_prompt(sid)
        
        # 礼貌休眠：每张图之间休息 1.5 秒，保护 API 额度不被瞬间 429 封禁
        time.sleep(1.5)

    print("\n" + "="*40)
    print("【风景建筑类全量像素背景生产任务圆满完成】")
    print(f"所有像素背景均已安全存入：{OUTPUT_FOLDER}")
    print(f"所有精细 Prompt 文本均已安全存入：{PROMPT_TXT_FOLDER}")
    print("="*40)

if __name__ == "__main__":
    main()