#!/bin/bash

# Minecraft Server Manager - Linux/Mac Installer

# Ensure we are in the project root directory (2 levels up from setup/script/)
# Resolve the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if requirements.txt is in SCRIPT_DIR (script is in root)
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    ROOT_DIR="$SCRIPT_DIR"
# Check if requirements.txt is 2 levels up (script is in setup/script)
elif [ -f "$SCRIPT_DIR/../../requirements.txt" ]; then
    ROOT_DIR="$SCRIPT_DIR/../.."
else
    echo "Error: Could not find requirements.txt. Are you running this from the correct directory?"
    exit 1
fi

cd "$ROOT_DIR" || exit 1

echo "Detection of Operating System..."

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
    echo "Installing System Dependencies..."
    case $DISTRO in
        ubuntu|debian|kali|linuxmint)
            sudo apt-get update
            sudo apt-get install -y python3-venv python3-pip openjdk-17-jre
            ;;
        fedora)
            sudo dnf install -y python3 pip java-17-openjdk
            ;;
        arch|manjaro)
            sudo pacman -Syu --noconfirm python python-pip jre17-openjdk
            ;;
        centos|rhel)
            sudo yum install -y python3 pip java-17-openjdk
            ;;
        macos)
            if ! command -v brew &> /dev/null; then
                echo "Homebrew not found. Please install Homebrew first."
                exit 1
            fi
            brew install python openjdk@17
            ;;
        *)
            echo "Unsupported distribution: $DISTRO. Please install Python 3 and Java 17 manually."
            ;;
    esac
}

# Check for Java
if ! command -v java &> /dev/null; then
    install_deps
else
    echo "Java is already installed."
    # We might still need python3-venv on some minimal installs
    if [ "$DISTRO" = "ubuntu" ] || [ "$DISTRO" = "debian" ]; then
        dpkg -s python3-venv &> /dev/null || sudo apt-get install -y python3-venv
    fi
fi

# Create Venv
if [ ! -d "venv" ]; then
    echo "Creating Python Virtual Environment..."
    python3 -m venv venv
else
    echo "Virtual Environment already exists."
fi

# Install Dependencies (Use direct venv path to avoid 'source' issues)
echo "Installing Python Dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# Run Setup
echo "Running Setup Configuration..."
./venv/bin/python mine.py database init-db

echo ""
echo "Installation Complete!"
echo "You can now run the server using: ./venv/bin/python run.py"
