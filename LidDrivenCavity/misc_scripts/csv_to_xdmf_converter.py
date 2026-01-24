#!/usr/bin/env python3
import os
import glob
import numpy as np
import pandas as pd
import h5py
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
from pathlib import Path


def clean_column_names(df):
    """
    Clean and standardize column names from Fluent CSV files.
    
    Args:
        df (pandas.DataFrame): Input dataframe with original column names
        
    Returns:
        pandas.DataFrame: Dataframe with cleaned column names
    """
    # Create a mapping for common column name variations
    column_mapping = {
        'x-coordinate': 'x',
        'y-coordinate': 'y', 
        'x-velocity': 'velocity_x',
        'y-velocity': 'velocity_y',
        'velocity-magnitude': 'velocity_magnitude',
        'x-wall-shear': 'wall_shear_x',
        'y-wall-shear': 'wall_shear_y',
        'wall-shear': 'wall_shear_magnitude',
        'pressure': 'pressure',
        'cellnumber': 'cell_id'
    }
    
    # Clean column names (remove extra spaces, standardize)
    df.columns = df.columns.str.strip()
    
    # Apply mapping
    df = df.rename(columns=column_mapping)
    
    # Remove duplicate coordinate columns (Fluent sometimes exports them twice)
    cols_to_keep = []
    for col in df.columns:
        if col not in cols_to_keep:
            cols_to_keep.append(col)
    
    return df[cols_to_keep]


def convert_csv_to_xdmf(csv_file_path, wall_type="unknown", wall_id=0):
    """
    Convert a single CSV file to XDMF format.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        wall_type (str): Type of wall ('moving' or 'stationary')
        wall_id (int): Numeric identifier for the wall
        
    Returns:
        tuple: (points_array, data_dict, num_points) where:
            - points_array: Nx3 array of coordinates (x, y, z=0)
            - data_dict: Dictionary of field data arrays
            - num_points: Number of data points
    """
    print(f"  Converting {os.path.basename(csv_file_path)} ({wall_type} wall)")
    
    # Read CSV file
    try:
        df = pd.read_csv(csv_file_path, sep='\s+')
    except Exception as e:
        print(f"    Error reading CSV file: {e}")
        return None, None, 0
    
    # Clean column names
    df = clean_column_names(df)
    
    # Check if we have coordinate data
    if 'x' not in df.columns or 'y' not in df.columns:
        print(f"    Error: Missing coordinate columns in {csv_file_path}")
        return None, None, 0
    
    # Create 3D points array (z=0 for 2D data)
    num_points = len(df)
    points = np.zeros((num_points, 3), dtype=np.float64)
    points[:, 0] = df['x'].values  # X coordinates
    points[:, 1] = df['y'].values  # Y coordinates
    points[:, 2] = 0.0             # Z coordinates (2D data)
    
    # Prepare data dictionary for all scalar fields
    data_dict = {}
    
    # Add wall identifier
    data_dict['wall_id'] = np.full(num_points, wall_id, dtype=np.int32)
    data_dict['wall_type'] = np.full(num_points, 1 if wall_type == 'moving' else 0, dtype=np.int32)
    
    # Extract available data fields
    scalar_fields = ['velocity_x', 'velocity_y', 'velocity_magnitude', 
                    'wall_shear_x', 'wall_shear_y', 'wall_shear_magnitude', 
                    'pressure']
    
    for field in scalar_fields:
        if field in df.columns:
            data_dict[field] = df[field].values.astype(np.float64)
    
    # Add cell ID if available
    if 'cell_id' in df.columns:
        data_dict['cell_id'] = df['cell_id'].values.astype(np.int32)
    
    print(f"    Loaded {num_points} points with {len(data_dict)} data fields")
    return points, data_dict, num_points


