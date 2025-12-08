"""
数据融合模块
为未来扩展准备：可以融合EEG、陀螺仪、EMG等多种传感器数据
当前版本：仅传递EEG数据（作为占位符）
"""
import numpy as np


class DataFusion:
    """数据融合器（为未来扩展准备）"""
    
    def __init__(self):
        """初始化数据融合器"""
        self.has_gyro = False
        self.has_emg = False
        # 未来可以添加更多传感器标志
    
    def add_gyroscope(self, gyro_data):
        """
        添加陀螺仪数据（未来扩展）
        
        Args:
            gyro_data: 陀螺仪数据（格式待定）
        """
        self.has_gyro = True
        self.gyro_data = gyro_data
        # TODO: 实现陀螺仪数据融合逻辑
    
    def add_emg(self, emg_data):
        """
        添加EMG数据（未来扩展）
        
        Args:
            emg_data: EMG数据（格式待定）
        """
        self.has_emg = True
        self.emg_data = emg_data
        # TODO: 实现EMG数据融合逻辑
    
    def fuse(self, eeg_data):
        """
        融合多种传感器数据
        
        Args:
            eeg_data: EEG数据，shape = (n_channels, buffer_size)
        
        Returns:
            numpy.ndarray: 融合后的数据（当前仅返回EEG数据）
        """
        # 当前版本：仅返回EEG数据
        # 未来可以在这里实现融合逻辑
        fused_data = eeg_data.copy()
        
        # 示例：未来可以在这里添加融合逻辑
        # if self.has_gyro:
        #     fused_data = self._fuse_gyro(fused_data, self.gyro_data)
        # if self.has_emg:
        #     fused_data = self._fuse_emg(fused_data, self.emg_data)
        
        return fused_data
    
    def _fuse_gyro(self, eeg_data, gyro_data):
        """融合陀螺仪数据（未来实现）"""
        # TODO: 实现陀螺仪融合逻辑
        return eeg_data
    
    def _fuse_emg(self, eeg_data, emg_data):
        """融合EMG数据（未来实现）"""
        # TODO: 实现EMG融合逻辑
        return eeg_data

