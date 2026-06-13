#!/bin/bash
set -e

VERSION="${1:-0.3.1-Beta}"
PKG_DIR="${RUNNER_TEMP}/litepan"
DEB_NAME="litepan_${VERSION}_all.deb"

mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/litepan"
mkdir -p "$PKG_DIR/lib/systemd/system"

rsync -a --exclude=.git --exclude=.github --exclude=node_modules --exclude=build-deb.sh "$GITHUB_WORKSPACE/" "$PKG_DIR/opt/litepan/"

cat > "$PKG_DIR/DEBIAN/control" << EOF
Package: litepan
Version: ${VERSION}
Section: net
Priority: optional
Architecture: all
Depends: python3, python3-pip
Maintainer: LitePan Builder <build@litepan.local>
Description: LitePan - multi-cloud storage management tool
Homepage: https://github.com/jhf3324/LitePan
EOF

cat > "$PKG_DIR/DEBIAN/postinst" << 'POSTINSTEOF'
#!/bin/bash
set -e
cd /opt/litepan
pip3 install --no-cache-dir -r requirements.txt 2>&1 | tail -5
mkdir -p /opt/litepan/data /opt/litepan/log /opt/litepan/strm
systemctl daemon-reload
systemctl enable litepan.service
systemctl start litepan.service || true
POSTINSTEOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

cat > "$PKG_DIR/lib/systemd/system/litepan.service" << 'SERVICEEOF'
[Unit]
Description=LitePan - Multi-cloud drive aggregation tool
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory=/opt/litepan
ExecStart=/usr/bin/python3 /opt/litepan/main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
SERVICEEOF

dpkg-deb --build "$PKG_DIR" "$PKG_DIR/../$DEB_NAME"
echo "Built: $PKG_DIR/../$DEB_NAME"
