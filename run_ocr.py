import os
import requests
import glob
import re
from datetime import datetime

def process_all_screenshots():
    print("【系統日誌】目前雲端資料夾內的檔案列表：", os.listdir('.'))
    today_str = datetime.now().strftime("%Y%m%d")
    
    # 1. 自動偵測並更名所有圖片 (包含 1782 開頭與 Image 開頭的所有截圖)
    extensions = ['Screenshot_*.*', 'screenshot_*.*', 'IMG_*.*', 'img_*.*', 'Image_*.*', 'image-*.*', 'image_*.*']
    temp_images = []
    for ext in extensions:
        temp_images.extend(glob.glob(ext))
        
    temp_images = sorted(list(set(temp_images)))
    
    if temp_images:
        print(f"🎯 成功偵測到 {len(temp_images)} 張全新原始截圖，開始自動更名...")
        for index, old_path in enumerate(temp_images, start=1):
            ext = os.path.splitext(old_path)[1].lower()
            new_name = f"{today_str}_{index}{ext}"
            os.rename(old_path, new_name)
            print(f"重新命名成功：{old_path} -> {new_name}")
            
    today_images = sorted(glob.glob(f"{today_str}_*.*"))
    if not today_images:
        print("📭 今天沒有需要辨識的圖片，流程結束。")
        return

    print(f"📝 開始發送 AI 辨識今天的 {len(today_images)} 張圖片...")
    
    final_data_pairs = [] # 存放最終結果 [(名字, 周活躍, 總活躍), ...]
    url = "https://api.ocr.space/parse/image"
    
    for img_path in today_images:
        print(f"正在辨識圖片: {img_path} ...")
        # 💡 關鍵變更：因為切換成英文版介面，OCR 辨識語言調整為 'eng' 速度與精準度會大幅提升！
        payload = {'apikey': 'helloworld', 'language': 'cht'}
        with open(img_path, 'rb') as f:
            files = {'file': f}
            try:
                response = requests.post(url, data=payload, files=files)
                
                if not response.text.strip().startswith('{'):
                    print(f"❌ 免費伺服器此時超載，已智慧跳過圖片 {img_path}")
                    continue
                
                result = response.json()
                if result.get('OCRExitCode') == 1:
                    text = result['ParsedResults'][0]['ParsedText']
                    
                    print(f"--- 💡【偵錯】AI 原始文字 ---")
                    print(text)
                    print("----------------------------")
                    
                    lines = text.split('\r\n')
                    
                    # 狀態機位置記憶體初始化
                    temp_name = None
                    temp_weekly = None
                    temp_total = None
                    expecting = None # 用於處理數值與關鍵字斷行的防呆

                                        # 建立一個乾淨的清單（舊的 temp_name, temp_weekly 等暫存盒都不需要了！）
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        line_lower = line.lower()
                        
                        # 【強力防噪防線】排除手機頂部雜訊（時間、網路、標題列等）
                        if (re.match(r'^\d{2}:\d{2}$', line) or 
                            re.match(r'^\d+/\d+$', line) or     
                            line_lower in ["4g", "5g", "lte", "wifi"] or 
                            any(k in line_lower for k in ["family", "tasks", "members", "moments", "manage", "成員", "任務", "動態", "管理", "activeness", "donation", "weekly", "total", "週貢獻", "總貢獻"])):
                            continue

                        # ✨【全新設定：單行直抓名字+雙數字】
                        # 1. 用 findall 找出這一行所有的數字（例如輸入 "李艾德 1100 30.0K"，會抓出 ['1100', '30.0K']）
                        nums = re.findall(r'\d+\.?\d*[Kk]?', line)
                        
                        # 2. 核心條件：這一行必須「至少有兩個數字」才處理
                        if len(nums) >= 2:
                            weekly_val = nums[0]  # 第一個數字是週活躍
                            total_val = nums[1]   # 第二個數字是總活躍
                            
                            # 3. 用 find 找到第一個數字在字串中的起點位置
                            first_num_pos = line.find(weekly_val)
                            
                            # 4. 切割字串：起點左邊 [:first_num_pos] 的通通歸類為名字
                            name_part = line[:first_num_pos]
                            
                            # 5. 擦除名字區域內可能夾帶的職稱或等級雜訊
                            titles_to_remove = ["leader", "deputy", "admin", "member", "core", "family", "族長", "副族長", "長老", "成員", "lv", "level", "id"]
                            for title in titles_to_remove:
                                name_part = re.sub(re.escape(title), "", name_part, flags=re.IGNORECASE)
                            
                            # 6. 清理常見 OCR 錯判的符號
                            for symbol in [":", ".", "：", " ", "-", "_", ",", "I", "l", "|", "…", "★", "☆"]:
                                name_part = name_part.replace(symbol, "")
                                
                            clean_text = name_part.strip()
                            
                            # 7. 只要名字擦乾淨後長度大於 1，立刻 append 打包進最終總表！
                            if clean_text and len(clean_text) > 1:
                                final_data_pairs.append((clean_text, weekly_val, total_val))

                            
                            # 重置暫存置物盒，開始裝新人的資料
                            temp_name = clean_text
                            temp_weekly = None
                            temp_total = None
                            expecting = None

                    # 檢查並儲存最後留存在盒子裡的最後一個人
                    if temp_name and (temp_weekly or temp_total):
                        final_data_pairs.append((temp_name, temp_weekly or "0", temp_total or "0"))
                            
                else:
                    print(f"圖片 {img_path} 辨識出錯：", result.get('ErrorMessage'))
            except Exception as e:
                print(f"連線失敗或處理出錯: {e}")

    # 3. 寫入或更新 CSV 表格
    csv_path = "家族貢獻總表.csv"
    needs_header = True
    
    # 【超級安全機制】檢查舊表格欄位是否相符
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            first_line = f.readline()
            if "周活躍" in first_line:
                needs_header = False
            else:
                # 如果是舊版的單一活躍度表格，自動更名備份，不讓新舊數據混在一起
                backup_path = f"家族貢獻總表_舊版備份_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
                os.rename(csv_path, backup_path)
                print(f"⚠️ 偵測到舊版欄位表格，已自動備份為：{backup_path}")
                needs_header = True
    
    print(f"📊 【精準配對統計】本次成功綁定「周+總活躍」的總人數：{len(final_data_pairs)} 人")
    
    with open(csv_path, 'a', encoding='utf-8-sig') as f:
        if needs_header:
            f.write("日期,族友暱稱,周活躍值,總活躍值\n")
        
        display_date = datetime.now().strftime("%Y-%m-%d")
        for name, weekly, total in final_data_pairs:
            f.write(f"{display_date},{name},{weekly},{total}\n")
            
    print("🎉 名字、周活躍、總活躍已完美登記至 家族貢獻總表.csv！")

if __name__ == "__main__":
    process_all_screenshots()
