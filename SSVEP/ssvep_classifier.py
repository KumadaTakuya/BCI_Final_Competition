"""
SSVEP分類器模組 / SSVEP Classifier Module
使用CCA（典型相關分析）方法檢測SSVEP頻率並判斷動作 / Uses CCA (Canonical Correlation Analysis) method to detect SSVEP frequencies and determine actions
輸入：EEG資料 (numpy array) / Input: EEG data (numpy array)
輸出：動作字串 ("forward", "backward", "left", "right", "stop") / Output: Action string ("forward", "backward", "left", "right", "stop")
"""
import numpy as np
from scipy import linalg
from scipy.signal import butter, filtfilt


class SSVEPClassifier:
    """SSVEP分類器，使用CCA方法 / SSVEP Classifier using CCA method"""
    
    def __init__(self, sample_rate=1000, buffer_size=3000, 
                 frequencies=[6.0, 7.5, 8.57, 10.0],
                 frequency_labels=["forward", "left", "right", "backward"],
                 threshold=0.3, harmonics=2):
        """
        初始化SSVEP分類器 / Initialize SSVEP Classifier
        
        Args:
            sample_rate: 採樣率 (Hz) / Sampling rate (Hz)
            buffer_size: 緩衝區大小（樣本數） / Buffer size (number of samples)
            frequencies: 目標頻率列表 (Hz) / List of target frequencies (Hz)
            frequency_labels: 對應頻率的標籤（動作名稱） / Labels corresponding to frequencies (action names)
            threshold: CCA相關係數閾值，超過此值才認為檢測到 / CCA correlation coefficient threshold, only detected if exceeds this value
            harmonics: 使用的諧波數量（通常為2，即基頻和二次諧波） / Number of harmonics used (usually 2, i.e., fundamental and second harmonic)
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.frequencies = frequencies
        self.frequency_labels = frequency_labels
        self.threshold = threshold
        self.harmonics = harmonics
        
        # 驗證頻率和標籤數量匹配 / Verify frequencies and labels have matching length
        if len(frequencies) != len(frequency_labels):
            raise ValueError("frequencies and frequency_labels must have the same length")
        
        # 為每個頻率生成參考訊號（用於CCA） / Generate reference signals for each frequency (for CCA)
        self.reference_signals = {}
        self._generate_reference_signals()
    
    def _generate_reference_signals(self):
        """為每個目標頻率生成參考訊號（包含基頻和諧波） / Generate reference signals for each target frequency (including fundamental and harmonics)"""
        t = np.arange(self.buffer_size) / self.sample_rate  # 時間軸 / Time axis
        
        for freq, label in zip(self.frequencies, self.frequency_labels):
            # 生成基頻和諧波的參考訊號 / Generate reference signals for fundamental and harmonics
            # 每個頻率生成2*harmonics個訊號（sin和cos） / Each frequency generates 2*harmonics signals (sin and cos)
            ref_signals = []
            
            for h in range(1, self.harmonics + 1):
                # 基頻和諧波的sin和cos / sin and cos for fundamental and harmonics
                ref_signals.append(np.sin(2 * np.pi * h * freq * t))
                ref_signals.append(np.cos(2 * np.pi * h * freq * t))
            
            # 轉換為numpy array: shape = (2*harmonics, buffer_size) / Convert to numpy array: shape = (2*harmonics, buffer_size)
            self.reference_signals[label] = np.array(ref_signals)
    
    def _cca(self, X, Y):
        """
        典型相關分析 (Canonical Correlation Analysis)
        
        Args:
            X: 資料矩陣，shape = (n_channels, n_samples) / Data matrix, shape = (n_channels, n_samples)
            Y: 參考訊號矩陣，shape = (n_ref_signals, n_samples) / Reference signal matrix, shape = (n_ref_signals, n_samples)
        
        Returns:
            rho: 最大典型相關係數 / Maximum canonical correlation coefficient
        """
        # 轉置以便計算：CCA通常使用 (n_samples, n_features) 格式 / Transpose for computation: CCA usually uses (n_samples, n_features) format
        X = X.T  # (n_samples, n_channels)
        Y = Y.T  # (n_samples, n_ref_signals)
        
        # 中心化 / Centering
        X = X - np.mean(X, axis=0)
        Y = Y - np.mean(Y, axis=0)
        
        # 計算協方差矩陣 / Compute covariance matrices
        n = X.shape[0]
        Cxx = np.dot(X.T, X) / (n - 1)
        Cyy = np.dot(Y.T, Y) / (n - 1)
        Cxy = np.dot(X.T, Y) / (n - 1)
        Cyx = Cxy.T
        
        # 避免奇異矩陣 / Avoid singular matrix
        try:
            # 計算 Cxx^(-1/2) 和 Cyy^(-1/2) / Compute Cxx^(-1/2) and Cyy^(-1/2)
            invCxx = linalg.inv(Cxx + np.eye(Cxx.shape[0]) * 1e-6)
            invCyy = linalg.inv(Cyy + np.eye(Cyy.shape[0]) * 1e-6)
            
            # 計算典型相關係數 / Compute canonical correlation coefficient
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
        對EEG資料進行SSVEP分類 / Perform SSVEP classification on EEG data
        
        Args:
            eeg_data: EEG資料，shape = (n_channels, buffer_size) / EEG data, shape = (n_channels, buffer_size)
        
        Returns:
            str: 動作字串 ("forward", "backward", "left", "right", "stop") / Action string ("forward", "backward", "left", "right", "stop")
        """
        if eeg_data.shape[1] != self.buffer_size:
            raise ValueError(f"EEG data size mismatch. Expected {self.buffer_size}, got {eeg_data.shape[1]}")
        
        # 對每個頻率計算CCA相關係數 / Calculate CCA correlation coefficient for each frequency
        cca_scores = {}
        
        for label in self.frequency_labels:
            ref_signal = self.reference_signals[label]
            rho = self._cca(eeg_data, ref_signal)
            cca_scores[label] = rho
        
        # 找到最大相關係數 / Find maximum correlation coefficient
        best_label = max(cca_scores, key=cca_scores.get)
        best_score = cca_scores[best_label]
        
        # 如果最大相關係數超過閾值，返回對應動作；否則返回"stop" / If maximum correlation coefficient exceeds threshold, return corresponding action; otherwise return "stop"
        if best_score > self.threshold:
            return best_label
        else:
            return "stop"
    
    def classify_with_scores(self, eeg_data):
        """
        對EEG資料進行SSVEP分類，並返回所有頻率的得分 / Perform SSVEP classification on EEG data and return scores for all frequencies
        
        Args:
            eeg_data: EEG資料，shape = (n_channels, buffer_size) / EEG data, shape = (n_channels, buffer_size)
        
        Returns:
            tuple: (動作字串, 得分字典) / Tuple: (action string, score dictionary)
        """
        if eeg_data.shape[1] != self.buffer_size:
            raise ValueError(f"EEG data size mismatch. Expected {self.buffer_size}, got {eeg_data.shape[1]}")
        
        # 對每個頻率計算CCA相關係數 / Calculate CCA correlation coefficient for each frequency
        cca_scores = {}
        
        for label in self.frequency_labels:
            ref_signal = self.reference_signals[label]
            rho = self._cca(eeg_data, ref_signal)
            cca_scores[label] = rho
        
        # 找到最大相關係數 / Find maximum correlation coefficient
        best_label = max(cca_scores, key=cca_scores.get)
        best_score = cca_scores[best_label]
        
        # 如果最大相關係數超過閾值，返回對應動作；否則返回"stop" / If maximum correlation coefficient exceeds threshold, return corresponding action; otherwise return "stop"
        if best_score > self.threshold:
            return best_label, cca_scores
        else:
            return "stop", cca_scores
    
    def set_threshold(self, threshold):
        """設置CCA閾值 / Set CCA threshold"""
        self.threshold = threshold
    
    def set_frequencies(self, frequencies, labels):
        """更新目標頻率和標籤 / Update target frequencies and labels"""
        if len(frequencies) != len(labels):
            raise ValueError("frequencies and labels must have the same length")
        self.frequencies = frequencies
        self.frequency_labels = labels
        self._generate_reference_signals()

