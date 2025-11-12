#!/usr/bin/env bash
set -e

# ===================== PHYSICS =====================
L=1.0                      # cavity side length [m]
rho=998.2                  # density [kg/m^3] (water at ~20°C)
mu=0.001003                # dynamic viscosity [Pa·s]
nu=$(python3 -c "print(${mu}/${rho})")

MESH="lidDrivenCavityFlow.msh"   # .msh mesh file exported from Workbench

echo "=========================================="
echo "Lid-Driven Cavity CFD Batch Simulation"
echo "=========================================="
echo "Physical properties:"
echo "  Density (ρ):           ${rho} kg/m³"
echo "  Dynamic viscosity (μ): ${mu} Pa·s"
echo "  Kinematic viscosity:   ${nu} m²/s"
echo "  Cavity length (L):     ${L} m"
echo "  Mesh file:             ${MESH}"
echo "=========================================="

# ===================== SIMULATION SETUP =====================
mkdir -p results

# Reynolds numbers to simulate
RES=(150 200 250 300 350 400 450 500 550 600 650 700 750 800 850 900 950
     1050 1100 1150 1200 1250 1300 1350 1400 1450 1500 1550 1600 1650 1700 1750 1800 1850 1900 1950 2000
     2050 2100 2150 2200 2250 2300 2350 2400 2450 2500 2550 2600 2650 2700 2750 2800 2850 2900 2950 3000
     3050 3100 3150 3200 3250)

TOTAL_CASES=${#RES[@]}
CURRENT_CASE=0

for Re in "${RES[@]}"; do
  CURRENT_CASE=$((CURRENT_CASE + 1))
  
  # Compute lid velocity U = Re * nu / L
  U=$(python3 -c "print(${Re} * ${nu} / ${L})")
  
  # Adaptive iterations based on Reynolds number
  if [ $(python3 -c "print(1 if ${Re} < 100 else 0)") -eq 1 ]; then
    ITERS=2000     # Low Re: typically converges quickly
  elif [ $(python3 -c "print(1 if ${Re} < 1000 else 0)") -eq 1 ]; then
    ITERS=6000     # Medium Re: needs more iterations
  else
    ITERS=10000    # High Re: needs many iterations
  fi
  
  mkdir -p "results/Re${Re}"
  
  # Generate journal: run_${Re}.jou
  sed -e "s|MESH_FILE|${MESH}|g" \
      -e "s|VALUE_U|${U}|g" \
      -e "s|VALUE_RE|${Re}|g" \
      -e "s|VALUE_ITERS|${ITERS}|g" \
      journal_template.jou > "run_${Re}.jou"
  
  echo ""
  echo "=========================================="
  echo "Case ${CURRENT_CASE}/${TOTAL_CASES}: Re = ${Re}"
  echo "=========================================="
  echo "  Lid velocity (U): ${U} m/s"
  echo "  Iterations:       ${ITERS}"
  echo "  Journal file:     run_${Re}.jou"
  echo "  Output directory: results/Re${Re}/"
  echo "=========================================="
  
  start=$(date +%s)
  
  # Run Fluent simulation
  fluent 2d -g -t1 -i "run_${Re}.jou" | tee "results/Re${Re}/console.log"
  
  end=$(date +%s)
  elapsed=$((end - start))
  
  echo "$elapsed" > "results/Re${Re}/runtime.txt"
  echo "✓ Completed in ${elapsed} seconds"
  
  # Save simulation metadata
  cat > "results/Re${Re}/metadata.txt" << EOF
Reynolds Number: ${Re}
Lid Velocity: ${U} m/s
Iterations: ${ITERS}
Runtime: ${elapsed} seconds
Density: ${rho} kg/m³
Dynamic Viscosity: ${mu} Pa·s
Kinematic Viscosity: ${nu} m²/s
Cavity Length: ${L} m
Mesh File: ${MESH}
Date: $(date)
EOF

done

echo ""
echo "=========================================="
echo "ALL SIMULATIONS COMPLETED!"
echo "=========================================="
echo "Total cases: ${TOTAL_CASES}"
echo "Results directory: results/"
echo "=========================================="

# Generate summary report
echo "Generating summary report..."
cat > "results/batch_summary.txt" << EOF
Lid-Driven Cavity CFD Batch Simulation Summary
==============================================
Date: $(date)
Total simulations: ${TOTAL_CASES}
Reynolds numbers: ${RES[@]}

Physical Properties:
- Density: ${rho} kg/m³
- Dynamic viscosity: ${mu} Pa·s
- Kinematic viscosity: ${nu} m²/s
- Cavity length: ${L} m
- Mesh file: ${MESH}

Outputs per case (in results/ReXXX/):
- *.cas.h5                              Case/data file
- interior_full_ReXXX.csv              Full interior field data
- moving_wall_full_ReXXX.csv           Moving wall data (incl. shear stress)
- stat_walls_full_ReXXX.csv            Stationary walls data
- vertical_centerline_ReXXX.csv        Vertical centerline profile
- horizontal_centerline_ReXXX.csv      Horizontal centerline profile
- forces_ReXXX.txt                     Force reports
- mass_flow_ReXXX.txt                  Mass flow reports
- avg_wall_shear_*.txt                 Average wall shear stress
- avg_pressure_*.txt                   Average pressure
- total_kinetic_energy_ReXXX.txt       Total kinetic energy
- residuals_ReXXX.csv                  Convergence history
- contour_*.png                        10+ contour visualizations
- vector_velocity_ReXXX.png            Velocity vector plot
- xy_*.png                             XY profile plots
- simulation_summary_ReXXX.txt         Per-case summary
- console.log                          Fluent console output
- runtime.txt                          Simulation runtime
- metadata.txt                         Simulation metadata

==============================================
EOF

echo "✓ Summary saved to results/batch_summary.txt"
echo ""
echo "Done! 🚀"