# CSV to XDMF Converter - Usage Guide

## Overview

The `csv_to_xdmf_converter.py` script successfully converts Ansys Fluent wall surface CSV data into XDMF format for visualization in ParaView. The script processes both moving wall and stationary wall data, creating individual and combined datasets.

## Generated Files

For each Reynolds number folder (e.g., Re100, Re1000, etc.), the script creates:

1. **ReXXXX_moving_wall.xdmf/.h5** - Moving wall surface data only
2. **ReXXXX_stat_walls.xdmf/.h5** - Stationary walls surface data only  
3. **ReXXXX_combined.xdmf/.h5** - Combined dataset with both surfaces

## Data Fields Available

Each XDMF file contains the following attributes:

### Coordinate Data
- **coordinates**: 3D point coordinates (x, y, z=0 for 2D data)

### Wall Identification
- **wall_id**: Numeric identifier (1 = moving wall, 0 = stationary walls)
- **wall_type**: Binary flag (1 = moving, 0 = stationary)

### Flow Field Data
- **velocity_x**: X-component of velocity
- **velocity_y**: Y-component of velocity  
- **velocity_magnitude**: Magnitude of velocity vector
- **pressure**: Static pressure

### Wall Shear Stress
- **wall_shear_x**: X-component of wall shear stress
- **wall_shear_y**: Y-component of wall shear stress
- **wall_shear_magnitude**: Magnitude of wall shear stress vector

### Additional
- **cell_id**: Original Fluent cell number

## Using in ParaView

### Opening Files
1. Launch ParaView
2. Open any `.xdmf` file (File → Open)
3. Click "Apply" in the Properties panel

### Visualization Recommendations

#### Individual Surface Analysis
- Open `ReXXXX_moving_wall.xdmf` for moving wall analysis only
- Open `ReXXXX_stat_walls.xdmf` for stationary walls analysis only

#### Combined Surface Analysis  
- Open `ReXXXX_combined.xdmf` for both surfaces together
- Use the `wall_id` or `wall_type` field to filter/color surfaces:
  - Filters → Common → Threshold (threshold on wall_id)
  - Use wall_id = 1 for moving wall only
  - Use wall_id = 0 for stationary walls only

#### Recommended Visualizations

1. **Wall Shear Stress Distribution**
   - Color by: `wall_shear_magnitude`
   - Representation: Surface
   - Add colorbar and adjust range

2. **Velocity Profiles**
   - Color by: `velocity_magnitude` 
   - Use "Glyph" filter with velocity components as vectors
   - Scale glyphs appropriately

3. **Pressure Distribution**
   - Color by: `pressure`
   - Use contour lines for pressure isolines

4. **Surface Comparison**
   - Color by: `wall_type` to distinguish surfaces
   - Use different opacity or representations

### Animation Across Reynolds Numbers
1. Open multiple ReXXXX_combined.xdmf files
2. Use ParaView's "Animation View" 
3. Create keyframes for different Reynolds numbers
4. Animate flow field evolution with Re number

## File Structure Summary

```
results-3rd-order-disc/
├── Re100/
│   ├── moving_wall_full_Re100.csv      (original)
│   ├── stat_walls_full_Re100.csv       (original)
│   ├── Re100_moving_wall.xdmf/.h5      (converted)
│   ├── Re100_stat_walls.xdmf/.h5       (converted)
│   └── Re100_combined.xdmf/.h5         (converted)
├── Re150/
│   └── ... (similar structure)
├── ...
└── Re3250/
    └── ... (similar structure)
```

## Performance Notes

- **HDF5 files**: Contain the actual numerical data (binary format, compressed)
- **XDMF files**: Contain metadata and references to HDF5 data (XML format)
- **File sizes**: HDF5 files are much larger; XDMF files are small text files
- **ParaView performance**: XDMF+HDF5 format loads much faster than CSV

## Troubleshooting

### Common Issues
1. **File not loading**: Ensure both .xdmf and .h5 files are in the same directory
2. **No data visible**: Check that "Apply" was clicked in Properties panel
3. **Wrong coordinate system**: Data uses standard CFD coordinates (x-right, y-up)
4. **Missing fields**: Check the CSV source files have expected column names

### Verification
- Each dataset should have 516 points (129 moving + 387 stationary)
- Combined files should show data for both wall types
- All Reynolds numbers from Re100 to Re3250 should be processed

## Script Information

- **Script**: `csv_to_xdmf_converter.py`
- **Dependencies**: numpy, pandas, h5py, xml.etree.ElementTree
- **Total datasets processed**: 66 Reynolds number folders
- **Total files created**: 396 files (6 files per Reynolds number)

## Next Steps

The converted XDMF files are now ready for advanced CFD post-processing in ParaView, including:
- Quantitative analysis of wall shear stress distributions
- Flow separation and reattachment studies  
- Reynolds number dependency visualization
- Publication-quality rendering and animations