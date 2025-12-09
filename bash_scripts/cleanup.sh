#!/usr/bin/env bash
set -e

echo "=========================================="
echo "CLEANUP & RE-RUN SCRIPT"
echo "=========================================="
echo ""
echo "This will:"
echo "  1. Delete garbage results (no backup)"
echo "  2. Clean up old run files"
echo "  3. Re-run ALL simulations with proper convergence"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

# Delete old results
echo ""
echo "Deleting old results..."
if [ -d "results" ]; then
  rm -rf results
  echo "✓ Old results deleted"
fi

# Clean up old journal files
echo ""
echo "Cleaning up old journal files..."
rm -f run_*.jou
echo "✓ Old journal files removed"

# Clean up Fluent cleanup scripts
rm -f cleanup-fluent-*.bat
echo "✓ Fluent cleanup scripts removed"

echo ""
echo "=========================================="
echo "Starting fresh simulation batch..."
echo "=========================================="
echo ""
echo "IMPORTANT CHANGES:"
echo "  - Proper convergence criteria: 1e-6 (instead of default 1e-3)"
echo "  - Adaptive iterations:"
echo "    * Re < 100:    2,000 iterations"
echo "    * Re < 1000:   5,000 iterations"  
echo "    * Re >= 1000: 10,000 iterations"
echo "  - PNG visualizations will be saved"
echo ""
echo "Expected runtime: ~2-4 hours (much longer than before, but ACCURATE!)"
echo ""

# Run the batch
./run_batch.sh