#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INSTALL_DIR="/opt/loggerpi-otterpi"
SERVICE_NAME="otterpi.observer.service"
SERVICE_FILE="$REPO_DIR/deploy/otterpi/$SERVICE_NAME"

echo "Installing OtterPi to $INSTALL_DIR"

install -d -o root -g root -m 0755 "$INSTALL_DIR"
install -d -o root -g root -m 0755 "$INSTALL_DIR/model"

OTTERPI_FILES=(
    otterpi.py
    otterpi_observer.py
    otterpi_store.py
)

for file in "${OTTERPI_FILES[@]}"; do
    install -o root -g root -m 0644 \
        "$REPO_DIR/src/loggerpi_otterpi/$file" \
        "$INSTALL_DIR/$file"
done

install -o root -g root -m 0644 \
    "$REPO_DIR/src/loggerpi_otterpi/model/__init__.py" \
    "$INSTALL_DIR/model/__init__.py"

install -o root -g root -m 0644 \
    "$REPO_DIR/src/loggerpi_otterpi/model/batch.py" \
    "$INSTALL_DIR/model/batch.py"

install -o root -g root -m 0644 \
    "$REPO_DIR/src/loggerpi_otterpi/model/measurement.py" \
    "$INSTALL_DIR/model/measurement.py"

install -d -o root -g root -m 0755 /etc/loggerpi-otterpi

if [ ! -f /etc/loggerpi-otterpi/otterpi.env ]; then
    install -o root -g root -m 0640 \
        "$REPO_DIR/deploy/otterpi/otterpi.env.example" \
        /etc/loggerpi-otterpi/otterpi.env

    echo
    echo "Created /etc/loggerpi-otterpi/otterpi.env"
    echo "Please review it before starting the service."
fi

install -o root -g root -m 0644 \
    "$SERVICE_FILE" \
    "/etc/systemd/system/$SERVICE_NAME"

install -d -o makki -g makki -m 0750 \
    /var/lib/loggerpi-otterpi

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

install -o root -g root -m 0755 \
    "$REPO_DIR/deploy/update.sh" \
    /usr/local/sbin/loggerpi-otterpi-update

echo
echo "OtterPi installation complete."
echo
echo "Check configuration:"
echo "  sudoedit /etc/loggerpi-otterpi/otterpi.env"
echo
echo "Start service:"
echo "  sudo systemctl restart $SERVICE_NAME"
echo
echo "Status:"
echo "  systemctl status $SERVICE_NAME --no-pager"
