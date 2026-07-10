from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line

from app.ui.state.session import SessionState
from app.database.student_queries import get_student_courses, get_course_history
from app.ui.theme import (
    BG_DARK, BG_CARD, BG_INPUT, PRIMARY, SECONDARY,
    ACCENT_GREEN, ACCENT_RED,
    TEXT_WHITE, TEXT_MUTED,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY,
    FONT_SIZE_BUTTON, FONT_SIZE_SMALL
)


class StudentDashboardScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        root = FloatLayout()

        with root.canvas.before:
            Color(*BG_DARK)
            self._bg_rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=self._update_bg, pos=self._update_bg)

        # ── Scrollable column ──
        scroll = ScrollView(
            size_hint=(0.92, 0.92),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            do_scroll_x=False
        )

        self.layout = BoxLayout(
            orientation="vertical",
            spacing=14,
            padding=[24, 24, 24, 24],
            size_hint_y=None
        )
        self.layout.bind(minimum_height=self.layout.setter('height'))

        # ── Header Card ──
        header_card = BoxLayout(
            orientation="vertical",
            spacing=6,
            padding=[20, 16, 20, 16],
            size_hint_y=None,
            height=100
        )
        with header_card.canvas.before:
            Color(*BG_CARD)
            header_card._bg = RoundedRectangle(
                size=header_card.size, pos=header_card.pos, radius=[16]
            )
        header_card.bind(
            size=lambda w, v: setattr(w._bg, 'size', v),
            pos=lambda w, v: setattr(w._bg, 'pos', v)
        )

        role_tag = Label(
            text="🎒  Student Dashboard",
            font_size=FONT_SIZE_SMALL,
            color=SECONDARY,
            size_hint_y=None,
            height=22,
            halign="left",
            valign="middle"
        )
        role_tag.bind(size=role_tag.setter('text_size'))

        self.info_label = Label(
            text="",
            font_size=FONT_SIZE_TITLE,
            bold=True,
            color=TEXT_WHITE,
            size_hint_y=None,
            height=36,
            halign="left",
            valign="middle"
        )
        self.info_label.bind(size=self.info_label.setter('text_size'))

        header_card.add_widget(role_tag)
        header_card.add_widget(self.info_label)

        # ── Course Selector ──
        self.course_spinner = Spinner(
            text="Select Course",
            font_size=FONT_SIZE_BODY,
            size_hint_y=None,
            height=48,
            background_normal="",
            background_color=BG_INPUT,
            color=TEXT_WHITE
        )
        self.course_spinner.bind(text=self.select_course)

        # ── Attendance Overview Card ──
        overview_card = BoxLayout(
            orientation="vertical",
            padding=[16, 12, 16, 12],
            size_hint_y=None,
            height=200
        )
        with overview_card.canvas.before:
            Color(*BG_CARD)
            overview_card._bg = RoundedRectangle(
                size=overview_card.size, pos=overview_card.pos, radius=[14]
            )
        overview_card.bind(
            size=lambda w, v: setattr(w._bg, 'size', v),
            pos=lambda w, v: setattr(w._bg, 'pos', v)
        )

        overview_title = Label(
            text="Attendance Overview",
            font_size=FONT_SIZE_SUBTITLE,
            bold=True,
            color=TEXT_WHITE,
            size_hint_y=None,
            height=28,
            halign="left",
            valign="middle"
        )
        overview_title.bind(size=overview_title.setter('text_size'))

        self.result_label = Label(
            text="",
            font_size=FONT_SIZE_SMALL,
            color=TEXT_MUTED,
            halign="left",
            valign="top",
            markup=True
        )
        self.result_label.bind(size=self.result_label.setter('text_size'))

        overview_card.add_widget(overview_title)
        overview_card.add_widget(self.result_label)

        # ── Logout ──
        logout_btn = Button(
            text="Logout",
            font_size=FONT_SIZE_SMALL,
            size_hint_y=None,
            height=42,
            background_normal="",
            background_color=[0, 0, 0, 0],
            color=ACCENT_RED,
            bold=False
        )
        logout_btn.bind(on_press=self.logout)

        # ── Assemble ──
        self.layout.add_widget(header_card)
        self.layout.add_widget(Widget(size_hint_y=None, height=8))
        self.layout.add_widget(self.course_spinner)
        self.layout.add_widget(Widget(size_hint_y=None, height=6))
        self.layout.add_widget(overview_card)
        self.layout.add_widget(Widget(size_hint_y=None, height=6))
        self.layout.add_widget(logout_btn)

        scroll.add_widget(self.layout)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_enter(self):
        student = SessionState.student
        self.student = student

        self.info_label.text = f"{student['name']}"

        self.courses = get_student_courses(student["student_id"])

        values = []
        output = []

        for c in self.courses:
            values.append(c["course_name"])
            pct = c["percentage"]
            color = "[color=00E676]" if pct >= 75 else (
                "[color=FFAB40]" if pct >= 50 else "[color=FF5252]"
            )
            output.append(f"  •  {c['course_name']}  —  {color}{pct}%[/color]")

        self.course_spinner.values = values
        self.result_label.text = "\n".join(output) if output else "[color=8888AA]No courses found.[/color]"

    def select_course(self, spinner, text):
        selected = None

        for c in self.courses:
            if c["course_name"] == text:
                selected = c

        if not selected:
            return

        history = get_course_history(
            self.student["student_id"],
            selected["course_id"]
        )

        output = [f"[b]{text}[/b]\n"]

        for row in history:
            date = row["class_sessions"]["class_date"]
            status = row["status"]
            color = "[color=00E676]" if status == "PRESENT" else (
                "[color=FFAB40]" if status == "LATE" else "[color=FF5252]"
            )
            output.append(f"  {date}  —  {color}{status}[/color]")

        self.result_label.text = "\n".join(output)

    def logout(self, instance):
        SessionState.student = None
        self.manager.current = "home"

    # ── Canvas helpers ──
    def _update_bg(self, *args):
        self._bg_rect.size = self.children[0].size
        self._bg_rect.pos = self.children[0].pos