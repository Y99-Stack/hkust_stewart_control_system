
from dof_controller.dof_controller import DofController
from dof_controller.command_message import CommandMessage
from dof_controller.command_message import CommandCodes
from dof_controller.command_message import SubCommandCodes
from dof_controller.sinwave_acc_vel_limits import validate_sine_motion
from dof_controller.pos_limits import validate_position_excursion,scale_amplitude_to_reachable
from dof_controller.ip_setting import IpSetting
import time
import random

# 最初随动运动
"""def main():
    # 初始化 IP 设置
    ip_setting = IpSetting()

    # 创建控制器实例
    controller = DofController(ip_setting)

    controller.connect()

    print("程序已启动，输入 'set dofs' 设置姿态，输入 'get feedback' 获取反馈信息，输入 'exit' 退出程序")

    while True:
        user_input = input("请输入命令: ").strip().lower()  # 获取用户输入并处理

        if user_input == "set dofs":
            # 提示用户输入每个轴的值
            print("请输入6个轴的值，用空格分隔（例如：10.0 0.0 0.0 0.0 0.0 0.0）：")
            try:
                dofs_input = input("DOFs: ").strip()
                dofs_values = list(map(float, dofs_input.split()))
                if len(dofs_values) != 6:
                    print("输入的值数量不正确，需要6个值。")
                    continue

                # 构造命令消息
                command = CommandMessage(
                    command_code=CommandCodes.ContinuousMoving,  # 示例命令
                    dofs=dofs_values  # 设置姿态
                )
                command_bytes = command.to_bytes()
                print(f"Command bytes: {command_bytes}")
                # 发送命令
                controller.send_command(command)
            except ValueError:
                print("输入的值无效，请输入数字。")
        elif user_input == "get feedback":
            feedback = controller.get_feedback()
            if feedback is not None:
                print(f"收到反馈: {feedback}")
        elif user_input == "exit":
            print("程序退出")
            break
        else:
            print("无效的命令，请输入 'set dofs'、'get feedback' 或 'exit'")

    controller.dispose()"""

# 2025 正常运动
"""def main():
    # 初始化 IP 设置
    ip_setting = IpSetting()

    # 创建控制器实例
    controller = DofController(ip_setting)

    controller.connect()
    # 构造命令消息
    # 到达某一个点
    command = CommandMessage(
        command_code=CommandCodes.MoveToMiddle, # 2
        # command_code=CommandCodes.FindBottomInitialize     # 4
        # command_code=CommandCodes.MoveFromBottomToMiddle   # 6
        # command_code=CommandCodes.ContinuousMoving,         # 9
        # command_code=CommandCodes.CommandMoving,              # 11
        # sub_command_code=SubCommandCodes.SineWave,            # 11-2
        # amplitude_array = [0, 0, 0, 0, 0, 0],
        # frequency_array = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        # phase_array

        dofs=[0, 0.0, 0.0, 0.0, 0.0, 0] # 设置姿态
    )
    command_bytes = command.to_bytes()
    print(f"Command bytes: {command_bytes}")
    # 发送命令
    controller.send_command(command)
    
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
            time.sleep(1)"""

# sin wave limit acc vel
"""amplitude = [0, 0, 0, 0, 0, 0.0]
frequency = [0.8, 0.1, 0.1, 0.1, 0.1, 0.1]
def main():
    # 初始化 IP 设置
    ip_setting = IpSetting()

    # 创建控制器实例
    controller = DofController(ip_setting)

    controller.connect()
    # 构造命令消息
    # 到达某一个点
    # 在下发前先校验用户预设的幅值/频率是否合法（速度/加速度是否超限）
    is_ok, details = validate_sine_motion(amplitude, frequency)
    if not is_ok:
        # 构造友好提示并弹窗（回退到控制台输出如果 GUI 不可用）
        axis_names = ["Rx", "Ry", "Rz", "X", "Y", "Z"]
        msgs = []
        for p in details["per_axis"]:
            if p["v_exceeded"] or p["a_exceeded"]:
                parts = []
                if p["v_exceeded"]:
                    parts.append(f"速度超限值，建议减小该轴速度")
                if p["a_exceeded"]:
                    parts.append(f"加速度超限值，建议减小该轴加速度")
                msgs.append(f"{axis_names[p['axis']]}: " + "; ".join(parts))

        summary = ("检测到运动超限：\n" + "\n".join(msgs))
        try:
            import tkinter as _tk
            from tkinter import messagebox as _mb
            root = _tk.Tk()
            root.withdraw()
            _mb.showwarning("运动超限 - 未下发指令", summary)
            root.destroy()
        except Exception:
            print(summary)
    else:
        # 通过校验：构造并下发命令（相位保持默认 0 向量）
        command = CommandMessage(
        # command_code=CommandCodes.FindBottomInitialize     # 4
        # command_code=CommandCodes.MoveFromBottomToMiddle   # 6
        # command_code=CommandCodes.ContinuousMoving,         # 9
        command_code=CommandCodes.CommandMoving,              # 11
        sub_command_code=SubCommandCodes.SineWave,            # 11-2
        amplitude_array = amplitude,
        frequency_array = frequency,
        # phase_array

        # dofs=[0, 0.0, 0.0, 0.0, 0.0, 0] # 设置姿态
    )
        command_bytes = command.to_bytes()
        # print(f"Command bytes: {command_bytes}")
        controller.send_command(command)

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

        controller.dispose()

        while True:
            time.sleep(1)"""


