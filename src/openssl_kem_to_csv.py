from __future__ import annotations

import csv
import re
import subprocess
import time
from pathlib import Path


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

LINE_RE = re.compile(
    r"Doing\s+(?P<alg>\S+)\s+(?P<phase>keygen|encaps|decaps)\s+ops\s+for\s+\d+s:\s+"
    r"(?P<count>\d+)\s+.+?\s+in\s+(?P<seconds>\d+(\.\d+)?)s",
    re.IGNORECASE,
)

# Algorithms we care about (add more later if you want)
TARGET_ALGS = [
    "X25519",
    "ML-KEM-512",
    "ML-KEM-768",
    "ML-KEM-1024",
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


def run_openssl_speed(seconds: int = 3) -> str:
    p = subprocess.run(
        ["openssl", "speed", "-seconds", str(seconds), "-kem-algorithms"],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr or "openssl speed failed")
    return p.stdout


def parse_output(text: str) -> dict[tuple[str, str], float]:
    """
    Returns mapping: (alg, phase) -> ms_per_op
    phase is one of: keygen, encaps, decaps
    """
    results: dict[tuple[str, str], float] = {}
    for line in text.splitlines():
        m = LINE_RE.search(line)
        if not m:
            continue
        alg = m.group("alg")
        phase = m.group("phase").lower()
        count = int(m.group("count"))
        seconds = float(m.group("seconds"))
        ms_per_op = (seconds * 1000.0) / count
        results[(alg, phase)] = ms_per_op
    return results


def main() -> None:
    seconds = 3
    text = run_openssl_speed(seconds=seconds)
    ms_map = parse_output(text)

    now = time.time()

    for alg in TARGET_ALGS:
        for phase in ("keygen", "encaps", "decaps"):
            key = (alg, phase)
            if key not in ms_map:
                continue

            ms_per_op = ms_map[key]
            configuration = f"openssl_{alg}_{phase}"

            append_row(
                {
                    "timestamp": now,
                    "configuration": configuration,
                    "trial": 0,
                    "execution_time_ms": ms_per_op,
                    "energy_J": None,
                    "avg_current_mA": None,
                    "peak_current_mA": None,
                }
            )

    print(f"Appended OpenSSL KEM ms/op rows to {OUT}")


if __name__ == "__main__":
    main()
