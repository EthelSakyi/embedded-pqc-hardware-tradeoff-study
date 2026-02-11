from __future__ import annotations

import pandas as pd

INFILE = "data/raw/results.csv"
BASELINE_CONFIG = "classical_ecdh_software"


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def main() -> None:
    df = pd.read_csv(INFILE)

    # Ensure numeric types (energy will be None until hardware is added)
    df["execution_time_ms"] = pd.to_numeric(df["execution_time_ms"], errors="coerce")
    df["energy_J"] = pd.to_numeric(df.get("energy_J", None), errors="coerce")
    df["avg_current_mA"] = pd.to_numeric(df.get("avg_current_mA", None), errors="coerce")
    df["peak_current_mA"] = pd.to_numeric(df.get("peak_current_mA", None), errors="coerce")

    # Basic timing summary
    summary = (
        df.groupby("configuration", as_index=False)
          .agg(
              trials=("execution_time_ms", "count"),
              mean_time_ms=("execution_time_ms", "mean"),
              std_time_ms=("execution_time_ms", "std"),
              min_time_ms=("execution_time_ms", "min"),
              max_time_ms=("execution_time_ms", "max"),
          )
    )

    # Add energy summary only if you actually have non-null energy values
    if df["energy_J"].notna().any():
        energy_summary = (
            df.groupby("configuration", as_index=False)
              .agg(
                  mean_energy_J=("energy_J", "mean"),
                  std_energy_J=("energy_J", "std"),
                  mean_avg_current_mA=("avg_current_mA", "mean"),
                  mean_peak_current_mA=("peak_current_mA", "mean"),
              )
        )
        summary = summary.merge(energy_summary, on="configuration", how="left")

    # Compute overhead vs baseline (timing)
    baseline_row = summary.loc[summary["configuration"] == BASELINE_CONFIG]
    if len(baseline_row) == 1:
        baseline_time = float(baseline_row["mean_time_ms"].iloc[0])
        summary["time_overhead_vs_classical_pct"] = ((summary["mean_time_ms"] - baseline_time) / baseline_time) * 100.0
    else:
        summary["time_overhead_vs_classical_pct"] = None

    # Compute overhead vs baseline (energy) if available
    if "mean_energy_J" in summary.columns and len(baseline_row) == 1:
        baseline_energy = safe_float(
            summary.loc[summary["configuration"] == BASELINE_CONFIG, "mean_energy_J"].iloc[0]
        )
        if baseline_energy is not None:
            summary["energy_overhead_vs_classical_pct"] = ((summary["mean_energy_J"] - baseline_energy) / baseline_energy) * 100.0
        else:
            summary["energy_overhead_vs_classical_pct"] = None

    # Sort: baseline first, then others by mean time
    summary["is_baseline"] = summary["configuration"].eq(BASELINE_CONFIG)
    summary = summary.sort_values(["is_baseline", "mean_time_ms"], ascending=[False, True]).drop(columns=["is_baseline"])

    # Pretty print
    pd.set_option("display.max_columns", 50)
    pd.set_option("display.width", 140)

    print("\n=== RESULTS SUMMARY (Timing + optional Energy) ===\n")
    print(summary.to_string(index=False, justify="left"))

    # Save a processed copy for your docs / plots
    out_csv = "data/processed/summary.csv"
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_csv, index=False)
    print(f"\nSaved summary to: {out_csv}")


if __name__ == "__main__":
    from pathlib import Path
    main()
