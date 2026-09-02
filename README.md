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
| **z13-power** | `v1.1.1` (`459e77dfc0133cb1ae1a6c023eb52a6d148d7297`) | [rog-z13-power-management-1.1.1.tar.gz](https://github.com/randallyash/rog-z13-power-management/releases/download/v1.1.1/rog-z13-power-management-1.1.1.tar.gz) `sha256:1a784787464a5f4b82a3dbf3848d393407cea7fb58ef301a8a58e9f0fbaf6ee9` | `/usr/share/z13-power-management/z13-power` `sha256:14194c983032382f265dc8df2e9bcda814d7354c66c7a4048025afcdff1b9d68` | `z13-power 1.1.1` |
| **z13-power-settings** | same `v1.1.1` tree | same tarball | `/usr/share/z13-power-management/z13-power-settings` `sha256:6f70f9d2e2a9ee14770793bce08b0e95ddd6b240f100063a98578798961f23e0` | file digest |
| **z13_power_common.py** | same `v1.1.1` tree | same tarball | `/usr/share/z13-power-management/z13_power_common.py` `sha256:5a0823d39ac43719c12c5ec73f11e75d1ffbf4e0311c7e24ae7e9d64b97b23d5` | file digest |
| **z13_power_theme.py** | same `v1.1.1` tree | same tarball | `/usr/share/z13-power-management/z13_power_theme.py` `sha256:3c476b2c1fa56be4bd245249ce3072784b07be26a006fa84daf31d7686b28959` | file digest |

Provenance: [dahui/z13ctl v1.3.2](https://github.com/dahui/z13ctl/releases/tag/v1.3.2) (annotated, signed tag; `checksums.txt` on the release matches the tarball digest) and [randallyash/rog-z13-power-management v1.1.1](https://github.com/randallyash/rog-z13-power-management/releases/tag/v1.1.1) (`SHA256SUMS` on the release; GitHub asset digest matches the tarball). A rebuilt or debug-split binary will not match and is refused.

### Install the pinned files

```sh
# z13ctl v1.3.2 → /usr/bin/z13ctl
curl -L -O https://github.com/dahui/z13ctl/releases/download/v1.3.2/z13ctl_1.3.2_linux_amd64.tar.gz
echo '95448e095673d38c507e0910ec9fb6ae9ea738eeb8beff691af12b74f548df94  z13ctl_1.3.2_linux_amd64.tar.gz' | sha256sum -c
tar -xzf z13ctl_1.3.2_linux_amd64.tar.gz z13ctl
sudo install -Dm755 z13ctl /usr/bin/z13ctl
echo '3e49f796e6eec2021ce4716f57c19f5f65f43f76408cb56a6454f88147f5f4d6  /usr/bin/z13ctl' | sha256sum -c

# z13-power v1.1.1 → /usr/share/z13-power-management/
curl -L -O https://github.com/randallyash/rog-z13-power-management/releases/download/v1.1.1/rog-z13-power-management-1.1.1.tar.gz
echo '1a784787464a5f4b82a3dbf3848d393407cea7fb58ef301a8a58e9f0fbaf6ee9  rog-z13-power-management-1.1.1.tar.gz' | sha256sum -c
tar -xzf rog-z13-power-management-1.1.1.tar.gz
sudo install -Dm755 rog-z13-power-management-1.1.1/scripts/z13-power \
  /usr/share/z13-power-management/z13-power
sudo install -Dm755 rog-z13-power-management-1.1.1/service/z13-power-settings \
  /usr/share/z13-power-management/z13-power-settings
sudo install -Dm644 rog-z13-power-management-1.1.1/service/z13_power_common.py \
  /usr/share/z13-power-management/z13_power_common.py
sudo install -Dm644 rog-z13-power-management-1.1.1/service/z13_power_theme.py \
  /usr/share/z13-power-management/z13_power_theme.py
echo '14194c983032382f265dc8df2e9bcda814d7354c66c7a4048025afcdff1b9d68  /usr/share/z13-power-management/z13-power' | sha256sum -c
echo '6f70f9d2e2a9ee14770793bce08b0e95ddd6b240f100063a98578798961f23e0  /usr/share/z13-power-management/z13-power-settings' | sha256sum -c
echo '5a0823d39ac43719c12c5ec73f11e75d1ffbf4e0311c7e24ae7e9d64b97b23d5  /usr/share/z13-power-management/z13_power_common.py' | sha256sum -c
echo '3c476b2c1fa56be4bd245249ce3072784b07be26a006fa84daf31d7686b28959  /usr/share/z13-power-management/z13_power_theme.py' | sha256sum -c
```

Those five files are the plugin's runtime closure. Remaining files in the
same v1.1.1 tarball (service, udev, license) may be installed from that tree
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
  same fd. `spawn-settings` also hashes `z13_power_common.py` and
  `z13_power_theme.py` before exec.
- Child processes get a sanitized environment: `PATH=/usr/bin`,
  `PYTHONNOUSERSITE=1`, `PYTHONSAFEPATH=1`,
  `PYTHONPATH=/usr/share/z13-power-management`, `Z13CTL=/usr/bin/z13ctl`.
  `PYTHONPATH`/`PYTHONHOME`/`LD_PRELOAD` from the caller are dropped.
- The v1.1.1 wrapper invokes only `/usr/bin/z13ctl` (not `command -v`) and
  does not import from `~/.local/bin`.
- Never downloads packages.

## Remove

```sh
omarchy plugin remove io.github.randallyash.z13-power
```

That takes the plugin away and nothing else. Config under `~/.config/z13-power/`
is left alone on purpose.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
