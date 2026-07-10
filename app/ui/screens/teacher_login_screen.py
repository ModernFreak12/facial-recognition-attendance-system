from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line

from app.services.supabase_client import supabase
from app.ui.state.session import SessionState
from app.ui.theme import (
    BG_DARK, BG_CARD, BG_INPUT, PRIMARY, ACCENT_RED,
    TEXT_WHITE, TEXT_MUTED, SECONDARY,
    FONT_SIZE_TITLE, FONT_SIZE_BODY, FONT_SIZE_BUTTON, FONT_SIZE_SMALL
)


class TeacherLoginScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()

        with root.canvas.before:
            Color(*BG_DARK)
            self._bg_rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=self._update_bg, pos=self._update_bg)

        # ── Card ──
        card = BoxLayout(
            orientation="vertical",
            spacing=16,
            padding=[36, 36, 36, 36],
            size_hint=(0.88, 0.68),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        with card.canvas.before:
            Color(*BG_CARD)
            self._card_rect = RoundedRectangle(
                size=card.size, pos=card.pos, radius=[20]
            )
            Color(*PRIMARY[:3], 0.2)
            self._card_border = Line(
                rounded_rectangle=[*card.pos, *card.size, 20],
                width=1.2
            )
        card.bind(size=self._update_card, pos=self._update_card)

        # ── Icon ──
        icon = Label(text="👨‍🏫", font_size=44, size_hint=(1, 0.16))

        # ── Title ──
        title = Label(
            text="Teacher Login",
            font_size=FONT_SIZE_TITLE,
            bold=True,
            color=TEXT_WHITE,
            size_hint=(1, 0.1)
        )

        desc = Label(
            text="Sign in with your credentials",
            font_size=FONT_SIZE_SMALL,
            color=TEXT_MUTED,
            size_hint=(1, 0.06)
        )

        spacer = Widget(size_hint=(1, 0.04))

        # ── Email Input ──
        self.email_input = TextInput(
            hint_text="Teacher Email",
            multiline=False,
            size_hint=(1, 0.1),
            font_size=FONT_SIZE_BODY,
            background_color=BG_INPUT,
            foreground_color=TEXT_WHITE,
            hint_text_color=TEXT_MUTED,
            cursor_color=PRIMARY,
            padding=[16, 14, 16, 14]
        )

        # ── Password Input ──
        self.password_input = TextInput(
            hint_text="Teacher Name",
            multiline=False,
            password=True,
            size_hint=(1, 0.1),
            font_size=FONT_SIZE_BODY,
            background_color=BG_INPUT,
            foreground_color=TEXT_WHITE,
            hint_text_color=TEXT_MUTED,
            cursor_color=PRIMARY,
            padding=[16, 14, 16, 14]
        )

        # ── Message Label ──
        self.message_label = Label(
            text="",
            font_size=FONT_SIZE_SMALL,
            color=ACCENT_RED,
            size_hint=(1, 0.06)
        )

        # ── Login Button ──
        login_btn = Button(
            text="Sign In",
            font_size=FONT_SIZE_BUTTON,
            size_hint=(1, 0.12),
            background_normal="",
            background_color=[0, 0, 0, 0],
            color=TEXT_WHITE,
            bold=True
        )
        login_btn.bind(on_press=self.login)
        self._apply_rounded_bg(login_btn, PRIMARY, radius=14)

        # ── Back Button ──
        back_btn = Button(
            text="← Back",
            font_size=FONT_SIZE_SMALL,
            size_hint=(1, 0.08),
            background_normal="",
            background_color=[0, 0, 0, 0],
            color=TEXT_MUTED,
            bold=False
        )
        back_btn.bind(on_press=self.go_back)

        card.add_widget(icon)
        card.add_widget(title)
        card.add_widget(desc)
        card.add_widget(spacer)
        card.add_widget(self.email_input)
        card.add_widget(self.password_input)
        card.add_widget(self.message_label)
        card.add_widget(login_btn)
        card.add_widget(back_btn)

        root.add_widget(card)
        self.add_widget(root)

    def login(self, instance):
        email = self.email_input.text.strip()
        password = self.password_input.text.strip()

        response = (
            supabase.table("teachers")
            .select("*")
            .eq("email", email)
            .eq("name", password)
            .execute()
        )

        if not response.data:
            self.message_label.text = "Invalid login."
            return

        SessionState.teacher = response.data[0]
        self.manager.current = "teacher_dashboard"

    def go_back(self, instance):
        self.manager.current = "home"

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