from Controller.dof_controller import DofController
from ForceSensor.ati_mini85 import ATIMini85
from ForceSensor.control_algorithm import ControlAlgorithm
from Controller.ip_setting import IpSetting
from Controller.command_message import CommandMessage, CommandCodes
from ForceSensor.visualization import RealTimePlot, SingleAxisMonitor

import numpy as np
import time
import threading
from queue import Queue
from pyqtgraph import QtWidgets
import sys
import os
import csv

# Configurations
CONTROL_CYCLE = 0.01  
FORCE_SAMPLE_CYCLE = 0.001  
FORCE_SAMPLE_RATE = 1000
SAMPLE_CHUNK = 10      # number of samples to read each time (10 samples = 10ms at 1000Hz)
SAVE_DATA_CYCLE = 0.01

# 0414 No visualization no filter 6 axis write to csv
"""
class ControlSystem:
    def __init__(self):
        ip_setting =IpSetting()
        self.robot = DofController(ip_setting)
        self.force_sensor = ATIMini85()
        # init control algorithm parameters
        M = np.diag([1]*6)
        D = np.diag([5]*6)
        K = np.diag([100]*6)
        self.control_algorithm = ControlAlgorithm(M, D, K, CONTROL_CYCLE)

        # share data between threads
        self.force_queue = Queue()
        self.position_queue = Queue()
        # Synchronous event
        self.force_event = threading.Event()
        self.position_event = threading.Event()
        self.force_thread = None
        self.control_thread = None
        self.exit_event = threading.Event()
        self.is_running = False

        self.last_avg = np.zeros(6)
        # init filter
        self.filter_window = 10
        self.filter_buffer = np.zeros((self.filter_window,6))

        # Save data
        self.data = []
        self.data_file_path = "data/control_data1.csv"
        self.data_counter = 0
        self.data_interval = 10  
        self.last_save_time = time.time()


    def force_acquisition(self):
        # Force data acquisition thread: read data from sensor and put into queue
        self.force_sensor.start(sampling_rate=FORCE_SAMPLE_RATE)
        self.force_sensor.calibrate_zero()
        try:
            while not self.exit_event.is_set():
                forces = self.force_sensor.get_calibrated_forces(num_samples=SAMPLE_CHUNK) # forces shape: [SAMPLE_CHUNK, 6 channels]
                forces[:,:3], forces[:,3:] = forces[:,3:], forces[:,:3]
                # 1. slide average filter
                # if len(self.filter_buffer) >= self.filter_window:
                #     self.filter_buffer.pop(0)
                # self.filter_buffer.append(forces)
                # averaged_forces = np.mean(self.filter_buffer, axis=0)[-1]
                # real time low pass
                # current_avg = np.mean(forces, axis=0)
                # averaged_forces = 0.2*current_avg + 0.8*self.last_avg  # TODO: change the paramete coefficient
                # self.last_avg = averaged_forces

                if not self.force_queue.full():
                    # self.force_queue.put(averaged_forces) # forces[-1] Get the newest sample TODO: maybe use the average of the last 10 samples to avoid noise
                    self.force_queue.put(forces[-1])
                    self.force_event.set()
                else:
                    print("Warning: Force data queue is full. Force data may be lost.")
                time.sleep(FORCE_SAMPLE_CYCLE) # Small sleep to prevent CPU overload
        finally:
            self.force_sensor.stop()
            print("Force sensor acquisition thread stopped!")

    def control_loop(self):
        # Main Control Thread
        self.robot.connect() # Connect to the platform controller
        last_control_time = time.time()

        try:
            while not self.exit_event.is_set():
                # Synchronous control cycle
                current_time = time.time()
                # if (current_time - last_control_time)>=CONTROL_CYCLE:
                if current_time >= last_control_time:
                    # Get current pos and force
                    feedback = self.robot.get_feedback()
                    current_pos = feedback.AttitudesArray
                    a=self.force_queue.empty()
                    if not self.force_event.is_set():
                        self.force_event.wait()
                    F_e = self.force_queue.get()
                    F_e = -F_e
                    # F_e = self.force_queue.get() if not self.force_queue.empty() else np.zeros(6) # Get the latest force data from the queue
                    # F_e = [0, 0, 0, 0, 0, -10] # Test Step1: keep the Fz constant
                    F_e[0:5] = 0 # Test Step2: only keep the z=axis force TODO: remember to remove this line 
                    # F_e[5] = 0

                    # Excute the control algorithm
                    target_pos = self.control_algorithm.update(F_e)

                    self.force_event.clear()

                    # Send command to the platform
                    command = CommandMessage(
                        command_code=CommandCodes.ContinuousMoving,         # 9
                        dofs = target_pos # dofs TODO: Control algorithm output
                    )
                    # command_bytes = command.to_bytes()
                    # print(f"Command bytes: {command_bytes}")
                    self.robot.send_command(command)
                    # Write data to CSV
                    self.save_data(target_pos, current_pos,F_e)
                    last_control_time += CONTROL_CYCLE
                    if last_control_time<current_time:
                        last_control_time = current_time+ CONTROL_CYCLE
                    # update the last control time
                    # last_control_time = current_time
                else:
                    time.sleep(max(0, last_control_time - current_time - 0.001))
        finally:
            self.robot.dispose()
            print("Control loop thread stopped!")
    def save_data(self, target_pos, current_pos, force):
        timestamp = time.time()
        self.data.append({
            "timestamp": timestamp,
            "target_pos": target_pos,
            "current_pos": current_pos,
            "force": force
        })

        current_time = time.time()
        if current_time - self.last_save_time >= SAVE_DATA_CYCLE:  
            self.export_to_csv()
            self.last_save_time = current_time

    def export_to_csv(self):
        # Export data to CSV file
        os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
        with open(self.data_file_path, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'target_pos', 'current_pos', 'force']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
            for row in self.data:
                writer.writerow({
                    # 'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    'timestamp': str(row['timestamp']),
                    'target_pos': row['target_pos'],
                    'current_pos': row['current_pos'],
                    'force': row['force']
                })
        print(f"Data appended to {self.data_file_path}")
        self.data = []

    def start(self):
        # Start the control system
        self.force_thread = threading.Thread(target=self.force_acquisition, daemon=True)
        self.control_thread = threading.Thread(target=self.control_loop, daemon=True)

        self.force_thread.start()
        time.sleep(0.1)
        self.control_thread.start()

    def stop(self):
        # Stop the control system
        self.exit_event.set()
        self.force_thread.join()
        self.control_thread.join()
        self.export_to_csv()

if __name__ == "__main__":
    system = ControlSystem()
    try:
        system.start()
        while True:  # Main loop running
            time.sleep(1)
    except KeyboardInterrupt:
        system.stop()
"""


