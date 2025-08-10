#!/bin/bash

# Bug Bounty Automation Demo Script
# This script demonstrates all the features of the automation framework

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_TARGET="httpbin.org"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_banner() {
    clear
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              🎯 Bug Bounty Automation Demo                   ║"
    echo "║            Complete Vulnerability Discovery System          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_demo() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[$timestamp]${NC} ${message}"
            ;;
        "STEP")
            echo -e "${CYAN}[$timestamp] 🔄${NC} ${message}"
            ;;
        "SUCCESS")
            echo -e "${PURPLE}[$timestamp] ✅${NC} ${message}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[$timestamp] ⚠️${NC} ${message}"
            ;;
    esac
}

check_setup() {
    log_demo "STEP" "Checking system setup..."
    
    # Check if framework exists
    if [ ! -f "$SCRIPT_DIR/hunt.sh" ]; then
        log_demo "WARNING" "Main hunt.sh script not found!"
        return 1
    fi
    
    # Check configuration
    if [ ! -f "$SCRIPT_DIR/config/email_config.json" ]; then
        log_demo "WARNING" "Email configuration not found!"
        return 1
    fi
    
    # Check available tools
    local tools_available=0
    local tools=("curl" "wget" "httpx" "nmap")
    
    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            log_demo "SUCCESS" "✓ $tool is available"
            tools_available=$((tools_available + 1))
        else
            log_demo "WARNING" "✗ $tool is not available"
        fi
    done
    
    log_demo "INFO" "Found $tools_available available security tools"
    return 0
}

demo_recon() {
    log_demo "STEP" "Demonstrating reconnaissance capabilities..."
    
    # Create demo session
    local session_dir="$SCRIPT_DIR/results/demo_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$session_dir"/{recon,alive,urls,vulnerabilities,reports}
    
    # Simulate subdomain discovery
    log_demo "INFO" "Running subdomain enumeration for $DEMO_TARGET"
    echo "$DEMO_TARGET" > "$session_dir/recon/all_subdomains.txt"
    echo "api.$DEMO_TARGET" >> "$session_dir/recon/all_subdomains.txt"
    echo "www.$DEMO_TARGET" >> "$session_dir/recon/all_subdomains.txt"
    
    # Simulate alive check with httpx if available
    if command -v httpx >/dev/null 2>&1; then
        log_demo "INFO" "Checking alive hosts with HTTPx..."
        httpx -list "$session_dir/recon/all_subdomains.txt" -o "$session_dir/alive/alive_hosts.txt" -silent -threads 10 2>/dev/null || {
            # Fallback manual check
            echo "https://$DEMO_TARGET" > "$session_dir/alive/alive_hosts.txt"
        }
    else
        # Fallback with curl
        log_demo "INFO" "Checking alive hosts with curl..."
        while IFS= read -r host; do
            if curl -s --max-time 5 "https://$host" >/dev/null 2>&1; then
                echo "https://$host" >> "$session_dir/alive/alive_hosts.txt"
            elif curl -s --max-time 5 "http://$host" >/dev/null 2>&1; then
                echo "http://$host" >> "$session_dir/alive/alive_hosts.txt"
            fi
        done < "$session_dir/recon/all_subdomains.txt"
    fi
    
    local alive_count=$(wc -l < "$session_dir/alive/alive_hosts.txt" 2>/dev/null || echo "0")
    log_demo "SUCCESS" "Found $alive_count alive hosts"
    
    # Simulate URL crawling
    log_demo "INFO" "Simulating URL discovery..."
    cat > "$session_dir/urls/all_urls.txt" << EOF
https://$DEMO_TARGET/get
https://$DEMO_TARGET/post
https://$DEMO_TARGET/put
https://$DEMO_TARGET/delete
https://$DEMO_TARGET/status/200
https://$DEMO_TARGET/json
EOF
    
    # Extract parameterized URLs (simulated)
    echo "https://$DEMO_TARGET/get?param=test" > "$session_dir/urls/parametrized_urls.txt"
    
    local url_count=$(wc -l < "$session_dir/urls/all_urls.txt")
    local param_count=$(wc -l < "$session_dir/urls/parametrized_urls.txt")
    log_demo "SUCCESS" "Discovered $url_count URLs ($param_count with parameters)"
    
    echo "$session_dir"
}

demo_vulnerability_scan() {
    local session_dir=$1
    log_demo "STEP" "Demonstrating vulnerability scanning..."
    
    # Simulate vulnerability findings
    local vuln_dir="$session_dir/vulnerabilities"
    
    # Simulate Nuclei findings
    cat > "$vuln_dir/nuclei_results.txt" << 'EOF'
[demo-tech-detect] [http] [info] https://httpbin.org [nginx,python,gunicorn]
[demo-headers-check] [http] [info] https://httpbin.org [missing-security-headers]
[demo-ssl-check] [http] [medium] https://httpbin.org [ssl-configuration-weak]
EOF
    
    # Simulate XSS findings (example)
    cat > "$vuln_dir/dalfox_results.txt" << 'EOF'
[DEMO] Reflected XSS found at https://httpbin.org/get?param=<script>alert(1)</script>
[DEMO] Parameter: param
[DEMO] Payload: <script>alert(1)</script>
EOF
    
    log_demo "SUCCESS" "Simulated vulnerability scan completed"
    log_demo "INFO" "Found example findings: SSL issues, missing headers, XSS potential"
}

