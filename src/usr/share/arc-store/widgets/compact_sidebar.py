"""
widgets/compact_sidebar.py — animates an Adw.NavigationSplitView's numeric
sidebar width (not the widget itself), swapping content exactly halfway
through, plus a synchronized arrow-icon rotation done by rewriting CSS every
frame (GTK CSS can't animate transform: rotate() from a Python variable).

Not currently wired into any Arc Store screen — the package manager view's
own actions panel already has a working, animated show/hide built on
Gtk.Revealer, so this isn't force-fitted in on top of it. Kept here, ready
to use, for any future Adw.NavigationSplitView-based screen.
"""

from gi.repository import Gtk, Adw


class CompactSidebarAnimator:
    def __init__(self, split_view, toggle_btn, *,
                 width_normal=330, width_compact=62, duration_ms=350):
        self.split_view, self.toggle_btn = split_view, toggle_btn
        self.width_normal, self.width_compact, self.duration_ms = width_normal, width_compact, duration_ms
        self.rotation_deg = 180.0
        self._rotate_css = Gtk.CssProvider()
        toggle_btn.get_style_context().add_provider(
            self._rotate_css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1
        )
        self._apply_rotation(self.rotation_deg)

    def _apply_width(self, w):
        self.split_view.set_min_sidebar_width(int(w))
        self.split_view.set_max_sidebar_width(int(w))

    def _apply_rotation(self, deg):
        css = f".compact-toggle-btn {{ transition: none; transform: rotate({deg}deg); }}"
        self._rotate_css.load_from_data(css.encode())

    def set_compact(self, compact: bool, on_swap_content):
        deg_to = 0.0 if compact else 180.0

        target_r = Adw.CallbackAnimationTarget.new(self._apply_rotation)
        rotate_anim = Adw.TimedAnimation.new(self.toggle_btn, self.rotation_deg, deg_to, self.duration_ms, target_r)
        rotate_anim.set_easing(Adw.Easing.EASE_IN_OUT_CUBIC)
        rotate_anim.connect("done", lambda *_: setattr(self, "rotation_deg", deg_to))
        rotate_anim.play()

        mid = (self.width_normal + self.width_compact) / 2.0
        swapped = [False]

        def on_tick(v, *_):
            self._apply_width(v)
            crossed = (v <= mid) if compact else (v >= mid)
            if not swapped[0] and crossed:
                swapped[0] = True
                on_swap_content()

        target_w = Adw.CallbackAnimationTarget.new(on_tick)
        width_anim = Adw.TimedAnimation.new(
            self.split_view, float(self.width_normal if compact else self.width_compact),
            float(self.width_compact if compact else self.width_normal), self.duration_ms, target_w
        )
        width_anim.set_easing(Adw.Easing.EASE_IN_OUT_CUBIC)
        width_anim.play()
