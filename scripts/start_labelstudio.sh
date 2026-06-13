#!/usr/bin/env bash
#
# Dynamic V* — Label Studio quick start
#
# Prerequisites:
#   1. Docker Desktop installed and running
#   2. Python 3.10+ (for image upload and annotation parsing)
#   3. This repo cloned: git clone https://github.com/Xxxxxsun/rekey-vstar.git
#
# Usage:
#   cd rekey-vstar
#   bash scripts/start_labelstudio.sh
#   bash scripts/start_labelstudio.sh --domain your-tunnel-domain.trycloudflare.com
#
# After startup:
#   - Local access: http://127.0.0.1:8080
#   - If --domain is set, also accessible via that domain (you still
#     need to run cloudflared or similar tunnel yourself)
#
# Default credentials:
#   Email:    admin@vstar.local
#   Password: vstar2026
#   Change the password after first login.
#

set -e

CONTAINER_NAME="labelstudio"
PORT=8080
DATA_DIR="$PWD/ls-data"
IMAGE="heartexlabs/label-studio:latest"
ADMIN_EMAIL="admin@vstar.local"
ADMIN_PASSWORD="vstar2026"
DOMAIN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --domain) DOMAIN="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# ── Check Docker ──
if ! command -v docker &>/dev/null; then
    echo "ERROR: docker is not installed. Please install Docker Desktop first."
    exit 1
fi

if ! docker info &>/dev/null; then
    echo "ERROR: Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# ── Already running ──
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Label Studio is already running at http://127.0.0.1:${PORT}"
    echo "  Stop:  docker stop ${CONTAINER_NAME}"
    echo "  Logs:  docker logs -f ${CONTAINER_NAME}"
    exit 0
fi

# ── Restart stopped container ──
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Restarting stopped container..."
    docker start ${CONTAINER_NAME}
    echo "Label Studio is up at http://127.0.0.1:${PORT}"
    exit 0
fi

# ── First run ──
echo "Starting Label Studio for the first time..."
echo "  Data dir: ${DATA_DIR}"
echo "  Port:     ${PORT}"
echo "  Account:  ${ADMIN_EMAIL} / ${ADMIN_PASSWORD}"
if [[ -n "$DOMAIN" ]]; then
    echo "  Domain:   ${DOMAIN}"
fi
echo ""

mkdir -p "${DATA_DIR}"

CSRF_ARGS=()
if [[ -n "$DOMAIN" ]]; then
    CSRF_ARGS+=(-e "CSRF_TRUSTED_ORIGINS=https://${DOMAIN}")
    CSRF_ARGS+=(-e "LABEL_STUDIO_HOST=https://${DOMAIN}")
fi

docker run -d \
    --name ${CONTAINER_NAME} \
    --restart unless-stopped \
    -p 127.0.0.1:${PORT}:8080 \
    -v "${DATA_DIR}:/label-studio/data" \
    -e LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK=true \
    -e LABEL_STUDIO_USERNAME="${ADMIN_EMAIL}" \
    -e LABEL_STUDIO_PASSWORD="${ADMIN_PASSWORD}" \
    "${CSRF_ARGS[@]}" \
    ${IMAGE}

echo ""
echo "Waiting for Label Studio to start..."
until curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}" 2>/dev/null | grep -q "200\|302"; do
    sleep 2
done

echo ""
echo "========================================="
echo "  Label Studio is ready"
echo "  URL:      http://127.0.0.1:${PORT}"
if [[ -n "$DOMAIN" ]]; then
echo "  Public:   https://${DOMAIN}"
fi
echo "  Email:    ${ADMIN_EMAIL}"
echo "  Password: ${ADMIN_PASSWORD}"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Open http://127.0.0.1:${PORT} in your browser and log in"
echo ""
echo "  2. Upload V* images (if new project):"
echo "     python scripts/upload_vstar_to_labelstudio.py \\"
echo "       --ls-url http://127.0.0.1:${PORT} \\"
echo "       --ls-token <your-API-token> \\"
echo "       --project-id 1 --limit 191"
echo ""
echo "  3. Invite annotators:"
echo "     - Go to Organization Settings (top-right menu)"
echo "     - Click 'Get Link' to generate an invite URL"
echo "     - Send the invite URL to annotators"
echo "     - They sign up via the link and can start annotating"
echo "     - To assign tasks: Project Settings > Members > add them"
