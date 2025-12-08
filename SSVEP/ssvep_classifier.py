"""
SSVEP分类器模块
使用CCA（典型相关分析）方法检测SSVEP频率并判断动作
输入：EEG数据 (numpy array)
输出：动作字符串 ("forward", "backward", "left", "right", "stop")
"""
import numpy as np
from scipy import linalg
from scipy.signal import butter, filtfilt


class SSVEPClassifier:
    """SSVEP分类器，使用CCA方法"""
    
    def __init__(self, sample_rate=1000, buffer_size=3000, 
                 frequencies=[6.0, 7.5, 8.57, 10.0],
                 frequency_labels=["forward", "left", "right", "backward"],
                 threshold=0.3, harmonics=2):
        """
        初始化SSVEP分类器
        
        Args:
            sample_rate: 采样率 (Hz)
            buffer_size: 缓冲区大小（样本数）
            frequencies: 目标频率列表 (Hz)
            frequency_labels: 对应频率的标签（动作名称）
            threshold: CCA相关系数阈值，超过此值才认为检测到
            harmonics: 使用的谐波数量（通常为2，即基频和二次谐波）
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.frequencies = frequencies
        self.frequency_labels = frequency_labels
        self.threshold = threshold
        self.harmonics = harmonics
        
        # 验证频率和标签数量匹配
        if len(frequencies) != len(frequency_labels):
            raise ValueError("frequencies and frequency_labels must have the same length")
        
        # 为每个频率生成参考信号（用于CCA）
        self.reference_signals = {}
        self._generate_reference_signals()
    
    def _generate_reference_signals(self):
        """为每个目标频率生成参考信号（包含基频和谐波）"""
        t = np.arange(self.buffer_size) / self.sample_rate  # 时间轴
        
        for freq, label in zip(self.frequencies, self.frequency_labels):
            # 生成基频和谐波的参考信号
            # 每个频率生成2*harmonics个信号（sin和cos）
            ref_signals = []
            
            for h in range(1, self.harmonics + 1):
                # 基频和谐波的sin和cos
                ref_signals.append(np.sin(2 * np.pi * h * freq * t))
                ref_signals.append(np.cos(2 * np.pi * h * freq * t))
            
            # 转换为numpy array: shape = (2*harmonics, buffer_size)
            self.reference_signals[label] = np.array(ref_signals)
    
    def _cca(self, X, Y):
        """
        典型相关分析 (Canonical Correlation Analysis)
        
        Args:
            X: 数据矩阵，shape = (n_channels, n_samples)
            Y: 参考信号矩阵，shape = (n_ref_signals, n_samples)
        
        Returns:
            rho: 最大典型相关系数
        """
        # 转置以便计算：CCA通常使用 (n_samples, n_features) 格式
        X = X.T  # (n_samples, n_channels)
        Y = Y.T  # (n_samples, n_ref_signals)
        
        # 中心化
        X = X - np.mean(X, axis=0)
        Y = Y - np.mean(Y, axis=0)
        
        # 计算协方差矩阵
        n = X.shape[0]
        Cxx = np.dot(X.T, X) / (n - 1)
        Cyy = np.dot(Y.T, Y) / (n - 1)
        Cxy = np.dot(X.T, Y) / (n - 1)
        Cyx = Cxy.T
        
        # 避免奇异矩阵
        try:
            # 计算 Cxx^(-1/2) 和 Cyy^(-1/2)
            invCxx = linalg.inv(Cxx + np.eye(Cxx.shape[0]) * 1e-6)
            invCyy = linalg.inv(Cyy + np.eye(Cyy.shape[0]) * 1e-6)
            
            # 计算典型相关系数
            # rho = max eigenvalue of (Cxx^(-1/2) * Cxy * Cyy^(-1) * Cyx * Cxx^(-1/2))
            M = np.dot(np.dot(np.dot(invCxx, Cxy), invCyy), Cyx)
            eigenvals = linalg.eigvals(M)
            rho = np.sqrt(np.max(np.real(eigenvals)))
            
        except Exception as e:
            print(f"Warning: CCA computation error: {e}")
            return 0.0
        
        return rho
    
    def classify(self, eeg_data):
        """
        对EEG数据进行SSVEP分类
        
        Args:
            eeg_data: EEG数据，shape = (n_channels, buffer_size)
        
        Returns:
            str: 动作字符串 ("forward", "backward", "left", "right", "stop")
        """
        if eeg_data.shape[1] != self.buffer_size:
            raise ValueError(f"EEG data size mismatch. Expected {self.buffer_size}, got {eeg_data.shape[1]}")
        
        # 对每个频率计算CCA相关系数
        cca_scores = {}
        
        for label in self.frequency_labels:
            ref_signal = self.reference_signals[label]
            rho = self._cca(eeg_data, ref_signal)
            cca_scores[label] = rho
        
        # 找到最大相关系数
        best_label = max(cca_scores, key=cca_scores.get)
        best_score = cca_scores[best_label]
        
        # 如果最大相关系数超过阈值，返回对应动作；否则返回"stop"
        if best_score > self.threshold:
            return best_label
        else:
            return "stop"
    
    def classify_with_scores(self, eeg_data):
        """
        对EEG数据进行SSVEP分类，并返回所有频率的得分
        
        Args:
            eeg_data: EEG数据，shape = (n_channels, buffer_size)
        
        Returns:
            tuple: (动作字符串, 得分字典)
        """
        if eeg_data.shape[1] != self.buffer_size:
            raise ValueError(f"EEG data size mismatch. Expected {self.buffer_size}, got {eeg_data.shape[1]}")
        
        # 对每个频率计算CCA相关系数
        cca_scores = {}
        
        for label in self.frequency_labels:
            ref_signal = self.reference_signals[label]
            rho = self._cca(eeg_data, ref_signal)
            cca_scores[label] = rho
        
        # 找到最大相关系数
        best_label = max(cca_scores, key=cca_scores.get)
        best_score = cca_scores[best_label]
        
        # 如果最大相关系数超过阈值，返回对应动作；否则返回"stop"
        if best_score > self.threshold:
            return best_label, cca_scores
        else:
            return "stop", cca_scores
    
    def set_threshold(self, threshold):
        """设置CCA阈值"""
        self.threshold = threshold
    
    def set_frequencies(self, frequencies, labels):
        """更新目标频率和标签"""
        if len(frequencies) != len(labels):
            raise ValueError("frequencies and labels must have the same length")
        self.frequencies = frequencies
        self.frequency_labels = labels
        self._generate_reference_signals()

