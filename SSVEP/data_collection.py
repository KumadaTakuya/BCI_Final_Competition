"""
SSVEP數據收集腳本 / SSVEP Data Collection Script
隨機顯示單個閃爍方塊並收集EEG頻率數據 / Randomly display single flickering square and collect EEG frequency data
用於後續分析 / For subsequent analysis
"""
from pylsl import StreamInlet, resolve_streams
import numpy as np
import time
import threading
import random
import json
import os
from datetime import datetime
import sys

# 添加utils目錄到路徑 / Add utils directory to path
utils_path = os.path.join(os.path.dirname(__file__), 'utils')
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)
from ssvep_stimulus import SSVEPStimulus

# ======== 設定參數 ========
SAMPLE_RATE = 1000
CHANNEL_COUNT = 2
BUFFER_SIZE = 1000   # 1s (頻率解析度 Resolution = 1Hz)
eeg_buffer = np.zeros((CHANNEL_COUNT, BUFFER_SIZE))

# SSVEP刺激設定 / SSVEP Stimulus Settings
STIMULUS_CONFIG = {
    "frequencies": [7.5, 6.0, 8.57],  # Left, Forward, Right
    "labels": ["Left", "Forward", "Right"],
    "colors": [
        (100, 255, 100),  # 綠色 / Green - Left
        (255, 100, 100),  # 紅色 / Red - Forward
        (100, 100, 255),  # 藍色 / Blue - Right
    ],
    "window_size": (1200, 800),
    "stimulus_size": 300
}

# 數據收集設定 / Data Collection Settings
TRIAL_DURATION = 5.0  # 每個試驗持續時間（秒）/ Trial duration (seconds)
TRIAL_INTERVAL = 2.0  # 試驗間隔（秒）/ Interval between trials (seconds)
NUM_TRIALS = 20  # 總試驗次數 / Total number of trials

# 預先計算 FFT 相關參數 / Pre-calculate FFT parameters
freqs = np.fft.rfftfreq(BUFFER_SIZE, d=1/SAMPLE_RATE)
window = np.hanning(BUFFER_SIZE).reshape(1, -1)

# 數據存儲 / Data storage
collected_data = []
current_trial = None
data_lock = threading.Lock()

# ======== EEG Reading Thread ============
def read_eeg(inlet):
    """持續讀取EEG數據 / Continuously read EEG data"""
    global eeg_buffer
    while True:
        try:
            sample, timestamp = inlet.pull_sample()
            if sample:
                # 假設設備 O1=Channel 4, O2=Channel 5
                selected_data = sample[4:6]
                sample_np = np.array(selected_data).reshape(-1, 1)
                
                # 更新 Buffer (FIFO)
                eeg_buffer[:, :-1] = eeg_buffer[:, 1:]
                eeg_buffer[:, -1] = sample_np.flatten()
        except Exception as e:
            print(f"Error reading EEG: {e}")
            time.sleep(0.01)

# ======== 輔助函式：計算特定頻帶能量 ========
def get_band_power(psd, freq_axis, low, high):
    """計算特定頻帶能量 / Calculate specific frequency band power"""
    idx = np.logical_and(freq_axis >= low, freq_axis <= high)
    return np.sum(psd[idx])

# ======== 輔助函式：計算各Hz區間能量 ========
def get_frequency_bands(psd, freq_axis, band_width=1.0):
    """計算各Hz區間的能量 / Calculate energy for each Hz band"""
    bands = {}
    max_freq = int(np.max(freq_axis))
    
    for center_freq in range(0, max_freq + 1):
        low = center_freq - band_width / 2
        high = center_freq + band_width / 2
        power = get_band_power(psd, freq_axis, low, high)
        bands[center_freq] = float(power)  # 轉換為Python float以便JSON序列化
    
    return bands

