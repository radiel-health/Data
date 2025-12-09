#!/usr/bin/env python3
"""
Test script for CSV to XDMF converter - single folder test
"""

import sys
import os
sys.path.append(r'c:\Repositories\Data')

# Import our converter functions
from csv_to_xdmf_converter import merge_surfaces_to_xdmf

def test_single_folder():
    """Test conversion on a single Reynolds number folder"""
    
    # Test with Re100 folder
    re_folder_path = r"c:\Repositories\Data\results-3rd-order-disc\Re100"
    re_number = "100"
    
    print("Testing CSV to XDMF conversion on Re100 folder...")
    
    try:
        success = merge_surfaces_to_xdmf(re_folder_path, re_number)
        if success:
            print("✓ Test successful! Check the Re100 folder for .xdmf and .h5 files")
        else:
            print("✗ Test failed")
    except Exception as e:
        print(f"✗ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_folder()