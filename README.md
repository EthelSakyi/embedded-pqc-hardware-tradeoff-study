# Hardware–Software Tradeoff Study for Post-Quantum Cryptography  
## Detailed Progress Report (Software Phase)

Author: Ethel Sakyi  
Platform: macOS 15.6.1 (ARM64 / Apple Silicon)  
Python: 3.11.14  
liboqs: 0.14.0  
liboqs-python: 0.14.0  
OpenSSL: 3.6.1  

---

# 1. Project Objective

The purpose of this project is to evaluate the performance tradeoffs between classical cryptography and post-quantum cryptography (PQC), specifically:

- Execution time (completed)
- Energy consumption (planned for hardware phase)
- Current draw (planned for hardware phase)
- Embedded deployment feasibility

The broader research goal is to determine whether ML-KEM (Kyber) is realistically deployable on embedded systems compared to classical X25519 ECDH.

---

# 2. What We Have Done So Far (High-Level Summary)

We completed a full software prototype of the benchmarking pipeline:

1. Set up a clean Python 3.11 virtual environment on macOS ARM64.
2. Installed and verified liboqs-python and cryptography toolchains.
3. Implemented classical baseline benchmark (X25519 ECDH).
4. Implemented PQC benchmark (ML-KEM via liboqs-python).
5. Implemented an experiment runner that writes raw results to CSV.
6. Implemented analysis scripts to summarize, compare, and plot results.
7. Verified the runtime results and produced summary.csv and plots.

---

# 3. Roadblocks Encountered and How They Were Handled

## 3.1 Python Version Conflict When Installing oqs/liboqs-python

### Problem
Initial `pip install oqs` failed, showing messages like:
- “Ignored versions that require a different python version … Requires-Python >=3.10”
- “No matching distribution found for oqs”

### Root Cause
The project originally ran under Python 3.9.x, but modern liboqs-python packages require Python >= 3.10.

### Resolution
- Installed Python 3.11 via Homebrew
- Recreated `.venv` using Python 3.11
- Reinstalled dependencies

After switching, `pip install oqs` succeeded.

---

## 3.2 API Mismatch: Using Non-Existent OQS Functions

### Problem
We attempted calls that do not exist in your installed oqs module:
- `oqs.get_enabled_KEM_mechanisms()` (wrong casing)
- `oqs.build_info()` (not present)
- `oqs.__version__` (not present)

### Root Cause
The liboqs-python API exposes versions and mechanisms through different attributes/functions.

### Resolution
We inspected the module via `dir(oqs)` and switched to valid APIs:
- `oqs.get_enabled_kem_mechanisms()`
- `oqs.oqs_version()`
- `oqs.oqs_python_version()`
- `oqs.OQS_VERSION` (constant)

Confirmed:
- liboqs: 0.14.0
- liboqs-python: 0.14.0
- enabled KEMs include ML-KEM-512/768/1024

---

## 3.3 NameError in the ML-KEM Trial Runner

### Problem
The runner crashed with:
- `NameError: name 'kem_name' is not defined`

### Root Cause
Inside `run_trials_mlkem()`, the code called `mlkem_once(kem_name)` but never initialized `kem_name`.

### Resolution
We updated the runner so that `kem_name` is selected before use, using your helper:
- `kem_name = pick_kem_name()`

We also fixed a second issue in the same function:
- writing `configuration` into the CSV row, even though the function only had `configuration_prefix`.

So the runner now creates:
- configuration string like `pqc_mlkem_software_ML-KEM-512`

---

## 3.4 OpenSSL Benchmarking Failure Using EVP Mode for X25519

### Problem
This command failed:
- `openssl speed -seconds 3 -evp x25519`

Error:
- “x25519 is an unknown cipher or digest”
- “unsupported … evp_fetch … Algorithm (x25519 …)”

### Root Cause
In OpenSSL 3.x, X25519 is not benchmarked via `-evp` as a cipher/digest. It is benchmarked under KEM algorithms.

### Resolution
We switched to:
- `openssl speed -seconds 3 -kem-algorithms`

This successfully benchmarked:
- X25519
- ML-KEM-512 / 768 / 1024
- hybrid KEMs (e.g., X25519MLKEM768)

---

# 4. Codebase Walkthrough: Each File and What It Does

Below is the current structure based on what you showed:

- src/
  - classical_ecdh.py
  - pqc_mlkem.py
  - experiment_runner.py
  - measurement.py
  - classical_x25519_openssl.py (optional/experimental)
- analysis/
  - analyze_results.py
  - plot_results.py