# 0414 constant force no viuslization write to csv
"""class ControlSystem:
    def __init__(self):
        ip_setting =IpSetting()
        self.robot = DofController(ip_setting)
        self.force_sensor = ATIMini85()
        # init control algorithm parameters
        M = np.diag([1]*6)
        D = np.diag([5]*6)
        K = np.diag([100]*6)
        self.control_algorithm = ControlAlgorithm(M, D, K, CONTROL_CYCLE)

        # share data between threads
        self.force_queue = Queue()
        self.position_queue = Queue()
        # Synchronous event
        self.force_event = threading.Event()
        self.position_event = threading.Event()
        self.force_thread = None
        self.control_thread = None
        self.exit_event = threading.Event()
        self.is_running = False

        self.last_avg = np.zeros(6)
        # init filter
        self.filter_window = 10
        self.filter_buffer = np.zeros((self.filter_window,6))

        # Save data
        self.data = []
        self.data_file_path = "data/control_data1.csv"
        self.data_counter = 0
        self.data_interval = 10  
        self.last_save_time = time.time()


    def force_acquisition(self):
        # Force data acquisition thread: read data from sensor and put into queue
        self.force_sensor.start(sampling_rate=FORCE_SAMPLE_RATE)
        self.force_sensor.calibrate_zero()
        try:
            while not self.exit_event.is_set():
                forces = self.force_sensor.get_calibrated_forces(num_samples=SAMPLE_CHUNK) # forces shape: [SAMPLE_CHUNK, 6 channels]
                forces[:,:3], forces[:,3:] = forces[:,3:], forces[:,:3]
                # 1. slide average filter
                # if len(self.filter_buffer) >= self.filter_window:
                #     self.filter_buffer.pop(0)
                # self.filter_buffer.append(forces)
                # averaged_forces = np.mean(self.filter_buffer, axis=0)[-1]
                # real time low pass
                # current_avg = np.mean(forces, axis=0)
                # averaged_forces = 0.2*current_avg + 0.8*self.last_avg  # TODO: change the paramete coefficient
                # self.last_avg = averaged_forces

                if not self.force_queue.full():
                    # self.force_queue.put(averaged_forces) # forces[-1] Get the newest sample TODO: maybe use the average of the last 10 samples to avoid noise
                    self.force_queue.put(forces[-1])
                    self.force_event.set()
                else:
                    print("Warning: Force data queue is full. Force data may be lost.")
                time.sleep(FORCE_SAMPLE_CYCLE) # Small sleep to prevent CPU overload
        finally:
            self.force_sensor.stop()
            print("Force sensor acquisition thread stopped!")

    def control_loop(self):
        # Main Control Thread
        self.robot.connect() # Connect to the platform controller
        last_control_time = time.time()

        try:
            while not self.exit_event.is_set():
                # Synchronous control cycle
                current_time = time.time()
                # if (current_time - last_control_time)>=CONTROL_CYCLE:
                if current_time >= last_control_time:
                    # Get current pos and force
                    feedback = self.robot.get_feedback()
                    current_pos = feedback.AttitudesArray
                    a=self.force_queue.empty()
                    if not self.force_event.is_set():
                        self.force_event.wait()
                    # F_e = self.force_queue.get()
                    # F_e = -F_e
                    # F_e = self.force_queue.get() if not self.force_queue.empty() else np.zeros(6) # Get the latest force data from the queue
                    F_e = [0, 0, 0, 0, 0, -10] # Test Step1: keep the Fz constant
                    # F_e[0:4] = 0 # Test Step2: only keep the z=axis force TODO: remember to remove this line 
                    # F_e[5] = 0

                    # Excute the control algorithm
                    target_pos = self.control_algorithm.update(F_e)

                    self.force_event.clear()

                    # Send command to the platform
                    command = CommandMessage(
                        command_code=CommandCodes.ContinuousMoving,         # 9
                        dofs = target_pos # dofs TODO: Control algorithm output
                    )
                    # command_bytes = command.to_bytes()
                    # print(f"Command bytes: {command_bytes}")
                    self.robot.send_command(command)
                    # Write data to CSV
                    self.save_data(target_pos[5], current_pos[5],F_e[5])
                    last_control_time += CONTROL_CYCLE
                    if last_control_time<current_time:
                        last_control_time = current_time+ CONTROL_CYCLE
                    # update the last control time
                    # last_control_time = current_time
                else:
                    time.sleep(max(0, last_control_time - current_time - 0.001))
        finally:
            self.robot.dispose()
            print("Control loop thread stopped!")
    def save_data(self, target_pos, current_pos, force):
        timestamp = time.time()
        self.data.append({
            "timestamp": timestamp,
            "target_pos": target_pos,
            "current_pos": current_pos,
            "force": force
        })

        current_time = time.time()
        if current_time - self.last_save_time >= SAVE_DATA_CYCLE:  
            self.export_to_csv()
            self.last_save_time = current_time

    def export_to_csv(self):
        # Export data to CSV file
        os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
        with open(self.data_file_path, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'target_pos', 'current_pos', 'force']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
            for row in self.data:
                writer.writerow({
                    # 'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    'timestamp': str(row['timestamp']),
                    'target_pos': row['target_pos'],
                    'current_pos': row['current_pos'],
                    'force': row['force']
                })
        print(f"Data appended to {self.data_file_path}")
        self.data = []

    def start(self):
        # Start the control system
        self.force_thread = threading.Thread(target=self.force_acquisition, daemon=True)
        self.control_thread = threading.Thread(target=self.control_loop, daemon=True)

        self.force_thread.start()
        time.sleep(0.1)
        self.control_thread.start()

    def stop(self):
        # Stop the control system
        self.exit_event.set()
        self.force_thread.join()
        self.control_thread.join()
        self.export_to_csv()

if __name__ == "__main__":
    system = ControlSystem()
    try:
        system.start()
        while True:  # Main loop running
            time.sleep(1)
    except KeyboardInterrupt:
        system.stop()
"""
# 0414 single axis force constant with visualization
"""
class ControlSystem:
    def __init__(self):
        ip_setting =IpSetting()
        self.robot = DofController(ip_setting)
        self.force_sensor = ATIMini85()
        # self.monitor = RealTimePlot()
        # self.single_axis_monitor = SingleAxisMonitor()
        # init control algorithm parameters
        M = np.diag([1]*6)
        D = np.diag([5]*6)
        K = np.diag([100]*6)
        self.control_algorithm = ControlAlgorithm(M, D, K, CONTROL_CYCLE)

        # share data between threads
        self.force_queue = Queue()
        self.position_queue = Queue()
        # self.command_queue = Queue()
        # self.feedback_queue = Queue()
        # Synchronous event
        self.force_event = threading.Event()
        self.position_event = threading.Event()
        self.force_thread = None
        self.control_thread = None
        self.exit_event = threading.Event()
        self.is_running = False

        self.last_avg = np.zeros(6)
        # init filter
        self.filter_window = 10
        self.filter_buffer = np.zeros((self.filter_window,6))


    def force_acquisition(self):
        # Force data acquisition thread: read data from sensor and put into queue
        self.force_sensor.start(sampling_rate=FORCE_SAMPLE_RATE)
        self.force_sensor.calibrate_zero()
        try:
            while not self.exit_event.is_set():
                forces = self.force_sensor.get_calibrated_forces(num_samples=SAMPLE_CHUNK) # forces shape: [SAMPLE_CHUNK, 6 channels]
                # forces[:3], forces[3:] = forces[3:], forces[:3]
                if forces.shape[0] != SAMPLE_CHUNK or forces.shape[1] != 6:
                    print(f"Warning: Unexpected forces shape: {forces.shape}. Expected shape: ({SAMPLE_CHUNK}, 6)")
                else:
                    forces[:,:3], forces[:,3:] = forces[:,3:], forces[:,:3]
                # 1. slide average filter
                # if len(self.filter_buffer) >= self.filter_window:
                #     self.filter_buffer.pop(0)
                # self.filter_buffer.append(forces)
                # averaged_forces = np.mean(self.filter_buffer, axis=0)[-1]
                # real time low pass
                # current_avg = np.mean(forces, axis=0)
                # averaged_forces = 0.2*current_avg + 0.8*self.last_avg  # TODO: change the paramete coefficient
                # self.last_avg = averaged_forces

                if not self.force_queue.full():
                    # self.force_queue.put(averaged_forces) # forces[-1] Get the newest sample TODO: maybe use the average of the last 10 samples to avoid noise
                    self.force_queue.put(forces[-1])
                    self.force_event.set()
                else:
                    print("Warning: Force data queue is full. Force data may be lost.")
                time.sleep(FORCE_SAMPLE_CYCLE) # Small sleep to prevent CPU overload
        finally:
            self.force_sensor.stop()
            print("Force sensor acquisition thread stopped!")

    def control_loop(self):
        # Main Control Thread
        self.robot.connect() # Connect to the platform controller
        last_control_time = time.time()
        # self.initialize_csv()

        try:
            while not self.exit_event.is_set():
                # Synchronous control cycle
                current_time = time.time()
                # if (current_time - last_control_time)>=CONTROL_CYCLE:
                if current_time >= last_control_time:
                    # Get current pos and force
                    feedback = self.robot.get_feedback()
                    current_pos = feedback.AttitudesArray
                    a=self.force_queue.empty()
                    if not self.force_event.is_set():
                        self.force_event.wait()
                    # F_e = self.force_queue.get()
                    # F_e = -F_e
                    # F_e = self.force_queue.get() if not self.force_queue.empty() else np.zeros(6) # Get the latest force data from the queue
                    F_e = [0, 0, 0, 0, 0, -10] # Test Step1: keep the Fz constant
                    # F_e[0:4] = 0 # Test Step2: only keep the z=axis force TODO: remember to remove this line 
                    # F_e[5] = 0

                    # Excute the control algorithm
                    target_pos = self.control_algorithm.update(F_e)

                    self.force_event.clear()

                    # Send command to the platform
                    command = CommandMessage(
                        command_code=CommandCodes.ContinuousMoving,         # 9
                        dofs = target_pos # dofs TODO: Control algorithm output
                    )
                    # command_bytes = command.to_bytes()
                    # print(f"Command bytes: {command_bytes}")
                    self.robot.send_command(command)
                    # Write data to CSV
                    # self.data_counter += 1
                    # if self.data_counter >= self.data_interval:
                    #     timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    #     self.write_to_csv(timestamp, target_pos, current_pos)
                    #     self.data_counter = 0 

                    # self.monitor.update(target_pos,current_pos,F_e) # TODO: Maybe need to remove 6axis monitor
                    self.single_axis_monitor.update(target_pos[5],current_pos[5],F_e[5]) # Z-axis monitor
                    last_control_time += CONTROL_CYCLE
                    if last_control_time<current_time:
                        last_control_time = current_time+ CONTROL_CYCLE
                    # update the last control time
                    # last_control_time = current_time
                else:
                    time.sleep(max(0, last_control_time - current_time - 0.001))
        finally:
            # if self.csv_file is not None:
            #     self.csv_file.close()
            self.robot.dispose()
            print("Control loop thread stopped!")

    def start(self):
        # Start the control system
        self.single_axis_monitor = SingleAxisMonitor()
        # self.monitor = RealTimePlot()
        # self.single_axis_monitor.show()

        self.force_thread = threading.Thread(target=self.force_acquisition, daemon=True)
        self.control_thread = threading.Thread(target=self.control_loop, daemon=True)

        self.force_thread.start()
        time.sleep(0.1)
        self.control_thread.start()

    def stop(self):
        # Stop the control system
        self.exit_event.set()
        self.force_thread.join()
        self.control_thread.join()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    system = ControlSystem()
    try:
        system.start()
        sys.exit(app.exec())
        while True:  # Main loop running
            time.sleep(1)
            
    except KeyboardInterrupt:
        system.stop()
"""

