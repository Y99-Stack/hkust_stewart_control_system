## Notes:
Force sensor: $[F_x,F_y,F_z,T_x,T_y,T_z]$
                0   1   2   3   4   5
Feedback from robot: $[R_x, R_y, R_z, x, y, z]$ 
                       3    4    5   0  1  2
                       0    1    2   -3 -2 -1
Force对应到position的时候要右移3 force[i] = force[i-3]

## Problems
现在面临的问题是在施加力之前actual_pos与x_d没有对应，所以要么在程序里设定让他先到x_d的位置，要么就直接让x_d=这一刻的actual_pos, target_pos=0.001，actual_pos = 0.22, x_d = 0， 最后就会出现一个阶跃, 由于这里先设置x_d=0所以让robot从x_d=0开始运动。



## 0728 record

Fx=100N Ty=20 cannot back to original pose[0,0,0,0,0,0] when Fx=50, can back
