
from Controller.dof_controller import DofController
from Controller.command_message import CommandMessage
from Controller.command_message import CommandCodes
from Controller.command_message import SubCommandCodes
from Controller.feedback_message import FeedbackMessage
from Controller.ip_setting import IpSetting
import time
import csv

# 20250227 validated follow-motion script version

def main():
    # Initialize IP settings.
    ip_setting = IpSetting()

    # Create the platform controller client.
    controller = DofController(ip_setting)

    controller.connect()
    # Build a command message.
    # Example goal: move to one target point.
    command = CommandMessage(
        # command_code=CommandCodes.FindBottomInitialize     # 4
        # command_code=CommandCodes.MoveFromBottomToMiddle   # 6
        command_code=CommandCodes.ContinuousMoving         # 9
        dofs = [] # dofs TODO: Control algorithm output
        # command_code=CommandCodes.CommandMoving,              # 11
        # amplitude_array = [0, 0, 0, 0, 0, 0],
        # frequency_array = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        # phase_array

        # dofs=[10, 0.0, 0.0, 0.0, 0.0, 0] # Set target pose.
    )
    command_bytes = command.to_bytes()
    print(f"Command bytes: {command_bytes}")
    # Send command to platform controller.
    controller.send_command(command)
    feedback = controller.get_feedback()
    dof_feedback = feedback.AttitudesArray # get the real time posistion
    print("Program started. Enter 'get feedback' for feedback, or 'exit' to quit.")

    while True:
        user_input = input("Enter command: ").strip().lower()  # Read and normalize user input.

        if user_input == "get feedback":
            feedback = controller.get_feedback()
            if feedback is not None:
                print(f"Received feedback: {feedback}")
        elif user_input == "exit":
            print("Program exited")
            break
        else:
            print("Invalid command. Enter 'get feedback' or 'exit'.")

        #controller.dispose()

        while True:
            time.sleep(1)




if __name__ == "__main__":
    main()