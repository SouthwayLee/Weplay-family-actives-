import os
import requests
import glob
from datetime import datetime

def process_all_screenshots():
    today_str = datetime.now().strftime("%Y%m%d")
    
    # 這裡把所有可能的關鍵字（包含大寫 Screenshot、小寫 screenshot、IMG）全部封鎖抓進來
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
    all_files = []
    for ext in extensions:
        all_files.extend(glob.glob(ext))
        
    # 過濾掉已經被我們改名成當天日期的檔案，剩下的就是你剛上傳的新截圖
    temp_images = [f for f in all_files if not f.startswith(today_str) and f != "run_ocr.py"]
    temp_images = sorted(temp_images)
    
    if temp_images:
        print(f"偵測到 {len(temp_images)} 張新截圖，開始自動更名與處理...")
        for index, old_path in enumerate(temp_images, start=1):
            ext = os.path.splitext(old_path)[1].lower()
            new_name = f"{today_str}_{index}{ext}"
            os.rename(old_path, new_name)
            print(f"重新命名成功：{old_path} -> {new_name}")
    else:
        print("沒有偵測到新上傳的臨時截圖。")

    # 重新抓取今天已經更名完成的檔案準備辨識
    today_images = sorted([f for f in glob.glob(f"{today_str}_*") if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    
    if not today_images:
        print("沒有找到今日需要辨識的截圖。")
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

    # 寫入 CSV 表格
    csv_path = "家族貢獻總表.csv"
    file_exists = os.path.exists(csv_path)
    
    with open(csv_path, 'a', encoding='utf-8-sig') as f:
        if not file_exists:
            f.write("日期,族友暱稱,今日活躍值\n")
        
        min_len = min(len(all_names), len(all_scores))
        display_date = datetime.now().strftime("%Y-%m-%d")
        for i in range(min_len):
            f.write(f"{display_date},{all_names[i]},{all_scores[i]}\n")
            
    print(f"🎉 所有人數據已成功登記！")

if __name__ == "__main__":
    process_all_screenshots()
