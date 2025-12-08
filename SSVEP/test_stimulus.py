"""
SSVEP視覺刺激測試腳本 / SSVEP Visual Stimulus Test Script
用於測試SSVEP閃爍窗口是否正常工作 / For testing if SSVEP flickering window works correctly
"""
import sys
import os

# 添加utils目錄到路徑 / Add utils directory to path
utils_path = os.path.join(os.path.dirname(__file__), 'utils')
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)

from ssvep_stimulus import SSVEPStimulus


def main():
    """測試SSVEP視覺刺激窗口 / Test SSVEP visual stimulus window"""
    print("=" * 60)
    print("SSVEP Visual Stimulus Test")
    print("=" * 60)
    print("\n這個程序會顯示一個包含4個閃爍方塊的窗口")
    print("This program will display a window with 4 flickering squares")
    print("\n頻率對應 / Frequency Mapping:")
    print("  6.0 Hz  - Forward (前進) - 紅色方塊 / Red square")
    print("  7.5 Hz  - Left (左轉) - 綠色方塊 / Green square")
    print("  8.57 Hz - Right (右轉) - 藍色方塊 / Blue square")
    print("  10.0 Hz - Backward (後退) - 黃色方塊 / Yellow square")
    print("\n使用說明 / Instructions:")
    print("  - 注視其中一個閃爍方塊 / Focus on one flickering square")
    print("  - 按ESC鍵退出 / Press ESC to exit")
    print("=" * 60)
    print("\n啟動視覺刺激窗口... / Starting visual stimulus window...\n")
    
    # 創建刺激生成器 / Create stimulus generator
    # 使用與main.py相同的頻率設置 / Use same frequency settings as main.py
    stimulus = SSVEPStimulus(
        frequencies=[6.0, 7.5, 8.57, 10.0],
        labels=["Forward", "Left", "Right", "Backward"],
        window_size=(1200, 800),
        stimulus_size=200
    )
    
    # 運行視覺刺激 / Run visual stimulus
    try:
        stimulus.run(target_fps=120)
    except KeyboardInterrupt:
        print("\n\n測試中斷 / Test interrupted.")
    except Exception as e:
        print(f"\n錯誤 / Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n測試完成 / Test completed.")


if __name__ == "__main__":
    main()

