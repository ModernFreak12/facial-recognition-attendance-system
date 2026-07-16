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


def get_course_history_table(course_id):
    """
    One row per session with attendance counts, used for the
    weekly/monthly reports:
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


def get_course_attendance_matrix(course_id):
    """
    Student x session-date attendance grid for the teacher dashboard table.

    Returns:
    {
        "dates": [class_date, class_date, ...],   # sorted session dates
        "students": [
            {
                "student_id": ...,
                "name": "...",
                "roll_no": "...",                  # from students.univ_roll_no
                "attendance": {class_date: "PRESENT" | "LATE" | "ABSENT", ...}
            },
            ...
        ]
    }

    Students enrolled in the course but with no attendance row for a given
    session are defaulted to "ABSENT" for that date, so they still appear
    in the table instead of being silently skipped.
    """

    sessions_response = (
        supabase.table("class_sessions")
        .select("class_id, class_date")
        .eq("course_id", course_id)
        .order("class_date")
        .execute()
    )

    sessions = sessions_response.data or []
    if not sessions:
        return {"dates": [], "students": []}

    session_ids = [s["class_id"] for s in sessions]
    session_dates = [s["class_date"] for s in sessions]
    session_date_map = {s["class_id"]: s["class_date"] for s in sessions}

    # Full roster for the course, so students with zero attendance rows
    # still show up as ABSENT across every session date.
    # NOTE: assumes a "student_courses" enrollment junction table with
    # student_id + course_id — adjust the table/column names below if yours differ.
    enrollment_response = (
        supabase.table("student_courses")
        .select("""
            student_id,
            students (
                name,
                univ_roll_no
            )
        """)
        .eq("course_id", course_id)
        .execute()
    )

    enrollments = enrollment_response.data or []

    students_map = {}
    for enrollment in enrollments:
        sid = enrollment["student_id"]
        student = enrollment["students"]
        students_map[sid] = {
            "student_id": sid,
            "name": student["name"],
            "roll_no": student["univ_roll_no"],
            "attendance": {d: "ABSENT" for d in session_dates},
        }

    attendance_response = (
        supabase.table("attendance")
        .select("student_id, class_id, status")
        .in_("class_id", session_ids)
        .execute()
    )

    for row in attendance_response.data or []:
        sid = row["student_id"]
        class_date = session_date_map[row["class_id"]]
        if sid in students_map:
            students_map[sid]["attendance"][class_date] = row["status"]

    students = sorted(students_map.values(), key=lambda s: (s["roll_no"] or ""))

    return {"dates": session_dates, "students": students}