import socket
import threading
import time
from typing import Optional
from .ip_setting import IpSetting
from .feedback_message import FeedbackMessage
from .command_message import CommandMessage

class DofController:
    """platfrom controller"""
#     def __init__(self):
#         self._socket_lock = threading.Lock()
#         self._socket: Optional[socket.socket] = None
#         self._local_endpoint = ("192.168.0.131", 10000)  # 上位机 IP 和端口
#         self._remote_endpoint = ("192.168.0.125", 5000)  # 下位机 IP 和端口

#         self.is_connect_disabled = False
#         self.is_auto_connect_enabled = True
#         self.is_connecting = False
#         self.is_connected = False
#         self.connect_message = ""

#         self._no_feedback_time = 0
#         self._connection_broken_timer = threading.Timer(0.1, self._check_connection)
#         self._connection_broken_timer.start()

#         self._feedback_thread = threading.Thread(target=self._get_feedback_message, daemon=True)
#         self._feedback_thread.start()

#     def start_connecting(self):
#         """启动连接过程"""
#         if self.is_connect_disabled:
#             print("连接已手动关闭，无法启动连接")
#             return

#         self.is_connected = False
#         self.is_connecting = True
#         self.connect_message = "正在连接"
#         print(self.connect_message)

#     def connect(self):
#         """尝试连接到下位机"""
#         with self._socket_lock:
#             if self._socket:
#                 self._socket.close()
#                 print("关闭现有连接")

#             self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#             try:
#                 self._socket.bind(self._local_endpoint)
#                 self._socket.settimeout(0.5)  # 设置超时时间
#                 self.is_connected = True
#                 self.connect_message = "连接成功"
#                 print(self.connect_message)
#             except Exception as e:
#                 self.is_connected = False
#                 self.connect_message = f"连接失败: {e}"
#                 print(self.connect_message)

#     def send_command_message(self, command_message: bytes):
#         """发送命令消息"""
#         if not self.is_connected:
#             print("未连接到下位机，无法发送命令")
#             return

#         with self._socket_lock:
#             try:
#                 self._socket.sendto(command_message, self._remote_endpoint)
#                 print("命令已发送")
#             except Exception as e:
#                 print(f"发送命令失败: {e}")

#     def _get_feedback_message(self):
#         """接收反馈消息"""
#         while True:
#             try:
#                 if not self.is_connected and not self.is_auto_connect_enabled or self.is_connect_disabled:
#                     print("未连接且未启用自动连接，等待重新连接...")
#                     time.sleep(1)
#                     continue

#                 if not self.is_connected:
#                     print("尝试重新连接...")
#                     self.connect()

#                 data, _ = self._socket.recvfrom(200)  # 接收数据
#                 if data[0] != 55:  # 检查数据包标识
#                     raise ValueError("无效的数据包")

#                 # 处理反馈消息
#                 feedback_message = FeedbackMessage.from_bytes(data)
#                 self.is_connected = True
#                 print(f"收到反馈: {feedback_message}")
#                 self._no_feedback_time = 0  # 重置未收到反馈的时间

#             except socket.timeout:
#                 print("连接超时，未收到下位机反馈")
#                 self._no_feedback_time += 500
#                 if self._no_feedback_time >= 500:
#                     self.is_connected = False
#                     self.connect_message = "连接断开"
#                     print(self.connect_message)

#             except Exception as e:
#                 print(f"接收反馈消息出错: {e}")
#                 self.is_connected = False
#                 self.connect_message = "连接断开"
#             time.sleep(1)


#     def _check_connection(self):
#         """检测连接是否断开"""
        
#         self._no_feedback_time += 100

#         if self._no_feedback_time >= 500 and self.is_connected:
#             print("通信超时,判定断线")
#             self.is_connected = False

#         self._connection_broken_timer = threading.Timer(0.1, self._check_connection)
#         self._connection_broken_timer.start()


#     def dispose(self):
#         """释放资源"""
#         with self._socket_lock:
#             if self._socket:
#                 self._socket.close()
#             self._connection_broken_timer.cancel()
#             self.is_connected = False
#             self.is_connecting = False
#             self.is_connect_disabled = True
#             self.is_auto_connect_enabled = False
#             print("资源已释放")

