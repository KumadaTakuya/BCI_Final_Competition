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

# ======== MAIN 控制邏輯 ============
def main():
    global action_window

    print("Realtime Control Started! (FFT Mode)")
    print("Alpha (8-13Hz) → Forward")
    print("Red (11-13Hz) → Left")
    print("Blue (14-16Hz) → Right")

    while True:
        if np.abs(eeg_buffer[0, 0]) < 1e-6:
            time.sleep(0.1)
            continue

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

        if ratio < THRESHOLD_LEFT_RATIO and red_power > THRESHOLD_RED:
            action = "Left"

        elif ratio > THRESHOLD_RIGHT_RATIO and blue_power > THRESHOLD_BLUE: 
            # 注意：這裡我把 THRESHOLD_RED 改成 THRESHOLD_BLUE，原本你的 code 寫 red
            action = "Right"

        elif alpha_power > THRESHOLD_FORWARD:
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
        """
        if smooth_action == "Forward": ser.write(b'1')
        elif smooth_action == "Left": ser.write(b'4')
        elif smooth_action == "Right": ser.write(b'3')
        elif smooth_action == "Stop": ser.write(b'0')
        """

        print(f"Act: {smooth_action} | α={alpha_power:.1f} β={beta_power:.1f} Ratio={ratio:.2f} | Red={red_power:.1f} Blue={blue_power:.1f}")

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