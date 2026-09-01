# Z13 Power

Omarchy bar plugin for the **2025 ASUS ROG Flow Z13 (GZ302)**. A battery
flyout with live charge, watts, and temp, plus Max / Perf / Mid / Quiet / Low,
Automatic, Lock, and a one-shot charge-to-100%. A background service handles
low-battery warnings without calling Omarchy’s `powerprofiles-set`.

This is a `bar-widget` with a nested details panel (same shape as stock
`omarchy.power`) plus a `service`. Profile apply goes through
[z13-power](https://github.com/randallyash/rog-z13-power-management); without
that backend the glyph still shows charge, and the pills will not drive TDP.

## Install

1. Install **z13-power** and **z13ctl-bin** from the table above (GZ302 only).
2. Then add this widget:

```sh
omarchy plugin add https://github.com/randallyash/omarchy-z13-power.git --enable
```

That clones and enables the plugin. It does not rewrite your bar and does not
install the backend.

## Usage

Click the battery glyph to open or close the flyout. Press Escape to close it.
Pills apply Max / Perf / Mid / Quiet / Low. Automatic follows AC, battery, and
low battery. Lock keeps a manual pick across plug/unplug.

## Configure

Put it in the right-hand (battery) slot:

```sh
omarchy bar move io.github.randallyash.z13-power --section right
```

This is a **manual-setup** plugin. `omarchy plugin add` only installs the
bar widget. Profile apply, TDP, and charge cap come from a separately
installed backend:

| Dependency | Provenance | Install |
|---|---|---|
| **z13-power** | https://github.com/randallyash/rog-z13-power-management (GPL-3.0-or-later) | clone that repo, then `cd packaging/arch/z13-power-git && makepkg -si`, or `./install.sh` |
| **z13ctl-bin** | AUR, upstream https://github.com/dahui/z13ctl | `paru -S z13ctl-bin` (required by z13-power, not by this widget itself) |

Both land as `/usr/bin/z13-power` (package) or `~/.local/bin/z13-power` (from-source). This plugin never downloads them; `z13-io.py` only opens those two fixed paths after `O_NOFOLLOW` + regular-file checks.

## Remove

```sh
omarchy plugin remove io.github.randallyash.z13-power
```

That takes the plugin away and nothing else. Config under `~/.config/z13-power/`
is left alone on purpose.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
