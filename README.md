# Z13 Power

Omarchy command center for the **2025 ASUS ROG Flow Z13 (GZ302)**. Click the
battery glyph for live charge, watts, and temp, then drive the machine:
TDP profiles, RGB, fans, undervolt, and charge cap. Settings is one tap
from the flyout.

| | |
|---|---|
| **TDP** | Max / Perf / Mid / Quiet / Low, plus Automatic and Lock across plug/unplug |
| **Telemetry** | Live charge, draw, package watts, and APU temp in the bar flyout |
| **RGB** | Keyboard + lightbar: modes, colors, brightness, theme-follow |
| **Fans** | Eight-point custom curve, or firmware auto |
| **Undervolt** | Curve Optimizer with a silicon-lottery score (best / weakest core) and a suggested starting offset |
| **Battery** | Charge cap, one-shot fill-to-100%, low-battery warnings that do not call Omarchy’s `powerprofiles-set` |

This is a `bar-widget` with a nested details panel (same shape as stock
`omarchy.power`) plus a `service`. Profile apply, lighting, fans, and
undervolt go through
[z13-power](https://github.com/randallyash/rog-z13-power-management) **1.2.0
or newer**. That backend writes power limits directly to the Ryzen SMU
(stapm, slow, and fast), which is what the APU follows. **`z13ctl` is not
a dependency** and is not executed, so an AUR update of `z13ctl-bin` cannot
break the pills. Without that backend the glyph still shows charge.

## Backend

`z13-io.py` runs only a root-owned `z13-power` under `/usr` and requires
`z13-power 1.2.0` or newer (`z13-power --version`). Hardware control is
inside that tree (`z13_power_hw.py`), including the SMU mailbox. There is
no `z13ctl` package to install and `/usr/bin/z13ctl` is not executed.

| Dependency | Required | Installed path | Runtime identity |
|---|---|---|---|
| **z13-power** | `1.2.0+` | `/usr/share/z13-power-management/z13-power` | `z13-power 1.2.0` |
| **controller** | same tree | `/usr/share/z13-power-management/z13_power_hw.py` | imported by the service |
| **settings** | same tree | `/usr/share/z13-power-management/z13-power-settings` | root-owned file |

Install z13-power 1.2.0 from its tree (`install.sh`, or copy `scripts/` and
`service/` into `/usr/share/z13-power-management/`). Do not install a
`z13ctl` package for this plugin.

## Install the plugin

GZ302 only. Backends first, then:

```sh
omarchy plugin add https://github.com/randallyash/omarchy-z13-power.git --enable
```

That clones and enables the plugin. It does not rewrite your bar and does not
install the backend.

## Usage

Click the battery glyph to open or close the flyout. Press Escape to close it.
Pills apply Max / Perf / Mid / Quiet / Low. Automatic follows AC, battery, and
low battery. Lock keeps a manual pick across plug/unplug. Settings opens RGB,
fan curve, undervolt (with silicon-lottery scoring), and charge cap.

## Configure

Put it in the right-hand (battery) slot:

```sh
omarchy bar move io.github.randallyash.z13-power --section right
```

This is a **manual-setup** plugin. `omarchy plugin add` only installs the
bar widget. Profile apply, TDP, and charge cap come from the pinned backend
above.

Runtime enforcement in `z13-io.py`:

- QML launches `/usr/bin/python3` (not `PATH` `python3`). The helper refuses
  to run unless that interpreter is the same inode as a root-owned,
  non-group-writable `/usr/bin/python3` (one same-dir symlink allowed).
- Executes only root-owned regular files under `/usr` (never `~/.local/bin`),
  via a held file descriptor (`/proc/self/fd/N`).
- Rejects `S_IWGRP` and `S_IWOTH` on `/usr` itself, every path component, and
  the file.
- Requires `z13-power --version` to be 1.2.0 or newer on that same fd.
  Settings is started from the same root-owned directory. There is no
  `/usr/bin/z13ctl` fd and no `Z13CTL` environment variable.
- Child processes get a sanitized environment: `PATH=/usr/bin`,
  `PYTHONNOUSERSITE=1`, `PYTHONSAFEPATH=1`.
  `PYTHONPATH`/`PYTHONHOME`/`LD_PRELOAD` from the caller are dropped.
- The v1.1.4 settings closure writes user state with O_NOFOLLOW + O_EXCL tmp
  + fsync + rename; reads are byte/schema capped; helpers are `/usr`
  fd-executed with a wall-clock deadline and TERM→KILL/reap. `xdg-open` is
  double-forked and reaped; `$EDITOR` is not used.
- Never downloads packages.

## Remove

```sh
omarchy plugin remove io.github.randallyash.z13-power
```

That takes the plugin away and nothing else. Config under `~/.config/z13-power/`
is left alone on purpose.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
