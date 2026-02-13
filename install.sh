#!/bin/bash
# Shelley Bio Installation Script

set -euo pipefail

echo "🧬 Shelley Bio Installation Script"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Found Python $python_version"
    
    # Check pip
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        log_error "pip is not installed. Please install pip."
        exit 1
    fi
    
    # Check CVMFS
    if [[ ! -d "/cvmfs/singularity.galaxyproject.org" ]]; then
        log_warning "CVMFS singularity repository not found at /cvmfs/singularity.galaxyproject.org"
        log_warning "Shelley Bio will not be able to access containers without CVMFS"
    else
        log_success "CVMFS singularity repository found"
    fi
    
    # Check Lmod
    if ! command -v module &> /dev/null; then
        log_warning "Lmod (module command) not found"
        log_warning "Module building features will require Lmod to be installed"
    else
        log_success "Lmod found"
    fi
    
    # Check Singularity/Apptainer
    if ! command -v singularity &> /dev/null && ! command -v apptainer &> /dev/null; then
        log_warning "Neither Singularity nor Apptainer found"
        log_warning "Container execution will require one of these tools"
    else
        log_success "Container runtime found"
    fi
}

# Install function
install_shelley_bio() {
    log_info "Installing Shelley Bio..."
    
    # Create virtual environment if requested
    if [[ "${CREATE_VENV:-}" == "true" ]]; then
        log_info "Creating virtual environment..."
        python3 -m venv shelley-bio-env
        source shelley-bio-env/bin/activate
        log_success "Virtual environment created and activated"
    fi
    
    # Choose pip command
    PIP_CMD="pip3"
    if command -v pip &> /dev/null; then
        PIP_CMD="pip"
    fi
    
    # Install dependencies
    log_info "Installing Python dependencies..."
    $PIP_CMD install -r requirements.txt
    
    # Install package
    if [[ "${DEVELOPMENT_MODE:-false}" == "true" ]]; then
        log_info "Installing in development mode..."
        $PIP_CMD install -e .
    else
        log_info "Installing package..."
        $PIP_CMD install .
    fi
    
    log_success "Shelley Bio installed successfully!"
}

# Test installation
test_installation() {
    log_info "Testing installation..."
    
    if command -v shelley-bio &> /dev/null; then
        log_success "shelley-bio command available"
    else
        log_error "shelley-bio command not found in PATH"
        return 1
    fi
    
    if command -v shelley-bio-batch &> /dev/null; then
        log_success "shelley-bio-batch command available"
    else
        log_error "shelley-bio-batch command not found in PATH"
        return 1
    fi
    
    # Test basic functionality
    log_info "Running basic functionality test..."
    if shelley-bio --help > /dev/null 2>&1; then
        log_success "Basic functionality test passed"
    else
        log_error "Basic functionality test failed"
        return 1
    fi
}

# Print usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --venv              Create and use a virtual environment"
    echo "  --dev               Install in development mode"
    echo "  --skip-tests        Skip installation tests"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Standard installation"
    echo "  $0 --venv           # Install in virtual environment"
    echo "  $0 --dev --venv     # Development installation in venv"
}

# Parse arguments
SKIP_TESTS=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --venv)
            CREATE_VENV=true
            shift
            ;;
        --dev)
            DEVELOPMENT_MODE=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main installation process
main() {
    echo "Starting installation process..."
    echo ""
    
    # Check if we're in the right directory
    if [[ ! -f "setup.py" ]] || [[ ! -f "pyproject.toml" ]]; then
        log_error "This script must be run from the Shelley Bio source directory"
        log_error "Please ensure you're in the directory containing setup.py"
        exit 1
    fi
    
    check_requirements
    echo ""
    
    install_shelley_bio
    echo ""
    
    if [[ "$SKIP_TESTS" != "true" ]]; then
        test_installation
        echo ""
    fi
    
    log_success "🎉 Shelley Bio installation completed!"
    echo ""
    echo "Next steps:"
    echo "1. Try: shelley-bio --help"
    echo "2. Find a tool: shelley-bio find fastqc"
    echo "3. Interactive mode: shelley-bio interactive"
    echo ""
    
    if [[ "${CREATE_VENV:-}" == "true" ]]; then
        echo "Note: Virtual environment created at ./shelley-bio-env"
        echo "To activate it later: source shelley-bio-env/bin/activate"
        echo ""
    fi
}

# Run main function
main "$@"