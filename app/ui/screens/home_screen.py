from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.animation import Animation
from kivy.clock import Clock

from app.ui.theme import (
    BG_DARK, BG_CARD, PRIMARY, PRIMARY_LIGHT, SECONDARY,
    TEXT_WHITE, TEXT_MUTED,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY, FONT_SIZE_BUTTON
)


class HomeScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()

        # ── Background ──
        with root.canvas.before:
            Color(*BG_DARK)
            self._bg_rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=self._update_bg, pos=self._update_bg)

        # ── Card container ──
        card = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=[40, 40, 40, 40],
            size_hint=(0.88, 0.72),
            pos_hint={"center_x": 0.5, "center_y": 0.48}
        )

        with card.canvas.before:
            Color(*BG_CARD)
            self._card_rect = RoundedRectangle(
                size=card.size, pos=card.pos, radius=[20]
            )
            Color(*PRIMARY[:3], 0.25)
            self._card_border = Line(
                rounded_rectangle=[*card.pos, *card.size, 20],
                width=1.2
            )
        card.bind(size=self._update_card, pos=self._update_card)

        # ── Icon / emoji label ──
        icon_label = Label(
            text="🎓",
            font_size=52,
            size_hint=(1, 0.22)
        )

        # ── Title ──
        title = Label(
            text="Smart Classroom",
            font_size=FONT_SIZE_TITLE,
            bold=True,
            color=TEXT_WHITE,
            size_hint=(1, 0.12)
        )

        # ── Subtitle ──
        subtitle = Label(
            text="Facial Recognition Attendance",
            font_size=FONT_SIZE_BODY,
            color=TEXT_MUTED,
            size_hint=(1, 0.08)
        )

        # ── Spacer ──
        spacer = Widget(size_hint=(1, 0.08))

        # ── Teacher Button ──
        teacher_btn = Button(
            text="👨‍🏫  Teacher Login",
            font_size=FONT_SIZE_BUTTON,
            size_hint=(1, 0.14),
            background_normal="",
            background_color=PRIMARY,
            color=TEXT_WHITE,
            bold=True
        )
        teacher_btn.bind(on_press=self.go_teacher_login)
        self._apply_rounded_bg(teacher_btn, PRIMARY, radius=14)

        # ── Student Button ──
        student_btn = Button(
            text="🎒  Student Login",
            font_size=FONT_SIZE_BUTTON,
            size_hint=(1, 0.14),
            background_normal="",
            background_color=[0, 0, 0, 0],
            color=SECONDARY,
            bold=True
        )
        student_btn.bind(on_press=self.go_student_login)
        self._apply_outline_bg(student_btn, SECONDARY, radius=14)

        # ── Footer ──
        footer = Label(
            text="v1.0  •  Secure & Smart",
            font_size=11,
            color=TEXT_MUTED,
            size_hint=(1, 0.06)
        )

        card.add_widget(icon_label)
        card.add_widget(title)
        card.add_widget(subtitle)
        card.add_widget(spacer)
        card.add_widget(teacher_btn)
        card.add_widget(student_btn)
        card.add_widget(footer)

        root.add_widget(card)
        self.add_widget(root)

    # ── Navigation ──
    def go_teacher_login(self, instance):
        self.manager.current = "teacher_login"

    def go_student_login(self, instance):
        self.manager.current = "student_login"

    # ── Canvas helpers ──
    def _update_bg(self, *args):
        self._bg_rect.size = self.children[0].size
        self._bg_rect.pos = self.children[0].pos

    def _update_card(self, widget, *args):
        self._card_rect.size = widget.size
        self._card_rect.pos = widget.pos
        self._card_border.rounded_rectangle = [*widget.pos, *widget.size, 20]

    def _apply_rounded_bg(self, btn, color, radius=12):
        btn.background_color = [0, 0, 0, 0]
        with btn.canvas.before:
            Color(*color)
            btn._rounded_bg = RoundedRectangle(
                size=btn.size, pos=btn.pos, radius=[radius]
            )
        btn.bind(
            size=lambda w, v: setattr(w._rounded_bg, 'size', v),
            pos=lambda w, v: setattr(w._rounded_bg, 'pos', v)
        )

    def _apply_outline_bg(self, btn, color, radius=12):
        btn.background_color = [0, 0, 0, 0]
        with btn.canvas.before:
            Color(*BG_CARD)
            btn._fill_bg = RoundedRectangle(
                size=btn.size, pos=btn.pos, radius=[radius]
            )
            Color(*color)
            btn._outline = Line(
                rounded_rectangle=[*btn.pos, *btn.size, radius],
                width=1.5
            )
        btn.bind(
            size=self._outline_update_factory(btn, radius),
            pos=self._outline_update_factory(btn, radius)
        )

    @staticmethod
    def _outline_update_factory(btn, radius):
        def _update(widget, value):
            btn._fill_bg.size = widget.size
            btn._fill_bg.pos = widget.pos
            btn._outline.rounded_rectangle = [*widget.pos, *widget.size, radius]
        return _update