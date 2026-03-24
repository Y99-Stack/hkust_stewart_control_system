import numpy as np

from Mode.force_feedback._force_feedback_core import run_force_feedback_mode


def _arbitrary_force_transform(force: np.ndarray) -> np.ndarray:
    return -np.asarray(force, dtype=float)


def run_mode(**kwargs) -> None:
    run_force_feedback_mode(
        force_transform=_arbitrary_force_transform,
        use_force_sensor=True,
        **kwargs,
    )


if __name__ == "__main__":
    run_mode()

