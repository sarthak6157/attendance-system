-- ═══════════════════════════════════════════════════════════
-- SUPABASE SETUP — Run this in Supabase SQL Editor
-- Go to: Supabase → SQL Editor → New query → paste → Run
-- ═══════════════════════════════════════════════════════════

-- Drop old tables if starting fresh (CAREFUL: deletes all data)
-- Comment these out if you want to keep existing data
DROP TABLE IF EXISTS attendance_records CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS timetable_slots CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- The app will auto-create all tables on first startup via SQLAlchemy.
-- Just run the DROP statements above to clear old data, then deploy.

-- After deployment, verify tables were created:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
