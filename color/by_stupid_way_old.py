from pylsl import StreamInlet, resolve_streams
import numpy as np
import time
import threading
import serial
import mode_display as MD

# ======== adjust para ==============
IF_SERIAL = True
ADJ_SPD = False

# Fp1=0, Fp2=1, O1=4, O2=5
CHANNEL_IDX = [4, 5]

CHANNEL_COUNT = len(CHANNEL_IDX)

ACTION_WINDOW_SIZE = 5  # 保留window次數 size=5 ---> 1s

mode_keep_time = 5.0 # ---> 5s


# ======== speed adjust =========

## S ---> forward, T ---> rota
## ori speedS = 10, speedT = 10
 # if speedS > 10 still keep 10, speedS < 0 still keep 0, same rules on speedT

add_speedS = -8
add_speedT = -8


# ======== threshold ========
THRESHOLD_FORWARD = 10000.0   #  α power



#  ======== serial 設定 ========
if IF_SERIAL:
    ser = serial.Serial("COM12", 9600, timeout=10, write_timeout=10)




# ======== background setting =========

SAMPLE_RATE = 1000
BUFFER_SIZE = 1000   # 1s 
eeg_buffer = np.zeros((CHANNEL_COUNT, BUFFER_SIZE))

action_window = []




# ======== FFT use ========
# 頻率軸 (0, 1, 2, ..., 500 Hz)
freqs = np.fft.rfftfreq(BUFFER_SIZE, d=1/SAMPLE_RATE)

# 窗函數 (Hanning Window)，用於減少頻譜洩漏
# fft_window (1, BUFFER_SIZE) 以便與 
# eeg_buffer (n_channel, BUFFER_SIZE) 相乘
fft_window = np.hanning(BUFFER_SIZE).reshape(1, -1)



# ======== EEG Reading Thread ============
def read_eeg(inlet):
    global eeg_buffer

    while True:
        sample, timestamp = inlet.pull_sample()

        if sample:
            sample_np = np.array(sample)
            selected_data = sample_np[CHANNEL_IDX]
            selected_data_np = np.array(selected_data).reshape(-1, 1)

            # 更新 Buffer (FIFO)
            eeg_buffer[:, :-1] = eeg_buffer[:, 1:]
            eeg_buffer[:, -1] = selected_data_np.flatten()



# ======== get_band_power ========
def get_band_power(psd, low, high):
    """
    psd             : after channel ave
    low, high       : 頻帶範圍
    """
    global freqs
    idx = np.logical_and(freqs >= low, freqs <= high)
    
    return np.sum(psd[idx])



# ======== adjust_speed ========


def adj(add_speed, add_order, minus_order):

    if add_speed > 0:
        adj_order = add_order
    else:
        adj_order = minus_order

    for i in range(np.abs(add_speed)):
        ser.write(adj_order)
        time.sleep(0.2)


    # back to stop
    ser.write(b'0')
    time.sleep(0.2)


def adjust_speed():
    """
    ## speedS ---> forward, speedT ---> rota
    ## ori speedS = 10, speedT = 10

    b'5' --> speedS+1
    b'6' --> speedS-1
    b'7' --> speedT+1
    b'8' --> speedT-1

    """

    print("Start adjust speed, ori speedS = 10, speedT = 10")

    print("if speedS > 10 still keep 10, speedS < 0 still keep 0, same rules on speedT")

    global add_speedS
    global add_speedT
    
    adj(add_speedS, add_order = b'5', minus_order = b'6')
    adj(add_speedT, add_order = b'7', minus_order = b'8')

    print(f"add_speedS: {add_speedS} | add_speedT: {add_speedT}")
    

    # if speedS > 10 still keep 10, speedS < 0 still keep 0, same rules on speedT

    spS = np.clip(10 + add_speedS, 0, 10)
    spT = np.clip(10 + add_speedT, 0, 10)

    print(f"Final:  speedS: {spS} |  speedT: {spT}")

    
