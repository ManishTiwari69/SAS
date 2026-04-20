-- ================================================================
--  Attenad  —  RBAC + Face Retrain Migration
--  Run ONCE against attendance_db
--  Compatible: MySQL 5.7+  /  MariaDB 10.3+
-- ================================================================

USE attendance_db;

-- ── 1. Add role + status to admins ───────────────────────────────────
ALTER TABLE admins
  ADD COLUMN IF NOT EXISTS role   VARCHAR(20) NOT NULL DEFAULT 'Teacher'
      COMMENT 'Super | Teacher',
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active'
      COMMENT 'active | inactive';

-- ── 2. Bootstrap first admin as Super ────────────────────────────────
-- Change admin_id = 1 to your actual first admin's id if different
UPDATE admins SET role='Super', status='active' WHERE admin_id = 1;
UPDATE admins SET role='Teacher', status='active' WHERE admin_id != 1;

-- ── 3. Verify ─────────────────────────────────────────────────────────
SELECT admin_id, username, role, status FROM admins;

-- ================================================================
-- END
-- ================================================================
