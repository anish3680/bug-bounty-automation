#!/bin/bash

# Bug Bounty Automation Debug Monitor
# Real-time monitoring and debugging for scan processes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"
RESULTS_DIR="$SCRIPT_DIR/results"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

print_banner() {
    clear
    echo -e "${BLUE}"
    echo "┌─────────────────────────────────────────────────────────┐"
    echo "│              🔍 Bug Bounty Debug Monitor                │"
    echo "│            Real-time Scan Analysis & Debug             │"
    echo "└─────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

show_system_info() {
    echo -e "${CYAN}📋 System Information${NC}"
    echo "=============================="
    echo "Hostname: $(hostname)"
    echo "Date: $(date)"
    echo "User: $(whoami)"
    echo "Working Directory: $(pwd)"
    echo "Available Disk Space: $(df -h . | awk 'NR==2 {print $4}')"
    echo "Memory Usage: $(free -h | awk 'NR==2{print $3"/"$2}')"
    echo "CPU Load: $(uptime | awk -F'load average:' '{print $2}')"
    echo ""
}

check_tool_status() {
    echo -e "${YELLOW}🛠️  Tool Status Check${NC}"
    echo "========================"
    
    local tools=("subfinder" "amass" "assetfinder" "httpx" "katana" "gau" "hakrawler" "nuclei" "dalfox" "sqlmap")
    local missing_tools=()
    
    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            echo -e "✅ ${GREEN}$tool${NC} - Available"
        else
            echo -e "❌ ${RED}$tool${NC} - Missing"
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo ""
        echo -e "${RED}⚠️  Missing tools: ${missing_tools[*]}${NC}"
        echo "Run ./install.sh to install missing tools"
    fi
    echo ""
}

show_active_processes() {
    echo -e "${PURPLE}⚡ Active Security Scan Processes${NC}"
    echo "====================================="
    
    # Check for running security tools
    local processes=$(ps aux | grep -E "(subfinder|amass|assetfinder|httpx|katana|gau|hakrawler|nuclei|dalfox|sqlmap)" | grep -v grep)
    
    if [ -n "$processes" ]; then
        echo "$processes" | while IFS= read -r line; do
            local tool=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}' | sed 's/.*\///g' | cut -d' ' -f1)
            local pid=$(echo "$line" | awk '{print $2}')
            local cpu=$(echo "$line" | awk '{print $3}')
            local mem=$(echo "$line" | awk '{print $4}')
            
            echo -e "🔄 ${YELLOW}$tool${NC} (PID: $pid) - CPU: $cpu% - Memory: $mem%"
        done
    else
        echo "No active security scanning processes found"
    fi
    echo ""
}

monitor_log_files() {
    echo -e "${GREEN}📋 Recent Log Activity${NC}"
    echo "========================"
    
    if [ -d "$LOGS_DIR" ]; then
        # Show recent errors
        echo -e "${RED}🚨 Recent Errors:${NC}"
        find "$LOGS_DIR" -name "*.log" -type f -exec grep -l "ERROR\|FAILED\|TIMEOUT" {} \; 2>/dev/null | head -5 | while read -r logfile; do
            echo "  📁 $(basename "$logfile")"
            grep -E "ERROR|FAILED|TIMEOUT" "$logfile" 2>/dev/null | tail -3 | sed 's/^/    /'
        done
        
        echo ""
        echo -e "${YELLOW}⚠️  Recent Warnings:${NC}"
        find "$LOGS_DIR" -name "*.log" -type f -exec grep -l "WARN\|WARNING" {} \; 2>/dev/null | head -5 | while read -r logfile; do
            echo "  📁 $(basename "$logfile")"
            grep -E "WARN|WARNING" "$logfile" 2>/dev/null | tail -2 | sed 's/^/    /'
        done
        
        echo ""
        echo -e "${BLUE}ℹ️  Latest Scan Activity:${NC}"
        if [ -f "$LOGS_DIR/hunt.log" ]; then
            tail -5 "$LOGS_DIR/hunt.log" | sed 's/^/  /'
        else
            echo "  No hunt.log found"
        fi
    else
        echo "No logs directory found"
    fi
    echo ""
}

