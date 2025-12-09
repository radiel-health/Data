#!/usr/bin/env python3
"""
Post-processing and visualization script for multi-aspect ratio CFD results.
Analyzes centerline profiles, creates comparison plots, and generates reports.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import glob

class CFDResultsAnalyzer:
    """Analyze and visualize CFD simulation results."""
    
    def __init__(self, results_dir='results'):
        self.results_dir = Path(results_dir)
        self.aspect_ratios = []
        self.reynolds_numbers = []
        self.load_simulation_matrix()
        
    def load_simulation_matrix(self):
        """Discover available aspect ratios and Reynolds numbers."""
        ar_dirs = sorted(self.results_dir.glob('AR_*'))
        
        for ar_dir in ar_dirs:
            ar_str = ar_dir.name.replace('AR_', '').replace('x1', '')
            self.aspect_ratios.append(float(ar_str))
            
            re_dirs = sorted(ar_dir.glob('Re_*'))
            if not self.reynolds_numbers:
                for re_dir in re_dirs:
                    re_str = re_dir.name.replace('Re_', '')
                    self.reynolds_numbers.append(int(re_str))
        
        print(f"Found {len(self.aspect_ratios)} aspect ratios: {self.aspect_ratios}")
        print(f"Found {len(self.reynolds_numbers)} Reynolds numbers: {self.reynolds_numbers}")
    
    def load_centerline_data(self, ar, re, centerline='vertical'):
        """Load vertical or horizontal centerline data."""
        ar_dir = self.results_dir / f'AR_{ar}x1'
        re_dir = ar_dir / f'Re_{re}'
        
        if centerline == 'vertical':
            csv_file = re_dir / f'vertical_centerline_Re_{re}.csv'
        else:
            csv_file = re_dir / f'horizontal_centerline_Re_{re}.csv'
        
        if not csv_file.exists():
            print(f"Warning: {csv_file} not found")
            return None
        
        try:
            df = pd.read_csv(csv_file)
            return df
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")
            return None
    
    def plot_velocity_profiles_vs_reynolds(self, ar, save=True):
        """Plot vertical centerline velocity profiles for different Re at fixed AR."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        for re in self.reynolds_numbers:
            df = self.load_centerline_data(ar, re, 'vertical')
            if df is not None and 'y-coordinate' in df.columns and 'x-velocity' in df.columns:
                y = df['y-coordinate'].values
                u = df['x-velocity'].values
                ax1.plot(u, y, label=f'Re={re}', linewidth=1.5)
        
        ax1.set_xlabel('u-velocity (m/s)', fontsize=12)
        ax1.set_ylabel('y-coordinate (m)', fontsize=12)
        ax1.set_title(f'Vertical Centerline u-velocity\nAspect Ratio {ar}:1', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        
        for re in self.reynolds_numbers:
            df = self.load_centerline_data(ar, re, 'horizontal')
            if df is not None and 'x-coordinate' in df.columns and 'y-velocity' in df.columns:
                x = df['x-coordinate'].values
                v = df['y-velocity'].values
                ax2.plot(x, v, label=f'Re={re}', linewidth=1.5)
        
        ax2.set_xlabel('x-coordinate (m)', fontsize=12)
        ax2.set_ylabel('v-velocity (m/s)', fontsize=12)
        ax2.set_title(f'Horizontal Centerline v-velocity\nAspect Ratio {ar}:1', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
        
        plt.tight_layout()
        
        if save:
            output_dir = self.results_dir / f'AR_{ar}x1' / 'analysis'
            output_dir.mkdir(exist_ok=True)
            plt.savefig(output_dir / f'velocity_profiles_AR{ar}.png', dpi=300, bbox_inches='tight')
            print(f"Saved: {output_dir / f'velocity_profiles_AR{ar}.png'}")
        
        plt.close()
    
    def plot_aspect_ratio_comparison(self, re, save=True):
        """Compare velocity profiles across aspect ratios at fixed Re."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        for ar in self.aspect_ratios:
            df = self.load_centerline_data(ar, re, 'vertical')
            if df is not None and 'y-coordinate' in df.columns and 'x-velocity' in df.columns:
                y = df['y-coordinate'].values
                u = df['x-velocity'].values
                ax1.plot(u, y, label=f'AR={ar}:1', linewidth=2, marker='o', markersize=3, markevery=10)
        
        ax1.set_xlabel('u-velocity (m/s)', fontsize=12)
        ax1.set_ylabel('y-coordinate (m)', fontsize=12)
        ax1.set_title(f'Vertical Centerline u-velocity\nRe = {re}', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=10)
        
        for ar in self.aspect_ratios:
            df = self.load_centerline_data(ar, re, 'horizontal')
            if df is not None and 'x-coordinate' in df.columns and 'y-velocity' in df.columns:
                x = df['x-coordinate'].values
                v = df['y-velocity'].values
                # Normalize x by width for fair comparison
                x_norm = x / (ar * 1.0)  # height = 1.0
                ax2.plot(x_norm, v, label=f'AR={ar}:1', linewidth=2, marker='s', markersize=3, markevery=10)
        
        ax2.set_xlabel('Normalized x-coordinate (x/W)', fontsize=12)
        ax2.set_ylabel('v-velocity (m/s)', fontsize=12)
        ax2.set_title(f'Horizontal Centerline v-velocity\nRe = {re}', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=10)
        
        plt.tight_layout()
        
        if save:
            output_dir = self.results_dir / 'comparison_plots'
            output_dir.mkdir(exist_ok=True)
            plt.savefig(output_dir / f'AR_comparison_Re{re}.png', dpi=300, bbox_inches='tight')
            print(f"Saved: {output_dir / f'AR_comparison_Re{re}.png'}")
        
        plt.close()
    
    def analyze_vortex_center(self, ar, re):
        """Find primary vortex center location from velocity data."""
        df_v = self.load_centerline_data(ar, re, 'vertical')
        df_h = self.load_centerline_data(ar, re, 'horizontal')
        
        if df_v is None or df_h is None:
            return None
        
        # Find zero-crossing of u-velocity (approximate vortex center y-location)
        if 'y-coordinate' in df_v.columns and 'x-velocity' in df_v.columns:
            y = df_v['y-coordinate'].values
            u = df_v['x-velocity'].values
            
            # Find where u crosses zero
            zero_crossings = np.where(np.diff(np.sign(u)))[0]
            if len(zero_crossings) > 0:
                idx = zero_crossings[0]
                vortex_y = (y[idx] + y[idx+1]) / 2
            else:
                vortex_y = None
        else:
            vortex_y = None
        
        # Find zero-crossing of v-velocity (approximate vortex center x-location)
        if 'x-coordinate' in df_h.columns and 'y-velocity' in df_h.columns:
            x = df_h['x-coordinate'].values
            v = df_h['y-velocity'].values
            
            zero_crossings = np.where(np.diff(np.sign(v)))[0]
            if len(zero_crossings) > 0:
                idx = zero_crossings[0]
                vortex_x = (x[idx] + x[idx+1]) / 2
            else:
                vortex_x = None
        else:
            vortex_x = None
        
        return {'x': vortex_x, 'y': vortex_y, 'ar': ar, 're': re}
    
    def plot_vortex_center_migration(self, save=True):
        """Plot how vortex center moves with Reynolds number and aspect ratio."""
        vortex_data = []
        
        for ar in self.aspect_ratios:
            for re in self.reynolds_numbers:
                vortex = self.analyze_vortex_center(ar, re)
                if vortex and vortex['x'] is not None and vortex['y'] is not None:
                    vortex_data.append(vortex)
        
        if not vortex_data:
            print("No vortex data found")
            return
        
        df = pd.DataFrame(vortex_data)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        for ar in self.aspect_ratios:
            data = df[df['ar'] == ar]
            if len(data) > 0:
                ax1.plot(data['re'], data['x'], marker='o', label=f'AR={ar}:1', linewidth=2)
                ax2.plot(data['re'], data['y'], marker='s', label=f'AR={ar}:1', linewidth=2)
        
        ax1.set_xlabel('Reynolds Number', fontsize=12)
        ax1.set_ylabel('Vortex Center X-coordinate (m)', fontsize=12)
        ax1.set_title('Primary Vortex Center X-location', fontsize=14)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=10)
        
        ax2.set_xlabel('Reynolds Number', fontsize=12)
        ax2.set_ylabel('Vortex Center Y-coordinate (m)', fontsize=12)
        ax2.set_title('Primary Vortex Center Y-location', fontsize=14)
        ax2.grid(True, alpha=0.3)
        ax2.legend(fontsize=10)
        
        plt.tight_layout()
        
        if save:
            output_dir = self.results_dir / 'analysis'
            output_dir.mkdir(exist_ok=True)
            plt.savefig(output_dir / 'vortex_center_migration.png', dpi=300, bbox_inches='tight')
            print(f"Saved: {output_dir / 'vortex_center_migration.png'}")
        
        plt.close()
    
    def generate_summary_report(self):
        """Generate text summary of all simulations."""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("CFD SIMULATION RESULTS SUMMARY")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        for ar in self.aspect_ratios:
            report_lines.append(f"\nAspect Ratio: {ar}:1 (Width = {ar*1.0:.1f}m × Height = 1.0m)")
            report_lines.append("-" * 80)
            
            for re in self.reynolds_numbers:
                ar_dir = self.results_dir / f'AR_{ar}x1'
                re_dir = ar_dir / f'Re_{re}'
                
                metadata_file = re_dir / 'metadata.txt'
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        lines = f.readlines()
                        runtime = next((l.split(':')[1].strip() for l in lines if 'Runtime' in l), 'N/A')
                        lid_vel = next((l.split(':')[1].strip() for l in lines if 'Lid Velocity' in l), 'N/A')
                    
                    report_lines.append(f"  Re={re:4d}: Runtime={runtime:>10s}, Lid Velocity={lid_vel}")
                else:
                    report_lines.append(f"  Re={re:4d}: NOT COMPLETED")
        
        report_lines.append("\n" + "=" * 80)
        
        report_path = self.results_dir / 'analysis' / 'detailed_summary.txt'
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"Summary report saved: {report_path}")
        return '\n'.join(report_lines)

def main():
    """Main execution function."""
    print("CFD Results Post-Processing Tool")
    print("=" * 50)
    
    analyzer = CFDResultsAnalyzer('results')
    
    if not analyzer.aspect_ratios:
        print("No results found! Make sure simulations have completed.")
        return
    
    print("\n1. Generating velocity profile plots for each aspect ratio...")
    for ar in analyzer.aspect_ratios:
        analyzer.plot_velocity_profiles_vs_reynolds(ar)
    
    print("\n2. Generating aspect ratio comparison plots...")
    # Select a few representative Reynolds numbers for comparison
    re_compare = [100, 400, 1000, 1600, 2100]
    for re in re_compare:
        if re in analyzer.reynolds_numbers:
            analyzer.plot_aspect_ratio_comparison(re)
    
    print("\n3. Analyzing vortex center migration...")
    analyzer.plot_vortex_center_migration()
    
    print("\n4. Generating detailed summary report...")
    analyzer.generate_summary_report()
    
    print("\n" + "=" * 50)
    print("Post-processing complete!")
    print("Check results/analysis/ and results/comparison_plots/ for outputs")

if __name__ == '__main__':
    main()