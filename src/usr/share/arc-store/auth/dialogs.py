"""
auth/dialogs.py — the standard Adw.MessageDialog + Gtk.PasswordEntry prompt
that goes with SudoManager, plus a helper to lock the rest of the window
while a privileged operation is running.

package_manager.py ships its own equivalent of prompt_password() (see its
prompt_for_password method) because it needs per-action wording ("enter
your password to remove this package", etc.) — this module is the generic
version for any future screen that just needs a plain yes/no auth prompt.
"""

from gi.repository import Gtk, Adw

from .sudo_manager import get_sudo_manager


def prompt_password(parent_window, message: str, on_success, primary_label="Authenticate"):
    """Adw.MessageDialog + Gtk.PasswordEntry. on_success() only fires once
    sudo -S -v has accepted the entered password."""
    manager = get_sudo_manager()

    dialog = Adw.MessageDialog(heading="Authentication Required", body=message, transient_for=parent_window)
    dialog.add_response("cancel", "Cancel")
    dialog.add_response("go", primary_label)
    dialog.set_response_appearance("go", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_default_response("go")

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    entry = Gtk.PasswordEntry(placeholder_text="Password")
    box.append(entry)
    dialog.set_extra_child(box)

    def on_response(dlg, response):
        if response == "go":
            pwd = entry.get_text()
            if pwd and manager.validate_password(pwd):
                manager.set_password(pwd)
                on_success()
            else:
                err = Adw.MessageDialog(heading="Authentication Failed", body="Incorrect password.",
                                         transient_for=parent_window)
                err.add_response("ok", "OK")
                err.present()
        dlg.close()

    dialog.connect("response", on_response)
    entry.connect("activate", lambda *_: dialog.response("go"))
    dialog.present()


def set_ui_locked(window, content_widget, locked: bool):
    """Disable interaction with the rest of the window during a long-running
    privileged operation, and block the window from being closed out from
    under it. Pair with `widget:insensitive { opacity: 0.3; }` from theme.py."""
    content_widget.set_sensitive(not locked)
    if locked:
        window._block_id = window.connect("close-request", lambda *_: True)
    elif hasattr(window, "_block_id"):
        window.disconnect(window._block_id)
        del window._block_id
