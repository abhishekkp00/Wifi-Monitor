#!/bin/bash
# scripts/share_public_link.sh

PORT=5001

echo "=========================================================="
echo "⚡ Starting public HTTPS tunnel to share your dashboard..."
echo "=========================================================="
echo ""
echo "Press Ctrl+C to close the public link and stop the tunnel."
echo ""

# Connect to localhost.run
ssh -o StrictHostKeyChecking=no -R 80:localhost:$PORT nokey@localhost.run
