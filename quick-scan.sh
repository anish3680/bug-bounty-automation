#!/bin/bash

# Quick Bug Bounty Scan Script
# Easy-to-use wrapper for single target scanning

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_banner() {
    echo -e "${BLUE}"
    echo "┌─────────────────────────────────────────┐"
    echo "│       🎯 Bug Bounty Quick Scanner       │"
    echo "│        Automated Vulnerability         │"
    echo "│           Discovery Tool               │"
    echo "└─────────────────────────────────────────┘"
    echo -e "${NC}"
}

usage() {
    echo -e "${YELLOW}Usage: $0 <target-domain>${NC}"
    echo ""
    echo "Examples:"
    echo "  $0 example.com"
    echo "  $0 subdomain.example.com"
    echo ""
    echo "The script will:"
    echo "  • Find all subdomains"
    echo "  • Check which hosts are alive"
    echo "  • Crawl for URLs and parameters"
    echo "  • Scan for vulnerabilities (XSS, SQLi, etc.)"
    echo "  • Generate detailed HTML report"
    echo "  • Send email notification"
    echo ""
    echo -e "${RED}⚠️  IMPORTANT: Only scan domains you own or have permission to test!${NC}"
}

check_setup() {
    if [ ! -f "$SCRIPT_DIR/hunt.sh" ]; then
        echo -e "${RED}❌ Bug bounty framework not found!${NC}"
        echo "Please run: ./install.sh first"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/config/email_config.json" ]; then
        echo -e "${YELLOW}⚠️  Email configuration not found${NC}"
        echo "Creating default email config..."
        mkdir -p "$SCRIPT_DIR/config"
        cat > "$SCRIPT_DIR/config/email_config.json" << 'EOF'
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "recipient_email": "your-email@gmail.com",
    "developer_email": "developer@target-company.com"
}
EOF
        echo -e "${YELLOW}📝 Please edit $SCRIPT_DIR/config/email_config.json with your email settings${NC}"
    fi
}

validate_domain() {
    local domain=$1
    
    # Basic domain validation
    if [[ ! $domain =~ ^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$ ]]; then
        echo -e "${RED}❌ Invalid domain format: $domain${NC}"
        exit 1
    fi
    
    # Check if domain resolves
    if ! nslookup "$domain" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Warning: Domain $domain does not resolve to an IP address${NC}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

confirm_scan() {
    local domain=$1
    
    echo -e "${YELLOW}⚠️  LEGAL WARNING${NC}"
    echo "You are about to scan: $domain"
    echo ""
    echo "By continuing, you confirm that:"
    echo "  • You own this domain OR have explicit written permission to test it"
    echo "  • You will follow responsible disclosure practices"
    echo "  • You understand this is for authorized security testing only"
    echo ""
    read -p "Do you have permission to scan $domain? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Scan cancelled."
        exit 0
    fi
}

run_scan() {
    local domain=$1
    local temp_file=$(mktemp)
    
    echo "$domain" > "$temp_file"
    
    echo -e "${GREEN}🚀 Starting bug bounty scan for $domain${NC}"
    echo "This may take 30-60 minutes depending on the target size..."
    echo ""
    
    # Run the main hunting script
    "$SCRIPT_DIR/hunt.sh" "$temp_file"
    
    # Cleanup
    rm -f "$temp_file"
    
    # Show results
    local latest_session=$(cat "$SCRIPT_DIR/results/latest_session.txt" 2>/dev/null || echo "")
    if [ -n "$latest_session" ] && [ -d "$latest_session" ]; then
        echo -e "${GREEN}✅ Scan completed!${NC}"
        echo ""
        echo "Results location: $latest_session"
        
        # Show quick summary
        local subdomains=$(wc -l < "$latest_session/recon/all_subdomains.txt" 2>/dev/null || echo "0")
        local alive=$(wc -l < "$latest_session/alive/alive_hosts.txt" 2>/dev/null || echo "0")
        local urls=$(wc -l < "$latest_session/urls/all_urls.txt" 2>/dev/null || echo "0")
        local vulns=$(cat "$latest_session/reports/vuln_count.txt" 2>/dev/null || echo "0")
        
        echo -e "${BLUE}📊 Quick Summary:${NC}"
        echo "  Subdomains found: $subdomains"
        echo "  Alive hosts: $alive"
        echo "  URLs discovered: $urls"
        echo "  Potential vulnerabilities: $vulns"
        echo ""
        
        # Check if report exists
        local report_file="$latest_session/reports/final_report.html"
        if [ -f "$report_file" ]; then
            echo -e "${GREEN}📄 HTML Report: $report_file${NC}"
            echo ""
            
            # Offer to open report
            if command -v firefox >/dev/null 2>&1; then
                read -p "Open report in Firefox? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    firefox "$report_file" &
                fi
            elif command -v google-chrome >/dev/null 2>&1; then
                read -p "Open report in Chrome? (y/N): " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    google-chrome "$report_file" &
                fi
            fi
        fi
        
        echo -e "${YELLOW}📧 Check your email for detailed results!${NC}"
    else
        echo -e "${RED}❌ Scan may have failed. Check logs in $SCRIPT_DIR/logs/${NC}"
    fi
}

main() {
    print_banner
    
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi
    
    local target=$1
    
    # Remove protocol if present
    target=$(echo "$target" | sed 's|^https\?://||' | sed 's|/.*||')
    
    echo -e "${BLUE}🎯 Target: $target${NC}"
    echo ""
    
    # Check setup
    check_setup
    
    # Validate domain
    validate_domain "$target"
    
    # Confirm permission
    confirm_scan "$target"
    
    # Run scan
    run_scan "$target"
}

# Run main function
main "$@"
