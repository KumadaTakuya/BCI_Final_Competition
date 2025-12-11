from pylsl import StreamInlet, resolve_streams
import numpy as np
# from serial import Serial
from time import sleep
from threading import Thread


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

eeg_buffer = np.zeros((CHANNEL_COUNT, BUFFER_SIZE))


def setup_lsl_inlet(stream_name: str) -> StreamInlet:
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


def get_band_power(psd, freq_axis, low, high):
    """
    psd: Power Spectral Density (已經平均過頻道的)
    freq_axis: 頻率軸
    low, high: 頻帶範圍
    """

    idx = np.logical_and(freq_axis >= low, freq_axis <= high)
    
    return np.sum(psd[idx])


def main():
    # ======== 預先計算 FFT 相關參數 ========
    # 頻率軸 (0, 1, 2, ..., 500 Hz)
    freqs = np.fft.rfftfreq(BUFFER_SIZE, d=1/SAMPLE_RATE)

    # 窗函數 (Hanning Window)，用於減少頻譜洩漏
    # window = np.hanning(500)
    n = np.arange(BUFFER_SIZE)
    window = 0.5 * (1 - np.cos(np.pi * n / (BUFFER_SIZE - 1)))

    while np.abs(eeg_buffer[0, 0]) < 1e-6:
        sleep(0.1)

    while True:
        # ====== 1. 預處理：去直流 (Demean) 與 加窗 (Windowing) ======
        # 去除 DC offset (平均值)，避免 0Hz 能量過大
        data_detrend = eeg_buffer - np.mean(eeg_buffer, axis=1, keepdims=True)
        # 乘上窗函數
        data_windowed = data_detrend * window

        # ====== 2. FFT 運算 ======
        # Real FFT
        fft_vals = np.fft.rfft(data_windowed, axis=1)
        
        # 計算功率譜 (PSD)
        # 取絕對值(振幅) -> 平方 -> 除以長度(正規化)
        # 這裡簡單用 |FFT|^2 / N 即可代表相對能量強度
        psd = (np.abs(fft_vals) ** 2) / BUFFER_SIZE
        
        # 將頻道的能量平均
        avg_psd = np.mean(psd, axis=0)

        # ====== 3. 提取頻帶能量 ======
        delta_power = get_band_power(avg_psd, freqs,  1,  4)
        alpha_power = get_band_power(avg_psd, freqs,  8, 13)
        beta_power  = get_band_power(avg_psd, freqs, 13, 30)
        gamma_power = get_band_power(avg_psd, freqs, 30, 48)
        # Fp1 & Fp2 power
        Fp1_power = np.mean(np.abs(data_detrend[0]) ** 2)
        Fp2_power = np.mean(np.abs(data_detrend[1]) ** 2)
        O1_power  = np.mean(np.abs(data_detrend[2]) ** 2)
        O2_power  = np.mean(np.abs(data_detrend[3]) ** 2)

        print(f"alpha: {alpha_power:10.0f}, beta: {beta_power:10.0f}, gamma: {gamma_power:10.0f}, delta: {delta_power:10.0f}")
        print(f"Fp1: {Fp1_power:10.0f}, Fp2: {Fp2_power:10.0f}, O1: {O1_power:10.0f}, O2: {O2_power:10.0f}")
        sleep(0.2)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CECNL BCI 2023 Car Demo")
    parser.add_argument("port_num", type=str, help="Arduino bluetooth serial port")
    parser.add_argument("EEG_cap_ID", type=str, help="EEG cap ID, 6 numbers")
    args = parser.parse_args()

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
