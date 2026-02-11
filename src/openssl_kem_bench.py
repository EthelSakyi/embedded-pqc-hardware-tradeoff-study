from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass


LINE_RE = re.compile(
    r"Doing\s+(?P<alg>\S+)\s+(?P<phase>keygen|encaps|decaps)\s+ops\s+for\s+\d+s:\s+"
    r"(?P<count>\d+)\s+.+?\s+in\s+(?P<seconds>\d+(\.\d+)?)s",
    re.IGNORECASE,
)


@dataclass
class KemResult:
    alg: str
    phase: str  # keygen / encaps / decaps
    count: int
    seconds: float

    @property
    def ms_per_op(self) -> float:
        return (self.seconds * 1000.0) / self.count


def run_openssl_speed(seconds: int = 3) -> str:
    p = subprocess.run(
        ["openssl", "speed", "-seconds", str(seconds), "-kem-algorithms"],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr or "openssl speed failed")
    return p.stdout


def parse_speed_output(text: str) -> list[KemResult]:
    out: list[KemResult] = []
    for line in text.splitlines():
        m = LINE_RE.search(line)
        if not m:
            continue
        out.append(
            KemResult(
                alg=m.group("alg"),
                phase=m.group("phase").lower(),
                count=int(m.group("count")),
                seconds=float(m.group("seconds")),
            )
        )
    return out


def summarize(results: list[KemResult], alg_filter: str) -> None:
    rows = [r for r in results if alg_filter.lower() in r.alg.lower()]
    if not rows:
        print(f"No matches for filter: {alg_filter}")
        return

    print(f"\n=== OpenSSL KEM benchmark: {alg_filter} ===")
    total = 0.0
    for phase in ("keygen", "encaps", "decaps"):
        r = next((x for x in rows if x.phase == phase), None)
        if r is None:
            continue
        total += r.ms_per_op
        print(f"{r.alg:18s} {phase:6s}  {r.ms_per_op:.5f} ms/op   (count={r.count}, seconds={r.seconds})")
    print(f"TOTAL (sum): {total:.5f} ms/op")


if __name__ == "__main__":
    text = run_openssl_speed(seconds=3)
    results = parse_speed_output(text)

    # Quick summaries you care about
    summarize(results, "X25519")
    summarize(results, "ML-KEM-512")
    summarize(results, "ML-KEM-768")
    summarize(results, "ML-KEM-1024")
    # Optional hybrids:
    summarize(results, "X25519MLKEM768")
