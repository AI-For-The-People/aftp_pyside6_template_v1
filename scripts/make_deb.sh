#!/usr/bin/env bash
set -euo pipefail
# Make a simple .deb using fpm or dpkg-deb. This packages the source + runner script.
# For a single-file binary, build with Nuitka first, then package that file instead.

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
proj="$(cd "$here/.." && pwd)"
pkgroot="$proj/build/debian/aftp-template"
bindir="$pkgroot/usr/bin"
appdir="$pkgroot/opt/aftp-template"

rm -rf "$pkgroot"; mkdir -p "$bindir" "$appdir"

# Copy app sources
rsync -a --exclude '__pycache__' --exclude 'venvs' "$proj/app" "$appdir/"
cp "$proj/requirements.txt" "$appdir/"
cat > "$bindir/aftp-template" <<'SH'
#!/usr/bin/env bash
set -e
cd /opt/aftp-template
# Expect a system Python with PySide6 or ship a venv here
exec python3 -m app
SH
chmod +x "$bindir/aftp-template"

# Minimal control files via dpkg-deb
control="$pkgroot/DEBIAN/control"
mkdir -p "$(dirname "$control")"
cat > "$control" <<'CTRL'
Package: aftp-template
Version: 0.1.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: AI For The People <noreply@example.com>
Description: AI For The People — PySide6 template app
CTRL

dpkg-deb --build "$pkgroot" "$proj/build/aftp-template_0.1.0_amd64.deb"
echo "[AFTP] Created $proj/build/aftp-template_0.1.0_amd64.deb"
