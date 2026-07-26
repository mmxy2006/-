import os
import json
import base64
import urllib.request
import urllib.error
import ssl
import csv
import time
from PIL import Image
from io import BytesIO

# ================= 配置区域 =================
API_KEY = "sk-ws-H.EIHHLXE.ZZm7.MEQCIGGtcynQmeymU0PhYlej0lzzKUTkeHH456a0zxaiCOPfAiBaUWcYTwN-jbvwdIB9ezZQMbP9o18Mdb_DgDnycdSxCA"
API_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
IMAGE_FOLDER = "." 
OUTPUT_JSON_FILE = "dataset_annotation.json"
# ============================================

def safe_int(val, default=0):
    try:
        if val is None: return default
        if isinstance(val, int): return val
        digits = ''.join(filter(str.isdigit, str(val).strip()))
        return int(digits) if digits else default
    except Exception:
        return default

def encode_image_to_base64(image_path, max_size=(800, 800)):
    with Image.open(image_path) as img:
        if img.mode != 'RGB': img = img.convert('RGB')
        img.thumbnail(max_size)
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

def classify_image(image_path):
    try:
        base64_image = encode_image_to_base64(image_path)
    except Exception:
        return None

    prompt = """
    你是一个专业的数据标注师。请分析我上传的这张图片，严格按照以下 JSON 格式输出结果，不要包含任何多余解释或 markdown 标记：

    {
      "category": "请务必只从以下六个选项中选择一个填入：[人像类, 风景建筑类, 动物类, 食物静物类, 文本截图类,设备类]",
      "visual_features": "用中文简短总结这张图片最核心的画面特征",
      "ai_generated_description": {
        "key_elements": "描述画面主体、动作或环境",
        "suggested_prompt": "如果要把这张图转化为Q版3D卡通风格，请给出对应的英文图像生成提示词"
      },
      "nailong_suitability_score": "如果 category 是'人像类'，请评估该人物转化为Q版奶龙形象的适合度打分(1-10的数字)；否则填 0"
    }
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-vl-plus", 
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}],
        "temperature": 0.1
    }
    
    req = urllib.request.Request(url=API_BASE_URL, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
    context = ssl._create_unverified_context()

    
    while True:
        try:
            with urllib.request.urlopen(req, context=context, timeout=60) as response:
                result_json = json.loads(response.read().decode('utf-8'))
                clean_text = result_json['choices'][0]['message']['content'].strip().replace("```json", "").replace("```", "").strip()
                return json.loads(clean_text)
                
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("      [!] 触发阿里限流 (429)，等待 15 秒后自动重试...")
                time.sleep(15)
                continue
            else:
                print(f"      [!] 请求失败 HTTP {e.code}")
                return None
        except Exception as e:
            print(f"      [!] 网络错误: {e}")
            return None

def generate_excel_and_stats(results, total_images):
    stats = {}
    for r in results:
        cat = r.get("category", "Error")
        stats[cat] = stats.get(cat, 0) + 1
        
    print(f"\n总计: {total_images} 张 (成功: {len(results)} 张)")
    for cat, count in stats.items():
        print(f" - {cat}: {count} 张 ({(count / total_images) * 100:.1f}%)")

    for cat in ["人像类", "风景建筑类", "动物类", "食物静物类", "文本截图类", "设备类","Error"]:
        items = [r for r in results if r.get("category") == cat or (cat=="Error" and r.get("category") not in ["人像类", "风景建筑类", "动物类", "食物静物类", "文本截图类"])]
        if not items: continue
            
        try:
            with open(f"{cat}.csv", "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["编号", "类别", "特征", "Prompt", "打分"])
                for item in items:
                    writer.writerow([item.get("image_id", ""), item.get("category", ""), item.get("visual_features", ""), item.get("ai_generated_description", {}).get("suggested_prompt", ""), item.get("nailong_suitability_score", "0")])
        except Exception: pass

def main():
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
    try: image_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))
    except Exception: image_files.sort()

    results = []
    processed_ids = set()
    if os.path.exists(OUTPUT_JSON_FILE):
        try:
            with open(OUTPUT_JSON_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
                processed_ids = {entry['image_id'] for entry in results if 'image_id' in entry}
                print(f"【断点续传】已读取本地数据，准备跳过 {len(processed_ids)} 张已完成图片。")
        except Exception: pass

    for index, filename in enumerate(image_files):
        if filename == "classify.py": continue
        
        if filename in processed_ids: 
            continue
        
        print(f"[{index + 1}/{len(image_files)}] 分析中: {filename}...")
        analysis = classify_image(os.path.join(IMAGE_FOLDER, filename))
        
        if analysis:
            cat = analysis.get("category", "")
            score = safe_int(analysis.get("nailong_suitability_score", 0)) if cat == "人像类" else 0
            results.append({
                "image_id": filename, "category": cat, "visual_features": analysis.get("visual_features", ""),
                "ai_generated_description": analysis.get("ai_generated_description", {}), "nailong_suitability_score": score
            })
            print(f" -> 成功: {cat} | 打分: {score}")
            
            try:
                with open(OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                processed_ids.add(filename)
            except Exception: pass
        time.sleep(1.5)

    generate_excel_and_stats(results, len(image_files))

if __name__ == "__main__":
    main()
