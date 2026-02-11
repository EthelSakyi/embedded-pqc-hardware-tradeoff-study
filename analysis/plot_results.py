from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

INFILE = "data/raw/results.csv"
OUTDIR = Path("data/processed")


def plot_bar_with_error(df: pd.DataFrame, value_col: str, err_col: str, title: str, ylabel: str, outpath: Path) -> None:
    plt.figure()
    plt.bar(df["configuration"], df[value_col], yerr=df[err_col])
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    print(f"Saved plot: {outpath}")


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INFILE)
    df["execution_time_ms"] = pd.to_numeric(df["execution_time_ms"], errors="coerce")
    df["energy_J"] = pd.to_numeric(df.get("energy_J", None), errors="coerce")

    # Timing summary for plotting
    timing = df.groupby("configuration")["execution_time_ms"].agg(["mean", "std"]).reset_index()
    timing = timing.sort_values("mean", ascending=True)

    plot_bar_with_error(
        timing,
        value_col="mean",
        err_col="std",
        title="Execution Time by Configuration (mean ± std)",
        ylabel="Execution time (ms)",
        outpath=OUTDIR / "timing_mean_with_std.png",
    )

    # Energy plot only if energy exists
    if df["energy_J"].notna().any():
        energy = df.groupby("configuration")["energy_J"].agg(["mean", "std"]).reset_index()
        energy = energy.sort_values("mean", ascending=True)

        plot_bar_with_error(
            energy,
            value_col="mean",
            err_col="std",
            title="Energy per Operation by Configuration (mean ± std)",
            ylabel="Energy (J)",
            outpath=OUTDIR / "energy_mean_with_std.png",
        )


if __name__ == "__main__":
    main()
