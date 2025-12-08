"""
SSVEP车辆控制主程序
整合EEG读取、SSVEP分类、数据融合和车辆控制模块
"""
import argparse
import time
import sys
from eeg_reader import EEGReader
from ssvep_classifier import SSVEPClassifier
from car_controller import CarController
from data_fusion import DataFusion


# ========== 默认配置参数 ==========
DEFAULT_CONFIG = {
    # LSL设置
    "stream_name": "Cygnus-083704-RawEEG",
    "sample_rate": 1000,
    "buffer_size": 3000,  # 3秒 @ 1000Hz
    
    # SSVEP频率设置
    "frequencies": [6.0, 7.5, 8.57, 10.0],
    "frequency_labels": ["forward", "left", "right", "backward"],
    "cca_threshold": 0.3,
    "harmonics": 2,
    
    # 车辆控制设置
    "serial_port": None,  # 需要用户指定
    "baudrate": 9600,
    
    # 实时控制设置
    "update_interval": 0.2,  # 更新间隔（秒）
    "debounce_time": 0.0,  # 防抖时间（秒），0表示不使用防抖
    "buffer_wait_time": 2.0,  # 等待缓冲区填充的时间（秒）
}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SSVEP Car Control System")
    parser.add_argument("port", type=str, help="Serial port for car (e.g., COM3)")
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
    
    # ========== 初始化模块 ==========
    print("=" * 50)
    print("SSVEP Car Control System")
    print("=" * 50)
    
    # 1. 初始化EEG读取器
    print("\n[1/4] Initializing EEG Reader...")
    eeg_reader = EEGReader(
        sample_rate=DEFAULT_CONFIG["sample_rate"],
        buffer_size=DEFAULT_CONFIG["buffer_size"],
        channel_indices=[4, 5],  # 与lsl_mind_controll_car.py相同
        stream_name=args.stream_name
    )
    eeg_reader.setup_lsl_inlet()
    eeg_reader.start_reading()
    
    # 2. 初始化SSVEP分类器
    print("\n[2/4] Initializing SSVEP Classifier...")
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
    
    # 3. 初始化数据融合器
    print("\n[3/4] Initializing Data Fusion Module...")
    data_fusion = DataFusion()
    
    # 4. 初始化车辆控制器
    print("\n[4/4] Initializing Car Controller...")
    car_controller = CarController(
        port=args.port,
        baudrate=DEFAULT_CONFIG["baudrate"]
    )
    if not car_controller.connect():
        print("Failed to connect to car. Exiting...")
        eeg_reader.stop_reading()
        sys.exit(1)
    
    # ========== 等待缓冲区填充 ==========
    print(f"\nBuffering EEG data (waiting {args.buffer_wait} seconds)...")
    time.sleep(args.buffer_wait)
    
    # 检查缓冲区是否准备好
    while not eeg_reader.is_buffer_ready():
        print("Waiting for EEG buffer to be ready...")
        time.sleep(0.1)
    
    # ========== 主控制循环 ==========
    print("\n" + "=" * 50)
    print("Starting SSVEP detection and car control...")
    print("Press Ctrl+C to stop")
    print("=" * 50 + "\n")
    
    last_action = "stop"
    last_action_time = time.time()
    
    try:
        while True:
            # 1. 读取EEG数据
            eeg_data = eeg_reader.get_buffer()
            
            # 2. 数据融合（当前仅传递EEG数据）
            fused_data = data_fusion.fuse(eeg_data)
            
            # 3. SSVEP分类
            action, scores = ssvep_classifier.classify_with_scores(fused_data)
            
            # 4. 防抖处理
            current_time = time.time()
            if args.debounce > 0:
                # 如果动作改变，检查是否超过防抖时间
                if action != last_action:
                    if current_time - last_action_time < args.debounce:
                        # 未超过防抖时间，保持上一个动作
                        action = last_action
                    else:
                        # 超过防抖时间，更新动作
                        last_action = action
                        last_action_time = current_time
                else:
                    last_action_time = current_time
            else:
                last_action = action
            
            # 5. 发送指令到车辆
            car_controller.send_action(action)
            
            # 6. 显示状态
            score_str = ", ".join([f"{k}:{v:.3f}" for k, v in scores.items()])
            print(f"\rAction: {action:8s} | Scores: [{score_str}]", end="", flush=True)
            
            # 7. 等待下一次更新
            time.sleep(args.update_interval)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
    
    finally:
        # 清理资源
        print("Stopping car...")
        car_controller.send_action("stop")
        time.sleep(0.5)
        
        print("Disconnecting...")
        car_controller.disconnect()
        eeg_reader.stop_reading()
        
        print("Exited successfully.")


if __name__ == "__main__":
    main()

