#!/bin/bash
set -e

echo "=== GlamYouUp Database Initialization ==="
echo "Starting at $(date)"

DATABASES=(
    "analytics_db"
    "billing_db"
    "catalog_db"
    "credit_db"
    "merchant_db"
    "notification_db"
    "recommendation_db"
    "season_compatibility_db"
    "selfie_db"
    "token_db"
    "webhook_db"
)

for DB in "${DATABASES[@]}"; do
    echo "Creating database: $DB"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $DB
            WITH 
            ENCODING = 'UTF8'
            LC_COLLATE = 'C'
            LC_CTYPE = 'C'
            TEMPLATE = template0;

        GRANT ALL PRIVILEGES ON DATABASE $DB TO $POSTGRES_USER;
        
        \c $DB
        
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
        CREATE EXTENSION IF NOT EXISTS "pg_trgm";
        CREATE EXTENSION IF NOT EXISTS "btree_gin";
        CREATE EXTENSION IF NOT EXISTS "btree_gist";
        
        GRANT ALL ON SCHEMA public TO $POSTGRES_USER;
        GRANT ALL ON ALL TABLES IN SCHEMA public TO $POSTGRES_USER;
        GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO $POSTGRES_USER;
        GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO $POSTGRES_USER;
        
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
            GRANT ALL ON TABLES TO $POSTGRES_USER;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
            GRANT ALL ON SEQUENCES TO $POSTGRES_USER;
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
            GRANT ALL ON FUNCTIONS TO $POSTGRES_USER;
        
        ALTER DATABASE $DB SET random_page_cost = 1.1;
        ALTER DATABASE $DB SET effective_io_concurrency = 200;
        ALTER DATABASE $DB SET statement_timeout = '30s';
        ALTER DATABASE $DB SET idle_in_transaction_session_timeout = '5min';
EOSQL
    echo "✅ Created database: $DB"
done

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname=postgres <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
    
    CREATE OR REPLACE VIEW db_sizes AS
    SELECT 
        datname as database,
        pg_size_pretty(pg_database_size(datname)) as size,
        pg_database_size(datname) as bytes
    FROM pg_database
    WHERE datname NOT IN ('postgres', 'template0', 'template1')
    ORDER BY pg_database_size(datname) DESC;
    
    CREATE OR REPLACE VIEW db_connections AS
    SELECT 
        datname as database,
        count(*) as connections,
        max(backend_start) as oldest_connection,
        count(*) FILTER (WHERE state = 'active') as active,
        count(*) FILTER (WHERE state = 'idle') as idle,
        count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
    FROM pg_stat_activity
    WHERE datname IS NOT NULL
    GROUP BY datname
    ORDER BY count(*) DESC;
EOSQL

echo "✅ Initialization Complete"
echo "Total databases: ${#DATABASES[@]}"