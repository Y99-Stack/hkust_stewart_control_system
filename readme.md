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


# 0910
record errors:
Traceback (most recent call last):
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\site-packages\nidaqmx\_lib.py", line 206, in _import_lib
    windll, cdll = _load_lib("nicai_utf8")
                   ~~~~~~~~~^^^^^^^^^^^^^^
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\site-packages\nidaqmx\_lib.py", line 184, in _load_lib
    windll = ctypes.windll.LoadLibrary(libname)
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\ctypes\__init__.py", line 471, in LoadLibrary
    return self._dlltype(name)
           ~~~~~~~~~~~~~^^^^^^
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\ctypes\__init__.py", line 390, in __init__
    self._handle = _dlopen(self._name, mode)
                   ~~~~~~~^^^^^^^^^^^^^^^^^^
FileNotFoundError: Could not find module 'nicai_utf8' (or one of its dependencies). Try using the full path with constructor syntax.

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\site-packages\nidaqmx\_lib.py", line 211, in _import_lib
    windll, cdll = _load_lib("nicaiu")
                   ~~~~~~~~~^^^^^^^^^^
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\site-packages\nidaqmx\_lib.py", line 184, in _load_lib
    windll = ctypes.windll.LoadLibrary(libname)
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\ctypes\__init__.py", line 471, in LoadLibrary
    return self._dlltype(name)
           ~~~~~~~~~~~~~^^^^^^
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\ctypes\__init__.py", line 390, in __init__
    self._handle = _dlopen(self._name, mode)
                   ~~~~~~~^^^^^^^^^^^^^^^^^^
FileNotFoundError: Could not find module 'nicaiu' (or one of its dependencies). Try using the full path with constructor syntax.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\threading.py", line 1043, in _bootstrap_inner
    self.run()
    ~~~~~~~~^^
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\threading.py", line 994, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "c:\HKUST\Code\Python\2025-07\Force Control Experiments-6axis\main.py", line 568, in force_acquisition
    self.force_sensor.start(sampling_rate=FORCE_SAMPLE_RATE)
    ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "c:\HKUST\Code\Python\2025-07\Force Control Experiments-6axis\ForceSensor\ati_mini85.py", line 16, in start
    self.task = nidaqmx.Task()
                ~~~~~~~~~~~~^^
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\site-packages\nidaqmx\task\_task.py", line 97, in __init__
    self._interpreter = utils._select_interpreter(grpc_options)
                        ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\site-packages\nidaqmx\utils.py", line 213, in _select_interpreter
    return LibraryInterpreter()
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\site-packages\nidaqmx\_library_interpreter.py", line 53, in __init__
    self.set_runtime_environment(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        runtime_env,
        ^^^^^^^^^^^^
    ...<2 lines>...
        ''
        ^^
    )
    ^
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\site-packages\nidaqmx\_library_interpreter.py", line 5334, in set_runtime_environment
    cfunc = lib_importer.windll.DAQmxSetRuntimeEnvironment
            ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\site-packages\nidaqmx\_lib.py", line 146, in windll
    self._import_lib()
    ~~~~~~~~~~~~~~~~^^
  File "C:\Users\AANTC-MOTUS\anaconda3\envs\motus\Lib\site-packages\nidaqmx\_lib.py", line 214, in _import_lib
    raise DaqNotFoundError(_DAQ_NOT_FOUND_MESSAGE) from e
nidaqmx.errors.DaqNotFoundError: Could not find an installation of NI-DAQmx. Please ensure that NI-DAQmx is installed on this machine or contact National Instruments for support.

## 一些记录
z比xy范围要小