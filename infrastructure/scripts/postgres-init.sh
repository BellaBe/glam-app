#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    
    -- Create all databases
    CREATE DATABASE "shopify_session_db";
    
    CREATE DATABASE "analytics_db";
    CREATE DATABASE "billing_db";
    CREATE DATABASE "catalog_db";
    CREATE DATABASE "credit_db";
    CREATE DATABASE "merchant_db";
    CREATE DATABASE "notification_db";
    CREATE DATABASE "recommendation_db";
    CREATE DATABASE "season_compatibility_db";
    CREATE DATABASE "selfie_db";
    CREATE DATABASE "token_db";
    CREATE DATABASE "webhook_db";
    
    -- Create all users
    
    CREATE USER shopify_session_db_user WITH PASSWORD '$SHOPIFY_SESSION_DB_PASSWORD';
    
    CREATE USER analytics_db_user WITH PASSWORD '$ANALYTICS_DB_PASSWORD';
    CREATE USER billing_db_user WITH PASSWORD '$BILLING_DB_PASSWORD';
    CREATE USER catalog_db_user WITH PASSWORD '$CATALOG_DB_PASSWORD';
    CREATE USER credit_db_user WITH PASSWORD '$CREDIT_DB_PASSWORD';
    CREATE USER merchant_db_user WITH PASSWORD '$MERCHANT_DB_PASSWORD';
    CREATE USER notification_db_user WITH PASSWORD '$NOTIFICATION_DB_PASSWORD';
    CREATE USER recommendation_db_user WITH PASSWORD '$RECOMMENDATION_DB_PASSWORD';
    CREATE USER season_compatibility_db_user WITH PASSWORD '$SEASON_COMPATIBILITY_DB_PASSWORD';
    CREATE USER selfie_db_user WITH PASSWORD '$SELFIE_AI_DB_PASSWORD';
    CREATE USER token_db_user WITH PASSWORD '$TOKEN_DB_PASSWORD';
    CREATE USER webhook_db_user WITH PASSWORD '$WEBHOOK_DB_PASSWORD';
    
    
    -- Grant all privileges
    GRANT ALL PRIVILEGES ON DATABASE "shopify_session_db" TO shopify_session_db_user;

    GRANT ALL PRIVILEGES ON DATABASE "analytics_db" TO analytics_db_user;
    GRANT ALL PRIVILEGES ON DATABASE "billing_db" TO billing_db_user;
    GRANT ALL PRIVILEGES ON DATABASE "catalog_db" TO catalog_db_user;
    GRANT ALL PRIVILEGES ON DATABASE "credit_db" TO credit_db_user;
    GRANT ALL PRIVILEGES ON DATABASE "merchant_db" TO merchant_db_user;
    GRANT ALL PRIVILEGES ON DATABASE "notification_db" TO notification_db_user;
    GRANT ALL PRIVILEGES ON DATABASE "recommendation_db" TO recommendation_db_user;
    GRANT ALL PRIVILEGES ON DATABASE "season_compatibility_db" TO season_db_user;
    GRANT ALL PRIVILEGES ON DATABASE "selfie_db" TO selfie_db_user;
    GRANT ALL PRIVILEGES ON DATABASE "token_db" TO token_db_user;
    GRANT ALL PRIVILEGES ON DATABASE "webhook_db" TO webhook_db_user;
    
EOSQL