from app.services.report_generator import (
    export_weekly_report,
    export_monthly_report
)

course_id = (
    "ef7b243e-86b2-4216-8e21-34b45bc17b43"
)

export_weekly_report(
    course_id,
    "2026-05-01",
    "2026-05-31"
)

export_monthly_report(
    course_id,
    5,
    2026
)