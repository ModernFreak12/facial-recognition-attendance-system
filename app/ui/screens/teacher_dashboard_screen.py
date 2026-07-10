from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line

from app.ui.state.session import SessionState
from app.database.teacher_queries import get_teacher_courses, get_course_attendance
from app.services.class_runner import run_class
from app.services.report_generator import export_weekly_report, export_monthly_report
from app.ui.theme import (
    BG_DARK, BG_CARD, BG_INPUT, PRIMARY, PRIMARY_LIGHT,
    ACCENT_GREEN, ACCENT_RED, SECONDARY,
    TEXT_WHITE, TEXT_MUTED, TEXT_DARK,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_BODY,
    FONT_SIZE_BUTTON, FONT_SIZE_SMALL
)


class TeacherDashboardScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.selected_course = None

        root = FloatLayout()

        with root.canvas.before:
            Color(*BG_DARK)
            self._bg_rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=self._update_bg, pos=self._update_bg)

        # ── Main scrollable column ──
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

        role_tag = Label(
            text="👨‍🏫  Teacher Dashboard",
            font_size=FONT_SIZE_SMALL,
            color=PRIMARY_LIGHT,
            size_hint_y=None,
            height=22,
            halign="left",
            valign="middle"
        )
        role_tag.bind(size=role_tag.setter('text_size'))

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

        # Start class
        start_btn = Button(
            text="▶  Start Class",
            font_size=FONT_SIZE_BUTTON,
            size_hint_y=None,
            height=50,
            background_normal="",
            background_color=[0, 0, 0, 0],
            color=TEXT_WHITE,
            bold=True
        )
        start_btn.bind(on_press=self.start_class)
        self._apply_rounded_bg(start_btn, ACCENT_GREEN, radius=14)

        # ── Attendance date ──
        date_label = Label(
            text="View Attendance by Date",
            font_size=FONT_SIZE_SMALL,
            color=TEXT_MUTED,
            size_hint_y=None,
            height=24,
            halign="left",
            valign="middle"
        )
        date_label.bind(size=date_label.setter('text_size'))

        self.date_input = TextInput(
            hint_text="YYYY-MM-DD",
            multiline=False,
            size_hint_y=None,
            height=44,
            font_size=FONT_SIZE_BODY,
            background_color=BG_INPUT,
            foreground_color=TEXT_WHITE,
            hint_text_color=TEXT_MUTED,
            cursor_color=PRIMARY,
            padding=[16, 12, 16, 12]
        )

        attendance_btn = Button(
            text="📋  View Attendance",
            font_size=FONT_SIZE_BUTTON,
            size_hint_y=None,
            height=50,
            background_normal="",
            background_color=[0, 0, 0, 0],
            color=TEXT_WHITE,
            bold=True
        )
        attendance_btn.bind(on_press=self.view_attendance)
        self._apply_rounded_bg(attendance_btn, PRIMARY, radius=14)

        # ── Results Card ──
        results_card = BoxLayout(
            orientation="vertical",
            padding=[16, 12, 16, 12],
            size_hint_y=None,
            height=220
        )
        with results_card.canvas.before:
            Color(*BG_CARD)
            results_card._bg = RoundedRectangle(
                size=results_card.size, pos=results_card.pos, radius=[14]
            )
        results_card.bind(
            size=lambda w, v: setattr(w._bg, 'size', v),
            pos=lambda w, v: setattr(w._bg, 'pos', v)
        )

        self.result_label = Label(
            text="",
            font_size=FONT_SIZE_SMALL,
            color=TEXT_MUTED,
            halign="left",
            valign="top",
            markup=True
        )
        self.result_label.bind(size=self.result_label.setter('text_size'))
        results_card.add_widget(self.result_label)

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

        # ── Assemble layout ──
        self.layout.add_widget(header_card)
        self.layout.add_widget(Widget(size_hint_y=None, height=8))
        self.layout.add_widget(self.course_spinner)
        self.layout.add_widget(start_btn)
        self.layout.add_widget(Widget(size_hint_y=None, height=10))
        self.layout.add_widget(date_label)
        self.layout.add_widget(self.date_input)
        self.layout.add_widget(attendance_btn)
        self.layout.add_widget(Widget(size_hint_y=None, height=6))
        self.layout.add_widget(results_card)
        self.layout.add_widget(Widget(size_hint_y=None, height=6))
        self.layout.add_widget(logout_btn)

        scroll.add_widget(self.layout)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_enter(self):
        teacher = SessionState.teacher

        self.info_label.text = f"{teacher['name']}"

        courses = get_teacher_courses(teacher["teacher_id"])
        self.courses = courses

        self.course_spinner.values = [
            row["courses"]["course_name"]
            for row in courses
        ]

    def select_course(self, spinner, text):
        for row in self.courses:
            course = row["courses"]
            if course["course_name"] == text:
                self.selected_course = row
                break

    def start_class(self, instance):
        if not self.selected_course:
            return

        run_class(self.selected_course["course_id"])

    def view_attendance(self, instance):
        if not self.selected_course:
            return

        rows = get_course_attendance(
            self.selected_course["course_id"],
            self.date_input.text
        )

        output = []
        for row in rows:
            student = row["students"]
            status = row["status"]
            color = "[color=00E676]" if status == "PRESENT" else (
                "[color=FFAB40]" if status == "LATE" else "[color=FF5252]"
            )
            output.append(
                f"{student['name']} ({student['univ_roll_no']}) — {color}{status}[/color]"
            )

        self.result_label.text = "\n".join(output) if output else "[color=8888AA]No records found.[/color]"

    def logout(self, instance):
        SessionState.teacher = None
        self.manager.current = "home"

    # ── Canvas helpers ──
    def _update_bg(self, *args):
        self._bg_rect.size = self.children[0].size
        self._bg_rect.pos = self.children[0].pos

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