show_recent_sessions() {
    echo -e "${CYAN}📊 Recent Scan Sessions${NC}"
    echo "=========================="
    
    if [ -d "$RESULTS_DIR" ]; then
        local sessions=$(find "$RESULTS_DIR" -maxdepth 1 -type d -name "*_*" | sort -r | head -5)
        
        if [ -n "$sessions" ]; then
            echo "$sessions" | while IFS= read -r session_dir; do
                local session_name=$(basename "$session_dir")
                local target=$(echo "$session_name" | cut -d'_' -f1)
                local timestamp=$(echo "$session_name" | cut -d'_' -f2-)
                
                # Format timestamp
                local formatted_time=$(echo "$timestamp" | sed 's/\(.\{8\}\)\(.\{6\}\)/\1 \2/')
                formatted_time=$(date -d "${formatted_time:0:8} ${formatted_time:9:2}:${formatted_time:11:2}:${formatted_time:13:2}" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "$timestamp")
                
                # Check results
                local subdomains=0
                local alive=0
                local urls=0
                local vulns=0
                
                [ -f "$session_dir/recon/all_subdomains.txt" ] && subdomains=$(wc -l < "$session_dir/recon/all_subdomains.txt" 2>/dev/null || echo "0")
                [ -f "$session_dir/alive/alive_hosts.txt" ] && alive=$(wc -l < "$session_dir/alive/alive_hosts.txt" 2>/dev/null || echo "0")
                [ -f "$session_dir/urls/all_urls.txt" ] && urls=$(wc -l < "$session_dir/urls/all_urls.txt" 2>/dev/null || echo "0")
                [ -f "$session_dir/reports/vuln_count.txt" ] && vulns=$(cat "$session_dir/reports/vuln_count.txt" 2>/dev/null || echo "0")
                
                echo -e "🎯 ${YELLOW}$target${NC} - $formatted_time"
                echo "   Subdomains: $subdomains | Alive: $alive | URLs: $urls | Vulns: $vulns"
                echo ""
            done
        else
            echo "No recent sessions found"
        fi
    else
        echo "No results directory found"
    fi
}

show_disk_usage() {
    echo -e "${GREEN}💾 Disk Usage Analysis${NC}"
    echo "======================="
    
    echo "Framework Directory Usage:"
    du -sh "$SCRIPT_DIR" 2>/dev/null || echo "Cannot calculate size"
    
    if [ -d "$RESULTS_DIR" ]; then
        echo ""
        echo "Largest Result Sessions:"
        find "$RESULTS_DIR" -maxdepth 1 -type d -name "*_*" -exec du -sh {} \; 2>/dev/null | sort -hr | head -5
    fi
    
    if [ -d "$LOGS_DIR" ]; then
        echo ""
        echo "Log Files Size:"
        find "$LOGS_DIR" -name "*.log" -type f -exec du -sh {} \; 2>/dev/null | sort -hr | head -5
    fi
    echo ""
}

monitor_network_activity() {
    echo -e "${PURPLE}🌐 Network Activity${NC}"
    echo "===================="
    
    # Check for active network connections related to security tools
    local connections=$(netstat -tuln 2>/dev/null | grep -E ":80|:443|:8080|:8443" | wc -l)
    echo "Active web connections: $connections"
    
    # Check DNS queries (if available)
    if command -v ss >/dev/null 2>&1; then
        local dns_connections=$(ss -tuln | grep ":53" | wc -l)
        echo "DNS connections: $dns_connections"
    fi
    
    # Check if we can reach common security APIs
    echo ""
    echo "API Connectivity Tests:"
    
    local apis=("virustotal.com" "api.shodan.io" "crt.sh")
    for api in "${apis[@]}"; do
        if ping -c 1 -W 2 "$api" >/dev/null 2>&1; then
            echo -e "  ✅ ${GREEN}$api${NC} - Reachable"
        else
            echo -e "  ❌ ${RED}$api${NC} - Unreachable"
        fi
    done
    echo ""
}

