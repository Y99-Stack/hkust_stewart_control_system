from collections.abc import Sequence

from Controller.command_message import CommandCodes, CommandMessage
from Controller.dof_controller import DofController
from Controller.ip_setting import IpSetting
from Mode.platform_startup import ensure_platform_ready
from limits.pos_milits import scale_amplitude_to_reachable, validate_position_excursion


def _adjust_to_reachable(target: Sequence[float], max_iterations: int = 10) -> tuple[list[float], bool, float]:
    target_adj = list(target)
    pos_ok, pos_details = validate_position_excursion(target_adj, method="pairwise")
    total_scale = 1.0
    iteration = 0

    while (not pos_ok) and iteration < max_iterations:
        target_adj, scale_factor = scale_amplitude_to_reachable(target_adj, pos_details)
        total_scale *= scale_factor
        pos_ok, pos_details = validate_position_excursion(target_adj, method="pairwise")
        iteration += 1

    return target_adj, pos_ok, total_scale


def run_mode(
    target_dofs: Sequence[float] | None = None,
    speed: Sequence[float] | None = None,
) -> None:
    target = list(target_dofs) if target_dofs is not None else [0.0] * 6
    speed_array = list(speed) if speed is not None else None
    if len(target) != 6:
        raise ValueError("target_dofs must contain 6 values")
    if speed_array is not None and len(speed_array) != 6:
        raise ValueError("speed must contain 6 values when provided")

    target, reachable, scale = _adjust_to_reachable(target)
    if not reachable:
        raise ValueError("target_dofs exceeds reachable workspace and auto-adjustment failed")
    if scale < 0.999999:
        print("[LIMIT] Point target exceeded reachable workspace and was auto-adjusted.")
        print(f"[LIMIT] scale={scale:.6f}, adjusted_target={target}")

    controller = DofController(IpSetting())
    try:
        controller.connect()
        ensure_platform_ready(controller)
        command = CommandMessage(
            command_code=CommandCodes.ContinuousMoving,
            dofs=target,
            speed=speed_array,
        )
        controller.send_command(command)
        print(f"Point command sent. target_dofs={target}")
        print("Commands: 'get feedback' | 'set dofs' | 'exit'")

        while True:
            try:
                user_input = input(">> ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting point_move mode.")
                break

            if user_input == "get feedback":
                feedback = controller.get_feedback()
                if feedback is not None:
                    print(f"feedback.AttitudesArray={feedback.AttitudesArray}")
                else:
                    print("No feedback received.")

            elif user_input == "set dofs":
                print("Enter 6 DOF values separated by spaces (pitch roll yaw lateral longitudinal vertical):")
                try:
                    raw = input("DOFs: ").strip()
                    new_dofs = list(map(float, raw.split()))
                    if len(new_dofs) != 6:
                        print(f"Expected 6 values, got {len(new_dofs)}. Ignored.")
                        continue
                    new_dofs, reachable, scale = _adjust_to_reachable(new_dofs)
                    if not reachable:
                        print("[LIMIT] New target exceeds reachable workspace and could not be auto-adjusted. Ignored.")
                        continue
                    if scale < 0.999999:
                        print("[LIMIT] Input target exceeded workspace and was auto-adjusted.")
                        print(f"[LIMIT] scale={scale:.6f}, adjusted_target={new_dofs}")
                    new_cmd = CommandMessage(
                        command_code=CommandCodes.ContinuousMoving,
                        dofs=new_dofs,
                        speed=speed_array,
                    )
                    controller.send_command(new_cmd)
                    target = new_dofs
                    print(f"New target sent: {target}")
                except ValueError:
                    print("Invalid input. Please enter numbers only.")

            elif user_input == "exit":
                print("Exiting point_move mode.")
                break

            else:
                print("Unknown command. Use: 'get feedback' | 'set dofs' | 'exit'")
    finally:
        controller.dispose()


if __name__ == "__main__":
    run_mode()