#!/usr/bin/env python3
"""
Compare CFD results against Ghia et al. (1982) benchmark data
for lid-driven cavity flow
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Ghia et al. (1982) benchmark data for Re=100
GHIA_RE100 = {
    'y': [0.0000, 0.0547, 0.0625, 0.0703, 0.1016, 0.1719, 0.2813, 
          0.4531, 0.5000, 0.6172, 0.7344, 0.8516, 0.9531, 0.9609, 
          0.9688, 0.9766, 1.0000],
    'u': [0.00000, -0.03717, -0.04192, -0.04775, -0.06434, -0.10150, 
          -0.15662, -0.21090, -0.20581, -0.13641, 0.00332, 0.23151, 
          0.68717, 0.73722, 0.78871, 0.84123, 1.00000],
    'x': [0.0000, 0.0625, 0.0703, 0.0781, 0.0938, 0.1563, 0.2266, 
          0.2344, 0.5000, 0.8047, 0.8594, 0.9063, 0.9453, 0.9531, 
          0.9609, 0.9688, 1.0000],
    'v': [0.00000, 0.09233, 0.10091, 0.10890, 0.12317, 0.16077, 0.17507,
          0.17527, 0.05454, -0.24533, -0.22445, -0.16914, -0.10313,
          -0.08864, -0.07391, -0.05906, 0.00000]
}

# Ghia et al. (1982) benchmark data for Re=1000
GHIA_RE1000 = {
    'y': [0.0000, 0.0547, 0.0625, 0.0703, 0.1016, 0.1719, 0.2813,
          0.4531, 0.5000, 0.6172, 0.7344, 0.8516, 0.9531, 0.9609,
          0.9688, 0.9766, 1.0000],
    'u': [0.00000, -0.18109, -0.20196, -0.22220, -0.29730, -0.38289,
          -0.27805, -0.10648, -0.06080, 0.05702, 0.18719, 0.33304,
          0.46604, 0.51117, 0.57492, 0.65928, 1.00000],
    'x': [0.0000, 0.0625, 0.0703, 0.0781, 0.0938, 0.1563, 0.2266,
          0.2344, 0.5000, 0.8047, 0.8594, 0.9063, 0.9453, 0.9531,
          0.9609, 0.9688, 1.0000],
    'v': [0.00000, 0.27485, 0.29012, 0.30353, 0.32627, 0.37095, 0.33075,
          0.32235, 0.02526, -0.31966, -0.42665, -0.51550, -0.39188,
          -0.33714, -0.27669, -0.21388, 0.00000]
}

def load_cfd_results(Re):
    """Load CFD results for a given Reynolds number"""
    results_dir = Path(f'results/Re{Re}')
    
    # Load centerline data - use sep=r'\s+' instead of deprecated delim_whitespace
    v_center = pd.read_csv(results_dir / f'vertical_centerline_Re{Re}.csv', 
                           sep=r'\s+', skipinitialspace=True)
    h_center = pd.read_csv(results_dir / f'horizontal_centerline_Re{Re}.csv', 
                           sep=r'\s+', skipinitialspace=True)
    
    # Print column names for debugging
    print(f"  v_center columns: {list(v_center.columns)}")
    print(f"  h_center columns: {list(h_center.columns)}")
    
    # Normalize column names
    def normalize_columns(df):
        col_mapping = {}
        for col in df.columns:
            col_lower = col.lower().replace('"', '').strip()
            if col_lower == 'x-coordinate':
                col_mapping[col] = 'x-coordinate'
            elif col_lower == 'y-coordinate':
                col_mapping[col] = 'y-coordinate'
            elif col_lower == 'x-velocity':
                col_mapping[col] = 'x-velocity'
            elif col_lower == 'y-velocity':
                col_mapping[col] = 'y-velocity'
            elif col_lower == 'velocity-magnitude':
                col_mapping[col] = 'velocity-magnitude'
            elif col_lower == 'pressure':
                col_mapping[col] = 'pressure'
        df.rename(columns=col_mapping, inplace=True)
        return df
    
    v_center = normalize_columns(v_center)
    h_center = normalize_columns(h_center)
    
    print(f"  After normalization: {list(v_center.columns)}")
    
    return v_center, h_center

def normalize_cfd_data(v_center, h_center, Re):
    """
    Normalize CFD data to dimensionless form (matching Ghia et al.)
    
    Parameters:
    -----------
    v_center : DataFrame with vertical centerline data
    h_center : DataFrame with horizontal centerline data
    Re : Reynolds number (100 or 1000)
    
    Returns:
    --------
    Normalized dataframes with coordinates [0,1] and velocities normalized by U_lid
    """
    # Physical parameters
    nu = 1.004e-6  # kinematic viscosity of water [m²/s]
    L = 1.0        # cavity length [m]
    
    # Calculate lid velocity from Reynolds number: Re = U_lid * L / nu
    U_lid = Re * nu / L
    
    print(f"  Normalization: Re={Re}, U_lid={U_lid:.10f} m/s, L={L} m, nu={nu} m²/s")
    
    # Find the cavity bounds (min/max coordinates)
    y_min, y_max = v_center['y-coordinate'].min(), v_center['y-coordinate'].max()
    x_min, x_max = h_center['x-coordinate'].min(), h_center['x-coordinate'].max()
    
    print(f"  Cavity bounds: X=[{x_min:.3f}, {x_max:.3f}], Y=[{y_min:.3f}, {y_max:.3f}]")
    
    # Normalize coordinates to [0, 1]
    v_center['y_norm'] = (v_center['y-coordinate'] - y_min) / (y_max - y_min)
    h_center['x_norm'] = (h_center['x-coordinate'] - x_min) / (x_max - x_min)
    
    # Normalize velocities by lid velocity
    v_center['u_norm'] = v_center['x-velocity'] / U_lid
    h_center['v_norm'] = h_center['y-velocity'] / U_lid
    
    print(f"  Normalized U range: [{v_center['u_norm'].min():.4f}, {v_center['u_norm'].max():.4f}]")
    print(f"  Normalized V range: [{h_center['v_norm'].min():.4f}, {h_center['v_norm'].max():.4f}]")
    
    return v_center, h_center

def interpolate_to_ghia_points(cfd_df, coord_col, value_col, ghia_coords):
    """Interpolate CFD data to Ghia benchmark points"""
    return np.interp(ghia_coords, 
                     cfd_df[coord_col].values, 
                     cfd_df[value_col].values)

def compare_with_benchmark(Re, ghia_data, output_dir):
    """Compare CFD results with Ghia benchmark"""
    
    # Load CFD results
    v_center, h_center = load_cfd_results(Re)
    
    # Normalize the data to match Ghia's dimensionless format
    v_center, h_center = normalize_cfd_data(v_center, h_center, Re)
    
    # Sort data by normalized coordinates
    v_center = v_center.sort_values('y_norm')
    h_center = h_center.sort_values('x_norm')
    
    # Interpolate CFD results to Ghia points using normalized data
    cfd_u = interpolate_to_ghia_points(v_center, 'y_norm', 'u_norm', ghia_data['y'])
    cfd_v = interpolate_to_ghia_points(h_center, 'x_norm', 'v_norm', ghia_data['x'])
    
    # Create comparison plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # U-velocity comparison
    ax1.plot(ghia_data['u'], ghia_data['y'], 'ro', markersize=8, 
             label='Ghia et al. (1982)', markerfacecolor='none', markeredgewidth=2)
    ax1.plot(cfd_u, ghia_data['y'], 'b-', linewidth=2, label='Current CFD')
    ax1.set_xlabel('U Velocity (normalized)', fontsize=12)
    ax1.set_ylabel('Y (normalized)', fontsize=12)
    ax1.set_title(f'U-Velocity at X=0.5 (Re={Re})', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # V-velocity comparison
    ax2.plot(ghia_data['x'], ghia_data['v'], 'ro', markersize=8,
             label='Ghia et al. (1982)', markerfacecolor='none', markeredgewidth=2)
    ax2.plot(ghia_data['x'], cfd_v, 'b-', linewidth=2, label='Current CFD')
    ax2.set_xlabel('X (normalized)', fontsize=12)
    ax2.set_ylabel('V Velocity (normalized)', fontsize=12)
    ax2.set_title(f'V-Velocity at Y=0.5 (Re={Re})', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / f'benchmark_comparison_Re{Re}.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Calculate errors (these are now in dimensionless units)
    u_error = np.abs(cfd_u - ghia_data['u'])
    v_error = np.abs(cfd_v - ghia_data['v'])
    
    u_max_error = np.max(u_error)
    v_max_error = np.max(v_error)
    u_mean_error = np.mean(u_error)
    v_mean_error = np.mean(v_error)
    
    # Calculate L2 norm error
    u_l2_error = np.sqrt(np.mean(u_error**2))
    v_l2_error = np.sqrt(np.mean(v_error**2))
    
    return {
        'Re': Re,
        'U_max_error': u_max_error,
        'U_mean_error': u_mean_error,
        'U_L2_error': u_l2_error,
        'V_max_error': v_max_error,
        'V_mean_error': v_mean_error,
        'V_L2_error': v_l2_error
    }

def create_error_table(errors):
    """Create formatted error table"""
    print("\n" + "="*80)
    print("BENCHMARK COMPARISON RESULTS")
    print("="*80)
    print(f"{'Re':<10} {'U Max Err':<12} {'U Mean Err':<12} {'U L2 Err':<12} "
          f"{'V Max Err':<12} {'V Mean Err':<12} {'V L2 Err':<12}")
    print("-"*80)
    
    for err in errors:
        print(f"{err['Re']:<10} {err['U_max_error']:<12.6f} {err['U_mean_error']:<12.6f} "
              f"{err['U_L2_error']:<12.6f} {err['V_max_error']:<12.6f} "
              f"{err['V_mean_error']:<12.6f} {err['V_L2_error']:<12.6f}")
    
    print("="*80)
    print("\nError Interpretation (dimensionless units):")
    print("  < 0.01 (1% of lid velocity):  EXCELLENT ✓✓✓")
    print("  < 0.05 (5% of lid velocity):  GOOD ✓✓")
    print("  < 0.10 (10% of lid velocity): ACCEPTABLE ✓")
    print("  > 0.10 (10% of lid velocity): NEEDS REFINEMENT ✗")
    print("="*80 + "\n")

def main():
    """Main execution"""
    print("="*80)
    print("CFD BENCHMARK COMPARISON vs Ghia et al. (1982)")
    print("="*80)
    print()
    
    results_dir = Path('results')
    errors = []
    
    # Check Re=100
    if (results_dir / 'Re100').exists():
        print("Comparing Re=100...")
        err = compare_with_benchmark(100, GHIA_RE100, results_dir / 'Re100')
        errors.append(err)
        print(f"  ✓ Max U error: {err['U_max_error']:.6f}")
        print(f"  ✓ Max V error: {err['V_max_error']:.6f}\n")
    
    # Check Re=1000
    if (results_dir / 'Re1000').exists():
        print("Comparing Re=1000...")
        err = compare_with_benchmark(1000, GHIA_RE1000, results_dir / 'Re1000')
        errors.append(err)
        print(f"  ✓ Max U error: {err['U_max_error']:.6f}")
        print(f"  ✓ Max V error: {err['V_max_error']:.6f}\n")
    
    if errors:
        create_error_table(errors)
        
        # Save to CSV
        df = pd.DataFrame(errors)
        df.to_csv(results_dir / 'benchmark_comparison.csv', index=False)
        print(f"✓ Benchmark comparison saved to: {results_dir / 'benchmark_comparison.csv'}")
        print(f"✓ Plots saved to: results/Re100/ and results/Re1000/")
    else:
        print("No benchmark cases (Re=100 or Re=1000) found!")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()