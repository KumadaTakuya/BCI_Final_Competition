from pylsl import StreamInlet, resolve_streams
import numpy as np
from serial import Serial
from time import sleep
from threading import Thread
from scipy.signal import butter, sosfilt
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

# THRESHOLD_FORWARD = 100.0
# THRESHOLD_LEFT = 0.5
# THRESHOLD_RIGHT = 1.5
# THRESHOLD_BACKWARD = 0.0


def make_filter(low: float, high: float):
    nyq = 0.5 * SAMPLE_RATE
    sos = butter(4, [low/nyq, high/nyq], btype='bandpass', output='sos')
    return sos


# Global Variables
sos_delta = make_filter(0.5, 4)
sos_alpha = make_filter(8, 13)
sos_beta = make_filter(13, 30)
sos_gamma = make_filter(30, 48)

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
    '''
    while True:
        if np.abs(eeg_buffer[0, 0]) < 1e-6:
            sleep(0.1)
            continue

        # Filter
        delta_wave = sosfilt(sos_delta, eeg_buffer, axis=1)
        alpha_wave = sosfilt(sos_alpha, eeg_buffer, axis=1)
        beta_wave  = sosfilt(sos_beta , eeg_buffer, axis=1)
        gamma_wave = sosfilt(sos_gamma, eeg_buffer, axis=1)

        # Compute power
        alpha_power = np.mean(alpha_wave ** 2)  # type: ignore
        gamma_power = np.mean(gamma_wave ** 2)  # type: ignore
        Fp1_power = np.mean(eeg_buffer[0])
        Fp2_power = np.mean(eeg_buffer[1])

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
        counts = {action: actions.count(action) for action in set(actions)}
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

        if smooth_action == "Forward":
            ser.write(b'1')
        elif smooth_action == "Left":
            ser.write(b'4')
        elif smooth_action == "Right":
            ser.write(b'3')
        elif smooth_action == "Backward":
            ser.write(b'2')
        elif smooth_action == "Stop":
            ser.write(b'0')

        print(f"Action: {smooth_action} | alpha={alpha_power:.2f} gamma={gamma_power:.2f}")
        sleep(0.2)
    '''

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CECNL BCI 2023 Car Demo")
    parser.add_argument("port_num", type=str, help="Arduino bluetooth serial port")
    parser.add_argument("EEG_cap_ID", type=str, help="EEG cap ID, 6 numbers")
    args = parser.parse_args()

    ser = Serial(args.port_num, 9600, timeout=10, write_timeout=10)
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
