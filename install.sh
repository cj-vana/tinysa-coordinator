#!/bin/bash
#
# TinySA Coordinator - One-Line Installer
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/cj-vana/frequency-scanner/main/install.sh | bash
#   wget -qO- https://raw.githubusercontent.com/cj-vana/frequency-scanner/main/install.sh | bash
#
# Options:
#   --help      Show this help message
#   --no-start  Install without starting the development servers
#   --dev       Clone from develop branch instead of main
#   --dir DIR   Install to specified directory (default: frequency-scanner)
#

set -e

# ============================================================================
# Configuration
# ============================================================================

REPO_URL="https://github.com/cj-vana/frequency-scanner.git"
DEFAULT_DIR="frequency-scanner"
BRANCH="main"
START_SERVERS=true
INSTALL_DIR=""
MIN_PYTHON_VERSION="3.9"
MIN_NODE_VERSION="18"

# ============================================================================
# Colors and Output Helpers
# ============================================================================

# Check if stdout is a terminal for color support
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    BOLD=''
    NC=''
fi

print_banner() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║${NC}           ${BOLD}TinySA Coordinator Installer${NC}                       ${CYAN}${BOLD}║${NC}"
    echo -e "${CYAN}${BOLD}║${NC}     RF Spectrum Analysis & Coordination Software            ${CYAN}${BOLD}║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

step() {
    echo ""
    echo -e "${BOLD}==> $1${NC}"
}

# ============================================================================
# Help
# ============================================================================

show_help() {
    cat << EOF
TinySA Coordinator Installer

USAGE:
    install.sh [OPTIONS]

OPTIONS:
    --help          Show this help message and exit
    --no-start      Install without starting the development servers
    --dev           Clone from the develop branch instead of main
    --dir DIR       Install to specified directory (default: frequency-scanner)

EXAMPLES:
    # Default installation
    curl -sSL https://raw.githubusercontent.com/cj-vana/frequency-scanner/main/install.sh | bash

    # Install without starting servers
    curl -sSL https://raw.githubusercontent.com/cj-vana/frequency-scanner/main/install.sh | bash -s -- --no-start

    # Install from develop branch to custom directory
    curl -sSL https://raw.githubusercontent.com/cj-vana/frequency-scanner/main/install.sh | bash -s -- --dev --dir my-scanner

REQUIREMENTS:
    - Python $MIN_PYTHON_VERSION or higher
    - Node.js $MIN_NODE_VERSION or higher
    - git
    - macOS or Linux

WHAT THIS SCRIPT DOES:
    1. Checks system requirements (OS, Python, Node.js, git)
    2. Clones the repository (or uses existing directory)
    3. Creates a Python virtual environment
    4. Installs Python dependencies
    5. Installs Node.js dependencies
    6. Optionally starts the development servers

After installation, you can start the servers manually with:
    cd frequency-scanner
    ./scripts/run_dev.sh

For more information, visit:
    https://github.com/cj-vana/frequency-scanner

EOF
    exit 0
}

# ============================================================================
# Path Utilities
# ============================================================================

expand_tilde() {
    # Expand tilde to home directory for user-specified paths
    # Bash doesn't expand ~ when it's inside a quoted variable
    local path="$1"
    case "$path" in
        "~")
            echo "$HOME"
            ;;
        "~/"*)
            echo "${HOME}${path:1}"
            ;;
        "~+"*)
            # ~+ expands to current working directory
            echo "${PWD}${path:2}"
            ;;
        "~-"*)
            # ~- expands to previous working directory
            echo "${OLDPWD}${path:2}"
            ;;
        *)
            # Return path as-is for non-tilde paths
            echo "$path"
            ;;
    esac
}

# ============================================================================
# Argument Parsing
# ============================================================================

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                ;;
            --no-start)
                START_SERVERS=false
                shift
                ;;
            --dev)
                BRANCH="develop"
                shift
                ;;
            --dir)
                if [[ -n "$2" && ! "$2" =~ ^-- ]]; then
                    # Apply tilde expansion for user-specified paths
                    INSTALL_DIR="$(expand_tilde "$2")"
                    shift 2
                else
                    error "--dir requires a directory name"
                    exit 1
                fi
                ;;
            *)
                error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Set default install directory if not specified
    if [ -z "$INSTALL_DIR" ]; then
        INSTALL_DIR="$DEFAULT_DIR"
    fi
}

# ============================================================================
# System Detection
# ============================================================================

detect_os() {
    case "$(uname -s)" in
        Linux*)     OS="linux";;
        Darwin*)    OS="macos";;
        CYGWIN*)    OS="windows";;
        MINGW*)     OS="windows";;
        MSYS*)      OS="windows";;
        *)          OS="unknown";;
    esac
    echo "$OS"
}

# ============================================================================
# Version Comparison
# ============================================================================

