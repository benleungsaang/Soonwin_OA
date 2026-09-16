"""Windows-only controller for the production Waitress process.

This module deliberately does not call run_server.py, restart_services.py,
Windows Services, or the Nginx process.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "soonwin-os-Python-Server"
BACKEND_LOG = BACKEND_DIR / "backend.log"
PID_FILE = BACKEND_DIR / "windows-waitress.pid"
WAITRESS_EXE = BACKEND_DIR / "venv" / "Scripts" / "waitress-serve.exe"
BACKEND_URL = "http://127.0.0.1:5000/api/version"
PRODUCTION_URL = "http://127.0.0.1:5183/api/version"


def _log(message: str) -> None:
    BACKEND_LOG.parent.mkdir(parents=True, exist_ok=True)
    with BACKEND_LOG.open("a", encoding="utf-8", buffering=1) as handle:
        handle.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


def _powershell_json(script: str) -> Any:
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _list_listening_pids() -> list[int]:
    value = _powershell_json(
        "Get-NetTCPConnection -State Listen -LocalPort 5000 "
        "-ErrorAction SilentlyContinue | "
        "Select-Object -ExpandProperty OwningProcess | "
        "Sort-Object -Unique | ConvertTo-Json -Compress"
    )
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [int(item) for item in values if str(item).isdigit()]


def _process_info(pid: int) -> dict[str, Any] | None:
    value = _powershell_json(
        f"Get-CimInstance Win32_Process -Filter 'ProcessId={pid}' | "
        "Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine | "
        "ConvertTo-Json -Compress"
    )
    return value if isinstance(value, dict) else None


def _parent_chain(pid: int, limit: int = 8) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    current = _process_info(pid)
    for _ in range(limit):
        if not current:
            break
        chain.append(current)
        parent_pid = current.get("ParentProcessId")
        if not str(parent_pid).isdigit() or int(parent_pid) in (0, current.get("ProcessId")):
            break
        current = _process_info(int(parent_pid))
    return chain


def _command_is_waitress(info: dict[str, Any]) -> bool:
    command = str(info.get("CommandLine") or "").lower()
    name = str(info.get("Name") or "").lower()
    return (
        name in {"python.exe", "pythonw.exe", "waitress-serve.exe"}
        and "wsgi:application" in command
        and "waitress" in command
        and ("--port=5000" in command or "--port 5000" in command)
    )


def _is_project_waitress(pid: int, info: dict[str, Any]) -> tuple[bool, str]:
    if not _command_is_waitress(info):
        return False, "process command is not the production Waitress command"

    recorded_pid = None
    if PID_FILE.exists():
        try:
            recorded_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            recorded_pid = None
    if recorded_pid == pid:
        return True, "matches controller PID file and Waitress command"

    backend_marker = str(BACKEND_DIR).lower().replace("/", "\\")
    for parent in _parent_chain(pid):
        parent_command = str(parent.get("CommandLine") or "").lower().replace("/", "\\")
        if backend_marker in parent_command:
            return True, "Waitress command has a process ancestor rooted at the project backend"

    return False, "Waitress command ownership could not be tied to this project"


def find_project_waitress() -> tuple[int | None, str]:
    candidates = _list_listening_pids()
    if not candidates:
        return None, "no process is listening on port 5000"
    unknown: list[str] = []
    for pid in candidates:
        info = _process_info(pid)
        if not info:
            unknown.append(f"PID {pid}: process details unavailable")
            continue
        owned, reason = _is_project_waitress(pid, info)
        if owned:
            return pid, reason
        unknown.append(f"PID {pid}: {reason}")
    return None, "; ".join(unknown) or "ownership unknown"


def _port_is_free() -> bool:
    return not _listening_pids()


def _wait_until(predicate, timeout: float, interval: float = 0.25) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


def _http_json(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        request = Request(url, method="GET")
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            if response.status != 200:
                return False, f"HTTP {response.status}: {body[:200]}"
            return True, body[:500]
    except (OSError, URLError, TimeoutError) as exc:
        return False, str(exc)


def _hidden_creation_kwargs() -> dict[str, Any]:
    if os.name != "nt":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
        "startupinfo": startupinfo,
    }


def _terminate_owned_waitress(pid: int) -> tuple[bool, str]:
    info = _process_info(pid)
    if not info:
        return False, "process details unavailable before termination"
    owned, reason = _is_project_waitress(pid, info)
    if not owned:
        return False, f"ownership check failed: {reason}"
    result = subprocess.run(
        ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    if result.returncode != 0:
        return False, result.stderr.strip() or result.stdout.strip() or "taskkill failed"
    if not _wait_until(lambda: _process_info(pid) is None, 15):
        return False, f"old PID {pid} did not exit"
    if not _wait_until(_port_is_free, 10):
        return False, "port 5000 was not released"
    return True, f"old PID {pid} stopped and port 5000 released"


def _start_waitress() -> tuple[bool, str]:
    if os.name != "nt":
        return False, "Windows-only controller"
    if not WAITRESS_EXE.exists():
        return False, f"missing Waitress executable: {WAITRESS_EXE}"
    if not BACKEND_DIR.exists():
        return False, f"missing backend directory: {BACKEND_DIR}"

    log_handle = BACKEND_LOG.open("a", encoding="utf-8", buffering=1)
    try:
        command = [
            str(WAITRESS_EXE),
            "--host=0.0.0.0",
            "--port=5000",
            "wsgi:application",
        ]
        process = subprocess.Popen(
            command,
            cwd=str(BACKEND_DIR),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            close_fds=True,
            **_hidden_creation_kwargs(),
        )
    except Exception as exc:
        log_handle.close()
        return False, f"start failed: {exc}"
    finally:
        if "process" in locals():
            log_handle.close()

    PID_FILE.write_text(str(process.pid), encoding="utf-8")
    _log(f"started Waitress PID={process.pid} command=waitress-serve --host=0.0.0.0 --port=5000 wsgi:application")
    if not _wait_until(lambda: _http_json(BACKEND_URL, 1.5)[0], 20):
        return False, "new Waitress did not return HTTP 200 on 5000/api/version"
    return True, f"new Waitress PID {process.pid} is healthy"


def restart_backend() -> dict[str, Any]:
    """Restart only the project Waitress process and verify both HTTP paths."""
    _log("backend restart requested")
    old_pid, ownership = find_project_waitress()
    if old_pid is None:
        message = f"FAILED / ownership unknown: {ownership}"
        _log(message)
        return {"success": False, "status": "ownership_unknown", "message": message}

    stopped, stop_message = _terminate_owned_waitress(old_pid)
    if not stopped:
        _log(f"FAILED: {stop_message}")
        return {"success": False, "status": "stop_failed", "message": stop_message}

    started, start_message = _start_waitress()
    if not started:
        _log(f"FAILED: {start_message}")
        return {"success": False, "status": "start_failed", "message": start_message}

    production_ok, production_message = _http_json(PRODUCTION_URL, 3.0)
    if not production_ok:
        message = f"FAILED: production health check failed: {production_message}"
        _log(message)
        return {"success": False, "status": "production_health_failed", "message": message}

    message = f"SUCCESS: {stop_message}; {start_message}; production health OK"
    _log(message)
    return {"success": True, "status": "success", "message": message}


if __name__ == "__main__":
    print(json.dumps(restart_backend(), ensure_ascii=False))
