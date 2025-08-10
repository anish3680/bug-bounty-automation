#!/bin/bash

# Bug Bounty Automation - Quick Start Script
# Usage: ./start.sh <target-domain>

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
    echo "║              🎯 Bug Bounty Automation Starter               ║"
    echo "║            Complete Security Testing Framework              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_usage() {
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./start.sh <target-domain>     # Single target scan"
    echo "  ./start.sh --multiple          # Multiple targets from file"
    echo "  ./start.sh --demo              # Demo mode"
    echo "  ./start.sh --setup             # Setup configuration"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  ./start.sh example.com"
    echo "  ./start.sh subdomain.example.com" 
    echo "  ./start.sh --setup"
    echo ""
    echo -e "${RED}⚠️  IMPORTANT: Only scan domains you own or have permission!${NC}"
}

setup_config() {
    echo -e "${PURPLE}🔧 Setting up configuration...${NC}"
    echo ""
    
    # Email setup
    read -p "Enter your Gmail address: " email
    read -s -p "Enter your Gmail app password: " password
    echo ""
    read -p "Enter target company security email: " dev_email
    
    # Update config
    cat > config/email_config.json << EOF
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "$email",
    "sender_password": "$password",
    "recipient_email": "$email",
    "developer_email": "$dev_email"
}
EOF
    
    echo -e "${GREEN}✅ Configuration updated!${NC}"
}

run_single_scan() {
    local target=$1
    echo -e "${GREEN}🚀 Starting AI-Enhanced scan for: $target${NC}"
    echo ""
    
    # Ask user which type of scan to run
    echo -e "${YELLOW}Select scan type:${NC}"
    echo "1. Quick scan (faster, basic vulnerability detection)"
    echo "2. AI-Enhanced scan (comprehensive, AI-powered analysis, HackerOne reports)"
    echo ""
    read -p "Enter your choice (1 or 2): " scan_choice
    
    case $scan_choice in
        2)
            echo -e "${PURPLE}🤖 Running AI-Enhanced Bug Bounty Scan...${NC}"
            python3 ai_vuln_scanner.py "$target"
            
            # Find the latest results directory
            latest_dir=$(find results -maxdepth 1 -name "${target}_*" -type d | sort | tail -1)
            
            if [ -n "$latest_dir" ]; then
                echo -e "${GREEN}📧 Sending professional report via email...${NC}"
                python3 ai_report_sender.py "$latest_dir"
            else
                echo -e "${RED}❌ Could not find scan results directory${NC}"
            fi
            ;;
        1)
            echo -e "${BLUE}⚡ Running Quick Scan...${NC}"
            ./quick-scan.sh "$target"
            ;;
        *)
            echo -e "${RED}Invalid choice. Running quick scan...${NC}"
            ./quick-scan.sh "$target"
            ;;
    esac
}

run_multiple_scan() {
    echo -e "${PURPLE}📝 Multiple target scan${NC}"
    echo ""
    echo "Create a file called 'targets.txt' with one domain per line:"
    echo "example1.com"
    echo "example2.com"
    echo "subdomain.example3.com"
    echo ""
    
    if [ ! -f "targets.txt" ]; then
        echo "Creating example targets.txt file..."
        cat > targets.txt << EOF
# Add your target domains here (one per line)
# Remove the # and replace with real domains you have permission to test
# example1.com
# example2.com
# subdomain.example3.com
EOF
        echo -e "${YELLOW}📝 Edit targets.txt file and run again${NC}"
        return 1
    fi
    
    echo -e "${GREEN}🚀 Starting multiple target scan...${NC}"
    ./hunt.sh targets.txt
}

run_demo() {
    echo -e "${PURPLE}🎬 Running demonstration mode...${NC}"
    ./test_demo.sh
}

main() {
    print_banner
    
    case "${1:-}" in
        --setup)
            setup_config
            ;;
        --multiple)
            run_multiple_scan
            ;;
        --demo)
            run_demo
            ;;
        --help|-h)
            show_usage
            ;;
        "")
            show_usage
            exit 1
            ;;
        *)
            # Single target scan
            run_single_scan "$1"
            ;;
    esac
}

# Check if we're in the right directory
if [ ! -f "hunt.sh" ]; then
    echo -e "${RED}❌ Error: Please run this from the bug-bounty-automation directory${NC}"
    exit 1
fi

main "$@"
