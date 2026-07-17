-- ==========================
-- Students
-- ==========================
CREATE TABLE public.students (
    student_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    univ_roll_no VARCHAR(30) NOT NULL UNIQUE,
    name TEXT NOT NULL,
    department TEXT NOT NULL CHECK (
        department IN ('CSE', 'IT', 'AIML', 'ECE', 'EE')
    ),
    class_roll_no INTEGER NOT NULL,
    admission_year INTEGER NOT NULL,
    date_of_birth DATE NOT NULL,
    email TEXT NOT NULL UNIQUE,
    division TEXT CHECK (
        division IN ('1', '2', '3')
    ),
    password TEXT
);

-- ==========================
-- Student Embeddings
-- ==========================
CREATE TABLE public.student_embeddings (
    embedding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    embedding VECTOR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    augmentation TEXT,

    CONSTRAINT fk_student_embeddings_student
        FOREIGN KEY (student_id)
        REFERENCES public.students(student_id)
        ON DELETE CASCADE
);

-- ==========================
-- Teachers
-- ==========================
CREATE TABLE public.teachers (
    teacher_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL CHECK (
        department IN ('CSE', 'IT', 'AIML', 'ECE', 'EE')
    ),
    password TEXT
);

-- ==========================
-- Courses
-- ==========================
CREATE TABLE public.courses (
    course_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_code VARCHAR(20) NOT NULL UNIQUE,
    course_name TEXT NOT NULL,
    semester INTEGER NOT NULL CHECK (
        semester BETWEEN 1 AND 8
    ),
    course_type VARCHAR(20) NOT NULL
);

-- ==========================
-- Student-Course Mapping
-- ==========================
CREATE TABLE public.student_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    course_id UUID NOT NULL,

    CONSTRAINT fk_student_courses_student
        FOREIGN KEY (student_id)
        REFERENCES public.students(student_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_student_courses_course
        FOREIGN KEY (course_id)
        REFERENCES public.courses(course_id)
        ON DELETE CASCADE,

    CONSTRAINT unique_student_course
        UNIQUE (student_id, course_id)
);

-- ==========================
-- Teacher-Course Mapping
-- ==========================
CREATE TABLE public.teacher_courses (
    teacher_id UUID NOT NULL,
    course_id UUID NOT NULL,

    PRIMARY KEY (teacher_id, course_id),

    CONSTRAINT fk_teacher_courses_teacher
        FOREIGN KEY (teacher_id)
        REFERENCES public.teachers(teacher_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_teacher_courses_course
        FOREIGN KEY (course_id)
        REFERENCES public.courses(course_id)
        ON DELETE CASCADE
);

-- ==========================
-- Class Sessions
-- ==========================
CREATE TABLE public.class_sessions (
    class_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL,
    class_date DATE DEFAULT CURRENT_DATE,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,

    CONSTRAINT fk_class_sessions_course
        FOREIGN KEY (course_id)
        REFERENCES public.courses(course_id)
        ON DELETE CASCADE
);

-- ==========================
-- Attendance
-- ==========================
CREATE TABLE public.attendance (
    attendance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    class_id UUID NOT NULL,
    student_id UUID NOT NULL,

    status TEXT NOT NULL CHECK (
        status IN ('PRESENT', 'LATE', 'ABSENT')
    ),

    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_attendance_class
        FOREIGN KEY (class_id)
        REFERENCES public.class_sessions(class_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_attendance_student
        FOREIGN KEY (student_id)
        REFERENCES public.students(student_id)
        ON DELETE CASCADE,

    CONSTRAINT unique_class_student
        UNIQUE (class_id, student_id)
);