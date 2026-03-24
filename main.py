import argparse

from Mode import list_modes, run_mode

DEFAULT_MODE = "point_move"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Force control mode runner")
    parser.add_argument(
        "--mode",
        default=DEFAULT_MODE,
        choices=list_modes(),
        help="Mode name to run",
    )

    parser.add_argument(
        "--csv-path",
        default="data/wave/example2.txt",
        help="Script file path for csv_move format validation",
    )
    parser.add_argument(
        "--script-index",
        type=int,
        default=None,
        help="Internal script index for WorkingWithScript mode (optional)",
    )
    parser.add_argument(
        "--script-monitor",
        type=float,
        default=0.0,
        help="Feedback monitor seconds after sending WorkingWithScript command",
    )

    parser.add_argument(
        "--rt-interval",
        type=float,
        default=0.1,
        help="Time interval between two rt_move target positions",
    )

    parser.add_argument(
        "--point-dofs",
        type=float,
        nargs=6,
        metavar=("DOF1", "DOF2", "DOF3", "DOF4", "DOF5", "DOF6"),
        help="Target DOFs for point_move mode",
    )
    parser.add_argument(
        "--point-speed",
        type=float,
        nargs=6,
        metavar=("S1", "S2", "S3", "S4", "S5", "S6"),
        help="Optional speed array for point_move mode",
    )

    parser.add_argument(
        "--sin-amplitude",
        type=float,
        nargs=6,
        metavar=("A1", "A2", "A3", "A4", "A5", "A6"),
        help="Amplitude array for sin_move mode",
    )
    parser.add_argument(
        "--sin-frequency",
        type=float,
        nargs=6,
        metavar=("F1", "F2", "F3", "F4", "F5", "F6"),
        help="Frequency array for sin_move mode",
    )
    parser.add_argument(
        "--sin-phase",
        type=float,
        nargs=6,
        metavar=("P1", "P2", "P3", "P4", "P5", "P6"),
        help="Phase array for sin_move mode",
    )
    parser.add_argument(
        "--sin-monitor",
        type=float,
        default=0.0,
        help="Feedback monitor seconds for sin_move mode",
    )

    return parser


def build_mode_kwargs(args: argparse.Namespace) -> dict:
    if args.mode == "csv_move":
        return {
            "script_file_index": args.script_index,
            "script_path": args.csv_path,
            "monitor_seconds": args.script_monitor,
        }

    if args.mode == "rt_move":
        return {
            "position_interval": args.rt_interval,
        }

    if args.mode == "point_move":
        return {
            "target_dofs": args.point_dofs,
            "speed": args.point_speed,
        }

    if args.mode == "sin_move":
        return {
            "amplitude_array": args.sin_amplitude,
            "frequency_array": args.sin_frequency,
            "phase_array": args.sin_phase,
            "monitor_seconds": args.sin_monitor,
        }

    return {}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    mode_kwargs = build_mode_kwargs(args)
    run_mode(args.mode, **mode_kwargs)


if __name__ == "__main__":
    main()