version_gte() {
    # Returns 0 (true) if $1 >= $2
    local v1="$1"
    local v2="$2"

    # Extract major.minor from version strings
    local v1_major=$(echo "$v1" | cut -d. -f1)
    local v1_minor=$(echo "$v1" | cut -d. -f2)
    local v2_major=$(echo "$v2" | cut -d. -f1)
    local v2_minor=$(echo "$v2" | cut -d. -f2)

    # Handle missing minor version
    v1_minor=${v1_minor:-0}
    v2_minor=${v2_minor:-0}

    if [ "$v1_major" -gt "$v2_major" ]; then
        return 0
    elif [ "$v1_major" -eq "$v2_major" ] && [ "$v1_minor" -ge "$v2_minor" ]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Requirement Checks
# ============================================================================

check_os() {
    step "Checking operating system..."

    local os=$(detect_os)

    case "$os" in
        macos)
            success "Detected macOS"
            ;;
        linux)
            success "Detected Linux"
            ;;
        windows)
            error "Windows is not fully supported by this installer."
            echo "Please follow the manual installation instructions in the README."
            exit 1
            ;;
        *)
            error "Unknown operating system: $(uname -s)"
            exit 1
            ;;
    esac
}

check_git() {
    step "Checking for git..."

    if ! command -v git &> /dev/null; then
        error "git is not installed"
        echo ""
        echo "Please install git:"

        local os=$(detect_os)
        case "$os" in
            macos)
                echo "  brew install git"
                echo "  OR"
                echo "  xcode-select --install"
                ;;
            linux)
                echo "  sudo apt-get install git     # Debian/Ubuntu"
                echo "  sudo dnf install git         # Fedora"
                echo "  sudo pacman -S git           # Arch"
                ;;
        esac
        exit 1
    fi

    local git_version=$(git --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    success "Found git version $git_version"
}

check_python() {
    step "Checking for Python $MIN_PYTHON_VERSION+..."

    local python_cmd=""
    local python_version=""

    # Try python3 first, then python
    for cmd in python3 python; do
        if command -v "$cmd" &> /dev/null; then
            local version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
            if version_gte "$version" "$MIN_PYTHON_VERSION"; then
                python_cmd="$cmd"
                python_version="$version"
                break
            fi
        fi
    done

    if [ -z "$python_cmd" ]; then
        error "Python $MIN_PYTHON_VERSION or higher is required"
        echo ""
        echo "Please install Python:"

        local os=$(detect_os)
        case "$os" in
            macos)
                echo "  brew install python@3.11"
                echo "  OR download from https://www.python.org/downloads/"
                ;;
            linux)
                echo "  sudo apt-get install python3 python3-venv python3-pip  # Debian/Ubuntu"
                echo "  sudo dnf install python3                                # Fedora"
                echo "  sudo pacman -S python                                   # Arch"
                ;;
        esac
        exit 1
    fi

    success "Found Python $python_version ($python_cmd)"

    # Export for use in later steps
    PYTHON_CMD="$python_cmd"
}

check_node() {
    step "Checking for Node.js $MIN_NODE_VERSION+..."

    if ! command -v node &> /dev/null; then
        error "Node.js is not installed"
        echo ""
        echo "Please install Node.js $MIN_NODE_VERSION or higher:"

        local os=$(detect_os)
        case "$os" in
            macos)
                echo "  brew install node"
                echo "  OR use nvm: https://github.com/nvm-sh/nvm"
                echo "  OR download from https://nodejs.org/"
                ;;
            linux)
                echo "  # Using nvm (recommended):"
                echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
                echo "  nvm install 20"
                echo ""
                echo "  # OR using package manager:"
                echo "  sudo apt-get install nodejs npm  # Debian/Ubuntu"
                echo "  sudo dnf install nodejs          # Fedora"
                ;;
        esac
        exit 1
    fi

    local node_version=$(node --version | grep -oE '[0-9]+\.[0-9]+' | head -1)

    if ! version_gte "$node_version" "$MIN_NODE_VERSION"; then
        error "Node.js $MIN_NODE_VERSION or higher is required (found v$node_version)"
        echo ""
        echo "Please upgrade Node.js:"
        echo "  nvm install 20 && nvm use 20"
        echo "  OR download from https://nodejs.org/"
        exit 1
    fi

    success "Found Node.js v$node_version"

    # Check npm
    if ! command -v npm &> /dev/null; then
        error "npm is not installed"
        echo "npm should come with Node.js. Please reinstall Node.js."
        exit 1
    fi

    local npm_version=$(npm --version)
    success "Found npm v$npm_version"
}

# ============================================================================
# Installation Steps
# ============================================================================

