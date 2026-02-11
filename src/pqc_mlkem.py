from __future__ import annotations

import time
import oqs

CANDIDATE_KEMS = [
    "ML-KEM-512",
    "ML-KEM-768",
    "ML-KEM-1024",
    "Kyber512",
    "Kyber768",
    "Kyber1024",
]


def pick_kem_name() -> str:
    enabled = set(oqs.get_enabled_kem_mechanisms())
    for name in CANDIDATE_KEMS:
        if name in enabled:
            return name
    raise RuntimeError(f"No ML-KEM/Kyber found. Enabled KEMs sample: {list(enabled)[:30]}")


def mlkem_keygen(kem_name: str):
    kem = oqs.KeyEncapsulation(kem_name)
    pk = kem.generate_keypair()
    return kem, pk


def mlkem_encap(kem_name: str, pk: bytes):
    with oqs.KeyEncapsulation(kem_name) as kem:
        ct, ss = kem.encap_secret(pk)
        return ct, ss


def mlkem_decap(kem_name: str, ct: bytes, kem_obj: oqs.KeyEncapsulation, ss_expected: bytes):
    ss = kem_obj.decap_secret(ct)
    assert ss == ss_expected
    return ss


def benchmark_mlkem_components(trials: int = 200, batch_size: int = 50) -> dict:
    kem_name = pick_kem_name()

    # Warm-up
    for _ in range(10):
        kem, pk = mlkem_keygen(kem_name)
        ct, ss = mlkem_encap(kem_name, pk)
        _ = mlkem_decap(kem_name, ct, kem, ss)

    keygen_ms = []
    encap_ms = []
    decap_ms = []

    for _ in range(trials):
        # --- keygen batch ---
        t0 = time.perf_counter()
        pairs = [mlkem_keygen(kem_name) for _ in range(batch_size)]
        t1 = time.perf_counter()
        keygen_ms.append(((t1 - t0) * 1000.0) / batch_size)

        # --- encap batch (reuse keypairs) ---
        pks = [pk for (kem, pk) in pairs]
        t0 = time.perf_counter()
        encap_out = [mlkem_encap(kem_name, pk) for pk in pks]
        t1 = time.perf_counter()
        encap_ms.append(((t1 - t0) * 1000.0) / batch_size)

        # --- decap batch (reuse kem objects + matching ct/ss) ---
        t0 = time.perf_counter()
        for (kem, _pk), (ct, ss) in zip(pairs, encap_out):
            _ = mlkem_decap(kem_name, ct, kem, ss)
        t1 = time.perf_counter()
        decap_ms.append(((t1 - t0) * 1000.0) / batch_size)

    def stats(xs):
        return {
            "mean_ms": sum(xs) / len(xs),
            "min_ms": min(xs),
            "max_ms": max(xs),
        }

    return {
        "kem": kem_name,
        "trials": trials,
        "batch_size": batch_size,
        "keygen": stats(keygen_ms),
        "encap": stats(encap_ms),
        "decap": stats(decap_ms),
        "total_mean_ms": (sum(keygen_ms) + sum(encap_ms) + sum(decap_ms)) / len(keygen_ms),
    }


if __name__ == "__main__":
    print(benchmark_mlkem_components(trials=100, batch_size=50))
