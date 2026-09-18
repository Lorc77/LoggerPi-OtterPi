#!/bin/bash
set -euo pipefail

REPO_URL="https://github.com/Lorc77/LoggerPi-OtterPi.git"
BRANCH="main"
ROLE="${1:-}"

case "$ROLE" in
    loggerpi)
        INSTALL_SCRIPT="deploy/loggerpi/install.sh"
        SERVICE_NAME="loggerpi.observer.service"
        ;;
    otterpi)
        INSTALL_SCRIPT="deploy/otterpi/install.sh"
        SERVICE_NAME="otterpi.observer.service"
        ;;
    *)
        echo "Usage: sudo $0 {loggerpi|otterpi}"
        exit 2
        ;;
esac

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root."
    exit 1
fi

TMP_DIR="$(mktemp -d /tmp/loggerpi-otterpi-update.XXXXXX)"

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "Fetching $REPO_URL ($BRANCH)..."
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TMP_DIR/repo"

REPO_DIR="$TMP_DIR/repo"
COMMIT="$(git -C "$REPO_DIR" rev-parse HEAD)"

echo "Deploying commit: $COMMIT"
echo

cd "$REPO_DIR"
"./$INSTALL_SCRIPT"

echo
echo "Restarting $SERVICE_NAME..."
systemctl restart "$SERVICE_NAME"

echo
echo "Checking $SERVICE_NAME..."
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    echo
    echo "ERROR: $SERVICE_NAME did not become active."
    systemctl status "$SERVICE_NAME" --no-pager || true
    exit 1
fi

printf '%s\n' "$COMMIT" > /opt/loggerpi-otterpi/DEPLOYED_COMMIT
chown root:root /opt/loggerpi-otterpi/DEPLOYED_COMMIT
chmod 0644 /opt/loggerpi-otterpi/DEPLOYED_COMMIT

echo
echo "Deployment successful."
echo "Commit:  $COMMIT"
echo "Service: $SERVICE_NAME"
echo
systemctl status "$SERVICE_NAME" --no-pager
