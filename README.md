# Z13 Power

Omarchy bar plugin for the **2025 ASUS ROG Flow Z13 (GZ302)**. It takes the
battery slot: live charge, watts, temp, and the Max / Perf / Mid / Quiet / Low
pills, plus Automatic, Lock, and a one-shot charge-to-100%. A background
service handles low-battery warnings without calling Omarchy’s
`powerprofiles-set`.

The flyout talks to [z13-power](https://github.com/randallyash/rog-z13-power-management).
Install that backend first or the pills have nothing to drive.

## Install

```bash
# 1. Backend (TDP, profiles, tray, settings)
git clone https://github.com/randallyash/rog-z13-power-management.git
cd rog-z13-power-management
paru -S z13ctl-bin
cd packaging/arch/z13-power-git && makepkg -si

# 2. This plugin
omarchy plugin add https://github.com/randallyash/omarchy-z13-power.git --enable
```

`omarchy plugin add` clones and enables the plugin. It does not rewrite your
bar. To put it in the battery slot (replacing stock `omarchy.power` there
only):

```bash
z13-power-omarchy-setup
omarchy restart shell
```

That setup command is explicit and idempotent. It does not touch the rest of
your layout.

## Remove

```bash
omarchy plugin remove z13.power
```

If the setup script had pointed the battery slot at `z13.power`, put the stock
widget back:

```bash
omarchy refresh shell
```

or edit `~/.config/omarchy/shell.json` and set that slot to `omarchy.power`.
Your z13-power config under `~/.config/z13-power/` is left alone.

## Requirements

| | |
|---|---|
| [z13-power](https://github.com/randallyash/rog-z13-power-management) | backend: profiles, TDP, charge cap, tray |
| [`z13ctl-bin`](https://github.com/dahui/z13ctl) | AUR; hardware control for the GZ302 |
| Omarchy / Quickshell | this is a bar widget + service |

Without the backend, the glyph still shows charge; profile pills and TDP will
not apply.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE). Same license as z13-power.
The plugin does not vendor z13ctl.
