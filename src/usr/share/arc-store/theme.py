"""
theme.py — Arc Store's shared visual language.

Loaded exactly once at application start (see main.py) via
``apply_css(BASE_CSS)``. Every rule below styles through libadwaita's
named color aliases (``@accent_color``, ``@window_bg_color``, ...) so the
app follows the system theme and accent color automatically — nothing in
here hardcodes a color for a UI surface. The only acceptable exception to
that rule would be a purely decorative brand element, and there isn't one
here.
"""

from gi.repository import Gtk, Gdk

BASE_CSS = """
/* Header bar that blends into the window background */
headerbar.flat {
    min-height: 0; padding-top: 3px; padding-bottom: 3px;
    background: transparent; border: none; box-shadow: none;
}
.dim-label { opacity: 0.6; }
.navigation-sidebar row { margin-bottom: 6px; }

/* Locked state while a privileged operation is running (see auth/) */
widget:disabled { opacity: 0.3; }
.command-locked { background: alpha(@warning_color, 0.1); }

/* Cards / item grids, GNOME-Software style */
.app-card { border-radius: 12px; }
.app-grid > flowboxchild { border-radius: 12px; padding: 0; }
.highlight-section {
    background-color: alpha(@accent_bg_color, 0.08);
    border: 1px solid alpha(@accent_bg_color, 0.30);
    border-radius: 14px; padding: 10px;
}
.badge {
    background-color: @accent_bg_color; color: @accent_fg_color;
    border-radius: 9999px; padding: 1px 9px; font-size: 0.68em; font-weight: 800;
}
.pill-action { border-radius: 9999px; padding-left: 14px; padding-right: 14px; }

/* Installed/Discover mode switch: rounded rectangles (not a full pill),
   neutral grey — no accent color — so it reads as a plain view toggle
   rather than a call-to-action button. */
.mode-toggle-btn {
    border-radius: 10px; padding-left: 14px; padding-right: 14px;
    background-color: alpha(currentColor, 0.06);
}
.mode-toggle-btn:hover { background-color: alpha(currentColor, 0.10); }
.mode-toggle-btn:checked { background-color: alpha(currentColor, 0.14); }
.mode-toggle-btn:checked:hover { background-color: alpha(currentColor, 0.18); }

/* Compact icon buttons */
.compact-icon-btn { min-width: 40px; min-height: 40px; padding: 6px; border-radius: 10px; margin: 2px; }
.compact-icon-btn:hover { background: alpha(@accent_color, 0.15); }
.compact-icon-selected { background: alpha(@accent_color, 0.25); }
.compact-icon-selected:hover { background: alpha(@accent_color, 0.35); }

/* Staggered list row enter/exit (see widgets/stagger.py) */
.row-enter-prep { opacity: 0; transform: translateX(-12px) scale(0.95); }
.row-enter {
    opacity: 1; transform: translateX(0) scale(1);
    transition: opacity 300ms cubic-bezier(0.0,0.0,0.2,1),
                transform 400ms cubic-bezier(0.34,1.56,0.64,1);
}
.row-exit { opacity: 0.6; transform: scale(0.97); transition: opacity 250ms ease-out, transform 250ms ease-out; }
.row-dragging { opacity: 0.4; }
.drop-above { border-top: 2px solid @accent_color; }
.drop-below { border-bottom: 2px solid @accent_color; }

/* Package Manager view specifics (kept from the original widget) */
.buttons_all {
    font-size: 14px;
    min-width: 200px;
    min-height: 40px;
}
.rounded-list {
    border-radius: 12px;
}
"""

def apply_css(css: str) -> None:
    """Load an application-priority stylesheet onto the default display."""
    provider = Gtk.CssProvider()
    if hasattr(provider, "load_from_string"):
        provider.load_from_string(css)
    else:  # older GTK < 4.12
        provider.load_from_data(css.encode("utf-8"))
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
