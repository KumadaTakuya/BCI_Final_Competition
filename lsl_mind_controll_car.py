from pylsl import StreamInlet, resolve_streams, resolve_byprop
import numpy as np
import time
import threading
from scipy.signal import butter, filtfilt
import serial
# ======== 設定參數 ========
SAMPLE_RATE = 1000  # 請確認這與您的 LSL stream 採樣率一致
# 根據經驗設定
thres = 100.0
CHANNEL_COUNT = 2
BUFFER_SIZE = 1000  # alpha 波需要約 1秒資料比較準 (1000 samples)
eeg_buffer = np.zeros((CHANNEL_COUNT, BUFFER_SIZE))
ser = serial.Serial("COM3", 9600, timeout=10, write_timeout=10)

# ======== EEG Reading Thread ============
def read_eeg(inlet):
    global eeg_buffer
    while True:
        sample, timestamp = inlet.pull_sample()
        if sample:
            # 取出特定 channel
            # selected_data = sample[0:2] + sample[4:6]
            selected_data = sample[4:6]
            sample_np = np.array(selected_data).reshape(-1, 1)

            # Update buffer (Rolling buffer)
            eeg_buffer[:, :-1] = eeg_buffer[:, 1:]
            eeg_buffer[:, -1] = sample_np.flatten()


def main():
    # 設定濾波器：Alpha 波範圍 8-13 Hz
    lowcut = 8.0
    highcut = 13.0
    nyq = 0.5 * SAMPLE_RATE
    b, a = butter(2, [lowcut / nyq, highcut / nyq], btype='band')

    print(f"Start detecting Alpha Wave ({lowcut}-{highcut} Hz)...")
    print("Please CLOSE YOUR EYES to boost Alpha waves.")

    while True:
        # 簡單檢查 buffer 是否填滿 (避免初期雜訊)
        
        if np.abs(eeg_buffer[0, 0]) < 1e-6:
            # 這裡假設如果第一個值還是 0 代表還沒填滿或沒訊號
            time.sleep(0.1)
            continue
        

        # 1. 濾波：取出 Alpha 頻段
        # axis=1 代表對時間軸濾波
        alpha_wave = filtfilt(b, a, eeg_buffer, axis=1)

        # 2. 計算能量 (Alpha Power)
        # 方法：訊號平方 -> 取平均 (Mean Squared Power)
        # 我們計算所有 Channel 的平均能量
        # alpha_wave ** 2 把正負號都變正值
        power_per_channel = np.mean(alpha_wave ** 2, axis=1)
        avg_alpha_power = np.mean(power_per_channel)

        # 3. 判斷觸發
        if avg_alpha_power > thres:
            print(f"Move Forward! >>> Power: {avg_alpha_power:.2f}")
            ser.write(b'1')
        else:
            print(f"Stop.           ... Power: {avg_alpha_power:.2f}")
            ser.write(b'0')

        time.sleep(0.1999)  # 降低更新頻率，方便閱讀數據


# ======== LSL Inlet Setup ============
def setup_lsl_inlet(stream_name="Cygnus-083704-RawEEG"):
    print("Resolving streams...")
    # 這裡改成先列出所有 streams 讓你知道有沒有抓到
    streams = resolve_streams()
    if not streams:
        print("No streams found!")
        exit(1)

    for i, s in enumerate(streams):
        print(f"[{i}] {s.name()} - type: {s.type()}")

    # 嘗試自動抓取包含 'EEG' 的 stream，或是指定名稱
    target_stream = streams[0]  # 預設抓第一個
    for s in streams:
        if s.name() == stream_name:
            target_stream = s
            break

    print(f"Connecting to {target_stream.name()}...")
    inlet = StreamInlet(target_stream)
    return inlet


if __name__ == "__main__":
    inlet = setup_lsl_inlet()  # 視情況修改你的 Stream 名稱

    thread1 = threading.Thread(target=read_eeg, args=(inlet,), daemon=True)
    thread1.start()

    # 等待一點時間讓 buffer 累積
    print("Buffering...")
    time.sleep(2)

    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        exit(0)