clone_repo() {
    step "Setting up project directory..."

    # Check if we're already in the project directory
    if [ -f "requirements.txt" ] && [ -d "backend" ] && [ -d "frontend" ]; then
        info "Already in the project directory"
        INSTALL_DIR="$(pwd)"
        return 0
    fi

    # Check if target directory exists
    if [ -d "$INSTALL_DIR" ]; then
        if [ -f "$INSTALL_DIR/requirements.txt" ] && [ -d "$INSTALL_DIR/backend" ]; then
            info "Project already exists in $INSTALL_DIR"
            info "Pulling latest changes..."
            cd "$INSTALL_DIR"
            # Update INSTALL_DIR to absolute path for consistent messaging
            INSTALL_DIR="$(pwd)"
            git pull origin "$BRANCH" || warn "Could not pull latest changes"
            return 0
        else
            error "Directory $INSTALL_DIR exists but doesn't appear to be the project"
            echo "Please remove it or use --dir to specify a different directory"
            exit 1
        fi
    fi

    # Create parent directories if needed (for paths like ~/projects/scanner)
    local parent_dir
    parent_dir="$(dirname "$INSTALL_DIR")"
    if [ "$parent_dir" != "." ] && [ ! -d "$parent_dir" ]; then
        info "Creating parent directory: $parent_dir"
        mkdir -p "$parent_dir"
    fi

    info "Cloning repository from branch: $BRANCH"
    git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    # Update INSTALL_DIR to absolute path for consistent messaging
    INSTALL_DIR="$(pwd)"
    success "Repository cloned to $INSTALL_DIR"
}

setup_python_venv() {
    step "Setting up Python virtual environment..."

    if [ -d "venv" ]; then
        info "Virtual environment already exists"
    else
        info "Creating virtual environment..."
        "$PYTHON_CMD" -m venv venv
        success "Virtual environment created"
    fi

    # Activate venv
    source venv/bin/activate

    # Upgrade pip
    info "Upgrading pip..."
    pip install --upgrade pip --quiet

    # Install requirements
    info "Installing Python dependencies..."
    pip install -r requirements.txt --quiet
    success "Python dependencies installed"
}

setup_frontend() {
    step "Setting up frontend dependencies..."

    cd frontend

    if [ -d "node_modules" ]; then
        info "Node modules already installed"
        info "Checking for updates..."
        npm install --silent 2>/dev/null || npm install
    else
        info "Installing npm dependencies..."
        npm install --silent 2>/dev/null || npm install
    fi

    cd ..
    success "Frontend dependencies installed"
}

setup_permissions() {
    step "Setting up file permissions..."

    # Make scripts executable
    if [ -f "scripts/run_dev.sh" ]; then
        chmod +x scripts/run_dev.sh
    fi

    if [ -f "install.sh" ]; then
        chmod +x install.sh
    fi

    success "File permissions set"
}

start_servers() {
    step "Starting development servers..."

    echo ""
    echo -e "${GREEN}${BOLD}Installation complete!${NC}"
    echo ""
    echo "Starting development servers..."
    echo "  Backend API:  http://localhost:8000"
    echo "  Frontend App: http://localhost:5173"
    echo "  API Docs:     http://localhost:8000/docs"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop the servers${NC}"
    echo ""

    # Run the development script
    ./scripts/run_dev.sh
}

print_success_message() {
    echo ""
    echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║${NC}              ${BOLD}Installation Complete!${NC}                          ${GREEN}${BOLD}║${NC}"
    echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "To start the development servers:"
    echo ""
    echo -e "  ${CYAN}cd $INSTALL_DIR${NC}"
    echo -e "  ${CYAN}./scripts/run_dev.sh${NC}"
    echo ""
    echo "Or start them individually:"
    echo ""
    echo -e "  ${CYAN}# Backend (in one terminal)${NC}"
    echo -e "  cd $INSTALL_DIR"
    echo -e "  source venv/bin/activate"
    echo -e "  uvicorn backend.main:app --reload --port 8000"
    echo ""
    echo -e "  ${CYAN}# Frontend (in another terminal)${NC}"
    echo -e "  cd $INSTALL_DIR/frontend"
    echo -e "  npm run dev"
    echo ""
    echo "Access the application:"
    echo "  Frontend:  http://localhost:5173"
    echo "  API Docs:  http://localhost:8000/docs"
    echo ""
    echo "For more information, see the README.md or visit:"
    echo "  https://github.com/cj-vana/frequency-scanner"
    echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
    print_banner

    # Parse command line arguments
    parse_args "$@"

    info "Installing TinySA Coordinator..."
    info "Branch: $BRANCH"
    info "Directory: $INSTALL_DIR"
    info "Start servers after install: $START_SERVERS"

    # Run checks
    check_os
    check_git
    check_python
    check_node

    # Install
    clone_repo
    setup_python_venv
    setup_frontend
    setup_permissions

    # Start or show instructions
    if [ "$START_SERVERS" = true ]; then
        start_servers
    else
        print_success_message
    fi
}

# Run main with all arguments
main "$@"
