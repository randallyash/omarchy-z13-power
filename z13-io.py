#!/usr/bin/env python3
"""Bounded, descriptor-relative I/O for the Z13 Power Omarchy plugin.

Every file and child process used by the persistent shell goes through this
helper. Pathnames are never used after the first trusted directory open:
components are opened with O_NOFOLLOW, verified with fstat, and later
operations use dir_fd / /proc/self/fd.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import pwd
import re
import select
import signal
import stat
import subprocess
import sys
import time

MAX_FILE_BYTES = 16 * 1024
MAX_PROC_BYTES = 32 * 1024
MAX_ERR_BYTES = 8 * 1024
MAX_COMMAND_BYTES = 2048
MAX_STATUS_STRING = 64
DEFAULT_TIMEOUT = 3.0
DIAGNOSE_TIMEOUT = 8.0

Z13CTL_MIN = (1, 3, 2)
Z13_POWER_MIN = (1, 1, 0)
Z13CTL_PATH = ("bin", "z13ctl")
Z13_POWER_PATH = ("share", "z13-power-management", "z13-power")
Z13_SETTINGS_PATH = ("share", "z13-power-management", "z13-power-settings")
OMARCHY_BIN = {
    "omarchy-battery-status": ("bin", "omarchy-battery-status"),
    "omarchy-powerprofiles-list": ("bin", "omarchy-powerprofiles-list"),
    "omarchy-powerprofiles-set": ("bin", "omarchy-powerprofiles-set"),
    "omarchy-system-stats": ("bin", "omarchy-system-stats"),
    "omarchy-battery-low": ("bin", "omarchy-battery-low"),
}

STATUS_KEYS = {
    "mode": str,
    "label": str,
    "automatic": bool,
    "locked": bool,
    "ac": bool,
    "capacity": (int, float, type(None)),
    "tdp": (int, float, str, type(None)),
    "profile": str,
    "fill_once": bool,
    "charge_limit": (int, float, type(None)),
}


class Missing(Exception):
    pass


def fail(msg: str, code: int = 1) -> None:
    sys.stderr.write(msg + "\n")
    raise SystemExit(code)


def clamp_str(value: object, n: int = MAX_STATUS_STRING) -> str:
    return str(value if value is not None else "")[:n]


def open_anchor(path: str, *, owner: int | None) -> int:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        st = os.fstat(fd)
        if not stat.S_ISDIR(st.st_mode):
            fail(f"anchor is not a directory: {path}")
        if owner is not None and st.st_uid != owner:
            fail(f"anchor not owned as required: {path}")
        return fd
    except Exception:
        os.close(fd)
        raise


def trusted_home_fd() -> int:
    home = pwd.getpwuid(os.getuid()).pw_dir
    return open_anchor(home, owner=os.getuid())


def trusted_usr_fd() -> int:
    return open_anchor("/usr", owner=0)


def trusted_sys_fd() -> int:
    return open_anchor("/sys", owner=0)


def _check_dir(st: os.stat_result, *, owner: int | None) -> None:
    if not stat.S_ISDIR(st.st_mode):
        fail("path component is not a directory")
    if owner is not None and st.st_uid != owner:
        fail("directory owner mismatch")
    if st.st_mode & stat.S_IWOTH and not (st.st_mode & stat.S_ISVTX):
        fail("world-writable directory")


def _check_reg_exec(st: os.stat_result) -> None:
    if not stat.S_ISREG(st.st_mode):
        fail("not a regular file")
    if st.st_uid != 0:
        fail("binary is not root-owned")
    if st.st_mode & stat.S_IWOTH:
        fail("binary is world-writable")
    if st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) == 0:
        fail("binary is not executable")


def openat_dir(parent_fd: int, name: str, *, owner: int | None, create: bool = False, mode: int = 0o700) -> int:
    if name in ("", ".", "..") or "/" in name or "\x00" in name:
        fail("illegal path component")
    if create:
        try:
            os.mkdir(name, mode, dir_fd=parent_fd)
        except FileExistsError:
            pass
    try:
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
    except FileNotFoundError:
        raise Missing(name)
    try:
        st = os.fstat(fd)
        _check_dir(st, owner=owner)
        if create and owner == os.getuid():
            os.fchmod(fd, mode)
        return fd
    except Exception:
        os.close(fd)
        raise


def openat_file(parent_fd: int, name: str, flags: int, *, mode: int = 0) -> int:
    if name in ("", ".", "..") or "/" in name or "\x00" in name:
        fail("illegal path component")
    try:
        fd = os.open(name, flags | os.O_NOFOLLOW | os.O_CLOEXEC, mode, dir_fd=parent_fd)
    except FileNotFoundError:
        raise Missing(name)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            fail("not a regular file")
        return fd
    except Exception:
        os.close(fd)
        raise


def walk_dirs(anchor_fd: int, parts: list[str], *, owner: int | None, create: bool = False) -> int:
    fd = anchor_fd
    close_anchor = False
    try:
        for i, part in enumerate(parts):
            nxt = openat_dir(fd, part, owner=owner, create=create)
            if fd is not anchor_fd or close_anchor:
                os.close(fd)
            fd = nxt
            close_anchor = True
        if fd is anchor_fd:
            fail("walk_dirs requires at least one component")
        return fd
    except Exception:
        if fd is not anchor_fd:
            try:
                os.close(fd)
            except OSError:
                pass
        raise


def read_fd(fd: int, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        buf = os.read(fd, 4096)
        if not buf:
            break
        total += len(buf)
        if total > max_bytes:
            fail("file too large")
        chunks.append(buf)
    return b"".join(chunks)


def read_under(anchor_fd: int, dirs: list[str], filename: str, max_bytes: int, *, owner: int | None) -> bytes:
    dirfd = walk_dirs(anchor_fd, dirs, owner=owner) if dirs else anchor_fd
    close_dir = dirs != []
    try:
        fd = openat_file(dirfd, filename, os.O_RDONLY)
        try:
            return read_fd(fd, max_bytes)
        finally:
            os.close(fd)
    finally:
        if close_dir:
            os.close(dirfd)


def home_state_dirfd(*, create: bool) -> int:
    home = trusted_home_fd()
    try:
        local_fd = openat_dir(home, ".local", owner=os.getuid(), create=create, mode=0o755)
        try:
            state_fd = openat_dir(local_fd, "state", owner=os.getuid(), create=create, mode=0o755)
            try:
                return openat_dir(state_fd, "z13-power", owner=os.getuid(), create=create, mode=0o700)
            finally:
                os.close(state_fd)
        finally:
            os.close(local_fd)
    finally:
        os.close(home)


def _read_status_or_empty() -> None:
    home = trusted_home_fd()
    try:
        try:
            raw = read_under(
                home, [".local", "state", "z13-power"], "status.json", MAX_FILE_BYTES, owner=os.getuid()
            )
        except Missing:
            print("{}")
            return
    finally:
        os.close(home)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("status.json is not UTF-8 JSON")
    if not isinstance(data, dict):
        fail("status.json must be an object")
    out: dict = {}
    for key, typ in STATUS_KEYS.items():
        if key not in data:
            continue
        val = data[key]
        if isinstance(typ, tuple):
            if not isinstance(val, typ):
                continue
        elif not isinstance(val, typ):
            continue
        if isinstance(val, str):
            out[key] = clamp_str(val)
        elif isinstance(val, bool):
            out[key] = val
        elif isinstance(val, (int, float)) and not isinstance(val, bool):
            if not (-1e6 <= float(val) <= 1e6):
                continue
            out[key] = val
        elif val is None:
            out[key] = None
    print(json.dumps(out, separators=(",", ":")))


def _read_battery_or_empty() -> None:
    home = trusted_home_fd()
    try:
        try:
            raw = read_under(home, [".config", "z13-power"], "battery.conf", MAX_FILE_BYTES, owner=os.getuid())
        except Missing:
            print("{}")
            return
    finally:
        os.close(home)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("battery.conf is not UTF-8")
    limit = None
    for line in text.splitlines()[:32]:
        line = line.strip()
        if not line.startswith("charge_limit"):
            continue
        _, _, rest = line.partition("=")
        rest = rest.strip()
        if rest.isdigit():
            n = int(rest)
            if 40 <= n <= 100:
                limit = n
        break
    print(json.dumps({} if limit is None else {"charge_limit": limit}, separators=(",", ":")))


def cmd_write_command(payload: str) -> None:
    raw_in = payload.encode("utf-8")
    if len(raw_in) > MAX_COMMAND_BYTES:
        fail("command payload too large")
    try:
        obj = json.loads(payload)
    except json.JSONDecodeError:
        fail("command payload is not JSON")
    if not isinstance(obj, dict):
        fail("command payload must be an object")
    op = obj.get("op")
    if not isinstance(op, str) or op not in ("mode", "automatic", "lock", "fill"):
        fail("invalid command op")
    body = json.dumps(obj, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(body) > MAX_COMMAND_BYTES:
        fail("command payload too large")

    dirfd = home_state_dirfd(create=True)
    tmp_name = f".cmd.{os.getpid()}.{os.urandom(8).hex()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = None
    try:
        fd = os.open(tmp_name, flags, 0o600, dir_fd=dirfd)
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            fail("tmp is not a regular file")
        view = memoryview(body)
        off = 0
        while off < len(view):
            n = os.write(fd, view[off:])
            if n <= 0:
                fail("short write")
            off += n
        os.fsync(fd)
        os.rename(tmp_name, "command.json", src_dir_fd=dirfd, dst_dir_fd=dirfd)
        os.fsync(dirfd)
    except OSError as e:
        if fd is not None:
            try:
                os.unlink(tmp_name, dir_fd=dirfd)
            except OSError:
                pass
        fail(f"command write failed: {e}")
    finally:
        if fd is not None:
            os.close(fd)
        os.close(dirfd)


def open_usr_file(rel: tuple[str, ...]) -> int:
    usr = trusted_usr_fd()
    try:
        *dirs, name = rel
        dirfd = usr
        close_dir = False
        if dirs:
            # first component after /usr
            dirfd = walk_dirs(usr, list(dirs), owner=0)
            close_dir = True
        try:
            fd = openat_file(dirfd, name, os.O_RDONLY)
            st = os.fstat(fd)
            _check_reg_exec(st)
            return fd
        finally:
            if close_dir:
                os.close(dirfd)
    finally:
        os.close(usr)


def clear_cloexec(fd: int) -> None:
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    fcntl.fcntl(fd, fcntl.F_SETFD, flags & ~fcntl.FD_CLOEXEC)
    os.set_inheritable(fd, True)


def kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass


def bounded_collect(proc: subprocess.Popen, timeout: float, max_out: int, max_err: int) -> tuple[bytes, bytes, int]:
    out_fd = proc.stdout.fileno()
    err_fd = proc.stderr.fileno()
    for fd in (out_fd, err_fd):
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    out = bytearray()
    err = bytearray()
    open_fds = {out_fd, err_fd}
    deadline = time.monotonic() + timeout

    def read_one(fd: int) -> None:
        try:
            chunk = os.read(fd, 4096)
        except BlockingIOError:
            return
        if chunk == b"":
            open_fds.discard(fd)
            return
        if fd == out_fd:
            out.extend(chunk)
            if len(out) > max_out:
                kill_group(proc)
                fail("stdout overflow", 125)
        else:
            err.extend(chunk)
            if len(err) > max_err:
                kill_group(proc)
                fail("stderr overflow", 125)

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            kill_group(proc)
            fail("timeout", 124)
        rc = proc.poll()
        if not open_fds and rc is not None:
            return bytes(out), bytes(err), rc
        rlist = list(open_fds)
        if not rlist:
            try:
                proc.wait(timeout=min(remaining, 0.05))
            except subprocess.TimeoutExpired:
                continue
            return bytes(out), bytes(err), proc.returncode or 0
        ready, _, _ = select.select(rlist, [], [], min(remaining, 0.1))
        for fd in ready:
            read_one(fd)
        if rc is not None and not ready:
            for fd in list(open_fds):
                read_one(fd)
            if not open_fds:
                return bytes(out), bytes(err), rc


def spawn_fd(fd: int, extra_argv: list[str], timeout: float, max_out: int, max_err: int) -> tuple[bytes, int]:
    clear_cloexec(fd)
    proc_path = f"/proc/self/fd/{fd}"
    argv = [proc_path, *extra_argv]
    proc = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        close_fds=True,
        pass_fds=(fd,),
    )
    try:
        out, _err, rc = bounded_collect(proc, timeout, max_out, max_err)
        return out, rc
    finally:
        if proc.poll() is None:
            kill_group(proc)


def parse_semver(text: str) -> tuple[int, int, int] | None:
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def require_z13ctl() -> None:
    fd = open_usr_file(Z13CTL_PATH)
    try:
        out, rc = spawn_fd(fd, ["--version"], 2.0, 256, 256)
    finally:
        os.close(fd)
    ver = parse_semver(out.decode("utf-8", "replace"))
    if ver is None or ver < Z13CTL_MIN:
        fail(
            f"z13ctl-bin {Z13CTL_MIN[0]}.{Z13CTL_MIN[1]}.{Z13CTL_MIN[2]}+ required "
            f"(https://github.com/dahui/z13ctl, AUR z13ctl-bin); got {out!r}"
        )


def require_z13_power() -> None:
    fd = open_usr_file(Z13_POWER_PATH)
    try:
        out, rc = spawn_fd(fd, ["--version"], 2.0, 256, 256)
    finally:
        os.close(fd)
    ver = parse_semver(out.decode("utf-8", "replace"))
    if ver is None or ver < Z13_POWER_MIN:
        fail(
            "z13-power "
            f"{Z13_POWER_MIN[0]}.{Z13_POWER_MIN[1]}.{Z13_POWER_MIN[2]}+ required "
            "(https://github.com/randallyash/rog-z13-power-management, "
            "package z13-power-git); install/upgrade then retry"
        )


def cmd_run(argv: list[str], timeout: float, max_bytes: int) -> None:
    if not argv:
        fail("run requires a command")
    name = os.path.basename(argv[0])
    extra = argv[1:]
    if name in OMARCHY_BIN:
        rel = OMARCHY_BIN[name]
        fd = open_usr_file(rel)
    elif name == "z13-power":
        require_z13ctl()
        require_z13_power()
        fd = open_usr_file(Z13_POWER_PATH)
    else:
        fail(f"command not allowed: {name}")
    try:
        out, rc = spawn_fd(fd, extra, timeout, max_bytes, MAX_ERR_BYTES)
    finally:
        os.close(fd)
    sys.stdout.buffer.write(out)
    if rc not in (0, None):
        raise SystemExit(rc)


def cmd_spawn_settings() -> None:
    fd = open_usr_file(Z13_SETTINGS_PATH)
    try:
        clear_cloexec(fd)
        proc_path = f"/proc/self/fd/{fd}"
        pid = os.fork()
        if pid == 0:
            try:
                os.setsid()
                devnull = os.open("/dev/null", os.O_RDWR | os.O_CLOEXEC)
                os.dup2(devnull, 0)
                os.dup2(devnull, 1)
                os.dup2(devnull, 2)
                os.execv(proc_path, [proc_path])
            except Exception:
                os._exit(127)
        # Parent returns immediately; the settings window is a long-lived UI.
    finally:
        os.close(fd)


def cmd_read_hwmon() -> None:
    sysfd = trusted_sys_fd()
    sys_dev = os.fstat(sysfd).st_dev
    try:
        class_fd = openat_dir(sysfd, "class", owner=0)
        try:
            hwmon_fd = openat_dir(class_fd, "hwmon", owner=0)
        finally:
            os.close(class_fd)
    except (SystemExit, Missing, OSError):
        os.close(sysfd)
        print("{}")
        return
    if os.fstat(hwmon_fd).st_dev != sys_dev:
        os.close(hwmon_fd)
        os.close(sysfd)
        print("{}")
        return
    watts = None
    temp_c = None
    try:
        names = os.listdir(hwmon_fd)
    except OSError:
        os.close(hwmon_fd)
        os.close(sysfd)
        print("{}")
        return
    try:
        for name in names[:32]:
            if not re.fullmatch(r"hwmon\d+", name):
                continue
            try:
                # sysfs class/hwmon/hwmonN is a symlink into /sys/devices.
                # Follow only if the target remains on the same sysfs device.
                one = os.open(
                    name,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
                    dir_fd=hwmon_fd,
                )
                if os.fstat(one).st_dev != sys_dev:
                    os.close(one)
                    continue
            except OSError:
                continue
            try:
                nfd = openat_file(one, "name", os.O_RDONLY)
                try:
                    label = read_fd(nfd, 64).decode("ascii", "ignore").strip()
                finally:
                    os.close(nfd)
                if label != "amdgpu":
                    continue
                for fname in ("power1_average", "power1_input"):
                    try:
                        pfd = openat_file(one, fname, os.O_RDONLY)
                    except SystemExit:
                        continue
                    try:
                        raw = read_fd(pfd, 32).decode("ascii", "ignore").strip()
                        n = int(raw)
                        if 0 < n < 10**12:
                            watts = int(round(n / 1_000_000))
                            break
                    except ValueError:
                        pass
                    finally:
                        os.close(pfd)
                try:
                    tfd = openat_file(one, "temp1_input", os.O_RDONLY)
                except SystemExit:
                    tfd = None
                if tfd is not None:
                    try:
                        raw = read_fd(tfd, 32).decode("ascii", "ignore").strip()
                        n = int(raw)
                        if 0 < n < 200_000:
                            temp_c = int(round(n / 1000))
                    except ValueError:
                        pass
                    finally:
                        os.close(tfd)
                break
            finally:
                os.close(one)
    finally:
        os.close(hwmon_fd)
        os.close(sysfd)
    out = {}
    if watts is not None:
        out["watts"] = watts
    if temp_c is not None:
        out["temp_c"] = temp_c
    print(json.dumps(out, separators=(",", ":")))


def cmd_check_deps() -> None:
    require_z13ctl()
    require_z13_power()
    print(
        json.dumps(
            {
                "z13ctl_min": f"{Z13CTL_MIN[0]}.{Z13CTL_MIN[1]}.{Z13CTL_MIN[2]}",
                "z13_power_min": f"{Z13_POWER_MIN[0]}.{Z13_POWER_MIN[1]}.{Z13_POWER_MIN[2]}",
            },
            separators=(",", ":"),
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="z13-io")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("read-status")
    sub.add_parser("read-battery-conf")
    sub.add_parser("read-hwmon")
    sub.add_parser("check-deps")
    sub.add_parser("spawn-settings")
    p_write = sub.add_parser("write-command")
    p_write.add_argument("payload")
    p_run = sub.add_parser("run")
    p_run.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    p_run.add_argument("--max-bytes", type=int, default=MAX_PROC_BYTES)
    p_run.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.cmd == "read-status":
        _read_status_or_empty()
    elif args.cmd == "read-battery-conf":
        _read_battery_or_empty()
    elif args.cmd == "read-hwmon":
        cmd_read_hwmon()
    elif args.cmd == "check-deps":
        cmd_check_deps()
    elif args.cmd == "spawn-settings":
        cmd_spawn_settings()
    elif args.cmd == "write-command":
        cmd_write_command(args.payload)
    elif args.cmd == "run":
        argv = args.argv
        if argv and argv[0] == "--":
            argv = argv[1:]
        timeout = min(max(args.timeout, 0.1), 15.0)
        max_bytes = min(max(args.max_bytes, 64), MAX_PROC_BYTES)
        cmd_run(argv, timeout, max_bytes)


if __name__ == "__main__":
    main()
