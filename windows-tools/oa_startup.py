"""Windows-only idempotent startup launcher for the temporary OA host."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from oa_backend_controller import (
    ROOT_DIR,
    _listening_pids,
    _process_info,
    _hidden_creation_kwargs,
    start_backend,
)


NGINX_DIR = ROOT_DIR / "nginx-1.28.1"
NGINX_EXE = NGINX_DIR / "nginx.exe"
NGINX_CONF = NGINX_DIR / "conf" / "nginx.conf"
NGINX_LOG = ROOT_DIR / "windows-tools" / "nginx-startup.log"
TRAY_SCRIPT = ROOT_DIR / "windows-tools" / "oa_tray.py"


def _log(message: str) -> None:
    NGINX_LOG.parent.mkdir(parents=True, exist_ok=True)
    with NGINX_LOG.open("a", encoding="utf-8", buffering=1) as handle:
        handle.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


def _find_project_nginx() -> tuple[int | None, str]:
    pids = _listening_pids(5183)
    if not pids:
        return None, "no process is listening on port 5183"
    expected = str(NGINX_EXE).lower().replace("/", "\\")
    unknown: list[str] = []
    for pid in pids:
        info = _process_info(pid)
        if not info:
            unknown.append(f"PID {pid}: process details unavailable")
            continue
        name = str(info.get("Name") or "").lower()
        executable = str(info.get("ExecutablePath") or "").lower().replace("/", "\\")
        command = str(info.get("CommandLine") or "").lower().replace("/", "\\")
        if name == "nginx.exe" and (executable == expected or expected in command):
            return pid, "project nginx executable confirmed"
        unknown.append(f"PID {pid}: not the project nginx executable")
    return None, "; ".join(unknown) or "ownership unknown"


def _start_project_nginx() -> tuple[bool, str]:
    if os.name != "nt":
        return False, "Windows-only startup launcher"
    if not NGINX_EXE.exists() or not NGINX_CONF.exists():
        return False, f"project nginx files missing: {NGINX_EXE} / {NGINX_CONF}"
    log_handle = NGINX_LOG.open("a", encoding="utf-8", buffering=1)
    try:
        subprocess.Popen(
            [str(NGINX_EXE), "-c", str(NGINX_CONF)],
            cwd=str(NGINX_DIR),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            close_fds=True,
            **_hidden_creation_kwargs(),
        )
    except Exception as exc:
        log_handle.close()
        return False, f"project nginx start failed: {exc}"
    finally:
        log_handle.close()
    for _ in range(20):
        pid, reason = _find_project_nginx()
        if pid is not None:
            return True, f"project nginx started PID={pid}"
        time.sleep(0.25)
    return False, "project nginx did not listen on 5183"


def ensure_backend() -> tuple[bool, str]:
    result = start_backend()
    return bool(result.get("success")), str(result.get("message", "Backend start failed"))


def ensure_nginx() -> tuple[bool, str]:
    pid, reason = _find_project_nginx()
    if pid is not None:
        return True, f"project Nginx already running PID={pid}"
    if _listening_pids(5183):
        return False, f"port 5183 ownership unknown: {reason}"
    return _start_project_nginx()


def _tray_executable() -> str:
    current = Path(sys.executable)
    pythonw = current.with_name("pythonw.exe")
    return str(pythonw if pythonw.exists() else current)


def _tray_is_running() -> bool:
    if os.name != "nt":
        return False
    import ctypes

    synchronize = 0x00100000
    handle = ctypes.windll.kernel32.OpenMutexW(
        synchronize, False, "Global\\SoonwinOA_Tray_SingleInstance"
    )
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def launch_tray() -> tuple[bool, str]:
    if not TRAY_SCRIPT.exists():
        return False, f"Tray script missing: {TRAY_SCRIPT}"
    if _tray_is_running():
        return True, "Tray already running; no second Tray launched"
    try:
        subprocess.Popen(
            [_tray_executable(), str(TRAY_SCRIPT)],
            cwd=str(ROOT_DIR),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            **_hidden_creation_kwargs(),
        )
        return True, "Tray launch submitted; single-instance guard is enforced by Tray"
    except Exception as exc:
        return False, f"Tray launch failed: {exc}"


def main() -> int:
    if os.name != "nt":
        print("FAILED: Windows-only startup launcher")
        return 1
    backend_ok, backend_message = ensure_backend()
    _log(f"Backend: {backend_message}")
    if not backend_ok:
        return 1
    nginx_ok, nginx_message = ensure_nginx()
    _log(f"Nginx: {nginx_message}")
    if not nginx_ok:
        return 1
    tray_ok, tray_message = launch_tray()
    _log(f"Tray: {tray_message}")
    return 0 if tray_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
