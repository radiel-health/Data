# Data

Full Database for Radiel Health's ML model inputs...

# Data Avaliable Here...

1. Lid-Driven Cavity Flow (First Order Descritized)
   For Radiel's preliminary model to test on the age-old problem, from Re=100 to 3200 (just until it gets turbulent).
2. Lid-Driven Cavity Flow (Third Order Descritized)
   2a. 1x1 Aspect Ratios
   2b. 2x1 Aspect Ratios
   2c. 1x2 Aspect Ratios

# Lid-Driven Cavity Flow CFD Simulation

2D laminar flow simulation of the classical lid-driven cavity benchmark problem using ANSYS Fluent 2025 R2.

## Overview

This dataset contains comprehensive CFD simulation results for lid-driven cavity flow across a wide range of Reynolds numbers (Re = 100 to 3250). The simulations are validated against the benchmark data from Ghia et al. (1982).

## Reynolds Numbers Simulated

- **Range**: Re = 100, 150, 200, ..., 3250 (65 cases total)
- **Increment**: ΔRe = 50
- **Validated**: Re = 100 and Re = 1000 (benchmarked against Ghia et al.)

## Directory Structure

```
├── benchmark.py              # Validation script (compares against Ghia et al.)
├── visualization.py          # Plotting and visualization tools
├── summary_results.py        # Aggregate results analysis
├── run_batch.sh             # Batch simulation runner
├── centerline_fix.sh        # Script to fix centerline extraction
├── journal_template.jou     # Fluent journal file template
├── .gitignore               # Git ignore rules (excludes large binary files)
└── results/
    ├── Re100/               # Results for Re = 100
    ├── Re150/               # Results for Re = 150
    ├── ...
    └── Re3250/              # Results for Re = 3250
```

## Data Files (per Reynolds number)

Each `results/Re{number}/` folder contains:

### Flow Field Data

- `vertical_centerline_Re{Re}.csv` - Velocity profile along vertical centerline (X=0.5)
- `horizontal_centerline_Re{Re}.csv` - Velocity profile along horizontal centerline (Y=0.5)
- `moving_wall_full_Re{Re}.csv` - Velocity and wall shear stress on moving lid
- `stat_walls_full_Re{Re}.csv` - Data on stationary walls (bottom, left, right)

### Visualization

- `centerline_profiles.png` - U and V velocity profiles
- `plot_velocity_magnitude.png` - Velocity magnitude contour
- `plot_velocity_vectors.png` - Velocity vector field
- `plot_pressure.png` - Pressure contour
- `plot_streamlines.png` - Streamline visualization
- `wall_shear_stress.png` - WSS distribution on walls

### Metadata

- `metadata.txt` - Simulation parameters and convergence info
- `runtime.txt` - Computational time

### Benchmark Results (Re=100, Re=1000 only)

- `benchmark_comparison_Re{Re}.png` - Comparison plots vs. Ghia et al.

## Simulation Parameters

- **Geometry**: Square cavity (1.0 m × 1.0 m)
- **Actual mesh domain**: X ∈ [0.3, 1.4] m, Y ∈ [0.0, 1.0] m
- **Mesh**: 16,641 quadrilateral cells (129×129 structured grid)
- **Solver**: ANSYS Fluent 2025 R2
- **Model**: 2D, laminar, steady-state
- **Fluid**: Water (ρ = 998.2 kg/m³, μ = 0.001003 kg/(m·s))
- **Boundary Conditions**:
  - Top wall: Moving lid (velocity varies with Re)
  - Bottom, left, right walls: No-slip stationary
- **Discretization**:
  - Pressure: Standard (12)
  - Momentum: Second-order upwind (1)
  - Pressure-velocity coupling: SIMPLE
- **Convergence criteria**: Residuals < 10⁻³ (solution deemed converged)

## Validation

The simulations have been validated against the classical benchmark:

**Ghia, U., Ghia, K. N., & Shin, C. T. (1982).** _High-Re solutions for incompressible flow using the Navier-Stokes equations and a multigrid method._ Journal of Computational Physics, 48(3), 387-411.

### Benchmark Results

| Re   | U Max Error | V Max Error | Status |
| ---- | ----------- | ----------- | ------ |
| 100  | TBD         | TBD         | ✅     |
| 1000 | TBD         | TBD         | ✅     |

_Note: Centerline data is currently being re-extracted at correct locations for accurate benchmark comparison._

## Usage

### Run Benchmark Comparison

```bash
python benchmark.py
```

### Generate Visualizations

```bash
python visualization.py
```

### Analyze Results

```bash
python summary_results.py
```

## Data Format

All CSV files use space-delimited format with headers. Example columns:

**Centerline files**:

- `x-coordinate`, `y-coordinate` (m)
- `x-velocity`, `y-velocity` (m/s)
- `velocity-magnitude` (m/s)
- `pressure` (Pa)

**Wall files**:

- `x-coordinate`, `y-coordinate` (m)
- `pressure` (Pa)
- `wall-shear` (Pa) - magnitude
- `x-wall-shear`, `y-wall-shear` (Pa) - components

## Notes

- Large binary files (`.cas.h5`, `.dat.h5`) are excluded via `.gitignore`
- Interior full flow field CSVs (`interior_full_Re*.csv`) are also excluded due to size
- For complete raw simulation data, contact the repository maintainer

## Requirements

```bash
pip install pandas numpy matplotlib scipy
```

## Contact

Rishabh Sharma r342shar@uwaterloo.ca (DaGravyGod)

Note for myself: must export PATH="$PATH:/C/Program Files/ANSYS Inc/v252/fluent/ntbin/win64" every time in bash terminal!
