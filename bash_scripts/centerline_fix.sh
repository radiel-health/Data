#!/bin/bash

RE_VALUES=(100 150 200 250 300 350 400 450 500 550 600 650 700 750 800 850 900 950 1000 1050 1100 1150 1200 1250 1300 1350 1400 1450 1500 1550 1600 1650 1700 1750 1800 1850 1900 1950 2000 2050 2100 2150 2200 2250 2300 2350 2400 2450 2500 2550)

echo "================================================"
echo "Fixing centerlines for all Re values..."
echo "================================================"

for RE in "${RE_VALUES[@]}"; do
    echo "Processing Re=${RE}..."
    
    # Create journal file
    cat > fix_Re${RE}.jou << EOF
/file/read-case-data results/Re${RE}/cavity_Re${RE}.cas.h5
/surface/line-surface vertical-centerline 0.85 0.0 0.85 1.0
/surface/line-surface horizontal-centerline 0.3 0.5 1.4 0.5
/file/export/ascii results/Re${RE}/vertical_centerline_Re${RE}.csv vertical-centerline () no x-coordinate y-coordinate x-velocity y-velocity velocity-magnitude pressure
/file/export/ascii results/Re${RE}/horizontal_centerline_Re${RE}.csv horizontal-centerline () no x-coordinate y-coordinate x-velocity y-velocity velocity-magnitude pressure
/exit yes
EOF
    
    # Run Fluent quietly
    fluent 2d -g < fix_Re${RE}.jou > /dev/null 2>&1
    
    # Check if successful
    if [ -f "results/Re${RE}/vertical_centerline_Re${RE}.csv" ]; then
        echo "  ✓ Re=${RE} complete"
    else
        echo "  ✗ Re=${RE} FAILED"
    fi
done

echo "================================================"
echo "All centerlines fixed!"
echo "Now run: python benchmark.py"
echo "================================================"