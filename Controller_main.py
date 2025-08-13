
from Controller.dof_controller import DofController
from Controller.command_message import CommandMessage
from Controller.command_message import CommandCodes
from Controller.command_message import SubCommandCodes
from Controller.feedback_message import FeedbackMessage
from Controller.ip_setting import IpSetting
import time
import csv

# 20250227 随行运动正确版

def main():
    # 初始化 IP 设置
    ip_setting = IpSetting()

    # 创建控制器实例
    controller = DofController(ip_setting)

    controller.connect()
    # 构造命令消息
    # 到达某一个点
    command = CommandMessage(
        # command_code=CommandCodes.FindBottomInitialize     # 4
        # command_code=CommandCodes.MoveFromBottomToMiddle   # 6
        command_code=CommandCodes.ContinuousMoving         # 9
        dofs = [] # dofs TODO: Control algorithm output
        # command_code=CommandCodes.CommandMoving,              # 11
        # amplitude_array = [0, 0, 0, 0, 0, 0],
        # frequency_array = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        # phase_array

        # dofs=[10, 0.0, 0.0, 0.0, 0.0, 0] # 设置姿态
    )
    command_bytes = command.to_bytes()
    print(f"Command bytes: {command_bytes}")
    # 发送命令
    controller.send_command(command)
    feedback = controller.get_feedback()
    dof_feedback = feedback.AttitudesArray # get the real time posistion
    print("程序已启动，输入 'get feedback' 获取反馈信息，输入 'exit' 退出程序")

    while True:
        user_input = input("请输入命令: ").strip().lower()  # 获取用户输入并处理

        if user_input == "get feedback":
            feedback = controller.get_feedback()
            if feedback is not None:
                print(f"收到反馈: {feedback}")
        elif user_input == "exit":
            print("程序退出")
            break
        else:
            print("无效的命令，请输入 'get feedback' 或 'exit'")

        #controller.dispose()

        while True:
            time.sleep(1)




if __name__ == "__main__":
    main()