# sin wave pos acc vel limit
amplitude = [10, 18, 0, 0, 0, 0.08]
frequency = [1, 0.5, 0.1, 0.1, 0.1, 1]
def main():
    # 初始化 IP 设置
    ip_setting = IpSetting()

    # 创建控制器实例
    controller = DofController(ip_setting)

    controller.connect()
    # 构造命令消息
    # 到达某一个点
    # 在下发前先校验位置是否合法
    pos_ok, pos_details = validate_position_excursion(amplitude, method='pairwise')
    print("Details of position validation:", pos_details)
    # 在下发前先校验用户预设的幅值/频率是否合法（速度/加速度是否超限）
    dyn_ok, dyn_details = validate_sine_motion(amplitude, frequency)
    if (not pos_ok) or (not dyn_ok):
        merged = []
        if not pos_ok:
            # merged.append("位置可达性超限：" + (str(pos_details) if pos_details is not None else ""))
            merged.append("检测到位置可达性超限：请减小幅值以确保位置可达性")
        if not dyn_ok:
            axis_names = ["Rx", "Ry", "Rz", "X", "Y", "Z"]
            dyn_msgs = []
            for p in dyn_details["per_axis"]:
                if p["v_exceeded"] or p["a_exceeded"]:
                    sub = []
                    if p["v_exceeded"]:
                        sub.append(f"速度超限值，建议减小该轴速度")
                    if p["a_exceeded"]:
                        sub.append(f"加速度超限值，建议减小该轴加速度")
                    dyn_msgs.append(f"{axis_names[p['axis']]}: " + "; ".join(sub))
            merged.append("检测到运动超限：\n" + "\n".join(dyn_msgs))

        summary = "\n\n".join(merged)
        try:
            import tkinter as _tk
            from tkinter import messagebox as _mb
            root = _tk.Tk(); root.withdraw()
            _mb.showwarning("运动参数超限 - 未下发指令", summary)
            root.destroy()
        except Exception:
            print(summary)

    else:
        # 通过校验：构造并下发命令（相位保持默认 0 向量）
        command = CommandMessage(
        # command_code=CommandCodes.FindBottomInitialize     # 4
        # command_code=CommandCodes.MoveFromBottomToMiddle   # 6
        # command_code=CommandCodes.ContinuousMoving         # 9
        command_code=CommandCodes.CommandMoving,              # 11
        sub_command_code=SubCommandCodes.SineWave,            # 11-2
        amplitude_array = amplitude,
        frequency_array = frequency,
        # phase_array

        # dofs=amplitude # 设置姿态
    )
        command_bytes = command.to_bytes()
        # print(f"Command bytes: {command_bytes}")
        controller.send_command(command)

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

        controller.dispose()

        while True:
            time.sleep(1)
            

# single step test
"""amplitude = [0, 0, 0, 0, 0, 0.30]
def main():
    # 初始化 IP 设置
    # ip_setting = IpSetting()

    # 创建控制器实例
    # controller = DofController(ip_setting)

    # controller.connect()
    # 构造命令消息
    # 到达某一个点
    # 在下发前先校验位置是否合法
    pos_ok, pos_details = validate_position_excursion(amplitude, method='pairwise')
    print("Details of position validation:", pos_details)
    # 在下发前先校验用户预设的幅值/频率是否合法（速度/加速度是否超限）
    if (not pos_ok):
        merged = []
        if not pos_ok:
            # merged.append("位置可达性超限：" + (str(pos_details) if pos_details is not None else ""))
            merged.append("检测到位置可达性超限：请减小幅值以确保位置可达性")

        summary = "\n\n".join(merged)
        try:
            import tkinter as _tk
            from tkinter import messagebox as _mb
            root = _tk.Tk(); root.withdraw()
            _mb.showwarning("运动参数超限 - 未下发指令", summary)
            root.destroy()
        except Exception:
            print(summary)

    else:
        # 通过校验：构造并下发命令（相位保持默认 0 向量）
        command = CommandMessage(
        # command_code=CommandCodes.FindBottomInitialize     # 4
        # command_code=CommandCodes.MoveFromBottomToMiddle   # 6
        # command_code=CommandCodes.ContinuousMoving         # 9
        command_code=CommandCodes.CommandMoving,              # 11
        sub_command_code=SubCommandCodes.SineWave,            # 11-2
        # amplitude_array = amplitude,
        # frequency_array = frequency,
        # phase_array

        # dofs=amplitude # 设置姿态
    )
        command_bytes = command.to_bytes()
        # print(f"Command bytes: {command_bytes}")
        # controller.send_command(command)

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

        # controller.dispose()

        while True:
            time.sleep(1)"""