demo_reporting() {
    local session_dir=$1
    log_demo "STEP" "Generating comprehensive report..."
    
    local report_dir="$session_dir/reports"
    local vuln_count=5  # Simulated count
    
    # Generate HTML report
    cat > "$report_dir/final_report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Bug Bounty Demo Report - $DEMO_TARGET</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header { color: #e74c3c; border-bottom: 3px solid #e74c3c; padding-bottom: 20px; margin-bottom: 30px; }
        .vulnerability { background: #ffe6e6; border-left: 5px solid #e74c3c; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .info { background: #e8f4f8; border-left: 5px solid #3498db; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .success { background: #e8f5e8; border-left: 5px solid #27ae60; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat-box { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; }
        .demo-badge { background: #ff9800; color: white; padding: 5px 10px; border-radius: 20px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Bug Bounty Automation Demo Report</h1>
            <span class="demo-badge">DEMONSTRATION MODE</span>
            <h2>Target: $DEMO_TARGET</h2>
            <p><strong>Scan Date:</strong> $(date)</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <h3>3</h3>
                <p>Subdomains Found</p>
            </div>
            <div class="stat-box">
                <h3>1</h3>
                <p>Alive Hosts</p>
            </div>
            <div class="stat-box">
                <h3>6</h3>
                <p>URLs Crawled</p>
            </div>
            <div class="stat-box">
                <h3 style="color: #e74c3c;">$vuln_count</h3>
                <p>Demo Findings</p>
            </div>
        </div>
        
        <div class="vulnerability">
            <h3>🔍 Demo Security Findings</h3>
            <ul>
                <li><strong>SSL Configuration:</strong> Weak SSL/TLS configuration detected</li>
                <li><strong>Security Headers:</strong> Missing security headers (HSTS, CSP, etc.)</li>
                <li><strong>XSS Potential:</strong> Reflected XSS vulnerability in GET parameter</li>
                <li><strong>Information Disclosure:</strong> Server version information exposed</li>
                <li><strong>Technology Stack:</strong> Backend technologies detected (Nginx, Python, Gunicorn)</li>
            </ul>
        </div>
        
        <div class="info">
            <h3>📊 Automation Features Demonstrated</h3>
            <ul>
                <li>✅ Automated subdomain enumeration</li>
                <li>✅ Alive host detection</li>
                <li>✅ URL crawling and parameter discovery</li>
                <li>✅ Vulnerability scanning simulation</li>
                <li>✅ Comprehensive HTML reporting</li>
                <li>✅ Email notification system</li>
                <li>✅ Approval workflow for developer notifications</li>
                <li>✅ Debug monitoring and logging</li>
            </ul>
        </div>
        
        <div class="success">
            <h3>✨ What This System Provides</h3>
            <ol>
                <li><strong>Automated Discovery:</strong> Finds subdomains, URLs, and parameters automatically</li>
                <li><strong>Vulnerability Detection:</strong> Scans for XSS, SQLi, configuration issues, and more</li>
                <li><strong>Smart Reporting:</strong> Generates professional HTML and email reports</li>
                <li><strong>Approval Workflow:</strong> You review findings before notifying developers</li>
                <li><strong>Complete Logging:</strong> Debug every step for transparency</li>
                <li><strong>Terminal Integration:</strong> Runs fully automated from command line</li>
            </ol>
        </div>
        
        <div class="info">
            <h3>🚀 Ready for Production</h3>
            <p>To use this system for real bug bounty hunting:</p>
            <ol>
                <li>Configure email settings in <code>config/email_config.json</code></li>
                <li>Install additional security tools with <code>./install.sh</code></li>
                <li>Run <code>./quick-scan.sh target.com</code> for single targets</li>
                <li>Run <code>./hunt.sh targets.txt</code> for bulk scanning</li>
                <li>Monitor with <code>./debug_monitor.sh</code></li>
                <li>Review findings and approve developer notifications</li>
            </ol>
        </div>
        
        <p style="text-align: center; color: #7f8c8d; margin-top: 40px;">
            <em>Generated by Bug Bounty Automation Framework</em><br>
            <small>This is a demonstration - always verify findings manually</small>
        </p>
    </div>
</body>
</html>
EOF
    
    echo "$vuln_count" > "$report_dir/vuln_count.txt"
    log_demo "SUCCESS" "HTML report generated: $report_dir/final_report.html"
    
    echo "$report_dir/final_report.html"
}

demo_email_system() {
    local session_dir=$1
    local report_file=$2
    
    log_demo "STEP" "Demonstrating email notification system..."
    
    # Show what the email system would do
    cat << EOF

${CYAN}📧 EMAIL NOTIFICATION WORKFLOW DEMO${NC}
=====================================

${YELLOW}1. INITIAL NOTIFICATION TO SECURITY TEAM${NC}
   Subject: 🚨 URGENT: Bug Bounty Alert - $DEMO_TARGET (5 vulnerabilities)
   
   Content:
   - Executive summary of findings
   - Vulnerability breakdown by type
   - Risk assessment and severity levels
   - Technical details and proof of concepts
   - Next steps and recommendations

${YELLOW}2. APPROVAL WORKFLOW${NC}
   - System prompts you to review findings
   - You decide whether to notify developers
   - Only approved findings are sent to developers
   - All actions are logged for audit trail

${YELLOW}3. DEVELOPER NOTIFICATION (After Approval)${NC}
   Subject: 🛡️ Security Assessment Report - $DEMO_TARGET (5 findings)
   
   Content:
   - Professional vulnerability report
   - Remediation recommendations
   - Timeline for fixes
   - Responsible disclosure guidelines

EOF

    log_demo "INFO" "Email demo completed - no actual emails sent"
}

demo_approval_system() {
    log_demo "STEP" "Demonstrating approval workflow..."
    
    cat << EOF

${CYAN}🔍 APPROVAL SYSTEM WORKFLOW${NC}
============================

${GREEN}Current Status:${NC} 5 vulnerabilities found for $DEMO_TARGET

${YELLOW}Findings Summary:${NC}
• SSL Configuration Issues: 1
• Missing Security Headers: 1  
• XSS Vulnerabilities: 1
• Information Disclosure: 2

${PURPLE}Approval Options:${NC}
[Y] Yes - Send report to developer
[N] No - Do not send report  
[S] Show summary again

${BLUE}Benefits:${NC}
✅ You control what gets reported
✅ Prevents false positive spam
✅ Maintains professional relationships
✅ Ensures quality over quantity
✅ Complete audit trail

EOF

    log_demo "INFO" "Approval system demo completed"
}

demo_monitoring() {
    log_demo "STEP" "Demonstrating debug monitoring capabilities..."
    
    # Show monitoring features
    cat << EOF

${CYAN}🔍 DEBUG MONITORING FEATURES${NC}
===============================

${GREEN}Real-time System Monitoring:${NC}
• Active security scan processes
• Tool status and availability  
• Network connectivity checks
• Disk usage and cleanup alerts
• Recent scan session history

${GREEN}Log Analysis:${NC}
• Categorized error reporting
• Warning and timeout tracking
• Success rate monitoring
• Performance metrics
• Debug trace information

${GREEN}Interactive Commands:${NC}
• ./debug_monitor.sh           - Full monitoring dashboard
• ./debug_monitor.sh --monitor - Real-time log tailing
• ./debug_monitor.sh --report  - Generate system report

EOF

    log_demo "INFO" "Monitoring demo completed"
}

main() {
    print_banner
    
    echo -e "${BLUE}🎯 Bug Bounty Automation Framework Demo${NC}"
    echo "========================================"
    echo ""
    echo "This demonstration shows you a complete automated bug bounty system that:"
    echo "• Discovers subdomains and alive hosts automatically"
    echo "• Crawls for URLs and parameters"  
    echo "• Scans for vulnerabilities (XSS, SQLi, etc.)"
    echo "• Generates professional reports"
    echo "• Emails you findings first, then developers after approval"
    echo "• Provides complete debugging and monitoring"
    echo ""
    
    read -p "Press Enter to start the demonstration..."
    
    # Step 1: Check setup
    if ! check_setup; then
        log_demo "WARNING" "Some components missing, but demo will continue"
    fi
    echo ""
    
    # Step 2: Reconnaissance demo
    local session_dir=$(demo_recon)
    echo ""
    
    # Step 3: Vulnerability scanning demo
    demo_vulnerability_scan "$session_dir"
    echo ""
    
    # Step 4: Report generation demo
    local report_file=$(demo_reporting "$session_dir")
    echo ""
    
    # Step 5: Email system demo
    demo_email_system "$session_dir" "$report_file"
    echo ""
    
    # Step 6: Approval system demo
    demo_approval_system
    echo ""
    
    # Step 7: Monitoring demo
    demo_monitoring
    echo ""
    
    # Summary
    echo -e "${GREEN}🎉 DEMONSTRATION COMPLETED${NC}"
    echo "========================="
    echo ""
    echo -e "${CYAN}Generated Demo Files:${NC}"
    echo "• Session Directory: $session_dir"
    echo "• HTML Report: $report_file" 
    echo "• Vulnerability Data: $session_dir/vulnerabilities/"
    echo "• Logs: $session_dir/../logs/"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Configure email settings: config/email_config.json"
    echo "2. Install additional tools: ./install.sh"
    echo "3. Test on real target: ./quick-scan.sh example.com"
    echo "4. Monitor system: ./debug_monitor.sh"
    echo ""
    echo -e "${BLUE}View the generated report:${NC}"
    echo "firefox $report_file"
    echo ""
    echo -e "${GREEN}✅ Your complete bug bounty automation system is ready!${NC}"
}

# Check if script is being run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
