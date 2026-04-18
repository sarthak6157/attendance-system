-- Run this in Neon SQL Editor before deploying v4
-- It adds new columns without deleting existing data

ALTER TABLE users ADD COLUMN IF NOT EXISTS branch VARCHAR(150);
ALTER TABLE users ADD COLUMN IF NOT EXISTS section VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS semester VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS course VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS face_registered BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS face_embedding TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS face_image_b64 TEXT;

ALTER TABLE sessions ADD COLUMN IF NOT EXISTS timetable_id INTEGER;
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS branch VARCHAR(150);
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS section VARCHAR(20);
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS semester VARCHAR(20);
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS course_type VARCHAR(100);
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS gps_lat VARCHAR(50);
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS gps_lng VARCHAR(50);

ALTER TABLE attendance_records ADD COLUMN IF NOT EXISTS student_lat VARCHAR(50);
ALTER TABLE attendance_records ADD COLUMN IF NOT EXISTS student_lng VARCHAR(50);

ALTER TABLE courses ADD COLUMN IF NOT EXISTS branch VARCHAR(150);
ALTER TABLE courses ADD COLUMN IF NOT EXISTS section VARCHAR(20);
ALTER TABLE courses ADD COLUMN IF NOT EXISTS semester VARCHAR(20);
ALTER TABLE courses ADD COLUMN IF NOT EXISTS course_type VARCHAR(100);

ALTER TABLE system_settings ADD COLUMN IF NOT EXISTS manual_edit_window INTEGER DEFAULT 10;

-- Create timetable_slots table if it doesn't exist
CREATE TABLE IF NOT EXISTS timetable_slots (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    faculty_id INTEGER NOT NULL REFERENCES users(id),
    day_of_week VARCHAR(20) NOT NULL,
    start_time VARCHAR(10) NOT NULL,
    end_time VARCHAR(10) NOT NULL,
    room VARCHAR(100),
    branch VARCHAR(150),
    section VARCHAR(20),
    semester VARCHAR(20),
    course_type VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

SELECT 'Migration complete!' as status;
