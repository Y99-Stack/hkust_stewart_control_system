# csv_mode
PS: 联系厂家确认index
1. 基础用法
python main.py --mode csv_move

2. 指定文件和监控时间
python main.py --mode csv_move --csv-path data/my_script.txt --script-monitor 0.5

3. 完整参数
python main.py --mode csv_move --csv-path data/wave/example2.txt --script-index 2 --script-monitor 1.0

# point_move
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

# sin_move
1. 基础正弦波（6个自由度）
python main.py --mode sin_move --sin-amplitude 0.1 0.1 0.1 0.0 0.0 0.0 --sin-frequency 1.0 1.0 1.0 0.0 0.0 0.0

2. 完整参数（带相位和监控）
python main.py --mode sin_move \
    --sin-amplitude 0.1 0.1 0.1 0.0 0.0 0.0 \
    --sin-frequency 1.0 1.0 1.0 0.0 0.0 0.0 \
    --sin-phase 0.0 0.0 0.0 0.0 0.0 0.0 \
    --sin-monitor 0.5