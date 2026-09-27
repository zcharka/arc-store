#!/usr/bin/env python3
"""
Arc Store — main entry point.

A standalone graphical front-end for pacman + the AUR, built with
Python, GTK4 and libadwaita. Wraps package_manager.py (the original
Linexin Center package-manager widget) in its own Adw.Application and
window instead of a host sidebar.
"""

import os
import sys

# GTK4's default Vulkan-backed GSK renderer has documented crashes on
# NVIDIA's proprietary driver (ArchWiki's GTK page, the Arch forums, and
# NVIDIA's own developer forum). Falling back to the GL renderer is the
# standard workaround. Set as a *default* — os.environ.setdefault leaves
# it alone if the user (or the launcher) already set GSK_RENDERER. This
# has to happen before gi/Gtk is imported anywhere, and is a defensive
# second copy of the identical line in src/usr/bin/arc-store, for anyone
# running `python main.py` directly during development.
os.environ.setdefault("GSK_RENDERER", "gl")

# Let `import theme`, `import package_manager`, `from widgets...`,
# `from auth...` and `from i18n...` resolve no matter what directory the
# /usr/bin/arc-store launcher was started from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi  # noqa: E402
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio  # noqa: E402

from theme import apply_css, BASE_CSS  # noqa: E402
from widgets.icons import load_icon, app_icon_path  # noqa: E402
from widgets.hover_breathe import HoverBreatheController  # noqa: E402
from package_manager import PackageManagerView  # noqa: E402

APP_ID = "github.zcharka.arcstore"
APP_VERSION = "1.0.0"


class AboutWindow(Adw.Window):
    """A small, hand-built About screen.

    Adw.AboutWindow / Adw.AboutDialog take their application icon as a
    *themed icon name* string, and Arc Store's icon.png isn't installed
    into an icon theme search path — it just ships next to the rest of the
    Python files, per how this project is packaged. So instead of fighting
    that mismatch, this window is built by hand with load_icon(), which is
    the spec-mandated, always-correct way to show a raw PNG in GTK4
    (GdkPixbuf -> Gdk.Texture -> Gtk.Image.new_from_paintable)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_default_size(360, 420)
        self.set_resizable(False)
        self.set_modal(True)
        self.set_title("About Arc Store")

        header = Gtk.HeaderBar()
        header.add_css_class("flat")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_valign(Gtk.Align.CENTER)
        box.set_vexpand(True)
        box.set_margin_top(12)
        box.set_margin_bottom(32)
        box.set_margin_start(32)
        box.set_margin_end(32)

        # Logo with the spec's hover/press "breathe" animation.
        logo_shell = Gtk.Overlay()
        logo_shell.set_size_request(112, 112)
        logo_shell.set_halign(Gtk.Align.CENTER)
        logo = load_icon(app_icon_path(), size=88)
        logo_shell.set_child(logo)
        self._breathe = HoverBreatheController(logo_shell, logo)
        box.append(logo_shell)

        title = Gtk.Label(label="Arc Store")
        title.add_css_class("title-1")
        title.set_margin_top(8)
        box.append(title)

        version = Gtk.Label(label=f"Version {APP_VERSION}")
        version.add_css_class("dim-label")
        box.append(version)

        desc = Gtk.Label(label="A graphical package manager for pacman and the AUR.")
        desc.set_wrap(True)
        desc.set_justify(Gtk.Justification.CENTER)
        desc.add_css_class("body")
        desc.set_margin_top(8)
        box.append(desc)

        link_btn = Gtk.LinkButton(uri="https://github.com/zcharka", label="github.com/zcharka")
        link_btn.set_halign(Gtk.Align.CENTER)
        link_btn.set_margin_top(12)
        box.append(link_btn)

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)
        toolbar_view.set_content(box)
        self.set_content(toolbar_view)


class ArcStoreWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Arc Store")
        # Matches the screenshot Sebastian is using as the floor: the window
        # opens at this size and set_size_request() below stops it from
        # ever being resized smaller than it — it can still be made larger.
        self.set_default_size(1099, 728)
        self.set_size_request(1099, 728)

        header = Gtk.HeaderBar()
        header.add_css_class("flat")
        header.set_title_widget(Adw.WindowTitle(title="Arc Store", subtitle=""))

        about_btn = Gtk.Button()
        about_btn.set_icon_name("help-about-symbolic")
        about_btn.add_css_class("flat")
        about_btn.set_tooltip_text("About Arc Store")
        about_btn.connect("clicked", self._on_about_clicked)
        header.pack_end(about_btn)

        # The package manager view already implements its own adaptive
        # (wide/compact) layout internally, so it's the window's only
        # piece of content — no extra top-level breakpoint logic needed.
        self.pkg_view = PackageManagerView(hide_sidebar=True, window=self)

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(header)
        toolbar_view.set_content(self.pkg_view)

        # Adw.ApplicationWindow only ever supports set_content() — calling
        # the inherited Gtk.Window.set_child() on it is a hard, fatal
        # library error ("gtk_window_set_child() is not supported for
        # AdwApplicationWindow"), not just a warning. There is no
        # per-desktop alternative here: this is unconditional regardless
        # of GNOME/Plasma/Hyprland. (An earlier version of this file tried
        # to branch on desktop environment for this — that was wrong and
        # is exactly what was crashing the app on startup under Plasma.)
        self.set_content(toolbar_view)

    def _on_about_clicked(self, btn):
        about = AboutWindow(transient_for=self)
        about.present()


class ArcStoreApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.window = None

    def do_activate(self):
        apply_css(BASE_CSS)
        if not self.window:
            self.window = ArcStoreWindow(application=self)
        self.window.present()


def main():
    app = ArcStoreApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main() or 0)
