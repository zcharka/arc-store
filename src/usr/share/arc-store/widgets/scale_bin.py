"""
widgets/scale_bin.py — a transparent single-child container that scales its
child only at paint time (layout/allocation never changes, so nothing else
"jumps"), plus the two-phase exit/spring-enter transition that goes with it.

Not currently wired into any Arc Store screen (the package manager view
already has its own working adaptive-layout logic — see package_manager.py),
but shipped ready to use for future breakpoint-driven layout changes, per
the project's UI spec.
"""

import gi
gi.require_version("Graphene", "1.0")
from gi.repository import Gtk, Graphene, Adw


class ScaleBin(Gtk.Widget):
    """Transparent 1-child container that draws its child scaled around its
    own center. Use to animate the 'breathing' of whole UI sections."""

    def __init__(self):
        super().__init__()
        self._child = None
        self._scale = 1.0

    def set_child(self, child):
        if child is self._child:
            return
        if self._child is not None:
            self._child.unparent()
        self._child = child
        if child is not None:
            child.set_parent(self)

    def set_scale(self, scale):
        if scale != self._scale:
            self._scale = scale
            self.queue_draw()

    def do_measure(self, orientation, for_size):
        if self._child is None:
            return (0, 0, -1, -1)
        return self._child.measure(orientation, for_size)

    def do_size_allocate(self, width, height, baseline):
        if self._child is not None:
            self._child.allocate(width, height, baseline, None)

    def do_snapshot(self, snapshot):
        if self._child is None:
            return
        if self._scale == 1.0:
            self.snapshot_child(self._child, snapshot)
            return
        cx, cy = self.get_width() * 0.5, self.get_height() * 0.5
        snapshot.save()
        snapshot.translate(Graphene.Point().init(cx, cy))
        snapshot.scale(self._scale, self._scale)
        snapshot.translate(Graphene.Point().init(-cx, -cy))
        self.snapshot_child(self._child, snapshot)
        snapshot.restore()

    def do_dispose(self):
        if self._child is not None:
            self._child.unparent()
            self._child = None
        Gtk.Widget.do_dispose(self)


def play_exit_then_spring_enter(body, scale_bin, on_swap_content):
    """Two-phase layout transition:
    1) the old layout fades+shrinks out (110ms, EASE_IN_CUBIC)
    2) on_swap_content() actually swaps the content
    3) the new layout springs in with a bit of overshoot/bounce
    Respects the system's reduce-motion setting since it's built entirely on
    Adw.TimedAnimation/Adw.SpringAnimation.

    Note: if `body` might be hidden (e.g. inside a not-currently-visible
    stack page) at the moment the layout changes, skip the exit phase and
    swap immediately, then play only the spring once the widget is mapped
    again (`body.connect("map", ...)`) — an animation started on an unmapped
    widget completes instantly instead of playing.
    """

    def on_exit_value(value, *_):
        body.set_opacity(value)
        scale_bin.set_scale(0.96 + 0.04 * value)

    def on_enter_value(value, *_):
        body.set_opacity(max(0.0, min(1.0, value)))
        scale_bin.set_scale(0.90 + 0.10 * value)

    def after_exit(anim):
        on_swap_content()
        target = Adw.CallbackAnimationTarget.new(on_enter_value)
        params = Adw.SpringParams.new(0.62, 1.0, 300.0)  # damping ratio, mass, stiffness
        spring = Adw.SpringAnimation.new(body, 0.0, 1.0, params, target)
        spring.set_epsilon(0.001)
        spring.play()

    target = Adw.CallbackAnimationTarget.new(on_exit_value)
    exit_anim = Adw.TimedAnimation.new(body, 1.0, 0.0, 110, target)
    exit_anim.set_easing(Adw.Easing.EASE_IN_CUBIC)
    exit_anim.connect("done", after_exit)
    exit_anim.play()