def create_xdmf_file(output_path, h5_filename, points, data_dict, num_points):
    """
    Create an XDMF file that references HDF5 data.
    
    Args:
        output_path (str): Path for the output XDMF file
        h5_filename (str): Name of the HDF5 file (without path)
        points (np.array): Point coordinates array
        data_dict (dict): Dictionary of data arrays
        num_points (int): Number of points
    """
    # Create root XML structure
    root = ET.Element("Xdmf", Version="3.0")
    domain = ET.SubElement(root, "Domain")
    grid = ET.SubElement(domain, "Grid", Name="Wall_Surface", GridType="Uniform")
    
    # Define topology (point cloud)
    topology = ET.SubElement(grid, "Topology", TopologyType="Polyvertex", 
                           NodesPerElement=str(num_points))
    
    # Define geometry (3D coordinates)
    geometry = ET.SubElement(grid, "Geometry", GeometryType="XYZ")
    geom_dataitem = ET.SubElement(geometry, "DataItem", 
                                 Dimensions=f"{num_points} 3",
                                 NumberType="Float", 
                                 Precision="8",
                                 Format="HDF")
    geom_dataitem.text = f"{h5_filename}:/coordinates"
    
    # Add all scalar data fields as attributes
    for field_name, field_data in data_dict.items():
        attribute = ET.SubElement(grid, "Attribute", Name=field_name, 
                                AttributeType="Scalar", Center="Node")
        attr_dataitem = ET.SubElement(attribute, "DataItem",
                                    Dimensions=str(num_points),
                                    NumberType="Float" if field_data.dtype == np.float64 else "Int",
                                    Precision="8" if field_data.dtype == np.float64 else "4",
                                    Format="HDF")
        attr_dataitem.text = f"{h5_filename}:/{field_name}"
    
    # Write pretty-formatted XML
    rough_string = ET.tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Remove empty lines and fix XML declaration
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    lines[0] = '<?xml version="1.0" ?>'
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def save_to_hdf5(h5_path, points, data_dict):
    """
    Save point coordinates and data to HDF5 file.
    
    Args:
        h5_path (str): Path for the output HDF5 file
        points (np.array): Point coordinates array
        data_dict (dict): Dictionary of data arrays
    """
    with h5py.File(h5_path, 'w') as h5f:
        # Save coordinates
        h5f.create_dataset('coordinates', data=points, compression='gzip')
        
        # Save all data fields
        for field_name, field_data in data_dict.items():
            h5f.create_dataset(field_name, data=field_data, compression='gzip')


def merge_surfaces_to_xdmf(re_folder_path, re_number):
    """
    Merge moving wall and stationary walls data into a combined XDMF file.
    
    Args:
        re_folder_path (str): Path to the Reynolds number folder
        re_number (str): Reynolds number (e.g., "100", "1000")
    """
    print(f"Processing Reynolds number folder: Re{re_number}")
    
    # Define expected file patterns
    moving_wall_pattern = f"moving_wall_full_Re{re_number}.csv"
    stat_walls_pattern = f"stat_walls_full_Re{re_number}.csv"
    
    moving_wall_file = os.path.join(re_folder_path, moving_wall_pattern)
    stat_walls_file = os.path.join(re_folder_path, stat_walls_pattern)
    
    # Check if both files exist
    if not os.path.exists(moving_wall_file):
        print(f"  Warning: Moving wall file not found: {moving_wall_file}")
        return False
    
    if not os.path.exists(stat_walls_file):
        print(f"  Warning: Stationary walls file not found: {stat_walls_file}")
        return False
    
    # Convert individual CSV files
    moving_points, moving_data, moving_count = convert_csv_to_xdmf(
        moving_wall_file, "moving", wall_id=1)
    
    stat_points, stat_data, stat_count = convert_csv_to_xdmf(
        stat_walls_file, "stationary", wall_id=0)
    
    if moving_points is None or stat_points is None:
        print(f"  Error: Failed to process CSV files for Re{re_number}")
        return False
    
    # Create individual XDMF files for each surface
    print("  Creating individual XDMF files...")
    
    # Moving wall XDMF
    moving_h5_name = f"Re{re_number}_moving_wall.h5"
    moving_xdmf_name = f"Re{re_number}_moving_wall.xdmf"
    moving_h5_path = os.path.join(re_folder_path, moving_h5_name)
    moving_xdmf_path = os.path.join(re_folder_path, moving_xdmf_name)
    
    save_to_hdf5(moving_h5_path, moving_points, moving_data)
    create_xdmf_file(moving_xdmf_path, moving_h5_name, moving_points, 
                     moving_data, moving_count)
    
    # Stationary walls XDMF
    stat_h5_name = f"Re{re_number}_stat_walls.h5"
    stat_xdmf_name = f"Re{re_number}_stat_walls.xdmf"
    stat_h5_path = os.path.join(re_folder_path, stat_h5_name)
    stat_xdmf_path = os.path.join(re_folder_path, stat_xdmf_name)
    
    save_to_hdf5(stat_h5_path, stat_points, stat_data)
    create_xdmf_file(stat_xdmf_path, stat_h5_name, stat_points, 
                     stat_data, stat_count)
    
    # Merge into combined dataset
    print("  Creating combined XDMF file...")
    
    # Combine points
    combined_points = np.vstack([moving_points, stat_points])
    total_points = moving_count + stat_count
    
    # Combine data (ensure all fields are present in both datasets)
    combined_data = {}
    all_fields = set(moving_data.keys()) | set(stat_data.keys())
    
    for field in all_fields:
        if field in moving_data and field in stat_data:
            # Both datasets have this field
            combined_data[field] = np.concatenate([moving_data[field], stat_data[field]])
        elif field in moving_data:
            # Only moving wall has this field, pad stationary with zeros/default
            if moving_data[field].dtype == np.int32:
                stat_values = np.zeros(stat_count, dtype=np.int32)
            else:
                stat_values = np.zeros(stat_count, dtype=np.float64)
            combined_data[field] = np.concatenate([moving_data[field], stat_values])
        elif field in stat_data:
            # Only stationary walls have this field, pad moving with zeros/default
            if stat_data[field].dtype == np.int32:
                moving_values = np.zeros(moving_count, dtype=np.int32)
            else:
                moving_values = np.zeros(moving_count, dtype=np.float64)
            combined_data[field] = np.concatenate([moving_values, stat_data[field]])
    
    # Save combined dataset
    combined_h5_name = f"Re{re_number}_combined.h5"
    combined_xdmf_name = f"Re{re_number}_combined.xdmf"
    combined_h5_path = os.path.join(re_folder_path, combined_h5_name)
    combined_xdmf_path = os.path.join(re_folder_path, combined_xdmf_name)
    
    save_to_hdf5(combined_h5_path, combined_points, combined_data)
    create_xdmf_file(combined_xdmf_path, combined_h5_name, combined_points, 
                     combined_data, total_points)
    
    print(f"  ✓ Successfully processed Re{re_number}: {moving_count} + {stat_count} = {total_points} points")
    print(f"    Files created: {moving_xdmf_name}, {stat_xdmf_name}, {combined_xdmf_name}")
    
    return True


