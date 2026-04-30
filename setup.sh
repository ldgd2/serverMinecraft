#!/bin/bash

# Function to check for Python 3
check_python() {
    if command -v python3 &>/dev/null; then
        echo "[INFO] Python 3 is installed."
    else
        echo "[ERROR] Python 3 is not installed. Please install it manually."
        exit 1
    fi
}

# Function to check for package manager and install Java
install_java() {
    local version=$1
    local package_name=""

    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt update
        case $version in
            8) package_name="openjdk-8-jre-headless" ;;
            17) package_name="openjdk-17-jre-headless" ;;
            21) package_name="openjdk-21-jre-headless" ;;
        esac
        
        if [ -n "$package_name" ]; then
            echo "[INFO] Installing $package_name..."
            sudo apt install -y "$package_name"
        else
            echo "[ERROR] Unsupported Java version for this script."
        fi
    elif [ -f /etc/redhat-release ]; then
        # CentOS/RHEL/Fedora
        case $version in
            8) package_name="java-1.8.0-openjdk-headless" ;;
            17) package_name="java-17-openjdk-headless" ;;
            21) package_name="java-21-openjdk-headless" ;;
        esac
        
        if [ -n "$package_name" ]; then
             echo "[INFO] Installing $package_name..."
             sudo dnf install -y "$package_name"
        fi
    else
        echo "[WARNING] Unsupported Linux distribution for automatic Java installation."
        echo "Please install OpenJDK $version manually."
    fi
}

# Main Script
check_python

# Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[INFO] Virtual environment already exists."
fi

# Activate Virtual Environment
source venv/bin/activate

# Install Dependencies
if [ -f "requirements.txt" ]; then
    echo "[INFO] Installing requirements..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "[WARNING] requirements.txt not found!"
fi

# Function to list installed Java versions
list_java() {
    echo ""
    echo "[INFO] Listing installed Java versions..."
    if command -v update-java-alternatives &> /dev/null; then
        update-java-alternatives -l
    elif [ -d "/usr/lib/jvm" ]; then
        ls -1 /usr/lib/jvm
    else
        echo "[WARNING] Could not detect installed Java versions (update-java-alternatives not found and /usr/lib/jvm not present)."
    fi
    echo ""
    read -p "Press Enter to continue..."
}

# Function to install all supported Java versions
install_all_java() {
    echo "[INFO] Installing ALL supported Java versions (8, 17, 21)..."
    install_java 8
    install_java 17
    install_java 21
    echo "[INFO] All installations requested."
    read -p "Press Enter to continue..."
}

# Java Menu
while true; do
    echo ""
    echo "=========================================="
    echo "        Java Installation Setup"
    echo "=========================================="
    echo "[1] Install Java 8 (for older Minecraft versions)"
    echo "[2] Install Java 17 (for Minecraft 1.18 - 1.20.4)"
    echo "[3] Install Java 21 (for Minecraft 1.20.5+)"
    echo "[4] Install ALL Supported Java Versions (8, 17, 21)"
    echo "[5] List Installed Java Versions"
    echo "[6] Check current \"java -version\""
    echo "[7] Exit"
    echo "=========================================="
    read -p "Select an option (1-7): " CHOICE

    case $CHOICE in
        1) install_java 8 ;;
        2) install_java 17 ;;
        3) install_java 21 ;;
        4) install_all_java ;;
        5) list_java ;;
        6) java -version; read -p "Press Enter to continue..." ;;
        7) break ;;
        *) echo "Invalid option." ;;
    esac
done

echo "[INFO] Setup complete."
