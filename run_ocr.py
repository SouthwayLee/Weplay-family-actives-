import os
import requests
import json
from datetime import datetime

def do_ocr():
    # 這是免費的 OCR 線上辨識接口
    url = "https://api.ocr.space/parse/image"
    img_path = "weplay.jpg"
    
    if not os.path.exists(img_path):
        print("找不到 weplay.jpg 截圖，請先上傳圖片！")
        return

    print("正在啟動雲端 AI 辨識...")
    payload = {'apikey': 'helloworld', 'language': 'cht'}
    
    with open(img_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, data=payload, files=files)
        
    result = response.json()
    
    if result.get('OCRExitCode') == 1:
        text = result['ParsedResults'][0]['ParsedText']
        lines = text.split('\r\n')
        
        names = []
        scores = []
        for line in lines:
            line = line.strip()
            if not line or "家族" in line or "成員" in line:
                continue
            if line.isdigit():
                scores.append(line)
            else:
                names.append(line)
                
        # 寫入 CSV 紀錄表
        csv_path = "家族貢獻總表.csv"
        file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', encoding='utf-8-sig') as f:
            if not file_exists:
                f.write("日期,族友暱稱,今日活躍值\n")
            
            min_len = min(len(names), len(scores))
            today_str = datetime.now().strftime("%Y-%m-%d")
            for i in range(min_len):
                f.write(f"{today_str},{names[i]},{scores[i]}\n")
        print("數據已成功登記到 家族貢獻總表.csv！")
    else:
        print("辨識失敗：", result.get('ErrorMessage'))

if __name__ == "__main__":
    do_ocr()
