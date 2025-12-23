-- MySQL initialization script
-- This script runs when MySQL container starts for the first time

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS payment_db;

-- Create user if it doesn't exist
CREATE USER IF NOT EXISTS 'payment_user'@'%' IDENTIFIED BY 'mysql_password_123';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON payment_db.* TO 'payment_user'@'%';

-- Flush privileges to apply changes
FLUSH PRIVILEGES;