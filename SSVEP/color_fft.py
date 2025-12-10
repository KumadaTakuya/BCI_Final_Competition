from pylsl import StreamInlet, resolve_streams
import numpy as np
import time
import threading
# from scipy.signal import butter, filtfilt # 不需要了
import serial

# ======== 設定參數 ========
SAMPLE_RATE = 1000
CHANNEL_COUNT = 2
BUFFER_SIZE = 1000   # 1s (這剛好讓頻率解析度 Resolution = 1Hz，非常方便)
eeg_buffer = np.zeros((CHANNEL_COUNT, BUFFER_SIZE))

# serial 設定
# ser = serial.Serial("COM3", 9600, timeout=10, write_timeout=10)

action_window = []
WINDOW_SIZE = 5  # 保留window次數

# ======== 閾值 (注意：FFT 算出來的數值大小可能不同，請重新微調) ========
THRESHOLD_FORWARD = 10000.0   # 閉眼 / 前進 α power
THRESHOLD_LEFT_RATIO = 0.5  # 紅色 α/β ratio
THRESHOLD_RIGHT_RATIO = 1.5 # 藍色 α/β ratio

THRESHOLD_RED = 50.0     # 12 Hz band power threshold
THRESHOLD_BLUE = 50.0    # 15 Hz band power threshold

# ======== 預先計算 FFT 相關參數 ========
# 頻率軸 (0, 1, 2, ..., 500 Hz)
freqs = np.fft.rfftfreq(BUFFER_SIZE, d=1/SAMPLE_RATE)

# 窗函數 (Hanning Window)，用於減少頻譜洩漏
# 形狀需為 (1, BUFFER_SIZE) 以便與 eeg_buffer (2, BUFFER_SIZE) 相乘
window = np.hanning(BUFFER_SIZE).reshape(1, -1)

# ======== EEG Reading Thread ============
def read_eeg(inlet):
    global eeg_buffer

    while True:
        sample, timestamp = inlet.pull_sample()
        if sample:
            # 假設你的設備 O1=Channel 4, O2=Channel 5
            selected_data = sample[4:6]
            sample_np = np.array(selected_data).reshape(-1, 1)

            # 更新 Buffer (FIFO)
            eeg_buffer[:, :-1] = eeg_buffer[:, 1:]
            eeg_buffer[:, -1] = sample_np.flatten()

# ======== 輔助函式：計算特定頻帶能量 ========
def get_band_power(psd, freq_axis, low, high):
    """
    psd: Power Spectral Density (已經平均過頻道的)
    freq_axis: 頻率軸
    low, high: 頻帶範圍
    """
    # 找出在 low ~ high 範圍內的頻率 index
    idx = np.logical_and(freq_axis >= low, freq_axis <= high)
    # 將該範圍內的能量加總 (也可以用 mean，看你習慣)
    return np.sum(psd[idx])

# ======== 輔助函式：計算各Hz區間能量 ========
def get_frequency_bands(psd, freq_axis, band_width=1.0):
    """
    計算各Hz區間的能量 / Calculate energy for each Hz band
    
    Args:
        psd: Power Spectral Density
        freq_axis: 頻率軸 / Frequency axis
        band_width: 區間寬度（Hz）/ Band width (Hz)
    
    Returns:
        dict: {頻率中心: 能量} / {frequency_center: power}
    """
    bands = {}
    max_freq = int(np.max(freq_axis))
    
    for center_freq in range(0, max_freq + 1):
        low = center_freq - band_width / 2
        high = center_freq + band_width / 2
        power = get_band_power(psd, freq_axis, low, high)
        bands[center_freq] = power
    
    return bands

