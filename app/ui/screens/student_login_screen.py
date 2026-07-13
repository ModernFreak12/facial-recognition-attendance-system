from app.services.supabase_client import supabase
from app.services.auth import verify_password
from app.ui.state.session import SessionState
from app.ui.theme import SECONDARY
from app.ui.screens.base_auth_screen import BaseAuthScreen


class StudentLoginScreen(BaseAuthScreen):
    icon = "🎒"
    title_text = "Student Login"
    description = "Sign in with your email & password"
    accent_color = SECONDARY
    back_target = "home"

    def login(self, instance):
        email = self.email_input.text.strip().lower()
        password = self.password_input.text

        if not email or not password:
            self.message_label.text = "Enter your email and password."
            return

        response = (
            supabase.table("students")
            .select("*")
            .eq("email", email)
            .execute()
        )

        if not response.data:
            self.message_label.text = "Invalid email or password."
            return

        student = response.data[0]

        if not verify_password(password, student.get("password")):
            self.message_label.text = "Invalid email or password."
            return

        SessionState.student = student
        self.manager.current = "student_dashboard"
