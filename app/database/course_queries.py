from app.services.supabase_client import supabase


def get_all_courses():
    response = (
        supabase.table("courses")
        .select("*")
        .execute()
    )

    return response.data


def get_students_for_course(course_id):
    """
    Fetch enrolled students and embeddings
    for selected course.
    """

    enrollment_response = (
        supabase.table("student_courses")
        .select("*")
        .eq("course_id", course_id)
        .execute()
    )

    enrollments = enrollment_response.data

    students = []

    for enrollment in enrollments:
        student_id = enrollment["student_id"]

        student_response = (
            supabase.table("students")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        if not student_response.data:
            continue

        student = student_response.data[0]

        embedding_response = (
            supabase.table("student_embeddings")
            .select("embedding")
            .eq("student_id", student_id)
            .execute()
        )

        if not embedding_response.data:
            continue

        embedding = embedding_response.data[0]["embedding"]

        students.append({
            "student_id": student["student_id"],
            "name": student["name"],
            "roll_no": student["univ_roll_no"],
            "embedding": embedding
        })

    return students