#!/bin/bash
# Install the z13-power backend this plugin talks to.
# One command after `omarchy plugin add`. It does not install z13ctl, and it
# does not copy a second plugin over this one.
set -euo pipefail

PIN=f1f47f7e6b6aa7dd16923e241afef1447eda81d5
REPO=https://github.com/randallyash/rog-z13-power-management.git
SHARE=/usr/share/z13-power-management
MIN="z13-power 1.2"

say() { printf '%s\n' "$*"; }
die() { printf 'setup: %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -ne 0 ]] || die "run this as your desktop user, not root. It will ask for sudo."

installed="$(
  "$SHARE/z13-power" --version 2>/dev/null || true
)"
if [[ "$installed" == "$MIN"* ]]; then
  say "Backend already installed: $installed"
  say "z13ctl is not used."
  exit 0
fi

say "Z13 Power needs its backend before the pills can change watts."
say "This will:"
say "  - download rog-z13-power-management at $PIN"
say "  - install that tree under $SHARE and link /usr/bin/z13-power"
say "  - install the armoury udev rule and start z13-power-service"
say "  - install python-pyqt6, python-pyudev, python-dbus-next, and libnotify if they are missing"
say "It will not install z13ctl, and it will not replace this plugin."
say "Quiet is 20 W and Low is 15 W once ryzen_smu is loaded. That module is a separate package."
say
printf 'Type yes to continue: '
read -r answer
[[ "$answer" == "yes" ]] || die "cancelled"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git -C "$tmp" init -q
git -C "$tmp" remote add origin "$REPO"
git -C "$tmp" fetch --depth 1 origin "$PIN"
git -C "$tmp" checkout --detach FETCH_HEAD
got="$(git -C "$tmp" rev-parse HEAD)"
[[ "$got" == "$PIN" ]] || die "checkout was $got, wanted $PIN"
[[ -f "$tmp/service/z13_power_hw.py" && -f "$tmp/scripts/z13-power" ]] || die "downloaded tree is incomplete"

cat >"$tmp/install-root.sh" <<'EOF'
#!/bin/bash
set -euo pipefail
src="${1:?}"
share=/usr/share/z13-power-management
install -d "$share/contrib/ryzen-smu" /usr/bin /usr/lib/systemd/user /usr/lib/udev/rules.d
install -m755 "$src/scripts/z13-power" "$share/z13-power"
install -m755 "$src/service/z13-power-service" "$share/z13-power-service"
install -m755 "$src/service/z13-power-settings" "$share/z13-power-settings"
install -m755 "$src/service/z13-power-overlay" "$share/z13-power-overlay"
install -m755 "$src/contrib/z13-power-config" "$share/z13-power-config"
install -m644 "$src/service/z13_power_theme.py" "$share/z13_power_theme.py"
install -m644 "$src/service/z13_power_common.py" "$share/z13_power_common.py"
install -m644 "$src/service/z13_power_hw.py" "$share/z13_power_hw.py"
install -m644 "$src/service/z13_power_io.py" "$share/z13_power_io.py"
install -m644 "$src/kde/powerdevilrc" "$share/powerdevilrc"
install -m644 "$src/service/z13-power-service.service" /usr/lib/systemd/user/z13-power-service.service
install -Dm644 "$src/contrib/ryzen-smu/99-ryzen-smu.rules" "$share/contrib/ryzen-smu/99-ryzen-smu.rules"
install -Dm644 "$src/contrib/ryzen-smu/ryzen_smu.conf" "$share/contrib/ryzen-smu/ryzen_smu.conf"
install -Dm644 "$src/contrib/udev/99-z13-power-armoury-ppt.rules" /usr/lib/udev/rules.d/99-z13-power-armoury-ppt.rules
ln -sfn "$share/z13-power" /usr/bin/z13-power
ln -sfn "$share/z13-power-service" /usr/bin/z13-power-service
ln -sfn "$share/z13-power-settings" /usr/bin/z13-power-settings
ln -sfn "$share/z13-power-overlay" /usr/bin/z13-power-overlay
ln -sfn "$share/z13-power-config" /usr/bin/z13-power-config
pacman -S --needed python-pyqt6 python-pyudev python-dbus-next libnotify
udevadm control --reload-rules || true
for a in ppt_pl1_spl ppt_pl2_sppt ppt_pl3_fppt; do
  f="/sys/class/firmware-attributes/asus-armoury/attributes/$a/current_value"
  [[ -e "$f" ]] || continue
  chgrp users "$f" || true
  chmod g+w "$f" || true
done
EOF
chmod 700 "$tmp/install-root.sh"
sudo bash "$tmp/install-root.sh" "$tmp"

ver="$("$SHARE/z13-power" --version)"
[[ "$ver" == "$MIN"* ]] || die "installed $ver, wanted $MIN or newer"

systemctl --user daemon-reload
systemctl --user enable --now z13-power-service.service
systemctl --user mask --now z13ctl.socket z13ctl.service >/dev/null 2>&1 || true

say
say "Installed $ver"
say "z13ctl is not used."
if ! grep -qw ryzen_smu_drv /proc/modules 2>/dev/null; then
  say "ryzen_smu is not loaded, so 20 W Quiet and 15 W Low cannot hold yet."
  say "When you want that module: z13-power setup-undervolt"
fi
say "Open the battery flyout again. The pills should be live."
