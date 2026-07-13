import bcrypt
from datetime import datetime

from app.services.supabase_client import get_supabase
supabase = get_supabase()

# ==========================
# Fetch all students
# ==========================
response = (
    supabase.table("students")
    .select("student_id, date_of_birth")
    .execute()
)

students = response.data

if not students:
    print("No students found.")
    exit()


# ==========================
# Update passwords
# ==========================
for student in students:

    student_id = student["student_id"]
    dob = student["date_of_birth"]

    if dob is None:
        print(f"Skipping {student_id}: No date_of_birth")
        continue

    # Convert YYYY-MM-DD -> DDMMYYYY
    password = datetime.strptime(dob, "%Y-%m-%d").strftime("%d%m%Y")

    # Hash using bcrypt
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")

    # Update database
    (
        supabase.table("students")
        .update({"password": hashed_password})
        .eq("student_id", student_id)
        .execute()
    )

    print(f"Updated {student_id} -> Password: {password}")

print("\nDone! All student passwords updated.")