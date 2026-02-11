from __future__ import annotations

import csv
import time
from pathlib import Path

from measurement import MeasurementSession
from classical_ecdh import ecdh_x25519_once
from pqc_mlkem import pick_kem_name, mlkem_once


OUT = Path("data/raw/results.csv")

FIELDNAMES = [
    "timestamp",
    "configuration",
    "trial",
    "execution_time_ms",
    "energy_J",
    "avg_current_mA",
    "peak_current_mA",
]


def ensure_output_file() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUT.exists():
        with OUT.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES)
            w.writeheader()


def append_row(row: dict) -> None:
    ensure_output_file()
    with OUT.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writerow(row)


def run_trials_ecdh(configuration: str, trials: int = 200, warmup: int = 5) -> None:
    # Warm-up to reduce first-run noise
    for _ in range(warmup):
        _ = ecdh_x25519_once()

    for i in range(trials):
        with MeasurementSession() as ms:
            t0 = time.perf_counter()
            _ = ecdh_x25519_once()
            t1 = time.perf_counter()

        row = {
            "timestamp": time.time(),
            "configuration": configuration,
            "trial": i,
            "execution_time_ms": (t1 - t0) * 1000.0,
            **ms.results(),
        }
        append_row(row)


def run_trials_mlkem(configuration_prefix: str, trials: int = 200, warmup: int = 5) -> None:
    kem_name = pick_kem_name()
    configuration = f"{configuration_prefix}_{kem_name}"

    # Warm-up
    for _ in range(warmup):
        mlkem_once(kem_name)

    batch_size = 50  # number of KEM ops per timing block

    for i in range(trials):
        with MeasurementSession() as ms:
            t0 = time.perf_counter()

            for _ in range(batch_size):
                mlkem_once(kem_name)

            t1 = time.perf_counter()

        # Store per-operation time (ms) by dividing total batch time by batch_size
        execution_time_ms = ((t1 - t0) * 1000.0) / batch_size

        row = {
            "timestamp": time.time(),
            "configuration": configuration,
            "trial": i,
            "execution_time_ms": execution_time_ms,
            **ms.results(),
        }
        append_row(row)


if __name__ == "__main__":
    # NOTE: This appends to data/raw/results.csv.
    # If you want a fresh file each run, delete data/raw/results.csv first.
    run_trials_ecdh(configuration="classical_ecdh_software", trials=200)
    run_trials_mlkem(configuration_prefix="pqc_mlkem_software", trials=200)
    print(f"Saved results to {OUT}")
