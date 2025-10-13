#!/usr/bin/env python3
"""
Generate comprehensive visualizations for lid-driven cavity CFD results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
import glob
import os
from pathlib import Path

# Set style for publication-quality plots
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10

def create_contour_plot(df, variable, title, filename, cmap='viridis'):
    """Create filled contour plot"""
    fig, ax = plt.subplots(figsize=(8, 7))
    
    # Create triangulation for irregular grid
    triang = Triangulation(df['x-coordinate'], df['y-coordinate'])
    
    # Plot filled contours
    levels = 20
    contourf = ax.tricontourf(triang, df[variable], levels=levels, cmap=cmap)
    
    # Add colorbar
    cbar = plt.colorbar(contourf, ax=ax)
    cbar.set_label(variable, rotation=270, labelpad=20)
    
    # Format plot
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_title(title)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight')
    plt.close()

def create_velocity_vectors(df, title, filename, skip=8):
    """Create velocity vector plot"""
    fig, ax = plt.subplots(figsize=(8, 7))
    
    # Subsample for vector plot
    df_sub = df.iloc[::skip, :]
    
    # Plot velocity vectors
    quiver = ax.quiver(df_sub['x-coordinate'], df_sub['y-coordinate'],
                       df_sub['x-velocity'], df_sub['y-velocity'],
                       df_sub['velocity-magnitude'],
                       cmap='jet', scale=None, width=0.003)
    
    # Add colorbar
    cbar = plt.colorbar(quiver, ax=ax)
    cbar.set_label('Velocity Magnitude [m/s]', rotation=270, labelpad=20)
    
    # Format plot
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_title(title)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight')
    plt.close()

def create_streamlines(df, title, filename):
    """Create streamline plot"""
    fig, ax = plt.subplots(figsize=(8, 7))
    
    # Create regular grid for streamlines
    x = np.linspace(0, 1, 100)
    y = np.linspace(0, 1, 100)
    X, Y = np.meshgrid(x, y)
    
    # Interpolate velocities onto regular grid
    from scipy.interpolate import griddata
    U = griddata((df['x-coordinate'], df['y-coordinate']), 
                 df['x-velocity'], (X, Y), method='linear')
    V = griddata((df['x-coordinate'], df['y-coordinate']), 
                 df['y-velocity'], (X, Y), method='linear')
    
    # Plot streamlines
    speed = np.sqrt(U**2 + V**2)
    strm = ax.streamplot(X, Y, U, V, color=speed, linewidth=1.5, 
                         cmap='jet', density=2, arrowsize=1.5)
    
    # Add colorbar
    cbar = plt.colorbar(strm.lines, ax=ax)
    cbar.set_label('Velocity Magnitude [m/s]', rotation=270, labelpad=20)
    
    # Format plot
    ax.set_xlabel('X [m]')
    ax.set_ylabel('Y [m]')
    ax.set_title(title)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight')
    plt.close()

def create_centerline_profiles(v_df, h_df, Re, output_dir):
    """Create centerline velocity profiles"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Vertical centerline (U velocity vs Y)
    v_sorted = v_df.sort_values('y-coordinate')
    ax1.plot(v_sorted['x-velocity'], v_sorted['y-coordinate'], 'b-', linewidth=2)
    ax1.set_xlabel('U Velocity [m/s]')
    ax1.set_ylabel('Y [m]')
    ax1.set_title(f'U-Velocity Profile at X=0.5 (Re={Re})')
    ax1.grid(True, alpha=0.3)
    
    # Horizontal centerline (V velocity vs X)
    h_sorted = h_df.sort_values('x-coordinate')
    ax2.plot(h_sorted['x-coordinate'], h_sorted['y-velocity'], 'r-', linewidth=2)
    ax2.set_xlabel('X [m]')
    ax2.set_ylabel('V Velocity [m/s]')
    ax2.set_title(f'V-Velocity Profile at Y=0.5 (Re={Re})')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'centerline_profiles.png', bbox_inches='tight')
    plt.close()