- data/
  - raw/results.csv
  - processed/summary.csv
  - processed/*.png plots

---

## 4.1 `src/classical_ecdh.py`

### Purpose
Defines and benchmarks classical X25519 ECDH using the `cryptography` library.

### What it measures
It times two conceptual components:
- Key generation (two keypairs)
- Exchange (two shared-secret computations)

To reduce measurement noise, it uses batching:
- batch_size = 50 operations per timing block
- averages per operation

### Output
Prints a dictionary like:
- scheme: X25519
- trials
- batch_size
- keygen_pair timing stats
- exchange_pair timing stats
- total_mean_ms

This is your “classical baseline” measurement.

---

## 4.2 `src/pqc_mlkem.py`

### Purpose
Implements ML-KEM benchmarking using liboqs-python.

### Main responsibilities
- Select a KEM name (e.g., ML-KEM-512) using `pick_kem_name()`
- Perform one full KEM cycle via `mlkem_once(kem_name)`:
  - keygen
  - encaps
  - decaps
- Benchmark each component (keygen/encap/decap) with batching and summary stats.

### Output
Prints a dictionary like:
- kem: ML-KEM-512
- keygen stats
- encap stats
- decap stats
- total_mean_ms

This is the PQC benchmark.

---

## 4.3 `src/measurement.py`

### Purpose
Provides the abstraction for measurement collection.

### Current behavior
Right now, the framework supports returning measurement fields in a consistent shape for CSV output:
- energy_J
- avg_current_mA
- peak_current_mA

In software-only mode, those fields are either:
- None / missing / placeholders
- or computed from simulated/available values (depending on your implementation)

This file becomes much more important during the hardware phase because it will be upgraded to read real sensor data or instrumentation data.

---

## 4.4 `src/experiment_runner.py`

### Purpose
This is the main orchestration script for running full experiments and saving raw data.

### What it does
- Creates/ensures `data/raw/results.csv` exists with the correct header.
- Runs two experiments:
  1) Classical ECDH trials using `ecdh_x25519_once()`
  2) PQC ML-KEM trials using `mlkem_once(kem_name)`

### CSV Schema
Each row includes:
- timestamp
- configuration
- trial
- execution_time_ms
- energy_J
- avg_current_mA
- peak_current_mA

### Timing Method
- Uses `time.perf_counter()` around the cryptographic operation(s).
- For ML-KEM it uses a `batch_size` (e.g., 50) and divides by batch size to get per-operation time.

### Important design note
The script appends to results.csv by default.
So if you want a fresh run:
- delete `data/raw/results.csv` before running

---

## 4.5 `analysis/analyze_results.py`

### Purpose
Reads raw results CSV and produces a summarized comparison table.

### What it computes (grouped by configuration)
- trial count
- mean_time_ms
- std_time_ms
- min_time_ms
- max_time_ms
- time_overhead_vs_classical_pct

### Output
Writes:
- `data/processed/summary.csv`

And prints a summary in terminal.

---

## 4.6 `analysis/plot_results.py`

### Purpose
Reads processed summary and generates plots.

### Output
Saved plot examples you already generated:
- `data/processed/timing_by_config.png`
- `data/processed/timing_mean_with_std.png`

Your bar chart confirms:
- ML-KEM-512 is much faster than the chosen “classical” benchmark as implemented (because you measured “full ECDH exchange pair” vs “KEM cycle averaged per-op with batch”, so the comparison needs careful interpretation — see next steps).

---

## 4.7 `src/classical_x25519_openssl.py` (Optional)

### Purpose
Attempted to benchmark X25519 via OpenSSL speed.

### Status
The `-evp x25519` approach failed. This file is still useful if you modify it to call:
- `openssl speed -kem-algorithms` and parse out X25519 results.

This becomes valuable later because OpenSSL can act as a “standardized external baseline.”

---

# 5. Results Obtained So Far

## 5.1 Python Benchmarks (Component-Level)

ML-KEM-512 (liboqs-python, batched):
- total_mean_ms ≈ 0.02345 ms per KEM cycle
- keygen_mean_ms ≈ 0.00761
- encap_mean_ms ≈ 0.00868
- decap_mean_ms ≈ 0.00716

X25519 (cryptography, batched):
- total_mean_ms ≈ 0.386997 ms per “pair operation”
- keygen_pair_mean_ms ≈ 0.131856
- exchange_pair_mean_ms ≈ 0.255141

## 5.2 CSV / Analysis Pipeline Output

Your analysis script produced:
- `data/processed/summary.csv`

And your plotted figure shows:
- ML-KEM-512 timing bar is far smaller than the classical bar in your current measurement setup.

Important note: the classical and PQC operations measured are not exactly “the same unit of work” yet (see next steps).

---

# 6. Interpretation and Measurement Validity Notes

Right now, the project is correctly functioning end-to-end, but we must refine the experiment design to ensure comparisons are apples-to-apples.

Key points:

1) X25519 ECDH “pair benchmark” includes:
   - two key generations
   - two exchanges
   - validation check

2) ML-KEM benchmark includes:
   - keygen
   - encaps
   - decaps

These are comparable at a conceptual level (handshake primitives), but the exact work differs.

So the next phase should define:
- what “one handshake” means in a consistent way
- and measure equivalent “handshake units” for both.

---

# 7. Next Steps (Software Phase Improvements)

## 7.1 Make the Units Comparable (“Handshake Definition”)

Define one unit of work as:

Option A (Handshake Primitive Level)
- Classical: (1 keypair gen + 1 exchange)
- PQC: (1 keygen + 1 encaps + 1 decaps)

Option B (Protocol Simulation Level)
- Simulate a client/server handshake:
  - classical: client keypair + server keypair + exchange + confirm
  - PQC: client keygen + server encaps + client decaps + confirm

Pick one and enforce it consistently in the runner.

---

## 7.2 Record Separate Timing Columns (Component-Level in CSV)

Instead of only a single `execution_time_ms`, add:
- keygen_time_ms
- encap_time_ms
- decap_time_ms
- exchange_time_ms

Then compute “total handshake time” from those fields.

This will give you richer plots and a stronger paper/report.

---

## 7.3 Standardize Warmups

Add warmup loops for both classical and pqc (you already did this partially).

Recommendation:
- warmup 5–10
- then trials 200–1000 depending on runtime

---

## 7.4 Improve OpenSSL Benchmark Integration

Update the OpenSSL script to use:
- `openssl speed -kem-algorithms`

Then parse:
- X25519
- ML-KEM-512/768/1024
- hybrid KEMs (optional but interesting)

This gives you an external reference baseline.

---

# 8. Transition Plan: Switching to Hardware

This is the core “hardware tradeoff” step. The software pipeline you built is the foundation.

## 8.1 What Will Change on Hardware

Your pipeline already supports energy/current columns in CSV:
- energy_J
- avg_current_mA
- peak_current_mA

On hardware you will replace placeholder behavior in `MeasurementSession` with real measurements.

## 8.2 Hardware Measurement Approach Options

Option A: USB Power Meter (simple)
- Measure device power draw during runs
- Provides coarse energy/power numbers
- Easier setup, lower precision

Option B: INA219 / INA226 sensor (recommended)
- Measures voltage and current at high resolution
- Can compute energy from sampled power
- Works well for Raspberry Pi or embedded boards

Option C: Monsoon Power Monitor (best but expensive)
- Research-grade measurement

## 8.3 Software Changes Needed for Hardware Mode

### Update `measurement.py`
- Connect to sensor (I2C INA219/INA226 or equivalent)
- Sample current at a fixed rate during the timing window
- Compute:
  - avg_current_mA
  - peak_current_mA
  - energy_J = ∑(V * I * dt)

### Update `experiment_runner.py`
- Ensure MeasurementSession starts sampling before timing begins
- Stops sampling immediately after timing ends
- Save metrics into each trial row

### Add environment metadata to CSV
Add columns like:
- platform
- python_version
- liboqs_version
- cpu_arch
- temperature (optional)

This is very useful when you compare laptop results vs hardware.

---

# 9. Concrete “To Continue the Project” Checklist

## 9.1 Software To-Do (Before Hardware)

- Decide handshake unit definition (apples-to-apples)
- Update runner to measure equivalent units
- Add component timing columns to CSV
- Improve plots to show:
  - total handshake time
  - breakdown by component

## 9.2 Hardware To-Do

- Choose hardware platform (Raspberry Pi recommended for next step)
- Choose sensor approach (INA219/INA226 recommended)
- Wire sensor inline with device power supply
- Implement MeasurementSession hardware sampling
- Re-run experiments and regenerate:
  - results.csv
  - summary.csv
  - plots
- Compare:
  - laptop vs embedded execution time
  - energy and current differences classical vs pqc
  - overhead per handshake

---

# 10. Deliverables Produced So Far

- Raw results:
  - data/raw/results.csv

- Processed summary:
  - data/processed/summary.csv

- Plots:
  - data/processed/timing_by_config.png
  - data/processed/timing_mean_with_std.png

- Working benchmarks:
  - src/classical_ecdh.py
  - src/pqc_mlkem.py

- Working experiment pipeline:
  - src/experiment_runner.py
  - analysis/analyze_results.py
  - analysis/plot_results.py

---

# 11. Immediate Recommendation for Your Next Commit

1) Refactor experiment_runner to store component-level timings in CSV.
2) Add a “handshake definition” comment block so your methodology is explicit.
3) Update plotting to show:
   - total handshake time
   - component breakdown
4) Then proceed to hardware measurement integration.

This will make your eventual hardware results publishable-quality and defensible in a report/paper.

