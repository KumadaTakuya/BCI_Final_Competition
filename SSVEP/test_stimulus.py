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
    print("  Left (左轉) - 綠色方塊 / Green square")
    print("  Forward (前進) - 紅色方塊 / Red square")
    print("  Right (右轉) - 藍色方塊 / Blue square")
    print("\n使用說明 / Instructions:")
    print("  - 注視其中一個閃爍方塊 / Focus on one flickering square")
    print("  - 按ESC鍵退出 / Press ESC to exit")
    print("=" * 60)
    print("\n啟動視覺刺激窗口... / Starting visual stimulus window...\n")
    
    # 創建刺激生成器 / Create stimulus generator
    # 三個方塊：Left, Forward, Right / Three squares: Left, Forward, Right
    stimulus = SSVEPStimulus(
        frequencies=[7.5, 6.0, 8.57],  # Left, Forward, Right
        labels=["Left", "Forward", "Right"],
        window_size=(1200, 800),
        stimulus_size=200
    )
    
    # 自定義位置：並排從左到右 / Custom positions: side by side from left to right
    center_x, center_y = 1200 // 2, 800 // 2
    spacing = 300  # 方塊之間的間距 / Spacing between squares
    stimulus.positions = [
        (center_x - spacing, center_y),  # Left (左) - 綠色
        (center_x, center_y),            # Forward (中) - 紅色
        (center_x + spacing, center_y),   # Right (右) - 藍色
    ]
    
    # 自定義顏色：綠色、紅色、藍色 / Custom colors: Green, Red, Blue
    stimulus.COLORS = [
        (100, 255, 100),  # 綠色 / Green - Left
        (255, 100, 100),  # 紅色 / Red - Forward
        (100, 100, 255),  # 藍色 / Blue - Right
    ]
    
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

