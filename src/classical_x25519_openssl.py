from __future__ import annotations

import subprocess
import time


def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDERR:\n{p.stderr}")
    return p.stdout.strip()


def bench_openssl_x25519(trials: int = 50) -> dict:
    """
    Uses OpenSSL's built-in speed benchmark for X25519.

    Note: `openssl speed -seconds N -evp x25519` reports ops/s.
    We convert to ms/op.
    """
    # Run for a few seconds to reduce noise
    seconds = 3

    out = run(["openssl", "speed", "-seconds", str(seconds), "-evp", "x25519"])

    # Parse the last occurrence of a line that contains "x25519"
    # Output format varies, but usually includes something like:
    # "x25519        123456.7 ops/s"
    lines = [ln.strip() for ln in out.splitlines() if "x25519" in ln.lower()]

    if not lines:
        raise RuntimeError(f"Could not find x25519 line in output:\n{out}")

    line = lines[-1]

    # Extract the numeric ops/s
    tokens = line.replace(",", " ").split()
    ops_per_s = None
    for i, tok in enumerate(tokens):
        if tok.lower().endswith("ops/s") and i > 0:
            try:
                ops_per_s = float(tokens[i - 1])
                break
            except Exception:
                pass

    if ops_per_s is None:
        # Fallback: try to find any float token and assume it's ops/s
        for tok in tokens:
            try:
                ops_per_s = float(tok)
                break
            except Exception:
                continue

    if ops_per_s is None or ops_per_s <= 0:
        raise RuntimeError(f"Could not parse ops/s from line:\n{line}\n\nFull output:\n{out}")

    ms_per_op = 1000.0 / ops_per_s

    return {
        "backend": "openssl_cli",
        "scheme": "X25519",
        "seconds": seconds,
        "ops_per_s": ops_per_s,
        "ms_per_op": ms_per_op,
        "raw_line": line,
    }


if __name__ == "__main__":
    t0 = time.perf_counter()
    res = bench_openssl_x25519()
    t1 = time.perf_counter()
    res["wall_time_s"] = t1 - t0
    print(res)
