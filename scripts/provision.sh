#!/usr/bin/env bash
set -euo pipefail

ROLE="${1:-}"
V="1.8.2"
ARCH="$(dpkg --print-architecture)"   # amd64 ou arm64

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y curl stress-ng
 
 
# --- Node Exporter (toutes les VMs) ---
if ! id node_exporter &>/dev/null; then
  useradd --no-create-home --shell /usr/sbin/nologin node_exporter
fi

if [ ! -x /usr/local/bin/node_exporter ]; then
  cd /tmp
  curl -sLO "https://github.com/prometheus/node_exporter/releases/download/v${V}/node_exporter-${V}.linux-${ARCH}.tar.gz"
  tar xzf "node_exporter-${V}.linux-${ARCH}.tar.gz"
  install -m 0755 "node_exporter-${V}.linux-${ARCH}/node_exporter" /usr/local/bin/node_exporter
fi

cat > /etc/systemd/system/node_exporter.service <<'UNIT'
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now node_exporter

# --- Service selon le rôle ---
case "$ROLE" in
  web01)
    apt-get install -y nginx
    systemctl enable --now nginx
    ;;
  db01)
    apt-get install -y mariadb-server
    systemctl enable --now mariadb
    ;;
esac

echo "Provisioning of ${ROLE} done."
