"""
配置檔案範本 / Configuration File Template
複製此檔案為 config.py 並根據需要修改參數 / Copy this file as config.py and modify parameters as needed
"""

# ========== LSL設置 / LSL Settings ==========
LSL_CONFIG = {
    "stream_name": "Cygnus-083704-RawEEG",  # LSL流名稱 / LSL stream name
    "sample_rate": 1000,  # 採樣率 (Hz) / Sampling rate (Hz)
    "buffer_size": 3000,  # 緩衝區大小（樣本數），3秒 @ 1000Hz / Buffer size (number of samples), 3 seconds @ 1000Hz
    "channel_indices": [4, 5],  # 使用的EEG通道索引 / EEG channel indices to use
}

# ========== SSVEP頻率設置 / SSVEP Frequency Settings ==========
SSVEP_CONFIG = {
    # 目標頻率 (Hz) 和對應的動作標籤 / Target frequencies (Hz) and corresponding action labels
    "frequencies": [6.0, 7.5, 8.57, 10.0],
    "frequency_labels": ["forward", "left", "right", "backward"],
    
    # CCA參數 / CCA Parameters
    "cca_threshold": 0.3,  # CCA相關係數閾值 / CCA correlation coefficient threshold
    "harmonics": 2,  # 使用的諧波數量（基頻和二次諧波） / Number of harmonics used (fundamental and second harmonic)
}

# ========== 車輛控制設置 / Car Control Settings ==========
CAR_CONFIG = {
    "baudrate": 9600,  # 波特率 / Baud rate
    "timeout": 10,  # 讀取超時（秒） / Read timeout (seconds)
    "write_timeout": 10,  # 寫入超時（秒） / Write timeout (seconds)
}

# ========== 即時控制設置 / Real-time Control Settings ==========
CONTROL_CONFIG = {
    "update_interval": 0.2,  # 更新間隔（秒） / Update interval (seconds)
    "debounce_time": 0.0,  # 防抖時間（秒），0表示不使用防抖 / Debounce time (seconds), 0 means no debouncing
    "buffer_wait_time": 2.0,  # 等待緩衝區填充的時間（秒） / Time to wait for buffer to fill (seconds)
}

# ========== 資料融合設置（未來擴展） / Data Fusion Settings (Future Expansion) ==========
FUSION_CONFIG = {
    "use_gyroscope": False,  # 是否使用陀螺儀 / Whether to use gyroscope
    "use_emg": False,  # 是否使用EMG / Whether to use EMG
    # 未來可以添加更多融合參數 / Can add more fusion parameters in the future
}

