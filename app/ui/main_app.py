from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window

from app.ui.screens.home_screen import HomeScreen
from app.ui.screens.teacher_login_screen import TeacherLoginScreen
from app.ui.screens.student_login_screen import StudentLoginScreen
from app.ui.screens.teacher_dashboard_screen import TeacherDashboardScreen
from app.ui.screens.student_dashboard_screen import StudentDashboardScreen


class SmartClassroomApp(App):

    def build(self):
        # Window configuration
        Window.size = (480, 780)
        Window.clearcolor = (0.07, 0.07, 0.12, 1)  # Deep dark background

        sm = ScreenManager(transition=FadeTransition(duration=0.25))

        # ------------------------
        # Home
        # ------------------------
        sm.add_widget(HomeScreen(name="home"))

        # ------------------------
        # Login Screens
        # ------------------------
        sm.add_widget(TeacherLoginScreen(name="teacher_login"))
        sm.add_widget(StudentLoginScreen(name="student_login"))

        # ------------------------
        # Temporary Dashboards
        # (reuse old screens)
        # ------------------------
        sm.add_widget(TeacherDashboardScreen(name="teacher_dashboard"))
        sm.add_widget(StudentDashboardScreen(name="student_dashboard"))

        return sm