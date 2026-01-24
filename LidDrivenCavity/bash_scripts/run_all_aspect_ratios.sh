#!/usr/bin/env bash
set -e

# ===============================================
# MASTER BATCH SCRIPT FOR MULTIPLE ASPECT RATIOS
# Lid-Driven Cavity CFD Simulations
# ===============================================

# ===================== PHYSICS =====================
HEIGHT=1.0                 # cavity height [m] - FIXED
rho=998.2                  # density [kg/m^3] (water at ~20°C)
mu=0.001003                # dynamic viscosity [Pa·s]
nu=$(python3 -c "print(${mu}/${rho})")
L=${HEIGHT}                # characteristic length (HEIGHT) [m]

echo "=============================================="
echo "MULTI-ASPECT RATIO BATCH CFD SIMULATION"
echo "=============================================="
echo "Physical properties:"
echo "  Density (ρ):           ${rho} kg/m³"
echo "  Dynamic viscosity (μ): ${mu} Pa·s"
echo "  Kinematic viscosity:   ${nu} m²/s"
echo "  Cavity height:         ${HEIGHT} m (FIXED)"
echo "  Characteristic length: ${L} m"
echo "=============================================="

# ===================== ASPECT RATIOS TO SIMULATE =====================
ASPECT_RATIOS=(1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9)

# ===================== REYNOLDS NUMBERS =====================
# Re from 100 to 2100 in steps of 100 (21 values)
RES=(100 200 300 400 500 600 700 800 900 1000 1100 1200 1300 1400 1500 1600 1700 1800 1900 2000 2100)