def reset_speed():
    """
    ## speedS ---> forward, speedT ---> rota
    ## ori speedS = 10, speedT = 10

    b'5' --> speedS+1
    b'6' --> speedS-1
    b'7' --> speedT+1
    b'8' --> speedT-1

    """

    print("reset_speed speedS = 10, speedT = 10")

    print("if speedS > 10 still keep 10, speedS < 0 still keep 0, same rules on speedT")

    global add_speedS
    global add_speedT
    
    adj(-add_speedS, add_order = b'5', minus_order = b'6')
    adj(-add_speedT, add_order = b'7', minus_order = b'8')

    print(f"add_speedS: {-add_speedS} | add_speedT: {-add_speedT}")
    
    print(f"Reset finish")



    

DISCRETE = 0



# ======== MAIN  ============
def main():
    global action_window
    global DISCRETE

    print("Realtime Control Started! (FFT Mode)")
    print("Alpha (8-13Hz)")
    


    display = MD.TimeDisplay()
    display.start()

    mode_list = ["Forward", "Left", "Right"]
    mode_color_list = ["#00ff15", "#ff0000", "#ffff00"]
    current_mode = "Forward"
    current_color = "#04d616"

    current_time = 0.0
    total_mode_time = len(mode_list) * float(mode_keep_time)


    if IF_SERIAL:
        if ADJ_SPD:
            adjust_speed()

    
    while True:

        if np.abs(eeg_buffer[0, 0]) < 1e-6:
            print("debug")
            time.sleep(0.1)
            continue

        if DISCRETE >= 3:
            DISCRETE = 0
            for i in range(5):
                ser.write(b'0')
                time.sleep(0.2)


        # ====== 0. mode display ======

        md_idx = int(current_time // mode_keep_time)

        current_mode = mode_list[md_idx]
        current_color = mode_color_list[md_idx]


        display.update_time(current_time)
        display.update_mode(current_mode, current_color)


        # ====== 1. preprocess ======

        # 去除 DC offset (平均值)，避免 0Hz 能量過大
        data_detrend = eeg_buffer - np.mean(eeg_buffer, axis=1, keepdims=True)

        # Windowing
        data_windowed = data_detrend * fft_window


        # ====== 2. FFT  ======
        # rfft: Real FFT (只計算正頻率部分)
        fft_vals = np.fft.rfft(data_windowed, axis=1)
        
        # 計算功率譜 (PSD)
        # 取絕對值(振幅) -> 平方 -> 除以長度(正規化)
        # 這裡簡單用 |FFT|^2 / N 即可代表相對能量強度
        psd = (np.abs(fft_vals) ** 2) / BUFFER_SIZE
        
        #  O1, O2 ave
        avg_psd = np.mean(psd, axis=0)




        # ====== 3. get_band_power ======
        alpha_power = get_band_power(avg_psd, 8, 13)
        


        # ====== 4. action ======
        action = "Stop"

        if alpha_power > THRESHOLD_FORWARD:
            action = current_mode

        else:
            action = "Stop"



        # ====== 5. Sliding window ======
        action_window.append(action)

        if len(action_window) > ACTION_WINDOW_SIZE:
            action_window.pop(0)

        smooth_action = max(set(action_window), key=action_window.count)

        smooth_action_counts = action_window.count(smooth_action)
        

        if smooth_action_counts < len(action_window) / 2:
            print(f"{smooth_action} no half vote")
            smooth_action = "Stop"


        # ====== 6. Serial output ======
        
        if IF_SERIAL:

            if smooth_action == "Forward": 
                ser.write(b'1')
            elif smooth_action == "Left": 
                ser.write(b'3')
            elif smooth_action == "Right": 
                ser.write(b'4')
                
            elif smooth_action == "Stop": 
                ser.write(b'0')
        

        print(f"Act: {smooth_action} | α={alpha_power:.1f} | DISCRETE={DISCRETE}")



        # ====== 7. time adjust ======

        current_time += 0.2

        if smooth_action == current_mode:
            current_time -= 0.2
            DISCRETE += 1

        
        if current_time >= total_mode_time:
            current_time -= total_mode_time


        time.sleep(0.2)


# ======== LSL Setup  ============

def setup_lsl_inlet(stream_name="Cygnus-083704-RawEEG"):

    print("Resolving streams...")
    streams = resolve_streams()

    if not streams:
        print("No streams found!")
        exit(1)

    for i, s in enumerate(streams):
        print(f"[{i}] {s.name()} - type: {s.type()}")


    # 嘗試尋找指定名稱，找不到就用第一個
    target_stream = streams[0]
    
    for s in streams:
        if stream_name in s.name(): # partial match 
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