# ======== 計算FFT並提取所有頻率數據 ========
def analyze_eeg_data():
    """分析EEG數據並返回所有頻率信息 / Analyze EEG data and return all frequency information"""
    if np.abs(eeg_buffer[0, 0]) < 1e-6:
        return None
    
    # 1. 預處理：去直流與加窗 / Preprocessing: detrend and windowing
    data_detrend = eeg_buffer - np.mean(eeg_buffer, axis=1, keepdims=True)
    data_windowed = data_detrend * window
    
    # 2. FFT運算 / FFT computation
    fft_vals = np.fft.rfft(data_windowed, axis=1)
    psd = (np.abs(fft_vals) ** 2) / BUFFER_SIZE
    avg_psd = np.mean(psd, axis=0)
    
    # 3. 計算總能量 / Calculate total energy
    total_energy = float(np.sum(avg_psd))
    
    # 4. 計算主要頻帶能量 / Calculate main frequency band energies
    delta_power = float(get_band_power(avg_psd, freqs, 0.5, 4))
    theta_power = float(get_band_power(avg_psd, freqs, 4, 8))
    alpha_power = float(get_band_power(avg_psd, freqs, 8, 13))
    beta_power = float(get_band_power(avg_psd, freqs, 13, 30))
    gamma_power = float(get_band_power(avg_psd, freqs, 30, 100))
    
    # 5. 計算各Hz區間能量（0-50Hz）/ Calculate energy for each Hz band (0-50Hz)
    freq_bands = get_frequency_bands(avg_psd, freqs, band_width=1.0)
    
    # 6. 計算SSVEP相關頻帶 / Calculate SSVEP-related frequency bands
    left_power = float(get_band_power(avg_psd, freqs, 7.0, 8.0))    # 7.5 Hz附近
    forward_power = float(get_band_power(avg_psd, freqs, 5.5, 6.5))  # 6.0 Hz附近
    right_power = float(get_band_power(avg_psd, freqs, 8.0, 9.2))    # 8.57 Hz附近
    
    return {
        "total_energy": total_energy,
        "main_bands": {
            "delta": delta_power,
            "theta": theta_power,
            "alpha": alpha_power,
            "beta": beta_power,
            "gamma": gamma_power
        },
        "ssvep_bands": {
            "left": left_power,      # 7.5 Hz
            "forward": forward_power,  # 6.0 Hz
            "right": right_power      # 8.57 Hz
        },
        "frequency_bands": freq_bands,  # 0-50Hz各Hz區間能量
        "timestamp": time.time()
    }

