#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        RESTARTING MyCodingMaster IDE                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Kill any running instances
echo "→ Stopping old instances..."
pkill -f "python.*main.py" 2>/dev/null
sleep 1

# Start fresh instance
echo "→ Starting new instance with updated UI..."
cd /mnt/d/Projects/mycodingmaster
python main.py &

echo "✓ Application started!"
echo ""
echo "You should now see:"
echo "  ✓ Terminal visible at bottom (not just header)"
echo "  ✓ AI Workspace with more space (400px default)"
echo "  ✓ Professional model badge (● AI Model-Name)"
echo "  ✓ Professional workspace badge (📁 Workspace)"
echo "  ✓ Larger window (1600×1000 default)"
echo "  ✓ Better proportions (18% / 55% / 27%)"
echo ""
