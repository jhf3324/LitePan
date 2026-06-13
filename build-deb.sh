#!/bin/bash
set -e

VERSION="${1:-0.3.1-Beta}"
PKG_DIR="${RUNNER_TEMP}/litepan"
DEB_NAME="litepan_${VERSION}_all.deb"

# === Create package structure ===
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/opt/litepan"
mkdir -p "$PKG_DIR/lib/systemd/system"
mkdir -p "$PKG_DIR/opt/litepan/_deps"

# === Copy source code (exclude git stuff) ===
rsync -a --exclude=.git --exclude=.github --exclude=node_modules --exclude=build-deb.sh "$GITHUB_WORKSPACE/" "$PKG_DIR/opt/litepan/"

# === Download ARM wheels on x86_64 (no QEMU!) ===
echo "[Build] Downloading ARM wheels for armhf..."
pip3 install --upgrade pip -q
cd "$PKG_DIR/opt/litepan/_deps"
# Download all ARM-compatible wheels
pip3 download --platform linux_armv7l --python-version 3.11 --only-binary=:all: -r ../requirements.txt
# Extract all wheels
for w in *.whl; do
  echo "  Extracting: $w"
  unzip -qo "$w" && rm -f "$w"
done
cd "$OLDPWD"

# === control ===
cat > "$PKG_DIR/DEBIAN/control" << CONTROLEOF
Package: litepan
Version: ${VERSION}
Section: net
Priority: optional
Architecture: all
Depends: python3
Maintainer: LitePan Builder <build@litepan.local>
Description: LitePan - multi-cloud storage management tool
Homepage: https://github.com/jhf3324/LitePan
CONTROLEOF

# === postinst (no pip needed!) ===
cat > "$PKG_DIR/DEBIAN/postinst" << 'POSTINSTEOF'
#!/bin/bash
set -e
mkdir -p /opt/litepan/data /opt/litepan/log /opt/litepan/strm
systemctl daemon-reload
systemctl enable litepan.service
systemctl start litepan.service || true
echo ""
echo "============================================"
echo "  LitePan 安装完成!"
echo "  访问 http://$(hostname -I | awk '{print $1}'):5211"
echo "  默认账号: admin / admin"
echo "============================================"
POSTINSTEOF
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# === systemd service ===
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
Environment=PYTHONPATH=/opt/litepan/_deps

[Install]
WantedBy=multi-user.target
SERVICEEOF

# === Build .deb ===
dpkg-deb --build "$PKG_DIR" "$PKG_DIR/../$DEB_NAME"
echo "Built: $PKG_DIR/../$DEB_NAME"
echo "Size: $(du -sh $PKG_DIR/../$DEB_NAME | cut -f1)"
