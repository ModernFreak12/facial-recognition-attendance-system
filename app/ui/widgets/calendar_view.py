"""
AttendanceCalendar: a month-grid calendar where each day is colored
by attendance status for the currently selected subject.

Usage:
    cal = AttendanceCalendar(accent_color=PRIMARY)
    cal.set_data({"2026-07-01": "PRESENT", "2026-07-03": "LATE", ...})
    cal.set_data({})   # clears / shows an empty grey grid when no subject picked

Dates not present in the data dict are rendered as plain (no session).
"""
import calendar
from datetime import date

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle

from app.ui.theme import (
    TEXT_WHITE, TEXT_MUTED, TEXT_DARK, BG_CARD_ALT,
    FONT_SIZE_SMALL, FONT_SIZE_TINY, status_color
)

WEEKDAY_LABELS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class _DayCell(Button):
    def __init__(self, day_num, status, is_today=False, **kwargs):
        super().__init__(
            text=str(day_num) if day_num else "",
            font_size=FONT_SIZE_SMALL,
            bold=is_today,
            background_normal="",
            background_down="",
            background_color=[0, 0, 0, 0],
            color=TEXT_DARK if status not in (None, "NONE") else TEXT_WHITE,
            disabled=(day_num == 0),
        )
        if day_num:
            fill = status_color(status) if status else BG_CARD_ALT
            with self.canvas.before:
                Color(*fill)
                self._circle = RoundedRectangle(
                    size=(30, 30), pos=self.pos, radius=[15]
                )
            self.bind(pos=self._reposition, size=self._reposition)

    def _reposition(self, *args):
        cx = self.center_x - 15
        cy = self.center_y - 15
        self._circle.pos = (cx, cy)


class AttendanceCalendar(BoxLayout):
    """Month calendar. Call set_data({'YYYY-MM-DD': 'PRESENT'|'LATE'|'ABSENT'}) to render."""

    def __init__(self, accent_color, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", 8)
        kwargs.setdefault("size_hint_y", None)
        super().__init__(**kwargs)
        self.accent_color = accent_color
        today = date.today()
        self.year, self.month = today.year, today.month
        self._data = {}

        self._header = BoxLayout(size_hint_y=None, height=36, spacing=8)
        self._prev_btn = Button(
            text="<", size_hint_x=None, width=40,
            background_normal="", background_down="",
            background_color=[0, 0, 0, 0], color=accent_color, bold=True
        )
        self._prev_btn.bind(on_press=lambda *_: self._shift_month(-1))
        self._month_label = Label(text="", bold=True, color=TEXT_WHITE, font_size=FONT_SIZE_SMALL)
        self._next_btn = Button(
            text=">", size_hint_x=None, width=40,
            background_normal="", background_down="",
            background_color=[0, 0, 0, 0], color=accent_color, bold=True
        )
        self._next_btn.bind(on_press=lambda *_: self._shift_month(1))
        self._header.add_widget(self._prev_btn)
        self._header.add_widget(self._month_label)
        self._header.add_widget(self._next_btn)

        self._weekday_row = GridLayout(cols=7, size_hint_y=None, height=22, spacing=2)
        for wd in WEEKDAY_LABELS:
            self._weekday_row.add_widget(
                Label(text=wd, font_size=FONT_SIZE_TINY, color=TEXT_MUTED)
            )

        self._grid = GridLayout(cols=7, size_hint_y=None, spacing=4, row_default_height=36)
        self._grid.bind(minimum_height=self._grid.setter("height"))

        # legend
        self._legend = BoxLayout(size_hint_y=None, height=20, spacing=14)
        for label, status in (("Present", "PRESENT"), ("Late", "LATE"), ("Absent", "ABSENT")):
            self._legend.add_widget(self._legend_chip(label, status))

        self.add_widget(self._header)
        self.add_widget(self._weekday_row)
        self.add_widget(self._grid)
        self.add_widget(self._legend)

        self.height = 36 + 22 + 20 + 20 + (6 * 40)  # header+weekday+legend+spacing+~6 rows
        self._render()

    def _legend_chip(self, label, status):
        row = BoxLayout(spacing=4)
        dot = Label(text="●", color=status_color(status), font_size=FONT_SIZE_TINY, size_hint_x=None, width=14)
        txt = Label(text=label, color=TEXT_MUTED, font_size=FONT_SIZE_TINY)
        row.add_widget(dot)
        row.add_widget(txt)
        return row

    def set_data(self, data: dict):
        """data: {'YYYY-MM-DD': 'PRESENT' | 'LATE' | 'ABSENT'}"""
        self._data = data or {}
        self._render()

    def _shift_month(self, delta):
        m = self.month + delta
        y = self.year
        if m == 0:
            m = 12
            y -= 1
        elif m == 13:
            m = 1
            y += 1
        self.year, self.month = y, m
        self._render()

    def _render(self):
        self._month_label.text = f"{calendar.month_name[self.month]} {self.year}"
        self._grid.clear_widgets()

        cal = calendar.Calendar(firstweekday=0)  # Monday first
        for day_num in cal.itermonthdays(self.year, self.month):
            if day_num == 0:
                self._grid.add_widget(_DayCell(0, None))
                continue
            date_str = f"{self.year:04d}-{self.month:02d}-{day_num:02d}"
            status = self._data.get(date_str)
            self._grid.add_widget(_DayCell(day_num, status))
