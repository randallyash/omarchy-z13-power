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
| **z13-power** | `v1.1.2` (`2ecec501a1dcec83de420cda7a4b30b45129fe1e`) | [rog-z13-power-management-1.1.2.tar.gz](https://github.com/randallyash/rog-z13-power-management/releases/download/v1.1.2/rog-z13-power-management-1.1.2.tar.gz) `sha256:735770e72cb89183134f7516c3620e6e70ffd116197ea6b159dc45ac1f96805c` | `/usr/share/z13-power-management/z13-power` `sha256:60f63e2391492bf689de82e6974427468555564333824bbc75c6da416d1c87ca` | `z13-power 1.1.2` |
| **z13-power-settings** | same `v1.1.2` tree | same tarball | `/usr/share/z13-power-management/z13-power-settings` `sha256:2dac65348f0093f03a103f27976af902cdd3074619421f0d88b8d3f70bc708ad` | file digest |
| **z13_power_common.py** | same `v1.1.2` tree | same tarball | `/usr/share/z13-power-management/z13_power_common.py` `sha256:fa52d53b2c81505df40f0ed4738ff67baf953b73f5314fbc267b54f7a4120963` | file digest |
| **z13_power_theme.py** | same `v1.1.2` tree | same tarball | `/usr/share/z13-power-management/z13_power_theme.py` `sha256:eae0b1f2f540423097ea65e40501441c666073c7f603528a474018cb28892a9a` | file digest |
| **z13_power_io.py** | same `v1.1.2` tree | same tarball | `/usr/share/z13-power-management/z13_power_io.py` `sha256:887f5c20857a0963035f2bf865943d978b433efd7c9bd7f1fb76811c90885766` | file digest |

Provenance: [dahui/z13ctl v1.3.2](https://github.com/dahui/z13ctl/releases/tag/v1.3.2) (annotated, signed tag; `checksums.txt` on the release matches the tarball digest) and [randallyash/rog-z13-power-management v1.1.2](https://github.com/randallyash/rog-z13-power-management/releases/tag/v1.1.2) (`SHA256SUMS` on the release; GitHub asset digest matches the tarball). A rebuilt or debug-split binary will not match and is refused.

### Install the pinned files

```sh
# z13ctl v1.3.2 → /usr/bin/z13ctl
curl -L -O https://github.com/dahui/z13ctl/releases/download/v1.3.2/z13ctl_1.3.2_linux_amd64.tar.gz
echo '95448e095673d38c507e0910ec9fb6ae9ea738eeb8beff691af12b74f548df94  z13ctl_1.3.2_linux_amd64.tar.gz' | sha256sum -c
tar -xzf z13ctl_1.3.2_linux_amd64.tar.gz z13ctl
sudo install -Dm755 z13ctl /usr/bin/z13ctl
echo '3e49f796e6eec2021ce4716f57c19f5f65f43f76408cb56a6454f88147f5f4d6  /usr/bin/z13ctl' | sha256sum -c

# z13-power v1.1.2 → /usr/share/z13-power-management/
curl -L -O https://github.com/randallyash/rog-z13-power-management/releases/download/v1.1.2/rog-z13-power-management-1.1.2.tar.gz
echo '735770e72cb89183134f7516c3620e6e70ffd116197ea6b159dc45ac1f96805c  rog-z13-power-management-1.1.2.tar.gz' | sha256sum -c
tar -xzf rog-z13-power-management-1.1.2.tar.gz
sudo install -Dm755 rog-z13-power-management-1.1.2/scripts/z13-power \
  /usr/share/z13-power-management/z13-power
sudo install -Dm755 rog-z13-power-management-1.1.2/service/z13-power-settings \
  /usr/share/z13-power-management/z13-power-settings
sudo install -Dm644 rog-z13-power-management-1.1.2/service/z13_power_common.py \
  /usr/share/z13-power-management/z13_power_common.py
sudo install -Dm644 rog-z13-power-management-1.1.2/service/z13_power_theme.py \
  /usr/share/z13-power-management/z13_power_theme.py
sudo install -Dm644 rog-z13-power-management-1.1.2/service/z13_power_io.py \
  /usr/share/z13-power-management/z13_power_io.py
echo '60f63e2391492bf689de82e6974427468555564333824bbc75c6da416d1c87ca  /usr/share/z13-power-management/z13-power' | sha256sum -c
echo '2dac65348f0093f03a103f27976af902cdd3074619421f0d88b8d3f70bc708ad  /usr/share/z13-power-management/z13-power-settings' | sha256sum -c
echo 'fa52d53b2c81505df40f0ed4738ff67baf953b73f5314fbc267b54f7a4120963  /usr/share/z13-power-management/z13_power_common.py' | sha256sum -c
echo 'eae0b1f2f540423097ea65e40501441c666073c7f603528a474018cb28892a9a  /usr/share/z13-power-management/z13_power_theme.py' | sha256sum -c
echo '887f5c20857a0963035f2bf865943d978b433efd7c9bd7f1fb76811c90885766  /usr/share/z13-power-management/z13_power_io.py' | sha256sum -c
```

Those six files are the plugin's runtime closure. Remaining files in the
same v1.1.2 tarball (service, udev, license) may be installed from that tree
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

- Executes only root-owned regular files under `/usr` (never `~/.local/bin`),
  via a held file descriptor (`/proc/self/fd/N`).
- Rejects `S_IWGRP` and `S_IWOTH` on `/usr` itself, every path component, and
  the file.
- Requires the exact pinned sha256 (and `--version` where it exists) on the
  same fd. `spawn-settings` also hashes `z13_power_common.py`,
  `z13_power_theme.py`, and `z13_power_io.py` before exec.
- Child processes get a sanitized environment: `PATH=/usr/bin`,
  `PYTHONNOUSERSITE=1`, `PYTHONSAFEPATH=1`,
  `PYTHONPATH=/usr/share/z13-power-management`, `Z13CTL=/usr/bin/z13ctl`.
  `PYTHONPATH`/`PYTHONHOME`/`LD_PRELOAD` from the caller are dropped.
- The v1.1.2 settings closure writes user state with O_NOFOLLOW + O_EXCL tmp
  + fsync + rename; reads are byte/schema capped; helpers (`z13ctl`,
  `fc-match`, `hyprctl`, `asusctl`, `xdg-open`) are `/usr` fd-executed with
  a wall-clock deadline and TERM→KILL/reap. `xdg-open` is the only
  detached GUI launch, and `$EDITOR` is not used.
- Never downloads packages.

## Remove

```sh
omarchy plugin remove io.github.randallyash.z13-power
```

That takes the plugin away and nothing else. Config under `~/.config/z13-power/`
is left alone on purpose.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