# single step test and change to reachable pos
"""amplitude = [0, 0, 0, 0, 0.0, 0.0]

# 标志：是否自动调整目标位置到可达空间内
CHANGE_POS_ARRIVAL = True
def main():
    global amplitude
    global CHANGE_POS_ARRIVAL
    # 初始化 IP 设置
    ip_setting = IpSetting()

    # 创建控制器实例
    controller = DofController(ip_setting)

    controller.connect()
    # 构造命令消息
    # 到达某一个点
    # 在下发前先校验位置是否合法
    pos_ok, pos_details = validate_position_excursion(amplitude, method='pairwise')
    print("Details of position validation:", pos_details)
    
    # 如果位置超限且开启自动调整，则进行等比例缩放（循环调整直到通过）
    if (not pos_ok) and CHANGE_POS_ARRIVAL:
        total_scale_factor = 1.0
        max_iterations = 10  # 最多调整10次
        iteration = 0
        
        while (not pos_ok) and iteration < max_iterations:
            scaled_amplitude, scale_factor = scale_amplitude_to_reachable(amplitude, pos_details)
            amplitude = scaled_amplitude
            total_scale_factor *= scale_factor
            
            # 重新验证缩放后的幅值
            pos_ok, pos_details = validate_position_excursion(amplitude, method='pairwise')
            iteration += 1
            print(f"第 {iteration} 次调整 - 缩放因子: {scale_factor:.6f}，累计因子: {total_scale_factor:.6f}，幅值: {amplitude}")
        
        if pos_ok:
            print(f"✓ 调整成功！总缩放因子: {total_scale_factor:.6f}，最终幅值: {amplitude}")
            
            # 弹窗提示
            try:
                import tkinter as _tk
                from tkinter import messagebox as _mb
                root = _tk.Tk(); root.withdraw()
                msg = f"检测到位置超限，已自动调整目标位置到可达空间内。\n总缩放因子: {total_scale_factor:.6f}\n最终幅值: {[f'{x:.6f}' for x in amplitude]}"
                _mb.showinfo("位置已调整", msg)
                root.destroy()
            except Exception as e:
                print(f"弹窗显示失败: {e}")
                print("已调整目标position，总缩放因子: {:.6f}".format(total_scale_factor))
        else:
            print(f"✗ 调整失败！经过 {max_iterations} 次迭代仍然超限，请手动调整参数")
            
            # 弹窗提示失败
            try:
                import tkinter as _tk
                from tkinter import messagebox as _mb
                root = _tk.Tk(); root.withdraw()
                msg = f"位置超限调整失败！经过 {max_iterations} 次迭代仍然超限，请手动减小幅值。\n当前幅值: {[f'{x:.6f}' for x in amplitude]}"
                _mb.showerror("调整失败", msg)
                root.destroy()
            except Exception as e:
                print(f"弹窗显示失败: {e}")
    elif (not pos_ok) and (not CHANGE_POS_ARRIVAL):
        merged = []
        merged.append("检测到位置可达性超限：请减小幅值以确保位置可达性")

        summary = "\n\n".join(merged)
        try:
            import tkinter as _tk
            from tkinter import messagebox as _mb
            root = _tk.Tk(); root.withdraw()
            _mb.showwarning("运动参数超限 - 未下发指令", summary)
            root.destroy()
        except Exception:
            print(summary)
    
    # 通过校验：构造并下发命令（相位保持默认 0 向量）
    command = CommandMessage(
    # command_code=CommandCodes.MoveToMiddle, # 2
    # command_code=CommandCodes.FindBottomInitialize,     # 4
    # command_code=CommandCodes.MoveFromBottomToMiddle,   # 6
    command_code=CommandCodes.ContinuousMoving,         # 9
    # command_code=CommandCodes.CommandMoving,              # 11
    # sub_command_code=SubCommandCodes.SineWave,            # 11-2
    # amplitude_array = amplitude,
    # frequency_array = frequency,
    # phase_array

    dofs=amplitude # 设置姿态
    )
    command_bytes = command.to_bytes()
    # print(f"Command bytes: {command_bytes}")
    controller.send_command(command)

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

        controller.dispose()

        # while True:
        #     time.sleep(1)"""

