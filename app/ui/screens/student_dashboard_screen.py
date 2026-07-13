from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle

from app.ui.state.session import SessionState
from app.database.student_queries import (
    get_student_courses, get_course_history, get_course_calendar_data
)
from app.ui.widgets.buttons import GhostButton, Card
from app.ui.widgets.controls import styled_spinner, SegmentedToggle
from app.ui.widgets.calendar_view import AttendanceCalendar
from app.ui.theme import (
    BG_DARK, SECONDARY, ACCENT_RED,
    TEXT_WHITE, TEXT_MUTED,
    FONT_SIZE_TITLE, FONT_SIZE_SUBTITLE, FONT_SIZE_SMALL,
    status_markup
)
from datetime import date

NO_SUBJECT = "Select Subject"


class StudentDashboardScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.selected_course = None

        root = FloatLayout()
        with root.canvas.before:
            Color(*BG_DARK)
            self._bg_rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=self._update_bg, pos=self._update_bg)

        scroll = ScrollView(
            size_hint=(0.92, 0.92),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            do_scroll_x=False
        )

        self.layout = BoxLayout(
            orientation="vertical", spacing=14,
            padding=[24, 24, 24, 24], size_hint_y=None
        )
        self.layout.bind(minimum_height=self.layout.setter("height"))

        # ── Header Card ──
        header_card = Card(
            orientation="vertical", spacing=6,
            padding=[20, 16, 20, 16], size_hint_y=None, height=100
        )
        role_tag = self._label("🎒  Student Dashboard", SECONDARY, FONT_SIZE_SMALL, 22)
        self.info_label = self._label("", TEXT_WHITE, FONT_SIZE_TITLE, 36, bold=True)
        header_card.add_widget(role_tag)
        header_card.add_widget(self.info_label)

        # ── Subject selector (defaults to none selected) ──
        self.course_spinner = styled_spinner(SECONDARY, text=NO_SUBJECT)
        self.course_spinner.bind(text=self.select_course)

        # ── View toggle ──
        self.toggle = SegmentedToggle(
            ["Calendar", "Table"], accent_color=SECONDARY, on_select=self._on_view_change
        )

        # ── Calendar view ──
        self.calendar = AttendanceCalendar(accent_color=SECONDARY)

        # ── Table view card ──
        table_card = Card(
            orientation="vertical",
            padding=[16, 12, 16, 12],
            size_hint_y=None,
            height=260
        )

        self.result_label = Label(
            text="",
            font_size=FONT_SIZE_SMALL,
            color=TEXT_MUTED,
            halign="left",
            valign="top",
            markup=True
        )
        self.result_label.bind(size=self.result_label.setter("text_size"))

        table_card.add_widget(self.result_label)
        self.table_card = table_card

        # Container that holds either the calendar OR the table
        self.view_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=self.calendar.height
        )
        self.view_container.add_widget(self.calendar)

        logout_btn = GhostButton(text="Logout", color=ACCENT_RED, size_hint_y=None, height=42)
        logout_btn.bind(on_press=self.logout)

        self.layout.add_widget(header_card)
        self.layout.add_widget(Widget(size_hint_y=None, height=4))
        self.layout.add_widget(self.course_spinner)
        self.layout.add_widget(self.toggle)
        self.layout.add_widget(self.view_container)
        self.layout.add_widget(Widget(size_hint_y=None, height=6))
        self.layout.add_widget(logout_btn)

        scroll.add_widget(self.layout)
        root.add_widget(scroll)
        self.add_widget(root)

        self._show_empty_state()

    @staticmethod
    def _label(text, color, font_size, height, bold=False):
        lbl = Label(
            text=text, font_size=font_size, color=color, bold=bold,
            size_hint_y=None, height=height, halign="left", valign="middle"
        )
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def on_enter(self):
        student = SessionState.student
        self.student = student
        self.info_label.text = f"{student['name']}"

        self.courses = get_student_courses(student["student_id"])
        self.course_spinner.values = [c["course_name"] for c in self.courses]
        self.course_spinner.text = NO_SUBJECT
        self.selected_course = None
        self._show_empty_state()

    def select_course(self, spinner, text):
        if text == NO_SUBJECT:
            self.selected_course = None
            self._show_empty_state()
            return

        self.selected_course = next(
            (c for c in self.courses if c["course_name"] == text), None
        )
        if not self.selected_course:
            return

        self._refresh_data()

    def _refresh_data(self):
        if not self.selected_course:
            return

        course_id = self.selected_course["course_id"]

        calendar_data = get_course_calendar_data(self.student["student_id"], course_id)
        self.calendar.set_data(calendar_data)

        history = get_course_history(self.student["student_id"], course_id)
        output = [f"[b]{self.selected_course['course_name']}[/b]\n"]
        for row in history:
            d = row["class_sessions"]["class_date"]
            status = row["status"]
            output.append(f"  {d}  —  {status_markup(status)}{status}[/color]")
        self.result_label.text = "\n".join(output)

    def _show_empty_state(self):
        today = date.today()
        self.calendar.year = today.year
        self.calendar.month = today.month
        self.calendar.set_data({})

        self.result_label.text = (
            "[color=8888AA]Select a subject to view attendance.[/color]"
        )

    def _on_view_change(self, name):
        self.view_container.clear_widgets()

        if name == "Calendar":
            self.view_container.height = self.calendar.height
            self.view_container.add_widget(self.calendar)
        else:
            self.view_container.height = self.table_card.height
            self.view_container.add_widget(self.table_card)

    def logout(self, instance):
        SessionState.student = None
        self.manager.current = "home"

    def _update_bg(self, *args):
        self._bg_rect.size = self.children[0].size
        self._bg_rect.pos = self.children[0].pos
