"""Sine-wave peak velocity/acceleration calculator and validator.

Moved out of CommandMessage so motion-limit logic is in a single, testable module.
Functions:
- _sine_peak_vel_acc(amplitude, frequency) -> (v_peak, a_peak)
- validate_sine_motion(amplitude_array, frequency_array, ...)

Units: same as caller (degrees and meters as described in repo docs).
"""
from typing import Iterable, List, Tuple
import math


def _sine_peak_vel_acc(amplitude: float, frequency: float) -> Tuple[float, float]:
    """Return (v_peak, a_peak) for x = A * sin(2π f t)."""
    omega = 2.0 * math.pi * abs(frequency)
    v_peak = omega * abs(amplitude)
    a_peak = (omega ** 2) * abs(amplitude)
    return v_peak, a_peak


def validate_sine_motion(amplitude_array: Iterable[float],
                         frequency_array: Iterable[float],
                         vel_limits: List[float] = None,
                         acc_limits: List[float] = None,
                         moving_axes_threshold: int = 2,
                         eps: float = 1e-9):
    """Validate sine-wave motion (per-axis) against limits.

    Returns (is_ok: bool, details: dict).
    - amplitude_array and frequency_array must be length 6.
    - Default limits match project spec (degrees/m):
        vel_limits = [40,40,40,0.5,0.5,0.5]
        acc_limits = [90,90,90,5.0,5.0,5.0]
    - If more than `moving_axes_threshold` axes move, per-axis limits are halved.
    """
    if vel_limits is None:
        vel_limits = [40.0, 40.0, 40.0, 0.5, 0.5, 0.5]
    if acc_limits is None:
        acc_limits = [90.0, 90.0, 90.0, 5.0, 5.0, 5.0]

    amps = list(amplitude_array)
    freqs = list(frequency_array)
    if len(amps) != 6 or len(freqs) != 6:
        raise ValueError("amplitude_array and frequency_array must be length 6")

    moving = [i for i, (A, f) in enumerate(zip(amps, freqs)) if (abs(A) > eps and abs(f) > eps)]
    moving_count = len(moving)

    factor = 0.5 if moving_count > moving_axes_threshold else 1.0
    effective_vel_limits = [lv * factor for lv in vel_limits]
    effective_acc_limits = [la * factor for la in acc_limits]

    per_axis = []
    any_exceeded = False
    for i, (A, f, lv, la) in enumerate(zip(amps, freqs, effective_vel_limits, effective_acc_limits)):
        v_peak, a_peak = _sine_peak_vel_acc(A, f)
        v_exceeded = v_peak > lv + 1e-12
        a_exceeded = a_peak > la + 1e-12
        if v_exceeded or a_exceeded:
            any_exceeded = True
        per_axis.append({
            "axis": i,
            "amplitude": A,
            "frequency": f,
            "v_peak": v_peak,
            "a_peak": a_peak,
            "v_limit": lv,
            "a_limit": la,
            "v_exceeded": v_exceeded,
            "a_exceeded": a_exceeded,
        })

    details = {
        "moving_count": moving_count,
        "factor_applied": factor,
        "per_axis": per_axis,
        "any_exceeded": any_exceeded,
    }
    return (not any_exceeded), details