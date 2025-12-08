"""
EEG读取模块
负责从LSL流中读取EEG数据并维护缓冲区
返回numpy array格式的数据
"""
from pylsl import StreamInlet, resolve_streams
import numpy as np
import threading
import time


class EEGReader:
    """EEG数据读取器"""
    
    def __init__(self, sample_rate=1000, buffer_size=3000, channel_indices=[4, 5], stream_name="Cygnus-083704-RawEEG"):
        """
        初始化EEG读取器
        
        Args:
            sample_rate: 采样率 (Hz)
            buffer_size: 缓冲区大小（样本数），3秒 = 3000 samples @ 1000Hz
            channel_indices: 要使用的通道索引列表，默认[4,5]对应channel 4-6（Python索引从0开始）
            stream_name: LSL流名称
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.channel_count = len(channel_indices)
        self.channel_indices = channel_indices
        self.stream_name = stream_name
        
        # 初始化缓冲区: shape = (channel_count, buffer_size)
        self.eeg_buffer = np.zeros((self.channel_count, self.buffer_size))
        self.buffer_lock = threading.Lock()
        
        # LSL相关
        self.inlet = None
        self.reading_thread = None
        self.is_reading = False
        
    def setup_lsl_inlet(self):
        """设置LSL输入流"""
        print("Resolving LSL streams...")
        streams = resolve_streams()
        
        if not streams:
            raise RuntimeError("No LSL streams found!")
        
        # 列出所有可用的流
        for i, s in enumerate(streams):
            print(f"[{i}] {s.name()} - type: {s.type()}")
        
        # 尝试找到指定的流
        target_stream = None
        for s in streams:
            if s.name() == self.stream_name:
                target_stream = s
                break
        
        if target_stream is None:
            print(f"Warning: Stream '{self.stream_name}' not found. Using first available stream.")
            target_stream = streams[0]
        
        print(f"Connecting to {target_stream.name()}...")
        self.inlet = StreamInlet(target_stream)
        return self.inlet
    
    def _read_eeg_thread(self):
        """后台线程：持续读取EEG数据并更新缓冲区"""
        while self.is_reading:
            try:
                sample, timestamp = self.inlet.pull_sample()
                if sample:
                    # 提取指定的通道数据
                    selected_data = [sample[i] for i in self.channel_indices]
                    sample_np = np.array(selected_data).reshape(-1, 1)
                    
                    # 更新缓冲区（滚动缓冲区）
                    with self.buffer_lock:
                        self.eeg_buffer[:, :-1] = self.eeg_buffer[:, 1:]
                        self.eeg_buffer[:, -1] = sample_np.flatten()
            except Exception as e:
                print(f"Error reading EEG sample: {e}")
                time.sleep(0.01)
    
    def start_reading(self):
        """开始读取EEG数据"""
        if self.inlet is None:
            self.setup_lsl_inlet()
        
        self.is_reading = True
        self.reading_thread = threading.Thread(target=self._read_eeg_thread, daemon=True)
        self.reading_thread.start()
        print("EEG reading thread started.")
    
    def stop_reading(self):
        """停止读取EEG数据"""
        self.is_reading = False
        if self.reading_thread:
            self.reading_thread.join(timeout=1.0)
        print("EEG reading stopped.")
    
    def get_buffer(self):
        """
        获取当前EEG缓冲区数据
        
        Returns:
            numpy.ndarray: shape = (channel_count, buffer_size) 的EEG数据
        """
        with self.buffer_lock:
            return self.eeg_buffer.copy()
    
    def is_buffer_ready(self):
        """
        检查缓冲区是否已准备好（是否有有效数据）
        
        Returns:
            bool: 如果缓冲区有有效数据返回True
        """
        with self.buffer_lock:
            # 检查第一个值是否非零（简单检查是否有数据）
            return np.abs(self.eeg_buffer[0, 0]) > 1e-6

