"""
Arc Store as an Arc Center widget.

This is the file that the "Move to Arc Center" switch in Arc Store copies to
/usr/share/arcos/widgets/. It is kept tiny on purpose and holds no
application logic: Arc Center reads the three widget values at the bottom of
this file as plain text to build its sidebar, then imports the file and
creates the widget. Everything real lives in /usr/share/arc-store (see
arc_store_hosting.py), so an Arc Store package update reaches the widget too
— the copy in Arc Center's folder is not something pacman keeps current.
"""

import os
import sys

_CANDIDATE_DIRS = (
    "/usr/share/arc-store",
    # Running from a source tree: .../share/arcos/widgets/<this file>
    # sits next to .../share/arc-store.
    os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "arc-store")),
)
_APP_DIR = next(
    (d for d in _CANDIDATE_DIRS if os.path.isfile(os.path.join(d, "arc_store_hosting.py"))),
    _CANDIDATE_DIRS[0],
)

# Only for the duration of the import: Arc Store's modules have generic
# names that must not shadow anything for the other widgets that Arc Center
# loads into the same process afterwards.
sys.path.insert(0, _APP_DIR)
try:
    import arc_store_hosting as _hosting
finally:
    try:
        sys.path.remove(_APP_DIR)
    except ValueError:
        pass


class ArcStoreWidget(_hosting.HostedArcStore):
    def __init__(self, hide_sidebar=False, window=None, **kwargs):
        # `sudo_manager` is not defined in this file: Arc Center injects its
        # own into this module right after importing it, and the view adopts it.
        super().__init__(hide_sidebar=hide_sidebar, window=window,
                         host_sudo=globals().get("sudo_manager"))
        self.widgetname = "Arc Store"
        self.widgeticon = "/usr/share/icons/hicolor/256x256/apps/github.zcharka.arcstore.png"
        self.widget_id = "arc_store"