# ======== MAIN 控制邏輯 ============
def main():
    global action_window

    print("Realtime Control Started! (FFT Mode)")
    print("Alpha (8-13Hz) → Forward")
    print("Red (11-13Hz) → Left")
    print("Blue (14-16Hz) → Right")
    print("=" * 80)
    print("每5秒顯示一次詳細頻率資訊 / Detailed frequency information displayed every 5 seconds")
    print("=" * 80)

    # 時間追蹤 / Time tracking
    start_time = time.time()
    last_log_time = start_time
    log_interval = 10.0  # 每5秒顯示一次 / Display every 5 seconds
    loop_count = 0

    while True:
        if np.abs(eeg_buffer[0, 0]) < 1e-6:
            time.sleep(0.1)
            continue

        loop_count += 1
        current_time = time.time()

        # ====== 1. 預處理：去直流 (Demean) 與 加窗 (Windowing) ======
        # 去除 DC offset (平均值)，避免 0Hz 能量過大
        data_detrend = eeg_buffer - np.mean(eeg_buffer, axis=1, keepdims=True)
        # 乘上窗函數
        data_windowed = data_detrend * window

        # ====== 2. FFT 運算 ======
        # rfft: Real FFT (只計算正頻率部分)
        fft_vals = np.fft.rfft(data_windowed, axis=1)
        
        # 計算功率譜 (PSD)
        # 取絕對值(振幅) -> 平方 -> 除以長度(正規化)
        # 這裡簡單用 |FFT|^2 / N 即可代表相對能量強度
        psd = (np.abs(fft_vals) ** 2) / BUFFER_SIZE
        
        # 將兩個頻道的能量平均 (O1 和 O2 平均)
        avg_psd = np.mean(psd, axis=0)

        # ====== 3. 提取頻帶能量 ======
        alpha_power = get_band_power(avg_psd, freqs, 8, 13)
        beta_power  = get_band_power(avg_psd, freqs, 13, 30)
        
        red_power   = get_band_power(avg_psd, freqs, 11, 13) # 12Hz ± 1
        blue_power  = get_band_power(avg_psd, freqs, 14, 16) # 15Hz ± 1

        ratio = alpha_power / (beta_power + 1e-6)

        # ====== 4. 動作判斷 (邏輯維持不變) ======
        action = "Stop"

        """
        if ratio < THRESHOLD_LEFT_RATIO and red_power > THRESHOLD_RED:
            action = "Left"

        elif ratio > THRESHOLD_RIGHT_RATIO and blue_power > THRESHOLD_BLUE: 
            # 注意：這裡我把 THRESHOLD_RED 改成 THRESHOLD_BLUE，原本你的 code 寫 red
            action = "Right"
        """

        if alpha_power > THRESHOLD_FORWARD:
            action = "Forward"

        else:
            action = "Stop"

        # ====== Sliding window 平滑 ======
        action_window.append(action)
        if len(action_window) > WINDOW_SIZE:
            action_window.pop(0)

        smooth_action = max(set(action_window), key=action_window.count)

        # ====== Serial 輸出 ======
        counts = {action: action_window.count(action) for action in set(action_window)}
        max_count = counts[smooth_action]

        if max_count < len(action_window) / 2:
            smooth_action = "Stop"
            # print("no half vote")

        # Serial 寫入部分暫時註解...
        
        #if smooth_action == "Forward": ser.write(b'1')
        # elif smooth_action == "Left": ser.write(b'4')
        # elif smooth_action == "Right": ser.write(b'3')
        #elif smooth_action == "Stop": ser.write(b'0')
        
        # print(f"Act: {smooth_action} | α={alpha_power:.1f} β={beta_power:.1f} Ratio={ratio:.2f} | Red={red_power:.1f} Blue={blue_power:.1f}")

        # ====== 每5秒顯示一次詳細資訊 ======
        time_since_last_log = current_time - last_log_time
        if time_since_last_log >= log_interval:
            # 計算總能量 / Calculate total energy
            total_energy = np.sum(avg_psd)
            
            # 計算各Hz區間能量（1Hz間隔）/ Calculate energy for each Hz band (1Hz intervals)
            freq_bands = get_frequency_bands(avg_psd, freqs, band_width=1.0)
            
            # 計算主要頻帶能量 / Calculate main frequency band energies
            delta_power = get_band_power(avg_psd, freqs, 0.5, 4)    # Delta: 0.5-4 Hz
            theta_power = get_band_power(avg_psd, freqs, 4, 8)      # Theta: 4-8 Hz
            gamma_power = get_band_power(avg_psd, freqs, 30, 100)    # Gamma: 30-100 Hz
            
            # 顯示詳細資訊 / Display detailed information
            print("\n" + "=" * 80)
            print(f"檢測時間段 / Detection Time Segment - 時間 / Time: {current_time - start_time:.1f}s")
            print(f"循環次數 / Loop Count: {loop_count}")
            print("-" * 80)
            print(f"總能量 / Total Energy: {total_energy:.2f}")
            print("-" * 80)
            print("主要頻帶能量 / Main Frequency Band Energies:")
            print(f"  Delta (0.5-4 Hz):   {delta_power:8.2f}")
            print(f"  Theta (4-8 Hz):     {theta_power:8.2f}")
            print(f"  Alpha (8-13 Hz):    {alpha_power:8.2f}")
            print(f"  Beta (13-30 Hz):    {beta_power:8.2f}")
            print(f"  Gamma (30-100 Hz):  {gamma_power:8.2f}")
            print(f"  Red (11-13 Hz):     {red_power:8.2f}")
            print(f"  Blue (14-16 Hz):    {blue_power:8.2f}")
            print(f"  Alpha/Beta Ratio:   {ratio:8.2f}")
            print("-" * 80)
            print("各Hz區間能量 (0-50 Hz) / Energy per Hz Band (0-50 Hz):")
            
            # 顯示0-50Hz的詳細資訊（每5Hz一行） / Display 0-50Hz details (5Hz per line)
            for start_freq in range(0, 50, 5):
                line_parts = []
                for offset in range(5):
                    freq = start_freq + offset
                    if freq in freq_bands:
                        power = freq_bands[freq]
                        line_parts.append(f"{freq:2d}Hz:{power:7.1f}")
                    else:
                        line_parts.append(f"{freq:2d}Hz:   N/A")
                print("  " + " | ".join(line_parts))
            
            print("-" * 80)
            print(f"當前動作 / Current Action: {smooth_action}")
            print(f"閾值狀態 / Threshold Status:")
            print(f"  Forward (α > {THRESHOLD_FORWARD}): {'✓' if alpha_power > THRESHOLD_FORWARD else '✗'} ({alpha_power:.1f})")
            print(f"  Red (Red > {THRESHOLD_RED}): {'✓' if red_power > THRESHOLD_RED else '✗'} ({red_power:.1f})")
            print(f"  Blue (Blue > {THRESHOLD_BLUE}): {'✓' if blue_power > THRESHOLD_BLUE else '✗'} ({blue_power:.1f})")
            print("=" * 80 + "\n")
            
            last_log_time = current_time
        else:
            # 簡化顯示（非詳細輸出時間） / Simplified display (when not detailed output time)
            print(f"\rAct: {smooth_action} | α={alpha_power:.1f} β={beta_power:.1f} Ratio={ratio:.2f} | Red={red_power:.1f} Blue={blue_power:.1f} | Time: {current_time - start_time:.1f}s", end="", flush=True)

        # 稍微調整 sleep 時間，配合數據更新率
        time.sleep(0.1)

# ======== LSL Setup (不變) ============
def setup_lsl_inlet(stream_name="Cygnus-083704-RawEEG"):
    print("Resolving streams...")
    streams = resolve_streams()
    if not streams:
        print("No streams found!")
        exit(1)
    for i, s in enumerate(streams):
        print(f"[{i}] {s.name()} - type: {s.type()}")

    target_stream = streams[0]
    # 嘗試尋找指定名稱，找不到就用第一個
    for s in streams:
        if stream_name in s.name(): # 使用 partial match 比較安全
            target_stream = s
            break
            
    print(f"Connecting to {target_stream.name()}...")
    inlet = StreamInlet(target_stream)
    return inlet

# ======== Main entry ========
if __name__ == "__main__":
    inlet = setup_lsl_inlet()

    thread1 = threading.Thread(target=read_eeg, args=(inlet,), daemon=True)
    thread1.start()

    print("Buffering...")
    time.sleep(2)

    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        exit(0)