# Z13 Power

Omarchy bar plugin for the **2025 ASUS ROG Flow Z13 (GZ302)**. A battery
flyout with live charge, watts, and temp, plus Max / Perf / Mid / Quiet / Low,
Automatic, Lock, and a one-shot charge-to-100%. A background service handles
low-battery warnings without calling Omarchy’s `powerprofiles-set`.

This is a `bar-widget` with a nested details panel (same shape as stock
`omarchy.power`) plus a `service`. Profile apply goes through
[z13-power](https://github.com/randallyash/rog-z13-power-management); without
that backend the glyph still shows charge, and the pills will not drive TDP.

## Pinned backends

This plugin executes only the exact artifacts below. `z13-io.py` hashes the
held file descriptor and requires that exact identity; ranges such as
`1.1.0+` / `1.3.2+` are rejected. Install from these release URLs. Do not
install from `main`, from `z13-power-git`, or from an unverified clone.

| Dependency | Tag / commit | Release artifact | Installed path + digest | Runtime identity |
|---|---|---|---|---|
| **z13ctl** | `v1.3.2` (`2d794eadf28716e6acbc59df8275f08bea3a10c9`) | [z13ctl_1.3.2_linux_amd64.tar.gz](https://github.com/dahui/z13ctl/releases/download/v1.3.2/z13ctl_1.3.2_linux_amd64.tar.gz) `sha256:95448e095673d38c507e0910ec9fb6ae9ea738eeb8beff691af12b74f548df94` | `/usr/bin/z13ctl` `sha256:3e49f796e6eec2021ce4716f57c19f5f65f43f76408cb56a6454f88147f5f4d6` | `z13ctl version 1.3.2` |
| **z13-power** | `v1.1.3` (`7bc76cc2fa56c1779244a94946ab5fda239d2fec`) | [rog-z13-power-management-1.1.3.tar.gz](https://github.com/randallyash/rog-z13-power-management/releases/download/v1.1.3/rog-z13-power-management-1.1.3.tar.gz) `sha256:6ad2708902506caaea53887044416f84d7e662c1f42e7ab6eb4d91179008619c` | `/usr/share/z13-power-management/z13-power` `sha256:86fbc07ca87cbeaa87185d4899908ac0a807058e4fe1f80d8dc19beb0723d071` | `z13-power 1.1.3` |
| **z13-power-settings** | same `v1.1.3` tree | same tarball | `/usr/share/z13-power-management/z13-power-settings` `sha256:d22805c3347e5a816d94a0301431a242db777595c3c1dbdc1e4007cb42699768` | file digest |
| **z13_power_common.py** | same `v1.1.3` tree | same tarball | `/usr/share/z13-power-management/z13_power_common.py` `sha256:43aeaea43a28bd27b45ab6027a455345767b4874ef8b3f3b2e8090f1e2edc89e` | file digest |
| **z13_power_theme.py** | same `v1.1.3` tree | same tarball | `/usr/share/z13-power-management/z13_power_theme.py` `sha256:9152869ab456a0325d6e8bfeacb433b2f352f58ddf1abb18242c7113a6bdc518` | file digest |
| **z13_power_io.py** | same `v1.1.3` tree | same tarball | `/usr/share/z13-power-management/z13_power_io.py` `sha256:0656a72909250aa4fb18c09aa28d80e1ada6f5aa482bc96a5a7de76460002072` | file digest |

Provenance: [dahui/z13ctl v1.3.2](https://github.com/dahui/z13ctl/releases/tag/v1.3.2) (annotated, signed tag; `checksums.txt` on the release matches the tarball digest) and [randallyash/rog-z13-power-management v1.1.3](https://github.com/randallyash/rog-z13-power-management/releases/tag/v1.1.3) (`SHA256SUMS` on the release; GitHub asset digest matches the tarball). A rebuilt or debug-split binary will not match and is refused.

### Install the pinned files

```sh
# z13ctl v1.3.2 → /usr/bin/z13ctl
curl -L -O https://github.com/dahui/z13ctl/releases/download/v1.3.2/z13ctl_1.3.2_linux_amd64.tar.gz
echo '95448e095673d38c507e0910ec9fb6ae9ea738eeb8beff691af12b74f548df94  z13ctl_1.3.2_linux_amd64.tar.gz' | sha256sum -c
tar -xzf z13ctl_1.3.2_linux_amd64.tar.gz z13ctl
sudo install -Dm755 z13ctl /usr/bin/z13ctl
echo '3e49f796e6eec2021ce4716f57c19f5f65f43f76408cb56a6454f88147f5f4d6  /usr/bin/z13ctl' | sha256sum -c

# z13-power v1.1.3 → /usr/share/z13-power-management/
curl -L -O https://github.com/randallyash/rog-z13-power-management/releases/download/v1.1.3/rog-z13-power-management-1.1.3.tar.gz
echo '6ad2708902506caaea53887044416f84d7e662c1f42e7ab6eb4d91179008619c  rog-z13-power-management-1.1.3.tar.gz' | sha256sum -c
tar -xzf rog-z13-power-management-1.1.3.tar.gz
sudo install -Dm755 rog-z13-power-management-1.1.3/scripts/z13-power \
  /usr/share/z13-power-management/z13-power
sudo install -Dm755 rog-z13-power-management-1.1.3/service/z13-power-settings \
  /usr/share/z13-power-management/z13-power-settings
sudo install -Dm644 rog-z13-power-management-1.1.3/service/z13_power_common.py \
  /usr/share/z13-power-management/z13_power_common.py
sudo install -Dm644 rog-z13-power-management-1.1.3/service/z13_power_theme.py \
  /usr/share/z13-power-management/z13_power_theme.py
sudo install -Dm644 rog-z13-power-management-1.1.3/service/z13_power_io.py \
  /usr/share/z13-power-management/z13_power_io.py
echo '86fbc07ca87cbeaa87185d4899908ac0a807058e4fe1f80d8dc19beb0723d071  /usr/share/z13-power-management/z13-power' | sha256sum -c
echo 'd22805c3347e5a816d94a0301431a242db777595c3c1dbdc1e4007cb42699768  /usr/share/z13-power-management/z13-power-settings' | sha256sum -c
echo '43aeaea43a28bd27b45ab6027a455345767b4874ef8b3f3b2e8090f1e2edc89e  /usr/share/z13-power-management/z13_power_common.py' | sha256sum -c
echo '9152869ab456a0325d6e8bfeacb433b2f352f58ddf1abb18242c7113a6bdc518  /usr/share/z13-power-management/z13_power_theme.py' | sha256sum -c
echo '0656a72909250aa4fb18c09aa28d80e1ada6f5aa482bc96a5a7de76460002072  /usr/share/z13-power-management/z13_power_io.py' | sha256sum -c
```

Those six files are the plugin's runtime closure. Remaining files in the
same v1.1.3 tarball (service, udev, license) may be installed from that tree
into the same prefix; they must not come from a different commit.

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
low battery. Lock keeps a manual pick across plug/unplug.

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
- Requires the exact pinned sha256 (and `--version` where it exists) on the
  same fd. `z13-power` is launched with that already-validated `z13ctl` fd
  (`Z13CTL=/proc/self/fd/N`). Settings keeps the hashed `z13ctl` fd and
  rehashes it on every use.
- Child processes get a sanitized environment: `PATH=/usr/bin`,
  `PYTHONNOUSERSITE=1`, `PYTHONSAFEPATH=1`,
  `PYTHONPATH=/usr/share/z13-power-management`.
  `PYTHONPATH`/`PYTHONHOME`/`LD_PRELOAD` from the caller are dropped.
- The v1.1.3 settings closure writes user state with O_NOFOLLOW + O_EXCL tmp
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
