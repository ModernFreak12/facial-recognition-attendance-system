"""
Small reusable controls: a Calendar/Table segmented toggle and a
consistently-styled subject/course spinner.
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, RoundedRectangle

from app.ui.theme import (
    BG_CARD, BG_INPUT, TEXT_WHITE, TEXT_MUTED,
    FONT_SIZE_BODY, FONT_SIZE_SMALL, RADIUS_CHIP
)


def styled_spinner(accent_color, text="Select Subject", **kwargs):
    """Course/subject spinner. Defaults to no subject selected."""
    kwargs.setdefault("size_hint_y", None)
    kwargs.setdefault("height", 48)
    spinner = Spinner(
        text=text,
        font_size=FONT_SIZE_BODY,
        background_normal="",
        background_down="",
        background_color=BG_INPUT,
        color=TEXT_WHITE,
        **kwargs
    )
    with spinner.canvas.before:
        Color(*accent_color[:3], 0.35)
        border = RoundedRectangle(size=spinner.size, pos=spinner.pos, radius=[RADIUS_CHIP])

    def _update(w, v):
        border.size = w.size
        border.pos = w.pos

    spinner.bind(size=_update, pos=_update)
    return spinner


class SegmentedToggle(BoxLayout):
    """A two-option pill toggle, e.g. 'Calendar' / 'Table'. Fires on_select(name)."""

    def __init__(self, options, accent_color, on_select=None, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", 44)
        kwargs.setdefault("spacing", 6)
        kwargs.setdefault("padding", [4, 4, 4, 4])
        super().__init__(**kwargs)

        self._accent_color = accent_color
        self._on_select = on_select
        self._buttons = {}
        self.active = options[0]

        with self.canvas.before:
            Color(*BG_INPUT)
            self._bg = RoundedRectangle(size=self.size, pos=self.pos, radius=[RADIUS_CHIP + 2])
        self.bind(size=self._update_bg, pos=self._update_bg)

        for name in options:
            btn = Button(
                text=name,
                font_size=FONT_SIZE_SMALL,
                bold=True,
                background_normal="",
                background_down="",
                background_color=[0, 0, 0, 0],
                color=TEXT_MUTED,
            )
            with btn.canvas.before:
                Color(0, 0, 0, 0)
                btn._pill = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[RADIUS_CHIP])

            def _update_pill(w, v, b=btn):
                b._pill.size = w.size
                b._pill.pos = w.pos
            btn.bind(size=_update_pill, pos=_update_pill)

            btn.bind(on_press=lambda inst, n=name: self.select(n))
            self._buttons[name] = btn
            self.add_widget(btn)

        self.select(options[0], fire_callback=False)

    def _update_bg(self, w, v):
        self._bg.size = w.size
        self._bg.pos = w.pos

    def select(self, name, fire_callback=True):
        self.active = name
        for btn_name, btn in self._buttons.items():
            is_active = btn_name == name
            btn.color = [1, 1, 1, 1] if is_active else TEXT_MUTED
            with btn.canvas.before:
                btn.canvas.before.clear()
                Color(*(self._accent_color if is_active else [0, 0, 0, 0]))
                btn._pill = RoundedRectangle(size=btn.size, pos=btn.pos, radius=[RADIUS_CHIP])
        if fire_callback and self._on_select:
            self._on_select(name)
