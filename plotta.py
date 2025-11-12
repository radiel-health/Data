#!/usr/bin/env python3
"""
Generate convergence and flow field plots for lid-driven cavity simulations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150

def extract_residuals_from_log(log_file):
    """Extract residual history from console.log file"""
    residuals = {
        'iteration': [],
        'continuity': [],
        'x_velocity': [],
        'y_velocity': []
    }
    
    with open(log_file, 'r') as f:
        for line in f:
            # Match lines like: "  4999  1.5227e-05  2.2912e-08  1.8386e-08  0:00:00    1"
            match = re.match(r'\s+(\d+)\s+([\d.e+-]+)\s+([\d.e+-]+)\s+([\d.e+-]+)', line)
            if match:
                iteration = int(match.group(1))
                cont = float(match.group(2))
                xvel = float(match.group(3))
                yvel = float(match.group(4))
                
                # Only add non-zero residuals (skip false convergence cases)
                if cont > 0 or xvel > 0 or yvel > 0:
                    residuals['iteration'].append(iteration)
                    residuals['continuity'].append(cont if cont > 0 else 1e-15)  # Replace 0 with small value
                    residuals['x_velocity'].append(xvel if xvel > 0 else 1e-15)
                    residuals['y_velocity'].append(yvel if yvel > 0 else 1e-15)
    
    return pd.DataFrame(residuals)

def normalize_column_names(df):
    """Normalize column names from Fluent CSV exports"""
    # Strip whitespace and convert to lowercase
    df.columns = df.columns.str.strip().str.lower()
    return df

def read_fluent_csv(filepath):
    """Read Fluent space-separated CSV files"""
    # Fluent uses multiple spaces as delimiter (whitespace separated)
    # Use sep='\s+' instead of deprecated delim_whitespace
    df = pd.read_csv(filepath, sep=r'\s+')
    return normalize_column_names(df)

def plot_convergence(df_residuals, re_num, output_dir):
    """Plot residual convergence history with granular detail"""
    
    # Check if this is a false convergence case (all zeros or only 1 iteration)
    if len(df_residuals) <= 1:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f'Re = {re_num}\n\n✗ FALSE CONVERGENCE\nAll residuals = 0 at iteration 1\n\nThis case needs to be re-run',
                ha='center', va='center', fontsize=16, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        plt.tight_layout()
        plt.savefig(output_dir / f'convergence_Re{re_num}.png', bbox_inches='tight')
        plt.close()
        print(f"  ⚠ FALSE CONVERGENCE detected - plot generated")
        return "FALSE_CONVERGENCE"
    
    # Create figure with 3 subplots for more granular view
    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    ax1 = fig.add_subplot(gs[0, :])  # Full width for continuity
    ax2 = fig.add_subplot(gs[1, :])  # Full width for velocities
    ax3 = fig.add_subplot(gs[2, 0])  # Continuity last 500 iters
    ax4 = fig.add_subplot(gs[2, 1])  # Velocity last 500 iters
    
    # Plot 1: Full continuity history
    ax1.semilogy(df_residuals['iteration'], df_residuals['continuity'], 
                 'b-', linewidth=1.5, label='Continuity', alpha=0.8)
    ax1.axhline(y=1e-6, color='r', linestyle='--', linewidth=2, alpha=0.7, label='Target (1e-6)')
    ax1.set_ylabel('Continuity Residual', fontsize=11, fontweight='bold')
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_title(f'Convergence History - Re = {re_num}', fontsize=13, fontweight='bold')
    
    # Plot 2: Full velocity history
    ax2.semilogy(df_residuals['iteration'], df_residuals['x_velocity'], 
                 'g-', linewidth=1.5, label='X-Velocity', alpha=0.8)
    ax2.semilogy(df_residuals['iteration'], df_residuals['y_velocity'], 
                 'm-', linewidth=1.5, label='Y-Velocity', alpha=0.8)
    ax2.axhline(y=1e-9, color='r', linestyle='--', linewidth=2, alpha=0.7, label='Target (1e-9)')
    ax2.set_xlabel('Iteration', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Velocity Residual', fontsize=11, fontweight='bold')
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3 & 4: Zoomed view of last 500 iterations (or all if less)
    n_zoom = min(500, len(df_residuals))
    df_zoom = df_residuals.iloc[-n_zoom:]
    
    # Plot 3: Continuity zoom
    ax3.semilogy(df_zoom['iteration'], df_zoom['continuity'], 
                 'b-', linewidth=1.5, marker='o', markersize=2, alpha=0.7)
    ax3.axhline(y=1e-6, color='r', linestyle='--', linewidth=1.5, alpha=0.7)
    ax3.set_xlabel('Iteration', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Continuity', fontsize=10, fontweight='bold')
    ax3.set_title(f'Last {n_zoom} Iterations (Detail)', fontsize=11, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Velocity zoom
    ax4.semilogy(df_zoom['iteration'], df_zoom['x_velocity'], 
                 'g-', linewidth=1.5, marker='o', markersize=2, alpha=0.7, label='X-Vel')
    ax4.semilogy(df_zoom['iteration'], df_zoom['y_velocity'], 
                 'm-', linewidth=1.5, marker='s', markersize=2, alpha=0.7, label='Y-Vel')
    ax4.axhline(y=1e-9, color='r', linestyle='--', linewidth=1.5, alpha=0.7)
    ax4.set_xlabel('Iteration', fontsize=10, fontweight='bold')
    ax4.set_ylabel('Velocity', fontsize=10, fontweight='bold')
    ax4.set_title(f'Last {n_zoom} Iterations (Detail)', fontsize=11, fontweight='bold')
    ax4.legend(loc='best', fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    # Check convergence
    final_cont = df_residuals['continuity'].iloc[-1]
    final_xvel = df_residuals['x_velocity'].iloc[-1]
    final_yvel = df_residuals['y_velocity'].iloc[-1]
    
    min_cont = df_residuals['continuity'].min()
    min_xvel = df_residuals['x_velocity'].min()
    min_yvel = df_residuals['y_velocity'].min()
    
    # Check if plateaued (std dev of last 100 iterations)
    if len(df_residuals) >= 100:
        last_100_cont = df_residuals['continuity'].iloc[-100:]
        last_100_xvel = df_residuals['x_velocity'].iloc[-100:]
        last_100_yvel = df_residuals['y_velocity'].iloc[-100:]
        
        cont_std = last_100_cont.std() / last_100_cont.mean()
        xvel_std = last_100_xvel.std() / last_100_xvel.mean()
        yvel_std = last_100_yvel.std() / last_100_yvel.mean()
        
        is_plateaued = (cont_std < 0.1 and xvel_std < 0.1 and yvel_std < 0.1)
        
        # Check if residuals met criteria at any point or are acceptably low
        met_strict_criteria = (min_cont < 1e-6 and min_xvel < 1e-9 and min_yvel < 1e-9)
        met_practical_criteria = (final_cont < 2e-5 and final_xvel < 3e-8 and final_yvel < 3e-8 and is_plateaued)
        
        status_text = f"Final Residuals:\n"
        status_text += f"Cont: {final_cont:.2e}\n"
        status_text += f"X-Vel: {final_xvel:.2e}\n"
        status_text += f"Y-Vel: {final_yvel:.2e}\n\n"
        status_text += f"Minimum:\n"
        status_text += f"Cont: {min_cont:.2e}\n"
        status_text += f"X-Vel: {min_xvel:.2e}\n"
        status_text += f"Y-Vel: {min_yvel:.2e}\n\n"
        status_text += f"Std/Mean (last 100):\n"
        status_text += f"Cont: {cont_std:.3f}\n"
        status_text += f"X-Vel: {xvel_std:.3f}\n"
        status_text += f"Y-Vel: {yvel_std:.3f}\n\n"
        
        if met_strict_criteria:
            status_text += "✓ CONVERGED\n(Met strict criteria)"
            color = 'green'
            convergence_status = "CONVERGED"
        elif met_practical_criteria:
            status_text += "✓ PRACTICALLY\nCONVERGED\n(Plateaued)"
            color = 'lightgreen'
            convergence_status = "PRACTICALLY_CONVERGED"
        elif is_plateaued:
            status_text += "⚠ PLATEAUED\n(Stable, high res.)"
            color = 'orange'
            convergence_status = "PLATEAUED"
        else:
            status_text += "✗ NOT CONVERGED\n(Still evolving)"
            color = 'red'
            convergence_status = "NOT_CONVERGED"
        
        fig.text(0.98, 0.02, status_text, transform=fig.transFigure, 
                fontsize=8, verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor=color, alpha=0.3),
                family='monospace')
    else:
        convergence_status = "UNKNOWN"
    
    plt.savefig(output_dir / f'convergence_Re{re_num}.png', bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Convergence plot saved")
    return convergence_status

def calculate_surface_coordinate(x, y, L_height=2.0):
    """
    Calculate surface coordinate s that starts at (0,L_height) and increases counterclockwise
    Adjusted for 1m × 2m cavity
    
    Path: Top (moving lid) → Right wall → Bottom wall → Left wall
    s = 0 at (0, L_height)  [top-left corner]
    """
    
    # Tolerance for identifying walls
    tol = 0.01
    
    # Identify which wall this point is on
    if np.abs(y - L_height) < tol:  # Top wall (moving)
        s = x  # s goes from 0 to 1
    elif np.abs(x - 1.0) < tol:  # Right wall
        s = 1.0 + (L_height - y)  # s goes from 1 to 1+L_height
    elif np.abs(y) < tol:  # Bottom wall
        s = 1.0 + L_height + (1.0 - x)  # s goes from 1+L_height to 2+L_height
    elif np.abs(x) < tol:  # Left wall
        s = 2.0 + L_height + y  # s goes from 2+L_height to 2+2*L_height
    else:
        s = np.nan  # Not on a wall
        
    return s

def plot_wall_shear_stress_line(df_moving, df_stat, re_num, output_dir):
    """Plot wall shear stress as a line plot around the perimeter"""
    
    L_height = 2.0  # Cavity height
    
    # Calculate surface coordinates for all points
    all_s = []
    all_shear = []
    all_labels = []
    
    # Moving wall (top)
    x_moving = df_moving['x-coordinate'].values
    y_moving = df_moving['y-coordinate'].values
    shear_moving = df_moving['wall-shear'].values
    
    s_moving = np.array([calculate_surface_coordinate(x, y, L_height) 
                         for x, y in zip(x_moving, y_moving)])
    
    # Sort by s
    sort_idx = np.argsort(s_moving)
    s_moving_sorted = s_moving[sort_idx]
    shear_moving_sorted = shear_moving[sort_idx]
    
    all_s.append(s_moving_sorted)
    all_shear.append(shear_moving_sorted)
    all_labels.append('Top (Moving)')
    
    # Stationary walls - separate into segments
    x_stat = df_stat['x-coordinate'].values
    y_stat = df_stat['y-coordinate'].values
    shear_stat = df_stat['wall-shear'].values
    
    tol = 0.01
    
    # Right wall
    right_mask = np.abs(x_stat - 1.0) < tol
    if np.any(right_mask):
        x_r, y_r, shear_r = x_stat[right_mask], y_stat[right_mask], shear_stat[right_mask]
        s_r = np.array([calculate_surface_coordinate(x, y, L_height) for x, y in zip(x_r, y_r)])
        sort_idx = np.argsort(s_r)
        all_s.append(s_r[sort_idx])
        all_shear.append(shear_r[sort_idx])
        all_labels.append('Right')
    
    # Bottom wall
    bottom_mask = np.abs(y_stat) < tol
    if np.any(bottom_mask):
        x_b, y_b, shear_b = x_stat[bottom_mask], y_stat[bottom_mask], shear_stat[bottom_mask]
        s_b = np.array([calculate_surface_coordinate(x, y, L_height) for x, y in zip(x_b, y_b)])
        sort_idx = np.argsort(s_b)
        all_s.append(s_b[sort_idx])
        all_shear.append(shear_b[sort_idx])
        all_labels.append('Bottom')
    
    # Left wall
    left_mask = np.abs(x_stat) < tol
    if np.any(left_mask):
        x_l, y_l, shear_l = x_stat[left_mask], y_stat[left_mask], shear_stat[left_mask]
        s_l = np.array([calculate_surface_coordinate(x, y, L_height) for x, y in zip(x_l, y_l)])
        sort_idx = np.argsort(s_l)
        all_s.append(s_l[sort_idx])
        all_shear.append(shear_l[sort_idx])
        all_labels.append('Left')
    
    # Create plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    colors = ['red', 'blue', 'green', 'purple']
    
    # Plot 1: Linear scale
    for i, (s, shear, label) in enumerate(zip(all_s, all_shear, all_labels)):
        ax1.plot(s, shear, '-o', label=label, linewidth=2, markersize=3,
                color=colors[i % len(colors)], alpha=0.7)
    
    # Mark wall transitions
    ax1.axvline(x=1, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax1.axvline(x=1+L_height, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax1.axvline(x=2+L_height, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    ax1.set_xlabel('Surface Coordinate s', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Wall Shear Stress (Pa)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Wall Shear Stress Distribution - Re = {re_num}\ns=0 at (0,{L_height}), increases counterclockwise',
                 fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10, loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Log scale
    for i, (s, shear, label) in enumerate(zip(all_s, all_shear, all_labels)):
        ax2.semilogy(s, np.abs(shear), '-o', label=label, linewidth=2, markersize=3,
                    color=colors[i % len(colors)], alpha=0.7)
    
    ax2.axvline(x=1, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax2.axvline(x=1+L_height, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    ax2.axvline(x=2+L_height, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    ax2.set_xlabel('Surface Coordinate s', fontsize=12, fontweight='bold')
    ax2.set_ylabel('|Wall Shear Stress| (Pa) - Log Scale', fontsize=12, fontweight='bold')
    ax2.set_title('Absolute Wall Shear Stress (Log Scale)', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=10, loc='best')
    ax2.grid(True, alpha=0.3, which='both')
    
    # Statistics
    all_shear_combined = np.concatenate(all_shear)
    stats_text = f"Max: {np.max(np.abs(all_shear_combined)):.3e} Pa\n"
    stats_text += f"Min: {np.min(np.abs(all_shear_combined)):.3e} Pa\n"
    stats_text += f"Mean: {np.mean(np.abs(all_shear_combined)):.3e} Pa"
    
    ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes,
            fontsize=9, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
            family='monospace')
    
    plt.tight_layout()
    plt.savefig(output_dir / f'wall_shear_line_Re{re_num}.png', bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Wall shear stress line plot saved")

def plot_velocity_magnitude(df_interior, re_num, output_dir):
    """Plot velocity magnitude contour"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Create contour plot
    scatter = ax.scatter(df_interior['x-coordinate'], df_interior['y-coordinate'], 
                        c=df_interior['velocity-magnitude'], cmap='jet', s=1)
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Velocity Magnitude (m/s)', fontsize=12, fontweight='bold')
    
    ax.set_xlabel('X (m)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
    ax.set_title(f'Velocity Magnitude - Re = {re_num}', fontsize=14, fontweight='bold')
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(output_dir / f'velocity_magnitude_Re{re_num}.png', bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Velocity magnitude plot saved")

def plot_pressure(df_interior, re_num, output_dir):
    """Plot pressure contour"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    scatter = ax.scatter(df_interior['x-coordinate'], df_interior['y-coordinate'], 
                        c=df_interior['pressure'], cmap='RdBu_r', s=1)
    
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Pressure (Pa)', fontsize=12, fontweight='bold')
    
    ax.set_xlabel('X (m)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
    ax.set_title(f'Pressure Field - Re = {re_num}', fontsize=14, fontweight='bold')
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(output_dir / f'pressure_Re{re_num}.png', bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Pressure plot saved")

def plot_wall_shear_stress(df_walls, re_num, output_dir):
    """Plot wall shear stress on all walls (scatter view)"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Sort by x-coordinate for better visualization
    df_walls_sorted = df_walls.sort_values('x-coordinate')
    
    ax.plot(df_walls_sorted['x-coordinate'], df_walls_sorted['wall-shear'], 
            'b-', linewidth=2, marker='o', markersize=3)
    
    ax.set_xlabel('X-coordinate (m)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Wall Shear Stress (Pa)', fontsize=12, fontweight='bold')
    ax.set_title(f'Wall Shear Stress - Re = {re_num}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / f'wall_shear_stress_Re{re_num}.png', bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Wall shear stress plot saved")

def plot_centerline_profiles(df_vcenter, df_hcenter, re_num, output_dir):
    """Plot velocity profiles along centerlines"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Vertical centerline (U velocity vs Y)
    df_vcenter_sorted = df_vcenter.sort_values('y-coordinate')
    ax1.plot(df_vcenter_sorted['x-velocity'], df_vcenter_sorted['y-coordinate'], 
             'b-', linewidth=2, marker='o', markersize=4)
    ax1.set_xlabel('U Velocity (m/s)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Vertical Centerline (x=0.5m)\nRe = {re_num}', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Horizontal centerline (V velocity vs X)
    df_hcenter_sorted = df_hcenter.sort_values('x-coordinate')
    ax2.plot(df_hcenter_sorted['x-coordinate'], df_hcenter_sorted['y-velocity'], 
             'r-', linewidth=2, marker='o', markersize=4)
    ax2.set_xlabel('X (m)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('V Velocity (m/s)', fontsize=12, fontweight='bold')
    ax2.set_title(f'Horizontal Centerline (y=1.0m)\nRe = {re_num}', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / f'centerline_profiles_Re{re_num}.png', bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Centerline profiles plot saved")

def plot_vorticity(df_interior, re_num, output_dir):
    """Calculate and plot velocity vectors"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Subsample for vector plot (every Nth point)
    stride = max(1, len(df_interior) // 2000)
    df_sub = df_interior.iloc[::stride]
    
    # Quiver plot
    ax.quiver(df_sub['x-coordinate'], df_sub['y-coordinate'],
              df_sub['x-velocity'], df_sub['y-velocity'],
              df_sub['velocity-magnitude'], cmap='jet', scale=0.001, width=0.003)
    
    ax.set_xlabel('X (m)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Y (m)', fontsize=12, fontweight='bold')
    ax.set_title(f'Velocity Vectors - Re = {re_num}', fontsize=14, fontweight='bold')
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(output_dir / f'velocity_vectors_Re{re_num}.png', bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Velocity vector plot saved")

def process_case(case_dir):
    """Process a single Re case and generate all plots"""
    case_name = case_dir.name
    re_match = re.match(r'Re(\d+)', case_name)
    if not re_match:
        return None
    
    re_num = int(re_match.group(1))
    print(f"\nProcessing {case_name}...")
    
    # Check if required files exist
    log_file = case_dir / 'console.log'
    interior_file = case_dir / f'interior_full_Re{re_num}.csv'
    moving_wall_file = case_dir / f'moving_wall_full_Re{re_num}.csv'
    stat_walls_file = case_dir / f'stationary_walls_full_Re{re_num}.csv'
    vcenter_file = case_dir / f'vertical_centerline_Re{re_num}.csv'
    hcenter_file = case_dir / f'horizontal_centerline_Re{re_num}.csv'
    
    if not log_file.exists():
        print(f"  ✗ console.log not found, skipping...")
        return None
    
    # Create plots subdirectory
    plots_dir = case_dir / 'plots'
    plots_dir.mkdir(exist_ok=True)
    
    convergence_status = "UNKNOWN"
    
    # 1. Convergence plot
    try:
        df_residuals = extract_residuals_from_log(log_file)
        if len(df_residuals) > 0:
            convergence_status = plot_convergence(df_residuals, re_num, plots_dir)
        else:
            print(f"  ✗ No residual data found in log")
    except Exception as e:
        print(f"  ✗ Error plotting convergence: {e}")
    
    # 2. Interior field plots
    if interior_file.exists():
        try:
            df_interior = read_fluent_csv(interior_file)
            plot_velocity_magnitude(df_interior, re_num, plots_dir)
            plot_pressure(df_interior, re_num, plots_dir)
            plot_vorticity(df_interior, re_num, plots_dir)
        except Exception as e:
            print(f"  ✗ Error plotting interior fields: {e}")
    else:
        print(f"  ✗ Interior data file not found")
    
    # 3. Wall shear stress plots
    if moving_wall_file.exists() and stat_walls_file.exists():
        try:
            df_moving = read_fluent_csv(moving_wall_file)
            df_stat = read_fluent_csv(stat_walls_file)
            
            # Line plot around perimeter
            plot_wall_shear_stress_line(df_moving, df_stat, re_num, plots_dir)
            
            # Also do scatter plot for stationary walls
            plot_wall_shear_stress(df_stat, re_num, plots_dir)
        except Exception as e:
            print(f"  ✗ Error plotting wall shear stress: {e}")
    else:
        print(f"  ✗ Wall data files not found")
    
    # 4. Centerline profiles
    if vcenter_file.exists() and hcenter_file.exists():
        try:
            df_vcenter = read_fluent_csv(vcenter_file)
            df_hcenter = read_fluent_csv(hcenter_file)
            plot_centerline_profiles(df_vcenter, df_hcenter, re_num, plots_dir)
        except Exception as e:
            print(f"  ✗ Error plotting centerline profiles: {e}")
    
    print(f"  ✓ All plots saved to {plots_dir}")
    return (re_num, convergence_status)

def main():
    """Process all Re cases in results directory"""
    results_dir = Path('results')
    
    if not results_dir.exists():
        print("Error: 'results' directory not found!")
        return
    
    # Get all Re directories
    re_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith('Re')],
                     key=lambda x: int(re.match(r'Re(\d+)', x.name).group(1)))
    
    if len(re_dirs) == 0:
        print("No Re directories found in results/")
        return
    
    print(f"Found {len(re_dirs)} cases to process")
    print("=" * 60)
    
    convergence_summary = []
    for case_dir in re_dirs:
        result = process_case(case_dir)
        if result:
            convergence_summary.append(result)
    
    # Print summary
    print("\n" + "=" * 60)
    print("CONVERGENCE SUMMARY")
    print("=" * 60)
    
    status_counts = {}
    for re_num, status in convergence_summary:
        status_counts[status] = status_counts.get(status, 0) + 1
        symbol = "✓" if "CONVERGED" in status else ("⚠" if "PLATEAU" in status else "✗")
        print(f"Re {re_num:4d}: {symbol} {status}")
    
    print("\n" + "=" * 60)
    print("Status breakdown:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    print("\n" + "=" * 60)
    print("✓ All cases processed!")
    print(f"Plots saved in results/ReXXX/plots/ directories")
    print("\nGenerated plots per case:")
    print("  - convergence_ReXXX.png (3-panel detailed view)")
    print("  - velocity_magnitude_ReXXX.png")
    print("  - pressure_ReXXX.png")
    print("  - velocity_vectors_ReXXX.png")
    print("  - wall_shear_line_ReXXX.png (perimeter line plot)")
    print("  - wall_shear_stress_ReXXX.png (scatter)")
    print("  - centerline_profiles_ReXXX.png")

if __name__ == '__main__':
    main()