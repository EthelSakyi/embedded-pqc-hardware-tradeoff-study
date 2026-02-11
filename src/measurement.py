from __future__ import annotations
import time


class MeasurementSession:
    """Placeholder measurement session (no hardware yet)."""

    def __init__(self) -> None:
        self.start = 0.0
        self.end = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.end = time.perf_counter()

    def results(self) -> dict:
        return {
            "energy_J": None,
            "avg_current_mA": None,
            "peak_current_mA": None,
        }
