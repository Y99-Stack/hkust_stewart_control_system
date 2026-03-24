import numpy as np

from Mode.force_feedback._force_feedback_core import run_force_feedback_mode


def _lb_force_transform(force: np.ndarray) -> np.ndarray:
    transformed = -np.asarray(force, dtype=float).copy()
    transformed[1:5] = 0.0
    return transformed


def run_mode(**kwargs) -> None:
    run_force_feedback_mode(force_transform=_lb_force_transform, **kwargs)


if __name__ == "__main__":
    run_mode()

