import os
import json
import time
import pandas as pd
import dashscope
from dashscope import MultiModalConversation, ImageSynthesis

# ================= 配置区域 =================
dashscope.api_key = "sk-ws-H.EIHHLXE.ZZm7.MEQCIGGtcynQmeymU0PhYlej0lzzKUTkeHH456a0zxaiCOPfAiBaUWcYTwN-jbvwdIB9ezZQMbP9o18Mdb_DgDnycdSxCA"

IMAGE_FOLDER = "C:/Users/92788/Desktop/Train/Train" 
OUTPUT_FOLDER = "C:/Users/92788/Desktop/Train/output_cartoon_portraits"
CSV_PATH = "C:/Users/92788/Desktop/Train/character image.csv"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_pure_text(content):
    if isinstance(content, str): return content
    if isinstance(content, list):
        texts = [item['text'] for item in content if isinstance(item, dict) and 'text' in item]
        if texts: return " ".join(texts)
    return str(content)

def get_best_portraits(csv_path, n=5):
    """从 CSV 中筛选出【人像类】中打分最高的前 n 张图片"""
    df = pd.read_csv(csv_path)
    df['clean_id'] = df['编号'].astype(str).str.replace('.jpg', '', regex=False)
    
    # 筛选类别为“人像类”
    portrait_df = df[df['类别'] == '人像类']
    if portrait_df.empty:
        print(" -> 警告: 在 CSV 中没有找到‘人像类’，将从所有数据中按打分选取！")
        portrait_df = df
        
    # 按打分从高到低排序，取前 n 名
    if '打分' in portrait_df.columns:
        best_df = portrait_df.sort_values(by='打分', ascending=False).head(n)
    else:
        best_df = portrait_df.head(n)
        
    return best_df['clean_id'].tolist()

def generate_cartoon_portrait(human_id):
    """让 Qwen-VL 分析人像特征，并生成高质量的 3D 皮克斯/迪士尼风格卡通人物立绘"""
    human_img_path = os.path.join(IMAGE_FOLDER, f"{human_id}.jpg")
    if not os.path.exists(human_img_path):
        print(f" -> 警告: 找不到本地图片 {human_img_path}")
        return

    # 1. 多模态分析：提取人像的发型、性别、服装、配饰
    analysis_prompt = """
    【任务】：这是一张真人实拍人像照片。请仔细分析图中的人物特征：
    1. 性别与年龄段（如：年轻女性、小女孩、年轻男性等）。
    2. 发型、发色（如：短黑发、金色长卷发、双马尾等）。
    3. 脸型与标志性配饰（如：戴眼镜、微笑等）。
    4. 身上的衣服款式与颜色（如：粉色睡衣、蓝色格子裙、西装等）。
    
    【要求】：请将这些特征转化为一句高精度的 3D 迪士尼/皮克斯风格（Disney/Pixar 3D animation style）盲盒潮玩卡通人物立绘的英文 Prompt。
    必须包含：3D Pixar style, cute cartoon character, smooth clay texture, cinematic lighting, 8k resolution.
    只输出纯英文的 Prompt，不要任何多余废话。
    """

    messages = [{'role': 'user', 'content': [{'image': human_img_path}, {'text': analysis_prompt}]}]

    try:
        print(f" -> 正在分析编号 [{human_id}] 的真人面部与服装特征...")
        vl_response = MultiModalConversation.call(model='qwen-vl-plus', messages=messages)
        character_prompt = extract_pure_text(vl_response.output.choices[0].message.content)
        print(f"    [专属 3D 卡通 Prompt]: {character_prompt[:80]}...")

        # 2. 调用万相生图模型生成高颜值 3D 卡通人物
        rsp = ImageSynthesis.call(
            model='wanx2.1-t2i-turbo',  
            prompt=character_prompt,
            size='1024*1024',
            n=1
        )
        
        if rsp.status_code == 200:
            import urllib.request
            save_path = os.path.join(OUTPUT_FOLDER, f"cartoon_avatar_{human_id}.jpg")
            image_url = rsp.output.results[0].url
            urllib.request.urlretrieve(image_url, save_path)
            print(f"    [√] 3D 卡通人物生成成功！已保存至: {save_path}")
        else:
            print(f"    [×] 生成失败: {rsp.message}")
            
    except Exception as e:
        print(f"    [×] 运行报错: {e}")

def main():
    print("1. 正在从 CSV 中提取评分最高的人像类图片...")
    best_portrait_ids = get_best_portraits(CSV_PATH, n=5)
    print(f" -> 选中的高分人像编号为: {best_portrait_ids}")
    
    for hid in best_portrait_ids:
        generate_cartoon_portrait(hid)
        time.sleep(2)

    print("\n" + "="*40)
    print("【3D 卡通人物形象生成任务全部执行完毕】")
    print(f"请前往文件夹查看结果：{OUTPUT_FOLDER}")
    print("="*40)

if __name__ == "__main__":
    main()