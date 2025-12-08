"""
SSVEP車輛控制系統使用範例 / SSVEP Car Control System Usage Examples
示範如何單獨使用各個模組 / Demonstrates how to use each module separately
"""
import numpy as np
import sys
import os

# 添加utils目錄到路徑 / Add utils directory to path
utils_path = os.path.join(os.path.dirname(__file__), 'utils')
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)
from eeg_reader import EEGReader
from ssvep_classifier import SSVEPClassifier
from car_controller import CarController
from data_fusion import DataFusion


def example_eeg_reader():
    """範例：如何使用EEG讀取器 / Example: How to use EEG Reader"""
    print("=== EEG Reader Example ===")
    
    # 建立EEG讀取器 / Create EEG Reader
    reader = EEGReader(
        sample_rate=1000,
        buffer_size=3000,
        channel_indices=[4, 5],
        stream_name="Cygnus-083704-RawEEG"
    )
    
    # 設置LSL流 / Setup LSL stream
    reader.setup_lsl_inlet()
    
    # 開始讀取 / Start reading
    reader.start_reading()
    
    # 等待一段時間 / Wait for some time
    import time
    time.sleep(2)
    
    # 獲取緩衝區資料 / Get buffer data
    eeg_data = reader.get_buffer()
    print(f"EEG data shape: {eeg_data.shape}")
    print(f"Buffer ready: {reader.is_buffer_ready()}")
    
    # 停止讀取 / Stop reading
    reader.stop_reading()


def example_ssvep_classifier():
    """範例：如何使用SSVEP分類器 / Example: How to use SSVEP Classifier"""
    print("\n=== SSVEP Classifier Example ===")
    
    # 建立分類器 / Create classifier
    classifier = SSVEPClassifier(
        sample_rate=1000,
        buffer_size=3000,
        frequencies=[6.0, 7.5, 8.57, 10.0],
        frequency_labels=["forward", "left", "right", "backward"],
        threshold=0.3
    )
    
    # 建立模擬EEG資料（實際使用中應該從EEG讀取器獲取） / Create simulated EEG data (should get from EEG reader in actual use)
    # 這裡生成一個包含6Hz訊號的模擬資料 / Generate simulated data containing 6Hz signal
    t = np.arange(3000) / 1000.0
    signal_6hz = np.sin(2 * np.pi * 6.0 * t)
    eeg_data = np.array([signal_6hz, signal_6hz * 0.8])  # 2個通道 / 2 channels
    
    # 分類 / Classify
    action = classifier.classify(eeg_data)
    print(f"Detected action: {action}")
    
    # 獲取詳細得分 / Get detailed scores
    action, scores = classifier.classify_with_scores(eeg_data)
    print(f"Action: {action}")
    print(f"Scores: {scores}")


def example_car_controller():
    """範例：如何使用車輛控制器 / Example: How to use Car Controller"""
    print("\n=== Car Controller Example ===")
    
    # 建立控制器（不實際連接） / Create controller (not actually connected)
    controller = CarController(port="COM3", baudrate=9600)
    
    # 顯示動作映射 / Display action mapping
    print("Action to command mapping:")
    for action, cmd in controller.ACTION_COMMANDS.items():
        print(f"  {action} -> {cmd}")
    
    # 注意：實際連接需要真實的串口 / Note: Actual connection requires real serial port
    # controller.connect()
    # controller.send_action("forward")
    # controller.disconnect()


def example_data_fusion():
    """範例：如何使用資料融合器 / Example: How to use Data Fusion"""
    print("\n=== Data Fusion Example ===")
    
    # 建立融合器 / Create fusion module
    fusion = DataFusion()
    
    # 建立模擬EEG資料 / Create simulated EEG data
    eeg_data = np.random.randn(2, 3000)
    
    # 融合資料（當前僅返回EEG資料） / Fuse data (currently only returns EEG data)
    fused_data = fusion.fuse(eeg_data)
    print(f"Input shape: {eeg_data.shape}")
    print(f"Fused shape: {fused_data.shape}")
    print("Note: Currently only passes through EEG data.")
    print("Future: Can add gyroscope and EMG data fusion.")


if __name__ == "__main__":
    print("SSVEP Car Control System - Module Examples")
    print("=" * 50)
    
    # 注意：這些範例中，只有EEG讀取器需要實際的LSL流 / Note: In these examples, only EEG reader needs actual LSL stream
    # 其他範例可以使用模擬資料 / Other examples can use simulated data
    
    # example_eeg_reader()  # 需要LSL流，取消註解以執行 / Requires LSL stream, uncomment to run
    example_ssvep_classifier()
    example_car_controller()
    example_data_fusion()
    
    print("\n" + "=" * 50)
    print("Examples completed!")

