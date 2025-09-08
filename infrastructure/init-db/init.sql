-- init-db/init.sql

-- Create role if it does not exist
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE rolname = 'odynn_platform'
   ) THEN
      CREATE ROLE odynn_platform WITH LOGIN PASSWORD 'Pass123';
   END IF;
END
$do$;

-- Create database if it does not exist
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_database
      WHERE datname = 'odynn_platform'
   ) THEN
      PERFORM dblink_exec('host=localhost user=odynn password=Pass123', 'CREATE DATABASE odynn_platform OWNER odynn_platform');
   END IF;
END
$do$;

-- Grant privileges (optional if owned already)
GRANT ALL PRIVILEGES ON DATABASE odynn_platform TO odynn_platform;
