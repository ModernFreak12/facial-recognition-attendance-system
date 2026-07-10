from app.services.class_runner import run_class
from app.database.course_queries import get_all_courses


def main():
    courses = get_all_courses()

    print("\nCourses:\n")

    for i, course in enumerate(courses):
        print(f"{i+1}. {course['course_name']}")

    choice = int(input("\nSelect course: "))

    selected_course = courses[choice - 1]

    run_class(selected_course["course_id"])


if __name__ == "__main__":
    main()