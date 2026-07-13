from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from datetime import date, timedelta

from app.ui.state.session import SessionState
from app.database.teacher_queries import (
    get_teacher_courses, get_course_calendar_data, get_course_history_table
)
from app.services.class_runner import run_class
from app.services.report_generator import export_weekly_report, export_monthly_report
from app.ui.widgets.buttons import RoundedButton, OutlineButton, GhostButton, Card
from app.ui.widgets.controls import styled_spinner, SegmentedToggle
from app.ui.widgets.calendar_view import AttendanceCalendar
from app.ui.theme import (
    BG_DARK, PRIMARY, ACCENT_GREEN, ACCENT_RED,
    TEXT_WHITE, TEXT_MUTED,
    FONT_SIZE_TITLE, FONT_SIZE_SMALL
)

NO_SUBJECT = "Select Subject"


class TeacherDashboardScreen(Screen):

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
        role_tag = self._label("👨‍🏫  Teacher Dashboard", PRIMARY, FONT_SIZE_SMALL, 22)
        self.info_label = self._label("", TEXT_WHITE, FONT_SIZE_TITLE, 36, bold=True)
        header_card.add_widget(role_tag)
        header_card.add_widget(self.info_label)

        # ── Subject selector (defaults to none selected) ──
        self.course_spinner = styled_spinner(PRIMARY, text=NO_SUBJECT)
        self.course_spinner.bind(text=self.select_course)

        # Start class
        start_btn = RoundedButton(
            fill_color=ACCENT_GREEN, text="▶  Start Class",
            size_hint_y=None, height=50
        )
        start_btn.bind(on_press=self.start_class)

        # ── View toggle ──
        self.toggle = SegmentedToggle(
            ["Calendar", "Table"], accent_color=PRIMARY, on_select=self._on_view_change
        )

        # ── Calendar view ──
        self.calendar = AttendanceCalendar(accent_color=PRIMARY)

        # ── Table view card ──
        table_card = Card(
            orientation="vertical", padding=[16, 12, 16, 12], size_hint_y=None, height=260
        )
        self.result_label = Label(
            text="", font_size=FONT_SIZE_SMALL, color=TEXT_MUTED,
            halign="left", valign="top", markup=True
        )
        self.result_label.bind(size=self.result_label.setter("text_size"))
        table_card.add_widget(self.result_label)
        self.table_card = table_card
        self.table_card.opacity = 0
        self.table_card.height = 0
        self.table_card.disabled = True

        # ── Report generation ──
        report_row = BoxLayout(size_hint_y=None, height=48, spacing=10)
        weekly_btn = OutlineButton(outline_color=PRIMARY, text="📄 Weekly Report")
        weekly_btn.bind(on_press=self.export_weekly)
        monthly_btn = OutlineButton(outline_color=PRIMARY, text="📄 Monthly Report")
        monthly_btn.bind(on_press=self.export_monthly)
        report_row.add_widget(weekly_btn)
        report_row.add_widget(monthly_btn)

        self.report_status = self._label("", TEXT_MUTED, FONT_SIZE_SMALL, 20, markup=True)

        logout_btn = GhostButton(text="Logout", color=ACCENT_RED, size_hint_y=None, height=42)
        logout_btn.bind(on_press=self.logout)

        self.layout.add_widget(header_card)
        self.layout.add_widget(Widget(size_hint_y=None, height=4))
        self.layout.add_widget(self.course_spinner)
        self.layout.add_widget(start_btn)
        self.layout.add_widget(self.toggle)
        self.layout.add_widget(self.calendar)
        self.layout.add_widget(self.table_card)
        self.layout.add_widget(report_row)
        self.layout.add_widget(self.report_status)
        self.layout.add_widget(Widget(size_hint_y=None, height=6))
        self.layout.add_widget(logout_btn)

        scroll.add_widget(self.layout)
        root.add_widget(scroll)
        self.add_widget(root)

        self._show_empty_state()

    @staticmethod
    def _label(text, color, font_size, height, bold=False, markup=False):
        lbl = Label(
            text=text, font_size=font_size, color=color, bold=bold, markup=markup,
            size_hint_y=None, height=height, halign="left", valign="middle"
        )
        lbl.bind(size=lbl.setter("text_size"))
        return lbl

    def on_enter(self):
        teacher = SessionState.teacher
        self.info_label.text = f"{teacher['name']}"

        self.courses = get_teacher_courses(teacher["teacher_id"])
        self.course_spinner.values = [row["courses"]["course_name"] for row in self.courses]
        self.course_spinner.text = NO_SUBJECT
        self.selected_course = None
        self._show_empty_state()

    def select_course(self, spinner, text):
        if text == NO_SUBJECT:
            self.selected_course = None
            self._show_empty_state()
            return

        for row in self.courses:
            course = row["courses"]
            if course["course_name"] == text:
                self.selected_course = {
                    "course_id": row["course_id"],
                    "course_name": course["course_name"],
                    "course_code": course.get("course_code"),
                    "semester": course.get("semester"),
                }
                break

        self._refresh_data()

    def _refresh_data(self):
        if not self.selected_course:
            return

        course_id = self.selected_course["course_id"]

        calendar_data = get_course_calendar_data(course_id)
        self.calendar.set_data(calendar_data)

        rows = get_course_history_table(course_id)
        output = [f"[b]{self.selected_course['course_name']}[/b]\n"]
        for row in rows:
            pct = round((row["present"] + row["late"]) / row["total"] * 100) if row["total"] else 0
            color = "[color=00E676]" if pct >= 75 else ("[color=FFAB40]" if pct >= 50 else "[color=FF5252]")
            output.append(f"  {row['class_date']}  —  {color}{pct}%[/color]  ({row['present']}P / {row['late']}L / {row['absent']}A)")
        self.result_label.text = "\n".join(output)

    def _show_empty_state(self):
        self.calendar.set_data({})
        self.result_label.text = "[color=8888AA]Select a subject to view attendance.[/color]"
        self.report_status.text = ""

    def _on_view_change(self, name):
        show_calendar = (name == "Calendar")
        self.calendar.opacity = 1 if show_calendar else 0
        self.calendar.disabled = not show_calendar
        self.calendar.height = self.calendar.height if show_calendar else 0
        self.table_card.opacity = 0 if show_calendar else 1
        self.table_card.disabled = show_calendar
        self.table_card.height = 0 if show_calendar else 260

    def start_class(self, instance):
        if not self.selected_course:
            self.report_status.text = "[color=FF5252]Select a subject first.[/color]"
            return
        run_class(self.selected_course["course_id"])

    def export_weekly(self, instance):
        if not self.selected_course:
            self.report_status.text = "[color=FF5252]Select a subject first.[/color]"
            return

        end = date.today()
        start = end - timedelta(days=7)
        path = export_weekly_report(
            self.selected_course["course_id"], start.isoformat(), end.isoformat()
        )

        if path:
            self.report_status.text = f"[color=00E676]Saved weekly report to {path}[/color]"
        else:
            self.report_status.text = "[color=FFAB40]No sessions found in the last 7 days.[/color]"

    def export_monthly(self, instance):
        if not self.selected_course:
            self.report_status.text = "[color=FF5252]Select a subject first.[/color]"
            return

        today = date.today()
        path = export_monthly_report(
            self.selected_course["course_id"], today.month, today.year
        )

        if path:
            self.report_status.text = f"[color=00E676]Saved monthly report to {path}[/color]"
        else:
            self.report_status.text = "[color=FFAB40]No sessions found this month.[/color]"

    def logout(self, instance):
        SessionState.teacher = None
        self.manager.current = "home"

    def _update_bg(self, *args):
        self._bg_rect.size = self.children[0].size
        self._bg_rect.pos = self.children[0].pos
