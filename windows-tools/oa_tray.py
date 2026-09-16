"""Windows-only OA tray controller."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import webbrowser
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
        self._stop_event = threading.Event()

    def _image(self, color: str) -> Image.Image:
        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)
        draw.ellipse((10, 10, 54, 54), fill=color, outline="#333333", width=2)
        return image

    def _set_status(self, status: str, version: str = "") -> None:
        self.status = status
        self.version = version
        if self.icon:
            color = {
                "Running": "#22aa44",
                "Offline": "#cc3333",
                "Restarting": "#e09b20",
                "Building Frontend": "#e09b20",
            }.get(status, "#777777")
            self.icon.icon = self._image(color)
            self.icon.title = f"OA {status}" + (f" ({version})" if version else "")
            self.icon.update_menu()

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
            if not self.busy:
                healthy, version = self._health_check()
                self._set_status("Running" if healthy else "Offline", version)
            self._stop_event.wait(10)

    def _open_file(self, path: Path) -> None:
        if path.exists():
            os.startfile(str(path))

    def _run_restart(self) -> None:
        try:
            result = restart_backend()
            self._set_status("Running" if result.get("success") else "Offline")
        finally:
            self.busy = False
            self._operation_lock.release()

    def restart(self, icon: pystray.Icon, item: Any) -> None:
        if not self._operation_lock.acquire(blocking=False):
            return
        self.busy = True
        self._set_status("Restarting")
        threading.Thread(target=self._run_restart, daemon=True).start()

    def _run_build(self) -> None:
        FRONTEND_LOG.parent.mkdir(parents=True, exist_ok=True)
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
                    self._set_status("Running" if exit_code == 0 else "Offline")
                except Exception as exc:
                    log_handle.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] build failed: {exc}\n")
                    self._set_status("Offline")
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

    def status_text(self, item: Any) -> str:
        return f"状态：OA {self.status}" + (f" | {self.version}" if self.version else "")

    def run(self) -> None:
        self.icon = pystray.Icon(
            "Soonwin OA",
            self._image("#777777"),
            "OA Checking",
            pystray.Menu(
                pystray.MenuItem(self.status_text, None, enabled=False),
                pystray.MenuItem("打开 OA", lambda icon, item: webbrowser.open("http://127.0.0.1:5183/")),
                pystray.MenuItem("重启 Backend", self.restart),
                pystray.MenuItem("构建 Frontend", self.build),
                pystray.MenuItem("打开 Backend 日志", lambda icon, item: self._open_file(BACKEND_LOG)),
                pystray.MenuItem("打开 Frontend Build 日志", lambda icon, item: self._open_file(FRONTEND_LOG)),
                pystray.MenuItem("打开 Nginx Error 日志", lambda icon, item: self._open_file(NGINX_ERROR_LOG)),
                pystray.MenuItem("退出托盘", lambda icon, item: self._stop_tray()),
            ),
        )
        threading.Thread(target=self._status_loop, daemon=True).start()
        self.icon.run()

    def _stop_tray(self) -> None:
        self._stop_event.set()
        if self.icon:
            self.icon.stop()


if __name__ == "__main__":
    OATray().run()
