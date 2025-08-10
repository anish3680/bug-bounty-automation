#!/bin/bash

# AI Bug Bounty Scanner Setup Script
# Installs required dependencies and AI models

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_banner() {
    clear
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║            🤖 AI Bug Bounty Scanner Setup                   ║"
    echo "║        Installing AI Models and Dependencies               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

install_python_dependencies() {
    echo -e "${PURPLE}[1/5] Installing Python dependencies...${NC}"
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        echo "Installing pip3..."
        sudo apt-get update
        sudo apt-get install -y python3-pip
    fi
    
    # Install required Python packages
    pip3 install --user aiohttp requests asyncio pathlib

    echo -e "${GREEN}✅ Python dependencies installed${NC}"
}

install_ollama() {
    echo -e "${PURPLE}[2/5] Installing Ollama (Local AI)...${NC}"
    
    if ! command -v ollama &> /dev/null; then
        echo "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        
        # Start ollama service
        sudo systemctl enable ollama
        sudo systemctl start ollama
        
        # Wait for service to be ready
        sleep 5
        
        # Pull a lightweight model for vulnerability analysis
        echo "Pulling AI model for vulnerability analysis..."
        ollama pull llama2:7b-chat
        
        echo -e "${GREEN}✅ Ollama installed and model ready${NC}"
    else
        echo "Ollama already installed"
        
        # Make sure we have the required model
        if ! ollama list | grep -q "llama2"; then
            echo "Pulling required AI model..."
            ollama pull llama2:7b-chat
        fi
        
        echo -e "${GREEN}✅ Ollama configured${NC}"
    fi
}

setup_security_tools() {
    echo -e "${PURPLE}[3/5] Updating security tools...${NC}"
    
    # Update existing tools
    if command -v subfinder &> /dev/null; then
        echo "Updating subfinder..."
        GO111MODULE=on go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    fi
    
    if command -v httpx &> /dev/null; then
        echo "Updating httpx..."
        GO111MODULE=on go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
    fi
    
    if command -v nuclei &> /dev/null; then
        echo "Updating nuclei..."
        GO111MODULE=on go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
        nuclei -update-templates
    fi
    
    # Install additional tools for AI analysis
    echo "Installing additional tools..."
    
    # waybackurls for URL discovery
    if ! command -v waybackurls &> /dev/null; then
        GO111MODULE=on go install github.com/tomnomnom/waybackurls@latest
    fi
    
    # gau (GetAllUrls)
    if ! command -v gau &> /dev/null; then
        GO111MODULE=on go install github.com/lc/gau/v2/cmd/gau@latest
    fi
    
    # gospider
    if ! command -v gospider &> /dev/null; then
        GO111MODULE=on go install github.com/jaeles-project/gospider@latest
    fi
    
    echo -e "${GREEN}✅ Security tools updated${NC}"
}

setup_directories() {
    echo -e "${PURPLE}[4/5] Setting up directories...${NC}"
    
    # Create necessary directories
    mkdir -p results
    mkdir -p config
    mkdir -p logs
    mkdir -p temp
    
    # Set proper permissions
    chmod 755 results config logs temp
    chmod +x *.py
    chmod +x *.sh
    
    echo -e "${GREEN}✅ Directories configured${NC}"
}

create_ai_config() {
    echo -e "${PURPLE}[5/5] Creating AI configuration...${NC}"
    
    # Create AI configuration file
    cat > config/ai_config.json << EOF
{
    "ai_models": {
        "ollama": {
            "enabled": true,
            "endpoint": "http://localhost:11434/api/generate",
            "model": "llama2:7b-chat",
            "timeout": 30
        },
        "huggingface": {
            "enabled": true,
            "endpoint": "https://api-inference.huggingface.co/models/",
            "models": [
                "microsoft/DialoGPT-medium",
                "facebook/bart-large",
                "microsoft/CodeBERT-base"
            ],
            "timeout": 30
        }
    },
    "vulnerability_analysis": {
        "max_concurrent": 5,
        "detailed_analysis": true,
        "generate_poc": true,
        "severity_scoring": "cvss_v3"
    },
    "reporting": {
        "generate_html": true,
        "generate_json": true,
        "generate_hackerone": true,
        "auto_email": true
    }
}
EOF

    echo -e "${GREEN}✅ AI configuration created${NC}"
}

test_ai_setup() {
    echo -e "${PURPLE}Testing AI setup...${NC}"
    
    # Test Ollama
    if ollama list | grep -q "llama2"; then
        echo -e "${GREEN}✅ Ollama model ready${NC}"
    else
        echo -e "${YELLOW}⚠️  Ollama model not found, will use fallback methods${NC}"
    fi
    
    # Test Python dependencies
    python3 -c "import aiohttp, requests, asyncio, json" && echo -e "${GREEN}✅ Python dependencies working${NC}" || echo -e "${RED}❌ Python dependency issue${NC}"
    
    echo -e "${GREEN}🎉 AI setup complete!${NC}"
}

show_usage_instructions() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🚀 Setup Complete!                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${GREEN}Your AI-Enhanced Bug Bounty Scanner is ready!${NC}"
    echo ""
    echo -e "${YELLOW}Quick Start:${NC}"
    echo "1. Configure email settings:"
    echo "   ./start.sh --setup"
    echo ""
    echo "2. Run an AI-enhanced scan:"
    echo "   ./start.sh target.com"
    echo ""
    echo -e "${YELLOW}Features enabled:${NC}"
    echo "✅ AI-powered vulnerability analysis"
    echo "✅ Professional HackerOne report generation"
    echo "✅ Email report delivery"
    echo "✅ Comprehensive HTML reports"
    echo "✅ Executive summaries"
    echo ""
    echo -e "${PURPLE}AI Models Available:${NC}"
    echo "🤖 Ollama (local, private)"
    echo "🌐 HuggingFace (free tier)"
    echo ""
    echo -e "${RED}⚠️  Remember: Only scan domains you own or have permission to test!${NC}"
}

main() {
    print_banner
    
    echo "This script will install AI dependencies for enhanced bug bounty scanning."
    echo ""
    read -p "Continue with installation? (y/N): " confirm
    
    if [[ $confirm != [yY] && $confirm != [yY][eE][sS] ]]; then
        echo "Installation cancelled."
        exit 1
    fi
    
    install_python_dependencies
    install_ollama
    setup_security_tools
    setup_directories
    create_ai_config
    test_ai_setup
    show_usage_instructions
}

main "$@"
