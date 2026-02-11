from __future__ import annotations

import time
from cryptography.hazmat.primitives.asymmetric import x25519


def x25519_keygen():
    priv = x25519.X25519PrivateKey.generate()
    pub = priv.public_key()
    return priv, pub


def x25519_exchange(priv: x25519.X25519PrivateKey, peer_pub) -> bytes:
    return priv.exchange(peer_pub)


def ecdh_x25519_once() -> bytes:
    a_priv, a_pub = x25519_keygen()
    b_priv, b_pub = x25519_keygen()

    a_shared = x25519_exchange(a_priv, b_pub)
    b_shared = x25519_exchange(b_priv, a_pub)
    assert a_shared == b_shared
    return a_shared


def benchmark_x25519_components(trials: int = 200, batch_size: int = 50) -> dict:
    # Warm-up
    for _ in range(10):
        _ = ecdh_x25519_once()

    keygen_ms = []
    exch_ms = []

    for _ in range(trials):
        # keygen batch (two parties)
        t0 = time.perf_counter()
        pairs = [(x25519_keygen(), x25519_keygen()) for _ in range(batch_size)]
        t1 = time.perf_counter()
        keygen_ms.append(((t1 - t0) * 1000.0) / batch_size)

        # exchange batch (two exchanges)
        t0 = time.perf_counter()
        for (a_priv, a_pub), (b_priv, b_pub) in pairs:
            a_shared = x25519_exchange(a_priv, b_pub)
            b_shared = x25519_exchange(b_priv, a_pub)
            assert a_shared == b_shared
        t1 = time.perf_counter()
        exch_ms.append(((t1 - t0) * 1000.0) / batch_size)

    def stats(xs):
        return {
            "mean_ms": sum(xs) / len(xs),
            "min_ms": min(xs),
            "max_ms": max(xs),
        }

    return {
        "scheme": "X25519",
        "trials": trials,
        "batch_size": batch_size,
        "keygen_pair": stats(keygen_ms),
        "exchange_pair": stats(exch_ms),
        "total_mean_ms": (sum(keygen_ms) + sum(exch_ms)) / len(keygen_ms),
    }


if __name__ == "__main__":
    print(benchmark_x25519_components(trials=100, batch_size=50))
