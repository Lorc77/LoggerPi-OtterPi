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

# Setze Ausführbarkeit für install.sh-Dateien
chmod +x "$TMP_DIR/repo/deploy/loggerpi/install.sh"
chmod +x "$TMP_DIR/repo/deploy/otterpi/install.sh"

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

# Speichere Commit (für technische Debugging)
printf '%s\n' "$COMMIT" > /opt/loggerpi-otterpi/DEPLOYED_COMMIT

# Speichere Version (für Menschenlesbarkeit)
VERSION=$(git -C "$REPO_DIR" describe --tags --exact-match 2>/dev/null || echo "dev")
printf '%s\n' "$VERSION" > /opt/loggerpi-otterpi/DEPLOYED_VERSION

chown root:root /opt/loggerpi-otterpi/DEPLOYED_COMMIT /opt/loggerpi-otterpi/DEPLOYED_VERSION
chmod 0644 /opt/loggerpi-otterpi/DEPLOYED_COMMIT /opt/loggerpi-otterpi/DEPLOYED_VERSION

echo
echo "Deployment successful."
echo "Commit:  $COMMIT"
echo "Version: $VERSION"
echo "Service: $SERVICE_NAME"
echo
systemctl status "$SERVICE_NAME" --no-pager
