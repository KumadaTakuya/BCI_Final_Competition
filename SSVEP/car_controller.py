"""
車輛控制模組 / Car Control Module
負責接收動作字串並發送串口指令到車輛 / Responsible for receiving action strings and sending serial port commands to the car
"""
import serial
import time


class CarController:
    """車輛控制器 / Car Controller"""
    
    # 動作到命令的映射 / Action to command mapping
    ACTION_COMMANDS = {
        "forward": b'1',
        "backward": b'2',
        "left": b'3',
        "right": b'4',
        "stop": b'0'
    }
    
    def __init__(self, port=None, baudrate=9600, timeout=10, write_timeout=10):
        """
        初始化車輛控制器 / Initialize Car Controller
        
        Args:
            port: 串口號（如 "COM3"），如果為None則需要後續調用connect()時指定 / Serial port (e.g., "COM3"), if None, must be specified when calling connect()
            baudrate: 波特率，預設9600 / Baud rate, default 9600
            timeout: 讀取超時時間（秒） / Read timeout (seconds)
            write_timeout: 寫入超時時間（秒） / Write timeout (seconds)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self.ser = None
        self.is_connected = False
    
    def connect(self, port=None):
        """
        連接到車輛串口 / Connect to car serial port
        
        Args:
            port: 串口號，如果提供則覆蓋初始化時的port / Serial port, if provided, overrides the port set during initialization
        
        Returns:
            bool: 連接是否成功 / Whether connection was successful
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
        """斷開串口連接 / Disconnect serial port"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.is_connected = False
            print("Disconnected from car")
    
    def send_action(self, action):
        """
        發送動作指令到車輛 / Send action command to car
        
        Args:
            action: 動作字串 ("forward", "backward", "left", "right", "stop") / Action string ("forward", "backward", "left", "right", "stop")
        
        Returns:
            bool: 發送是否成功 / Whether sending was successful
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
        """上下文管理器入口 / Context manager entry"""
        if self.port:
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口 / Context manager exit"""
        self.disconnect()

