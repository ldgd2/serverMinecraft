#!/bin/bash

# Minecraft Server Manager - Linux/Mac Installer & Runner

# Ensure we are in the project root directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if requirements.txt is in SCRIPT_DIR
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    ROOT_DIR="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/../../requirements.txt" ]; then
    ROOT_DIR="$SCRIPT_DIR/../.."
else
    echo "Error: Could not find requirements.txt. Are you running this from the correct directory?"
    exit 1
fi

cd "$ROOT_DIR" || exit 1

echo "========================================================="
echo "🎮 Minecraft Server Manager - Environment Setup & Runner 🎮"
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
    echo "Installing System Dependencies (Python 3, Venv, SQLite3, Java 17)..."
    case $DISTRO in
        ubuntu|debian|kali|linuxmint)
            sudo apt-get update
            sudo apt-get install -y python3 python3-venv python3-pip sqlite3 openjdk-17-jre
            ;;
        fedora)
            sudo dnf install -y python3 pip sqlite java-17-openjdk
            ;;
        arch|manjaro)
            sudo pacman -Syu --noconfirm python python-pip sqlite jre17-openjdk
            ;;
        centos|rhel)
            sudo yum install -y python3 pip sqlite java-17-openjdk
            ;;
        macos)
            if ! command -v brew &> /dev/null; then
                echo "Homebrew not found. Please install Homebrew first."
                exit 1
            fi
            brew install python sqlite openjdk@17
            ;;
        *)
            echo "Unsupported distribution: $DISTRO. Please install Python 3, SQLite3, and Java 17 manually."
            ;;
    esac
}

# Check for required commands
if ! command -v python3 &> /dev/null || ! command -v sqlite3 &> /dev/null || ! command -v java &> /dev/null; then
    install_deps
else
    echo "✔ Python3, SQLite3, and Java are already installed."
    # Ensure python3-venv is installed on apt systems
    if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
        dpkg -s python3-venv &> /dev/null || sudo apt-get install -y python3-venv
    fi
fi

# Create Venv
if [ ! -d "venv" ]; then
    echo "Creating Python Virtual Environment..."
    python3 -m venv venv
else
    echo "✔ Virtual Environment already exists."
fi

# Install Dependencies
echo "Installing Python Dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# Run Setup using explicit python from venv to avoid permission/sourcing issues
echo "Ensuring Database is initialized..."
./venv/bin/python mine.py database init-db

echo ""
echo "========================================================="
echo "✅ Installation Complete! Activating VENV and starting CLI..."
echo "========================================================="

# Activate virtual environment and run the CLI interactively
# We use exec bash so that when the script finishes, if the user closes mine.py, 
# they are dropped into the activated virtual environment shell.
exec bash --init-file <(echo "source venv/bin/activate; python mine.py")
