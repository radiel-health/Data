"""
Plot wall shear stress along cavity walls
Surface coordinate s starts at top-left corner (0,1) and increases counterclockwise
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def calculate_surface_coordinate(x, y, wall_type):
    """
    Calculate surface coordinate s that starts at (0,1) and increases counterclockwise
    
    Path: Top (moving lid) → Right wall → Bottom wall → Left wall
    s = 0 at (0, 1)  [top-left corner]
    """
    
    if wall_type == 'moving_wall':
        # Top wall: x goes from 0 to 1, y = 1
        # s goes from 0 to 1
        s = x
        
    elif wall_type == 'right':
        # Right wall: x = 1, y goes from 1 to 0
        # s goes from 1 to 2
        s = 1 + (1 - y)
        
    elif wall_type == 'bottom':
        # Bottom wall: x goes from 1 to 0, y = 0
        # s goes from 2 to 3
        s = 2 + (1 - x)
        
    elif wall_type == 'left':
        # Left wall: x = 0, y goes from 0 to 1
        # s goes from 3 to 4
        s = 3 + y
        
    return s


def identify_wall_segments(df):
    """
    Separate stationary walls into left, right, and bottom
    """
    
    x = df['x-coordinate'].values
    y = df['y-coordinate'].values
    
    # Tolerance for identifying walls
    tol = 0.01
    
    # Identify each wall segment
    left_mask = np.abs(x) < tol
    right_mask = np.abs(x - 1.0) < tol
    bottom_mask = np.abs(y) < tol
    top_mask = np.abs(y - 1.0) < tol
    
    segments = []
    
    if np.any(left_mask):
        segments.append(('left', df[left_mask]))
    if np.any(right_mask):
        segments.append(('right', df[right_mask]))
    if np.any(bottom_mask):
        segments.append(('bottom', df[bottom_mask]))
    
    return segments


def plot_wall_shear_stress(moving_wall_csv, stat_walls_csv, Re, save_path=None):
    """
    Plot wall shear stress along all cavity walls
    """
    
    print("\n" + "="*70)
    print(f"WALL SHEAR STRESS ANALYSIS - Re = {Re}")
    print("="*70 + "\n")
    
    # Load data with flexible delimiter detection
    # Fluent CSV exports can use different delimiters
    def smart_read_csv(filepath):
        """Try different delimiters to read CSV"""
        # Try comma first (standard CSV)
        try:
            df = pd.read_csv(filepath)
            if len(df.columns) > 1:  # Multiple columns found
                return df
        except:
            pass
        
        # Try whitespace (common in Fluent exports)
        try:
            df = pd.read_csv(filepath, delim_whitespace=True, skipinitialspace=True)
            if len(df.columns) > 1:
                return df
        except:
            pass
        
        # Try tab-delimited
        try:
            df = pd.read_csv(filepath, sep='\t')
            if len(df.columns) > 1:
                return df
        except:
            pass
        
        # Last resort: try space as delimiter
        try:
            df = pd.read_csv(filepath, sep=r'\s+')
            return df
        except Exception as e:
            raise ValueError(f"Could not parse CSV file: {filepath}\nError: {e}")
    
    moving_df = smart_read_csv(moving_wall_csv)
    stat_df = smart_read_csv(stat_walls_csv)
    
    print(f"Moving wall points: {len(moving_df)}")
    print(f"Stationary wall points: {len(stat_df)}")
    
    # Debug: Print all columns
    print(f"\nAvailable columns in moving_wall:")
    for col in moving_df.columns:
        print(f"  - {col}")
    
    # Get column names (handle different naming conventions)
    x_col = [c for c in moving_df.columns if 'x-coordinate' in c.lower() or c.lower() == 'x'][0]
    y_col = [c for c in moving_df.columns if 'y-coordinate' in c.lower() or c.lower() == 'y'][0]
    
    # Try to find wall shear columns
    shear_candidates = [c for c in moving_df.columns if 'wall-shear' in c.lower() or 'shear' in c.lower()]
    shear_candidates = [c for c in shear_candidates if 'x-wall' not in c.lower() and 'y-wall' not in c.lower()]
    
    if len(shear_candidates) == 0:
        print(f"\n❌ ERROR: Could not find wall shear stress column!")
        print(f"Available columns: {list(moving_df.columns)}")
        raise ValueError("Wall shear stress column not found")
    
    shear_col = shear_candidates[0]
    
    # Also get vector components if available
    x_shear_candidates = [c for c in moving_df.columns if 'x-wall-shear' in c.lower()]
    y_shear_candidates = [c for c in moving_df.columns if 'y-wall-shear' in c.lower()]
    
    has_vector_components = len(x_shear_candidates) > 0 and len(y_shear_candidates) > 0
    
    if has_vector_components:
        x_shear_col = x_shear_candidates[0]
        y_shear_col = y_shear_candidates[0]
        print(f"\n✅ Vector components available: {x_shear_col}, {y_shear_col}")
    else:
        x_shear_col = None
        y_shear_col = None
    
    print(f"\nColumns detected:")
    print(f"  X: {x_col}")
    print(f"  Y: {y_col}")
    print(f"  Wall shear magnitude: {shear_col}")
    if has_vector_components:
        print(f"  X-component: {x_shear_col}")
        print(f"  Y-component: {y_shear_col}")
    
    # Collect all wall data with surface coordinates
    all_s = []
    all_shear = []
    wall_labels = []
    
    # 1. Moving wall (top)
    x_moving = moving_df[x_col].values
    y_moving = moving_df[y_col].values
    shear_moving = moving_df[shear_col].values
    
    s_moving = calculate_surface_coordinate(x_moving, y_moving, 'moving_wall')
    
    # Sort by s for moving wall
    sort_idx_moving = np.argsort(s_moving)
    s_moving = s_moving[sort_idx_moving]
    shear_moving = shear_moving[sort_idx_moving]
    
    all_s.append(s_moving)
    all_shear.append(shear_moving)
    wall_labels.append('Top (Moving)')
    
    # Store sorted indices for vector components later
    moving_wall_sort_idx = sort_idx_moving
    
    # 2. Stationary walls (right, bottom, left)
    segments = identify_wall_segments(stat_df)
    
    for wall_type, segment_df in segments:
        x_seg = segment_df[x_col].values
        y_seg = segment_df[y_col].values
        shear_seg = segment_df[shear_col].values
        
        s_seg = calculate_surface_coordinate(x_seg, y_seg, wall_type)
        
        # Sort by s
        sort_idx = np.argsort(s_seg)
        s_seg = s_seg[sort_idx]
        shear_seg = shear_seg[sort_idx]
        
        all_s.append(s_seg)
        all_shear.append(shear_seg)
        wall_labels.append(wall_type.capitalize())
    
    # Statistics
    all_shear_combined = np.concatenate(all_shear)
    print(f"\n📊 WALL SHEAR STRESS STATISTICS")
    print("-"*70)
    print(f"Maximum: {np.max(np.abs(all_shear_combined)):.6e} Pa")
    print(f"Minimum: {np.min(np.abs(all_shear_combined)):.6e} Pa")
    print(f"Mean:    {np.mean(np.abs(all_shear_combined)):.6e} Pa")
    
    # Find peak locations
    max_shear_idx = np.argmax(np.abs(all_shear_combined))
    max_shear_val = all_shear_combined[max_shear_idx]
    print(f"\nPeak shear stress: {max_shear_val:.6e} Pa")
    
    # Create plot - 2 subplots only (magnitude)
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Linear scale - shows the peaks clearly
    ax = axes[0]
    
    colors = ['red', 'blue', 'green', 'purple']
    
    for i, (s, shear, label) in enumerate(zip(all_s, all_shear, wall_labels)):
        ax.plot(s, shear, '-o', label=label, linewidth=2, markersize=4, 
                color=colors[i % len(colors)], alpha=0.7)
    
    # Mark wall transitions
    ax.axvline(x=1, color='gray', linestyle='--', alpha=0.5, label='Wall transitions')
    ax.axvline(x=2, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=3, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_xlabel('Surface Coordinate s', fontsize=12, fontweight='bold')
    ax.set_ylabel('Wall Shear Stress [Pa]', fontsize=12, fontweight='bold')
    ax.set_title(f'Wall Shear Stress Distribution (Re={Re})\ns=0 at (0,1), increases counterclockwise', 
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)
    
    # Add annotations for wall segments
    y_pos = ax.get_ylim()[1] * 0.95
    ax.text(0.5, y_pos, 'Top\n(Moving)', ha='center', fontsize=10, 
            bbox=dict(boxstyle='round', facecolor='red', alpha=0.2))
    ax.text(1.5, y_pos, 'Right\n(Stationary)', ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='blue', alpha=0.2))
    ax.text(2.5, y_pos, 'Bottom\n(Stationary)', ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='green', alpha=0.2))
    ax.text(3.5, y_pos, 'Left\n(Stationary)', ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='purple', alpha=0.2))
    
    # Plot 2: Log scale - shows small values and variations
    ax = axes[1]
    
    for i, (s, shear, label) in enumerate(zip(all_s, all_shear, wall_labels)):
        ax.semilogy(s, np.abs(shear), '-o', label=label, linewidth=2, markersize=4,
                    color=colors[i % len(colors)], alpha=0.7)
    
    ax.axvline(x=1, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=2, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=3, color='gray', linestyle='--', alpha=0.5)
    
    ax.set_xlabel('Surface Coordinate s', fontsize=12, fontweight='bold')
    ax.set_ylabel('|Wall Shear Stress| [Pa] (log scale)', fontsize=12, fontweight='bold')
    ax.set_title('Absolute Wall Shear Stress (Log Scale) - Shows All Magnitudes', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3, which='both')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\n✅ Saved plot: {save_path}")
    
    plt.show()
    
    print("\n" + "="*70)
    
    return all_s, all_shear


def create_schematic():
    """
    Create a schematic showing the surface coordinate system
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Draw cavity
    ax.plot([0, 1, 1, 0, 0], [1, 1, 0, 0, 1], 'k-', linewidth=3)
    
    # Mark corners with s values
    corners = [
        (0, 1, 's=0\n(0,1)', 'top'),
        (1, 1, 's=1\n(1,1)', 'top'),
        (1, 0, 's=2\n(1,0)', 'bottom'),
        (0, 0, 's=3\n(0,0)', 'bottom'),
    ]
    
    for x, y, label, va in corners:
        ax.plot(x, y, 'ro', markersize=15)
        if va == 'top':
            ax.text(x, y+0.08, label, ha='center', va='bottom', fontsize=12, fontweight='bold')
        else:
            ax.text(x, y-0.08, label, ha='center', va='top', fontsize=12, fontweight='bold')
    
    # Add arrows showing direction
    arrow_props = dict(arrowstyle='->', lw=3, color='blue')
    
    # Top
    ax.annotate('', xy=(0.5, 1.05), xytext=(0.2, 1.05), arrowprops=arrow_props)
    ax.text(0.5, 1.12, 'Moving Wall →', ha='center', fontsize=11, color='blue', fontweight='bold')
    
    # Right
    ax.annotate('', xy=(1.05, 0.5), xytext=(1.05, 0.8), arrowprops=arrow_props)
    ax.text(1.15, 0.5, '↓', ha='left', fontsize=20, color='blue', fontweight='bold')
    
    # Bottom
    ax.annotate('', xy=(0.5, -0.05), xytext=(0.8, -0.05), arrowprops=arrow_props)
    ax.text(0.5, -0.12, '← Stationary', ha='center', fontsize=11, color='blue', fontweight='bold')
    
    # Left
    ax.annotate('', xy=(-0.05, 0.5), xytext=(-0.05, 0.2), arrowprops=arrow_props)
    ax.text(-0.15, 0.5, '↑', ha='right', fontsize=20, color='blue', fontweight='bold')
    
    # Labels
    ax.text(0.5, 0.5, 'Lid-Driven\nCavity', ha='center', va='center', fontsize=14, 
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    ax.set_xlim(-0.3, 1.3)
    ax.set_ylim(-0.3, 1.3)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Surface Coordinate System\ns increases counterclockwise from top-left corner', 
                 fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('surface_coordinate_schematic.png', dpi=150, bbox_inches='tight')
    print("✅ Saved schematic: surface_coordinate_schematic.png")
    plt.show()


if __name__ == "__main__":
    
    # Reynolds numbers to process (matching your batch script)
    RES = [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000,
           1050, 1100, 1150, 1200, 1250, 1300, 1350, 1400, 1450, 1500, 1550, 1600, 1650, 1700, 1750, 1800, 
           1850, 1900, 1950, 2000, 2050, 2100, 2150, 2200, 2250, 2300, 2350, 2400, 2450, 2500, 2550, 2600, 
           2650, 2700, 2750, 2800, 2850, 2900, 2950, 3000, 3050, 3100, 3150, 3200, 3250]
    
    # Create schematic once
    print("\n📐 Creating surface coordinate schematic...")
    create_schematic()
    
    # Process all Reynolds numbers
    print("\n" + "="*70)
    print("BATCH WALL SHEAR STRESS PLOTTING")
    print("="*70)
    print(f"\nProcessing {len(RES)} Reynolds numbers...")
    
    successful = 0
    failed = []
    
    for i, Re in enumerate(RES, 1):
        print(f"\n[{i}/{len(RES)}] Processing Re = {Re}...")
        
        moving_wall_csv = f"results/Re{Re}/moving_wall_full_Re{Re}.csv"
        stat_walls_csv = f"results/Re{Re}/stat_walls_full_Re{Re}.csv"
        save_path = f"results/Re{Re}/plot_wall_shear_line_Re{Re}.png"
        
        try:
            all_s, all_shear = plot_wall_shear_stress(
                moving_wall_csv, 
                stat_walls_csv, 
                Re,
                save_path=save_path
            )
            successful += 1
            print(f"✅ Re={Re} complete!")
            
            # Close plot to free memory
            plt.close('all')
            
        except FileNotFoundError as e:
            print(f"⚠️  Skipping Re={Re} - files not found")
            failed.append(Re)
            
        except Exception as e:
            print(f"❌ Error processing Re={Re}: {e}")
            failed.append(Re)
    
    # Summary
    print("\n" + "="*70)
    print("BATCH PROCESSING COMPLETE")
    print("="*70)
    print(f"✅ Successful: {successful}/{len(RES)}")
    
    if failed:
        print(f"⚠️  Failed/Skipped: {len(failed)}")
        print(f"   Re values: {failed}")
    else:
        print("🎉 All Reynolds numbers processed successfully!")
    
    print("\n📁 Output files saved as:")
    print("   results/Re{Re}/plot_wall_shear_line_Re{Re}.png")
    print("="*70)