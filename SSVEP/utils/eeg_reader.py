"""
EEG讀取模組 / EEG Reading Module
負責從LSL流中讀取EEG資料並維護緩衝區 / Responsible for reading EEG data from LSL stream and maintaining buffer
返回numpy array格式的資料 / Returns data in numpy array format
"""
from pylsl import StreamInlet, resolve_streams
import numpy as np
import threading
import time


class EEGReader:
    """EEG資料讀取器 / EEG Data Reader"""
    
    def __init__(self, sample_rate=1000, buffer_size=3000, channel_indices=[4, 5], stream_name="Cygnus-083704-RawEEG"):
        """
        初始化EEG讀取器 / Initialize EEG Reader
        
        Args:
            sample_rate: 採樣率 (Hz) / Sampling rate (Hz)
            buffer_size: 緩衝區大小（樣本數），3秒 = 3000 samples @ 1000Hz / Buffer size (number of samples), 3 seconds = 3000 samples @ 1000Hz
            channel_indices: 要使用的通道索引列表，預設[4,5]對應channel 4-6（Python索引從0開始） / List of channel indices to use, default [4,5] corresponds to channel 4-6 (Python indexing starts from 0)
            stream_name: LSL流名稱 / LSL stream name
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.channel_count = len(channel_indices)
        self.channel_indices = channel_indices
        self.stream_name = stream_name
        
        # 初始化緩衝區: shape = (channel_count, buffer_size) / Initialize buffer: shape = (channel_count, buffer_size)
        self.eeg_buffer = np.zeros((self.channel_count, self.buffer_size))
        self.buffer_lock = threading.Lock()
        
        # LSL相關 / LSL related
        self.inlet = None
        self.reading_thread = None
        self.is_reading = False
        
    def setup_lsl_inlet(self):
        """設置LSL輸入流 / Setup LSL input stream"""
        print("Resolving LSL streams...")
        streams = resolve_streams()
        
        if not streams:
            raise RuntimeError("No LSL streams found!")
        
        # 列出所有可用的流 / List all available streams
        for i, s in enumerate(streams):
            print(f"[{i}] {s.name()} - type: {s.type()}")
        
        # 嘗試找到指定的流 / Try to find the specified stream
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
        """後台執行緒：持續讀取EEG資料並更新緩衝區 / Background thread: Continuously read EEG data and update buffer"""
        while self.is_reading:
            try:
                sample, timestamp = self.inlet.pull_sample()
                if sample:
                    # 提取指定的通道資料 / Extract specified channel data
                    selected_data = [sample[i] for i in self.channel_indices]
                    sample_np = np.array(selected_data).reshape(-1, 1)
                    
                    # 更新緩衝區（滾動緩衝區） / Update buffer (rolling buffer)
                    with self.buffer_lock:
                        self.eeg_buffer[:, :-1] = self.eeg_buffer[:, 1:]
                        self.eeg_buffer[:, -1] = sample_np.flatten()
            except Exception as e:
                print(f"Error reading EEG sample: {e}")
                time.sleep(0.01)
    
    def start_reading(self):
        """開始讀取EEG資料 / Start reading EEG data"""
        if self.inlet is None:
            self.setup_lsl_inlet()
        
        self.is_reading = True
        self.reading_thread = threading.Thread(target=self._read_eeg_thread, daemon=True)
        self.reading_thread.start()
        print("EEG reading thread started.")
    
    def stop_reading(self):
        """停止讀取EEG資料 / Stop reading EEG data"""
        self.is_reading = False
        if self.reading_thread:
            self.reading_thread.join(timeout=1.0)
        print("EEG reading stopped.")
    
    def get_buffer(self):
        """
        獲取當前EEG緩衝區資料 / Get current EEG buffer data
        
        Returns:
            numpy.ndarray: shape = (channel_count, buffer_size) 的EEG資料 / EEG data with shape = (channel_count, buffer_size)
        """
        with self.buffer_lock:
            return self.eeg_buffer.copy()
    
    def is_buffer_ready(self):
        """
        檢查緩衝區是否已準備好（是否有有效資料） / Check if buffer is ready (has valid data)
        
        Returns:
            bool: 如果緩衝區有有效資料返回True / Returns True if buffer has valid data
        """
        with self.buffer_lock:
            # 檢查第一個值是否非零（簡單檢查是否有資料） / Check if first value is non-zero (simple check for data presence)
            return np.abs(self.eeg_buffer[0, 0]) > 1e-6

