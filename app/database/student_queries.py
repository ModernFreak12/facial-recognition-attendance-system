from app.services.supabase_client import supabase


def get_student_courses(student_id):
    """
    Get student's enrolled courses
    and attendance %.
    """

    course_response = (
        supabase.table("student_courses")
        .select("""
            course_id,
            courses (
                course_name,
                course_code
            )
        """)
        .eq("student_id", student_id)
        .execute()
    )

    courses = course_response.data or []

    result = []

    for row in courses:
        course_id = row["course_id"]
        course_name = row["courses"]["course_name"]

        attendance_response = (
            supabase.table("attendance")
            .select("""
                status,
                class_sessions!inner(
                    course_id
                )
            """)
            .eq("student_id", student_id)
            .eq("class_sessions.course_id", course_id)
            .execute()
        )

        attendance_rows = attendance_response.data or []

        total = len(attendance_rows)

        present = sum(
            1 for r in attendance_rows
            if r["status"] in ("PRESENT", "LATE")
        )

        percentage = (present / total) * 100 if total > 0 else 0

        result.append({
            "course_id": course_id,
            "course_name": course_name,
            "percentage": round(percentage, 2)
        })

    return result


def get_course_history(student_id, course_id):
    """
    Attendance history
    for selected course.
    """

    response = (
        supabase.table("attendance")
        .select("""
            status,
            class_sessions!inner(
                class_date
            )
        """)
        .eq("student_id", student_id)
        .eq("class_sessions.course_id", course_id)
        .order("class_sessions(class_date)")
        .execute()
    )

    return response.data or []


def get_course_calendar_data(student_id, course_id):
    """
    Attendance history reshaped for the calendar widget:
    {"YYYY-MM-DD": "PRESENT" | "LATE" | "ABSENT"}
    """

    history = get_course_history(student_id, course_id)

    return {
        row["class_sessions"]["class_date"]: row["status"]
        for row in history
        if row.get("class_sessions", {}).get("class_date")
    }
