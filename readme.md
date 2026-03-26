# 6-Axis-Stewart-Force-Control
pip install -r requirements.txt
## csv_mode
PS: 联系厂家确认index
1. 基础用法
python main.py --mode csv_move

2. 指定文件和监控时间
python main.py --mode csv_move --csv-path data/my_script.txt --script-monitor 0.5

3. 完整参数
python main.py --mode csv_move --csv-path data/wave/example2.txt --script-index 2 --script-monitor 1.0

## point_move
0. base
python main.py
1. poistion
python main.py --point-dofs 0.1 0.2 0.3 0.0 0.0 0.0
1. speed
python main.py --point-dofs 0.1 0.2 0.3 0.0 0.0 0.0 --point-speed 0.5 0.5 0.5 0.2 0.2 0.2

# rt_move
1. 基础用法（默认间隔0.1秒）
python main.py --mode rt_move

2. 指定间隔
python main.py --mode rt_move --rt-interval 0.05

## sin_move
1. 基础正弦波（6个自由度）
python main.py --mode sin_move --sin-amplitude 0.1 0.1 0.1 0.0 0.0 0.0 --sin-frequency 1.0 1.0 1.0 0.0 0.0 0.0

2. 完整参数（带相位和监控）
python main.py --mode sin_move \
    --sin-amplitude 0.1 0.1 0.1 0.0 0.0 0.0 \
    --sin-frequency 1.0 1.0 1.0 0.0 0.0 0.0 \
    --sin-phase 0.0 0.0 0.0 0.0 0.0 0.0 \
    --sin-monitor 0.5

## steady_lb_force_input
1. 基础用法（固定力，默认MDK和六轴全开，不接传感器）
python main.py --mode steady_lb_force_input --force-fixed "[0,0,10,0,0,0]"

2. 固定力 + 先接入力传感器（读取后仍用固定力）
python main.py --mode steady_lb_force_input --force-fixed "[0,0,10,0,0,0]" --force-use-sensor

3. 完整参数（自定义MDK和六轴开关）
python main.py --mode steady_lb_force_input \
    --force-fixed "[0,0,10,0,0,0]" \
    --force-axes "[1,1,1,1,0,1]" \
    --force-m "[2,100,100,500,500,2]" \
    --force-d "[2.3,100,100,500,500,16]" \
    --force-k "[10,100,100,500,500,100]"

4. 交互式输入（可在终端逐项输入MDK、六轴开关、是否接传感器、固定力）
python Mode/force_feedback/steady_lb_force_input.py

## steady_arbitary_force_input
1. 基础用法（必须接入力传感器）
python main.py --mode steady_arbitary_force_input

2. 自定义六轴开关
python main.py --mode steady_arbitary_force_input --force-axes "[1,1,1,1,0,1]"

3. 自定义MDK（六轴数组）
python main.py --mode steady_arbitary_force_input \
    --force-m "[2,100,100,500,500,2]" \
    --force-d "[2.3,100,100,500,500,16]" \
    --force-k "[10,100,100,500,500,100]"

## seawave_arbitray_force_input
1. 基础用法（默认波形文件 data/wave/example1.txt，每周期逐行读取并循环，叠加传感器力控）
python main.py --mode seawave_arbitray_force_input

2. 指定seawave文件（支持.txt或.csv）
python main.py --mode seawave_arbitray_force_input --wave-path data/wave/my_wave.csv

3. 完整参数（六轴MDK + 六轴开关 + 自定义波形文件）
python main.py --mode seawave_arbitray_force_input \
    --wave-path data/wave/example1.txt \
    --force-axes "[1,1,1,1,1,1]" \
    --force-m "[2,100,100,500,500,2]" \
    --force-d "[2.3,100,100,500,500,16]" \
    --force-k "[10,100,100,500,500,100]"

## seawave_lb_force_input
1. 基础用法（默认波形文件 data/wave/example1.txt，每周期逐行读取并循环，叠加固定力，不接传感器）
python main.py --mode seawave_lb_force_input --force-fixed "[0,0,10,0,0,0]"

2. 固定力 + 可选接入力传感器
python main.py --mode seawave_lb_force_input \
    --force-fixed "[0,0,10,0,0,0]" \
    --force-use-sensor

3. 指定seawave文件（支持.txt或.csv）+ 六轴MDK/六轴开关
python main.py --mode seawave_lb_force_input \
    --force-fixed "[0,0,10,0,0,0]" \
    --wave-path data/wave/my_wave.csv \
    --force-axes "[1,1,1,1,1,1]" \
    --force-m "[2,100,100,500,500,2]" \
    --force-d "[2.3,100,100,500,500,16]" \
    --force-k "[10,100,100,500,500,100]"
