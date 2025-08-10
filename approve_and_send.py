#!/usr/bin/env python3

"""
Bug Bounty Email Approval System
Waits for user approval before sending vulnerability reports to developers
"""

import json
import smtplib
import sys
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def load_email_config(config_path):
    """Load email configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Email config not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in email config: {config_path}")
        sys.exit(1)

def create_developer_email_content(target, vuln_count, vulnerabilities):
    """Create professional email content for developers"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; background: #f8f9fa; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #e74c3c, #2c3e50); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; font-weight: 300; }}
            .content {{ padding: 30px; }}
            .vulnerability-section {{ margin: 20px 0; padding: 20px; border-left: 4px solid #e74c3c; background: #fff5f5; border-radius: 0 8px 8px 0; }}
            .vulnerability-item {{ background: #2c3e50; color: #ecf0f1; padding: 10px; margin: 10px 0; border-radius: 6px; font-family: monospace; font-size: 12px; overflow-x: auto; }}
            .info-box {{ background: #e8f4f8; border: 1px solid #3498db; border-radius: 8px; padding: 20px; margin: 20px 0; }}
            .footer {{ background: #2c3e50; color: white; text-align: center; padding: 20px; font-size: 12px; }}
            .severity-high {{ color: #e74c3c; font-weight: bold; }}
            .severity-medium {{ color: #f39c12; font-weight: bold; }}
            .severity-low {{ color: #27ae60; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ Security Vulnerability Report</h1>
                <div style="font-size: 18px; margin-top: 10px;">{target}</div>
                <div style="margin-top: 15px;">
                    <span style="background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px;">
                        {vuln_count} Vulnerabilities Identified
                    </span>
                </div>
            </div>
            
            <div class="content">
                <div class="info-box">
                    <h2>🔍 Executive Summary</h2>
                    <p>Our automated security assessment of <strong>{target}</strong> has identified <strong>{vuln_count}</strong> potential security vulnerabilities that require your attention.</p>
                    <p><strong>Assessment Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Scope:</strong> Automated vulnerability discovery and analysis</p>
                </div>
                
                <h2>🚨 Vulnerability Findings</h2>
    """
    
    # Add vulnerability details
    vuln_types = ['nuclei', 'xss', 'sqli']
    vuln_labels = {
        'nuclei': '🔍 Security Misconfiguration & Template-based Vulnerabilities',
        'xss': '⚡ Cross-Site Scripting (XSS) Vulnerabilities',
        'sqli': '💉 SQL Injection Vulnerabilities'
    }
    
    for vuln_type in vuln_types:
        if vulnerabilities.get(vuln_type):
            html_content += f'''
            <div class="vulnerability-section">
                <h3>{vuln_labels[vuln_type]}</h3>
                <p><strong>Risk Level:</strong> <span class="severity-high">HIGH</span></p>
                <p><strong>Affected Components:</strong></p>
            '''
            
            for vuln in vulnerabilities[vuln_type][:5]:  # Show max 5 per type
                html_content += f'<div class="vulnerability-item">{vuln.strip()}</div>'
            
            if len(vulnerabilities[vuln_type]) > 5:
                html_content += f'<p><em>... and {len(vulnerabilities[vuln_type]) - 5} additional findings of this type</em></p>'
            
            html_content += '</div>'
    
    # Add recommendations
    html_content += f'''
                <div class="info-box">
                    <h3>✅ Recommended Actions</h3>
                    <ol>
                        <li><strong>Immediate Review:</strong> Prioritize manual verification of all identified vulnerabilities</li>
                        <li><strong>Impact Assessment:</strong> Evaluate the potential business impact of each finding</li>
                        <li><strong>Remediation Planning:</strong> Develop a timeline for addressing each vulnerability based on severity</li>
                        <li><strong>Security Testing:</strong> Implement regular automated security scanning in your CI/CD pipeline</li>
                        <li><strong>Code Review:</strong> Enhance secure coding practices and peer review processes</li>
                    </ol>
                </div>
                
                <div class="info-box">
                    <h3>📞 Next Steps</h3>
                    <p>We recommend scheduling a security discussion to:</p>
                    <ul>
                        <li>Review detailed findings and proof-of-concepts</li>
                        <li>Discuss remediation timelines and priorities</li>
                        <li>Establish ongoing security testing procedures</li>
                        <li>Address any questions about the identified vulnerabilities</li>
                    </ul>
                    <p><strong>Note:</strong> This assessment was conducted using automated tools. Manual verification and additional testing may be required to confirm exploitability and assess full impact.</p>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #856404;">⚠️ Responsible Disclosure</h3>
                    <p style="color: #856404;">This report is provided under responsible disclosure guidelines. Please:</p>
                    <ul style="color: #856404;">
                        <li>Treat this information as confidential</li>
                        <li>Address vulnerabilities in order of severity</li>
                        <li>Implement fixes within reasonable timeframes</li>
                        <li>Notify us when remediation is complete</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p>🤖 Generated by Automated Security Assessment Framework</p>
                <p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p style="font-size: 10px; opacity: 0.8;">This is an automated security assessment. Manual verification recommended.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def send_developer_email(config, target, vuln_count, vulnerabilities):
    """Send email to developer after approval"""
    try:
        # Create subject
        if int(vuln_count) <= 3:
            subject = f"🛡️ Security Assessment Report - {target} ({vuln_count} findings)"
        else:
            subject = f"🚨 URGENT: Security Assessment Report - {target} ({vuln_count} vulnerabilities)"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = config['sender_email']
        msg['To'] = config['developer_email']
        msg['Subject'] = subject
        
        # Add HTML content
        html_content = create_developer_email_content(target, vuln_count, vulnerabilities)
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.send_message(msg)
        
        return True
    
    except Exception as e:
        print(f"❌ Failed to send email to developer: {e}")
        return False

def read_vulnerability_data(session_dir):
    """Read vulnerability data from scan results"""
    vulnerabilities = {
        'nuclei': [],
        'xss': [],
        'sqli': []
    }
    
    try:
        # Read Nuclei results
        nuclei_file = os.path.join(session_dir, 'vulnerabilities', 'nuclei_results.txt')
        if os.path.exists(nuclei_file) and os.path.getsize(nuclei_file) > 0:
            with open(nuclei_file, 'r') as f:
                vulnerabilities['nuclei'] = [line.strip() for line in f.readlines() if line.strip()]
        
        # Read XSS results
        xss_file = os.path.join(session_dir, 'vulnerabilities', 'dalfox_results.txt')
        if os.path.exists(xss_file) and os.path.getsize(xss_file) > 0:
            with open(xss_file, 'r') as f:
                vulnerabilities['xss'] = [line.strip() for line in f.readlines() if line.strip()]
        
        # Check SQLi results
        sqlmap_dir = os.path.join(session_dir, 'vulnerabilities', 'sqlmap')
        if os.path.exists(sqlmap_dir):
            for root, dirs, files in os.walk(sqlmap_dir):
                for file in files:
                    if file.endswith('.csv') or file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        if os.path.getsize(file_path) > 0:
                            vulnerabilities['sqli'].append(f"SQL Injection potential in: {file}")
    
    except Exception as e:
        print(f"⚠️ Warning: Could not read vulnerability data: {e}")
    
    return vulnerabilities

def wait_for_approval():
    """Wait for user approval via command line"""
    print("\n" + "="*60)
    print("🔍 VULNERABILITY REPORT REVIEW REQUIRED")
    print("="*60)
    print("\nA vulnerability report has been generated and sent to you.")
    print("Please review the findings and decide whether to notify the developer.")
    print("\nIMPORTANT:")
    print("• Only send if you have permission to report vulnerabilities")
    print("• Ensure this follows responsible disclosure practices")
    print("• Verify findings are legitimate security issues")
    print("\n" + "="*60)
    
    while True:
        print("\nOptions:")
        print("  [Y] Yes - Send report to developer")
        print("  [N] No - Do not send report")
        print("  [S] Show summary again")
        
        choice = input("\nYour decision: ").strip().upper()
        
        if choice == 'Y':
            print("✅ Approved! Sending report to developer...")
            return True
        elif choice == 'N':
            print("❌ Report sending cancelled.")
            return False
        elif choice == 'S':
            continue
        else:
            print("❌ Invalid choice. Please enter Y, N, or S.")

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 approve_and_send.py <target> <vuln_count> <session_dir>")
        sys.exit(1)
    
    target = sys.argv[1]
    vuln_count = sys.argv[2]
    session_dir = sys.argv[3]
    
    # Only proceed if vulnerabilities were found
    if int(vuln_count) == 0:
        print("ℹ️ No vulnerabilities found. No developer notification needed.")
        sys.exit(0)
    
    # Load email configuration
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config', 'email_config.json')
    config = load_email_config(config_path)
    
    # Check if developer email is configured
    if config.get('developer_email', '') in ['', 'developer@target-company.com']:
        print("❌ Developer email not configured in config/email_config.json")
        print("Please set the 'developer_email' field to proceed.")
        sys.exit(1)
    
    # Read vulnerability data
    vulnerabilities = read_vulnerability_data(session_dir)
    
    # Show summary
    print(f"\n📊 VULNERABILITY SUMMARY for {target}:")
    print(f"Total vulnerabilities: {vuln_count}")
    if vulnerabilities['nuclei']:
        print(f"  • Nuclei findings: {len(vulnerabilities['nuclei'])}")
    if vulnerabilities['xss']:
        print(f"  • XSS vulnerabilities: {len(vulnerabilities['xss'])}")
    if vulnerabilities['sqli']:
        print(f"  • SQL injection potential: {len(vulnerabilities['sqli'])}")
    
    # Wait for approval
    if wait_for_approval():
        # Send email to developer
        print("📧 Sending vulnerability report to developer...")
        if send_developer_email(config, target, vuln_count, vulnerabilities):
            print(f"✅ Developer notification sent successfully to {config['developer_email']}")
            
            # Log the action
            log_file = os.path.join(script_dir, 'logs', 'developer_notifications.log')
            with open(log_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - Developer notified for {target} ({vuln_count} vulnerabilities)\n")
        else:
            print("❌ Failed to send developer notification")
            sys.exit(1)
    else:
        print("ℹ️ Developer notification cancelled by user.")

if __name__ == "__main__":
    main()