def extract_reynolds_number(folder_name):
    """
    Extract Reynolds number from folder name.
    
    Args:
        folder_name (str): Folder name like "Re100", "Re1000", etc.
        
    Returns:
        str or None: Reynolds number as string, or None if not found
    """
    match = re.match(r'Re(\d+)(?:-\d+\w*)?$', folder_name)
    return match.group(1) if match else None


def process_all_reynolds_folders(base_path):
    """
    Process all Reynolds number folders in the given base path.
    
    Args:
        base_path (str): Base path containing Reynolds number folders
    """
    print(f"Scanning for Reynolds number folders in: {base_path}")
    
    # Find all Re* folders
    re_folders = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and item.startswith('Re'):
            re_number = extract_reynolds_number(item)
            if re_number:
                re_folders.append((item, re_number, item_path))
    
    # Sort by Reynolds number (numeric)
    re_folders.sort(key=lambda x: int(x[1]))
    
    print(f"Found {len(re_folders)} Reynolds number folders")
    
    successful_conversions = 0
    failed_conversions = 0
    
    for folder_name, re_number, folder_path in re_folders:
        try:
            success = merge_surfaces_to_xdmf(folder_path, re_number)
            if success:
                successful_conversions += 1
            else:
                failed_conversions += 1
        except Exception as e:
            print(f"  ✗ Error processing {folder_name}: {e}")
            failed_conversions += 1
        
        print("")  # Add blank line between folders
    
    # Print summary
    print("="*60)
    print("CONVERSION SUMMARY")
    print("="*60)
    print(f"Total folders processed: {len(re_folders)}")
    print(f"Successful conversions: {successful_conversions}")
    print(f"Failed conversions: {failed_conversions}")
    
    if successful_conversions > 0:
        print("\nXDMF files can now be opened in ParaView for visualization.")
        print("Look for files ending in .xdmf in each Reynolds number folder.")


def main():
    """
    Main function to run the CSV to XDMF conversion process.
    """
    print("="*60)
    print("CSV to XDMF Converter for Ansys Fluent Wall Data")
    print("="*60)
    
    # Define the base path for results
    base_path = r"c:\Repositories\Data\results-3rd-order-disc"
    
    # Check if base path exists
    if not os.path.exists(base_path):
        print(f"Error: Base path does not exist: {base_path}")
        return
    
    # Process all Reynolds number folders
    process_all_reynolds_folders(base_path)
    
    print("\nConversion complete!")


if __name__ == "__main__":
    main()