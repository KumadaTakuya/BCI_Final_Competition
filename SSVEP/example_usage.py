"""
SSVEP车辆控制系统使用示例
演示如何单独使用各个模块
"""
import numpy as np
from eeg_reader import EEGReader
from ssvep_classifier import SSVEPClassifier
from car_controller import CarController
from data_fusion import DataFusion


def example_eeg_reader():
    """示例：如何使用EEG读取器"""
    print("=== EEG Reader Example ===")
    
    # 创建EEG读取器
    reader = EEGReader(
        sample_rate=1000,
        buffer_size=3000,
        channel_indices=[4, 5],
        stream_name="Cygnus-083704-RawEEG"
    )
    
    # 设置LSL流
    reader.setup_lsl_inlet()
    
    # 开始读取
    reader.start_reading()
    
    # 等待一段时间
    import time
    time.sleep(2)
    
    # 获取缓冲区数据
    eeg_data = reader.get_buffer()
    print(f"EEG data shape: {eeg_data.shape}")
    print(f"Buffer ready: {reader.is_buffer_ready()}")
    
    # 停止读取
    reader.stop_reading()


def example_ssvep_classifier():
    """示例：如何使用SSVEP分类器"""
    print("\n=== SSVEP Classifier Example ===")
    
    # 创建分类器
    classifier = SSVEPClassifier(
        sample_rate=1000,
        buffer_size=3000,
        frequencies=[6.0, 7.5, 8.57, 10.0],
        frequency_labels=["forward", "left", "right", "backward"],
        threshold=0.3
    )
    
    # 创建模拟EEG数据（实际使用中应该从EEG读取器获取）
    # 这里生成一个包含6Hz信号的模拟数据
    t = np.arange(3000) / 1000.0
    signal_6hz = np.sin(2 * np.pi * 6.0 * t)
    eeg_data = np.array([signal_6hz, signal_6hz * 0.8])  # 2个通道
    
    # 分类
    action = classifier.classify(eeg_data)
    print(f"Detected action: {action}")
    
    # 获取详细得分
    action, scores = classifier.classify_with_scores(eeg_data)
    print(f"Action: {action}")
    print(f"Scores: {scores}")


def example_car_controller():
    """示例：如何使用车辆控制器"""
    print("\n=== Car Controller Example ===")
    
    # 创建控制器（不实际连接）
    controller = CarController(port="COM3", baudrate=9600)
    
    # 显示动作映射
    print("Action to command mapping:")
    for action, cmd in controller.ACTION_COMMANDS.items():
        print(f"  {action} -> {cmd}")
    
    # 注意：实际连接需要真实的串口
    # controller.connect()
    # controller.send_action("forward")
    # controller.disconnect()


def example_data_fusion():
    """示例：如何使用数据融合器"""
    print("\n=== Data Fusion Example ===")
    
    # 创建融合器
    fusion = DataFusion()
    
    # 创建模拟EEG数据
    eeg_data = np.random.randn(2, 3000)
    
    # 融合数据（当前仅返回EEG数据）
    fused_data = fusion.fuse(eeg_data)
    print(f"Input shape: {eeg_data.shape}")
    print(f"Fused shape: {fused_data.shape}")
    print("Note: Currently only passes through EEG data.")
    print("Future: Can add gyroscope and EMG data fusion.")


if __name__ == "__main__":
    print("SSVEP Car Control System - Module Examples")
    print("=" * 50)
    
    # 注意：这些示例中，只有EEG读取器需要实际的LSL流
    # 其他示例可以使用模拟数据
    
    # example_eeg_reader()  # 需要LSL流，取消注释以运行
    example_ssvep_classifier()
    example_car_controller()
    example_data_fusion()
    
    print("\n" + "=" * 50)
    print("Examples completed!")

