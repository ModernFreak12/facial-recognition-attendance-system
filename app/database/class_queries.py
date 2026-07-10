from app.services.supabase_client import supabase


def start_class(course_id):
    """
    Creates a class session.

    Returns:
        class_id
        started_at
    """

    response = (
        supabase.table("class_sessions")
        .insert({"course_id": course_id})
        .execute()
    )

    return response.data[0]


def end_class(class_id):
    """
    End class session.
    """

    (
        supabase.table("class_sessions")
        .update({"ended_at": "now()"})
        .eq("class_id", class_id)
        .execute()
    )