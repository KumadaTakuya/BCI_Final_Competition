"""
车辆控制模块
负责接收动作字符串并发送串口指令到车辆
"""
import serial
import time


class CarController:
    """车辆控制器"""
    
    # 动作到命令的映射
    ACTION_COMMANDS = {
        "forward": b'1',
        "backward": b'2',
        "left": b'3',
        "right": b'4',
        "stop": b'0'
    }
    
    def __init__(self, port=None, baudrate=9600, timeout=10, write_timeout=10):
        """
        初始化车辆控制器
        
        Args:
            port: 串口号（如 "COM3"），如果为None则需要后续调用connect()时指定
            baudrate: 波特率，默认9600
            timeout: 读取超时时间（秒）
            write_timeout: 写入超时时间（秒）
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.ser = None
        self.is_connected = False
    
    def connect(self, port=None):
        """
        连接到车辆串口
        
        Args:
            port: 串口号，如果提供则覆盖初始化时的port
        
        Returns:
            bool: 连接是否成功
        """
        if port is not None:
            self.port = port
        
        if self.port is None:
            raise ValueError("Serial port must be specified")
        
        try:
            self.ser = serial.Serial(
                self.port, 
                self.baudrate, 
                timeout=self.timeout, 
                write_timeout=self.write_timeout
            )
            self.is_connected = True
            print(f"Connected to car at {self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to car: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """断开串口连接"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.is_connected = False
            print("Disconnected from car")
    
    def send_action(self, action):
        """
        发送动作指令到车辆
        
        Args:
            action: 动作字符串 ("forward", "backward", "left", "right", "stop")
        
        Returns:
            bool: 发送是否成功
        """
        if not self.is_connected or self.ser is None or not self.ser.is_open:
            print("Warning: Car not connected. Cannot send action.")
            return False
        
        if action not in self.ACTION_COMMANDS:
            print(f"Warning: Unknown action '{action}'. Valid actions: {list(self.ACTION_COMMANDS.keys())}")
            return False
        
        try:
            command = self.ACTION_COMMANDS[action]
            self.ser.write(command)
            return True
        except Exception as e:
            print(f"Error sending action to car: {e}")
            return False
    
    def __enter__(self):
        """上下文管理器入口"""
        if self.port:
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()