tail_logs_realtime() {
    echo -e "${YELLOW}📺 Real-time Log Monitoring${NC}"
    echo "============================"
    echo "Monitoring logs in real-time... (Press Ctrl+C to stop)"
    echo ""
    
    # Create a named pipe for log aggregation
    local temp_pipe=$(mktemp -u)
    mkfifo "$temp_pipe"
    
    # Start tailing all log files
    find "$LOGS_DIR" -name "*.log" -type f -exec tail -f {} \; > "$temp_pipe" &
    local tail_pid=$!
    
    # Monitor the aggregated logs with colors
    while IFS= read -r line; do
        case "$line" in
            *ERROR*|*FAILED*)
                echo -e "${RED}$line${NC}"
                ;;
            *WARN*|*WARNING*)
                echo -e "${YELLOW}$line${NC}"
                ;;
            *SUCCESS*|*FOUND*)
                echo -e "${GREEN}$line${NC}"
                ;;
            *VULN*|*VULNERABILITY*)
                echo -e "${PURPLE}$line${NC}"
                ;;
            *)
                echo "$line"
                ;;
        esac
    done < "$temp_pipe"
    
    # Cleanup
    kill $tail_pid 2>/dev/null || true
    rm -f "$temp_pipe"
}

interactive_menu() {
    while true; do
        print_banner
        show_system_info
        
        echo -e "${BLUE}🎛️  Debug Monitor Menu${NC}"
        echo "======================"
        echo "1. Check Tool Status"
        echo "2. Show Active Processes"
        echo "3. Monitor Log Activity"
        echo "4. Show Recent Sessions"
        echo "5. Disk Usage Analysis"
        echo "6. Network Activity"
        echo "7. Real-time Log Monitor"
        echo "8. Full System Report"
        echo "9. Clean Old Logs"
        echo "0. Exit"
        echo ""
        
        read -p "Select option (0-9): " choice
        
        case $choice in
            1)
                echo ""
                check_tool_status
                read -p "Press Enter to continue..."
                ;;
            2)
                echo ""
                show_active_processes
                read -p "Press Enter to continue..."
                ;;
            3)
                echo ""
                monitor_log_files
                read -p "Press Enter to continue..."
                ;;
            4)
                echo ""
                show_recent_sessions
                read -p "Press Enter to continue..."
                ;;
            5)
                echo ""
                show_disk_usage
                read -p "Press Enter to continue..."
                ;;
            6)
                echo ""
                monitor_network_activity
                read -p "Press Enter to continue..."
                ;;
            7)
                echo ""
                tail_logs_realtime
                ;;
            8)
                echo ""
                echo -e "${GREEN}📊 Full System Report${NC}"
                echo "======================"
                check_tool_status
                show_active_processes
                monitor_log_files
                show_recent_sessions
                show_disk_usage
                monitor_network_activity
                read -p "Press Enter to continue..."
                ;;
            9)
                echo ""
                echo -e "${YELLOW}🧹 Cleaning Old Logs${NC}"
                echo "===================="
                
                # Clean logs older than 30 days
                find "$LOGS_DIR" -name "*.log" -type f -mtime +30 -exec rm {} \; 2>/dev/null || true
                
                # Clean old result sessions (keep last 10)
                if [ -d "$RESULTS_DIR" ]; then
                    find "$RESULTS_DIR" -maxdepth 1 -type d -name "*_*" | sort -r | tail -n +11 | xargs rm -rf 2>/dev/null || true
                fi
                
                echo "✅ Cleanup completed"
                read -p "Press Enter to continue..."
                ;;
            0)
                echo -e "${GREEN}👋 Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid option${NC}"
                sleep 1
                ;;
        esac
    done
}

# Main execution
main() {
    if [ "$1" = "--monitor" ]; then
        # Direct log monitoring
        tail_logs_realtime
    elif [ "$1" = "--report" ]; then
        # Generate and display full report
        print_banner
        check_tool_status
        show_active_processes
        monitor_log_files
        show_recent_sessions
        show_disk_usage
        monitor_network_activity
    else
        # Interactive menu
        interactive_menu
    fi
}

# Run main function
main "$@"
