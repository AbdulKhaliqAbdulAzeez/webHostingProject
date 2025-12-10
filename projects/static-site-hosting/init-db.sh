#!/bin/bash
set -e

# Create test database for pytest
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE fastapi_test_db;
EOSQL
