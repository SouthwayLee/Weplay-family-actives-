import os
import requests
import glob
from datetime import datetime

def process_all_screenshots():
    today_str = datetime.now().strftime("%Y%m%d")
    
    # 1. 搜集資料夾內所有的圖片
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    all_files = []
    for ext in extensions:
        all_files.extend(glob.glob(ext))
        
    # 【全新邏輯】只要名字裡面沒有「日期+底線+數字」，就代表是新上傳的原始截圖！
    temp_images = []
    for f in all_files:
        # 如果是 20260625_1.jpg 這種已經被我們改名過的就跳過
        if f.startswith(today_str) and "_" in f and f.split("_")[-1].replace(".jpg","").replace(".png","").replace(".jpeg","").isdigit():
            continue
        temp_images.append(f)
        
    temp_images = sorted(temp_images)
    
    if temp_images:
        print(f"偵測到 {len(temp_images)} 張新截圖，開始自動更名...")
        for index, old_path in enumerate(temp_images, start=1):
            ext = os.path.splitext(old_path)[1].lower()
            new_name = f"{today_str}_{index}{ext}"
            os.rename(old_path, new_name)
            print(f"重新命名成功：{old_path} -> {new_name}")
    else:
        print("沒有偵測到新上傳的原始截圖。")

    # 2. 重新抓取今天剛剛更名好的檔案 (例如 20260625_1.jpg)
    today_images = []
    for ext in ['.jpg', '.jpeg', '.png']:
        today_images.extend(glob.glob(f"{today_str}_*{ext}"))
    today_images = sorted(today_images)
    
    if not today_images:
        print("沒有找到今日改名完成、需要辨識的截圖。")
        return

    all_names = []
    all_scores = []
    url = "https://api.ocr.space/parse/image"
    
    for img_path in today_images:
        print(f"正在送往 AI 辨識圖片: {img_path} ...")
        payload = {'apikey': 'helloworld', 'language': 'cht'}
        with open(img_path, 'rb') as f:
            files = {'file': f}
            try:
                response = requests.post(url, data=payload, files=files)
                result = response.json()
                if result.get('OCRExitCode') == 1:
                    text = result['ParsedResults'][0]['ParsedText']
                    lines = text.split('\r\n')
                    for line in lines:
                        line = line.strip()
                        if not line or "家族" in line or "成員" in line:
                            continue
                        if line.isdigit():
                            all_scores.append(line)
                        else:
                            all_names.append(line)
                else:
                    print(f"圖片 {img_path} 辨識出錯：", result.get('ErrorMessage'))
            except Exception as e:
                print(f"連線失敗: {e}")

    # 3. 寫入或更新 CSV 表格
    csv_path = "家族貢獻總表.csv"
    file_exists = os.path.exists(csv_path)
    
    with open(csv_path, 'a', encoding='utf-8-sig') as f:
        if not file_exists:
            f.write("日期,族友暱稱,今日活躍值\n")
        
        min_len = min(len(all_names), len(all_scores))
        display_date = datetime.now().strftime("%Y-%m-%d")
        for i in range(min_len):
            f.write(f"{display_date},{all_names[i]},{all_scores[i]}\n")
            
    print("🎉 所有人數據已成功合併登記！")

if __name__ == "__main__":
    process_all_screenshots()
