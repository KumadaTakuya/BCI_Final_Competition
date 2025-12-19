from pylsl import StreamInlet, resolve_streams
import numpy as np
import time
import threading
from scipy.signal import butter, filtfilt
import serial

# ======== 設定參數 ========
SAMPLE_RATE = 1000  

CHANNEL_COUNT = 2  
BUFFER_SIZE = 1000   # 1s
eeg_buffer = np.zeros((CHANNEL_COUNT, BUFFER_SIZE))

# serial 設定
ser = serial.Serial("COM3", 9600, timeout=10, write_timeout=10)


WINDOW_SIZE = 5  # 保留window次數


# α / β 比值閾值（需自己微調）
# α/β 大 → 藍色（較放鬆）
# α/β 小 → 紅色（較興奮)

THRESHOLD_FORWARD = 100.0   # 閉眼 / 前進 α power
THRESHOLD_LEFT_RATIO = 0.5  # 紅色 α/β ratio
THRESHOLD_RIGHT_RATIO = 1.5 # 藍色 α/β ratio

THRESHOLD_RED = 50.0     # 12 Hz band power threshold
THRESHOLD_BLUE = 50.0    # 15 Hz band power threshold

# ======== EEG Reading Thread ============

def read_eeg(inlet):
    global eeg_buffer
    while True:
        sample, timestamp = inlet.pull_sample()
        if sample:
            # O1 = 4, O2 = 5
            selected_data = sample[4:6]
            sample_np = np.array(selected_data).reshape(-1, 1)

            eeg_buffer[:, :-1] = eeg_buffer[:, 1:]
            eeg_buffer[:, -1] = sample_np.flatten()


# ======== 建立濾波器 ========

def make_filter(low, high):
    nyq = 0.5 * SAMPLE_RATE
    b, a = butter(2, [low / nyq, high / nyq], btype='band')
    return b, a


#  8–13 Hz → Alpha
b_alpha, a_alpha = make_filter(8, 13)

# 13-30 Hz → Beta
b_beta, a_beta = make_filter(13, 30)

# 12 Hz ± 1 Hz → RED
b_red, a_red = make_filter(11, 13)

# 15 Hz ± 1 Hz → BLUE
b_blue, a_blue = make_filter(14, 16)


# ======== MAIN 控制邏輯 ============
def main():

    global action_window

    print("Realtime Control Started!")
    print("Alpha → Forward")
    
    print("RED(12Hz) → Left")
    print("BLUE(15Hz) → Right")
    

    while True:
        if np.abs(eeg_buffer[0, 0]) < 1e-6:
            time.sleep(0.1)
            continue

        # Filter
        alpha_wave = filtfilt(b_alpha, a_alpha, eeg_buffer, axis=1)
        beta_wave = filtfilt(b_beta, a_beta, eeg_buffer, axis=1)

        red_wave = filtfilt(b_red, a_red, eeg_buffer, axis=1)
        blue_wave = filtfilt(b_blue, a_blue, eeg_buffer, axis=1)

        # Compute power
        alpha_power = np.mean(alpha_wave ** 2)
        beta_power = np.mean(beta_wave ** 2)

        red_power = np.mean(red_wave ** 2)
        blue_power = np.mean(blue_wave ** 2)


        ratio = alpha_power / (beta_power + 1e-6)

        # ====== 四動作判斷 ======

        action = "Stop"

        if ratio < THRESHOLD_LEFT_RATIO: #or red_power > THRESHOLD_RED:
            action = "Left"

        elif ratio > THRESHOLD_RIGHT_RATIO: #or blue_power > THRESHOLD_RED:
            action = "Right"

        elif alpha_power > THRESHOLD_FORWARD:
            action = "Forward"

        else:
            action = "Stop"

        # ====== Sliding window 平滑 ======
        action_window.append(action)
        if len(action_window) > WINDOW_SIZE:
            action_window.pop(0)

        # 取出最多出現的動作
        smooth_action = max(set(action_window), key=action_window.count)

        # ====== Serial 輸出 ======
        counts = {action: action_window.count(action) for action in set(action_window)}
        max_count = counts[smooth_action]

        # 必須超過一半才算有效
        if max_count < len(action_window) / 2:
            smooth_action = "Stop"
            print("no half vote")


        

        if smooth_action == "Forward":
            ser.write(b'1')

        elif smooth_action == "Left":
            ser.write(b'4')

        elif smooth_action == "Right":
            ser.write(b'3')

        elif smooth_action == "Stop":
            ser.write(b'0')

        print(f"Action: {smooth_action} | α={alpha_power:.2f} β={beta_power:.2f} ratio={ratio:.2f}  red={red_power:.2f} blue={blue_power:.2f}")


        time.sleep(0.1999)


# ======== LSL Setup ============

def setup_lsl_inlet(stream_name="Cygnus-083704-RawEEG"):

    print("Resolving streams...")
    streams = resolve_streams()

    if not streams:
        print("No streams found!")
        exit(1)

    for i, s in enumerate(streams):
        print(f"[{i}] {s.name()} - type: {s.type()}")

    target_stream = streams[0]
    for s in streams:
        if s.name() == stream_name:
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
