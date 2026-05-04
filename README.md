# YOLO2 物品偵測系統 - 使用指南

## 📋 概述

這是一個基於 YOLO 的物品偵測系統，專門用於識別和追蹤零食/飲品產品，並提取其名稱和價格資訊。

### ✨ 功能特性

- ✅ 實時攝影機偵測
- ✅ 影片檔案分析  
- ✅ 單張圖片偵測
- ✅ 自動生成標註結果
- ✅ JSON 格式結果匯出
- ✅ 支持自訂物品價格表
- ✅ 信心度可調整

---

## 🚀 快速開始

### 方法 1：互動模式（推薦新手）

```bash
python quickstart.py
```

選擇推論模式：
1. **圖片偵測** - 偵測單張圖片
2. **影片偵測** - 分析影片文件
3. **攝影機即時** - 開啟攝影機即時偵測

### 方法 2：命令列模式（進階用戶）

```bash
# 偵測圖片
python detect.py image.jpg

# 偵測影片
python detect.py video.mp4

# 開啟攝影機
python detect.py camera
```

### 方法 3：測試模型

驗證模型是否正常運作：

```bash
python test_model.py
```

---

## 🏷️ 偵測對象

模型可以識別以下 **8 種產品**：

| 編號 | 產品名稱 | 預設價格 |
|------|---------|---------|
| 0 | Chocolate | $2.50 |
| 1 | Karamucho | $1.50 |
| 2 | Koala | $3.00 |
| 3 | Lays | $2.00 |
| 4 | Pepero | $1.80 |
| 5 | Pringles | $3.50 |
| 6 | Puff | $1.20 |
| 7 | WaferPies | $2.20 |

---

## ⚙️ 配置說明

編輯 `config.json` 來自訂您的設定：

### 基本設定

```json
{
  "model": "bestn.pt",              // 模型路徑
  "confidence_threshold": 0.5       // 信心度閾值 (0-1)
}
```

### 物品價格設定

修改 `price_map` 來更新價格：

```json
{
  "price_map": {
    "Chocolate": 2.5,
    "Lays": 2.0,
    ...
  }
}
```

### 攝影機設定

```json
{
  "camera": {
    "device_id": 0,          // 攝影機編號
    "duration_seconds": 30   // 運行時長
  }
}
```

---

## 📊 輸出結果

### JSON 格式範例

```json
[
  {
    "frame": null,
    "class_id": 3,
    "name": "Lays",
    "confidence": 0.95,
    "price": 2.0,
    "bbox": {
      "x1": 120,
      "y1": 150,
      "x2": 420,
      "y2": 380,
      "width": 300,
      "height": 230
    }
  }
]
```

### 輸出檔案

- `result_YYYYMMDD_HHMMSS.jpg` - 標註後的圖片
- `output_video.mp4` - 標註後的影片
- `detections.json` - 偵測結果 JSON

---

## 🎯 使用範例

### 範例 1：偵測圖片並保存結果

```python
from detect import ProductDetector

# 初始化
detector = ProductDetector("bestn.pt", conf_threshold=0.5)

# 偵測
detections = detector.detect_image("product_image.jpg", save_result=True)

# 輸出結果
for det in detections:
    print(f"{det['name']}: 信心度={det['confidence']}, 價格=${det['price']}")

# 匯出 JSON
detector.export_results(detections, "results.json")
```

### 範例 2：設定自訂價格表

```python
detector = ProductDetector("bestn.pt")

# 設定自訂價格
custom_prices = {
    "Chocolate": 3.0,
    "Lays": 2.5,
    "Pringles": 4.0
}
detector.set_price_map(custom_prices)

detections = detector.detect_image("image.jpg")
```

### 範例 3：攝影機即時偵測

```python
detector = ProductDetector("bestn.pt")

# 執行 30 秒的實時偵測
detections = detector.detect_camera(camera_id=0, duration_seconds=30)

# 統計結果
from collections import Counter
products = Counter(d['name'] for d in detections)
print(f"偵測結果: {dict(products)}")
```

---

## 🔧 進階技巧

### 1. 調整信心度

```bash
# 更嚴格的檢測（只保留高信心度）
python detect.py image.jpg --conf 0.8

# 更寬鬆的檢測（包含低信心度）
python detect.py image.jpg --conf 0.3
```

### 2. 批量處理資料夾

```python
from pathlib import Path
from detect import ProductDetector

detector = ProductDetector("bestn.pt")

# 處理資料夾中的所有圖片
image_folder = Path("images/")
all_detections = []

for image_path in image_folder.glob("*.jpg"):
    detections = detector.detect_image(str(image_path))
    all_detections.extend(detections)

detector.export_results(all_detections, "batch_results.json")
```

### 3. 計算總銷售金額

```python
from collections import Counter
from detect import ProductDetector

detector = ProductDetector("bestn.pt")
detector.set_price_map({
    "Chocolate": 2.5,
    "Lays": 2.0,
    "Pringles": 3.5,
    # ... 其他產品
})

detections = detector.detect_video("sales_video.mp4")

# 統計售出產品和金額
products = Counter(d['name'] for d in detections)
total_revenue = sum(d['price'] for d in detections if d['price'])

print(f"售出產品: {dict(products)}")
print(f"總收入: ${total_revenue:.2f}")
```

---

## 📁 檔案結構

```
c:\Users\USER\Desktop\name\
├── bestn.pt              # YOLO 模型檔案
├── detect.py             # 核心偵測模組
├── quickstart.py         # 互動式快速開始
├── test_model.py         # 模型測試工具
├── config.json           # 配置檔案
├── README.md             # 本檔案
└── results/              # 輸出結果目錄（自動創建）
```

---

## ⚠️ 常見問題

### Q1: 「找不到模型檔案」

**解決方法：** 確保 `bestn.pt` 在當前工作目錄中

```bash
# 檢查當前目錄
dir bestn.pt

# 或從 Python 檢查
python test_model.py
```

### Q2: 攝影機無法啟動

**解決方法：** 檢查攝影機編號

```python
import cv2

# 測試可用的攝影機
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"攝影機 {i} 可用")
        cap.release()
```

### Q3: 偵測結果為空

**解決方法：** 降低信心度閾值

```json
{
  "confidence_threshold": 0.3
}
```

### Q4: 處理速度太慢

**解決方法：** 使用 GPU 或跳幀

```python
# 影片處理時跳幀
detections = detector.detect_video(
    "video.mp4",
    skip_frames=5  # 每 5 幀處理一次
)
```

---

## 🔗 相關資源

- **Ultralytics YOLO 官方文檔**: https://docs.ultralytics.com/
- **YOLO GitHub**: https://github.com/ultralytics/ultralytics
- **OpenCV 文檔**: https://docs.opencv.org/

---

## 📝 版本信息

- **YOLO 版本**: YOLOv8/26
- **Python 版本**: 3.8+
- **主要依賴**: ultralytics, opencv-python, numpy

---

## 💡 需要幫助？

1. 執行 `python test_model.py` 驗證環境
2. 檢查 `config.json` 的配置是否正確
3. 查看輸出的 JSON 檔案瞭解偵測結果
4. 在命令行添加 `-v` 參數來查看詳細日誌

---

**祝您使用愉快！🎉**
