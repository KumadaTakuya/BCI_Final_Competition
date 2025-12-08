"""
SSVEP車輛控制主程式 / SSVEP Car Control Main Program
整合EEG讀取、SSVEP分類和車輛控制模組 / Integrates EEG reading, SSVEP classification and car control modules
支援多種輸入模式：EEG或鍵盤控制 / Supports multiple input modes: EEG or keyboard control
"""
import argparse
import time
import sys
import os
import threading

# 添加utils目錄到路徑 / Add utils directory to path
utils_path = os.path.join(os.path.dirname(__file__), 'utils')
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)
from eeg_reader import EEGReader
from keyboard_reader import KeyboardReader
from ssvep_classifier import SSVEPClassifier
from car_controller import CarController
from ssvep_stimulus import SSVEPStimulus


# ========== 預設配置參數 / Default Configuration Parameters ==========
DEFAULT_CONFIG = {
    # LSL設置 / LSL Settings
    "stream_name": "Cygnus-083704-RawEEG",
    "sample_rate": 1000,
    "buffer_size": 3000,  # 3秒 @ 1000Hz / 3 seconds @ 1000Hz
    
    # SSVEP頻率設置 / SSVEP Frequency Settings
    "frequencies": [6.0, 7.5, 8.57, 10.0],
    "frequency_labels": ["forward", "left", "right", "backward"],
    "cca_threshold": 0.3,
    "harmonics": 2,
    
    # 車輛控制設置 / Car Control Settings
    "serial_port": None,  # 需要使用者指定 / User must specify
    "baudrate": 9600,
    
    # 即時控制設置 / Real-time Control Settings
    "update_interval": 0.2,  # 更新間隔（秒） / Update interval (seconds)
    "debounce_time": 0.0,  # 防抖時間（秒），0表示不使用防抖 / Debounce time (seconds), 0 means no debouncing
    "buffer_wait_time": 2.0,  # 等待緩衝區填充的時間（秒） / Time to wait for buffer to fill (seconds)
}