# 0728 6 axis constant force/torque no visulization write to csv
class ControlSystem:
    def __init__(self):
        ip_setting =IpSetting()
        self.robot = DofController(ip_setting)
        self.force_sensor = ATIMini85()
        # init control algorithm parameters
        M = np.diag([1]*6)
        D = np.diag([5]*6)
        K = np.diag([100]*6)
        self.control_algorithm = ControlAlgorithm(M, D, K, CONTROL_CYCLE)

        # share data between threads
        self.force_queue = Queue()
        self.position_queue = Queue()
        # Synchronous event
        self.force_event = threading.Event()
        self.position_event = threading.Event()
        self.force_thread = None
        self.control_thread = None
        self.exit_event = threading.Event()
        self.is_running = False

        self.last_avg = np.zeros(6)
        # init filter
        self.filter_window = 10
        self.filter_buffer = np.zeros((self.filter_window,6))

        # Save data
        self.data = []
        self.data_file_path = "data/Tx5Ty5Tz5Fx25NFy25NFz25N.csv" 
        self.data_counter = 0
        self.data_interval = 10  
        self.last_save_time = time.time()


    def force_acquisition(self):
        # Force data acquisition thread: read data from sensor and put into queue
        self.force_sensor.start(sampling_rate=FORCE_SAMPLE_RATE)
        self.force_sensor.calibrate_zero()
        try:
            while not self.exit_event.is_set():
                forces = self.force_sensor.get_calibrated_forces(num_samples=SAMPLE_CHUNK) # forces shape: [SAMPLE_CHUNK, 6 channels]
                forces[:,:3], forces[:,3:] = forces[:,3:], forces[:,:3]
                # 1. slide average filter
                # if len(self.filter_buffer) >= self.filter_window:
                #     self.filter_buffer.pop(0)
                # self.filter_buffer.append(forces)
                # averaged_forces = np.mean(self.filter_buffer, axis=0)[-1]
                # real time low pass
                # current_avg = np.mean(forces, axis=0)
                # averaged_forces = 0.2*current_avg + 0.8*self.last_avg  # TODO: change the paramete coefficient
                # self.last_avg = averaged_forces

                if not self.force_queue.full():
                    # self.force_queue.put(averaged_forces) # forces[-1] Get the newest sample TODO: maybe use the average of the last 10 samples to avoid noise
                    self.force_queue.put(forces[-1])
                    self.force_event.set()
                else:
                    print("Warning: Force data queue is full. Force data may be lost.")
                time.sleep(FORCE_SAMPLE_CYCLE) # Small sleep to prevent CPU overload
        finally:
            self.force_sensor.stop()
            print("Force sensor acquisition thread stopped!")

    def control_loop(self):
        # Main Control Thread
        self.robot.connect() # Connect to the platform controller
        last_control_time = time.time()

        try:
            while not self.exit_event.is_set():
                # Synchronous control cycle
                current_time = time.time()
                # if (current_time - last_control_time)>=CONTROL_CYCLE:
                if current_time >= last_control_time:
                    # Get current pos and force
                    feedback = self.robot.get_feedback()
                    current_pos = feedback.AttitudesArray
                    a=self.force_queue.empty()
                    if not self.force_event.is_set():
                        self.force_event.wait()
                    # F_e = self.force_queue.get()
                    # F_e = -F_e
                    # F_e = self.force_queue.get() if not self.force_queue.empty() else np.zeros(6) # Get the latest force data from the queue
                    F_e = [5, 5, 5, 25, 25, 25] # [tx,ty,tz,fx,fy,fz]
                    # F_e[0:4] = 0 # Test Step2: only keep the z=axis force TODO: remember to remove this line 
                    # F_e[5] = 0

                    # Excute the control algorithm
                    target_pos = self.control_algorithm.update(F_e,current_pos)

                    self.force_event.clear()

                    # Send command to the platform
                    command = CommandMessage(
                        command_code=CommandCodes.ContinuousMoving,         # 9
                        dofs = target_pos # dofs TODO: Control algorithm output
                    )
                    # command_bytes = command.to_bytes()
                    # print(f"Command bytes: {command_bytes}")
                    self.robot.send_command(command)
                    # Write data to CSV
                    self.save_data(target_pos, current_pos,F_e)
                    last_control_time += CONTROL_CYCLE
                    if last_control_time<current_time:
                        last_control_time = current_time+ CONTROL_CYCLE
                    # update the last control time
                    # last_control_time = current_time
                else:
                    time.sleep(max(0, last_control_time - current_time - 0.001))
        finally:
            self.robot.dispose()
            print("Control loop thread stopped!")
    def save_data(self, target_pos, current_pos, force):
        timestamp = time.time()
        self.data.append({
            "timestamp": timestamp,
            "target_pos_rx": target_pos[0],
            "target_pos_ry": target_pos[1],
            "target_pos_rz": target_pos[2],
            "target_pos_x": target_pos[3],
            "target_pos_y": target_pos[4],
            "target_pos_z": target_pos[5],
            "current_pos_rx": current_pos[0],
            "current_pos_ry":current_pos[1],
            "current_pos_rz": current_pos[2],
            "current_pos_x": current_pos[3],
            "current_pos_y": current_pos[4],
            "current_pos_z": current_pos[5],
            "force": force
        })

        current_time = time.time()
        if current_time - self.last_save_time >= SAVE_DATA_CYCLE:  
            self.export_to_csv()
            self.last_save_time = current_time

    def export_to_csv(self):
        # Export data to CSV file
        os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
        with open(self.data_file_path, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'target_pos_rx', 'target_pos_ry', 'target_pos_rz', 'target_pos_x', 'target_pos_y', 'target_pos_z', 'current_pos_rx', 'current_pos_ry', 'current_pos_rz', 'current_pos_x', 'current_pos_y', 'current_pos_z', 'force']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
            for row in self.data:
                writer.writerow({
                    # 'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    'timestamp': str(row['timestamp']),
                    'target_pos_rx': row['target_pos_rx'],
                    'target_pos_ry': row['target_pos_ry'],
                    'target_pos_rz': row['target_pos_rz'],
                    "target_pos_x": row['target_pos_x'],
                    "target_pos_y": row['target_pos_y'],
                    "target_pos_z": row['target_pos_z'],
                    'current_pos_rx': row['current_pos_rx'],
                    'current_pos_ry': row['current_pos_ry'],
                    'current_pos_rz': row['current_pos_rz'],
                    'current_pos_x': row['current_pos_x'],
                    'current_pos_y': row['current_pos_y'],
                    'current_pos_z': row['current_pos_z'],
                    'force': row['force']
                })
        print(f"Data appended to {self.data_file_path}")
        self.data = []

    def start(self):
        # Start the control system
        self.force_thread = threading.Thread(target=self.force_acquisition, daemon=True)
        self.control_thread = threading.Thread(target=self.control_loop, daemon=True)

        self.force_thread.start()
        time.sleep(0.1)
        self.control_thread.start()

    def stop(self):
        # Stop the control system
        self.exit_event.set()
        self.force_thread.join()
        self.control_thread.join()
        self.export_to_csv()

