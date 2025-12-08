"""
鍵盤讀取模組 / Keyboard Reader Module
使用WASD鍵盤讀取輸入並轉換為動作 / Use WASD keyboard to read input and convert to actions
適合用於demo和測試 / Suitable for demo and testing
"""
import keyboard
import time


class KeyboardReader:
    """鍵盤讀取器 / Keyboard Reader"""
    
    # 按鍵到動作的映射 / Key to action mapping
    KEY_ACTIONS = {
        'w': "forward",
        's': "backward",
        'a': "left",
        'd': "right"
    }
    
    def __init__(self, update_interval=0.2):
        """
        初始化鍵盤讀取器 / Initialize Keyboard Reader
        
        Args:
            update_interval: 更新間隔（秒） / Update interval (seconds)
        """
        self.update_interval = update_interval
        self.is_running = False
    
    def get_action(self):
        """
        獲取當前按鍵對應的動作 / Get action corresponding to current key press
        
        Returns:
            str: 動作字串 ("forward", "backward", "left", "right", "stop") / Action string
        """
        # 檢查WASD按鍵 / Check WASD keys
        for key, action in self.KEY_ACTIONS.items():
            if keyboard.is_pressed(key):
                return action
        
        # 沒有按鍵被按下，返回停止 / No key pressed, return stop
        return "stop"
    
    def run_demo(self, car_controller):
        """
        運行鍵盤控制demo / Run keyboard control demo
        直接控制車輛並在console顯示狀態 / Directly control car and display status on console
        
        Args:
            car_controller: 車輛控制器實例 / CarController instance
        """
        if not car_controller.is_connected:
            print("Error: Car not connected. Please connect first.")
            return
        
        self.is_running = True
        print("\n" + "=" * 50)
        print("Keyboard Control Demo")
        print("=" * 50)
        print("Controls:")
        print("  W - Forward (前進)")
        print("  S - Backward (後退)")
        print("  A - Left (左轉)")
        print("  D - Right (右轉)")
        print("  (No key) - Stop (停止)")
        print("  Press Ctrl+C to exit")
        print("=" * 50 + "\n")
        
        try:
            while self.is_running and car_controller.is_connected:
                # 獲取當前動作 / Get current action
                action = self.get_action()
                
                # 發送指令到車輛 / Send command to car
                car_controller.send_action(action)
                
                # 在console顯示狀態 / Display status on console
                action_display = {
                    "forward": "前進 (Forward)",
                    "backward": "後退 (Backward)",
                    "left": "左轉 (Left)",
                    "right": "右轉 (Right)",
                    "stop": "停止 (Stop)"
                }
                
                print(f"\r當前動作 / Current Action: {action_display.get(action, action):20s}", end="", flush=True)
                
                # 等待下一次更新 / Wait for next update
                time.sleep(self.update_interval)
        
        except KeyboardInterrupt:
            print("\n\nStopping keyboard control...")
        
        finally:
            # 停止車輛 / Stop car
            car_controller.send_action("stop")
            print("\r" + " " * 50 + "\r", end="", flush=True)
            print("Keyboard control stopped.")
            self.is_running = False
    
    def stop(self):
        """停止鍵盤讀取 / Stop keyboard reading"""
        self.is_running = False


def main():
    """獨立運行鍵盤控制demo / Standalone keyboard control demo"""
    import argparse
    import sys
    import os
    
    # 添加父目錄到路徑以便導入car_controller / Add parent directory to path to import car_controller
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from car_controller import CarController
    
    parser = argparse.ArgumentParser(description="Keyboard Control Demo for Car")
    parser.add_argument("port", type=str, help="Serial port for car (e.g., COM3)")
    parser.add_argument("--update-interval", type=float, default=0.2,
                        help="Update interval in seconds (default: 0.2)")
    
    args = parser.parse_args()
    
    # 初始化車輛控制器 / Initialize car controller
    print("Initializing car controller...")
    car_controller = CarController(port=args.port, baudrate=9600)
    
    if not car_controller.connect():
        print("Failed to connect to car. Exiting...")
        sys.exit(1)
    
    # 初始化鍵盤讀取器 / Initialize keyboard reader
    keyboard_reader = KeyboardReader(update_interval=args.update_interval)
    
    # 運行demo / Run demo
    keyboard_reader.run_demo(car_controller)
    
    # 斷開連接 / Disconnect
    car_controller.disconnect()
    print("Demo completed.")


if __name__ == "__main__":
    main()

