# ==========================================================
# YOLO Tkinter 視覺化介面 (學生學習範例版)
# ==========================================================
# 說明：
# 這個程式展示了如何使用 Python 內建的 Tkinter 模組建立一個視窗應用程式，
# 並且結合 YOLO 模型，讓使用者可以透過按鈕來偵測圖片或開啟攝影機。
# 同時它會將 detect.py (現有模型) 的輸出呈現在畫面上計算總價。
# ==========================================================

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import cv2  # OpenCV：用來讀取圖片與攝影機視訊
from PIL import Image, ImageTk  # Pillow：用來將 OpenCV 的圖轉換給 Tkinter 顯示
import json
from pathlib import Path
from datetime import datetime
from ultralytics import YOLO

# ==========================================================
# ProductDetector 類別（整合自 detect.py）
# ==========================================================
class ProductDetector:
    """物品偵測與解析"""
    
    def __init__(self, model_path="bestn.pt", conf_threshold=0.5):
        """
        初始化檢測器
        
        Args:
            model_path: YOLO 模型路徑
            conf_threshold: 信心度閾值 (0-1)
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        
        # 物品名稱對應表 (可根據需要自訂)
        self.class_names = {}
        
        # 物品價格對應表 (需根據實際情況填入)
        self.price_map = {}
        
    def detect_image(self, image_path, save_result=True):
        """
        偵測單張圖片
        
        Args:
            image_path: 圖片路徑
            save_result: 是否保存標註結果
            
        Returns:
            List[dict]: 偵測結果
        """
        print(f"[IMAGE] Detecting: {image_path}")
        
        # 執行推論
        results = self.model.predict(
            source=image_path,
            conf=self.conf_threshold,
            verbose=False
        )
        
        # 解析結果
        detections = self._parse_results(results[0])
        
        # 保存標註圖片
        if save_result:
            output_path = f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            annotated_frame = results[0].plot()
            cv2.imwrite(output_path, annotated_frame)
            print(f"✅ 標註結果已保存: {output_path}")
        
        return detections
    
    def detect_video(self, video_path, output_path=None, skip_frames=1):
        """
        偵測影片
        
        Args:
            video_path: 影片路徑
            output_path: 輸出影片路徑
            skip_frames: 跳幀間隔 (加快處理)
        """
        print(f"🎬 正在處理影片: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 視頻寫入器
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        all_detections = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # 跳幀處理
            if frame_count % skip_frames != 0:
                continue
            
            # 推論
            results = self.model.predict(
                source=frame,
                conf=self.conf_threshold,
                verbose=False
            )
            
            # 解析結果
            detections = self._parse_results(results[0], frame_number=frame_count)
            all_detections.extend(detections)
            
            # 繪製標註
            annotated_frame = results[0].plot()
            
            # 寫出影片
            if output_path:
                out.write(annotated_frame)
            
            # 顯示進度
            if frame_count % (fps * 5) == 0:  # 每5秒打印一次
                print(f"⏳ 已處理 {frame_count} 幀...")
        
        cap.release()
        if output_path:
            out.release()
            print(f"✅ 輸出影片已保存: {output_path}")
        
        return all_detections
    
    def detect_camera(self, camera_id=0, duration_seconds=30):
        """
        即時攝影機偵測
        
        Args:
            camera_id: 攝影機編號
            duration_seconds: 執行時長
        """
        print(f"📷 啟動攝影機 #{camera_id}，持續 {duration_seconds} 秒...")
        print("   按 'Q' 退出、'S' 截圖")
        
        cap = cv2.VideoCapture(camera_id)
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        total_frames = fps * duration_seconds
        frame_count = 0
        
        all_detections = []
        screenshot_count = 0
        
        while frame_count < total_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # 推論
            results = self.model.predict(
                source=frame,
                conf=self.conf_threshold,
                verbose=False
            )
            
            # 解析結果
            detections = self._parse_results(results[0])
            all_detections.extend(detections)
            
            # 繪製標註
            annotated_frame = results[0].plot()
            
            # 顯示信息
            cv2.putText(
                annotated_frame,
                f"FPS: {fps:.1f} | Objects: {len(detections)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            # 顯示偵測物品
            y_offset = 60
            for det in detections:
                text = f"{det['name']} (信心度: {det['confidence']:.2f})"
                cv2.putText(
                    annotated_frame,
                    text,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    1
                )
                y_offset += 25
            
            # 顯示
            cv2.imshow("YOLO 物品偵測", annotated_frame)
            
            # 鍵盤控制
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                screenshot_count += 1
                screenshot_path = f"screenshot_{screenshot_count}.jpg"
                cv2.imwrite(screenshot_path, annotated_frame)
                print(f"📷 截圖已保存: {screenshot_path}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        return all_detections
    
    def _parse_results(self, result, frame_number=None):
        """
        解析 YOLO 推論結果
        
        Returns:
            List[dict]: 偵測物品清單
        """
        detections = []
        
        if result.boxes is None:
            return detections
        
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            
            # 獲取邊界框座標
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # 物品名稱 (預設為類別ID)
            class_name = self.class_names.get(
                class_id,
                self.model.names.get(class_id, f"Class_{class_id}")
            )
            
            # 物品價格 (根據物品名稱查詢)
            price = self.price_map.get(class_name, None)
            
            detection = {
                "frame": frame_number,
                "class_id": class_id,
                "name": class_name,
                "confidence": round(confidence, 3),
                "price": price,
                "bbox": {
                    "x1": x1, "y1": y1,
                    "x2": x2, "y2": y2,
                    "width": x2 - x1,
                    "height": y2 - y1
                }
            }
            
            detections.append(detection)
        
        return detections
    
    def export_results(self, detections, output_file="detections.json"):
        """匯出偵測結果為 JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detections, f, ensure_ascii=False, indent=2)
        print(f"📊 結果已匯出: {output_file}")
    
    def set_price_map(self, price_dict):
        """
        設定物品價格對應表
        
        Args:
            price_dict: {物品名稱: 價格}
        """
        self.price_map = price_dict
        print(f"✅ 已載入 {len(price_dict)} 個物品的價格資訊")


