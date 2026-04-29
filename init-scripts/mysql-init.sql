-- MySQL init script: create test database if not exists
-- The database is also set via MYSQL_DATABASE env var, this is a fallback
CREATE DATABASE IF NOT EXISTS business_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Example table for testing
-- CREATE TABLE IF NOT EXISTS test_data (
--   id       BIGINT AUTO_INCREMENT PRIMARY KEY,
--   name     VARCHAR(255) NOT NULL,
--   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
