from app.services.supabase_client import supabase


def get_teacher_courses(teacher_id):
    """
    Fetch courses assigned
    to teacher.
    """

    response = (
        supabase.table("teacher_courses")
        .select("""
            course_id,
            courses (
                course_name,
                course_code,
                semester
            )
        """)
        .eq("teacher_id", teacher_id)
        .execute()
    )

    return response.data or []


def get_course_attendance(course_id, date):
    """
    Get attendance for a
    course on a date.
    """

    session_response = (
        supabase.table("class_sessions")
        .select("class_id")
        .eq("course_id", course_id)
        .eq("class_date", date)
        .execute()
    )

    if not session_response.data:
        return []

    class_id = session_response.data[0]["class_id"]

    attendance_response = (
        supabase.table("attendance")
        .select("""
            status,
            students (
                name,
                univ_roll_no
            )
        """)
        .eq("class_id", class_id)
        .execute()
    )

    return attendance_response.data or []


def get_course_calendar_data(course_id):
    """
    One entry per session date for the calendar widget:
    {"YYYY-MM-DD": "PRESENT" | "LATE" | "ABSENT"}

    A session is marked PRESENT (green) if >=75% of students were
    present/late, LATE (orange) if 50-75%, ABSENT (red) below that.
    """

    sessions_response = (
        supabase.table("class_sessions")
        .select("class_id, class_date")
        .eq("course_id", course_id)
        .execute()
    )

    sessions = sessions_response.data or []

    calendar_data = {}

    for session in sessions:
        attendance_response = (
            supabase.table("attendance")
            .select("status")
            .eq("class_id", session["class_id"])
            .execute()
        )

        rows = attendance_response.data or []
        total = len(rows)
        present = sum(1 for r in rows if r["status"] in ("PRESENT", "LATE"))
        rate = (present / total) if total > 0 else 0

        if rate >= 0.75:
            status = "PRESENT"
        elif rate >= 0.5:
            status = "LATE"
        else:
            status = "ABSENT"

        calendar_data[session["class_date"]] = status

    return calendar_data


def get_course_history_table(course_id):
    """
    One row per session with attendance counts, used for the
    course-wide table view and the weekly/monthly reports:
    [{"class_date": ..., "present": n, "late": n, "absent": n, "total": n}, ...]
    """

    sessions_response = (
        supabase.table("class_sessions")
        .select("class_id, class_date")
        .eq("course_id", course_id)
        .order("class_date")
        .execute()
    )

    sessions = sessions_response.data or []

    rows = []

    for session in sessions:
        attendance_response = (
            supabase.table("attendance")
            .select("status")
            .eq("class_id", session["class_id"])
            .execute()
        )

        records = attendance_response.data or []

        rows.append({
            "class_date": session["class_date"],
            "present": sum(1 for r in records if r["status"] == "PRESENT"),
            "late": sum(1 for r in records if r["status"] == "LATE"),
            "absent": sum(1 for r in records if r["status"] == "ABSENT"),
            "total": len(records),
        })

    return rows
