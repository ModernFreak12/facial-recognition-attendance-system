from datetime import datetime

from app.database.class_queries import start_class
from app.database.attendance_queries import mark_attendance


course_id = "ef7b243e-86b2-4216-8e21-34b45bc17b43"
student_id = "e3a25582-fde7-4d02-a404-3d27d2613044"

session = start_class(course_id)

print(session)

class_id = session["class_id"]
class_start_time = datetime.now()

mark_attendance(class_id, student_id, class_start_time)