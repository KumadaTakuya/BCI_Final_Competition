# SSVEP车辆控制系统 - 快速开始指南

## 快速开始

### 1. 安装依赖
```bash
cd SSVEP
pip install -r requirements.txt
```

### 2. 运行程序
```bash
# 基本用法（必须指定串口号）
python main.py COM3

# 完整选项示例
python main.py COM3 \
    --stream-name "Cygnus-083704-RawEEG" \
    --threshold 0.3 \
    --update-interval 0.2 \
    --debounce 0.1 \
    --buffer-wait 2.0
```

## 频率映射

| 频率 (Hz) | 动作 | 命令 |
|----------|------|------|
| 6.0      | forward (前进) | b'1' |
| 7.5      | left (左转) | b'3' |
| 8.57     | right (右转) | b'4' |
| 10.0     | backward (后退) | b'2' |

## 参数调整建议

### CCA阈值 (--threshold)
- **默认值**: 0.3
- **调整建议**:
  - 如果检测不灵敏（很少触发），**降低**阈值（如 0.2）
  - 如果误检太多（频繁触发），**提高**阈值（如 0.4-0.5）
  - 建议范围: 0.2 - 0.6

### 更新间隔 (--update-interval)
- **默认值**: 0.2 秒
- **调整建议**:
  - 更快的响应：0.1 秒
  - 更稳定的控制：0.3-0.5 秒
  - 建议范围: 0.1 - 0.5 秒

### 防抖时间 (--debounce)
- **默认值**: 0.0 秒（不使用防抖）
- **调整建议**:
  - 如果动作切换过快：0.1-0.3 秒
  - 如果需要更稳定的控制：0.2-0.5 秒
  - 建议范围: 0.0 - 0.5 秒

## 常见问题

### Q: 如何知道当前检测到的频率？
A: 程序会实时显示所有频率的CCA得分，例如：
```
Action: forward  | Scores: [forward:0.452, left:0.123, right:0.089, backward:0.067]
```

### Q: 如何调整频率映射？
A: 修改 `main.py` 中的 `DEFAULT_CONFIG` 或使用配置文件：
```python
"frequencies": [6.0, 7.5, 8.57, 10.0],
"frequency_labels": ["forward", "left", "right", "backward"],
```

### Q: 如何添加更多传感器（陀螺仪/EMG）？
A: 在 `data_fusion.py` 中实现相应的融合方法，然后在 `main.py` 中调用。

### Q: 程序无法找到LSL流？
A: 
1. 确保LSL流正在运行
2. 检查流名称是否正确：`--stream-name "你的流名称"`
3. 运行程序时会列出所有可用的流，检查是否有你的流

### Q: 串口连接失败？
A:
1. 检查串口号是否正确（Windows: COM3, Linux: /dev/ttyUSB0）
2. 确保车辆已连接
3. 检查是否有其他程序占用串口
4. 尝试以管理员权限运行

## 测试建议

1. **先测试EEG读取**：确保能正常读取EEG数据
2. **再测试分类器**：使用 `example_usage.py` 测试SSVEP分类
3. **最后测试完整系统**：连接车辆并运行完整程序

## 下一步

- 查看 `NOTE/README.md` 了解详细文档
- 查看 `example_usage.py` 了解各模块的使用方法
- 根据实际情况调整参数以获得最佳性能

