-- Hermes Text-to-SQL Agent - Database Initialization Script

-- Create sample database if not exists
CREATE DATABASE IF NOT EXISTS hermes DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE hermes;

-- Create audit_log table for operation tracking
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    sql_query TEXT NOT NULL,
    execution_time INT,
    result_status VARCHAR(50),
    execution_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approval_status VARCHAR(50) DEFAULT 'pending',
    approval_comment TEXT,
    INDEX idx_timestamp (execution_timestamp),
    INDEX idx_user (user_id),
    INDEX idx_operation (operation_type),
    INDEX idx_approval (approval_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample data for testing
INSERT INTO audit_log (user_id, operation_type, table_name, sql_query, execution_time, result_status, approval_status) VALUES
('test_user', 'SELECT', 'employees', 'SELECT * FROM employees', 15, 'success', 'approved'),
('admin', 'INSERT', 'audit_log', 'INSERT INTO audit_log (user_id, operation_type, table_name) VALUES (\'user1\', \'SELECT\', \'users\')', 20, 'success', 'approved');

-- Create sample users table for demo
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
