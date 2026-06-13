#!/usr/bin/env bash
#
# Dynamic V* — Label Studio public deployment
#
# Deploys Label Studio behind a Cloudflare Tunnel so annotators
# can access it from anywhere via HTTPS.
#
# Prerequisites:
#   1. Docker installed and running
#   2. cloudflared installed (https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
#   3. A Cloudflare account with a domain whose DNS is managed by Cloudflare
#   4. cloudflared already logged in:  cloudflared tunnel login
#   5. Python 3.10+ (for image upload and annotation parsing)
#   6. This repo cloned
#
# Usage:
#   # First time — creates tunnel and DNS record:
#   bash scripts/start_labelstudio_public.sh --domain label.yourdomain.com
#
#   # Subsequent runs — just starts everything:
#   bash scripts/start_labelstudio_public.sh --domain label.yourdomain.com
#
# Default credentials:
#   Email:    admin@vstar.local
#   Password: vstar2026
#   Change the password after first login.
#

set -e

# ── Parse args ──
DOMAIN=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain) DOMAIN="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [[ -z "$DOMAIN" ]]; then
    echo "Usage: bash scripts/start_labelstudio_public.sh --domain label.yourdomain.com"
    exit 1
fi

CONTAINER_NAME="labelstudio"
PORT=8080
DATA_DIR="$PWD/ls-data"
IMAGE="heartexlabs/label-studio:latest"
ADMIN_EMAIL="admin@vstar.local"
ADMIN_PASSWORD="vstar2026"
TUNNEL_NAME="vstar-labelstudio"

# ── Check dependencies ──
for cmd in docker cloudflared curl; do
    if ! command -v $cmd &>/dev/null; then
        echo "ERROR: $cmd is not installed."
        exit 1
    fi
done

if ! docker info &>/dev/null; then
    echo "ERROR: Docker is not running."
    exit 1
fi

# ── Step 1: Start Label Studio container ──
echo "=== Step 1: Label Studio container ==="

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Already running."
elif docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Restarting stopped container..."
    docker start ${CONTAINER_NAME}
else
    echo "Starting Label Studio for the first time..."
    mkdir -p "${DATA_DIR}"
    docker run -d \
        --name ${CONTAINER_NAME} \
        --restart unless-stopped \
        -p 127.0.0.1:${PORT}:8080 \
        -v "${DATA_DIR}:/label-studio/data" \
        -e LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK=true \
        -e LABEL_STUDIO_USERNAME="${ADMIN_EMAIL}" \
        -e LABEL_STUDIO_PASSWORD="${ADMIN_PASSWORD}" \
        -e CSRF_TRUSTED_ORIGINS="https://${DOMAIN}" \
        -e LABEL_STUDIO_HOST="https://${DOMAIN}" \
        ${IMAGE}
fi

echo "Waiting for Label Studio..."
until curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}" 2>/dev/null | grep -q "200\|302"; do
    sleep 2
done
echo "Label Studio is up on port ${PORT}."
echo ""

# ── Step 2: Create or reuse Cloudflare Tunnel ──
echo "=== Step 2: Cloudflare Tunnel ==="

TUNNEL_ID=$(cloudflared tunnel list --output json 2>/dev/null | python3 -c "
import sys, json
tunnels = json.load(sys.stdin)
for t in tunnels:
    if t['name'] == '${TUNNEL_NAME}':
        print(t['id'])
        break
" 2>/dev/null || true)

if [[ -z "$TUNNEL_ID" ]]; then
    echo "Creating tunnel '${TUNNEL_NAME}'..."
    cloudflared tunnel create ${TUNNEL_NAME}
    TUNNEL_ID=$(cloudflared tunnel list --output json | python3 -c "
import sys, json
for t in json.load(sys.stdin):
    if t['name'] == '${TUNNEL_NAME}':
        print(t['id']); break
")
    echo "Tunnel created: ${TUNNEL_ID}"
else
    echo "Tunnel exists: ${TUNNEL_ID}"
fi
echo ""

# ── Step 3: Configure tunnel ──
echo "=== Step 3: Tunnel config ==="

CRED_FILE="$HOME/.cloudflared/${TUNNEL_ID}.json"
CONFIG_FILE="$HOME/.cloudflared/config.yml"

cat > "${CONFIG_FILE}" << EOF
tunnel: ${TUNNEL_NAME}
credentials-file: ${CRED_FILE}

ingress:
  - hostname: ${DOMAIN}
    service: http://localhost:${PORT}
  - service: http_status:404
EOF

echo "Written ${CONFIG_FILE}"
echo ""

# ── Step 4: DNS record ──
echo "=== Step 4: DNS ==="
echo "Adding CNAME ${DOMAIN} -> ${TUNNEL_ID}.cfargotunnel.com ..."
cloudflared tunnel route dns ${TUNNEL_NAME} ${DOMAIN} 2>/dev/null || true
echo ""

# ── Step 5: Start tunnel ──
echo "=== Step 5: Starting tunnel ==="
echo "Running cloudflared in background..."
nohup cloudflared tunnel run ${TUNNEL_NAME} > /tmp/cloudflared.log 2>&1 &
TUNNEL_PID=$!
sleep 3

if kill -0 ${TUNNEL_PID} 2>/dev/null; then
    echo "Tunnel is running (PID ${TUNNEL_PID})."
else
    echo "ERROR: Tunnel failed to start. Check /tmp/cloudflared.log"
    exit 1
fi

echo ""
echo "========================================="
echo "  Label Studio is live"
echo "  Public URL: https://${DOMAIN}"
echo "  Email:      ${ADMIN_EMAIL}"
echo "  Password:   ${ADMIN_PASSWORD}"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Open https://${DOMAIN} and log in"
echo ""
echo "  2. Upload V* images (if new project):"
echo "     python scripts/upload_vstar_to_labelstudio.py \\"
echo "       --ls-url https://${DOMAIN} \\"
echo "       --ls-token <your-API-token> \\"
echo "       --project-id 1 --limit 191"
echo ""
echo "  3. Invite annotators:"
echo "     - Go to Organization Settings (top-right menu)"
echo "     - Click 'Get Link' to generate an invite URL"
echo "     - Send the invite URL to annotators"
echo "     - They sign up via the link and can start annotating"
echo "     - To assign tasks: Project Settings > Members > add them"
echo ""
echo "Logs:"
echo "  Label Studio: docker logs -f ${CONTAINER_NAME}"
echo "  Tunnel:       tail -f /tmp/cloudflared.log"
echo ""
echo "To stop:"
echo "  kill ${TUNNEL_PID}          # stop tunnel"
echo "  docker stop ${CONTAINER_NAME}  # stop Label Studio"
