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
FORCE_SAMPLE_RATE = 100
FORCE_SAMPLE_CYCLE = 1 / FORCE_SAMPLE_RATE
SAMPLE_CHUNK = 1      # number of samples to read each time (10 samples = 10ms at 1000Hz)
SAVE_DATA_CYCLE = 0.01


# 1124 6axis no save data No visualization no filter 6 axis  
class ControlSystem:
    def __init__(self):
        ip_setting =IpSetting()
        self.robot = DofController(ip_setting)
        self.force_sensor = ATIMini85()

        M = np.diag([2,100,100,500,500,2]) # [1000]*6 [1000, 2000,3000,1000,1000,1000]
        D = np.diag([2.3,100,100,500,500,16])
        K = np.diag([10,100,100,500,500,100])
        self.control_algorithm = ControlAlgorithm(M, D, K, CONTROL_CYCLE)

        # share data between threads
        self.force_queue = Queue(maxsize=max(1, FORCE_SAMPLE_RATE // 5))
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
            target_period = 1 / FORCE_SAMPLE_RATE
            while not self.exit_event.is_set():
                start = time.perf_counter()
                forces = self.force_sensor.get_calibrated_forces(num_samples=SAMPLE_CHUNK) # forces shape: [SAMPLE_CHUNK, 6 channels]
                # print(f"[RAW] forces shape: {forces.shape}, sample[0]: {forces[0]}")
                # forces[:3], forces[3:] = forces[3:], forces[:3]
                if forces.shape[0] != SAMPLE_CHUNK or forces.shape[1] != 6:
                    print(f"Warning: Unexpected forces shape: {forces.shape}. Expected shape: ({SAMPLE_CHUNK}, 6)")
                else:
                    # forces[:,:3], forces[:,3:] = forces[:,3:], forces[:,:3]
                    tmp = forces.copy()
                    forces[:, :3] = tmp[:, 3:]   # 新前三 = 原力矩
                    forces[:, 3:] = tmp[:, :3]

                    if self.force_queue.full():
                        # self.force_queue.put(averaged_forces) # forces[-1] Get the newest sample TODO: maybe use the average of the last 10 samples to avoid noise
                        self.force_queue.get_nowait() 
                        # print("Warning: Force data queue is full. Force data may be lost.")
                    
                    self.force_queue.put(forces[-1])
                    self.force_event.set()
                elapsed = time.perf_counter() - start
                time.sleep(max(0, target_period - elapsed))
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
                    if not self.force_event.is_set():
                        self.force_event.wait(timeout = CONTROL_CYCLE)
                    if self.force_queue.empty():
                        # 当前周期没有新的力数据，就跳过这一轮控制
                        last_control_time += CONTROL_CYCLE
                        continue
                    while self.force_queue.qsize() > 1:
                        self.force_queue.get_nowait()
                    F_e = self.force_queue.get()
                    F_e[1:5]=0
                    F_e=-F_e
                    # print(f"Fe:{F_e}")

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
        self.control_thread.join()

if __name__ == "__main__":
    system = ControlSystem()
    try:
        system.start()
        while True:  # Main loop running
            time.sleep(1)
            
    except KeyboardInterrupt:
        system.stop()

