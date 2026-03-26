"""Position reachability / excursion limits for the 6-DOF platform.

Behavior implemented:
- Per-axis hard limits (max_abs per axis).
- Identification of which axes participate (non-zero amplitude).
- Pairwise (two-axis) reachable-area check using an L1-style convex hull:
    A point (x,y) is reachable for axes i,j if |x|/max_i + |y|/max_j <= 1.
  For sine excursions we check the rectangle corners (±A_i, ±A_j) which
  reduces to A_i/max_i + A_j/max_j <= 1.
- A conservative multi-axis approximate check using an ellipsoid metric:
    sqrt(sum( (A_i / max_i)**2 )) <= 1

API:
- axes_involved(amplitude_array) -> list[int]
- check_single_axis(amplitude_array) -> (ok, details)
- check_pairwise_amplitudes(amplitude_array) -> (ok, details)
- check_multi_axis_ellipsoid(amplitude_array) -> (ok, details)
- validate_position_excursion(amplitude_array, method='pairwise') -> (ok, details)

Units: degrees for Rx,Ry,Rz and meters for X,Y,Z. amplitude_array length must be 6.
"""
from typing import List, Tuple, Dict
import math

# maximum absolute reachable positions for each DOF (single-axis)
MAX_POS = [23.0, 24.0, 30.0, 0.32, 0.32, 0.23]
MIN_POS = [-m for m in MAX_POS]


def _validate_len(arr):
    if len(arr) != 6:
        raise ValueError("array must be length 6")


def axes_involved(amplitude_array: List[float], eps: float = 1e-9) -> List[int]:
    """Return indices of axes whose amplitude is non-negligible."""
    _validate_len(amplitude_array)
    return [i for i, a in enumerate(amplitude_array) if abs(a) > eps]


def check_single_axis(amplitude_array: List[float]) -> Tuple[bool, Dict]:
    """Check single-axis reachability: amplitude must be <= max_abs for that axis.

    Returns (ok, details) where details contains per-axis ratios and any exceeded axes.
    """
    _validate_len(amplitude_array)
    per_axis = []
    any_exceeded = False
    for i, A in enumerate(amplitude_array):
        ratio = abs(A) / MAX_POS[i]
        exceeded = ratio > 1.0
        if exceeded:
            any_exceeded = True
        per_axis.append({"axis": i, "amplitude": A, "ratio": ratio, "exceeded": exceeded, "limit": MAX_POS[i]})
    details = {"per_axis": per_axis, "any_exceeded": any_exceeded}
    return (not any_exceeded), details


def check_pairwise_amplitudes(amplitude_array: List[float]) -> Tuple[bool, Dict]:
    """For every pair of involved axes (i,j) check the L1-condition:
       A_i / MAX_i + A_j / MAX_j <= 1
    Returns (ok, details) with failing pairs listed.
    """
    _validate_len(amplitude_array)
    involved = axes_involved(amplitude_array)
    failing = []
    checked = []
    for idx in range(len(involved)):
        for jdx in range(idx + 1, len(involved)):
            i = involved[idx]
            j = involved[jdx]
            Ai = abs(amplitude_array[i])
            Aj = abs(amplitude_array[j])
            val = Ai / MAX_POS[i] + Aj / MAX_POS[j]
            ok = val <= 1.0 + 1e-12
            checked.append({"pair": (i, j), "Ai": Ai, "Aj": Aj, "metric": val, "ok": ok, "limits": (MAX_POS[i], MAX_POS[j])})
            if not ok:
                failing.append({"pair": (i, j), "metric": val, "threshold": 1.0})
    details = {"involved": involved, "checked_pairs": checked, "failing_pairs": failing}
    return (len(failing) == 0), details


