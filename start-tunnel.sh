#!/bin/bash
# Starts the Streamlit app + Cloudflare tunnel and saves the shareable URL
# Usage: ./start-tunnel.sh

TUNNEL_LOG="/tmp/cloudflare-tunnel.log"
URL_FILE="/Users/grahamhnatiw/Local/esplanade-competitive-analysis/SHAREABLE_URL.txt"

# Kill any existing tunnel
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 1

# Ensure Streamlit is running
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8502 | grep -q 200; then
    echo "Starting Streamlit..."
    cd /Users/grahamhnatiw/Local
    python3 -m streamlit run competitive_analysis_app.py --server.headless true --server.port 8502 &
    sleep 4
fi

# Start tunnel and capture URL
echo "Starting Cloudflare tunnel..."
cloudflared tunnel --url http://localhost:8502 > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

# Wait for URL to appear in logs
for i in $(seq 1 15); do
    URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$TUNNEL_LOG" 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
        echo "$URL" > "$URL_FILE"
        echo ""
        echo "========================================="
        echo "  SHAREABLE LINK:"
        echo "  $URL"
        echo "========================================="
        echo ""
        echo "URL also saved to: $URL_FILE"
        echo "Tunnel PID: $TUNNEL_PID"
        echo "To stop: kill $TUNNEL_PID"
        exit 0
    fi
    sleep 1
done

echo "ERROR: Tunnel URL not found after 15 seconds. Check $TUNNEL_LOG"
exit 1