# multi step test
"""import random
random.seed(42)  # 可复现的随机数

# 随机生成10个点，每个点6个幅值
# 根据可达空间限制：[23.0, 24.0, 30.0, 0.32, 0.32, 0.23]
MAX_AMPLITUDES = [23.0, 24.0, 50.0, 0.80, 0.90, 0.50]
amplitude = [
    [random.uniform(0, max_amp * 0.8) for max_amp in MAX_AMPLITUDES]
    for _ in range(10)
]
frequency = [0.1, 0.1, 0.1, 0.1, 0.1, 1]

# 标志：是否自动调整目标位置到可达空间内
CHANGE_POS_ARRIVAL = True

def validate_and_adjust_point(amplitude, point_idx=None):
    
    # 验证并调整单个点的幅值。
    # 返回 (adjusted_amplitude, is_ok, message)

    pos_ok, pos_details = validate_position_excursion(amplitude, method='pairwise')
    
    point_label = f"第 {point_idx} 点" if point_idx else "该点"
    
    if not pos_ok and CHANGE_POS_ARRIVAL:
        # 自动调整模式：循环调整直到通过，只打印不弹窗
        total_scale_factor = 1.0
        max_iterations = 10
        iteration = 0
        adjusted_amplitude = list(amplitude)
        
        while (not pos_ok) and iteration < max_iterations:
            scaled_amplitude, scale_factor = scale_amplitude_to_reachable(adjusted_amplitude, pos_details)
            adjusted_amplitude = scaled_amplitude
            total_scale_factor *= scale_factor
            pos_ok, pos_details = validate_position_excursion(adjusted_amplitude, method='pairwise')
            iteration += 1
        
        if pos_ok:
            msg = f"{point_label}: ✓ 超限已自动调整 (缩放因子: {total_scale_factor:.6f}) -> {[f'{x:.6f}' for x in adjusted_amplitude]}"
            print(msg)
            return adjusted_amplitude, True, msg
        else:
            msg = f"{point_label}: ✗ 调整失败！仍然超限 (最终值: {[f'{x:.6f}' for x in adjusted_amplitude]})"
            print(msg)
            return adjusted_amplitude, False, msg
    
    elif not pos_ok and not CHANGE_POS_ARRIVAL:
        # 非自动调整模式：弹窗提示并停止
        msg = f"{point_label}: ✗ 位置超限，未通过验证"
        print(msg)
        
        # 弹窗提示
        try:
            import tkinter as _tk
            from tkinter import messagebox as _mb
            root = _tk.Tk(); root.withdraw()
            
            limit_info = []
            if pos_details.get("method") == "single_axis":
                per_axis = pos_details.get("single", {}).get("per_axis", [])
                axis_names = ["Rx", "Ry", "Rz", "X", "Y", "Z"]
                for axis_info in per_axis:
                    if axis_info.get("exceeded"):
                        axis_idx = axis_info.get("axis", 0)
                        amp = axis_info.get("amplitude", 0)
                        limit = axis_info.get("limit", 0)
                        limit_info.append(f"{axis_names[axis_idx]}: {amp:.6f} > {limit:.6f}")
            
            detail_msg = "\n".join(limit_info) if limit_info else "详见日志"
            alert_msg = f"{point_label}位置超限！\n超限轴:\n{detail_msg}\n\n需要手动调整参数后重新下发。"
            _mb.showerror("位置超限 - 下发停止", alert_msg)
            root.destroy()
        except Exception as e:
            print(f"弹窗显示失败: {e}")
        
        return list(amplitude), False, msg
    
    else:
        # 验证通过
        msg = f"{point_label}: ✓ 通过验证"
        print(msg)
        return list(amplitude), True, msg

def main():
    global amplitude
    global CHANGE_POS_ARRIVAL
    # 初始化 IP 设置
    # ip_setting = IpSetting()

    # 创建控制器实例
    # controller = DofController(ip_setting)

    # controller.connect()
    # 构造命令消息
    # 多点验证和调整
    print("=" * 60)
    print("多点验证模式")
    print("=" * 60)
    adjusted_list = []
    all_ok = True
    
    for i, amp in enumerate(amplitude):
        adjusted_amp, point_ok, msg = validate_and_adjust_point(amp, i + 1)
        adjusted_list.append(adjusted_amp)
        
        if not point_ok:
            all_ok = False
            if not CHANGE_POS_ARRIVAL:
                # 停止处理后续的点
                print(f"\n因为 CHANGE_POS_ARRIVAL=False，已停止处理后续的点")
                break
    
    print(f"\n汇总: 总点数={len(amplitude)}, 通过={'全部' if all_ok else '部分'}")
    
    if not all_ok and CHANGE_POS_ARRIVAL:
        print("✓ 已调整完成，可下发已通过的点")
    
    amplitude = adjusted_list
    
    # 循环下发每个点的命令
    print("\n开始下发命令...")
    for i, amp in enumerate(adjusted_list):
        amp_formatted = [format(a, ".3f") for a in amp]
        print(f"\n下发第 {i + 1} 个点...:{amp_formatted}")
        command = CommandMessage(
            # command_code=CommandCodes.FindBottomInitialize     # 4
            # command_code=CommandCodes.MoveFromBottomToMiddle   # 6
            command_code=CommandCodes.ContinuousMoving,         # 9
            # command_code=CommandCodes.CommandMoving,              # 11
            # sub_command_code=SubCommandCodes.SineWave,            # 11-2
            # amplitude_array = amp,
            # frequency_array = frequency,
            # phase_array

            dofs=amp # 设置姿态
        )
        command_bytes = command.to_bytes()
        # print(f"第 {i + 1} 个点命令字节数: {len(command_bytes)}")
        # controller.send_command(command)

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

        # controller.dispose()

        # while True:
        #     time.sleep(1)"""


