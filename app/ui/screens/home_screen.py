from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle

from app.ui.widgets.buttons import RoundedButton, OutlineButton, Card
from app.ui.theme import (
    BG_DARK, PRIMARY, SECONDARY,
    TEXT_WHITE, TEXT_MUTED,
    FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_SIZE_TINY
)


class HomeScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()

        with root.canvas.before:
            Color(*BG_DARK)
            self._bg_rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=self._update_bg, pos=self._update_bg)

        card = Card(
            accent_color=PRIMARY,
            orientation="vertical",
            spacing=20,
            padding=[40, 40, 40, 40],
            size_hint=(0.88, 0.62),
            pos_hint={"center_x": 0.5, "center_y": 0.48}
        )

        title = Label(
            text="Smart Classroom",
            font_size=FONT_SIZE_TITLE + 4,
            bold=True,
            color=TEXT_WHITE,
            size_hint=(1, 0.12)
        )

        subtitle = Label(
            text="Facial Recognition Attendance",
            font_size=FONT_SIZE_BODY,
            color=TEXT_MUTED,
            size_hint=(1, 0.08)
        )

        spacer = Widget(size_hint=(1, 0.08))

        teacher_btn = RoundedButton(
            fill_color=PRIMARY,
            text="Teacher Login",
            size_hint=(1, 0.14),
        )
        teacher_btn.bind(on_press=self.go_teacher_login)

        student_btn = OutlineButton(
            outline_color=SECONDARY,
            text="Student Login",
            size_hint=(1, 0.14),
        )
        student_btn.bind(on_press=self.go_student_login)

        footer = Label(
            text="v1.0  •  Secure & Smart",
            font_size=FONT_SIZE_TINY,
            color=TEXT_MUTED,
            size_hint=(1, 0.06)
        )

        card.add_widget(title)
        card.add_widget(subtitle)
        card.add_widget(spacer)
        card.add_widget(teacher_btn)
        card.add_widget(student_btn)
        card.add_widget(footer)

        root.add_widget(card)
        self.add_widget(root)

    def go_teacher_login(self, instance):
        self.manager.current = "teacher_login"

    def go_student_login(self, instance):
        self.manager.current = "student_login"

    def _update_bg(self, *args):
        self._bg_rect.size = self.children[0].size
        self._bg_rect.pos = self.children[0].pos
