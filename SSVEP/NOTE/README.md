# SSVEP车辆控制系统说明文档

## 项目结构

```
SSVEP/
├── eeg_reader.py          # EEG读取模块
├── ssvep_classifier.py    # SSVEP分类器模块（使用CCA方法）
├── car_controller.py      # 车辆控制模块
├── data_fusion.py         # 数据融合模块（为未来扩展准备）
├── main.py                # 主程序
├── requirements.txt        # 依赖包列表
└── NOTE/                  # 笔记和文档
    └── README.md          # 本文件
```

## 模块说明

### 1. eeg_reader.py - EEG读取模块
- **功能**: 从LSL流中读取EEG数据并维护滚动缓冲区
- **输入**: LSL流（通过stream_name指定）
- **输出**: numpy array，shape = (n_channels, buffer_size)
- **主要类**: `EEGReader`
- **关键方法**:
  - `setup_lsl_inlet()`: 设置LSL输入流
  - `start_reading()`: 开始后台读取线程
  - `get_buffer()`: 获取当前EEG缓冲区数据
  - `is_buffer_ready()`: 检查缓冲区是否准备好

### 2. ssvep_classifier.py - SSVEP分类器模块
- **功能**: 使用CCA（典型相关分析）方法检测SSVEP频率并判断动作
- **输入**: EEG数据 (numpy array)
- **输出**: 动作字符串 ("forward", "backward", "left", "right", "stop")
- **主要类**: `SSVEPClassifier`
- **关键方法**:
  - `classify(eeg_data)`: 分类并返回动作字符串
  - `classify_with_scores(eeg_data)`: 分类并返回动作和所有频率的得分
  - `set_threshold(threshold)`: 设置CCA阈值
- **默认频率映射**:
  - 6.0 Hz → "forward" (前进)
  - 7.5 Hz → "left" (左转)
  - 8.57 Hz → "right" (右转)
  - 10.0 Hz → "backward" (后退)

### 3. car_controller.py - 车辆控制模块
- **功能**: 接收动作字符串并发送串口指令到车辆
- **输入**: 动作字符串
- **输出**: 串口命令（字节）
- **主要类**: `CarController`
- **关键方法**:
  - `connect(port)`: 连接到车辆串口
  - `send_action(action)`: 发送动作指令
  - `disconnect()`: 断开连接
- **动作到命令映射**:
  - "forward" → b'1'
  - "backward" → b'2'
  - "left" → b'3'
  - "right" → b'4'
  - "stop" → b'0'

### 4. data_fusion.py - 数据融合模块
- **功能**: 为未来扩展准备，可以融合多种传感器数据
- **当前状态**: 仅传递EEG数据（占位符）
- **未来扩展**: 可以添加陀螺仪、EMG等传感器数据融合
- **主要类**: `DataFusion`
- **关键方法**:
  - `fuse(eeg_data)`: 融合数据（当前仅返回EEG）
  - `add_gyroscope(gyro_data)`: 添加陀螺仪数据（待实现）
  - `add_emg(emg_data)`: 添加EMG数据（待实现）

### 5. main.py - 主程序
- **功能**: 整合所有模块，实现完整的SSVEP车辆控制系统
- **使用方式**: 
  ```bash
  python main.py COM3 [选项]
  ```

## 使用方法

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行程序
```bash
# 基本用法（必须指定串口号）
python main.py COM3

# 完整选项
python main.py COM3 \
    --stream-name "Cygnus-083704-RawEEG" \
    --threshold 0.3 \
    --update-interval 0.2 \
    --debounce 0.0 \
    --buffer-wait 2.0
```

### 3. 命令行参数说明
- `port` (必需): 串口号，如 COM3
- `--stream-name`: LSL流名称（默认: "Cygnus-083704-RawEEG"）
- `--threshold`: CCA阈值（默认: 0.3）
- `--update-interval`: 更新间隔，秒（默认: 0.2）
- `--debounce`: 防抖时间，秒（默认: 0.0，即不使用防抖）
- `--buffer-wait`: 缓冲区等待时间，秒（默认: 2.0）

## 配置参数

### 默认配置（在main.py中）
- **采样率**: 1000 Hz
- **缓冲区大小**: 3000 samples (3秒)
- **EEG通道**: [4, 5] (对应channel 4-6)
- **SSVEP频率**: [6.0, 7.5, 8.57, 10.0] Hz
- **谐波数量**: 2 (基频和二次谐波)
- **波特率**: 9600

## 未来扩展建议

### 1. 添加陀螺仪数据
在 `data_fusion.py` 中实现 `_fuse_gyro()` 方法，可以：
- 检测头部运动
- 辅助判断用户意图
- 提高控制精度

### 2. 添加EMG数据
在 `data_fusion.py` 中实现 `_fuse_emg()` 方法，可以：
- 检测肌肉活动
- 作为额外的控制信号
- 提高系统鲁棒性

### 3. 优化CCA算法
- 尝试不同的谐波数量
- 调整参考信号生成方式
- 添加自适应阈值

### 4. 添加可视化
- 实时显示EEG波形
- 显示各频率的CCA得分
- 显示当前动作状态

## 注意事项

1. **LSL流**: 确保LSL流正在运行，并且stream_name正确
2. **串口连接**: 确保车辆已连接，并且串口号正确
3. **缓冲区**: 系统需要2秒时间填充缓冲区，请耐心等待
4. **阈值调整**: 根据实际情况调整CCA阈值，过高可能无法检测，过低可能误检
5. **防抖设置**: 如果动作切换过快，可以增加防抖时间

## 故障排除

### 问题1: 找不到LSL流
- 检查LSL流是否正在运行
- 使用 `--stream-name` 参数指定正确的流名称
- 检查流名称是否与代码中的默认值匹配

### 问题2: 串口连接失败
- 检查串口号是否正确（Windows: COM3, Linux: /dev/ttyUSB0等）
- 检查车辆是否已连接
- 检查是否有其他程序占用串口

### 问题3: 检测不准确
- 调整 `--threshold` 参数
- 检查SSVEP刺激频率是否与代码中的频率匹配
- 确保用户正确注视对应的视觉刺激

### 问题4: 动作切换过快
- 增加 `--debounce` 参数值
- 增加 `--update-interval` 参数值

