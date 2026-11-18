#!/usr/bin/env bash
# Serve your radar locally with the official BYOR Docker image, with your own quadrant/ring names.
# Usage: scripts/serve_local.sh [path/to/radar-state.json] [port]
# Security: binds to 127.0.0.1 only (not your LAN). Pin the image for repeatable, reviewed deployments:
#   BYOR_IMAGE=wwwthoughtworks/build-your-own-radar@sha256:<digest> scripts/serve_local.sh
set -euo pipefail
STATE="${1:-radar-state.json}"; PORT="${2:-8080}"
IMAGE="${BYOR_IMAGE:-wwwthoughtworks/build-your-own-radar:latest}"
[[ "$PORT" =~ ^[0-9]{2,5}$ ]] || { echo "Port must be a number"; exit 1; }
DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$(cd "$(dirname "$STATE")" && pwd)/radar-output"
command -v docker >/dev/null || { echo "Docker is required: https://docs.docker.com/get-docker/"; exit 1; }
[ -f "$OUT/radar.csv" ] || python3 "$DIR/state_to_radar.py" "$STATE"
RINGS="$(python3 "$DIR/state_to_radar.py" "$STATE" --print-rings-json)"
QUADRANTS="$(python3 "$DIR/state_to_radar.py" "$STATE" --print-quadrants-json)"
echo "Open http://localhost:${PORT} and enter this URL in the box:  http://localhost:${PORT}/files/radar.csv"
docker run --rm -p "127.0.0.1:${PORT}:80" \
  -e SERVER_NAMES="localhost 127.0.0.1" \
  -e RINGS="$RINGS" -e QUADRANTS="$QUADRANTS" \
  -v "$OUT":/opt/build-your-own-radar/files:ro \
  "$IMAGE"
