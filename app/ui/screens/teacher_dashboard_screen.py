from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from datetime import date, timedelta

from app.ui.state.session import SessionState
from app.database.teacher_queries import (
    get_teacher_courses, get_course_attendance_matrix
)
from app.services.class_runner import run_class
from app.services.report_generator import (
    export_weekly_report, export_monthly_report, export_total_report
)
from app.ui.widgets.buttons import RoundedButton, OutlineButton, GhostButton, Card
from app.ui.widgets.controls import styled_spinner
from app.ui.theme import (
    BG_DARK, PRIMARY, ACCENT_GREEN, ACCENT_RED,
    TEXT_WHITE, TEXT_MUTED,
    FONT_SIZE_TITLE, FONT_SIZE_SMALL
)

NO_SUBJECT = "Select Subject"

# Table layout constants
ROW_HEIGHT = 42
NAME_COL_WIDTH = 170
ROLL_COL_WIDTH = 140
DATE_COL_WIDTH = 96

STATUS_COLORS = {
    "PRESENT": "00E676",
    "LATE": "FFAB40",
    "ABSENT": "FF5252",
}
STATUS_SHORT = {
    "PRESENT": "P",
    "LATE": "L",
    "ABSENT": "A",
}


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

        # ── Attendance table (student × date, horizontally scrollable) ──
        self.table_card = Card(
            orientation="vertical",
            padding=[12, 12, 12, 12],
            size_hint_y=None,
            height=ROW_HEIGHT * 2
        )

        self.table_grid = GridLayout(
            cols=2, rows=1,
            size_hint=(None, None),
            row_default_height=ROW_HEIGHT,
            row_force_default=True,
            spacing=1
        )

        self.table_scroll = ScrollView(
            size_hint=(1, None),
            height=ROW_HEIGHT,
            do_scroll_x=True,
            do_scroll_y=False,
            bar_width=6
        )
        self.table_scroll.add_widget(self.table_grid)
        self.table_card.add_widget(self.table_scroll)

        self.empty_label = self._label(
            "Select a subject to view attendance.", TEXT_MUTED, FONT_SIZE_SMALL, 24, markup=True
        )
        self.table_card.add_widget(self.empty_label)

        # ── Report generation ──
        report_row = BoxLayout(size_hint_y=None, height=48, spacing=10)
        weekly_btn = OutlineButton(outline_color=PRIMARY, text="📄 Weekly Report")
        weekly_btn.bind(on_press=self.export_weekly)
        monthly_btn = OutlineButton(outline_color=PRIMARY, text="📄 Monthly Report")
        monthly_btn.bind(on_press=self.export_monthly)
        total_btn = OutlineButton(outline_color=PRIMARY, text="📄 Total Course Report")
        total_btn.bind(on_press=self.export_total)
        report_row.add_widget(weekly_btn)
        report_row.add_widget(monthly_btn)
        report_row.add_widget(total_btn)

        self.report_status = self._label("", TEXT_MUTED, FONT_SIZE_SMALL, 20, markup=True)

        logout_btn = GhostButton(text="Logout", color=ACCENT_RED, size_hint_y=None, height=42)
        logout_btn.bind(on_press=self.logout)

        self.layout.add_widget(header_card)
        self.layout.add_widget(Widget(size_hint_y=None, height=4))
        self.layout.add_widget(self.course_spinner)
        self.layout.add_widget(start_btn)
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

    @staticmethod
    def _cell_label(text, width, color=TEXT_WHITE, bold=False, markup=False):
        lbl = Label(
            text=text, font_size=FONT_SIZE_SMALL, color=color, bold=bold, markup=markup,
            size_hint=(None, None), size=(width, ROW_HEIGHT),
            halign="center", valign="middle"
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
        matrix = get_course_attendance_matrix(course_id)
        self._build_table(matrix)

    def _build_table(self, matrix):
        dates = matrix.get("dates", [])
        students = matrix.get("students", [])

        self.table_grid.clear_widgets()

        if not students or not dates:
            self.table_scroll.height = 0
            self.table_card.height = ROW_HEIGHT
            self.empty_label.text = "[color=8888AA]No attendance records for this subject yet.[/color]"
            self.empty_label.opacity = 1
            self.empty_label.disabled = False
            return

        self.empty_label.text = ""
        self.empty_label.opacity = 0
        self.empty_label.disabled = True

        n_cols = 2 + len(dates)
        n_rows = 1 + len(students)

        self.table_grid.cols = n_cols
        self.table_grid.rows = n_rows

        total_width = NAME_COL_WIDTH + ROLL_COL_WIDTH + DATE_COL_WIDTH * len(dates)
        total_height = ROW_HEIGHT * n_rows

        self.table_grid.width = total_width
        self.table_grid.height = total_height
        self.table_scroll.height = total_height
        self.table_card.height = total_height + 24  # padding allowance

        # ── Header row ──
        self.table_grid.add_widget(
            self._cell_label("Student", NAME_COL_WIDTH, color=PRIMARY, bold=True)
        )
        self.table_grid.add_widget(
            self._cell_label("Roll No", ROLL_COL_WIDTH, color=PRIMARY, bold=True)
        )
        for d in dates:
            label_text = d.strftime("%d %b") if hasattr(d, "strftime") else str(d)
            self.table_grid.add_widget(
                self._cell_label(label_text, DATE_COL_WIDTH, color=PRIMARY, bold=True)
            )

        # ── Student rows ──
        for student in students:
            self.table_grid.add_widget(
                self._cell_label(student.get("name", ""), NAME_COL_WIDTH)
            )
            self.table_grid.add_widget(
                self._cell_label(student.get("roll_no", ""), ROLL_COL_WIDTH)
            )
            attendance = student.get("attendance", {})
            for d in dates:
                status = attendance.get(d, None)
                if status:
                    short = STATUS_SHORT.get(status, "?")
                    hex_color = STATUS_COLORS.get(status, "8888AA")
                    text = f"[color={hex_color}]{short}[/color]"
                else:
                    text = "[color=555566]—[/color]"
                self.table_grid.add_widget(
                    self._cell_label(text, DATE_COL_WIDTH, markup=True)
                )

    def _show_empty_state(self):
        self.table_grid.clear_widgets()
        self.table_scroll.height = 0
        self.table_card.height = ROW_HEIGHT
        self.empty_label.text = "[color=8888AA]Select a subject to view attendance.[/color]"
        self.empty_label.opacity = 1
        self.empty_label.disabled = False
        self.report_status.text = ""

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

    def export_total(self, instance):
        if not self.selected_course:
            self.report_status.text = "[color=FF5252]Select a subject first.[/color]"
            return

        path = export_total_report(self.selected_course["course_id"])

        if path:
            self.report_status.text = f"[color=00E676]Saved total course report to {path}[/color]"
        else:
            self.report_status.text = "[color=FFAB40]No sessions found for this course.[/color]"

    def logout(self, instance):
        SessionState.teacher = None
        self.manager.current = "home"

    def _update_bg(self, *args):
        self._bg_rect.size = self.children[0].size
        self._bg_rect.pos = self.children[0].pos