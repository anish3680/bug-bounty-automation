#!/usr/bin/env python3

"""
Bug Bounty Automation Email System
Sends detailed email notifications about discovered vulnerabilities
"""

import json
import smtplib
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
import subprocess

def load_email_config(config_path):
    """Load email configuration from JSON file with graceful fallback"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Check if email is properly configured
        if not config.get('sender_email') or not config.get('sender_password'):
            print("⚠️  Email configuration incomplete - reports will be saved locally only")
            print("💡 To enable email reports, configure config/email_config.json")
            return None
            
        return config
    except FileNotFoundError:
        print("⚠️  Email config not found - reports will be saved locally only")
        print("💡 Run 'python3 bug_bounty_scanner.py config' to set up email")
        return None
    except json.JSONDecodeError:
        print(f"⚠️  Invalid JSON in email config: {config_path}")
        print("💡 Please check your email configuration syntax")
        return None

def read_vulnerability_summary(session_dir):
    """Read and summarize vulnerability findings"""
    vuln_summary = {
        'nuclei': [],
        'xss': [],
        'sqli': [],
        'total_subdomains': 0,
        'alive_hosts': 0,
        'total_urls': 0
    }
    
    try:
        # Count subdomains
        subdomains_file = os.path.join(session_dir, 'recon', 'all_subdomains.txt')
        if os.path.exists(subdomains_file):
            with open(subdomains_file, 'r') as f:
                vuln_summary['total_subdomains'] = len(f.readlines())
        
        # Count alive hosts
        alive_file = os.path.join(session_dir, 'alive', 'alive_hosts.txt')
        if os.path.exists(alive_file):
            with open(alive_file, 'r') as f:
                vuln_summary['alive_hosts'] = len(f.readlines())
        
        # Count URLs
        urls_file = os.path.join(session_dir, 'urls', 'all_urls.txt')
        if os.path.exists(urls_file):
            with open(urls_file, 'r') as f:
                vuln_summary['total_urls'] = len(f.readlines())
        
        # Read Nuclei results
        nuclei_file = os.path.join(session_dir, 'vulnerabilities', 'nuclei_results.txt')
        if os.path.exists(nuclei_file) and os.path.getsize(nuclei_file) > 0:
            with open(nuclei_file, 'r') as f:
                vuln_summary['nuclei'] = f.readlines()[:10]  # Limit to first 10
        
        # Read XSS results
        xss_file = os.path.join(session_dir, 'vulnerabilities', 'dalfox_results.txt')
        if os.path.exists(xss_file) and os.path.getsize(xss_file) > 0:
            with open(xss_file, 'r') as f:
                vuln_summary['xss'] = f.readlines()[:5]  # Limit to first 5
        
        # Check SQLi results
        sqlmap_dir = os.path.join(session_dir, 'vulnerabilities', 'sqlmap')
        if os.path.exists(sqlmap_dir):
            for root, dirs, files in os.walk(sqlmap_dir):
                for file in files:
                    if file.endswith('.csv') or file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        if os.path.getsize(file_path) > 0:
                            vuln_summary['sqli'].append(f"Potential SQLi in: {file}")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not read vulnerability summary: {e}")
    
    return vuln_summary

def create_email_content(target, vuln_count, vuln_summary, session_dir):
    """Create HTML email content"""
    
    # Determine severity and emoji
    if int(vuln_count) == 0:
        severity = "🟢 CLEAN"
        priority = "LOW"
        color = "#27ae60"
    elif int(vuln_count) <= 3:
        severity = "🟡 MEDIUM"
        priority = "MEDIUM"
        color = "#f39c12"
    else:
        severity = "🔴 HIGH"
        priority = "HIGH"
        color = "#e74c3c"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; background: #f8f9fa; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, {color}, #2c3e50); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; font-weight: 300; }}
            .header .target {{ font-size: 20px; margin-top: 10px; opacity: 0.9; }}
            .stats {{ display: flex; justify-content: space-around; padding: 20px; background: #f8f9fa; }}
            .stat {{ text-align: center; }}
            .stat-number {{ font-size: 24px; font-weight: bold; color: {color}; }}
            .stat-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
            .content {{ padding: 30px; }}
            .vulnerability-section {{ margin: 20px 0; padding: 20px; border-left: 4px solid {color}; background: #fff5f5; border-radius: 0 8px 8px 0; }}
            .vulnerability-item {{ background: #2c3e50; color: #ecf0f1; padding: 10px; margin: 10px 0; border-radius: 6px; font-family: monospace; font-size: 12px; overflow-x: auto; }}
            .info-box {{ background: #e8f4f8; border: 1px solid #3498db; border-radius: 8px; padding: 20px; margin: 20px 0; }}
            .footer {{ background: #2c3e50; color: white; text-align: center; padding: 20px; font-size: 12px; }}
            .priority {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; background: {color}; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Bug Bounty Scan Complete</h1>
                <div class="target">{target}</div>
                <div style="margin-top: 15px;">
                    <span class="priority">{severity} - {priority} PRIORITY</span>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{vuln_summary['total_subdomains']}</div>
                    <div class="stat-label">Subdomains</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{vuln_summary['alive_hosts']}</div>
                    <div class="stat-label">Alive Hosts</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{vuln_summary['total_urls']}</div>
                    <div class="stat-label">URLs Found</div>
                </div>
                <div class="stat">
                    <div class="stat-number" style="color: #e74c3c;">{vuln_count}</div>
                    <div class="stat-label">Vulnerabilities</div>
                </div>
            </div>
            
            <div class="content">
                <h2>📊 Scan Summary</h2>
                <p><strong>Target:</strong> {target}<br>
                <strong>Scan Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                <strong>Session:</strong> {os.path.basename(session_dir)}<br>
                <strong>Status:</strong> {severity}</p>
    """
    
    # Add vulnerability details if found
    if int(vuln_count) > 0:
        html_content += '<h2>🚨 Vulnerability Findings</h2>'
        
        # Nuclei vulnerabilities
        if vuln_summary['nuclei']:
            html_content += '''
            <div class="vulnerability-section">
                <h3>🔍 Nuclei Scan Results</h3>
                <p>The following vulnerabilities were detected by Nuclei scanner:</p>
            '''
            for vuln in vuln_summary['nuclei'][:5]:  # Show max 5
                html_content += f'<div class="vulnerability-item">{vuln.strip()}</div>'
            if len(vuln_summary['nuclei']) > 5:
                html_content += f'<p><em>... and {len(vuln_summary["nuclei"]) - 5} more findings</em></p>'
            html_content += '</div>'
        
        # XSS vulnerabilities
        if vuln_summary['xss']:
            html_content += '''
            <div class="vulnerability-section">
                <h3>⚡ XSS Vulnerabilities</h3>
                <p>Cross-Site Scripting vulnerabilities found by Dalfox:</p>
            '''
            for xss in vuln_summary['xss']:
                html_content += f'<div class="vulnerability-item">{xss.strip()}</div>'
            html_content += '</div>'
        
        # SQL injection
        if vuln_summary['sqli']:
            html_content += '''
            <div class="vulnerability-section">
                <h3>💉 SQL Injection Potential</h3>
                <p>Possible SQL injection vulnerabilities detected:</p>
            '''
            for sqli in vuln_summary['sqli']:
                html_content += f'<div class="vulnerability-item">{sqli}</div>'
            html_content += '</div>'
        
        # Next steps for vulnerabilities
        html_content += '''
        <div class="info-box">
            <h3>🎯 Immediate Actions Required</h3>
            <ol>
                <li><strong>Manual Verification:</strong> Verify each finding manually to confirm exploitability</li>
                <li><strong>Impact Assessment:</strong> Determine the business impact of each vulnerability</li>
                <li><strong>Documentation:</strong> Create detailed proof-of-concept for confirmed issues</li>
                <li><strong>Responsible Disclosure:</strong> Follow the program's disclosure policy</li>
                <li><strong>Timeline:</strong> Report critical findings within 24 hours</li>
            </ol>
        </div>
        '''
    else:
        # No vulnerabilities found
        html_content += '''
        <div style="text-align: center; padding: 40px; background: #e8f5e8; border-radius: 10px; margin: 20px 0;">
            <h2 style="color: #27ae60;">✅ No Critical Vulnerabilities Detected</h2>
            <p>The automated scan did not identify any immediate security issues.</p>
            <p style="color: #666; font-size: 14px;">Consider manual testing for business logic flaws, authentication bypasses, and privilege escalation issues.</p>
        </div>
        '''
    
    # Add technical details
    html_content += f'''
                <div class="info-box">
                    <h3>🔧 Technical Details</h3>
                    <p><strong>Tools Used:</strong> Subfinder, Amass, Assetfinder, HTTPx, Katana, GAU, Nuclei, Dalfox, SQLMap</p>
                    <p><strong>Scan Duration:</strong> Automated (approx. 30-60 minutes)</p>
                    <p><strong>Results Directory:</strong> <code>{session_dir}</code></p>
                    <p><strong>Report Location:</strong> Check the session directory for detailed HTML report</p>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #856404;">⚠️ Important Reminders</h3>
                    <ul style="color: #856404;">
                        <li>Always manually verify automated findings</li>
                        <li>Follow responsible disclosure practices</li>
                        <li>Document all testing activities</li>
                        <li>Respect scope and terms of the bug bounty program</li>
                        <li>Never test on production systems without explicit permission</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>🤖 Generated by Bug Bounty Automation Framework</p>
                <p>Scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html_content

def send_email(config, subject, html_content, report_file_path=None):
    """Send email notification"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = config['sender_email']
        msg['To'] = config['recipient_email']
        msg['Subject'] = subject
        
        # Add HTML content
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Attach HTML report if it exists
        if report_file_path and os.path.exists(report_file_path):
            with open(report_file_path, 'rb') as f:
                attachment = MIMEApplication(f.read(), _subtype='html')
                attachment.add_header('Content-Disposition', 'attachment', filename='bug_bounty_report.html')
                msg.attach(attachment)
        
        # Send email
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        return True
    
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def main():
    if len(sys.argv) != 5:
        print("Usage: python3 send_email.py <target> <vuln_count> <report_file> <session_dir>")
        sys.exit(1)
    
    target = sys.argv[1]
    vuln_count = sys.argv[2]
    report_file = sys.argv[3]
    session_dir = sys.argv[4]
    
    # Load email configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config', 'email_config.json')
    config = load_email_config(config_path)
    
    # Read vulnerability summary
    vuln_summary = read_vulnerability_summary(session_dir)
    
    # Create subject line
    if int(vuln_count) == 0:
        subject = f"✅ Bug Bounty Scan Complete - {target} (Clean)"
    elif int(vuln_count) <= 3:
        subject = f"🟡 Bug Bounty Alert - {target} ({vuln_count} findings)"
    else:
        subject = f"🚨 URGENT: Bug Bounty Alert - {target} ({vuln_count} vulnerabilities)"
    
    # Create email content
    html_content = create_email_content(target, vuln_count, vuln_summary, session_dir)
    
    # Always save report locally as backup
    backup_report = os.path.join(session_dir, 'email_report_backup.html')
    try:
        with open(backup_report, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 Report saved locally: {backup_report}")
    except Exception as e:
        print(f"⚠️  Warning: Could not save backup report: {e}")
    
    # Try to send email if configuration is available
    if config:
        print(f"📧 Sending email notification for {target}...")
        if send_email(config, subject, html_content, report_file):
            print(f"✅ Email sent successfully to {config['recipient_email']}")
            
            # Log the notification
            log_file = os.path.join(script_dir, 'logs', 'email_notifications.log')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - Email sent for {target} ({vuln_count} vulnerabilities)\n")
        else:
            print("⚠️  Email sending failed - report saved locally only")
            print(f"📂 Check: {backup_report}")
    else:
        print("📧 Email not configured - report available locally only")
        print(f"📂 Report saved to: {backup_report}")
        
    # Always exit successfully since we have local backup
    print(f"✅ Scan notification complete for {target}")

if __name__ == "__main__":
    main()
