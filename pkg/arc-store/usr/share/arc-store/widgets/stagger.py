"""
widgets/stagger.py — staggered enter/exit for a list of rows: instead of
appearing/disappearing all at once, each row follows the previous one with
a small delay. Needs the .row-enter-prep / .row-enter / .row-exit CSS
classes defined in theme.py.

Not currently wired into the package manager's search results, which use a
virtualized Gtk.ListView + Gio.ListStore for performance on large result
sets — staggering individual persistent row widgets doesn't compose with
that virtualization. Kept here, ready to use, for any smaller/fixed-size
list Arc Store adds later (e.g. a manually-built confirmation list).
"""

from gi.repository import GLib


def stagger_reveal(rows, *, base_delay_ms=60, stride_ms=40, settle_ms=400):
    for row in rows:
        row.add_css_class("row-enter-prep")

    def reveal(row):
        row.remove_css_class("row-enter-prep")
        row.add_css_class("row-enter")
        GLib.timeout_add(settle_ms, lambda: row.remove_css_class("row-enter") or False)
        return False

    for i, row in enumerate(rows):
        GLib.timeout_add(base_delay_ms + i * stride_ms, reveal, row)


def stagger_dismiss(rows, on_all_done, *, stride_ms=30, buffer_ms=350):
    for i, row in enumerate(rows):
        GLib.timeout_add(i * stride_ms, lambda r=row: r.add_css_class("row-exit") or False)
    GLib.timeout_add(len(rows) * stride_ms + buffer_ms, lambda: on_all_done() or False)
