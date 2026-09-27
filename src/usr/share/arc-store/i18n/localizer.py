"""
i18n/localizer.py — Arc Store's translation layer: a plain Python-dict
table per language (see locales/<lang>/strings.py), applied with no
compile/msgfmt step.

package_manager.py binds this module's ``tr`` function as its ``_()`` —
so every ``_("some string")`` call in the app, not just dialogs, looks
itself up here. (`gettext` is still initialized alongside it for anyone
who later wants to add a real compiled .po/.mo catalog, but since none
ships today, routing through this table is what actually makes the app
show Polish text at all today.)

``translate_dialog()`` is a second, narrower use of the same table: it
re-checks an Adw.MessageDialog's already-built heading/body/buttons right
before it's shown, which matters for the handful of dialogs that assemble
their text from a runtime value rather than a single ``_()`` call.

Included out of the box: a pl_PL table (see locales/pl_PL/strings.py). It
activates automatically when the system locale is Polish.
"""

import os
import locale
import importlib.util
from pathlib import Path

from gi.repository import Gtk

LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")


class Localizer:
    def __init__(self, locales_dir: str, fallback_lang="en_US"):
        self.fallback_lang = fallback_lang
        lang = locale.getlocale()[0] or os.environ.get("LANG", "")
        self.lang = lang.split(".")[0] if lang else fallback_lang
        self.tables = {}
        locales_path = Path(locales_dir)
        if locales_path.is_dir():
            for lang_dir in locales_path.iterdir():
                f = lang_dir / "strings.py"
                if lang_dir.is_dir() and f.exists():
                    spec = importlib.util.spec_from_file_location(f"strings_{lang_dir.name}", f)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.tables[lang_dir.name] = getattr(module, "translations", {})

    def tr(self, key: str) -> str:
        for lang in (self.lang, self.fallback_lang):
            if key in self.tables.get(lang, {}):
                return self.tables[lang][key]
        return key


_default_localizer = None


def get_localizer() -> Localizer:
    global _default_localizer
    if _default_localizer is None:
        _default_localizer = Localizer(LOCALES_DIR)
    return _default_localizer


def tr(key: str) -> str:
    """Shorthand for get_localizer().tr(key). Bind this as `_` anywhere
    you want plain-string translation with no .mo compilation step —
    package_manager.py does `from i18n.localizer import tr as _`."""
    return get_localizer().tr(key)


def _translate_widget_tree(widget, localizer: Localizer):
    if isinstance(widget, Gtk.Label):
        widget.set_label(localizer.tr(widget.get_label()))
    elif isinstance(widget, Gtk.Button) and widget.get_label():
        widget.set_label(localizer.tr(widget.get_label()))
    child = widget.get_first_child()
    while child is not None:
        _translate_widget_tree(child, localizer)
        child = child.get_next_sibling()


def translate_dialog(dialog):
    """Translate an Adw.MessageDialog's heading/body/extra-child tree in
    place, using the default Localizer. This is the single-argument form
    that package_manager.py calls throughout — it binds a shared Localizer
    instance internally so every call site doesn't have to pass one in."""
    localizer = get_localizer()
    if dialog.get_heading():
        dialog.set_heading(localizer.tr(dialog.get_heading()))
    if dialog.get_body():
        dialog.set_body(localizer.tr(dialog.get_body()))
    extra = dialog.get_extra_child()
    if extra is not None:
        _translate_widget_tree(extra, localizer)
