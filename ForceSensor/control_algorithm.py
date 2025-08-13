import numpy as np
from scipy.linalg import inv
from scipy.spatial.transform import Rotation as R

# [Tx,Ty,Tz,Fx,Fy,Fz] 下位机是先欧拉角后位置
SAFETY_LIMITS = {
    'force': [50,50,50,1000,10,10],
    'position': [0.3,0.3,0.3,0.1,0.1,0.1]
}

class ControlAlgorithm:
    def __init__(self, M, D, K, dt=0.01):
        self.M = np.array(M)  
        self.D = np.array(D)  
        self.K = np.array(K)  
        self.dt = dt          

        # init state variables
        # self.x_e = np.zeros(6)     
        # self.x_e_dot = np.zeros(6) 
        # self.x_e_ddot = np.zeros(6)
        self.reset()
        
        # init desired variables
        
    
    def reset(self,initial_x_d=None):
        # TODO: x_d reset as the actual pos before add force
        self.x_d = np.zeros(6)     
        self.x_d_dot = np.zeros(6) 
        self.x_d_ddot = np.zeros(6)

        self.x_e = np.zeros(6, dtype=np.float64)
        self.x_e_dot = np.zeros(6, dtype=np.float64)
        self.x_e_ddot = np.zeros(6, dtype=np.float64)
        # self.R_e = np.eye(3, dtype=np.float64)  # Rotation matrix, identity for now
        self.R_e = R.identity().as_matrix()  # 偏差旋转矩阵
        self.R_d = R.identity().as_matrix()  # 期望旋转矩阵
        if initial_x_d is not None:
            self.set_desired_trajectory(initial_x_d)

        self.current_rot = np.eye(3)
    
    def _transform_force_to_world(self, F_sensor, current_pose):
        """
        将传感器数据转换到世界坐标系
        Args:
            F_sensor: [T_x, T_y, T_z, F_x, F_y, F_z]（传感器坐标系）
            current_pose: [rx, ry, rz, x, y, z ]（世界坐标系，姿态为旋转向量）欧拉角的形式
        Returns:
            F_world: 世界坐标系下的六维力
        """
        # 获取当前旋转矩阵
        # rot = R.from_rotvec(current_pose[:3]).as_matrix()
        rot = R.from_euler('xyz', current_pose[:3], degrees=True).as_matrix()
        # print("DEBUG: rot=",rot)
        
        # 转换力和力矩 before input this function Fe:[tx,ty,tz,fx,fy,fz]
        force_sensor = F_sensor[3:]
        # print("force_sensor:",force_sensor)
        torque_sensor = F_sensor[:3]
        # print("DEBUG torque_sensor:",torque_sensor)
        
        # 力向量转换：F_world = R * F_sensor
        force_world = rot @ force_sensor
        
        # 力矩转换：T_world = R @ T_sensor + position @ F_sensor
        # （假设传感器位于末端，忽略位置偏移的影响）
        torque_world = rot @ torque_sensor

        F_world = np.concatenate([torque_world,force_world])

        
        return F_world
    
    def update(self, F_sensor, current_pose=None):
        """
        update control variables
        Args: 
            F_sensor: get from force sensor
            current_pose: [rx, ry, rz, x, y, z]欧拉 (optional) current pose of the end effector in world coordinates
        return:
            target_pos: next loop target position 
        OR TODO: input x here and update it in the main.py
        """
        # self._update_trajectory()
        

        # self.current_rot = R.from_rotvec(current_pose[:3]).as_matrix()
        self.current_rot = R.from_euler('xyz', current_pose[:3], degrees=True).as_matrix()
        F_world = self._transform_force_to_world(F_sensor, current_pose) # return force in world coordinates
        # print("F_world:", F_world)
        # print("F_sensor:",F_sensor)
        # print(F_world==F_sensor)
        # print("current_pose:",current_pose)

        # Safety check
        for i in range(6):
            F_world[i] = np.clip(F_world[i], -SAFETY_LIMITS['force'][i], SAFETY_LIMITS['force'][i])

        self.x_e_ddot = inv(self.M) @ (F_world - self.D @ self.x_e_dot - self.K @ self.x_e)
        a=self.x_e_ddot
        self.x_e_dot += self.x_e_ddot * self.dt
        b=self.x_e_dot
        # Update position
        self.x_e[3:] += self.x_e_dot[3:] * self.dt
        c=self.x_e[3:]
        # Update orientation
        # delta_R = R.from_rotvec(self.x_e_dot[3:]) 
        # print("R_e:",self.R_e)
        delta_euler = self.x_e_dot[:3] * self.dt
        delta_R = R.from_euler('xyz', delta_euler, degrees=True).as_matrix()
        # print("Delta_R:",delta_R)
        self.R_e = delta_R @ self.R_e
        d=self.R_e
        # print("self.R_e:", self.R_e)
        # print(self.R_e==delta_R)
        # self.x_e[3:] = R.from_matrix(self.R_e).as_rotvec()

        # calculate the target position
        target_pos = self._calculate_target_position(self.x_e, self.x_d )
        # target_pos = np.zeros(6)
        # target_pos[:3] = self.x_d[:3] + self.x_e[:3]
        # # orientation part
        # target_R = self.R_d @ self.R_e
        # target_pos[3:] = R.from_matrix(target_R).as_rotvec()

        # Clip position for safety
        # target_pos = np.clip(target_pos, -SAFETY_LIMITS['position'], SAFETY_LIMITS['position'])
        return target_pos
    
    def _calculate_target_position(self, x_e, x_d):
        """
        Calculate the target position based on the current error and desired position
        Args:
            x_e: current error state
            x_d: desired state
        Returns:
            target_pos: calculated target position
        """
        target_pos = np.zeros(6)
        target_pos[3:] = x_d[3:] + x_e[3:]
        # orientation part
        target_R = self.R_d @ self.R_e
        target_pos[:3] = R.from_matrix(target_R).as_euler('xyz', degrees=True)
        return target_pos

    def set_desired_trajectory(self, x_d, x_d_dot=None, x_d_ddot=None):
        """
        update the desired trajectory
        now is static trajectory, but can be changed to dynamic trajectory in the future
        Args:

        """

        self.x_d = np.array(x_d)
        self.R_d = R.from_euler('xyz', self.x_d[:3], degrees=True).as_matrix()  # Desired rotation matrix from desired rotation vector
        self.x_d_dot = np.array(x_d_dot) if x_d_dot is not None else np.zeros_like(x_d)
        self.x_d_ddot = np.array(x_d_ddot) if x_d_ddot is not None else np.zeros_like(x_d)

