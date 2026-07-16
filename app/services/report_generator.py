import csv
import calendar
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from collections import defaultdict

from app.services.supabase_client import supabase

REPORT_FOLDER = "reports"


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def _ensure_report_folder():
    Path(REPORT_FOLDER).mkdir(exist_ok=True)


def _status_short(status):
    mapping = {
        "PRESENT": "P",
        "LATE": "L",
        "ABSENT": "A"
    }
    return mapping.get(status, "A")


def _to_local_time(timestamp):
    """
    Convert UTC timestamp from DB
    to local IST time for CSV.
    """

    if not timestamp:
        return ""

    # Supabase timestamp string → datetime
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    local_dt = dt.astimezone(ZoneInfo("Asia/Kolkata"))
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")


# -------------------------------------------------------
# SESSION REPORT
# -------------------------------------------------------
def export_session_report(class_id):
    """
    One CSV per class session.
    """
    _ensure_report_folder()

    response = (
        supabase.table("attendance")
        .select("""
            status,
            first_seen,
            last_seen,
            students (
                univ_roll_no,
                name
            )
        """)
        .eq("class_id", class_id)
        .execute()
    )

    rows = response.data or []
    file_path = Path(REPORT_FOLDER) / f"session_{class_id}.csv"

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Roll Number", "Name", "Status", "First Seen", "Last Seen"])

        for row in rows:
            student = row["students"]
            writer.writerow([
                student["univ_roll_no"],
                student["name"],
                row["status"],
                _to_local_time(row["first_seen"]),
                _to_local_time(row["last_seen"])
            ])

    print(f"Session report generated: {file_path}")
    return file_path


# -------------------------------------------------------
# COMMON ENGINE
# -------------------------------------------------------
def _build_attendance_matrix(course_id, start_date=None, end_date=None):
    """
    Shared engine for weekly/monthly/total reports.
    start_date/end_date are optional — omit both for an unbounded,
    whole-course range (used by the total report).
    """

    # ----------------------------------------
    # Get sessions
    # ----------------------------------------
    query = (
        supabase.table("class_sessions")
        .select("""
            class_id,
            class_date
        """)
        .eq("course_id", course_id)
    )

    if start_date:
        query = query.gte("class_date", start_date)
    if end_date:
        query = query.lte("class_date", end_date)

    session_response = query.order("class_date").execute()

    sessions = session_response.data or []
    if not sessions:
        print("No sessions found.")
        return None

    session_ids = [s["class_id"] for s in sessions]
    session_dates = [s["class_date"] for s in sessions]

    # ----------------------------------------
    # Get attendance
    # ----------------------------------------
    attendance_response = (
        supabase.table("attendance")
        .select("""
            student_id,
            class_id,
            status,
            students (
                univ_roll_no,
                name
            )
        """)
        .in_("class_id", session_ids)
        .execute()
    )

    attendance_rows = attendance_response.data or []

    # ----------------------------------------
    # Organize per student
    # ----------------------------------------
    student_data = defaultdict(
        lambda: {
            "roll": "",
            "name": "",
            "attendance": {}
        }
    )

    session_date_map = {s["class_id"]: s["class_date"] for s in sessions}

    for row in attendance_rows:
        sid = row["student_id"]
        student = row["students"]
        class_id = row["class_id"]
        date = session_date_map[class_id]

        student_data[sid]["roll"] = student["univ_roll_no"]
        student_data[sid]["name"] = student["name"]
        student_data[sid]["attendance"][date] = _status_short(row["status"])

    return student_data, session_dates


def _write_matrix_csv(file_path, student_data, session_dates):
    """
    Shared CSV writer for weekly/monthly/total reports:
    Roll Number, Name, one column per session date, Attendance %.
    """
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        header = ["Roll Number", "Name"]
        header.extend(session_dates)
        header.append("Attendance %")

        writer.writerow(header)
        total_sessions = len(session_dates)

        for student in student_data.values():
            row = [student["roll"], student["name"]]
            present_count = 0

            for date in session_dates:
                status = student["attendance"].get(date, "A")
                row.append(status)
                if status in ("P", "L"):
                    present_count += 1

            percentage = (present_count / total_sessions) * 100 if total_sessions else 0
            row.append(round(percentage, 2))
            writer.writerow(row)


# -------------------------------------------------------
# WEEKLY REPORT
# -------------------------------------------------------
def export_weekly_report(course_id, start_date, end_date):
    _ensure_report_folder()

    result = _build_attendance_matrix(course_id, start_date, end_date)

    if result is None:
        return

    student_data, session_dates = result

    file_path = Path(REPORT_FOLDER) / f"weekly_{start_date}_{end_date}.csv"
    _write_matrix_csv(file_path, student_data, session_dates)

    return file_path


# -------------------------------------------------------
# MONTHLY REPORT
# -------------------------------------------------------
def export_monthly_report(course_id, month, year):
    _ensure_report_folder()

    _, last_day = calendar.monthrange(year, month)

    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"

    result = _build_attendance_matrix(course_id, start_date, end_date)

    if result is None:
        return

    student_data, session_dates = result

    file_path = Path(REPORT_FOLDER) / f"monthly_{year}_{month:02d}.csv"
    _write_matrix_csv(file_path, student_data, session_dates)

    print("✅ Monthly report generated:")
    print(file_path)

    return file_path


# -------------------------------------------------------
# TOTAL COURSE REPORT
# -------------------------------------------------------
def export_total_report(course_id):
    """
    Full-course report covering every session ever held for the course,
    with no date range restriction.
    """
    _ensure_report_folder()

    result = _build_attendance_matrix(course_id)

    if result is None:
        return

    student_data, session_dates = result

    file_path = Path(REPORT_FOLDER) / f"total_course_{course_id}.csv"
    _write_matrix_csv(file_path, student_data, session_dates)

    print("✅ Total course report generated:")
    print(file_path)

    return file_path