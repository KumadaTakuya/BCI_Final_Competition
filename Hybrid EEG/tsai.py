from pylsl import StreamInlet, resolve_streams
import numpy as np
from serial import Serial
from time import sleep
from threading import Thread
# from scipy.signal import butter, sosfilt
from typing import Tuple


"""
Signals                                                 | Usage
1. Close eyes : Alpha power                             | Forward
2. Blink      : Fp1 and Fp2 large positive              | Left
3. Move eyes  : Opposing waveform at F7/Fp1 and F8/Fp2  | Right
4. Chew       : High frequency, large                   | Backward
5. Move tongue: Delta power                             |

Bands
0.5-4 Hz → Delta
8-13 Hz → Alpha
13-30 Hz → Beta
30-48 Hz → Gamma
"""

SAMPLE_RATE = 1000
FP1 = 0
FP2 = 1
O1 = 4
O2 = 5

CHANNEL_COUNT = 4
BUFFER_SIZE = 1000  # 1s
ACTION_BUFFER_SIZE = 5

THRESHOLD_FORWARD = 100.0
THRESHOLD_LEFT = 0.5
THRESHOLD_RIGHT = 1.5
THRESHOLD_BACKWARD = 0.0


# ======== 預先計算 FFT 相關參數 ========
# 頻率軸 (0, 1, 2, ..., 500 Hz)
freqs = np.fft.rfftfreq(BUFFER_SIZE, d=1/SAMPLE_RATE)

# 窗函數 (Hanning Window)，用於減少頻譜洩漏
# 形狀需為 (1, BUFFER_SIZE) 以便與 eeg_buffer (2, BUFFER_SIZE) 相乘
window = np.hanning(BUFFER_SIZE).reshape(1, -1)


# ======== get_band_power ========
def get_band_power(psd, freq_axis, low, high):
    """
    psd: Power Spectral Density (已經平均過頻道的)
    freq_axis: 頻率軸
    low, high: 頻帶範圍
    """

    idx = np.logical_and(freq_axis >= low, freq_axis <= high)
    
    return np.sum(psd[idx])

eeg_buffer = np.zeros((CHANNEL_COUNT, BUFFER_SIZE))


def setup_lsl_inlet(stream_name="") -> StreamInlet:
    print("Resolving streams...")
    streams = resolve_streams()
    if not streams:
        print("No streams found!")
        exit(1)

    for i, s in enumerate(streams):
        print(f"[{i}] {s.name()} - type: {s.type()}")

    target_stream = None
    for s in streams:
        if s.name() == stream_name:
            target_stream = s
            break
    if target_stream is None:
        print(stream_name, "does not exist")
        exit(1)
    print(f"Connecting to {target_stream.name()} ...")

    return StreamInlet(target_stream)


def read_eeg(inlet: StreamInlet):
    global eeg_buffer
    while True:
        sample, timestamp = inlet.pull_sample()
        if sample:
            selected_data = [sample[FP1], sample[FP2], sample[O1], sample[O2]]
            sample_np = np.array(selected_data).reshape(-1)

            eeg_buffer[:, :-1] = eeg_buffer[:, 1:]
            eeg_buffer[:, -1] = sample_np


def main():
    print("Real-time Control Started!")
    print("Normal    : Stop")
    print("Close eyes: Forward")
    print("Blink     : Left")
    print("Chew      : Right")
    print("Move eyes : Backward")

    actions = []
    real_time_eeg = []
    
    while True:
        if np.abs(eeg_buffer[0, 0]) < 1e-6:
            sleep(0.1)
            continue

       
        data_detrend = eeg_buffer - np.mean(eeg_buffer, axis=1, keepdims=True)
        data_windowed = data_detrend * window
        fft_vals = np.fft.rfft(data_windowed, axis=1)
        psd = (np.abs(fft_vals) ** 2) / BUFFER_SIZE

        #print(f"psd.shape {psd.shape}")
        

        # 將兩個頻道的能量平均 (O1 和 O2 平均)
        avg_psd = np.mean(psd, axis=0)

        # ====== 3. 提取頻帶能量 ======
        # psd[2:4] (O1 和 O2 平均)
        alpha_power = get_band_power(np.mean(psd[2:4, :], axis=0), freqs, 8, 13)
        beta_power  = get_band_power(avg_psd, freqs, 13, 30)
        gamma_power  = get_band_power(avg_psd, freqs, 30, 48)
        


        # Compute power
        sz = 500
        Fp1_power = np.sqrt(np.mean(eeg_buffer[FP1] ** 2))
        Fp2_power = np.sqrt(np.mean(eeg_buffer[FP2] ** 2))


        # Determine action
        action = "Stop"
        if alpha_power < THRESHOLD_FORWARD:
            action = "Forward"
        elif Fp1_power * Fp2_power > THRESHOLD_LEFT:
            action = "Left"
        elif Fp1_power * Fp2_power < THRESHOLD_RIGHT:
            action = "Right"
        elif gamma_power > THRESHOLD_BACKWARD:
            action = "Backward"

        # Sliding window smoothing
        actions.append(action)
        if len(actions) > ACTION_BUFFER_SIZE:
            actions.pop(0)

        # Action appear most & its count
        counts = [(action, actions.count(action)) for action in set(actions)]
        smooth_action = "Stop"
        action_count = 0
        for action, cnt in counts:
            if cnt > action_count:
                smooth_action = action
                action_count = cnt

        # Determine output
        if action_count < len(actions) // 2:
            smooth_action = "Stop"
            print("Votes < 50% -> Stop")

        # if smooth_action == "Forward":
        #     ser.write(b'1')
        # elif smooth_action == "Left":
        #     ser.write(b'4')
        # elif smooth_action == "Right":
        #     ser.write(b'3')
        # elif smooth_action == "Backward":
        #     ser.write(b'2')
        # elif smooth_action == "Stop":
        #     ser.write(b'0')

        print(f"Action: {smooth_action} | alpha={alpha_power:.2f} gamma={gamma_power:.2f} Fp1: {Fp1_power:.2f} Fp2: {Fp2_power:.2f}")
        sleep(0.2)
    

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CECNL BCI 2023 Car Demo")
    parser.add_argument("port_num", type=str, help="Arduino bluetooth serial port")
    parser.add_argument("EEG_cap_ID", type=str, help="EEG cap ID, 6 numbers")
    args = parser.parse_args()

    # ser = Serial(args.port_num, 9600, timeout=10, write_timeout=10)
    # inlet = setup_lsl_inlet("Cygnus-083746-RawEEG")
    inlet = setup_lsl_inlet(f"Cygnus-{args.EEG_cap_ID}-RawEEG")

    thread1 = Thread(target=read_eeg, args=(inlet,), daemon=True)
    thread1.start()

    print("Start a thread to read EEG ...")
    sleep(2)

    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        exit(0)
