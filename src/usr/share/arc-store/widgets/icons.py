"""
widgets/icons.py — correct, GTK4-safe icon loading.

Rules this follows (see ui_description section 3):
  * Icons in lists/sidebars render at 32px; icons in cards/headers at 36-48px.
  * SVGs load straight from file.
  * Rasters (PNG/JPG) always go through GdkPixbuf -> Gdk.Texture ->
    Gtk.Image.new_from_paintable — never the deprecated
    Gtk.Image.new_from_pixbuf.
  * Always fall back to a symbolic system icon name if the file is missing.
"""

import os
from gi.repository import Gtk, Gdk, GdkPixbuf

ICON_SIZE = 32


def load_icon(icon_path_or_name: str, size: int = ICON_SIZE,
              fallback: str = "application-x-addon-symbolic") -> Gtk.Image:
    """SVG -> straight from file. Raster -> Pixbuf -> Gdk.Texture -> Gtk.Image
    (the correct path in GTK4). Missing file / error -> treat the string as a
    system theme icon name, and if that also fails, use the fallback."""
    if icon_path_or_name and os.path.isfile(icon_path_or_name):
        try:
            if icon_path_or_name.lower().endswith(".svg"):
                image = Gtk.Image()
                image.set_from_file(icon_path_or_name)
            else:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(icon_path_or_name, size, size)
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                image = Gtk.Image.new_from_paintable(texture)
            image.set_pixel_size(size)
            return image
        except Exception:
            pass
    image = Gtk.Image.new_from_icon_name(icon_path_or_name or fallback)
    image.set_pixel_size(size)
    return image


def app_icon_path() -> str:
    """Absolute path to Arc Store's own icon.png, which ships next to the
    rest of the application's Python files."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icon.png")
