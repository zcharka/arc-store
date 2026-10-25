"""
arc_center_integration.py — what "Move to Arc Center" does on disk.

No GTK in here; the switch itself and its dialogs live in
package_manager.py. This module is only the file work behind them:

  * put arc_store_widget.py (the small file Arc Center loads) into Arc
    Center's widgets folder, or take it out again — both need root, so they
    go through the SudoManager handed in by the caller;
  * hide Arc Store from the application menu while it lives in Arc Center,
    and bring it back when it moves out. That part is *per user* and needs
    no root: a copy of the system .desktop file with NoDisplay=true is
    dropped into ~/.local/share/applications, where it takes precedence
    over the system one for that user (the system file is never touched).

Nothing here touches Arc Center's own files or repository — Arc Center just
scans /usr/share/arcos/widgets/ for *.py files, and this adds one of them.
"""

import os
import shutil
import subprocess
import sys

WIDGETS_DIR = "/usr/share/arcos/widgets"
WIDGET_FILENAME = "arc_store_widget.py"
WIDGET_DEST = os.path.join(WIDGETS_DIR, WIDGET_FILENAME)

DESKTOP_FILENAME = "github.zcharka.arcstore.desktop"
SYSTEM_DESKTOP = os.path.join("/usr/share/applications", DESKTOP_FILENAME)


def user_applications_dir() -> str:
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(data_home, "applications")


def user_desktop_path() -> str:
    return os.path.join(user_applications_dir(), DESKTOP_FILENAME)


def widget_source() -> str:
    """The packaged copy of the widget file, next to this module."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), WIDGET_FILENAME)


def is_in_arc_center() -> bool:
    return os.path.isfile(WIDGET_DEST)


def _run_privileged(sudo, cmd):
    """(ok, error text) for one root command run through the SudoManager."""
    result = sudo.run_privileged(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return False, detail or f"{cmd[0]} exited with status {result.returncode}"
    return True, ""


def _refresh_desktop_database() -> None:
    tool = shutil.which("update-desktop-database")
    if not tool:
        return
    try:
        subprocess.run([tool, user_applications_dir()], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


def hide_launcher() -> None:
    """Write the NoDisplay=true override. Does nothing if the system
    .desktop file isn't there (e.g. when run straight from a source tree)."""
    if not os.path.isfile(SYSTEM_DESKTOP):
        return
    with open(SYSTEM_DESKTOP, encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    out, placed = [], False
    for line in lines:
        if line.strip().lower().startswith("nodisplay="):
            continue  # ours replaces whatever was there
        out.append(line)
        if not placed and line.strip() == "[Desktop Entry]":
            out.append("NoDisplay=true")
            placed = True
    if not placed:
        out.append("NoDisplay=true")

    os.makedirs(user_applications_dir(), exist_ok=True)
    with open(user_desktop_path(), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    _refresh_desktop_database()


def show_launcher() -> None:
    """Remove the override again — but only if it is ours (hides the app).
    Best effort: a menu entry that can't be restored must not turn a
    finished move into an error."""
    path = user_desktop_path()
    try:
        with open(path, encoding="utf-8") as fh:
            ours = any(line.strip().lower() == "nodisplay=true" for line in fh)
        if ours:
            os.remove(path)
            _refresh_desktop_database()
    except FileNotFoundError:
        pass
    except OSError as exc:
        print(f"arc-store: could not restore the menu entry: {exc}", file=sys.stderr)


def move_to_arc_center(sudo):
    """Deploy the widget, then hide the menu entry. -> (ok, error text)."""
    source = widget_source()
    if not os.path.isfile(source):
        return False, f"{source} not found"
    # One root command: creates the folder if need be, copies, sets the mode.
    ok, error = _run_privileged(sudo, ["install", "-Dm644", source, WIDGET_DEST])
    if not ok:
        return False, error
    try:
        hide_launcher()
    except OSError as exc:
        # Half a move would leave Arc Store in both places; undo the copy.
        _run_privileged(sudo, ["rm", "-f", WIDGET_DEST])
        return False, f"{exc}"
    return True, ""


def move_out_of_arc_center(sudo):
    """Remove the widget, then bring the menu entry back. -> (ok, error text)."""
    ok, error = _run_privileged(sudo, ["rm", "-f", WIDGET_DEST])
    if not ok:
        return False, error
    show_launcher()
    return True, ""