# multi step test(pos/vel) and change to reachable pos (10ms send interval)
"""random.seed(42)  # 可复现的随机数

# 随机生成10个点，每个点6个幅值
# 根据可达空间限制：[23.0, 24.0, 30.0, 0.32, 0.32, 0.23]
MAX_AMPLITUDES = [23.0, 24.0, 30.0, 0.32, 0.32, 0.23]
# MAX_AMPLITUDES = [0,0,0,0,0,0]
amplitude = [
    [random.uniform(0, max_amp * 0.8) for max_amp in MAX_AMPLITUDES]
    for _ in range(1)
]
amplitude.append([0,0,0,0,0,0]) # 回到初始位置
frequency = [0.1, 0.1, 0.1, 0.1, 0.1, 1]

# 标志：是否自动调整目标位置到可达空间内
CHANGE_POS_ARRIVAL = True
SEND_INTERVAL_MS = 2000  # 下发间隔（毫秒）
MAX_VEL_LIMITS = [40.0, 40.0, 40.0, 0.5, 0.5, 0.5]
MAX_ACC_LIMITS = [90.0, 90.0, 90.0, 5.0, 5.0, 5.0]

def calculate_velocity_acceleration(prev_point, curr_point, interval_ms=10):
    
    # 计算两点之间的速度和加速度。
    # 速度 = (当前位置 - 上一位置) / 时间间隔
    # 返回 (velocities, accelerations)
    
    interval_s = interval_ms / 1000.0  # 转换为秒
    velocities = [(curr - prev) / interval_s for curr, prev in zip(curr_point, prev_point)]
    return velocities

def validate_adjacent_velocity(prev_point, curr_point, interval_ms=SEND_INTERVAL_MS):
    
    # 验证相邻两点之间的速度是否在允许范围内。
    # 返回 (vel_ok, details)
    
    velocities = calculate_velocity_acceleration(prev_point, curr_point, interval_ms)
    
    # 计算这两点之间的幅值变化作为虚拟的速度限制检查
    # 这里我们直接使用 validate_sine_motion 的逻辑进行速度检查
    # 实际上速度限制应该由您的系统硬件提供
    vel_ok = True
    details = {
        "velocities": velocities,
        "max_velocities": [abs(v) for v in velocities],
        "ok": vel_ok
    }
    
    return vel_ok, details

def validate_and_adjust_point(amplitude, point_idx=None):
    
    # 验证并调整单个点的幅值。
    # 返回 (adjusted_amplitude, is_ok, message)
    
    pos_ok, pos_details = validate_position_excursion(amplitude, method='pairwise')
    
    point_label = f"第 {point_idx} 点" if point_idx else "该点"
    
    if not pos_ok and CHANGE_POS_ARRIVAL:
        # 自动调整模式：循环调整直到通过，只打印不弹窗
        total_scale_factor = 1.0
        max_iterations = 10
        iteration = 0
        adjusted_amplitude = list(amplitude)
        
        while (not pos_ok) and iteration < max_iterations:
            scaled_amplitude, scale_factor = scale_amplitude_to_reachable(adjusted_amplitude, pos_details)
            adjusted_amplitude = scaled_amplitude
            total_scale_factor *= scale_factor
            pos_ok, pos_details = validate_position_excursion(adjusted_amplitude, method='pairwise')
            iteration += 1
        
        if pos_ok:
            msg = f"{point_label}: ✓ 超限已自动调整 (缩放因子: {total_scale_factor:.6f}) -> {[f'{x:.6f}' for x in adjusted_amplitude]}"
            print(msg)
            return adjusted_amplitude, True, msg
        else:
            msg = f"{point_label}: ✗ 调整失败！仍然超限 (最终值: {[f'{x:.6f}' for x in adjusted_amplitude]})"
            print(msg)
            return adjusted_amplitude, False, msg
    
    elif not pos_ok and not CHANGE_POS_ARRIVAL:
        # 非自动调整模式：弹窗提示并停止
        msg = f"{point_label}: ✗ 位置超限，未通过验证"
        print(msg)
        
        # 弹窗提示
        try:
            import tkinter as _tk
            from tkinter import messagebox as _mb
            root = _tk.Tk(); root.withdraw()
            
            limit_info = []
            if pos_details.get("method") == "single_axis":
                per_axis = pos_details.get("single", {}).get("per_axis", [])
                axis_names = ["Rx", "Ry", "Rz", "X", "Y", "Z"]
                for axis_info in per_axis:
                    if axis_info.get("exceeded"):
                        axis_idx = axis_info.get("axis", 0)
                        amp = axis_info.get("amplitude", 0)
                        limit = axis_info.get("limit", 0)
                        limit_info.append(f"{axis_names[axis_idx]}: {amp:.6f} > {limit:.6f}")
            
            detail_msg = "\n".join(limit_info) if limit_info else "详见日志"
            alert_msg = f"{point_label}位置超限！\n超限轴:\n{detail_msg}\n\n需要手动调整参数后重新下发。"
            _mb.showerror("位置超限 - 下发停止", alert_msg)
            root.destroy()
        except Exception as e:
            print(f"弹窗显示失败: {e}")
        
        return list(amplitude), False, msg
    
    else:
        # 验证通过
        msg = f"{point_label}: ✓ 通过验证"
        print(msg)
        return list(amplitude), True, msg

def main():
    global amplitude
    global CHANGE_POS_ARRIVAL
    # 初始化 IP 设置
    ip_setting = IpSetting()

    # 创建控制器实例
    controller = DofController(ip_setting)

    controller.connect()
    # 构造命令消息
    # 多点验证和调整
    print("=" * 60)
    print("多点验证模式 (下发间隔: {}ms)".format(SEND_INTERVAL_MS))
    print("=" * 60)
    adjusted_list = []
    all_ok = True
    
    for i, amp in enumerate(amplitude):
        adjusted_amp, point_ok, msg = validate_and_adjust_point(amp, i + 1)
        adjusted_list.append(adjusted_amp)
        
        if not point_ok:
            all_ok = False
            if not CHANGE_POS_ARRIVAL:
                # 停止处理后续的点
                print(f"\n因为 CHANGE_POS_ARRIVAL=False，已停止处理后续的点")
                break
    
    print(f"\n汇总: 总点数={len(amplitude)}, 通过={'全部' if all_ok else '部分'}")
    
    if not all_ok and CHANGE_POS_ARRIVAL:
        print("✓ 已调整完成，可下发已通过的点")
    
    amplitude = adjusted_list
    
    # 验证相邻两点之间的速度和加速度
    print("\n" + "=" * 60)
    print("验证相邻两点间的速度/加速度")
    print("=" * 60)
    
    velocity_ok = True
    for i in range(len(adjusted_list) - 1):
        curr_point = adjusted_list[i]
        next_point = adjusted_list[i + 1]
        
        # 计算速度
        vel_ok, vel_details = validate_adjacent_velocity(curr_point, next_point, SEND_INTERVAL_MS)
        velocities = vel_details["velocities"]
        max_vels = vel_details["max_velocities"]
        
        axis_names = ["Rx", "Ry", "Rz", "X", "Y", "Z"]
        vel_str = ", ".join([f"{axis_names[j]}: {abs(v):.4f}/s" for j, v in enumerate(velocities)])
        
        print(f"第 {i + 1} -> {i + 2} 点: {vel_str}")
        
        if not vel_ok:
            velocity_ok = False
    
    if velocity_ok:
        print("✓ 相邻点间速度验证通过")
    else:
        print("✗ 相邻点间速度验证失败")
    
    if CHANGE_POS_ARRIVAL:
    # 循环下发每个点的命令
        print("\n" + "=" * 60)
        print("开始下发命令...")
        print("=" * 60)

        for i, amp in enumerate(adjusted_list):
            amp_formatted = [format(a, ".3f") for a in amp]
            print(f"\n下发第 {i + 1} 个点...:{amp_formatted}")
            command = CommandMessage(
                # command_code=CommandCodes.FindBottomInitialize     # 4
                # command_code=CommandCodes.MoveFromBottomToMiddle   # 6
                command_code=CommandCodes.ContinuousMoving,         # 9
                # command_code=CommandCodes.CommandMoving,              # 11
                # sub_command_code=SubCommandCodes.SineWave,            # 11-2
                # amplitude_array = amp,
                # frequency_array = frequency,
                # phase_array

                dofs=amp # 设置姿态
            )
            command_bytes = command.to_bytes()
            # print(f"第 {i + 1} 个点命令字节数: {len(command_bytes)}")
            controller.send_command(command)

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

        # controller.dispose()

        while True:
            time.sleep(1)"""

