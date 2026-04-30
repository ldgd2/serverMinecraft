#!/bin/bash

# Minecraft Server Manager - Linux/Mac Installer & Runner

# Ensure we are in the project root directory (the directory containing the 'server' folder)
# If this script is inside 'server', the root is one level up.
CURRENT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -d "$CURRENT_DIR/server" ]; then
    # We are in the root
    ROOT_DIR="$CURRENT_DIR"
    SERVER_DIR="$ROOT_DIR/server"
else
    # We are likely inside 'server'
    ROOT_DIR="$(cd "$CURRENT_DIR/.." && pwd)"
    SERVER_DIR="$CURRENT_DIR"
fi

cd "$ROOT_DIR" || exit 1

echo "========================================================="
echo "🎮 Minecraft Server Manager - Setup & Runner 🎮"
echo "Project Root: $ROOT_DIR"
echo "========================================================="
echo "Detecting Operating System..."

OS="$(uname -s)"
DISTRO=""

if [ "$OS" = "Linux" ]; then
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
    fi
elif [ "$OS" = "Darwin" ]; then
    DISTRO="macos"
fi

echo "Detected: $OS ($DISTRO)"

# Function to install dependencies based on distro
install_deps() {
    echo "Installing System Dependencies (Python 3, Venv, PostgreSQL 16, Java 21, Screen)..."
    case $DISTRO in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y ca-certificates curl gnupg lsb-release
            # Add PostgreSQL 16 repo for Ubuntu/Debian
            sudo install -d /usr/share/postgresql-common/pgdg
            sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc
            echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
            
            sudo apt-get update
            sudo apt-get install -y python3 python3-venv python3-pip postgresql-16 openjdk-21-jre libpq-dev screen
            
            # Start and enable PostgreSQL
            sudo systemctl enable postgresql
            sudo systemctl start postgresql
            
            # Set default password for 'postgres' user to 'postgres' to simplify first-time setup
            sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
            ;;
        fedora)
            sudo dnf install -y python3 pip postgresql-server openjdk-21-jre libpq-devel screen
            sudo postgresql-setup --initdb
            sudo systemctl enable postgresql
            sudo systemctl start postgresql
            ;;
        arch|manjaro)
            sudo pacman -Syu --noconfirm python python-pip postgresql openjdk21-jre screen
            # Arch needs manual initdb usually
            if [ ! -d "/var/lib/postgres/data" ]; then
                sudo -u postgres initdb -D /var/lib/postgres/data
            fi
            sudo systemctl enable postgresql
            sudo systemctl start postgresql
            ;;
        macos)
            if ! command -v brew &> /dev/null; then
                echo "Homebrew not found. Please install Homebrew first."
                exit 1
            fi
            brew install python postgresql@16 openjdk@21 screen
            brew services start postgresql@16
            ;;
        *)
            echo "Unsupported distribution: $DISTRO. Please install Python 3, PostgreSQL 16, Java 21, and Screen manually."
            ;;
    esac
}

# Check for required commands
if ! command -v python3 &> /dev/null || ! command -v psql &> /dev/null || ! command -v java &> /dev/null || ! command -v screen &> /dev/null; then
    install_deps
else
    echo "✔ Python3, PostgreSQL, Java, and Screen are already installed."
    # Ensure services are running on Linux
    if [ "$OS" = "Linux" ]; then
        sudo systemctl start postgresql 2>/dev/null
    fi
    # Ensure python3-venv is installed on apt systems
    if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
        dpkg -s python3-venv &> /dev/null || sudo apt-get install -y python3-venv
    fi
fi

# Initialize .env if missing (should be in server folder)
if [ ! -f "$SERVER_DIR/.env" ]; then
    echo "Creating initial .env file in $SERVER_DIR..."
    cat > "$SERVER_DIR/.env" <<EOL
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
DB_ENGINE=postgresql
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=mine_db
DB_USER=postgres
DB_PASSWORD=postgres
API_PORT=8000
API_HOST=0.0.0.0
EOL
fi

# Create Venv in ROOT_DIR
if [ ! -d "$ROOT_DIR/venv" ]; then
    echo "Creating Python Virtual Environment in $ROOT_DIR/venv..."
    python3 -m venv "$ROOT_DIR/venv"
else
    echo "✔ Virtual Environment already exists."
fi

# Install Dependencies
echo "Installing Python Dependencies..."
"$ROOT_DIR/venv/bin/pip" install --upgrade pip
"$ROOT_DIR/venv/bin/pip" install -r "$SERVER_DIR/requirements.txt"

# Run Setup
echo "Ensuring Database is initialized..."
cd "$SERVER_DIR" || exit 1
"$ROOT_DIR/venv/bin/python" mine.py database init-db

echo ""
echo "========================================================="
echo "✅ Everything is ready! Starting the Manager..."
echo "========================================================="

# Run the CLI
"$ROOT_DIR/venv/bin/python" mine.py