if __name__ == "__main__":
    system = ControlSystem()
    try:
        system.start()
        while True:  # Main loop running
            time.sleep(1)
    except KeyboardInterrupt:
        system.stop()

# 0728 6axis no problem No visualization no filter 6 axis 
'''class ControlSystem:
    def __init__(self):
        ip_setting =IpSetting()
        self.robot = DofController(ip_setting)
        self.force_sensor = ATIMini85()
        M = np.diag([1]*6)
        D = np.diag([5]*6)
        K = np.diag([100]*6)
        self.control_algorithm = ControlAlgorithm(M, D, K, CONTROL_CYCLE)

        # share data between threads
        self.force_queue = Queue()
        self.position_queue = Queue()
        # Synchronous event
        self.force_event = threading.Event()
        self.position_event = threading.Event()
        self.force_thread = None
        self.control_thread = None
        self.exit_event = threading.Event()
        self.is_running = False

        self.last_avg = np.zeros(6)
        # init filter
        self.filter_window = 10
        self.filter_buffer = np.zeros((self.filter_window,6))
    
    def force_acquisition(self):
        # Force data acquisition thread: read data from sensor and put into queue
        self.force_sensor.start(sampling_rate=FORCE_SAMPLE_RATE)
        self.force_sensor.calibrate_zero()
        try:
            while not self.exit_event.is_set():
                forces = self.force_sensor.get_calibrated_forces(num_samples=SAMPLE_CHUNK) # forces shape: [SAMPLE_CHUNK, 6 channels]
                # forces[:3], forces[3:] = forces[3:], forces[:3]
                if forces.shape[0] != SAMPLE_CHUNK or forces.shape[1] != 6:
                    print(f"Warning: Unexpected forces shape: {forces.shape}. Expected shape: ({SAMPLE_CHUNK}, 6)")
                else:
                    forces[:,:3], forces[:,3:] = forces[:,3:], forces[:,:3]
                # 1. slide average filter
                # if len(self.filter_buffer) >= self.filter_window:
                #     self.filter_buffer.pop(0)
                # self.filter_buffer.append(forces)
                # averaged_forces = np.mean(self.filter_buffer, axis=0)[-1]
                # real time low pass
                # current_avg = np.mean(forces, axis=0)
                # averaged_forces = 0.2*current_avg + 0.8*self.last_avg  # TODO: change the paramete coefficient
                # self.last_avg = averaged_forces

                if not self.force_queue.full():
                    # self.force_queue.put(averaged_forces) # forces[-1] Get the newest sample TODO: maybe use the average of the last 10 samples to avoid noise
                    self.force_queue.put(forces[-1])
                    self.force_event.set()
                else:
                    print("Warning: Force data queue is full. Force data may be lost.")
                time.sleep(FORCE_SAMPLE_CYCLE) # Small sleep to prevent CPU overload
        finally:
            self.force_sensor.stop()
            print("Force sensor acquisition thread stopped!")

    def control_loop(self):
        # Main Control Thread
        self.robot.connect() # Connect to the platform controller
        last_control_time = time.time()
        # self.initialize_csv()

        try:
            while not self.exit_event.is_set():
                # Synchronous control cycle
                current_time = time.time()
                # if (current_time - last_control_time)>=CONTROL_CYCLE:
                if current_time >= last_control_time:
                    # Get current pos and force
                    feedback = self.robot.get_feedback()
                    current_pos = feedback.AttitudesArray
                    a=self.force_queue.empty()
                    if not self.force_event.is_set():
                        self.force_event.wait()
                    F_e = self.force_queue.get()
                    F_e = -F_e
                    F_e[3:6]=0
                    # F_e[0]=2
                    # F_e[2]=2
                    # for i in range(6):
                    #     if -2<F_e[i]<2:
                    #         F_e[i] = 0
                    # F_e = self.force_queue.get() if not self.force_queue.empty() else np.zeros(6) # Get the latest force data from the queue
                    # F_e = [0, 0, 0, 0, 0, -10] # Test Step1: keep the Fz constant
                    # F_e[0:4] = 0 # Test Step2: only keep the z=axis force TODO: remember to remove this line 
                    # F_e[5] = 0

                    # Excute the control algorithm
                    target_pos = self.control_algorithm.update(F_e,current_pos)

                    self.force_event.clear()

                    # Send command to the platform
                    command = CommandMessage(
                        command_code=CommandCodes.ContinuousMoving,         # 9
                        dofs = target_pos # dofs TODO: Control algorithm output
                    )
                    # command_bytes = command.to_bytes()
                    # print(f"Command bytes: {command_bytes}")
                    self.robot.send_command(command)

                    # self.monitor.update(target_pos,current_pos,F_e) # TODO: Maybe need to remove 6axis monitor
                    # self.single_axis_monitor.update(target_pos[5],current_pos[5],F_e[5]) # Z-axis monitor
                    last_control_time += CONTROL_CYCLE
                    if last_control_time<current_time:
                        last_control_time = current_time+ CONTROL_CYCLE
                    # update the last control time
                    # last_control_time = current_time
                else:
                    time.sleep(max(0, last_control_time - current_time - 0.001))
        finally:
            # if self.csv_file is not None:
            #     self.csv_file.close()
            self.robot.dispose()
            print("Control loop thread stopped!")

    def start(self):

        self.force_thread = threading.Thread(target=self.force_acquisition, daemon=True)
        self.control_thread = threading.Thread(target=self.control_loop, daemon=True)

        self.force_thread.start()
        time.sleep(0.1)
        self.control_thread.start()

    def stop(self):
        # Stop the control system
        self.exit_event.set()
        self.force_thread.join()
        self.control_thread.join()'''

if __name__ == "__main__":
    # app = QtWidgets.QApplication(sys.argv)
    system = ControlSystem()
    try:
        system.start()
        # sys.exit(app.exec())
        while True:  # Main loop running
            time.sleep(1)
            
    except KeyboardInterrupt:
        system.stop()

