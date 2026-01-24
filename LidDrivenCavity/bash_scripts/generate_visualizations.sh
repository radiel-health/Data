#!/bin/bash

#==============================================================================
# SELECTIVE POST-PROCESSING VISUALIZATION SCRIPT
# Generates contour plots for REPRESENTATIVE cases only
# 3 Reynolds numbers per aspect ratio: Low, Medium, High
#==============================================================================

echo "=============================================="
echo "SELECTIVE VISUALIZATION POST-PROCESSING"
echo "=============================================="
echo ""

# Check if visualize_template.jou exists
if [ ! -f "visualize_template.jou" ]; then
  echo "ERROR: visualize_template.jou not found!"
  echo "Please place visualize_template.jou in the current directory."
  exit 1
fi

# Define aspect ratios
ASPECT_RATIOS=(1.1 1.2 1.3 1.4 1.5 1.6 1.7 1.8 1.9)

# Define REPRESENTATIVE Reynolds numbers (low, medium, high)
# You can customize these!
RE_LOW=100
RE_MED=1000
RE_HIGH=2000

REPRESENTATIVE_RES=($RE_LOW $RE_MED $RE_HIGH)

echo "Generating visualizations for representative cases:"
echo "  Reynolds numbers: ${REPRESENTATIVE_RES[@]}"
echo "  Aspect ratios: ${ASPECT_RATIOS[@]}"
echo ""
echo "Total cases to visualize: 9 ARs × 3 Re = 27 cases"
echo "Total images: 27 × 6 plots = 162 images"
echo ""

# Counter
COUNT=0
TOTAL_CASES=$((${#ASPECT_RATIOS[@]} * ${#REPRESENTATIVE_RES[@]}))

# Loop through aspect ratios and representative Re values
for AR in "${ASPECT_RATIOS[@]}"; do
  echo "----------------------------------------------"
  echo "Aspect Ratio: ${AR}:1"
  echo "----------------------------------------------"
  
  for Re in "${REPRESENTATIVE_RES[@]}"; do
    COUNT=$((COUNT + 1))
    
    # Define paths
    CASE_DIR="results/AR_${AR}x1/Re_${Re}"
    CASE_FILE="${CASE_DIR}/cavity_Re_${Re}.cas.h5"
    
    # Check if case exists
    if [ ! -f "$CASE_FILE" ]; then
      echo "  ⚠ Case $COUNT/$TOTAL_CASES (Re=$Re): Case file not found - skipping"
      continue
    fi
    
    # Check if visualizations already exist
    VIZ_CHECK="$CASE_DIR/contour_velocity_magnitude.png"
    if [ -f "$VIZ_CHECK" ]; then
      echo "  ✓ Case $COUNT/$TOTAL_CASES (Re=$Re): Visualizations already exist - skipping"
      continue
    fi
    
    echo "  → Case $COUNT/$TOTAL_CASES (Re=$Re): Generating visualizations..."
    
    # Create temporary journal file with correct paths
    TEMP_JOU="$CASE_DIR/visualize_temp.jou"
    sed -e "s|CASE_FILE|${CASE_FILE}|g" \
        -e "s|OUTPUT_DIR|${CASE_DIR}|g" \
        visualize_template.jou > "$TEMP_JOU"
    
    # Run Fluent in batch mode to generate visualizations
    fluent 2d -g -i "$TEMP_JOU" > "$CASE_DIR/visualization.log" 2>&1
    
    # Check if visualizations were created
    if [ -f "$VIZ_CHECK" ]; then
      echo "  ✓ Case $COUNT/$TOTAL_CASES (Re=$Re): Successfully created visualizations"
      rm "$TEMP_JOU"
    else
      echo "  ✗ Case $COUNT/$TOTAL_CASES (Re=$Re): Warning - visualizations may have failed"
      echo "     Check: $CASE_DIR/visualization.log"
    fi
    
  done
  echo ""
done

echo "=============================================="
echo "VISUALIZATION COMPLETE!"
echo "=============================================="
echo ""
echo "Summary:"
echo "  Aspect ratios processed: ${#ASPECT_RATIOS[@]}"
echo "  Reynolds per AR: ${#REPRESENTATIVE_RES[@]} (${REPRESENTATIVE_RES[@]})"
echo "  Total cases visualized: $TOTAL_CASES"
echo "  Total images: ~$((TOTAL_CASES * 6))"
echo ""
echo "Visualizations saved to:"
echo "  results/AR_X.Xx1/Re_YYY/*.png"
echo ""
echo "To view results:"
echo "  cd results/AR_1.5x1/Re_1000"
echo "  ls *.png"
echo ""