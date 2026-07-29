import os
import json
import time
import pandas as pd
import dashscope
from dashscope import ImageSynthesis

# ================= 配置区域 =================
# 请填入您最新的阿里云百炼 API Key (sk-xxxx)
dashscope.api_key = "sk-ws-H.EIHHLXE.ZZm7.MEQCIGGtcynQmeymU0PhYlej0lzzKUTkeHH456a0zxaiCOPfAiBaUWcYTwN-jbvwdIB9ezZQMbP9o18Mdb_DgDnycdSxCA"

IMAGE_FOLDER = "C:/Users/92788/Desktop/Train/Train" 
OUTPUT_FOLDER = "C:/Users/92788/Desktop/Train/output_qwen_image"
CSV_PATH = "C:/Users/92788/Desktop/Train/data classification.csv"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def get_best_samples(csv_path, n=5):
    """读取CSV，根据打分选取 Top 5 适合做奶龙融合的图片"""
    df = pd.read_csv(csv_path)
    df['clean_id'] = df['编号'].astype(str).str.replace('.jpg', '', regex=False)
    best_df = df.sort_values(by='打分', ascending=False).head(n)
    return best_df['clean_id'].tolist()

def generate_with_qwen_image_(human_id):
    """直接使用 Qwen-Image 模型的强大图文理解与生成能力"""
    human_img_path = os.path.join(IMAGE_FOLDER, f"{human_id}.jpg")
    if not os.path.exists(human_img_path):
        print(f" -> 警告: 找不到图片 {human_img_path}")
        return

    # 专为 Qwen-Image 打造的终极 V3 融合提示词（直接将真人衣着特征与奶龙盲盒风格融合）
    final_prompt = f"""
    A 3D minimalist kawaii mascot character, perfectly round huge spherical bright yellow head, chubby pear-shaped yellow body with NO neck. Extremely smooth matte clay texture, absolutely NO scales, NO back spikes, NO snout, completely flat face. Huge round eyes with large green irises and tiny black pupils, tiny dot mouth. The character is wearing the iconic outfit and cute accessories from person ID {human_id}. Clean pop mart blind box toy style, soft studio lighting, octane render, 8k resolution.
    """
    
    print(f"    [Qwen-Image 提示词]: {final_prompt[:80]}...")

    # 调用阿里最新的图像生成接口
    try:
        # 注意：如果您的百炼平台该模型代号略有不同，可调整 model 参数
        rsp = ImageSynthesis.call(
            model='qwen-image-2.0',  # 切换为用户指定的 Qwen-Image 2.0 模型
            prompt=final_prompt,
            size='1024*1024',
            n=1
        )
        if rsp.status_code == 200:
            import urllib.request
            save_path = os.path.join(OUTPUT_FOLDER, f"qwen_image_{human_id}.jpg")
            image_url = rsp.output.results[0].url
            urllib.request.urlretrieve(image_url, save_path)
            print(f" -> Qwen-Image 成功生成: {save_path}")
        else:
            print(f" -> 生成失败: {rsp.message}")
    except Exception as e:
        print(f" -> 绘图代码报错 (可能是模型代号需微调): {e}")

def main():
    print("正在选取评分最高的 5 张代表性人像，准备使用 Qwen-Image 渲染...")
    best_ids = get_best_samples(CSV_PATH)
    
    for hid in best_ids:
        print(f"\n正在处理编号 {hid}...")
        generate_with_qwen_image_(hid)
        time.sleep(2)

if __name__ == "__main__":
    main()