# ======== 單個刺激顯示類 / Single Stimulus Display Class ========
class SingleStimulusDisplay:
    """單個刺激顯示器 / Single Stimulus Display"""
    
    def __init__(self, config):
        self.config = config
        self.current_stimulus_index = None
        self.running = False
        
        # 初始化pygame / Initialize pygame
        import pygame
        pygame.init()
        self.screen = pygame.display.set_mode(config["window_size"])
        pygame.display.set_caption("SSVEP Data Collection - Press ESC to exit")
        self.clock = pygame.time.Clock()
        self.start_time = None
        
        # 顏色定義 / Color definitions
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        
        # 字體設置 / Font settings
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        self.pygame = pygame
    
    def show_stimulus(self, index, duration):
        """
        顯示單個刺激 / Display single stimulus
        
        Args:
            index: 刺激索引 (0=Left, 1=Forward, 2=Right) / Stimulus index
            duration: 顯示持續時間（秒）/ Display duration (seconds)
        """
        self.current_stimulus_index = index
        self.running = True
        self.start_time = time.time()
        
        frequency = self.config["frequencies"][index]
        label = self.config["labels"][index]
        color = self.config["colors"][index]
        
        center_x, center_y = self.config["window_size"][0] // 2, self.config["window_size"][1] // 2
        stimulus_size = self.config["stimulus_size"]
        
        end_time = self.start_time + duration
        
        while self.running and time.time() < end_time:
            # 處理事件 / Handle events
            for event in self.pygame.event.get():
                if event.type == self.pygame.QUIT:
                    self.running = False
                    return False
                elif event.type == self.pygame.KEYDOWN:
                    if event.key == self.pygame.K_ESCAPE:
                        self.running = False
                        return False
            
            # 計算當前時間和相位 / Calculate current time and phase
            current_time = time.time() - self.start_time
            phase = 2 * np.pi * frequency * current_time
            is_on = (phase % (2 * np.pi)) < np.pi
            
            # 清空屏幕 / Clear screen
            self.screen.fill(self.BLACK)
            
            # 繪製刺激方塊 / Draw stimulus square
            rect = self.pygame.Rect(
                center_x - stimulus_size // 2,
                center_y - stimulus_size // 2,
                stimulus_size,
                stimulus_size
            )
            
            if is_on:
                self.pygame.draw.rect(self.screen, color, rect)
                self.pygame.draw.rect(self.screen, self.WHITE, rect, 5)
            else:
                self.pygame.draw.rect(self.screen, self.BLACK, rect)
                self.pygame.draw.rect(self.screen, self.GRAY, rect, 5)
            
            # 顯示標籤和頻率 / Display label and frequency
            if is_on:
                label_text = self.font_large.render(label, True, self.WHITE)
                label_rect = label_text.get_rect(center=(center_x, center_y - 30))
                self.screen.blit(label_text, label_rect)
                
                freq_text = self.font_medium.render(f"{frequency} Hz", True, self.WHITE)
                freq_rect = freq_text.get_rect(center=(center_x, center_y + 30))
                self.screen.blit(freq_text, freq_rect)
            
            # 顯示剩餘時間 / Display remaining time
            remaining = end_time - time.time()
            if remaining > 0:
                time_text = self.font_small.render(f"Time: {remaining:.1f}s", True, self.WHITE)
                self.screen.blit(time_text, (20, 20))
            
            # 更新顯示 / Update display
            self.pygame.display.flip()
            self.clock.tick(120)
        
        return True
    
    def show_rest(self, duration):
        """顯示休息畫面（黑屏）/ Show rest screen (black screen)"""
        end_time = time.time() + duration
        
        while self.running and time.time() < end_time:
            for event in self.pygame.event.get():
                if event.type == self.pygame.QUIT:
                    self.running = False
                    return False
                elif event.type == self.pygame.KEYDOWN:
                    if event.key == self.pygame.K_ESCAPE:
                        self.running = False
                        return False
            
            self.screen.fill(self.BLACK)
            
            # 顯示"休息"文字 / Display "Rest" text
            rest_text = self.font_medium.render("Rest...", True, self.WHITE)
            rest_rect = rest_text.get_rect(center=(self.config["window_size"][0] // 2, 
                                                   self.config["window_size"][1] // 2))
            self.screen.blit(rest_text, rest_rect)
            
            remaining = end_time - time.time()
            if remaining > 0:
                time_text = self.font_small.render(f"Time: {remaining:.1f}s", True, self.WHITE)
                self.screen.blit(time_text, (20, 20))
            
            self.pygame.display.flip()
            self.clock.tick(60)
        
        return True
    
    def close(self):
        """關閉窗口 / Close window"""
        self.running = False
        self.pygame.quit()

# ======== 數據收集主函數 ============
def collect_data(inlet, display):
    """收集數據 / Collect data"""
    global collected_data, current_trial
    
    print("\n" + "=" * 80)
    print("開始數據收集 / Starting Data Collection")
    print("=" * 80)
    print(f"總試驗次數 / Total Trials: {NUM_TRIALS}")
    print(f"每個試驗持續時間 / Trial Duration: {TRIAL_DURATION}秒")
    print(f"試驗間隔 / Trial Interval: {TRIAL_INTERVAL}秒")
    print("=" * 80 + "\n")
    
    # 生成隨機試驗序列 / Generate random trial sequence
    trial_sequence = [random.randint(0, 2) for _ in range(NUM_TRIALS)]
    
    for trial_num in range(NUM_TRIALS):
        if not display.running:
            break
        
        stimulus_index = trial_sequence[trial_num]
        stimulus_label = STIMULUS_CONFIG["labels"][stimulus_index]
        stimulus_freq = STIMULUS_CONFIG["frequencies"][stimulus_index]
        
        print(f"\n試驗 {trial_num + 1}/{NUM_TRIALS} / Trial {trial_num + 1}/{NUM_TRIALS}")
        print(f"刺激類型 / Stimulus: {stimulus_label} ({stimulus_freq} Hz)")
        print("-" * 80)
        
        # 記錄試驗開始 / Record trial start
        trial_start_time = time.time()
        current_trial = {
            "trial_number": trial_num + 1,
            "stimulus_index": stimulus_index,
            "stimulus_label": stimulus_label,
            "stimulus_frequency": stimulus_freq,
            "start_time": trial_start_time,
            "samples": []
        }
        
        # 顯示刺激並收集數據 / Display stimulus and collect data
        sample_interval = 0.1  # 每0.1秒採樣一次 / Sample every 0.1 seconds
        samples_per_trial = int(TRIAL_DURATION / sample_interval)
        
        display_thread = threading.Thread(
            target=display.show_stimulus,
            args=(stimulus_index, TRIAL_DURATION),
            daemon=True
        )
        display_thread.start()
        
        # 收集數據 / Collect data
        sample_count = 0
        while sample_count < samples_per_trial and display.running:
            eeg_data = analyze_eeg_data()
            if eeg_data:
                sample_data = eeg_data.copy()
                sample_data["sample_number"] = sample_count + 1
                sample_data["elapsed_time"] = time.time() - trial_start_time
                current_trial["samples"].append(sample_data)
                sample_count += 1
            
            time.sleep(sample_interval)
        
        # 等待顯示線程結束 / Wait for display thread to finish
        display_thread.join(timeout=1.0)
        
        trial_end_time = time.time()
        current_trial["end_time"] = trial_end_time
        current_trial["duration"] = trial_end_time - trial_start_time
        current_trial["num_samples"] = len(current_trial["samples"])
        
        # 保存試驗數據 / Save trial data
        with data_lock:
            collected_data.append(current_trial.copy())
        
        print(f"收集樣本數 / Samples Collected: {len(current_trial['samples'])}")
        print(f"試驗完成 / Trial Completed")
        
        # 試驗間隔（休息） / Trial interval (rest)
        if trial_num < NUM_TRIALS - 1:  # 最後一個試驗不需要休息 / Last trial doesn't need rest
            print(f"\n休息 {TRIAL_INTERVAL} 秒... / Resting for {TRIAL_INTERVAL} seconds...")
            display.show_rest(TRIAL_INTERVAL)
    
    print("\n" + "=" * 80)
    print("數據收集完成 / Data Collection Completed")
    print("=" * 80)

# ======== 保存數據 ============
def save_data(filename=None):
    """保存收集的數據到JSON文件 / Save collected data to JSON file"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ssvep_data_{timestamp}.json"
    
    filepath = os.path.join(os.path.dirname(__file__), filename)
    
    output_data = {
        "metadata": {
            "collection_time": datetime.now().isoformat(),
            "sample_rate": SAMPLE_RATE,
            "buffer_size": BUFFER_SIZE,
            "trial_duration": TRIAL_DURATION,
            "trial_interval": TRIAL_INTERVAL,
            "num_trials": NUM_TRIALS,
            "stimulus_config": STIMULUS_CONFIG
        },
        "trials": collected_data
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n數據已保存到 / Data saved to: {filepath}")
    print(f"總試驗數 / Total Trials: {len(collected_data)}")
    
    # 統計信息 / Statistics
    total_samples = sum(len(trial["samples"]) for trial in collected_data)
    print(f"總樣本數 / Total Samples: {total_samples}")
    
    return filepath

# ======== LSL Setup ============
def setup_lsl_inlet(stream_name="Cygnus-083704-RawEEG"):
    """設置LSL輸入流 / Setup LSL input stream"""
    print("Resolving streams...")
    streams = resolve_streams()
    if not streams:
        print("No streams found!")
        exit(1)
    for i, s in enumerate(streams):
        print(f"[{i}] {s.name()} - type: {s.type()}")
    
    target_stream = streams[0]
    for s in streams:
        if stream_name in s.name():
            target_stream = s
            break
    
    print(f"Connecting to {target_stream.name()}...")
    inlet = StreamInlet(target_stream)
    return inlet

# ======== Main Entry ============
def main():
    """主函數 / Main Function"""
    import argparse
    
    # 聲明全局變量 / Declare global variables
    global NUM_TRIALS, TRIAL_DURATION, TRIAL_INTERVAL
    
    parser = argparse.ArgumentParser(description="SSVEP Data Collection")
    parser.add_argument("--trials", type=int, default=NUM_TRIALS,
                        help=f"Number of trials (default: {NUM_TRIALS})")
    parser.add_argument("--duration", type=float, default=TRIAL_DURATION,
                        help=f"Trial duration in seconds (default: {TRIAL_DURATION})")
    parser.add_argument("--interval", type=float, default=TRIAL_INTERVAL,
                        help=f"Interval between trials in seconds (default: {TRIAL_INTERVAL})")
    parser.add_argument("--output", type=str, default=None,
                        help="Output filename (default: auto-generated)")
    parser.add_argument("--stream-name", type=str, default="Cygnus-083704-RawEEG",
                        help="LSL stream name")
    
    args = parser.parse_args()
    
    # 更新全局設定 / Update global settings
    NUM_TRIALS = args.trials
    TRIAL_DURATION = args.duration
    TRIAL_INTERVAL = args.interval
    
    print("=" * 80)
    print("SSVEP Data Collection System")
    print("=" * 80)
    print(f"試驗次數 / Trials: {NUM_TRIALS}")
    print(f"試驗持續時間 / Trial Duration: {TRIAL_DURATION}秒")
    print(f"試驗間隔 / Trial Interval: {TRIAL_INTERVAL}秒")
    print("=" * 80)
    
    # 設置LSL / Setup LSL
    inlet = setup_lsl_inlet(args.stream_name)
    
    # 啟動EEG讀取線程 / Start EEG reading thread
    eeg_thread = threading.Thread(target=read_eeg, args=(inlet,), daemon=True)
    eeg_thread.start()
    
    print("\nBuffering EEG data...")
    time.sleep(2)
    
    # 創建顯示器 / Create display
    display = SingleStimulusDisplay(STIMULUS_CONFIG)
    
    try:
        # 開始數據收集 / Start data collection
        collect_data(inlet, display)
        
        # 保存數據 / Save data
        save_data(args.output)
        
    except KeyboardInterrupt:
        print("\n\n數據收集中斷 / Data collection interrupted")
        if collected_data:
            save_data(args.output)
    except Exception as e:
        print(f"\n錯誤 / Error: {e}")
        import traceback
        traceback.print_exc()
        if collected_data:
            save_data(args.output)
    finally:
        display.close()
        print("\n程序結束 / Program ended")

if __name__ == "__main__":
    main()

