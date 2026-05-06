"""GTK-free helpers for child PID visibility and subprocess liveness.

Used by ``linux-wallpaperengine-gtk.py`` and exercised by pytest without PyGObject.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Callable, Optional


def pid_exists(pid: int) -> bool:
    """Return True if ``pid`` exists in this kernel namespace.

    Uses ``/proc/<pid>`` on Linux (no signals). Else ``os.kill(pid, 0)``.
    On ``PermissionError`` for ``kill(0)``, returns False so wait-loops do not spin forever.
    """
    if pid <= 0:
        return False
    if sys.platform.startswith("linux"):
        return os.path.isdir(os.path.join("/proc", str(pid)))
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return False


def wallpaper_subprocess_running(
    process: subprocess.Popen,
    *,
    on_kill_permission_denied: Optional[Callable[[], None]] = None,
) -> bool:
    """True if ``process`` has no exit code yet and the kernel still shows a live PID.

    Uses ``poll()`` (reap + exit status) and ``/proc`` on Linux or ``kill(0)`` elsewhere.
    No wall-clock delay: evidence-only, same contract as the former post-``Popen`` check.
    """
    rc = process.poll()
    if rc is not None:
        return False
    pid = process.pid
    if sys.platform.startswith("linux"):
        proc_dir = os.path.join("/proc", str(pid))
        if not os.path.isdir(proc_dir):
            process.poll()
            return False
        # Second non-blocking reap: narrows fork/exec vs instant-exit races where the
        # first poll() has not yet observed a zombie the kernel has already retired.
        rc = process.poll()
        if rc is not None:
            return False
        return True
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        if on_kill_permission_denied:
            on_kill_permission_denied()
        return True