#     @property
#     def is_connected(self):
#         return self._is_connected

#     @is_connected.setter
#     def is_connected(self, value):
#         self._is_connected = value
#         print(f"连接状态: {value}")
   
    def __init__(self, ip_setting: IpSetting):
        self._socket_lock = threading.Lock()
        self.ip_settings = ip_setting
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._is_connected = False
        # self._feedback_thread = threading.Thread(target=self._receive_feedback, daemon=True)
        # self._feedback_thread.start()

    def connect(self):
        try:
            self._socket.bind((self.ip_settings.local_ip, self.ip_settings.local_port))
            self._socket.settimeout(0.5)
            self._is_connected = True
            print(f"连接成功: 本地 {self.ip_settings.local_ip}:{self.ip_settings.local_port} -> 远程 {self.ip_settings.remote_ip}:{self.ip_settings.remote_port}")
        except Exception as e:
            self._is_connected = False
            print(f"连接失败: {e}")

    def disconnect(self):
        """断开连接"""
        if self._is_connected:
            self._socket.close()
            self._is_connected = False
            print("连接已断开")

    def send_command(self, command_message: CommandMessage):
        if not self._is_connected:
            print("未连接到下位机，请检查 IP 和端口设置")
            return

        try:
            command_bytes = command_message.to_bytes()
            if not command_bytes:
                print("命令数据打包失败")
                return
            self._socket.sendto(command_bytes, (self.ip_settings.remote_ip, self.ip_settings.remote_port))
            # print(f"命令已发送")
            # 打印每个参数的值
            # print(f"Id: {command_message.Id}")
            # print(f"CommandCode: {command_message.CommandCode.value}")
            # print(f"SubCommandCode: {command_message.SubCommandCode.value}")
            # print(f"ScriptFileIndex: {command_message.ScriptFileIndex}")
            # print(f"DO: {command_message.DO}")
            # print(f"CyChoose: {command_message.CyChoose}")
            # print(f"JogSpeed: {command_message.JogSpeed}")
            # print(f"Send DOFs: {command_message.DOFs}")
            # print(f"AmplitudeArray: {command_message.AmplitudeArray}")
            # print(f"FrequencyArray: {command_message.FrequencyArray}")
            # print(f"PhaseArray: {command_message.PhaseArray}")
            # print(f"DestinationPosition: {command_message.DestinationPosition}")
            # print(f"Speed: {command_message.Speed}")
            # print(f"Vxyz: {command_message.Vxyz}")
            # print(f"Axyz: {command_message.Axyz}")
            # print(f"Timestamp: {command_message.Timestamp}")
        except Exception as e:
            print(f"发送命令失败: {e}")

    # def _receive_feedback(self):
    #     """接收反馈消息"""
    #     while True:
    #         try:
    #             data, _ = self._socket.recvfrom(200)
    #             feedback = FeedbackMessage.from_bytes(data)
    #             self._is_connected = True
    #             print(f"接收到的数据大小: {len(data)} 字节")
    #             print(f"收到反馈: {feedback}")
    #         except socket.timeout:
    #             #self._is_connected = False
    #             print("连接超时，未收到下位机反馈")
    #         except Exception as e:
    #             print(f"接收反馈出错: {e}")
    #             #self._is_connected = False
    #         time.sleep(10) # 10s update
    def get_feedback(self):
        """按需接收反馈消息"""
        try:
            data, _ = self._socket.recvfrom(200)
            feedback = FeedbackMessage.from_bytes(data)
            self._is_connected = True
            # print(f"接收到的数据大小: {len(data)} 字节")
            #print(f"收到反馈: {feedback}")
            # print(f"收到的dofs:{feedback.AttitudesArray}")
            return feedback
        except socket.timeout:
            print("连接超时，未收到下位机反馈")
            return None
        except Exception as e:
            print(f"接收反馈消息出错: {e}")
            self._is_connected = False
            return None

    def dispose(self):
        """释放资源"""
        
        with self._socket_lock:
            if self._socket:
                self._socket.close()
            self.is_connected = False
            self.is_connecting = False
            self.is_connect_disabled = True
            self.is_auto_connect_enabled = False
            print("资源已释放")