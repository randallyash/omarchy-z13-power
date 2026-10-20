#!/bin/bash
# Install the z13-power backend this plugin talks to.
# One command after `omarchy plugin add`. It does not install z13ctl, and it
# does not copy a second plugin over this one.
set -euo pipefail

REPO=https://github.com/randallyash/rog-z13-power-management.git
SHARE=/usr/share/z13-power-management
MIN="z13-power 1.4"

say() { printf '%s\n' "$*"; }
die() { printf 'setup: %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -ne 0 ]] || die "run this as your desktop user, not root. It will ask for sudo."

installed="$(
  "$SHARE/z13-power" --version 2>/dev/null || true
)"
rule=/etc/udev/rules.d/99-ryzen-smu.rules
open_mailbox=0
if [[ -f "$rule" ]] && grep -q 'a+w' "$rule"; then
  open_mailbox=1
fi
if [[ "$installed" == "$MIN"* && "$open_mailbox" == 0 ]]; then
  say "Backend already installed: $installed"
  say "z13ctl is not used."
  exit 0
fi

say "Z13 Power needs its backend before the pills can change watts."
say "This will:"
say "  - download rog-z13-power-management at 9e3ce9f1e895a8d7dddff8a34d41d9531096400c"
say "  - install that tree under $SHARE and link /usr/bin/z13-power"
say "  - install the armoury udev rule, lock the SMU mailbox to root, and start z13-power-service"
say "  - install python-pyqt6, python-pyudev, python-dbus-next, and libnotify if they are missing"
say "It will not install z13ctl, and it will not replace this plugin."
say "Quiet uses the firmware quiet profile. It does not pin the SMU."
say
printf 'Type yes to continue: '
read -r answer
[[ "$answer" == "yes" ]] || die "cancelled"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git -C "$tmp" init -q
git -C "$tmp" remote add origin "$REPO"
git -C "$tmp" fetch --depth 1 origin 9e3ce9f1e895a8d7dddff8a34d41d9531096400c
git -C "$tmp" checkout --detach 9e3ce9f1e895a8d7dddff8a34d41d9531096400c
got="$(git -C "$tmp" rev-parse HEAD)"
[[ "$got" == "9e3ce9f1e895a8d7dddff8a34d41d9531096400c" ]] || die "checkout was $got"
[[ -f "$tmp/service/z13_power_hw.py" && -f "$tmp/scripts/z13-power" ]] || die "downloaded tree is incomplete"

# Copy reviewed files into /usr. Do not execute anything from the checkout.
sudo bash -c '
set -euo pipefail
src="${1:?}"
share=/usr/share/z13-power-management
install -d "$share/contrib/ryzen-smu" /usr/bin /usr/lib/z13-power /usr/lib/systemd/user /usr/lib/systemd/system /usr/lib/udev/rules.d
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
install -Dm644 "$src/contrib/ryzen-smu/99-ryzen-smu.rules" /etc/udev/rules.d/99-ryzen-smu.rules
install -Dm644 "$src/contrib/ryzen-smu/99-ryzen-smu.rules" /usr/lib/udev/rules.d/99-ryzen-smu.rules
install -m755 "$src/contrib/ryzen-smu/lock-smu-sysfs" /usr/lib/z13-power/lock-smu-sysfs
install -m755 "$src/contrib/ryzen-smu/lock-smu-sysfs" "$share/contrib/ryzen-smu/lock-smu-sysfs"
install -m755 "$src/service/z13-power-smu" /usr/lib/z13-power/z13-power-smu
install -m644 "$src/service/z13-power-smu.socket" /usr/lib/systemd/system/z13-power-smu.socket
install -m644 "$src/service/z13-power-smu@.service" /usr/lib/systemd/system/z13-power-smu@.service
install -Dm644 "$src/contrib/ryzen-smu/ryzen_smu.conf" "$share/contrib/ryzen-smu/ryzen_smu.conf"
install -Dm644 "$src/contrib/udev/99-z13-power-armoury-ppt.rules" /usr/lib/udev/rules.d/99-z13-power-armoury-ppt.rules
ln -sfn "$share/z13-power" /usr/bin/z13-power
ln -sfn "$share/z13-power-service" /usr/bin/z13-power-service
ln -sfn "$share/z13-power-settings" /usr/bin/z13-power-settings
ln -sfn "$share/z13-power-overlay" /usr/bin/z13-power-overlay
ln -sfn "$share/z13-power-config" /usr/bin/z13-power-config
pacman -S --needed python-pyqt6 python-pyudev python-dbus-next libnotify
udevadm control --reload-rules || true
getent group z13-power >/dev/null || groupadd --system z13-power
if [[ -n "${2:-}" && "${2}" != root ]]; then
  usermod -aG z13-power "${2}"
fi
install -m755 "$src/contrib/z13-power/lock-power-sysfs" /usr/lib/z13-power/lock-power-sysfs
install -Dm644 "$src/contrib/udev/99-z13power-access.rules" /etc/udev/rules.d/99-z13power-access.rules
install -Dm644 "$src/contrib/udev/99-z13power-access.rules" /usr/lib/udev/rules.d/99-z13power-access.rules
install -m644 "$src/service/z13-power-perms.service" /usr/lib/systemd/system/z13-power-perms.service
/usr/lib/z13-power/lock-power-sysfs "${2:-}"
systemctl daemon-reload
systemctl enable --now z13-power-smu.socket
systemctl enable --now z13-power-perms.service
if [[ -f /etc/systemd/system/z13ctl-perms.service && ! -L /etc/systemd/system/z13ctl-perms.service ]]; then
  systemctl disable --now z13ctl-perms.service >/dev/null 2>&1 || true
  rm -f /etc/systemd/system/z13ctl-perms.service
fi
systemctl mask --now z13ctl-perms.service >/dev/null 2>&1 || true
' bash "$tmp" "$USER"

ver="$("$SHARE/z13-power" --version)"
[[ "$ver" == "$MIN"* ]] || die "installed $ver, wanted $MIN or newer"

systemctl --user daemon-reload
systemctl --user enable --now z13-power-service.service
systemctl --user mask --now z13ctl.socket z13ctl.service >/dev/null 2>&1 || true

say
say "Installed $ver"
say "z13ctl is not used."
if ! grep -qw ryzen_smu_drv /proc/modules 2>/dev/null; then
  say "ryzen_smu is not loaded. Quiet does not need it."
  say "When you want curve optimizer: z13-power setup-undervolt"
fi
say "Open the battery flyout again. The pills should be live."
