#!/usr/bin/env bash
set -e

# Trapezoid Lid-Driven Cavity - Batch Simulation
# Matches YOUR working journal template

# Geometry
WIDTH=1.0
HEIGHT=1.0
CENTERLINE_X=0.0    # Vertical centerline X position
CENTERLINE_Y=0.5    # Horizontal centerline Y position

# Physics  
rho=998.2
mu=0.001003
nu=$(python3 -c "print(${mu}/${rho})")
L=${HEIGHT}

MESH="trapezoid.msh"
TEMPLATE="journal_templates/journal_template_FINAL.jou"

echo "=========================================="
echo "Trapezoid Batch Simulation"
echo "=========================================="

if [ ! -f "${MESH}" ]; then
    echo "ERROR: ${MESH} not found!"
    exit 1
fi

if [ ! -f "${TEMPLATE}" ]; then
    echo "ERROR: ${TEMPLATE} not found!"
    echo "Rename your working template to: ${TEMPLATE}"
    exit 1
fi

mkdir -p results

RES=(100 200 300 400 500 600 700 800 900 1000 1100 1200 1300 1400 1500 1600 1700 1800 1900 2000 2100)
TOTAL=${#RES[@]}
CURRENT=0

for Re in "${RES[@]}"; do
  CURRENT=$((CURRENT + 1))
  
  U=$(python3 -c "print(${Re} * ${nu} / ${L})")
  
  if [ ${Re} -le 400 ]; then
    ITERS=5000
  elif [ ${Re} -le 1000 ]; then
    ITERS=10000
  elif [ ${Re} -le 1500 ]; then
    ITERS=15000
  else
    ITERS=20000
  fi
  
  OUTPUT_DIR="results/Re_${Re}"
  mkdir -p "${OUTPUT_DIR}"
  
  # Substitute ALL placeholders from YOUR working template
  sed -e "s|MESH_FILE|${MESH}|g" \
      -e "s|VALUE_WIDTH|${WIDTH}|g" \
      -e "s|VALUE_HEIGHT|${HEIGHT}|g" \
      -e "s|VALUE_U|${U}|g" \
      -e "s|VALUE_RE|${Re}|g" \
      -e "s|VALUE_ITERS|${ITERS}|g" \
      -e "s|VALUE_OUTPUT_DIR|${OUTPUT_DIR}|g" \
      -e "s|VALUE_CENTERLINE_X|${CENTERLINE_X}|g" \
      -e "s|VALUE_CENTERLINE_Y|${CENTERLINE_Y}|g" \
      "${TEMPLATE}" > "run_Re_${Re}.jou"
  
  echo ""
  echo "=========================================="
  echo "Case ${CURRENT}/${TOTAL}: Re = ${Re}"
  echo "=========================================="
  echo "  Lid velocity: ${U} m/s"
  echo "  Max iters:    ${ITERS}"
  echo "  Output:       ${OUTPUT_DIR}/"
  echo "=========================================="
  
  start=$(date +%s)
  fluent 2ddp -g -t1 -i "run_Re_${Re}.jou" | tee "${OUTPUT_DIR}/console.log"
  end=$(date +%s)
  elapsed=$((end - start))
  
  echo "${elapsed}" > "${OUTPUT_DIR}/runtime.txt"
  
  TOTAL_ITERS=$(grep -oP 'iter\s+\K\d+' "${OUTPUT_DIR}/console.log" | tail -1)
  if [ ! -z "$TOTAL_ITERS" ] && [ "$TOTAL_ITERS" -gt 1 ]; then
    echo "✓ Completed: ${TOTAL_ITERS} iterations in ${elapsed}s"
  else
    echo "⚠ WARNING: Check console.log"
  fi
  
done

echo ""
echo "=========================================="
echo "ALL DONE! 🎉"
echo "=========================================="
echo "Results in: results/"