# ==========================================================
# YOLO Tkinter 視覺化介面

class YoloTkinterApp:
    def __init__(self, root):
        """
        初始化應用程式主要的視窗與變數
        """
        self.root = root
        self.root.title("楠梓高中商店物件偵測與結帳系統")
        self.root.geometry("1000x700")  # 設定視窗寬高
        self.root.configure(bg="#F0F0F0") # 背景顏色

        # ==========================================
        # 1. 載入模型與變數初始化
        # ==========================================
        try:
            # 先讀取 config.json 的所有設定
            config = {}
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                print(f"⚠️  無法讀取 config.json: {e}，使用預設值")
            
            # 從 config.json 或使用預設值
            model_path = config.get("model", "bestn.pt")
            conf_threshold = config.get("confidence_threshold", 0.5)
            
            # 建立 YOLO 模型偵測器，使用 config.json 中的模型路徑
            self.detector = ProductDetector(model_path=model_path, conf_threshold=conf_threshold)
            
            # 載入設定檔中自訂的價錢對應表與類別名稱
            if "price_map" in config:
                self.detector.set_price_map(config["price_map"])
            if "class_names" in config:
                # 配合原有設定填入名稱
                self.detector.class_names = {int(k): v for k, v in config["class_names"].items()}
        except Exception as e:
            messagebox.showerror("錯誤", f"載入模型或設定時發生錯誤:\n{e}")
            self.detector = None

        self.cap = None             # 攝影機物件
        self.video_running = False  # 攝影機是否運行中
        self.total_price = 0.0      # 目前總價

        # 設定介面排版
        self.setup_ui()

        # 延遲 500 毫秒後自動啟動攝影機
        # 使用 after() 是為了讓視窗先完成繪製，避免畫面還沒出來就開始擷取影像
        self.root.after(500, self.toggle_camera)

    def setup_ui(self):
        """
        設定畫面的佈局 (左側顯示影像，右側顯示清單與按鈕)
        """
        # --- 左側：影像顯示區塊 ---
        self.frame_left = tk.Frame(self.root, bg="black", width=640, height=480)
        self.frame_left.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 顯示影像用的 Label
        self.lbl_video = tk.Label(self.frame_left, text="等待影像載入...", fg="white", bg="black", font=("msjh.ttc", 16))
        self.lbl_video.pack(expand=True, fill=tk.BOTH)

        # --- 右側：控制與結帳區塊 ---
        self.frame_right = tk.Frame(self.root, width=300)
        self.frame_right.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)

        # 學校 Logo 圖片
        # 使用 Path 取得程式所在目錄，確保圖片路徑正確
        from pathlib import Path
        logo_path = Path(__file__).parent / "nths_s.png"
        try:
            # 載入圖片並調整大小 (等比例縮放)
            logo_img = Image.open(logo_path)
            logo_img.thumbnail((120, 120))  # 限制最大寬高為 120px
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            lbl_logo = tk.Label(self.frame_right, image=self.logo_photo)
            lbl_logo.pack(pady=(10, 5))
        except Exception as e:
            print(f"無法載入 Logo 圖片: {e}")

        # 按鈕區
        lbl_title = tk.Label(self.frame_right, text="楠梓高中AI商店結帳系統", font=("msjh.ttc", 16, "bold"))
        lbl_title.pack(pady=(5, 0))

        # 副標題：專題
        lbl_subtitle = tk.Label(self.frame_right, text="數理實驗班專題", font=("msjh.ttc", 12))
        lbl_subtitle.pack(pady=(0, 10))

        # 按鈕：選擇圖片
        btn_image = tk.Button(self.frame_right, text="📁 載入圖片並偵測", font=("msjh.ttc", 12), command=self.load_image_and_detect)
        btn_image.pack(fill=tk.X, pady=5)

        # 按鈕：啟動攝影機
        self.btn_camera = tk.Button(self.frame_right, text="📷 啟動攝影機", font=("msjh.ttc", 12), command=self.toggle_camera)
        self.btn_camera.pack(fill=tk.X, pady=5)

        # 商品清單標題
        lbl_list_title = tk.Label(self.frame_right, text="🛒 偵測商品清單", font=("msjh.ttc", 14, "bold"))
        lbl_list_title.pack(pady=(20, 5))

        # 建立 Treeview 來呈現表格 (包含名稱 / 信心度 / 價錢)
        columns = ("name", "conf", "price")
        # height=15 代表可以顯示 15 行
        self.tree = ttk.Treeview(self.frame_right, columns=columns, show="headings", height=15)
        self.tree.heading("name", text="物品名稱")
        self.tree.heading("conf", text="信心度")
        self.tree.heading("price", text="價錢")
        
        self.tree.column("name", width=120, anchor="center")
        self.tree.column("conf", width=60, anchor="center")
        self.tree.column("price", width=80, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- 結帳區 (右側底部) ---
        self.lbl_total = tk.Label(self.frame_right, text="總計: $0.0", font=("msjh.ttc", 18, "bold"), fg="#D32F2F")
        self.lbl_total.pack(pady=20, side=tk.BOTTOM)

    # ==========================================
    # 2. 圖片偵測邏輯
    # ==========================================
    def load_image_and_detect(self):
        """
        處理載入圖片並執行 YOLO 偵測的動作
        """
        if self.detector is None:
            messagebox.showwarning("警告", "模型尚未載入完成！")
            return

        # 若攝影機正在拍攝，則先自動停止
        if self.video_running:
            self.toggle_camera()

        # 開啟系統檔案對話框，挑選圖片
        file_path = filedialog.askopenfilename(
            title="選擇要偵測的圖片",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )
        # 如果使用者點了取消，則直接離開函式
        if not file_path:
            return

        try:
            # 清空先前的表單與金額資料
            self.clear_list()

            # 使用 OpenCV 讀取圖片，準備做推論
            frame = cv2.imread(file_path)
            if frame is None:
                messagebox.showerror("錯誤", "無法讀取該圖片，可能路徑包含無法解析的字元。")
                return

            # 交給共用的推論函式更新畫面
            self.process_frame_and_update(frame)

        except Exception as e:
            messagebox.showerror("發生錯誤", f"偵測發生異常:\n{str(e)}")

    # ==========================================
    # 3. 攝影機偵測邏輯
    # ==========================================
    def toggle_camera(self):
        """
        切換攝影機為開啟或關閉的狀態
        """
        if not self.video_running:
            # 嘗試開啟攝影機設備 (0 代表預設的第一顆鏡頭)
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                messagebox.showerror("錯誤", "無法開啟攝影機！請檢查是否被其他程式佔用。")
                return
            
            self.video_running = True
            self.btn_camera.config(text="🛑 停止攝影機") # 改變按鈕字樣
            self.clear_list()
            # 呼叫更新迴圈函式來不斷擷取畫面
            self.update_camera_frame()
        else:
            # 停止攝影機
            self.video_running = False
            self.btn_camera.config(text="📷 啟動攝影機")
            if self.cap:
                self.cap.release()
                self.cap = None

    def update_camera_frame(self):
        """
        不斷擷取攝影機畫面的迴圈函式 (利用 Tkinter 的 after 達成非同步更新)
        這是避免 Tkinter 畫面 "當機" 凍結的重要技巧！
        """
        # 如果使用者按下停止攝影機，就終止迴圈
        if not self.video_running:
            return

        # 讀取一幀畫面
        ret, frame = self.cap.read()
        if ret:
            # 水平翻轉畫面 (左右鏡像)，參數 1 代表沿 Y 軸翻轉
            frame = cv2.flip(frame, 1)
            self.clear_list() # 在顯示新的一幀前，清空清單
            self.process_frame_and_update(frame)

        # "after" 的意思是：在 30 毫秒後，呼叫自己一次 (約為 30 FPS)
        self.root.after(30, self.update_camera_frame)

    # ==========================================
    # 4. 共用的推論與介面更新模組
    # ==========================================
    def process_frame_and_update(self, frame):
        """
        將影像傳入 YOLO 進行偵測，繪製標註框並更新到 Tkinter 的畫布上
        """
        if self.detector is None:
            return

        # 1. 直接套用 detector 物件內部的 model 來進行推論
        # source=frame 代表輸入 OpenCV 的影像陣列
        results = self.detector.model.predict(source=frame, conf=self.detector.conf_threshold, verbose=False)
        
        # 2. 取出 YOLO 畫好邊界框 (Bounding Box) 的影像
        annotated_frame = results[0].plot()

        # 3. 解析結果 (取得商品名稱、信心度、物件座標等)
        detections = self.detector._parse_results(results[0])

        # 4. 將解析出的資訊更新至右方表格與結帳區
        self.update_list(detections)

        # 5. 將影像轉換為 Tkinter 支援的格式
        # OpenCV 預設色彩通道為 BGR，而 PIL/Tkinter 需要 RGB，因此必須轉換
        rgb_image = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_image)

        # 針對畫布大小調整圖片 (等比例縮放)，避免畫面過大超出視窗
        display_width, display_height = 640, 480
        pil_img.thumbnail((display_width, display_height))

        # 轉換為 PhotoImage 給 Label 使用
        imgtk = ImageTk.PhotoImage(image=pil_img)
        
        # [非常重要!] 需將圖片綁定在 lbl_video 物件上，否則會被 Python 收垃圾機制清掉導致圖片一片白
        self.lbl_video.imgtk = imgtk  
        self.lbl_video.configure(image=imgtk, text="") # 設定圖片並隱藏預設文字

    def clear_list(self):
        """
        清空結帳清單與總金額
        """
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.total_price = 0.0
        self.lbl_total.config(text="總計: $0.0")

    def update_list(self, detections):
        """
        更新商品清單表格與總金額
        
        Args:
            detections (list): 包含許多字典的陣列，每個字典代表一個偵測到的商品
        """
        self.total_price = 0.0
        
        # 逐一處理偵測到的商品
        for det in detections:
            name = det.get("name", "Unknown")
            conf = f"{det.get('confidence', 0.0):.2f}"
            price = det.get("price")
            
            # 若無對應的價錢資料，就不加入總額計算
            if price is None:
                price_str = "未知"
                item_price = 0.0
            else:
                price_str = f"${price:.2f}"
                item_price = float(price)

            self.total_price += item_price

            # 加入至 Treeview UI 清單的最後方 (tk.END)
            self.tree.insert("", tk.END, values=(name, conf, price_str))
        
        # 將最終計算完成的金額更新於結帳標籤
        self.lbl_total.config(text=f"總計: ${self.total_price:.2f}")

# ==========================================
# 程式啟動點
# ==========================================
if __name__ == "__main__":
    # 初始化一個空的 Tk 視窗
    root = tk.Tk()
    
    # 建立我們的 YOLO 應用程式並將視窗傳給它
    app = YoloTkinterApp(root)
    
    # 設計當按下右上角 'X' 關閉時的防護機制 (安全地釋放攝影機)
    def on_closing():
        if app.video_running:
            app.toggle_camera()
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 開始持續監聽使用者按鈕與滑鼠事件
    root.mainloop()
