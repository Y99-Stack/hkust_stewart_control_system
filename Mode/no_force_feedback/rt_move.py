import threading
import time

from Controller.command_message import CommandCodes, CommandMessage, SubCommandCodes
from Controller.dof_controller import DofController
from Controller.ip_setting import IpSetting
from Mode.platform_startup import ensure_platform_ready

try:
	import msvcrt
except ImportError:  # pragma: no cover
	msvcrt = None


TARGET_POSITION_ARRAY: list[list[float]] = [
	[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
	[0.0, 0.0, 0.0, 0.5, 0.0, 0.0],
	[0.0, 0.0, 0.0, 1.0, 0.2, 0.0],
	[0.0, 0.0, 0.0, 1.5, 0.2, 0.2],
	[0.0, 0.0, 0.0, 1.0, 0.0, 0.5],
	[0.0, 0.0, 0.0, 0.5, -0.2, 0.2],
	[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
]

# If needed, change this constant for repeated execution.
LOOP_SEQUENCE = False


def _keyboard_control_worker(
	stop_event: threading.Event,
	state: dict[str, bool],
	enable_control: bool,
) -> None:
	if not enable_control or msvcrt is None:
		return

	print("Keyboard control enabled: Space=pause, C+Space=continue, Q=quit")
	while not stop_event.is_set():
		if not msvcrt.kbhit():
			time.sleep(0.02)
			continue

		key = msvcrt.getwch().lower()
		if key == "q":
			print("Stop requested by keyboard (Q).")
			stop_event.set()
			return

		if key == " ":
			if not state["paused"]:
				state["paused"] = True
				state["continue_armed"] = False
				print("Paused. Press C then Space to continue.")
			elif state["continue_armed"]:
				state["paused"] = False
				state["continue_armed"] = False
				print("Resumed.")
			else:
				print("Still paused. Press C then Space to continue.")
			continue

		if key == "c" and state["paused"]:
			state["continue_armed"] = True
			print("Continue armed. Press Space to resume.")


def run_mode(position_interval: float = 0.1) -> None:
	if position_interval <= 0:
		raise ValueError("position_interval must be positive")

	positions = [list(position) for position in TARGET_POSITION_ARRAY]

	if not positions:
		raise ValueError("target position list is empty")
	for index, dofs in enumerate(positions):
		if len(dofs) != 6:
			raise ValueError(f"Target position at index {index} must contain 6 values")

	controller = DofController(IpSetting())
	stop_event = threading.Event()
	state = {"paused": False, "continue_armed": False}

	keyboard_thread = threading.Thread(
		target=_keyboard_control_worker,
		args=(stop_event, state, True),
		daemon=True,
	)

	try:
		controller.connect()
		ensure_platform_ready(controller)
		keyboard_thread.start()

		sequence_count = 0
		while not stop_event.is_set():
			sequence_count += 1
			print(f"Running position sequence #{sequence_count} ({len(positions)} points)")

			for point_index, dofs in enumerate(positions, start=1):
				if stop_event.is_set():
					break

				while state["paused"] and not stop_event.is_set():
					time.sleep(0.05)

				command = CommandMessage(
					command_code=CommandCodes.CommandMoving,
					sub_command_code=SubCommandCodes.Step,
					dofs=dofs,
				)
				controller.send_command(command)
				print(f"Sent point {point_index}: {dofs}")
				time.sleep(position_interval)

			if not LOOP_SEQUENCE:
				break
	finally:
		stop_event.set()
		if keyboard_thread.is_alive():
			keyboard_thread.join(timeout=0.2)
		controller.dispose()


if __name__ == "__main__":
	run_mode()
