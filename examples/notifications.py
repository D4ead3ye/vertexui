"""Click-through notifications over another application.

Run it, then click on any other window - the toasts keep drawing on top
and never steal focus.

    python examples/notifications.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vertexui import toasts  # noqa: E402

tray = toasts.Toasts(seconds=3.0, on_status=print)
tray.start()

for kind, text in (("ok", "Connected"),
                   ("info", "Syncing 240 files"),
                   ("warn", "Retrying after timeout"),
                   ("error", "Write failed: device busy")):
    tray.notify(kind, text)
    time.sleep(1.2)

time.sleep(4)
tray.stop()
