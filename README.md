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
| **z13-power** | `v1.1.4` (`620a227d0905363bdd17d94e321d51eeb0254940`) | [rog-z13-power-management-1.1.4.tar.gz](https://github.com/randallyash/rog-z13-power-management/releases/download/v1.1.4/rog-z13-power-management-1.1.4.tar.gz) `sha256:93959bce9e22ae58d731c4b39a7aa02d871628b9954cc1f375d95e572f4ec4d5` | `/usr/share/z13-power-management/z13-power` `sha256:ce518274d54d4c1b366b2381bd4f48c76d03884e20a8c6bc9aaabc16ab2fc734` | `z13-power 1.1.4` |
| **z13-power-settings** | same `v1.1.4` tree | same tarball | `/usr/share/z13-power-management/z13-power-settings` `sha256:cac5377de48eaa3ae3b30f45327f03971aa9a77d14e14a369fbd25c9fc9bcf92` | file digest |
| **z13_power_common.py** | same `v1.1.4` tree | same tarball | `/usr/share/z13-power-management/z13_power_common.py` `sha256:642961682003749d599597373f906f7312f42cec6bf578d1c23845ca356efa09` | file digest |
| **z13_power_theme.py** | same `v1.1.4` tree | same tarball | `/usr/share/z13-power-management/z13_power_theme.py` `sha256:9152869ab456a0325d6e8bfeacb433b2f352f58ddf1abb18242c7113a6bdc518` | file digest |
| **z13_power_io.py** | same `v1.1.4` tree | same tarball | `/usr/share/z13-power-management/z13_power_io.py` `sha256:518dc7adc478ddd6b260f2d07077ef44d1a20d2ac3d880a8c4dde4353e31493a` | file digest |

Provenance: [dahui/z13ctl v1.3.2](https://github.com/dahui/z13ctl/releases/tag/v1.3.2) (annotated, signed tag; `checksums.txt` on the release matches the tarball digest) and [randallyash/rog-z13-power-management v1.1.4](https://github.com/randallyash/rog-z13-power-management/releases/tag/v1.1.4) (`SHA256SUMS` on the release; GitHub asset digest matches the tarball). A rebuilt or debug-split binary will not match and is refused.

### Install the pinned files

```sh
# z13ctl v1.3.2 → /usr/bin/z13ctl
curl -L -O https://github.com/dahui/z13ctl/releases/download/v1.3.2/z13ctl_1.3.2_linux_amd64.tar.gz
echo '95448e095673d38c507e0910ec9fb6ae9ea738eeb8beff691af12b74f548df94  z13ctl_1.3.2_linux_amd64.tar.gz' | sha256sum -c
tar -xzf z13ctl_1.3.2_linux_amd64.tar.gz z13ctl
sudo install -Dm755 z13ctl /usr/bin/z13ctl
echo '3e49f796e6eec2021ce4716f57c19f5f65f43f76408cb56a6454f88147f5f4d6  /usr/bin/z13ctl' | sha256sum -c

# z13-power v1.1.4 → /usr/share/z13-power-management/
curl -L -O https://github.com/randallyash/rog-z13-power-management/releases/download/v1.1.4/rog-z13-power-management-1.1.4.tar.gz
echo '93959bce9e22ae58d731c4b39a7aa02d871628b9954cc1f375d95e572f4ec4d5  rog-z13-power-management-1.1.4.tar.gz' | sha256sum -c
tar -xzf rog-z13-power-management-1.1.4.tar.gz
sudo install -Dm755 rog-z13-power-management-1.1.4/scripts/z13-power \
  /usr/share/z13-power-management/z13-power
sudo install -Dm755 rog-z13-power-management-1.1.4/service/z13-power-settings \
  /usr/share/z13-power-management/z13-power-settings
sudo install -Dm644 rog-z13-power-management-1.1.4/service/z13_power_common.py \
  /usr/share/z13-power-management/z13_power_common.py
sudo install -Dm644 rog-z13-power-management-1.1.4/service/z13_power_theme.py \
  /usr/share/z13-power-management/z13_power_theme.py
sudo install -Dm644 rog-z13-power-management-1.1.4/service/z13_power_io.py \
  /usr/share/z13-power-management/z13_power_io.py
echo 'ce518274d54d4c1b366b2381bd4f48c76d03884e20a8c6bc9aaabc16ab2fc734  /usr/share/z13-power-management/z13-power' | sha256sum -c
echo 'cac5377de48eaa3ae3b30f45327f03971aa9a77d14e14a369fbd25c9fc9bcf92  /usr/share/z13-power-management/z13-power-settings' | sha256sum -c
echo '642961682003749d599597373f906f7312f42cec6bf578d1c23845ca356efa09  /usr/share/z13-power-management/z13_power_common.py' | sha256sum -c
echo '9152869ab456a0325d6e8bfeacb433b2f352f58ddf1abb18242c7113a6bdc518  /usr/share/z13-power-management/z13_power_theme.py' | sha256sum -c
echo '518dc7adc478ddd6b260f2d07077ef44d1a20d2ac3d880a8c4dde4353e31493a  /usr/share/z13-power-management/z13_power_io.py' | sha256sum -c
```

Those six files are the plugin's runtime closure. Remaining files in the
same v1.1.4 tarball (service, udev, license) may be installed from that tree
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
  (`Z13CTL=/proc/self/fd/N`). Settings is started with the hashed companion
  module fds (`Z13_MOD_IO` / `_COMMON` / `_THEME`); it rehashes those same
  fds and `importlib`-loads them before any companion code runs. There is
  no pathname import and no `PYTHONPATH`.
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
