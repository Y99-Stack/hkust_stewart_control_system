"""Helper to validate sine params and (optionally) send command.

This module is intentionally small and unit-test friendly so tests can
exercise the validation + not-connected behavior without touching
`main.py` or a real robot.
"""
from typing import Dict, Optional
from .sinwave_acc_vel_limits import validate_sine_motion
from .pos_limits import validate_position_excursion
from .command_message import CommandMessage, CommandCodes, SubCommandCodes


def check_sine_before_send(controller, amplitude, frequency, show_popup: bool = True) -> Dict:
    """Validate amplitude/frequency for sine motion and optionally send.

    This helper now performs:
      1) position-excursion check (pos limits)
      2) velocity/acceleration check (sine limits)

    Returns a dict with keys:
      - sent: bool (True if a command was actually sent)
      - ok: bool (True if validation passed)
      - reason: Optional[str] ("pos_limit" | "dyn_limit" | "not_connected" | None)
      - summary: Optional[str] (human-readable diagnostic when not ok)
      - would_send: bool (True if validation passed but controller not connected)
    """
    result = {"sent": False, "ok": True, "reason": None, "summary": None, "would_send": False}

    # 1) position excursion check
    pos_ok, pos_details = validate_position_excursion(amplitude, method='pairwise')
    if not pos_ok:
        # build summary
        msgs = []
        for fail in pos_details.get('pairwise', {}).get('failing_pairs', []):
            (i, j) = fail['pair'] if 'pair' in fail else fail.get('pair', (None, None))
            msgs.append(f"轴({i},{j}) 可达投影超限 (metric={fail['metric']:.3f})")
        summary = "检测到位置可达性超限：\n" + ("\n".join(msgs) if msgs else str(pos_details))
        result.update({"ok": False, "reason": "pos_limit", "summary": summary})
        if show_popup:
            try:
                import tkinter as _tk
                from tkinter import messagebox as _mb
                root = _tk.Tk(); root.withdraw()
                _mb.showwarning("位置可达超限 - 未下发指令", summary)
                root.destroy()
            except Exception:
                pass
        return result

    # 2) dynamic (velocity/acceleration) check
    dyn_ok, dyn_details = validate_sine_motion(amplitude, frequency)
    if not dyn_ok:
        axis_names = ["Rx", "Ry", "Rz", "X", "Y", "Z"]
        msgs = []
        for p in dyn_details["per_axis"]:
            if p["v_exceeded"] or p["a_exceeded"]:
                parts = []
                if p["v_exceeded"]:
                    parts.append(f"速度 {p['v_peak']:.3f} > 限值 {p['v_limit']:.3f}")
                if p["a_exceeded"]:
                    parts.append(f"加速度 {p['a_peak']:.3f} > 限值 {p['a_limit']:.3f}")
                msgs.append(f"{axis_names[p['axis']]}: " + "; ".join(parts))
        summary = "检测到正弦运动速度/加速度超限：\n" + "\n".join(msgs)
        result.update({"ok": False, "reason": "dyn_limit", "summary": summary})
        if show_popup:
            try:
                import tkinter as _tk
                from tkinter import messagebox as _mb
                root = _tk.Tk(); root.withdraw()
                _mb.showwarning("运动超限 - 未下发指令", summary)
                root.destroy()
            except Exception:
                pass
        return result

    # validation passed
    connected = getattr(controller, "_is_connected", False) or getattr(controller, "is_connected", False)
    if not connected:
        result.update({"would_send": True, "reason": "not_connected"})
        return result

    # connected -> send command
    cmd = CommandMessage(
        command_code=CommandCodes.CommandMoving,
        sub_command_code=SubCommandCodes.SineWave,
        amplitude_array=amplitude,
        frequency_array=frequency,
    )
    controller.send_command(cmd)
    result.update({"sent": True})
    return result