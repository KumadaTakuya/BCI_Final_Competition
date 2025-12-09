import tkinter as tk
import threading
import time

class TimeDisplay:
    def __init__(self):
        self.current_time = 0.0
        self.current_mode = "Forward"
        self.window = None
        self.time_label = None
        self.mode_label = None
        self.running = True
        
    def create_window(self):
        """在獨立線程中創建視窗"""
        self.window = tk.Tk()
        self.window.title("時間顯示")
        self.window.geometry("300x200")
        self.window.attributes('-topmost', True)
        
        # 創建模式標籤
        self.mode_label = tk.Label(
            self.window,
            text="Forward",
            font=("Arial", 24, "bold"),
            fg="green"
        )
        self.mode_label.pack(pady=10)
        
        # 創建時間標籤
        self.time_label = tk.Label(
            self.window,
            text="0.0",
            font=("Arial", 40, "bold"),
            fg="blue"
        )
        self.time_label.pack(expand=True)
        
        # 創建說明標籤
        info_label = tk.Label(
            self.window,
            text="秒",
            font=("Arial", 14)
        )
        info_label.pack()
        
        # 設置關閉事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 啟動更新檢查
        self.check_update()
        
        # 啟動視窗主迴圈
        self.window.mainloop()
    
    def check_update(self):
        """定期檢查並更新顯示"""
        if self.time_label and self.mode_label and self.running:
            self.time_label.config(text=f"{self.current_time:.1f}")
            self.mode_label.config(text=self.current_mode)
            self.window.after(50, self.check_update)  # 每 50ms 檢查一次
    
    def update_time(self, new_time):
        """從主程式更新時間"""
        self.current_time = new_time
    
    def update_mode(self, new_mode):
        """從主程式更新模式"""
        self.current_mode = new_mode
    
    def on_closing(self):
        """關閉視窗時的處理"""
        self.running = False
        if self.window:
            self.window.destroy()
    
    def start(self):
        """在獨立線程中啟動視窗"""
        thread = threading.Thread(target=self.create_window, daemon=True)
        thread.start()
        time.sleep(0.5)  # 等待視窗初始化


# ===== 使用範例 =====
if __name__ == "__main__":
    # 創建並啟動顯示視窗
    display = TimeDisplay()
    display.start()
    
    # 你的主程式迴圈
    current_time = 0.0
    current_mode = "Forward"
    
    while True:
        current_time += 0.2
        
        # 更新視窗顯示
        display.update_time(current_time)
        display.update_mode(current_mode)
        
        # === 你的其他功能在這裡 ===
        print(f"執行中... {current_time:.1f}秒 - 模式: {current_mode}")
        
        # 範例：切換模式
        if current_time >= 5.0 and current_mode == "Forward":
            current_mode = "Backward"
        
        # 你的其他 func
        # do_something()
        # process_data()
        # ===========================
        
        time.sleep(0.2)
        
        # 可選：設置停止條件
        if current_time >= 10.0:
            print("達到 10 秒，停止")
            break
    
    print("程式結束")