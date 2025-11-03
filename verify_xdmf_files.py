#!/usr/bin/env python3
"""
Verification script for CSV to XDMF conversion
This script checks the integrity of converted XDMF files
"""

import os
import glob
import h5py
import xml.etree.ElementTree as ET

def verify_xdmf_files(base_path):
    """
    Verify the integrity of all XDMF files in the results directory
    """
    print("="*60)
    print("XDMF FILE VERIFICATION")
    print("="*60)
    
    # Find all XDMF files
    xdmf_pattern = os.path.join(base_path, "Re*", "*.xdmf")
    xdmf_files = glob.glob(xdmf_pattern)
    
    print(f"Found {len(xdmf_files)} XDMF files to verify")
    print("")
    
    verification_results = {
        'total_files': len(xdmf_files),
        'valid_files': 0,
        'invalid_files': 0,
        'missing_h5_files': 0,
        'xml_errors': 0,
        'h5_errors': 0
    }
    
    for xdmf_file in sorted(xdmf_files):
        file_name = os.path.basename(xdmf_file)
        folder_name = os.path.basename(os.path.dirname(xdmf_file))
        
        try:
            # Check XML structure
            tree = ET.parse(xdmf_file)
            root = tree.getroot()
            
            # Find the HDF5 file reference
            h5_filename = None
            for dataitem in root.iter('DataItem'):
                if dataitem.get('Format') == 'HDF':
                    text = dataitem.text
                    if text and ':' in text:
                        h5_filename = text.split(':')[0]
                        break
            
            if not h5_filename:
                print(f"  ✗ {folder_name}/{file_name}: No HDF5 reference found")
                verification_results['xml_errors'] += 1
                continue
            
            # Check if HDF5 file exists
            h5_path = os.path.join(os.path.dirname(xdmf_file), h5_filename)
            if not os.path.exists(h5_path):
                print(f"  ✗ {folder_name}/{file_name}: Missing HDF5 file {h5_filename}")
                verification_results['missing_h5_files'] += 1
                continue
            
            # Verify HDF5 file can be opened and has expected datasets
            try:
                with h5py.File(h5_path, 'r') as h5f:
                    # Check for coordinates dataset
                    if 'coordinates' not in h5f:
                        print(f"  ✗ {folder_name}/{file_name}: Missing coordinates dataset")
                        verification_results['h5_errors'] += 1
                        continue
                    
                    coords = h5f['coordinates']
                    num_points = coords.shape[0]
                    
                    # Check expected number of points
                    if 'combined' in file_name and num_points != 516:
                        print(f"  ⚠ {folder_name}/{file_name}: Unexpected point count {num_points} (expected 516)")
                    elif 'moving_wall' in file_name and num_points != 129:
                        print(f"  ⚠ {folder_name}/{file_name}: Unexpected point count {num_points} (expected 129)")
                    elif 'stat_walls' in file_name and num_points != 387:
                        print(f"  ⚠ {folder_name}/{file_name}: Unexpected point count {num_points} (expected 387)")
                    
                    # Count available datasets
                    dataset_count = len(list(h5f.keys()))
                    
                print(f"  ✓ {folder_name}/{file_name}: OK ({num_points} points, {dataset_count} datasets)")
                verification_results['valid_files'] += 1
                
            except Exception as e:
                print(f"  ✗ {folder_name}/{file_name}: HDF5 error - {e}")
                verification_results['h5_errors'] += 1
                
        except Exception as e:
            print(f"  ✗ {folder_name}/{file_name}: XML error - {e}")
            verification_results['xml_errors'] += 1
    
    # Print summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    print(f"Total XDMF files checked: {verification_results['total_files']}")
    print(f"Valid files: {verification_results['valid_files']}")
    print(f"Invalid files: {verification_results['invalid_files']}")
    print(f"Missing HDF5 files: {verification_results['missing_h5_files']}")
    print(f"XML parsing errors: {verification_results['xml_errors']}")
    print(f"HDF5 access errors: {verification_results['h5_errors']}")
    
    if verification_results['valid_files'] == verification_results['total_files']:
        print("\n🎉 All files verified successfully! Ready for ParaView.")
    else:
        print(f"\n⚠️  {verification_results['total_files'] - verification_results['valid_files']} files have issues.")
    
    return verification_results

def main():
    base_path = r"c:\Repositories\Data\results-3rd-order-disc"
    
    if not os.path.exists(base_path):
        print(f"Error: Directory not found: {base_path}")
        return
    
    verify_xdmf_files(base_path)

if __name__ == "__main__":
    main()