TOTAL_ASPECT_RATIOS=${#ASPECT_RATIOS[@]}
TOTAL_RES=${#RES[@]}
TOTAL_SIMULATIONS=$((TOTAL_ASPECT_RATIOS * TOTAL_RES))

echo ""
echo "Simulation matrix:"
echo "  Aspect ratios: ${ASPECT_RATIOS[@]}"
echo "  Reynolds numbers: ${RES[@]}"
echo "  Total aspect ratios: ${TOTAL_ASPECT_RATIOS}"
echo "  Reynolds per aspect ratio: ${TOTAL_RES}"
echo "  TOTAL SIMULATIONS: ${TOTAL_SIMULATIONS}"
echo "=============================================="
echo ""

# Create main results directory
mkdir -p results

SIMULATION_COUNT=0
START_TIME=$(date +%s)

# ===================== LOOP OVER ASPECT RATIOS =====================
for AR in "${ASPECT_RATIOS[@]}"; do
  
  # Calculate width from aspect ratio
  WIDTH=$(python3 -c "print(${AR} * ${HEIGHT})")
  
  # Construct mesh filename
  MESH="lidDrivenCavity${AR}x1.msh"
  
  # Create aspect ratio directory
  AR_DIR="results/AR_${AR}x1"
  mkdir -p "${AR_DIR}"
  
  echo ""
  echo "=============================================="
  echo "ASPECT RATIO: ${AR}:1 (Width × Height = ${WIDTH}m × ${HEIGHT}m)"
  echo "=============================================="
  echo "Mesh file: ${MESH}"
  
  # Check if mesh file exists
  if [ ! -f "${MESH}" ]; then
    echo "⚠ WARNING: Mesh file '${MESH}' not found!"
    echo "           Skipping aspect ratio ${AR}:1"
    echo "=============================================="
    continue
  fi
  
  # ===================== LOOP OVER REYNOLDS NUMBERS =====================
  for Re in "${RES[@]}"; do
    SIMULATION_COUNT=$((SIMULATION_COUNT + 1))
    
    # Compute lid velocity U = Re * nu / L
    U=$(python3 -c "print(${Re} * ${nu} / ${L})")
    
    # Adaptive iterations based on Reynolds number
    if [ $(python3 -c "print(1 if ${Re} <= 400 else 0)") -eq 1 ]; then
      ITERS=8000
    elif [ $(python3 -c "print(1 if ${Re} <= 1000 else 0)") -eq 1 ]; then
      ITERS=12000
    elif [ $(python3 -c "print(1 if ${Re} <= 1600 else 0)") -eq 1 ]; then
      ITERS=28000
    else
      ITERS=35000
    fi
    
    # Create case directory
    CASE_DIR="${AR_DIR}/Re_${Re}"
    mkdir -p "${CASE_DIR}"
    
    # Calculate centerline positions
    CENTERLINE_X=$(python3 -c "print(${WIDTH} / 2.0)")
    CENTERLINE_Y=$(python3 -c "print(${HEIGHT} / 2.0)")
    
    # Generate journal file from template
    JOURNAL_FILE="${AR_DIR}/run_AR${AR}_Re${Re}.jou"
    sed -e "s|MESH_FILE|${MESH}|g" \
        -e "s|VALUE_U|${U}|g" \
        -e "s|VALUE_RE|${Re}|g" \
        -e "s|VALUE_ITERS|${ITERS}|g" \
        -e "s|VALUE_WIDTH|${WIDTH}|g" \
        -e "s|VALUE_HEIGHT|${HEIGHT}|g" \
        -e "s|VALUE_CENTERLINE_X|${CENTERLINE_X}|g" \
        -e "s|VALUE_CENTERLINE_Y|${CENTERLINE_Y}|g" \
        -e "s|VALUE_OUTPUT_DIR|${CASE_DIR}|g" \
        journal_template_FINAL.jou > "${JOURNAL_FILE}"
    
    echo ""
    echo "----------------------------------------------"
    echo "Simulation ${SIMULATION_COUNT}/${TOTAL_SIMULATIONS}"
    echo "AR = ${AR}:1, Re = ${Re}"
    echo "----------------------------------------------"
    echo "  Width:            ${WIDTH} m"
    echo "  Lid velocity (U): ${U} m/s"
    echo "  Max iterations:   ${ITERS}"
    echo "  Journal:          ${JOURNAL_FILE}"
    echo "  Output:           ${CASE_DIR}/"
    echo "----------------------------------------------"
    
    # Run Fluent simulation
    sim_start=$(date +%s)
    
    fluent 2d -g -t1 -i "${JOURNAL_FILE}" | tee "${CASE_DIR}/console.log"
    
    sim_end=$(date +%s)
    sim_elapsed=$((sim_end - sim_start))
    
    echo "${sim_elapsed}" > "${CASE_DIR}/runtime.txt"
    echo "✓ Completed in ${sim_elapsed} seconds"
    
    # Save simulation metadata
    cat > "${CASE_DIR}/metadata.txt" << EOF
Aspect Ratio: ${AR}:1
Width: ${WIDTH} m
Height: ${HEIGHT} m
Reynolds Number: ${Re}
Lid Velocity: ${U} m/s
Max Iterations: ${ITERS}
Runtime: ${sim_elapsed} seconds
Density: ${rho} kg/m³
Dynamic Viscosity: ${mu} Pa·s
Kinematic Viscosity: ${nu} m²/s
Characteristic Length: ${L} m (height)
Mesh File: ${MESH}
Date: $(date)
EOF
    
  done  # End Reynolds number loop
  
  # Generate summary for this aspect ratio
  cat > "${AR_DIR}/aspect_ratio_summary.txt" << EOF
Aspect Ratio ${AR}:1 Summary
============================
Width × Height: ${WIDTH}m × ${HEIGHT}m
Mesh file: ${MESH}
Reynolds numbers: ${RES[@]}
Total simulations: ${TOTAL_RES}

Outputs per case (in Re_XXX/):
- case_Re_XXX.cas.h5                    Case/data file
- interior_full_Re_XXX.csv              Full interior field data
- moving_wall_Re_XXX.csv                Moving wall data
- stationary_walls_Re_XXX.csv           Stationary walls data
- vertical_centerline_Re_XXX.csv        Vertical centerline profile
- horizontal_centerline_Re_XXX.csv      Horizontal centerline profile
- contour_velocity_magnitude_Re_XXX.png Velocity magnitude contour
- contour_pressure_Re_XXX.png           Pressure contour
- contour_x_velocity_Re_XXX.png         X-velocity contour
- contour_y_velocity_Re_XXX.png         Y-velocity contour
- contour_vorticity_Re_XXX.png          Vorticity contour
- vector_velocity_Re_XXX.png            Velocity vectors
- pathlines_Re_XXX.png                  Pathlines/streamlines
- console.log                           Fluent console output
- runtime.txt                           Simulation runtime
- metadata.txt                          Simulation metadata

EOF
  
done  # End aspect ratio loop

# ===================== FINAL SUMMARY =====================
END_TIME=$(date +%s)
TOTAL_ELAPSED=$((END_TIME - START_TIME))
HOURS=$((TOTAL_ELAPSED / 3600))
MINUTES=$(((TOTAL_ELAPSED % 3600) / 60))
SECONDS=$((TOTAL_ELAPSED % 60))

echo ""
echo "=============================================="
echo "ALL SIMULATIONS COMPLETED!"
echo "=============================================="
echo "Total simulations run: ${SIMULATION_COUNT}/${TOTAL_SIMULATIONS}"
echo "Total runtime: ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo "Results directory: results/"
echo "=============================================="

# Generate master summary report
cat > "results/MASTER_SUMMARY.txt" << EOF
MULTI-ASPECT RATIO CFD BATCH SIMULATION - MASTER SUMMARY
========================================================
Completion Date: $(date)
Total Runtime: ${HOURS}h ${MINUTES}m ${SECONDS}s

SIMULATION MATRIX:
- Aspect ratios: ${ASPECT_RATIOS[@]}
- Reynolds numbers: ${RES[@]}
- Total aspect ratios: ${TOTAL_ASPECT_RATIOS}
- Reynolds per aspect ratio: ${TOTAL_RES}
- Total simulations: ${SIMULATION_COUNT}

PHYSICAL PROPERTIES:
- Density: ${rho} kg/m³
- Dynamic viscosity: ${mu} Pa·s
- Kinematic viscosity: ${nu} m²/s
- Cavity height: ${HEIGHT} m (FIXED)
- Characteristic length: ${L} m

DIRECTORY STRUCTURE:
results/
├── AR_1.1x1/
│   ├── Re_100/
│   ├── Re_200/
│   ├── ...
│   ├── Re_2100/
│   └── aspect_ratio_summary.txt
├── AR_1.2x1/
│   └── ...
├── ...
└── AR_1.9x1/
    └── ...

VISUALIZATIONS GENERATED PER CASE:
- Velocity magnitude contour
- Pressure contour
- X-velocity contour
- Y-velocity contour  
- Vorticity contour
- Velocity vector plot
- Pathlines/streamlines

DATA EXPORTS PER CASE:
- Interior field data (CSV)
- Moving wall data (CSV)
- Stationary walls data (CSV)
- Vertical centerline (CSV)
- Horizontal centerline (CSV)
- Case/data file (.cas.h5)

========================================================
EOF

echo ""
echo "✓ Master summary saved to results/MASTER_SUMMARY.txt"
echo ""
echo "🎉 Done! All aspect ratios completed! 🚀"
