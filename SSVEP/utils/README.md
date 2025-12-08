# Utils 模組說明 / Utils Module Documentation

## 鍵盤控制模組 / Keyboard Controller Module

### 功能 / Features
- 使用WASD鍵盤控制車輛 / Use WASD keyboard to control car
- 適合用於demo和測試 / Suitable for demo and testing
- 在console顯示當前動作 / Display current action on console

### 獨立使用 / Standalone Usage

```bash
# 直接運行鍵盤控制demo / Run keyboard control demo directly
python utils/keyboard_controller.py COM3

# 指定更新間隔 / Specify update interval
python utils/keyboard_controller.py COM3 --update-interval 0.1
```

### 控制說明 / Controls
- **W** - 前進 (Forward)
- **S** - 後退 (Backward)
- **A** - 左轉 (Left)
- **D** - 右轉 (Right)
- **無按鍵** - 停止 (Stop)
- **Ctrl+C** - 退出 (Exit)

### 在主程式中使用 / Use in Main Program

```bash
# 使用鍵盤控制模式 / Use keyboard control mode
python main.py COM3 --input-mode keyboard

# 使用EEG控制模式（預設） / Use EEG control mode (default)
python main.py COM3 --input-mode eeg
```

