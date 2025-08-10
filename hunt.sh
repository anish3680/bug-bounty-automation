#!/bin/bash

# Bug Bounty Automation Hunter
# Main script that orchestrates the entire bug hunting process

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"
LOGS_DIR="$SCRIPT_DIR/logs"
CONFIG_DIR="$SCRIPT_DIR/config"
TOOLS_DIR="$SCRIPT_DIR/tools"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} ${message}"
            echo "[$timestamp] [INFO] $message" >> "$LOGS_DIR/hunt.log"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} ${message}"
            echo "[$timestamp] [WARN] $message" >> "$LOGS_DIR/hunt.log"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${message}"
            echo "[$timestamp] [ERROR] $message" >> "$LOGS_DIR/hunt.log"
            ;;
        "SUCCESS")
            echo -e "${PURPLE}[SUCCESS]${NC} ${message}"
            echo "[$timestamp] [SUCCESS] $message" >> "$LOGS_DIR/hunt.log"
            ;;
        "VULN")
            echo -e "${RED}[VULNERABILITY]${NC} ${message}"
            echo "[$timestamp] [VULNERABILITY] $message" >> "$LOGS_DIR/hunt.log"
            ;;
    esac
}

# Function to check if required tools are installed
check_tools() {
    local required_tools=("subfinder" "amass" "assetfinder" "httpx" "katana" "gau" "nuclei" "dalfox" "sqlmap" "hakrawler")
    local missing_tools=()
    
    log "INFO" "Checking required tools..."
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log "ERROR" "Missing tools: ${missing_tools[*]}"
        log "ERROR" "Please run ./install.sh first"
        exit 1
    fi
    
    log "SUCCESS" "All required tools are installed"
}

# Function to create session directory
create_session() {
    local target_domain=$1
    local session_id=$(date +"%Y%m%d_%H%M%S")
    SESSION_DIR="$RESULTS_DIR/${target_domain}_${session_id}"
    
    mkdir -p "$SESSION_DIR"/{recon,alive,urls,vulnerabilities,reports}
    
    log "INFO" "Created session: $SESSION_DIR"
    echo "$SESSION_DIR" > "$RESULTS_DIR/latest_session.txt"
}