def check_multi_axis_ellipsoid(amplitude_array: List[float]) -> Tuple[bool, Dict]:
    """Conservative ellipsoid approximation for N-axis simultaneous motion.

    Condition: sqrt(sum (A_i / MAX_i)^2) <= 1
    Returns (ok, details) with the computed ellipsoid metric.
    """
    _validate_len(amplitude_array)
    s = 0.0
    comps = []
    for i, A in enumerate(amplitude_array):
        comp = (abs(A) / MAX_POS[i]) ** 2
        comps.append(comp)
        s += comp
    metric = math.sqrt(s)
    ok = metric <= 1.0 + 1e-12
    details = {"metric": metric, "components": comps, "ok": ok}
    return ok, details


def validate_position_excursion(amplitude_array: List[float], method: str = "pairwise") -> Tuple[bool, Dict]:
    """Top-level validator.

    method:
      - 'pairwise' (default): perform single-axis check and pairwise checks for all
         involved axes. Passes only if single-axis OK and all pairwise checks OK.
      - 'ellipsoid': use the conservative ellipsoid approximation.

    Returns (ok, details) where details merges relevant sub-checks.
    """
    _validate_len(amplitude_array)
    single_ok, single_details = check_single_axis(amplitude_array)
    if not single_ok:
        return False, {"method": "single_axis", "single": single_details}

    if method == "pairwise":
        pair_ok, pair_details = check_pairwise_amplitudes(amplitude_array)
        return pair_ok, {"method": "pairwise", "single": single_details, "pairwise": pair_details}
    elif method == "ellipsoid":
        ell_ok, ell_details = check_multi_axis_ellipsoid(amplitude_array)
        return ell_ok, {"method": "ellipsoid", "single": single_details, "ellipsoid": ell_details}
    else:
        raise ValueError("unknown method: %s" % method)

def scale_amplitude_to_reachable(amplitude, pos_details):
    """
    当位置超限时，等比例缩小幅值使其在可达空间内。
    返回调整后的幅值列表和缩放因子。
    pos_details 应该是 validate_position_excursion 返回的结构。
    """
    min_scale = 1.0
    
    # 情况1：单轴超限
    if pos_details.get("method") == "single_axis":
        per_axis = pos_details.get("single", {}).get("per_axis", [])
        for axis_info in per_axis:
            if axis_info.get("exceeded", False):
                ratio = axis_info.get("ratio", 1.0)
                if ratio > 1.0:
                    scale = 1.0 / ratio
                    min_scale = min(min_scale, scale)
    
    # 情况2：pairwise 超限
    elif pos_details.get("method") == "pairwise":
        failing_pairs = pos_details.get("pairwise", {}).get("failing_pairs", [])
        for pair_info in failing_pairs:
            metric = pair_info.get("metric", 1.0)
            if metric > 1.0:
                scale = 1.0 / metric
                min_scale = min(min_scale, scale)
    
    # 情况3：ellipsoid 超限
    elif pos_details.get("method") == "ellipsoid":
        ellipsoid = pos_details.get("ellipsoid", {})
        if not ellipsoid.get("ok", True):
            metric = ellipsoid.get("metric", 1.0)
            if metric > 1.0:
                min_scale = 1.0 / metric
    
    if min_scale >= 1.0:
        return amplitude, 1.0
    
    # 应用最小缩放因子到所有幅值，并乘以安全系数以避免浮点精度问题
    safety_factor = 0.999
    scaled_amplitude = [a * min_scale * safety_factor for a in amplitude]
    return scaled_amplitude, min_scale * safety_factor

# # test
# # 示例使用
# amplitudes = [0.0, 40.0, 0.0, 0.1, 0.05, 0.0]  # Rx=10°, Ry=15°, X=0.1m, Y=0.05m

# # 基本检查
# ok, details = validate_position_excursion(amplitudes, method='pairwise')
# if ok:
#     print("位置可达")
# else:
#     print("位置不可达")
#     print(details)

# # 或者分别检查
# single_ok, single_details = check_single_axis(amplitudes)
# pair_ok, pair_details = check_pairwise_amplitudes(amplitudes)