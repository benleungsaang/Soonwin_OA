"""Windows-only OA tray controller."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover - depends on the Windows host
    raise SystemExit(
        "缺少 Tray 依赖，请先执行: py -3 -m pip install -r windows-tools\\requirements.txt"
    ) from exc

from oa_backend_controller import BACKEND_LOG, ROOT_DIR, restart_backend
from oa_backup_scheduler import BackupScheduler
from oa_database_backup import BackupResult, backup_database


FRONTEND_DIR = ROOT_DIR / "soonwin-oa-VUE-FrontEnd"
FRONTEND_LOG = FRONTEND_DIR / "frontend-build.log"
NGINX_ERROR_LOG = ROOT_DIR / "nginx-1.28.1" / "logs" / "error.log"
PRODUCTION_URL = "http://127.0.0.1:5183/api/version"


class OATray:
    def __init__(self) -> None:
        self.icon: pystray.Icon | None = None
        self.status = "Checking"
        self.version = ""
        self.busy = False
        self._operation_lock = threading.Lock()
        self._backup_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._backup_scheduler = BackupScheduler(self._submit_backup)
        self.last_health_check: datetime | None = None
        self.last_backup: BackupResult | None = None
        self._tray_mutex = None
        self._busy_animation_stop = threading.Event()
        self._busy_animation_thread: threading.Thread | None = None
        self._last_menu_signature: tuple[str, str, str] | None = None
        self._status_colors = {
            "Checking": ("#455A64", "#CFD8DC"),
            "Running": ("#00C853", "#B9F6CA"),
            "Offline": ("#D50000", "#FFCDD2"),
            "Restarting": ("#FF6D00", "#FFF176"),
            "Building Frontend": ("#FF6D00", "#FFF176"),
        }

    def _image(self, color: str) -> Image.Image:
        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.ellipse((10, 10, 54, 54), fill=color, outline="#333333", width=2)
        return image

    def _notify(self, message: str, title: str = "Soonwin OA") -> None:
        if not self.icon:
            return
        try:
            self.icon.notify(message, title)
        except Exception:
            pass

    def _start_busy_animation(self) -> None:
        if self._busy_animation_thread and self._busy_animation_thread.is_alive():
            return
        self._busy_animation_stop.clear()
        self._busy_animation_thread = threading.Thread(
            target=self._busy_animation_loop,
            name="oa-tray-busy-animation",
            daemon=True,
        )
        self._busy_animation_thread.start()

    def _stop_busy_animation(self) -> None:
        self._busy_animation_stop.set()
        thread = self._busy_animation_thread
        self._busy_animation_thread = None
        if thread and thread is not threading.current_thread():
            thread.join(timeout=1.2)

    def _busy_animation_loop(self) -> None:
        index = 0
        while True:
            interval = 1.2 if self.status == "Running" else 0.65
            if self._busy_animation_stop.wait(interval):
                break
            if not self.icon:
                continue
            colors = self._status_colors.get(self.status, ("#424242", "#E0E0E0"))
            self.icon.icon = self._image(colors[index])
            index = 1 - index

    def _menu_signature(self) -> tuple[str, str, str]:
        if self.last_backup is None:
            backup_state = "None"
        elif self.last_backup.success:
            backup_state = self.last_backup.finished_at.strftime("%Y-%m-%d %H:%M")
        else:
            backup_state = "Failed"
        return self.status, self.version, backup_state

    def _update_menu_if_needed(self) -> None:
        if not self.icon:
            return
        signature = self._menu_signature()
        if signature == self._last_menu_signature:
            return
        self._last_menu_signature = signature
        self.icon.update_menu()

    def _set_status(self, status: str, version: str = "") -> None:
        self.status = status
        self.version = version
        self._start_busy_animation()
        if self.icon:
            colors = self._status_colors.get(status, ("#424242", "#E0E0E0"))
            self.icon.icon = self._image(colors[0])
            last_check = self.last_health_check.strftime("%H:%M") if self.last_health_check else "None"
            if self.last_backup is None:
                last_backup = "None"
            elif self.last_backup.success:
                last_backup = self.last_backup.finished_at.strftime("%H:%M")
            else:
                last_backup = "Failed"
            self.icon.title = (
                f"Soonwin OA\n{status}"
                + (f" · v{version}" if version else "")
                + f"\nLast check: {last_check}\nLast backup: {last_backup}"
            )
            self._update_menu_if_needed()

    def _health_check(self) -> tuple[bool, str]:
        try:
            request = Request(PRODUCTION_URL, method="GET")
            with urlopen(request, timeout=3) as response:
                body = response.read().decode("utf-8", errors="replace")
                if response.status != 200:
                    return False, ""
                try:
                    version = str(json.loads(body).get("version", ""))
                except (TypeError, ValueError):
                    version = ""
                return True, version
        except (OSError, URLError, TimeoutError):
            return False, ""

    def _status_loop(self) -> None:
        while not self._stop_event.is_set():
            healthy, version = self._health_check()
            self.last_health_check = datetime.now()
            if not self.busy:
                self._set_status("Running" if healthy else "Offline", version)
            else:
                self._set_status(self.status, version or self.version)
            self._stop_event.wait(10)

    def _backup_loop(self) -> None:
        while not self._stop_event.is_set():
            self._backup_scheduler.poll()
            self._stop_event.wait(20)

    def _open_file(self, path: Path) -> None:
        if path.exists():
            os.startfile(str(path))

    def _run_restart(self) -> None:
        try:
            result = restart_backend()
            self._set_status("Running" if result.get("success") else "Offline")
            self._notify(
                "Backend restarted successfully"
                if result.get("success")
                else f"Backend restart failed: {result.get('message', 'unknown error')}"
            )
        finally:
            self.busy = False
            self._operation_lock.release()

    def _submit_backup(self, scheduled: bool = False) -> None:
        if not self._backup_lock.acquire(blocking=False):
            self.last_backup = BackupResult(False, None, "backup already running", datetime.now())
            self._set_status(self.status)
            return
        threading.Thread(target=self._run_backup, args=(scheduled,), daemon=True).start()

    def _run_backup(self, scheduled: bool = False) -> None:
        try:
            self.last_backup = backup_database()
            self._set_status(self.status)
            if not scheduled:
                self._notify(
                    "Database backup completed"
                    if self.last_backup.success
                    else f"Database backup failed: {self.last_backup.message}"
                )
        finally:
            self._backup_lock.release()

    def backup(self, icon: pystray.Icon, item: Any) -> None:
        self._submit_backup(False)

    def last_backup_text(self, item: Any) -> str:
        if self.last_backup is None:
            return "Last backup: None"
        if self.last_backup.success:
            return "Last backup: " + self.last_backup.finished_at.strftime("%Y-%m-%d %H:%M") + " \u2713"
        return "Last backup: Failed"
        if self.last_backup is None:
            value = "None"
        elif self.last_backup.success:
            value = self.last_backup.finished_at.strftime("%Y-%m-%d %H:%M") + " ✓"
        elif self.last_backup is not None and self.last_backup.success:
            value = self.last_backup.finished_at.strftime("%Y-%m-%d %H:%M") + "\u2713"
        else:
            value = "Failed"
        return f"Last backup: {value}"

    def restart(self, icon: pystray.Icon, item: Any) -> None:
        if not self._operation_lock.acquire(blocking=False):
            return
        self.busy = True
        self._set_status("Restarting")
        threading.Thread(target=self._run_restart, daemon=True).start()

    def _run_build(self) -> None:
        FRONTEND_LOG.parent.mkdir(parents=True, exist_ok=True)
        success = False
        failure_message = "unknown error"
        try:
            with FRONTEND_LOG.open("a", encoding="utf-8", buffering=1) as log_handle:
                log_handle.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] build:prod started\n")
                try:
                    process = subprocess.Popen(
                        ["yarn.cmd", "build:prod"],
                        cwd=str(FRONTEND_DIR),
                        stdin=subprocess.DEVNULL,
                        stdout=log_handle,
                        stderr=subprocess.STDOUT,
                        close_fds=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        startupinfo=self._startupinfo(),
                    )
                    exit_code = process.wait()
                    log_handle.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] exit_code={exit_code}\n")
                    success = exit_code == 0
                    if not success:
                        failure_message = f"exit code {exit_code}"
                    self._set_status("Running" if exit_code == 0 else "Offline")
                except Exception as exc:
                    failure_message = str(exc)
                    log_handle.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] build failed: {exc}\n")
                    self._set_status("Offline")
            self._notify(
                "Frontend build completed"
                if success
                else f"Frontend build failed: {failure_message}"
            )
        finally:
            self.busy = False
            self._operation_lock.release()

    @staticmethod
    def _startupinfo() -> subprocess.STARTUPINFO:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo

    def build(self, icon: pystray.Icon, item: Any) -> None:
        if not self._operation_lock.acquire(blocking=False):
            return
        self.busy = True
        self._set_status("Building Frontend")
        threading.Thread(target=self._run_build, daemon=True).start()

    def _acquire_single_instance(self) -> bool:
        if os.name != "nt":
            return True
        import ctypes

        self._tray_mutex = ctypes.windll.kernel32.CreateMutexW(
            None, False, "Global\\SoonwinOA_Tray_SingleInstance"
        )
        if not self._tray_mutex:
            return False
        if ctypes.windll.kernel32.GetLastError() == 183:
            ctypes.windll.kernel32.CloseHandle(self._tray_mutex)
            self._tray_mutex = None
            return False
        return True

    def status_text(self, item: Any) -> str:
        last_check = self.last_health_check.strftime("%H:%M") if self.last_health_check else "None"
        return (
            f"OA {self.status}"
            + (f" | v{self.version}" if self.version else "")
            + f" | Last check: {last_check}"
        )
        return f"状态：OA {self.status}" + (f" | {self.version}" if self.version else "")

    def version_text(self, item: Any) -> str:
        return f"Version: {self.version or 'None'}"

    def health_text(self, item: Any) -> str:
        value = self.last_health_check.strftime("%H:%M") if self.last_health_check else "None"
        return f"Last check: {value}"

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(self.status_text, None, enabled=False),
            pystray.MenuItem(self.version_text, None, enabled=False),
            pystray.MenuItem(self.health_text, None, enabled=False),
            pystray.MenuItem(self.last_backup_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("\u6253\u5f00 OA", lambda icon, item: webbrowser.open("http://127.0.0.1:5183/")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("\u91cd\u542f Backend", self.restart),
            pystray.MenuItem("\u6784\u5efa Frontend", self.build),
            pystray.MenuItem("\u7acb\u5373\u5907\u4efd\u6570\u636e\u5e93", self.backup),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("\u6253\u5f00 Backend \u65e5\u5fd7", lambda icon, item: self._open_file(BACKEND_LOG)),
            pystray.MenuItem("\u6253\u5f00 Frontend Build \u65e5\u5fd7", lambda icon, item: self._open_file(FRONTEND_LOG)),
            pystray.MenuItem("\u6253\u5f00 Nginx Error \u65e5\u5fd7", lambda icon, item: self._open_file(NGINX_ERROR_LOG)),
            pystray.MenuItem("\u6253\u5f00\u5907\u4efd\u76ee\u5f55", lambda icon, item: self._open_file(self._backup_dir())),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("\u9000\u51fa\u6258\u76d8", lambda icon, item: self._stop_tray()),
        )

    def run(self) -> None:
        if not self._acquire_single_instance():
            return
        self.icon = pystray.Icon(
            "Soonwin OA",
            self._image("#777777"),
            "OA Checking",
            pystray.Menu(
                pystray.MenuItem(self.status_text, None, enabled=False),
                pystray.MenuItem(self.last_backup_text, None, enabled=False),
                pystray.MenuItem("Backup database now", self.backup),
                pystray.MenuItem("Open backup directory", lambda icon, item: self._open_file(self._backup_dir())),
                pystray.MenuItem("打开 OA", lambda icon, item: webbrowser.open("http://127.0.0.1:5183/")),
                pystray.MenuItem("重启 Backend", self.restart),
                pystray.MenuItem("构建 Frontend", self.build),
                pystray.MenuItem("打开 Backend 日志", lambda icon, item: self._open_file(BACKEND_LOG)),
                pystray.MenuItem("打开 Frontend Build 日志", lambda icon, item: self._open_file(FRONTEND_LOG)),
                pystray.MenuItem("打开 Nginx Error 日志", lambda icon, item: self._open_file(NGINX_ERROR_LOG)),
                pystray.MenuItem("退出托盘", lambda icon, item: self._stop_tray()),
            ),
        )
        self.icon.menu = self._build_menu()
        self.icon.update_menu()
        self._start_busy_animation()
        threading.Thread(target=self._status_loop, daemon=True).start()
        threading.Thread(target=self._backup_loop, daemon=True).start()
        self.icon.run()
        self._stop_event.set()
        self._stop_busy_animation()

    @staticmethod
    def _backup_dir() -> Path:
        return ROOT_DIR / "windows-backup" / "database"

    def _stop_tray(self) -> None:
        self._stop_event.set()
        self._stop_busy_animation()
        if self.icon:
            self.icon.stop()


if __name__ == "__main__":
    OATray().run()