# Function to run subdomain enumeration
run_recon() {
    local target=$1
    local recon_dir="$SESSION_DIR/recon"
    
    log "INFO" "Starting reconnaissance for $target"
    
    # Subfinder
    log "INFO" "Running subfinder..."
    timeout 300 subfinder -d "$target" -o "$recon_dir/subfinder.txt" -silent 2>>"$LOGS_DIR/subfinder_error.log" || {
        log "WARN" "Subfinder timed out or failed for $target"
    }
    
    # Assetfinder
    log "INFO" "Running assetfinder..."
    timeout 300 assetfinder --subs-only "$target" > "$recon_dir/assetfinder.txt" 2>>"$LOGS_DIR/assetfinder_error.log" || {
        log "WARN" "Assetfinder timed out or failed for $target"
    }
    
    # Amass (limited time for faster results)
    log "INFO" "Running amass (passive)..."
    timeout 600 amass enum -passive -d "$target" -o "$recon_dir/amass.txt" 2>>"$LOGS_DIR/amass_error.log" || {
        log "WARN" "Amass timed out or failed for $target"
    }
    
    # Combine and deduplicate results
    log "INFO" "Combining subdomain results..."
    cat "$recon_dir"/*.txt 2>/dev/null | sort -u > "$recon_dir/all_subdomains.txt" || {
        echo "$target" > "$recon_dir/all_subdomains.txt"
    }
    
    local subdomain_count=$(wc -l < "$recon_dir/all_subdomains.txt")
    log "SUCCESS" "Found $subdomain_count subdomains for $target"
}

# Function to check alive hosts
check_alive() {
    local recon_dir="$SESSION_DIR/recon"
    local alive_dir="$SESSION_DIR/alive"
    
    log "INFO" "Checking alive hosts..."
    
    if [ -f "$recon_dir/all_subdomains.txt" ]; then
        timeout 300 httpx -l "$recon_dir/all_subdomains.txt" -o "$alive_dir/alive_hosts.txt" -silent -threads 50 2>>"$LOGS_DIR/httpx_error.log" || {
            log "WARN" "HTTPx timed out or failed"
        }
        
        # Also save with full URLs
        timeout 300 httpx -l "$recon_dir/all_subdomains.txt" -o "$alive_dir/alive_urls.txt" -silent -threads 50 -no-color 2>>"$LOGS_DIR/httpx_error.log" || {
            log "WARN" "HTTPx URL enumeration timed out or failed"
        }
        
        local alive_count=$(wc -l < "$alive_dir/alive_hosts.txt" 2>/dev/null || echo "0")
        log "SUCCESS" "Found $alive_count alive hosts"
    else
        log "ERROR" "No subdomains file found"
        return 1
    fi
}

# Function to crawl URLs and find parameters
crawl_urls() {
    local alive_dir="$SESSION_DIR/alive"
    local urls_dir="$SESSION_DIR/urls"
    
    log "INFO" "Starting URL crawling and parameter discovery..."
    
    if [ -f "$alive_dir/alive_hosts.txt" ]; then
        # Katana crawling
        log "INFO" "Running katana crawler..."
        timeout 600 katana -list "$alive_dir/alive_hosts.txt" -o "$urls_dir/katana_urls.txt" -silent -d 3 -c 20 2>>"$LOGS_DIR/katana_error.log" || {
            log "WARN" "Katana timed out or failed"
        }
        
        # GAU (GetAllURLs)
        log "INFO" "Running gau..."
        while IFS= read -r host; do
            domain=$(echo "$host" | sed 's/https\?:\/\///' | cut -d'/' -f1)
            timeout 120 gau "$domain" >> "$urls_dir/gau_urls.txt" 2>>"$LOGS_DIR/gau_error.log" || {
                log "WARN" "GAU timed out or failed for $domain"
            }
        done < "$alive_dir/alive_hosts.txt"
        
        # Hakrawler
        log "INFO" "Running hakrawler..."
        timeout 300 hakrawler -urls "$alive_dir/alive_hosts.txt" -depth 2 -plain > "$urls_dir/hakrawler_urls.txt" 2>>"$LOGS_DIR/hakrawler_error.log" || {
            log "WARN" "Hakrawler timed out or failed"
        }
        
        # Combine all URLs
        cat "$urls_dir"/*.txt 2>/dev/null | sort -u > "$urls_dir/all_urls.txt" || {
            log "WARN" "No URLs collected from crawling"
            touch "$urls_dir/all_urls.txt"
        }
        
        # Extract URLs with parameters
        grep -E '\?' "$urls_dir/all_urls.txt" > "$urls_dir/parametrized_urls.txt" 2>/dev/null || {
            log "INFO" "No parametrized URLs found"
            touch "$urls_dir/parametrized_urls.txt"
        }
        
        local total_urls=$(wc -l < "$urls_dir/all_urls.txt" 2>/dev/null || echo "0")
        local param_urls=$(wc -l < "$urls_dir/parametrized_urls.txt" 2>/dev/null || echo "0")
        log "SUCCESS" "Collected $total_urls URLs ($param_urls with parameters)"
    else
        log "ERROR" "No alive hosts found for crawling"
        return 1
    fi
}

# Function to run vulnerability scans
run_vulnerability_scans() {
    local alive_dir="$SESSION_DIR/alive"
    local urls_dir="$SESSION_DIR/urls"
    local vuln_dir="$SESSION_DIR/vulnerabilities"
    
    log "INFO" "Starting vulnerability scans..."
    
    # Nuclei scan
    if [ -f "$alive_dir/alive_urls.txt" ]; then
        log "INFO" "Running Nuclei vulnerability scanner..."
        timeout 1800 nuclei -l "$alive_dir/alive_urls.txt" -o "$vuln_dir/nuclei_results.txt" -silent -severity low,medium,high,critical -rate-limit 10 2>>"$LOGS_DIR/nuclei_error.log" || {
            log "WARN" "Nuclei scan timed out or failed"
        }
    fi
    
    # XSS scan with Dalfox
    if [ -f "$urls_dir/parametrized_urls.txt" ] && [ -s "$urls_dir/parametrized_urls.txt" ]; then
        log "INFO" "Running XSS scan with Dalfox..."
        timeout 900 dalfox file "$urls_dir/parametrized_urls.txt" -o "$vuln_dir/dalfox_results.txt" --silence 2>>"$LOGS_DIR/dalfox_error.log" || {
            log "WARN" "Dalfox XSS scan timed out or failed"
        }
    fi
    
    # SQLi scan with SQLMap (limited to first 10 URLs to avoid long scans)
    if [ -f "$urls_dir/parametrized_urls.txt" ] && [ -s "$urls_dir/parametrized_urls.txt" ]; then
        log "INFO" "Running SQL injection scan (limited scope)..."
        head -10 "$urls_dir/parametrized_urls.txt" > "$urls_dir/sqlmap_targets.txt"
        
        while IFS= read -r url; do
            if [[ -n "$url" ]]; then
                timeout 300 sqlmap -u "$url" --batch --random-agent --level 1 --risk 1 --dbs --output-dir="$vuln_dir/sqlmap/" 2>>"$LOGS_DIR/sqlmap_error.log" || {
                    log "WARN" "SQLMap scan failed or timed out for $url"
                }
            fi
        done < "$urls_dir/sqlmap_targets.txt"
    fi
    
    log "SUCCESS" "Vulnerability scanning completed"
}

# Function to analyze results and find vulnerabilities
analyze_results() {
    local vuln_dir="$SESSION_DIR/vulnerabilities"
    local report_dir="$SESSION_DIR/reports"
    
    log "INFO" "Analyzing scan results for vulnerabilities..."
    
    local found_vulns=0
    
    # Check Nuclei results
    if [ -f "$vuln_dir/nuclei_results.txt" ] && [ -s "$vuln_dir/nuclei_results.txt" ]; then
        log "VULN" "Nuclei found vulnerabilities!"
        cp "$vuln_dir/nuclei_results.txt" "$report_dir/nuclei_vulns.txt"
        found_vulns=$((found_vulns + $(wc -l < "$vuln_dir/nuclei_results.txt")))
    fi
    
    # Check Dalfox results
    if [ -f "$vuln_dir/dalfox_results.txt" ] && [ -s "$vuln_dir/dalfox_results.txt" ]; then
        log "VULN" "XSS vulnerabilities found by Dalfox!"
        cp "$vuln_dir/dalfox_results.txt" "$report_dir/xss_vulns.txt"
        found_vulns=$((found_vulns + 1))
    fi
    
    # Check SQLMap results
    if [ -d "$vuln_dir/sqlmap" ]; then
        find "$vuln_dir/sqlmap" -name "*.csv" -o -name "*.txt" | while read -r file; do
            if [ -s "$file" ]; then
                log "VULN" "Potential SQL injection found: $file"
                cp "$file" "$report_dir/sqli_$(basename "$file")"
                found_vulns=$((found_vulns + 1))
            fi
        done
    fi
    
    echo "$found_vulns" > "$report_dir/vuln_count.txt"
    log "SUCCESS" "Analysis completed. Found $found_vulns potential vulnerabilities"
    
    return $found_vulns
}

# Function to generate report
generate_report() {
    local target=$1
    local report_dir="$SESSION_DIR/reports"
    local vuln_count=$(cat "$report_dir/vuln_count.txt" 2>/dev/null || echo "0")
    
    log "INFO" "Generating vulnerability report..."
    
    local report_file="$report_dir/final_report.html"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Bug Bounty Report - $target</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { color: #e74c3c; border-bottom: 3px solid #e74c3c; padding-bottom: 20px; margin-bottom: 30px; }
        .vulnerability { background: #ffe6e6; border-left: 5px solid #e74c3c; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .info { background: #e8f4f8; border-left: 5px solid #3498db; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .success { background: #e8f5e8; border-left: 5px solid #27ae60; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .code { background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 5px; font-family: monospace; overflow-x: auto; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat-box { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Bug Bounty Automation Report</h1>
            <h2>Target: $target</h2>
            <p><strong>Scan Date:</strong> $(date)</p>
            <p><strong>Session ID:</strong> $(basename "$SESSION_DIR")</p>
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <h3>$(wc -l < "$SESSION_DIR/recon/all_subdomains.txt" 2>/dev/null || echo "0")</h3>
                <p>Subdomains Found</p>
            </div>
            <div class="stat-box">
                <h3>$(wc -l < "$SESSION_DIR/alive/alive_hosts.txt" 2>/dev/null || echo "0")</h3>
                <p>Alive Hosts</p>
            </div>
            <div class="stat-box">
                <h3>$(wc -l < "$SESSION_DIR/urls/all_urls.txt" 2>/dev/null || echo "0")</h3>
                <p>URLs Crawled</p>
            </div>
            <div class="stat-box">
                <h3 style="color: #e74c3c;">$vuln_count</h3>
                <p>Vulnerabilities</p>
            </div>
        </div>
EOF

    # Add vulnerability details
    if [ "$vuln_count" -gt 0 ]; then
        echo "<h2>🚨 Vulnerabilities Found</h2>" >> "$report_file"
        
        # Nuclei vulnerabilities
        if [ -f "$report_dir/nuclei_vulns.txt" ]; then
            echo "<div class='vulnerability'>" >> "$report_file"
            echo "<h3>Nuclei Scan Results</h3>" >> "$report_file"
            echo "<div class='code'>" >> "$report_file"
            cat "$report_dir/nuclei_vulns.txt" | head -20 >> "$report_file"
            echo "</div></div>" >> "$report_file"
        fi
        
        # XSS vulnerabilities
        if [ -f "$report_dir/xss_vulns.txt" ]; then
            echo "<div class='vulnerability'>" >> "$report_file"
            echo "<h3>XSS Vulnerabilities (Dalfox)</h3>" >> "$report_file"
            echo "<div class='code'>" >> "$report_file"
            cat "$report_dir/xss_vulns.txt" | head -10 >> "$report_file"
            echo "</div></div>" >> "$report_file"
        fi
        
        # SQL injection
        if ls "$report_dir"/sqli_* 1> /dev/null 2>&1; then
            echo "<div class='vulnerability'>" >> "$report_file"
            echo "<h3>SQL Injection Findings</h3>" >> "$report_file"
            for sqli_file in "$report_dir"/sqli_*; do
                if [ -f "$sqli_file" ]; then
                    echo "<h4>$(basename "$sqli_file")</h4>" >> "$report_file"
                    echo "<div class='code'>" >> "$report_file"
                    head -10 "$sqli_file" >> "$report_file"
                    echo "</div>" >> "$report_file"
                fi
            done
            echo "</div>" >> "$report_file"
        fi
    else
        echo "<div class='success'>" >> "$report_file"
        echo "<h2>✅ No Critical Vulnerabilities Found</h2>" >> "$report_file"
        echo "<p>The automated scans did not identify any immediate security vulnerabilities. However, manual testing may reveal additional issues.</p>" >> "$report_file"
        echo "</div>" >> "$report_file"
    fi

    # Add scan details
    cat >> "$report_file" << EOF
        
        <div class="info">
            <h2>📊 Scan Details</h2>
            <p><strong>Reconnaissance Tools:</strong> Subfinder, Amass, Assetfinder</p>
            <p><strong>Crawling Tools:</strong> Katana, GAU, Hakrawler</p>
            <p><strong>Vulnerability Scanners:</strong> Nuclei, Dalfox, SQLMap</p>
            <p><strong>Full Results Location:</strong> $SESSION_DIR</p>
        </div>
        
        <div class="info">
            <h2>📋 Next Steps</h2>
            <ol>
                <li>Review the full scan results in the session directory</li>
                <li>Manually verify any identified vulnerabilities</li>
                <li>Perform manual testing on interesting endpoints</li>
                <li>Check for business logic flaws</li>
                <li>Test authentication and authorization controls</li>
            </ol>
        </div>
        
        <p style="text-align: center; color: #7f8c8d; margin-top: 40px;">
            <em>Generated by Bug Bounty Automation Framework</em><br>
            <small>Always verify findings manually before reporting</small>
        </p>
    </div>
</body>
</html>
EOF

    log "SUCCESS" "Report generated: $report_file"
    echo "$report_file" > "$RESULTS_DIR/latest_report.txt"
}

# Function to send email notification with approval system
send_email_notification() {
    local target=$1
    local vuln_count=$(cat "$SESSION_DIR/reports/vuln_count.txt" 2>/dev/null || echo "0")
    local report_file=$(cat "$RESULTS_DIR/latest_report.txt" 2>/dev/null)
    
    log "INFO" "Sending initial email notification to security team..."
    
    # Send initial notification to security team
    python3 "$SCRIPT_DIR/send_email.py" "$target" "$vuln_count" "$report_file" "$SESSION_DIR" || {
        log "ERROR" "Failed to send email notification"
        return 1
    }
    
    log "SUCCESS" "Email notification sent to security team successfully"
    
    # If vulnerabilities were found, prompt for developer notification approval
    if [ "$vuln_count" -gt 0 ]; then
        log "INFO" "Starting approval process for developer notification..."
        
        # Run the approval system in background to not block the main process
        nohup python3 "$SCRIPT_DIR/approve_and_send.py" "$target" "$vuln_count" "$SESSION_DIR" > "$LOGS_DIR/approval_$(date +%s).log" 2>&1 &
        local approval_pid=$!
        
        log "INFO" "Approval process started (PID: $approval_pid)"
        log "INFO" "Check the terminal for approval prompt or review logs in $LOGS_DIR"
    fi
}

# Main execution function
main() {
    local target_file=$1
    
    if [ $# -eq 0 ]; then
        echo "Usage: $0 <targets.txt>"
        echo "Example: $0 targets.txt"
        exit 1
    fi
    
    if [ ! -f "$target_file" ]; then
        log "ERROR" "Target file not found: $target_file"
        exit 1
    fi
    
    # Initialize
    mkdir -p "$RESULTS_DIR" "$LOGS_DIR"
    
    log "INFO" "🚀 Starting Bug Bounty Automation Framework"
    log "INFO" "Target file: $target_file"
    
    # Check tools
    check_tools
    
    # Process each target
    while IFS= read -r target; do
        if [[ -n "$target" && ! "$target" =~ ^[[:space:]]*# ]]; then
            log "INFO" "🎯 Processing target: $target"
            
            # Create session
            create_session "$target"
            
            # Run the hunting pipeline
            if run_recon "$target"; then
                if check_alive; then
                    if crawl_urls; then
                        run_vulnerability_scans
                        if analyze_results; then
                            generate_report "$target"
                            send_email_notification "$target"
                        fi
                    fi
                fi
            fi
            
            log "SUCCESS" "✅ Completed processing: $target"
            echo "----------------------------------------"
        fi
    done < "$target_file"
    
    log "SUCCESS" "🎉 Bug bounty automation completed!"
    log "INFO" "Latest results: $(cat "$RESULTS_DIR/latest_session.txt" 2>/dev/null || echo "No session found")"
}

# Run main function
main "$@"
