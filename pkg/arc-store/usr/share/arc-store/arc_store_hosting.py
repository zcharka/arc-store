"""
arc_store_hosting.py — Arc Store as a widget inside Arc Center.

arc_store_widget.py (the small file that "Move to Arc Center" copies into
/usr/share/arcos/widgets/) imports this module and builds its widget class
on HostedArcStore below. Arc Center itself is never modified: it just scans
its widgets folder for *.py files, imports each, and instantiates the Gtk
widget classes it finds.

Three things about being a guest in someone else's process shape this file.

1. Name hygiene. Arc Store's own modules have short, generic top-level
   names (auth, i18n, theme, widgets, ...), because on its own it is the
   only thing in its process. Inside Arc Center those names could already
   belong to another widget — or be claimed by a later one. So the import
   below runs against a sys.modules with those names set aside, and puts
   everything back afterwards: Arc Store gets its own modules, and nobody
   else's get shadowed, replaced or leaked into. (The arc_store_widget.py
   that imports this also removes /usr/share/arc-store from sys.path again
   for the same reason.)

2. Threads. Arc Center imports widget modules in a *background* thread and
   only creates the widget on the main thread afterwards. Nothing at import
   time may therefore touch GTK; everything display-related happens in
   HostedArcStore.__init__.

3. One sudo manager. Arc Center already has one, and it locks its sidebar
   and window controls while a command runs through *its* wrapper script.
   Arc Store adopts that manager instead of making its own, so a package
   transaction started here gets the same protection as in any other widget.
"""

import gettext
import sys

# Every top-level module Arc Store ships next to this file.
_OWN_MODULES = (
    "package_manager", "arc_center_integration", "theme",
    "auth", "i18n", "widgets", "main",
)


def _is_own(name):
    return name.split(".", 1)[0] in _OWN_MODULES


_set_aside = {name: module for name, module in sys.modules.items() if _is_own(name)}
for _name in _set_aside:
    del sys.modules[_name]
# package_manager.py selects its own gettext text domain at import time; that
# is process-wide state, so hand it back exactly as it was found.
_text_domain = gettext.textdomain()
try:
    import package_manager as _package_manager
    import theme as _theme
    from auth import sudo_manager as _sudo_manager_module
finally:
    for _name in [n for n in sys.modules if _is_own(n)]:
        del sys.modules[_name]
    sys.modules.update(_set_aside)
    gettext.textdomain(_text_domain)
    globals().pop("_name", None)


class HostedArcStore(_package_manager.PackageManagerView):
    """The package manager view, adapted to live in Arc Center's content area."""

    is_hosted = True

    def __init__(self, hide_sidebar=False, window=None, host_sudo=None, **_ignored):
        # Arc Center also passes voice_autostart / conversation_id, which
        # mean nothing here; swallowing them lets its first attempt at
        # instantiating succeed, instead of failing with a TypeError and
        # being retried with fewer arguments.
        #
        # Before the view is built, so that nothing it sets up on the way
        # can touch (and so create) a second sudo manager.
        _sudo_manager_module.use_shared_manager(host_sudo)
        # Only the stylesheet the view needs — not theme.BASE_CSS, which
        # would restyle Arc Center's own header bars and sidebar.
        _theme.apply_hosted_css()
        super().__init__(hide_sidebar=hide_sidebar, window=window)
        self.set_hexpand(True)
        self.set_vexpand(True)
