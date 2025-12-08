"""
資料融合模組 / Data Fusion Module
為未來擴展準備：可以融合EEG、陀螺儀、EMG等多種感測器資料 / Prepared for future expansion: can fuse EEG, gyroscope, EMG and other sensor data
當前版本：僅傳遞EEG資料（作為佔位符） / Current version: only passes through EEG data (as placeholder)
"""
import numpy as np


class DataFusion:
    """資料融合器（為未來擴展準備） / Data Fusion (prepared for future expansion)"""
    
    def __init__(self):
        """初始化資料融合器 / Initialize Data Fusion"""
        self.has_gyro = False
        self.has_emg = False
        # 未來可以添加更多感測器標誌 / Can add more sensor flags in the future
    
    def add_gyroscope(self, gyro_data):
        """
        添加陀螺儀資料（未來擴展） / Add gyroscope data (future expansion)
        
        Args:
            gyro_data: 陀螺儀資料（格式待定） / Gyroscope data (format to be determined)
        """
        self.has_gyro = True
        self.gyro_data = gyro_data
        # TODO: 實現陀螺儀資料融合邏輯 / TODO: Implement gyroscope data fusion logic
    
    def add_emg(self, emg_data):
        """
        添加EMG資料（未來擴展） / Add EMG data (future expansion)
        
        Args:
            emg_data: EMG資料（格式待定） / EMG data (format to be determined)
        """
        self.has_emg = True
        self.emg_data = emg_data
        # TODO: 實現EMG資料融合邏輯 / TODO: Implement EMG data fusion logic
    
    def fuse(self, eeg_data):
        """
        融合多種感測器資料 / Fuse multiple sensor data
        
        Args:
            eeg_data: EEG資料，shape = (n_channels, buffer_size) / EEG data, shape = (n_channels, buffer_size)
        
        Returns:
            numpy.ndarray: 融合後的資料（當前僅返回EEG資料） / Fused data (currently only returns EEG data)
        """
        # 當前版本：僅返回EEG資料 / Current version: only returns EEG data
        # 未來可以在這裡實現融合邏輯 / Can implement fusion logic here in the future
        fused_data = eeg_data.copy()
        
        # 範例：未來可以在這裡添加融合邏輯 / Example: can add fusion logic here in the future
        # if self.has_gyro:
        #     fused_data = self._fuse_gyro(fused_data, self.gyro_data)
        # if self.has_emg:
        #     fused_data = self._fuse_emg(fused_data, self.emg_data)
        
        return fused_data
    
    def _fuse_gyro(self, eeg_data, gyro_data):
        """融合陀螺儀資料（未來實現） / Fuse gyroscope data (to be implemented)"""
        # TODO: 實現陀螺儀融合邏輯 / TODO: Implement gyroscope fusion logic
        return eeg_data
    
    def _fuse_emg(self, eeg_data, emg_data):
        """融合EMG資料（未來實現） / Fuse EMG data (to be implemented)"""
        # TODO: 實現EMG融合邏輯 / TODO: Implement EMG fusion logic
        return eeg_data

