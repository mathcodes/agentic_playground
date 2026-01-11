#!/bin/bash
# PostgreSQL Setup Script for Voice-to-SQL Agent

echo "=========================================="
echo "PostgreSQL Setup for Voice-to-SQL"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}This script will:${NC}"
echo "1. Temporarily modify PostgreSQL authentication to 'trust'"
echo "2. Set a password for your PostgreSQL user"
echo "3. Create the voice_sql_test database"
echo "4. Initialize the database with sample data"
echo "5. Restore secure authentication"
echo ""
echo -e "${RED}You will need to enter your macOS sudo password.${NC}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Setup cancelled."
    exit 1
fi

echo ""
echo "Step 1: Backing up pg_hba.conf..."
sudo cp /usr/local/var/postgresql@15/pg_hba.conf /usr/local/var/postgresql@15/pg_hba.conf.backup

echo "Step 2: Enabling trust authentication temporarily..."
sudo sed -i '' 's/md5/trust/g' /usr/local/var/postgresql@15/pg_hba.conf

echo "Step 3: Restarting PostgreSQL..."
brew services restart postgresql@15
sleep 3

echo "Step 4: Setting password for user 'jonchristie'..."
psql postgres -c "ALTER USER jonchristie WITH PASSWORD 'postgres';" || {
    echo "Creating user first..."
    psql postgres -c "CREATE USER jonchristie WITH PASSWORD 'postgres' SUPERUSER;"
}

echo "Step 5: Creating database..."
psql postgres -c "DROP DATABASE IF EXISTS voice_sql_test;"
psql postgres -c "CREATE DATABASE voice_sql_test;"

echo "Step 6: Restoring md5 authentication..."
sudo cp /usr/local/var/postgresql@15/pg_hba.conf.backup /usr/local/var/postgresql@15/pg_hba.conf

echo "Step 7: Restarting PostgreSQL..."
brew services restart postgresql@15
sleep 3

echo "Step 8: Creating .pgpass file for passwordless access..."
echo "localhost:5432:*:jonchristie:postgres" > ~/.pgpass
echo "*:*:*:jonchristie:postgres" >> ~/.pgpass
chmod 600 ~/.pgpass

echo "Step 9: Testing connection..."
PGPASSWORD=postgres psql -U jonchristie -d voice_sql_test -c "SELECT 'Connection successful!' as status;"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PostgreSQL setup complete!${NC}"
    echo ""
    echo "Now run:"
    echo "  source venv/bin/activate"
    echo "  export DATABASE_URL='postgresql://jonchristie:postgres@localhost:5432/voice_sql_test'"
    echo "  python scripts/init_db.py"
else
    echo -e "${RED}❌ Connection test failed. Please check the output above.${NC}"
    exit 1
fi
