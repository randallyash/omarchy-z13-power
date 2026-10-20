#!/usr/bin/python3
"""Security checks for the Z13 Omarchy plugin helper.

The helper must run as /usr/bin/python3, talk only to a root-owned
z13-power 1.4.1+, and refuse z13ctl plus any other command.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

PY = "/usr/bin/python3"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IO = os.path.join(ROOT, "z13-io.py")


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PY, IO, *args],
        text=True,
        capture_output=True,
        timeout=8,
        env={**os.environ, "PATH": "/usr/bin"},
    )


def check(name: str, ok: bool, detail: str = "") -> None:
    if not ok:
        raise SystemExit(f"FAIL {name}: {detail}")
    print(f"ok {name}")


def main() -> None:
    src = open(IO, encoding="utf-8").read()
    # The failure text may say z13ctl is not used. It must not name a binary to run.
    named = src.replace("/usr/bin/z13ctl is not used", "")
    check(
        "no z13ctl exec",
        "require_z13ctl" not in src
        and "Z13CTL_PATH" not in src
        and "Z13CTL_MIN" not in src
        and "/usr/bin/z13ctl" not in named,
    )
    check("no digest pin", "sha256" not in src and "require_pinned" not in src)
    check("trusted interpreter gate", "interpreter is not trusted /usr/bin/python3" in src)
    for name in ("Panel.qml", "Z13PowerPanel.qml", "Service.qml"):
        qml = open(os.path.join(ROOT, name), encoding="utf-8").read()
        check(f"{name} uses /usr/bin/python3", '"/usr/bin/python3"' in qml and '"python3"' not in qml)

    panel = open(os.path.join(ROOT, "Z13PowerPanel.qml"), encoding="utf-8").read()
    check("flyout offers setup", "Install backend" in panel and "xdg-terminal-exec" in panel)
    setup = open(os.path.join(ROOT, "setup.sh"), encoding="utf-8").read()
    check(
        "setup pins backend and skips z13ctl",
        "d1c26524e64e2946559812f06f235fc1e613ae44" in setup
        and "lock-smu-sysfs" in setup
        and "lock-power-sysfs" in setup
        and "chmod a+w" not in setup
        and "chgrp users" not in setup
        and "z13-power-omarchy-setup" not in setup
        and "z13ctl is not used" in setup
        and "/usr/bin/z13ctl" not in setup,
    )

    deps = run(["check-deps"])
    check("check-deps exits 0", deps.returncode == 0, deps.stderr)
    body = json.loads(deps.stdout)
    check("z13ctl not used", body["z13-power"]["z13ctl"] == "not used", deps.stdout)
    check("backend 1.4", "1.4" in body["z13-power"]["version"], deps.stdout)

    ver = run(["run", "--", "z13-power", "--version"])
    check("run version", ver.returncode == 0 and ver.stdout.strip().startswith("z13-power 1.4"), ver.stderr or ver.stdout)

    denied = run(["run", "--", "z13ctl", "--version"])
    check("z13ctl command refused", denied.returncode != 0 and "not allowed" in denied.stderr, denied.stderr)

    bad = run(["write-command", '{"op":"shell"}'])
    check("bad op refused", bad.returncode != 0 and "invalid command op" in bad.stderr, bad.stderr)

    huge = run(["write-command", "x" * 5000])
    check("oversize payload refused", huge.returncode != 0, huge.stderr)

    status = run(["read-status"])
    check("read-status", status.returncode == 0 and status.stdout.strip().startswith("{"), status.stderr)
    parsed = json.loads(status.stdout)
    check("status stays quiet", parsed.get("mode") == "silent" and parsed.get("profile") == "quiet", status.stdout)

    print("security tests passed")


if __name__ == "__main__":
    main()