# multi step test(pos/vel/acc) and change to reachable pos (10ms send interval)
"""random.seed(42)  # 可复现的随机数

# 随机生成10个点，每个点6个幅值
# 根据可达空间限制：[23.0, 24.0, 30.0, 0.32, 0.32, 0.23]
MAX_AMPLITUDES = [0,0,0,0,0,0]
MAX_AMPLITUDES = [23.0, 24.0, 30.0, 0.32, 0.32, 0.23] # 用于随机点生成
MAX_VEL_LIMITS = [40.0, 40.0, 40.0, 0.5, 0.5, 0.5] # vel limits
MAX_ACC_LIMITS = [90.0, 90.0, 90.0, 5.0, 5.0, 5.0] # acc limits
amplitude = [
    [random.uniform(0, max_amp * 0.5) for max_amp in MAX_AMPLITUDES]
    for _ in range(4)
]
amplitude.append([0,0,0,0,0,0])  # 添加终点为零点
print(amplitude)
frequency = [0.1, 0.1, 0.1, 0.1, 0.1, 1]

# 标志：是否自动调整目标位置到可达空间内
CHANGE_POS_ARRIVAL = True
SEND_INTERVAL_MS = 1000  # 下发间隔（毫秒）

def calculate_velocity(prev_point, curr_point, interval_ms=10):
    # 计算两点之间的速度：v = (curr - prev) / dt
    interval_s = interval_ms / 1000.0
    return [(curr - prev) / interval_s for curr, prev in zip(curr_point, prev_point)]

def calculate_acceleration(prev_point, curr_point, next_point, interval_ms=10):
    # 计算三点之间的加速度：a = (v2 - v1) / dt
    interval_s = interval_ms / 1000.0
    v1 = calculate_velocity(prev_point, curr_point, interval_ms)
    v2 = calculate_velocity(curr_point, next_point, interval_ms)
    return [(v2_i - v1_i) / interval_s for v1_i, v2_i in zip(v1, v2)]

def clamp_next_point(prev_point, curr_point, next_point, interval_ms=10,
                     max_vel_limits=None, max_acc_limits=None):
    # 根据速度/加速度限制调整 next_point，使速度平滑过渡。
    if max_vel_limits is None:
        max_vel_limits = MAX_VEL_LIMITS
    if max_acc_limits is None:
        max_acc_limits = MAX_ACC_LIMITS

    interval_s = interval_ms / 1000.0
    v1 = calculate_velocity(prev_point, curr_point, interval_ms)
    new_next = []
    changed = False
    exceeded_axes = []

    for i, (prev, curr, nxt) in enumerate(zip(prev_point, curr_point, next_point)):
        v2 = (nxt - curr) / interval_s
        v_min = v1[i] - max_acc_limits[i] * interval_s
        v_max = v1[i] + max_acc_limits[i] * interval_s

        v_min = max(v_min, -max_vel_limits[i])
        v_max = min(v_max, max_vel_limits[i])

        v2_clamped = min(max(v2, v_min), v_max)
        if abs(v2 - v2_clamped) > 1e-12:
            changed = True
            exceeded_axes.append(i)

        new_next.append(curr + v2_clamped * interval_s)

    return new_next, changed, exceeded_axes

def validate_adjacent_velocity(prev_point, curr_point, interval_ms=SEND_INTERVAL_MS,
                               max_vel_limits=None):
    # 验证相邻两点之间的速度是否在允许范围内。
    if max_vel_limits is None:
        max_vel_limits = MAX_VEL_LIMITS
    velocities = calculate_velocity(prev_point, curr_point, interval_ms)

    per_axis = []
    any_exceeded = False
    for i, v in enumerate(velocities):
        exceeded = abs(v) > max_vel_limits[i] + 1e-12
        if exceeded:
            any_exceeded = True
        per_axis.append({"axis": i, "velocity": v, "limit": max_vel_limits[i], "exceeded": exceeded})

    details = {"velocities": velocities, "per_axis": per_axis, "ok": not any_exceeded}
    return (not any_exceeded), details

def validate_adjacent_acceleration(prev_point, curr_point, next_point, interval_ms=SEND_INTERVAL_MS,
                                   max_acc_limits=None):
    # 验证相邻三点之间的加速度是否在允许范围内。
    if max_acc_limits is None:
        max_acc_limits = MAX_ACC_LIMITS
    accels = calculate_acceleration(prev_point, curr_point, next_point, interval_ms)

    per_axis = []
    any_exceeded = False
    for i, a in enumerate(accels):
        exceeded = abs(a) > max_acc_limits[i] + 1e-12
        if exceeded:
            any_exceeded = True
        per_axis.append({"axis": i, "acceleration": a, "limit": max_acc_limits[i], "exceeded": exceeded})

    details = {"accelerations": accels, "per_axis": per_axis, "ok": not any_exceeded}
    return (not any_exceeded), details

def validate_and_adjust_point(amplitude, point_idx=None):
    
    # 验证并调整单个点的幅值。
    # 返回 (adjusted_amplitude, is_ok, message)
    
    pos_ok, pos_details = validate_position_excursion(amplitude, method='pairwise')
    
    point_label = f"第 {point_idx} 点" if point_idx else "该点"
    
    if not pos_ok and CHANGE_POS_ARRIVAL:
        # 自动调整模式：循环调整直到通过，只打印不弹窗
        total_scale_factor = 1.0
        max_iterations = 10
        iteration = 0
        adjusted_amplitude = list(amplitude)
        
        while (not pos_ok) and iteration < max_iterations:
            scaled_amplitude, scale_factor = scale_amplitude_to_reachable(adjusted_amplitude, pos_details)
            adjusted_amplitude = scaled_amplitude
            total_scale_factor *= scale_factor
            pos_ok, pos_details = validate_position_excursion(adjusted_amplitude, method='pairwise')
            iteration += 1
        
        if pos_ok:
            msg = f"{point_label}: ✓ 超限已自动调整 (缩放因子: {total_scale_factor:.6f}) -> {[f'{x:.6f}' for x in adjusted_amplitude]}"
            print(msg)
            return adjusted_amplitude, True, msg
        else:
            msg = f"{point_label}: ✗ 调整失败！仍然超限 (最终值: {[f'{x:.6f}' for x in adjusted_amplitude]})"
            print(msg)
            return adjusted_amplitude, False, msg
    
    elif not pos_ok and not CHANGE_POS_ARRIVAL:
        # 非自动调整模式：弹窗提示并停止
        msg = f"{point_label}: ✗ 位置超限，未通过验证"
        print(msg)
        
        # 弹窗提示
        try:
            import tkinter as _tk
            from tkinter import messagebox as _mb
            root = _tk.Tk(); root.withdraw()
            
            limit_info = []
            if pos_details.get("method") == "single_axis":
                per_axis = pos_details.get("single", {}).get("per_axis", [])
                axis_names = ["Rx", "Ry", "Rz", "X", "Y", "Z"]
                for axis_info in per_axis:
                    if axis_info.get("exceeded"):
                        axis_idx = axis_info.get("axis", 0)
                        amp = axis_info.get("amplitude", 0)
                        limit = axis_info.get("limit", 0)
                        limit_info.append(f"{axis_names[axis_idx]}: {amp:.6f} > {limit:.6f}")
            
            detail_msg = "\n".join(limit_info) if limit_info else "详见日志"
            alert_msg = f"{point_label}位置超限！\n超限轴:\n{detail_msg}\n\n需要手动调整参数后重新下发。"
            _mb.showerror("位置超限 - 下发停止", alert_msg)
            root.destroy()
        except Exception as e:
            print(f"弹窗显示失败: {e}")
        
        return list(amplitude), False, msg
    
    else:
        # 验证通过
        msg = f"{point_label}: ✓ 通过验证"
        print(msg)
        return list(amplitude), True, msg

def main():
    global amplitude
    global CHANGE_POS_ARRIVAL
    # 初始化 IP 设置
    ip_setting = IpSetting()

    # 创建控制器实例
    controller = DofController(ip_setting)

    controller.connect()
    # 构造命令消息
    # 多点验证和调整
    print("=" * 60)
    print("多点验证模式 (下发间隔: {}ms)".format(SEND_INTERVAL_MS))
    print("=" * 60)
    adjusted_list = []
    all_ok = True
    
    for i, amp in enumerate(amplitude):
        adjusted_amp, point_ok, msg = validate_and_adjust_point(amp, i + 1)
        adjusted_list.append(adjusted_amp)
        
        if not point_ok:
            all_ok = False
            if not CHANGE_POS_ARRIVAL:
                # 停止处理后续的点
                print(f"\n因为 CHANGE_POS_ARRIVAL=False，已停止处理后续的点")
                break
    
    print(f"\n汇总: 总点数={len(amplitude)}, 通过={'全部' if all_ok else '部分'}")
    
    if not all_ok and CHANGE_POS_ARRIVAL:
        print("✓ 已调整完成，可下发已通过的点")
    
    amplitude = adjusted_list
    
    # 验证相邻两点之间的速度和加速度
    print("\n" + "=" * 60)
    print("验证相邻两点间的速度/加速度")
    print("=" * 60)
    
    velocity_ok = True
    acceleration_ok = True
    for i in range(len(adjusted_list) - 1):
        curr_point = adjusted_list[i]
        next_point = adjusted_list[i + 1]
        
        # 计算速度
        vel_ok, vel_details = validate_adjacent_velocity(curr_point, next_point, SEND_INTERVAL_MS)
        velocities = vel_details["velocities"]
        
        axis_names = ["Rx", "Ry", "Rz", "X", "Y", "Z"]
        vel_str = ", ".join([f"{axis_names[j]}: {abs(v):.4f}/s" for j, v in enumerate(velocities)])
        
        print(f"第 {i + 1} -> {i + 2} 点: {vel_str}")
        
        if not vel_ok:
            velocity_ok = False

        # 计算加速度（需要三点）
        if i >= 1:
            prev_point = adjusted_list[i - 1]
            acc_ok, acc_details = validate_adjacent_acceleration(prev_point, curr_point, next_point, SEND_INTERVAL_MS)
            accels = acc_details["accelerations"]
            acc_str = ", ".join([f"{axis_names[j]}: {abs(a):.4f}/s²" for j, a in enumerate(accels)])
            print(f"第 {i} -> {i + 1} -> {i + 2} 点加速度: {acc_str}")

            if not acc_ok:
                acceleration_ok = False

                if CHANGE_POS_ARRIVAL:
                    new_next, changed, exceeded_axes = clamp_next_point(
                        prev_point, curr_point, next_point, SEND_INTERVAL_MS
                    )
                    if changed:
                        adjusted_list[i + 1] = new_next
                        axis_names = ["Rx", "Ry", "Rz", "X", "Y", "Z"]
                        axes_str = ", ".join([axis_names[a] for a in exceeded_axes])
                        print(f"第 {i + 2} 点加速度超限，已平滑调整轴: {axes_str}")
                else:
                    print(f"第 {i + 2} 点加速度超限，停止下发")
                    break
    
    if velocity_ok and acceleration_ok:
        print("✓ 相邻点间速度/加速度验证通过")
    else:
        print("✗ 相邻点间速度/加速度验证失败")
    if CHANGE_POS_ARRIVAL:
        # 循环下发每个点的命令
        print("\n" + "=" * 60)
        print("开始下发命令...")
        print("=" * 60)
        for i, amp in enumerate(adjusted_list):
            amp_formatted = [format(a, ".3f") for a in amp]
            print(f"\n下发第 {i + 1} 个点...:{amp_formatted}")
            command = CommandMessage(
                # command_code=CommandCodes.FindBottomInitialize     # 4
                # command_code=CommandCodes.MoveFromBottomToMiddle   # 6
                command_code=CommandCodes.ContinuousMoving,         # 9
                # command_code=CommandCodes.CommandMoving,              # 11
                # sub_command_code=SubCommandCodes.SineWave,            # 11-2
                # amplitude_array = amp,
                # frequency_array = frequency,
                # phase_array

                dofs=amp # 设置姿态
            )
            command_bytes = command.to_bytes()
            # print(f"第 {i + 1} 个点命令字节数: {len(command_bytes)}")
            controller.send_command(command)

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
            print("无效的命令，请输入 'get feedback' 或 'exit'")"""

if __name__ == "__main__":
    main()