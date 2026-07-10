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