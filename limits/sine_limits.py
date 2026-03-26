from dof_controller.command_message import validate_sine_motion


def test_single_axis_within_limits():
    amps = [0.1, 0, 0, 0, 0, 0]
    freqs = [0.5, 0, 0, 0, 0, 0]
    ok, details = validate_sine_motion(amps, freqs)
    assert ok is True
    assert details["moving_count"] == 1


def test_single_axis_exceeds_velocity():
    # amplitude=1 deg, f=10Hz -> v_peak ~= 62.8 deg/s (exceeds 40)
    amps = [1.0, 0, 0, 0, 0, 0]
    freqs = [10.0, 0, 0, 0, 0, 0]
    ok, details = validate_sine_motion(amps, freqs)
    assert ok is False
    per0 = details["per_axis"][0]
    assert per0["v_exceeded"] is True


def test_three_axes_halved_limits_trigger():
    # choose parameters that are OK under full limits but exceed when limits are halved
    # amp=1deg, f=6Hz -> v_peak ~= 37.7 (OK vs 40), but halved limit -> 20 -> exceed
    amps = [1.0, 1.0, 1.0, 0, 0, 0]
    freqs = [6.0, 6.0, 6.0, 0, 0, 0]
    ok, details = validate_sine_motion(amps, freqs)
    assert ok is False
    assert details["moving_count"] == 3
    assert details["factor_applied"] == 0.5
    assert any(p["v_exceeded"] for p in details["per_axis"]) is True