def main():
    """主函數 / Main Function"""
    parser = argparse.ArgumentParser(description="SSVEP Car Control System")
    parser.add_argument("port", type=str, help="Serial port for car (e.g., COM3)")
    parser.add_argument("--input-mode", type=str, choices=["eeg", "keyboard"], default="eeg",
                        help="Input mode: 'eeg' for SSVEP control, 'keyboard' for WASD keyboard control (default: eeg)")
    parser.add_argument("--stream-name", type=str, default=DEFAULT_CONFIG["stream_name"],
                        help=f"LSL stream name (default: {DEFAULT_CONFIG['stream_name']})")
    parser.add_argument("--threshold", type=float, default=DEFAULT_CONFIG["cca_threshold"],
                        help=f"CCA threshold (default: {DEFAULT_CONFIG['cca_threshold']})")
    parser.add_argument("--update-interval", type=float, default=DEFAULT_CONFIG["update_interval"],
                        help=f"Update interval in seconds (default: {DEFAULT_CONFIG['update_interval']})")
    parser.add_argument("--debounce", type=float, default=DEFAULT_CONFIG["debounce_time"],
                        help=f"Debounce time in seconds (default: {DEFAULT_CONFIG['debounce_time']})")
    parser.add_argument("--buffer-wait", type=float, default=DEFAULT_CONFIG["buffer_wait_time"],
                        help=f"Buffer wait time in seconds (default: {DEFAULT_CONFIG['buffer_wait_time']})")
    
    args = parser.parse_args()
    
    # ========== 初始化模組 / Initialize Modules ==========
    print("=" * 50)
    print("SSVEP Car Control System")
    print(f"Input Mode: {args.input_mode.upper()}")
    print("=" * 50)
    
    # 初始化輸入模組 / Initialize Input Module
    eeg_reader = None
    ssvep_classifier = None
    keyboard_reader = None
    ssvep_stimulus = None
    stimulus_thread = None
    
    if args.input_mode == "eeg":
        # 1. 初始化SSVEP視覺刺激窗口 / Initialize SSVEP Visual Stimulus Window
        print("\n[1/3] Initializing SSVEP Visual Stimulus Window...")
        # 將頻率標籤轉換為首字母大寫 / Convert frequency labels to title case
        stimulus_labels = [label.capitalize() for label in DEFAULT_CONFIG["frequency_labels"]]
        ssvep_stimulus = SSVEPStimulus(
            frequencies=DEFAULT_CONFIG["frequencies"],
            labels=stimulus_labels,
            window_size=(1200, 800),
            stimulus_size=200
        )
        # 在後台執行緒中運行視覺刺激窗口 / Run visual stimulus window in background thread
        stimulus_thread = threading.Thread(target=ssvep_stimulus.run, args=(120,), daemon=True)
        stimulus_thread.start()
        print("Visual stimulus window started.")
        
        # 2. 初始化EEG讀取器 / Initialize EEG Reader
        print("\n[2/3] Initializing EEG Reader...")
        eeg_reader = EEGReader(
            sample_rate=DEFAULT_CONFIG["sample_rate"],
            buffer_size=DEFAULT_CONFIG["buffer_size"],
            channel_indices=[4, 5],  # 與lsl_mind_controll_car.py相同 / Same as lsl_mind_controll_car.py
            stream_name=args.stream_name
        )
        eeg_reader.setup_lsl_inlet()
        eeg_reader.start_reading()
        
        # 3. 初始化SSVEP分類器 / Initialize SSVEP Classifier
        print("\n[3/3] Initializing SSVEP Classifier...")
        print(f"  Frequencies: {DEFAULT_CONFIG['frequencies']} Hz")
        print(f"  Labels: {DEFAULT_CONFIG['frequency_labels']}")
        print(f"  CCA Threshold: {args.threshold}")
        ssvep_classifier = SSVEPClassifier(
            sample_rate=DEFAULT_CONFIG["sample_rate"],
            buffer_size=DEFAULT_CONFIG["buffer_size"],
            frequencies=DEFAULT_CONFIG["frequencies"],
            frequency_labels=DEFAULT_CONFIG["frequency_labels"],
            threshold=args.threshold,
            harmonics=DEFAULT_CONFIG["harmonics"]
        )
    elif args.input_mode == "keyboard":  # keyboard mode
        # 1. 初始化鍵盤讀取器 / Initialize Keyboard Reader
        print("\n[1/1] Initializing Keyboard Reader...")
        keyboard_reader = KeyboardReader(update_interval=args.update_interval)
    else:
        print("Invalid input mode. Exiting...")
        sys.exit(1)

    # 初始化車輛控制器
    print("Initializing Car Controller...")
    car_controller = CarController(
        port=args.port,
        baudrate=DEFAULT_CONFIG["baudrate"]
    )
    if not car_controller.connect():
        print("Failed to connect to car. Exiting...")
        if eeg_reader:
            eeg_reader.stop_reading()
        sys.exit(1)
    print("Car Controller initialized successfully.")
    
    # ========== 根據輸入模式進行初始化 / Initialize based on input mode ==========
    try:
        if args.input_mode == "eeg":
            # 等待緩衝區填充 / Wait for Buffer to Fill
            print(f"\nBuffering EEG data (waiting {args.buffer_wait} seconds)...")
            time.sleep(args.buffer_wait)
            
            # 檢查緩衝區是否準備好 / Check if buffer is ready
            while not eeg_reader.is_buffer_ready():
                print("Waiting for EEG buffer to be ready...")
                time.sleep(0.1)
            
            # ========== 主控制迴圈（EEG模式） / Main Control Loop (EEG Mode) ==========
            print("\n" + "=" * 50)
            print("Starting SSVEP detection and car control...")
            print("Press Ctrl+C to stop")
            print("=" * 50 + "\n")
            
            last_action = "stop"
            last_action_time = time.time()
            
            # 時間段追蹤 / Time segment tracking
            detection_start_time = time.time()
            detection_count = 0
            log_interval = args.buffer_wait_time  # 每隔buffer_wait_time記錄一次 / Log every buffer_wait_time
            last_log_time = detection_start_time
            
            while True:
                # 1. 讀取EEG資料 / Read EEG data
                eeg_data = eeg_reader.get_buffer()
                
                # 2. SSVEP分類 / SSVEP classification
                current_detection_time = time.time()
                action, scores = ssvep_classifier.classify_with_scores(eeg_data)
                detection_count += 1
                
                # 3. 記錄詳細資訊（每隔log_interval秒） / Log detailed information (every log_interval seconds)
                time_since_last_log = current_detection_time - last_log_time
                if time_since_last_log >= log_interval:
                    # 計算時間段 / Calculate time segment
                    segment_start = last_log_time
                    segment_end = current_detection_time
                    segment_duration = segment_end - segment_start
                    total_elapsed = current_detection_time - detection_start_time
                    
                    print("\n" + "-" * 80)
                    print(f"檢測時間段 / Detection Time Segment #{detection_count}")
                    print(f"  開始時間 / Start Time: {segment_start:.3f} s")
                    print(f"  結束時間 / End Time: {segment_end:.3f} s")
                    print(f"  持續時間 / Duration: {segment_duration:.3f} s")
                    print(f"  總運行時間 / Total Elapsed: {total_elapsed:.3f} s")
                    print(f"\n各頻率CCA得分 / CCA Scores for Each Frequency:")
                    for freq, label in zip(DEFAULT_CONFIG["frequencies"], DEFAULT_CONFIG["frequency_labels"]):
                        score = scores.get(label, 0.0)
                        threshold_status = "✓ 超過閾值" if score > args.threshold else "✗ 未達閾值"
                        threshold_status_en = "✓ Exceeds" if score > args.threshold else "✗ Below"
                        print(f"  {freq:5.2f} Hz ({label:8s}): {score:6.4f} [{threshold_status} / {threshold_status_en}]")
                    print(f"\n檢測結果 / Detection Result: {action}")
                    print(f"閾值 / Threshold: {args.threshold}")
                    print("-" * 80)
                    
                    last_log_time = current_detection_time
                
                # 4. 防抖處理 / Debounce processing
                current_time = time.time()
                if args.debounce > 0:
                    # 如果動作改變，檢查是否超過防抖時間 / If action changed, check if debounce time exceeded
                    if action != last_action:
                        if current_time - last_action_time < args.debounce:
                            # 未超過防抖時間，保持上一個動作 / Debounce time not exceeded, keep previous action
                            action = last_action
                        else:
                            # 超過防抖時間，更新動作 / Debounce time exceeded, update action
                            last_action = action
                            last_action_time = current_time
                    else:
                        last_action_time = current_time
                else:
                    last_action = action
                
                # 5. 發送指令到車輛 / Send command to car
                car_controller.send_action(action)
                
                # 6. 顯示狀態 / Display status
                score_str = ", ".join([f"{k}:{v:.3f}" for k, v in scores.items()])
                print(f"\rAction: {action:8s} | Scores: [{score_str}] | Time: {current_time - detection_start_time:.1f}s", end="", flush=True)
                
                # 7. 等待下一次更新 / Wait for next update
                time.sleep(args.update_interval)
        
        elif args.input_mode == "keyboard":  # keyboard mode
            keyboard_reader.run_demo(car_controller)
        else:
            print("Invalid input mode. Exiting...")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        # 清理資源 / Cleanup resources
        if args.input_mode == "eeg":
            print("Stopping car...")
            car_controller.send_action("stop")
            time.sleep(0.5)
            
            # 關閉視覺刺激窗口 / Close visual stimulus window
            if ssvep_stimulus:
                print("Closing visual stimulus window...")
                ssvep_stimulus.running = False
                time.sleep(0.5)  # 等待窗口關閉 / Wait for window to close
            
            print("Disconnecting...")
            car_controller.disconnect()
            if eeg_reader:
                eeg_reader.stop_reading()
        elif args.input_mode == "keyboard":
            # 鍵盤模式已在run_demo中處理清理 / Keyboard mode cleanup handled in run_demo
            if keyboard_reader:
                keyboard_reader.stop()
            car_controller.disconnect()
        
        print("Exited successfully.")


if __name__ == "__main__":
    main()