def create_wall_shear_plots(moving_df, stat_df, Re, output_dir):
    """Create wall shear stress plots"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Moving wall (top)
    moving_sorted = moving_df.sort_values('x-coordinate')
    ax1.plot(moving_sorted['x-coordinate'], moving_sorted['wall-shear'], 'b-', linewidth=2)
    ax1.set_xlabel('X [m]')
    ax1.set_ylabel('Wall Shear Stress [Pa]')
    ax1.set_title(f'Wall Shear Stress on Moving Wall (Re={Re})')
    ax1.grid(True, alpha=0.3)
    
    # Stationary walls (separate by coordinate)
    # Bottom wall
    bottom = stat_df[stat_df['y-coordinate'] < 0.01].sort_values('x-coordinate')
    # Left wall
    left = stat_df[stat_df['x-coordinate'] < 0.01].sort_values('y-coordinate')
    # Right wall
    right = stat_df[stat_df['x-coordinate'] > 0.99].sort_values('y-coordinate')
    
    if len(bottom) > 0:
        ax2.plot(bottom['x-coordinate'], bottom['wall-shear'], 'r-', 
                linewidth=2, label='Bottom Wall')
    if len(left) > 0:
        ax2.plot(left['y-coordinate'], left['wall-shear'], 'g-', 
                linewidth=2, label='Left Wall')
    if len(right) > 0:
        ax2.plot(right['y-coordinate'], right['wall-shear'], 'b-', 
                linewidth=2, label='Right Wall')
    
    ax2.set_xlabel('Position [m]')
    ax2.set_ylabel('Wall Shear Stress [Pa]')
    ax2.set_title(f'Wall Shear Stress on Stationary Walls (Re={Re})')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'wall_shear_stress.png', bbox_inches='tight')
    plt.close()

def process_case(case_dir):
    """Process a single Reynolds number case"""
    case_dir = Path(case_dir)
    Re = case_dir.name.replace('Re', '')
    
    print(f"Processing Re = {Re}...")
    
    try:
        # Load data - use space delimiter for Fluent format
        interior_df = pd.read_csv(case_dir / f'interior_full_Re{Re}.csv', delim_whitespace=True)
        moving_df = pd.read_csv(case_dir / f'moving_wall_full_Re{Re}.csv', delim_whitespace=True)
        stat_df = pd.read_csv(case_dir / f'stat_walls_full_Re{Re}.csv', delim_whitespace=True)
        v_center_df = pd.read_csv(case_dir / f'vertical_centerline_Re{Re}.csv', delim_whitespace=True)
        h_center_df = pd.read_csv(case_dir / f'horizontal_centerline_Re{Re}.csv', delim_whitespace=True)
        
        # Normalize column names
        for df in [interior_df, moving_df, stat_df, v_center_df, h_center_df]:
            df.columns = df.columns.str.strip().str.replace('"', '').str.lower()
        
        # Create visualizations
        print(f"  - Creating velocity magnitude contour...")
        create_contour_plot(interior_df, 'velocity-magnitude', 
                          f'Velocity Magnitude (Re={Re})',
                          case_dir / 'plot_velocity_magnitude.png',
                          cmap='jet')
        
        print(f"  - Creating pressure contour...")
        create_contour_plot(interior_df, 'pressure',
                          f'Pressure Field (Re={Re})',
                          case_dir / 'plot_pressure.png',
                          cmap='RdBu_r')
        
        print(f"  - Creating velocity vectors...")
        create_velocity_vectors(interior_df,
                               f'Velocity Vectors (Re={Re})',
                               case_dir / 'plot_velocity_vectors.png')
        
        print(f"  - Creating streamlines...")
        create_streamlines(interior_df,
                          f'Streamlines (Re={Re})',
                          case_dir / 'plot_streamlines.png')
        
        print(f"  - Creating centerline profiles...")
        create_centerline_profiles(v_center_df, h_center_df, Re, case_dir)
        
        print(f"  - Creating wall shear stress plots...")
        create_wall_shear_plots(moving_df, stat_df, Re, case_dir)
        
        print(f"  ✓ Completed Re = {Re}\n")
        
    except Exception as e:
        import traceback
        print(f"  ✗ Error processing Re = {Re}: {e}")
        print(traceback.format_exc())
        print()

def main():
    """Main execution"""
    print("=" * 60)
    print("CFD Visualization Generator")
    print("=" * 60)
    print()
    
    # Find all result directories
    result_dirs = sorted(glob.glob('results/Re*'))
    
    if not result_dirs:
        print("No result directories found!")
        return
    
    print(f"Found {len(result_dirs)} cases to process\n")
    
    # Process each case
    for case_dir in result_dirs:
        process_case(case_dir)
    
    print("=" * 60)
    print(f"✓ All visualizations completed!")
    print(f"✓ Generated 6 plots per case")
    print(f"✓ Total: {len(result_dirs) * 6} plots")
    print("=" * 60)

if __name__ == "__main__":
    main()