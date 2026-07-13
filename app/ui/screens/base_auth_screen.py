from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle

from app.ui.widgets.buttons import RoundedButton, GhostButton, styled_text_input, Card
from app.ui.theme import (
    BG_DARK, ACCENT_RED, TEXT_WHITE, TEXT_MUTED,
    FONT_SIZE_TITLE, FONT_SIZE_SMALL
)


class BaseAuthScreen(Screen):
    """
    Shared card layout for the teacher & student login screens so both
    look and behave identically apart from accent color / copy / the
    table they authenticate against.
    """

    icon = "👤"
    title_text = "Sign In"
    description = "Sign in with your email and password"
    accent_color = TEXT_WHITE
    back_target = "home"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()
        with root.canvas.before:
            Color(*BG_DARK)
            self._bg_rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=self._update_bg, pos=self._update_bg)

        card = Card(
            accent_color=self.accent_color,
            orientation="vertical",
            spacing=16,
            padding=[36, 36, 36, 36],
            size_hint=(0.88, 0.66),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        icon_label = Label(text=self.icon, font_size=44, size_hint=(1, 0.16))
        title = Label(
            text=self.title_text, font_size=FONT_SIZE_TITLE, bold=True,
            color=TEXT_WHITE, size_hint=(1, 0.1)
        )
        desc = Label(
            text=self.description, font_size=FONT_SIZE_SMALL,
            color=TEXT_MUTED, size_hint=(1, 0.06)
        )
        spacer = Widget(size_hint=(1, 0.04))

        self.email_input = styled_text_input(
            "Email", cursor_color=self.accent_color, size_hint=(1, 0.1)
        )

        self.password_input = styled_text_input(
            "Password", password=True, cursor_color=self.accent_color,
            size_hint=(1, 0.1)
        )

        self.message_label = Label(
            text="", font_size=FONT_SIZE_SMALL, color=ACCENT_RED, size_hint=(1, 0.06)
        )

        login_btn = RoundedButton(
            fill_color=self.accent_color, text="Sign In", size_hint=(1, 0.12)
        )
        login_btn.bind(on_press=self.login)

        back_btn = GhostButton(text="← Back", size_hint=(1, 0.08))
        back_btn.bind(on_press=self.go_back)

        card.add_widget(icon_label)
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
        raise NotImplementedError

    def go_back(self, instance):
        self.manager.current = self.back_target

    def _update_bg(self, *args):
        self._bg_rect.size = self.children[0].size
        self._bg_rect.pos = self.children[0].pos