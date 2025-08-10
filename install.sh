#!/bin/bash

# Bug Bounty Automation Framework Installer
# Installs all required tools with error handling

set -e  # Exit on any error

INSTALL_DIR="/home/phantomx/bug-bounty-automation"
TOOLS_DIR="$INSTALL_DIR/tools"
LOGS_DIR="$INSTALL_DIR/logs"
RESULTS_DIR="$INSTALL_DIR/results"
CONFIG_DIR="$INSTALL_DIR/config"

echo "🚀 Installing Bug Bounty Automation Framework..."
echo "================================================"

# Create directories
mkdir -p "$TOOLS_DIR" "$LOGS_DIR" "$RESULTS_DIR" "$CONFIG_DIR"

# Function to log installation
log_install() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGS_DIR/install.log"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

log_install "Starting installation process..."

# Update system
log_install "Updating system packages..."
sudo apt update -y || { log_install "ERROR: Failed to update packages"; exit 1; }

# Install basic dependencies
log_install "Installing basic dependencies..."
sudo apt install -y curl wget git unzip python3 python3-pip golang-go jq nodejs npm || {
    log_install "ERROR: Failed to install basic dependencies"
    exit 1
}

# Install Python dependencies
log_install "Installing Python dependencies..."
# Use system packages or virtual environment to avoid externally-managed-environment error
sudo apt install -y python3-requests python3-bs4 python3-lxml python3-colorama python3-termcolor || {
    log_install "WARNING: Some Python packages may not be available via apt"
    # Try with --break-system-packages as fallback
    pip3 install --break-system-packages requests beautifulsoup4 lxml colorama termcolor || {
        log_install "WARNING: Failed to install some Python dependencies, continuing..."
    }
}

# Set up Go environment
export GOPATH="$HOME/go"
export PATH="$PATH:$GOPATH/bin"
echo 'export GOPATH="$HOME/go"' >> ~/.bashrc
echo 'export PATH="$PATH:$GOPATH/bin"' >> ~/.bashrc

# Install Go tools
log_install "Installing reconnaissance tools..."

# Subfinder
if ! command_exists subfinder; then
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest || {
        log_install "ERROR: Failed to install subfinder"
        exit 1
    }
    log_install "✓ Subfinder installed"
else
    log_install "✓ Subfinder already installed"
fi

# Amass
if ! command_exists amass; then
    go install -v github.com/owasp-amass/amass/v4/...@master || {
        log_install "ERROR: Failed to install amass"
        exit 1
    }
    log_install "✓ Amass installed"
else
    log_install "✓ Amass already installed"
fi

# Assetfinder
if ! command_exists assetfinder; then
    go install github.com/tomnomnom/assetfinder@latest || {
        log_install "ERROR: Failed to install assetfinder"
        exit 1
    }
    log_install "✓ Assetfinder installed"
else
    log_install "✓ Assetfinder already installed"
fi

# HTTPx
if ! command_exists httpx; then
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest || {
        log_install "ERROR: Failed to install httpx"
        exit 1
    }
    log_install "✓ HTTPx installed"
else
    log_install "✓ HTTPx already installed"
fi

# Katana (crawler)
if ! command_exists katana; then
    go install github.com/projectdiscovery/katana/cmd/katana@latest || {
        log_install "ERROR: Failed to install katana"
        exit 1
    }
    log_install "✓ Katana installed"
else
    log_install "✓ Katana already installed"
fi

# GAU (Get All URLs)
if ! command_exists gau; then
    go install github.com/lc/gau/v2/cmd/gau@latest || {
        log_install "ERROR: Failed to install gau"
        exit 1
    }
    log_install "✓ GAU installed"
else
    log_install "✓ GAU already installed"
fi

# Nuclei
if ! command_exists nuclei; then
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest || {
        log_install "ERROR: Failed to install nuclei"
        exit 1
    }
    log_install "✓ Nuclei installed"
else
    log_install "✓ Nuclei already installed"
fi

# Dalfox (XSS scanner)
if ! command_exists dalfox; then
    go install github.com/hahwul/dalfox/v2@latest || {
        log_install "ERROR: Failed to install dalfox"
        exit 1
    }
    log_install "✓ Dalfox installed"
else
    log_install "✓ Dalfox already installed"
fi

# Install SQLMap
if ! command_exists sqlmap; then
    sudo apt install -y sqlmap || {
        log_install "ERROR: Failed to install sqlmap"
        exit 1
    }
    log_install "✓ SQLMap installed"
else
    log_install "✓ SQLMap already installed"
fi

# Install Hakrawler
if ! command_exists hakrawler; then
    go install github.com/hakluke/hakrawler@latest || {
        log_install "ERROR: Failed to install hakrawler"
        exit 1
    }
    log_install "✓ Hakrawler installed"
else
    log_install "✓ Hakrawler already installed"
fi

# Update Nuclei templates
log_install "Updating Nuclei templates..."
nuclei -update-templates || {
    log_install "WARNING: Failed to update nuclei templates, continuing..."
}

# Create configuration files
log_install "Creating configuration files..."

# Email configuration template
cat > "$CONFIG_DIR/email_config.json" << 'EOF'
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "recipient_email": "your-email@gmail.com",
    "developer_email": "developer@target-company.com"
}
EOF

# Subfinder configuration
mkdir -p ~/.config/subfinder/
cat > ~/.config/subfinder/provider-config.yaml << 'EOF'
# Add your API keys here for better results
# virustotal: 
#   - "YOUR_VT_API_KEY"
# shodan: 
#   - "YOUR_SHODAN_API_KEY"
# censys: 
#   - "YOUR_CENSYS_API_ID:YOUR_CENSYS_SECRET"
EOF

# Create wordlists directory
mkdir -p "$TOOLS_DIR/wordlists"
log_install "Downloading wordlists..."

# Download common wordlists
if [ ! -f "$TOOLS_DIR/wordlists/common.txt" ]; then
    curl -s "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt" -o "$TOOLS_DIR/wordlists/common.txt" || {
        log_install "WARNING: Failed to download common.txt wordlist"
    }
fi

if [ ! -f "$TOOLS_DIR/wordlists/directory-list-2.3-medium.txt" ]; then
    curl -s "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/directory-list-2.3-medium.txt" -o "$TOOLS_DIR/wordlists/directory-list-2.3-medium.txt" || {
        log_install "WARNING: Failed to download directory-list-2.3-medium.txt wordlist"
    }
fi

# Make all scripts executable
chmod +x "$INSTALL_DIR"/*.sh 2>/dev/null || true

log_install "✅ Installation completed successfully!"
log_install "📁 Framework installed in: $INSTALL_DIR"
log_install "📝 Configuration files in: $CONFIG_DIR"
log_install "📊 Results will be saved in: $RESULTS_DIR"
log_install "📋 Logs will be saved in: $LOGS_DIR"

echo ""
echo "🎯 NEXT STEPS:"
echo "1. Edit $CONFIG_DIR/email_config.json with your email settings"
echo "2. Add API keys to ~/.config/subfinder/provider-config.yaml (optional but recommended)"
echo "3. Create target list: echo 'target.com' > targets.txt"
echo "4. Run: ./hunt.sh targets.txt"
echo ""
echo "✅ Bug Bounty Automation Framework Ready!"
