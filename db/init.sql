-- SIEM Analytics System Database Initialization Schema

CREATE DATABASE IF NOT EXISTS siem_db;
USE siem_db;

-- 1. Logs Table
CREATE TABLE IF NOT EXISTS logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  event_uuid VARCHAR(36) NOT NULL UNIQUE,
  timestamp DATETIME(3) NOT NULL,
  source_host VARCHAR(255) DEFAULT 'localhost',
  source_type VARCHAR(50) NOT NULL COMMENT 'ssh, nginx, apache, syslog, windows, custom',
  event_type VARCHAR(100) NOT NULL COMMENT 'login_failed, login_success, port_scan, http_request, privilege_change, generic',
  src_ip VARCHAR(45) DEFAULT NULL,
  dest_ip VARCHAR(45) DEFAULT NULL,
  src_port INT DEFAULT NULL,
  dest_port INT DEFAULT NULL,
  user VARCHAR(255) DEFAULT NULL,
  message_raw TEXT NOT NULL,
  severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'low',
  tags JSON DEFAULT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_timestamp (timestamp),
  INDEX idx_src_ip (src_ip),
  INDEX idx_dest_ip (dest_ip),
  INDEX idx_event_type (event_type),
  INDEX idx_source_type (source_type),
  INDEX idx_severity (severity),
  INDEX idx_timestamp_srcip (timestamp, src_ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  alert_uuid VARCHAR(36) NOT NULL UNIQUE,
  rule_name VARCHAR(100) NOT NULL,
  severity ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'medium',
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  related_log_ids JSON DEFAULT NULL,
  src_ip VARCHAR(45) DEFAULT NULL,
  dest_ip VARCHAR(45) DEFAULT NULL,
  triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status ENUM('open', 'acknowledged', 'resolved') DEFAULT 'open',
  INDEX idx_alert_triggered (triggered_at),
  INDEX idx_alert_status (status),
  INDEX idx_alert_severity (severity),
  INDEX idx_alert_srcip (src_ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Users Table (for Dashboard Authentication)
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  hashed_password VARCHAR(255) NOT NULL,
  role ENUM('admin', 'analyst', 'viewer') DEFAULT 'analyst',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Detection Rule Configurations Table
CREATE TABLE IF NOT EXISTS rule_configs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  rule_name VARCHAR(100) NOT NULL UNIQUE,
  enabled BOOLEAN DEFAULT TRUE,
  window_minutes INT DEFAULT 5,
  threshold INT DEFAULT 5,
  severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'high',
  description TEXT,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Initial Seed Data: Default Detection Rules
INSERT INTO rule_configs (rule_name, enabled, window_minutes, threshold, severity, description)
VALUES 
  ('brute_force', TRUE, 5, 5, 'high', 'Detects multiple failed login attempts from a single source IP'),
  ('port_scan', TRUE, 1, 15, 'high', 'Detects connections to multiple distinct destination ports from a single IP'),
  ('ddos_spike', TRUE, 1, 100, 'critical', 'Detects abnormal high volume request bursts to a single destination IP'),
  ('privilege_escalation', TRUE, 5, 1, 'critical', 'Detects sensitive privilege changes (sudo, group modification, admin access)')
ON DUPLICATE KEY UPDATE rule_name=VALUES(rule_name);

-- Default Admin User (Password: admin123 hashed via bcrypt)
-- Note: In FastAPI app initialization, default admin will also be auto-seeded if not present.
