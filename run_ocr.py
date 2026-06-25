import os
import requests
import glob
from datetime import datetime

def process_all_screenshots():
    # 【偵錯防線】強迫印出目前雲端資料夾看得到的所有檔案
    print("【系統日誌】目前雲端資料夾內的檔案列表：", os.listdir('.'))
    
    today_str = datetime.now().strftime("%Y%m%d")
    
    # 1. 直接精準抓取所有以 Screenshot_ 或 IMG_ 開頭的原始截圖 (不分大小寫)
    extensions = ['Screenshot_*.*', 'screenshot_*.*', 'image-*.*', 'Image-*.*', 'IMG_*.*', 'img_*.*']
    temp_images = []
    for ext in extensions:
        temp_images.extend(glob.glob(ext))
        
    temp_images = sorted(list(set(temp_images))) # 去除重複並排序
    
    if temp_images:
        print(f"🎯 成功偵測到 {len(temp_images)} 張全新原始截圖，開始自動更名...")
        for index, old_path in enumerate(temp_images, start=1):
            ext = os.path.splitext(old_path)[1].lower()
            new_name = f"{today_str}_{index}{ext}"
            os.rename(old_path, new_name)
            print(f"重新命名成功：{old_path} -> {new_name}")
    else:
        print("❌ 沒有偵測到任何以 Screenshot_ 或 IMG_ 開頭的新截圖。")

    # 2. 抓取今天已經改名好的檔案 (例如 20260625_1.jpg) 準備送去辨識
    today_images = sorted(glob.glob(f"{today_str}_*.*"))
    
    if not today_images:
        print("📭 今天沒有改名完成的圖片需要辨識，流程結束。")
        return

    print(f"📝 開始發送 AI 辨識今天的 {len(today_images)} 張圖片...")
    all_names = []
    all_scores = []
    url = "https://api.ocr.space/parse/image"
    
    for img_path in today_images:
        print(f"正在辨識圖片: {img_path} ...")
        payload = {'apikey': 'helloworld', 'language': 'cht'}
        with open(img_path, 'rb') as f:
            files = {'file': f}
            try:
                response = requests.post(url, data=payload, files=files)
                
                # 【智慧防線：阻擋錯誤網頁，防止 JSONDecodeError 崩潰】
                if not response.text.strip().startswith('{'):
                    print(f"❌ 免費伺服器此時超載(未回傳標準資料)，已智慧跳過圖片 {img_path}，稍後重新觸發即可")
                    continue
                
                result = response.json()
                if result.get('OCRExitCode') == 1:
                    text = result['ParsedResults'][0]['ParsedText']
                    lines = text.split('\r\n')
                    
                    # 【智慧過濾黑名單：中英文職稱】
                    titles_to_remove = [
                        "族長", "副族長", "長老", "精英", "核心", "成員", "家族",
                        "Leader", "Deputy", "Admin", "Elder", "Elite", "Member"
                    ]

                    for line in lines:
                        line = line.strip()
                        
                        # 1. 智慧攔截：只要這行包含 ID、Lv 或活躍等介面雜訊，整行直接抹除跳過
                        skip_keywords = ["ID", "id", "Lv", "lv", "活躍", "位元", "總分", "貢獻"]
                        if any(k in line for k in skip_keywords):
                            continue
                            
                        # 2. 擦除傳統職稱
                        for title in titles_to_remove:
                            line = line.replace(title, "")
                            
                        # 3. 符號擦除器：消滅殘留的冒號與點號，防止干擾純數字判定
                        for symbol in [":", ".", "：", " ", "-", "_"]:
                            line = line.replace(symbol, "")
                            
                        line = line.strip()  # 再次修剪前後多餘的空白
                        
                        # 4. 空行防呆跳過
                        if not line:
                            continue
                            
                        # 5. 精準分類
                        if line.isdigit():
                            all_scores.append(line)
                        else:
                            all_names.append(line)
                else:
                    print(f"圖片 {img_path} 辨識出錯：", result.get('ErrorMessage'))
            except Exception as e:
                print(f"連線失敗或處理出錯: {e}")

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
            
    print("🎉 所有人數據已成功合併登記至 家族貢獻總表.csv！")

if __name__ == "__main__":
    process_all_screenshots()
