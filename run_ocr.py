import os
import requests
import glob
from datetime import datetime

def process_all_screenshots():
    # 1. 找出所有剛上傳、還沒被更名的臨時截圖檔案 (支援 png, jpg, jpeg)
    temp_images = sorted(glob.glob("temp_screenshot.*") + glob.glob("IMG_*.*") + glob.glob("Screenshot_*.*"))
    today_str = datetime.now().strftime("%Y%m%d")
    
    if temp_images:
        print(f"偵測到 {len(temp_images)} 張新截圖，開始自動更名與處理...")
        # 自動重新命名為：20260625_1.jpg, 20260625_2.jpg ...
        for index, old_path in enumerate(temp_images, start=1):
            ext = os.path.splitext(old_path)[1].lower()
            new_name = f"{today_str}_{index}{ext}"
            os.rename(old_path, new_name)
            print(f"重新命名：{old_path} -> {new_name}")

    # 2. 找出所有屬於今天的日期檔案開始辨識
    today_images = sorted(glob.glob(f"{today_str}_*{ext}" for ext in ['.jpg', '.jpeg', '.png']))
    if not today_images:
        print("沒有找到今日需要辨識的截圖。")
        return

    all_names = []
    all_scores = []
    url = "https://api.ocr.space/parse/image"
    
    # 3. 逐張圖片發送給 AI 辨識 (Loop through all images for OCR)
    for img_path in today_images:
        print(f"正在辨識圖片: {img_path} ...")
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

    # 4. 數據配對並寫入 Excel 可開的 CSV 總表
    csv_path = "家族貢獻總表.csv"
    file_exists = os.path.exists(csv_path)
    
    with open(csv_path, 'a', encoding='utf-8-sig') as f:
        if not file_exists:
            f.write("日期,族友暱稱,今日活躍值\n")
        
        min_len = min(len(all_names), len(all_scores))
        display_date = datetime.now().strftime("%Y-%m-%d")
        for i in range(min_len):
            f.write(f"{display_date},{all_names[i]},{all_scores[i]}\n")
            
    print(f"🎉 所有人數據已成功合併登記至 家族貢獻總表.csv！")

if __name__ == "__main__":
    process_all_screenshots()
