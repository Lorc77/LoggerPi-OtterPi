#!/bin/bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INSTALL_DIR="/opt/loggerpi-otterpi"
SERVICE_NAME="loggerpi.observer.service"
SERVICE_FILE="$REPO_DIR/deploy/loggerpi/$SERVICE_NAME"

echo "Installing LoggerPi to $INSTALL_DIR"

install -d -o root -g root -m 0755 "$INSTALL_DIR"
install -d -o root -g root -m 0755 "$INSTALL_DIR/model"

LOGGERPI_FILES=(
    atmoweb.py
    atmoweb_config.py
    batch_factory.py
    composer.py
    delivery.py
    loggerpi_observer.py
    loggerpi_runner.py
    queue.py
    runtime.py
    system_info.py
)

for file in "${LOGGERPI_FILES[@]}"; do
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

if [ ! -f /etc/loggerpi-otterpi/loggerpi.env ]; then
    install -o root -g root -m 0640 \
        "$REPO_DIR/deploy/loggerpi/loggerpi.env.example" \
        /etc/loggerpi-otterpi/loggerpi.env

    echo
    echo "Created /etc/loggerpi-otterpi/loggerpi.env"
    echo "Please review it before starting the service."
fi

install -o root -g root -m 0644 \
    "$SERVICE_FILE" \
    "/etc/systemd/system/$SERVICE_NAME"

install -d -o ZOOLOGY-observ -g ZOOLOGY-observ -m 0750 \
    /var/lib/loggerpi-otterpi

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

install -o root -g root -m 0755 \
    "$REPO_DIR/deploy/update.sh" \
    /usr/local/sbin/loggerpi-otterpi-update

echo
echo "LoggerPi installation complete."
echo
echo "Check configuration:"
echo "  sudoedit /etc/loggerpi-otterpi/loggerpi.env"
echo
echo "Start service:"
echo "  sudo systemctl restart $SERVICE_NAME"
echo
echo "Status:"
echo "  systemctl status $SERVICE_NAME --no-pager"
