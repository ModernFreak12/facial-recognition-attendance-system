from datetime import datetime, timezone
from app.services.supabase_client import supabase


LATE_THRESHOLD_MINUTES = 15


def mark_attendance(class_id, student_id, class_start_time):
    """
    Insert attendance once; on repeat detections in the same
    session, just refresh last_seen instead of dropping the update.
    """

    now = datetime.now(timezone.utc)

    # Prevent duplicate attendance rows, but keep last_seen fresh
    existing = (
        supabase.table("attendance")
        .select("*")
        .eq("class_id", class_id)
        .eq("student_id", student_id)
        .execute()
    )

    if existing.data:
        (
            supabase.table("attendance")
            .update({"last_seen": now.isoformat()})
            .eq("class_id", class_id)
            .eq("student_id", student_id)
            .execute()
        )
        return

    minutes_elapsed = (now - class_start_time).total_seconds() / 60

    status = "LATE" if minutes_elapsed > LATE_THRESHOLD_MINUTES else "PRESENT"

    (
        supabase.table("attendance")
        .insert({
            "class_id": class_id,
            "student_id": student_id,
            "status": status,
            "first_seen": now.isoformat(),
            "last_seen": now.isoformat()
        })
        .execute()
    )

    print(f"✅ Attendance marked: {student_id} ({status})")


def mark_absent_students(class_id, course_id):
    """
    Mark students not detected
    as ABSENT.
    """

    from app.database.course_queries import get_students_for_course
    enrolled_students = get_students_for_course(course_id)

    attendance_response = (
        supabase.table("attendance")
        .select("student_id")
        .eq("class_id", class_id)
        .execute()
    )

    present_students = {
        row["student_id"]
        for row in attendance_response.data
    }

    absent_students = []

    for student in enrolled_students:
        sid = student["student_id"]

        if sid not in present_students:
            absent_students.append({
                "class_id": class_id,
                "student_id": sid,
                "status": "ABSENT"
            })

    if absent_students:
        (
            supabase.table("attendance")
            .insert(absent_students)
            .execute()
        )

    print(f"Marked {len(absent_students)} students absent.")