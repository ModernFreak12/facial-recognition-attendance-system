"""
Shared widgets so every screen looks & behaves the same way.
Previously each screen (home, teacher_login, student_login, ...)
re-implemented rounded buttons, cards, and text inputs with slightly
different padding/radius values. Everything now goes through here.
"""
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle, Line

from app.ui.theme import (
    BG_CARD, BG_INPUT, TEXT_WHITE, TEXT_MUTED,
    FONT_SIZE_BODY, FONT_SIZE_BUTTON, RADIUS_BUTTON, RADIUS_CARD
)


def _bind_rect(widget, rect, *extra_lines):
    def _update(w, v):
        rect.size = w.size
        rect.pos = w.pos
        for line in extra_lines:
            line.rounded_rectangle = [*w.pos, *w.size, rect.radius[0]]
    widget.bind(size=_update, pos=_update)


class RoundedButton(Button):
    """A solid, rounded, filled button. Use for primary actions."""

    def __init__(self, fill_color, text_color=None, radius=RADIUS_BUTTON, **kwargs):
        kwargs.setdefault("font_size", FONT_SIZE_BUTTON)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", [0, 0, 0, 0])
        kwargs.setdefault("color", text_color or TEXT_WHITE)
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*fill_color)
            self._rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[radius])
        _bind_rect(self, self._rect)


class OutlineButton(Button):
    """A card-colored button with a subtle 1.5px outline. Use for secondary actions."""

    def __init__(self, outline_color, text_color=None, radius=RADIUS_BUTTON, **kwargs):
        kwargs.setdefault("font_size", FONT_SIZE_BUTTON)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", [0, 0, 0, 0])
        kwargs.setdefault("color", text_color or outline_color)
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*BG_CARD)
            self._fill = RoundedRectangle(size=self.size, pos=self.pos, radius=[radius])
            Color(*outline_color)
            self._outline = Line(
                rounded_rectangle=[*self.pos, *self.size, radius], width=1.5
            )

        def _update(w, v):
            self._fill.size = w.size
            self._fill.pos = w.pos
            self._outline.rounded_rectangle = [*w.pos, *w.size, radius]

        self.bind(size=_update, pos=_update)


class GhostButton(Button):
    """Fully transparent, text-only button. Use for 'Back' / 'Logout' style actions."""

    def __init__(self, text_color=TEXT_MUTED, **kwargs):
        kwargs.setdefault("font_size", FONT_SIZE_BODY)
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", [0, 0, 0, 0])
        kwargs.setdefault("color", text_color)
        super().__init__(**kwargs)


def styled_text_input(hint_text, password=False, cursor_color=None, **kwargs):
    """Consistent text input styling used across all login/search fields."""
    kwargs.setdefault("multiline", False)
    kwargs.setdefault("font_size", FONT_SIZE_BODY)
    kwargs.setdefault("background_color", BG_INPUT)
    kwargs.setdefault("foreground_color", TEXT_WHITE)
    kwargs.setdefault("hint_text_color", TEXT_MUTED)
    kwargs.setdefault("padding", [16, 14, 16, 14])
    kwargs.setdefault("size_hint", (1, None))
    kwargs.setdefault("height", 48)
    return TextInput(
        hint_text=hint_text,
        password=password,
        cursor_color=cursor_color or TEXT_WHITE,
        **kwargs
    )


class Card(BoxLayout):
    """A rounded card container with an optional subtle accent border."""

    def __init__(self, accent_color=None, radius=RADIUS_CARD, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*BG_CARD)
            self._rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[radius])
            self._border = None
            if accent_color:
                Color(*accent_color[:3], 0.25)
                self._border = Line(
                    rounded_rectangle=[*self.pos, *self.size, radius], width=1.2
                )

        def _update(w, v):
            self._rect.size = w.size
            self._rect.pos = w.pos
            if self._border:
                self._border.rounded_rectangle = [*w.pos, *w.size, radius]

        self.bind(size=_update, pos=_update)
