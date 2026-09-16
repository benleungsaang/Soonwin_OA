"""In-process schedule helper for the Windows OA Tray."""

from __future__ import annotations

from datetime import datetime


SCHEDULED_TIMES = ((7, 30), (12, 5), (18, 0))


class BackupScheduler:
    def __init__(self, submit_backup) -> None:
        self._submit_backup = submit_backup
        self._claimed_slots: set[str] = set()

    def poll(self, now: datetime | None = None) -> bool:
        """Claim at most one current minute; never catch up missed minutes."""
        current = now or datetime.now()
        if (current.hour, current.minute) not in SCHEDULED_TIMES:
            return False
        slot = current.strftime("%Y-%m-%d %H:%M")
        if slot in self._claimed_slots:
            return False
        self._claimed_slots.add(slot)
        self._submit_backup(True)
        return True