# TODO next step: add dynamic trajectory
    """
    def set_static_position(self, x_d):
        self.traj_type = "static"
        self.x_d = np.array(x_d, dtype=np.float64)

    def set_sine_trajectory(self,axis,amplitude, frequency):
        self.traj_type = "sine"
        self.traj_data = (int(axis), float(amplitude), float(frequency))
        self.traj_time = 0.0

    def set_csv_trajectory(self, csv_file):
        self.traj_type = "csv"
        self.traj_data = np.loadtxt(csv_file,delimiter=",")
        self.traj_time = 0.0

    def _update_trajectory(self):
        if self.traj_type == "sine":
            axis, amplitude, frequency = self.traj_data
            t = self.traj_time
            self.x_d[axis] = amplitude * np.sin(2 * np.pi * frequency * t)
            self.traj_time += self.dt
        elif self.traj_type == "csv":
            if self.traj_time < len(self.traj_data):
                self.x_d = self.traj_data[int(self.traj_time)]
                self.traj_time += 1
    """        

#test
# 示例使用
# M = np.eye(6)  # 示例质量矩阵
# D = np.eye(6)  # 示例阻尼矩阵
# K = np.eye(6)  # 示例刚度矩阵

# control = ControlAlgorithm(M, D, K)
# control.set_desired_trajectory([0,0,0,0,0,0])
# # 示例力输入
# F_e = np.array([0, 1, 0, 10, 0, 0])
# target_pos = [0,0,0,0,0,0]
# for i in range(100):
#     target_pos = control.update(F_e, target_pos)
#     print("目标位置:", [f"{val:.6f}" for val in target_pos])


