#!/usr/bin/env python3
"""Bounded I/O helper for the Z13 Power Omarchy plugin.

All file and subprocess access from the persistent shell goes through here:
regular-file reads with O_NOFOLLOW, atomic command.json writes, and
process-group-limited child runs with a wall-clock timeout and byte cap.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import stat
import subprocess
import sys
from pathlib import Path

MAX_FILE_BYTES = 16 * 1024
MAX_PROC_BYTES = 32 * 1024
MAX_COMMAND_BYTES = 2048
MAX_DIAGNOSE_BYTES = 32 * 1024
MAX_STATUS_STRING = 64
MAX_PROFILES = 16
DEFAULT_TIMEOUT = 3.0
DIAGNOSE_TIMEOUT = 8.0
HWMON_TIMEOUT = 2.0

STATE_DIR = Path.home() / ".local" / "state" / "z13-power"
STATUS_PATH = STATE_DIR / "status.json"
COMMAND_PATH = STATE_DIR / "command.json"
BATTERY_CONF = Path.home() / ".config" / "z13-power" / "battery.conf"

ALLOWED_RUN = {
    "omarchy-battery-status",
    "omarchy-powerprofiles-list",
    "omarchy-powerprofiles-set",
    "omarchy-system-stats",
    "omarchy-battery-low",
}

ALLOWED_BINS = {
    "z13-power",
    "z13-power-settings",
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


def fail(msg: str, code: int = 1) -> None:
    sys.stderr.write(msg + "\n")
    raise SystemExit(code)


def clamp_str(value: object, n: int = MAX_STATUS_STRING) -> str:
    s = str(value if value is not None else "")
    return s[:n]


def read_regular(path: Path, max_bytes: int) -> bytes:
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as e:
        fail(f"open failed: {e}")
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            fail("not a regular file")
        # Do not trust st_size: sysfs reports 4096 for tiny files.
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
    finally:
        os.close(fd)


def ensure_state_dir() -> int:
    """Return a directory fd for ~/.local/state/z13-power (private, owned)."""
    parent = STATE_DIR.parent
    os.makedirs(parent, mode=0o755, exist_ok=True)
    if not STATE_DIR.exists():
        try:
            os.mkdir(STATE_DIR, 0o700)
        except FileExistsError:
            pass
    try:
        dirfd = os.open(str(STATE_DIR), os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as e:
        fail(f"state dir open failed: {e}")
    try:
        st = os.fstat(dirfd)
        if not stat.S_ISDIR(st.st_mode):
            fail("state path is not a directory")
        if st.st_uid != os.getuid():
            fail("state dir not owned by the user")
        os.fchmod(dirfd, 0o700)
        return dirfd
    except Exception:
        os.close(dirfd)
        raise


def cmd_read_status() -> None:
    if not STATUS_PATH.exists():
        print("{}")
        return
    raw = read_regular(STATUS_PATH, MAX_FILE_BYTES)
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


def cmd_read_battery_conf() -> None:
    if not BATTERY_CONF.exists():
        print("{}")
        return
    raw = read_regular(BATTERY_CONF, MAX_FILE_BYTES)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("battery.conf is not UTF-8")
    limit = None
    for line in text.splitlines()[:32]:
        line = line.strip()
        if line.startswith("charge_limit"):
            _, _, rest = line.partition("=")
            rest = rest.strip()
            if rest.isdigit():
                n = int(rest)
                if 40 <= n <= 100:
                    limit = n
            break
    print(json.dumps({} if limit is None else {"charge_limit": limit}, separators=(",", ":")))


def cmd_write_command(payload: str) -> None:
    raw = payload.encode("utf-8")
    if len(raw) > MAX_COMMAND_BYTES:
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

    dirfd = ensure_state_dir()
    tmp_name = f".cmd.{os.getpid()}.{os.urandom(8).hex()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = None
    try:
        fd = os.open(tmp_name, flags, 0o600, dir_fd=dirfd)
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


def resolve_bin(name: str) -> str:
    if name not in ALLOWED_BINS:
        fail(f"binary not allowed: {name}")
    candidates = [
        Path.home() / ".local" / "bin" / name,
        Path("/usr/bin") / name,
    ]
    for path in candidates:
        try:
            fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        except OSError:
            continue
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                continue
            if st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) == 0:
                continue
            return str(path)
        finally:
            os.close(fd)
    fail(f"binary not found: {name}")


def cmd_resolve_bin(name: str) -> None:
    print(resolve_bin(name))


def kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass


def cmd_run(argv: list[str], timeout: float, max_bytes: int) -> None:
    if not argv:
        fail("run requires a command")
    prog = argv[0]
    if prog in ALLOWED_BINS:
        argv = [resolve_bin(prog)] + argv[1:]
        prog = argv[0]
    else:
        base = os.path.basename(prog)
        if base not in ALLOWED_RUN:
            fail(f"command not allowed: {base}")
        if os.path.sep in prog:
            fail("refusing a path for an omarchy helper")
    proc = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        close_fds=True,
    )
    try:
        stdout, _stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_group(proc)
        fail("timeout", 124)
    except Exception:
        kill_group(proc)
        raise
    out = stdout or b""
    if len(out) > max_bytes:
        out = out[:max_bytes]
    sys.stdout.buffer.write(out)


def cmd_read_hwmon() -> None:
    """Read amdgpu average power and temp with the same file constraints."""
    hwmon = Path("/sys/class/hwmon")
    if not hwmon.is_dir():
        print("{}")
        return
    watts = None
    temp_c = None
    try:
        names = list(os.listdir(hwmon))[:32]
    except OSError:
        print("{}")
        return
    for name in names:
        if not name.startswith("hwmon"):
            continue
        base = hwmon / name
        try:
            label = read_regular(base / "name", 64).decode("ascii", "ignore").strip()
        except SystemExit:
            continue
        if label != "amdgpu":
            continue
        for fname in ("power1_average", "power1_input"):
            try:
                raw = read_regular(base / fname, 32).decode("ascii", "ignore").strip()
                n = int(raw)
                if 0 < n < 10**12:
                    watts = int(round(n / 1_000_000))
                    break
            except (SystemExit, ValueError):
                continue
        try:
            raw = read_regular(base / "temp1_input", 32).decode("ascii", "ignore").strip()
            n = int(raw)
            if 0 < n < 200_000:
                temp_c = int(round(n / 1000))
        except (SystemExit, ValueError):
            pass
        break
    out = {}
    if watts is not None:
        out["watts"] = watts
    if temp_c is not None:
        out["temp_c"] = temp_c
    print(json.dumps(out, separators=(",", ":")))


def main() -> None:
    parser = argparse.ArgumentParser(prog="z13-io")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("read-status")
    sub.add_parser("read-battery-conf")
    sub.add_parser("read-hwmon")

    p_write = sub.add_parser("write-command")
    p_write.add_argument("payload")

    p_resolve = sub.add_parser("resolve-bin")
    p_resolve.add_argument("name")

    p_run = sub.add_parser("run")
    p_run.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    p_run.add_argument("--max-bytes", type=int, default=MAX_PROC_BYTES)
    p_run.add_argument("argv", nargs=argparse.REMAINDER)

    args = parser.parse_args()
    if args.cmd == "read-status":
        cmd_read_status()
    elif args.cmd == "read-battery-conf":
        cmd_read_battery_conf()
    elif args.cmd == "read-hwmon":
        cmd_read_hwmon()
    elif args.cmd == "write-command":
        cmd_write_command(args.payload)
    elif args.cmd == "resolve-bin":
        cmd_resolve_bin(args.name)
    elif args.cmd == "run":
        argv = args.argv
        if argv and argv[0] == "--":
            argv = argv[1:]
        timeout = min(max(args.timeout, 0.1), 15.0)
        max_bytes = min(max(args.max_bytes, 64), MAX_DIAGNOSE_BYTES)
        cmd_run(argv, timeout, max_bytes)


if __name__ == "__main__":
    main()
