"""
YOLO 物品偵測與資訊提取
支援：圖片、影片、即時攝影機
"""

import cv2
from ultralytics import YOLO
import json
from pathlib import Path
from datetime import datetime


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


# ============ 使用範例 ============

if __name__ == "__main__":
    # 初始化檢測器
    detector = ProductDetector(model_path="bestn.pt", conf_threshold=0.5)
    
    # [選項1] 設定物品價格對應表
    # detector.set_price_map({
    #     "apple": 5.0,
    #     "banana": 3.0,
    #     "orange": 4.5,
    # })
    
    # [選項2] 設定自訂類別名稱 (如果模型使用自訂標籤)
    # detector.class_names = {
    #     0: "蘋果",
    #     1: "香蕉",
    #     2: "橙",
    # }
    
    print("=" * 50)
    print("YOLO 物品偵測系統")
    print("=" * 50)
    
    # 選擇推論來源
    import sys
    
    if len(sys.argv) > 1:
        source = sys.argv[1]
        
        if source.lower().startswith("camera"):
            # 攝影機模式
            detections = detector.detect_camera(
                camera_id=0,
                duration_seconds=30
            )
            detector.export_results(detections, "camera_detections.json")
            
        elif source.lower().endswith(('.mp4', '.avi', '.mov')):
            # 影片模式
            detections = detector.detect_video(
                video_path=source,
                output_path="output_video.mp4",
                skip_frames=1
            )
            detector.export_results(detections, "video_detections.json")
            
        else:
            # 圖片模式
            detections = detector.detect_image(image_path=source)
            detector.export_results(detections, "image_detections.json")
            print("\n📋 偵測結果:")
            for det in detections:
                print(f"  - {det['name']}: 信心度={det['confidence']}, 價格={det['price']}")
    else:
        print("\n使用方式:")
        print("  圖片:  python detect.py image.jpg")
        print("  影片:  python detect.py video.mp4")
        print("  攝影機: python detect.py camera")
        print("\n若不提供參數，請編輯此檔案的 if __name__ 區段來自訂")
