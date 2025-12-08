"""
配置文件模板
复制此文件为 config.py 并根据需要修改参数
"""

# ========== LSL设置 ==========
LSL_CONFIG = {
    "stream_name": "Cygnus-083704-RawEEG",  # LSL流名称
    "sample_rate": 1000,  # 采样率 (Hz)
    "buffer_size": 3000,  # 缓冲区大小（样本数），3秒 @ 1000Hz
    "channel_indices": [4, 5],  # 使用的EEG通道索引
}

# ========== SSVEP频率设置 ==========
SSVEP_CONFIG = {
    # 目标频率 (Hz) 和对应的动作标签
    "frequencies": [6.0, 7.5, 8.57, 10.0],
    "frequency_labels": ["forward", "left", "right", "backward"],
    
    # CCA参数
    "cca_threshold": 0.3,  # CCA相关系数阈值
    "harmonics": 2,  # 使用的谐波数量（基频和二次谐波）
}

# ========== 车辆控制设置 ==========
CAR_CONFIG = {
    "baudrate": 9600,  # 波特率
    "timeout": 10,  # 读取超时（秒）
    "write_timeout": 10,  # 写入超时（秒）
}

# ========== 实时控制设置 ==========
CONTROL_CONFIG = {
    "update_interval": 0.2,  # 更新间隔（秒）
    "debounce_time": 0.0,  # 防抖时间（秒），0表示不使用防抖
    "buffer_wait_time": 2.0,  # 等待缓冲区填充的时间（秒）
}

# ========== 数据融合设置（未来扩展） ==========
FUSION_CONFIG = {
    "use_gyroscope": False,  # 是否使用陀螺仪
    "use_emg": False,  # 是否使用EMG
    # 未来可以添加更多融合参数
}

