#!/usr/bin/env python3
"""
AI-Enhanced Bug Bounty Report Sender
Sends professional vulnerability reports via email
Integrates with HackerOne API for automated submissions
"""

import smtplib
import os
import json
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import zipfile
import requests
from pathlib import Path

class AIReportSender:
    def __init__(self, config_file="config/email_config.json"):
        self.config = self.load_config(config_file)
        self.setup_email_config()
        
    def load_config(self, config_file):
        """Load email configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] Config file {config_file} not found!")
            print("Please run './start.sh --setup' to configure email settings")
            sys.exit(1)
    
    def setup_email_config(self):
        """Setup email configuration with defaults"""
        default_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "recipient_email": "",
            "developer_email": ""
        }
        
        # Merge with defaults
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def create_professional_email(self, report_data, report_dir):
        """Create professional HTML email with vulnerability summary"""
        target = report_data.get('target', 'Unknown Target')
        vuln_count = len(report_data.get('vulnerabilities', []))
        severity_score = report_data.get('severity_score', 0)
        scan_time = report_data.get('scan_time', datetime.now().isoformat())
        
        # Count vulnerabilities by severity
        severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        for vuln in report_data.get('vulnerabilities', []):
            severity = vuln.get('severity', 'Medium')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Generate email HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .severity-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .severity-card {{
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
        }}
        .critical {{ background-color: #dc3545; }}
        .high {{ background-color: #fd7e14; }}
        .medium {{ background-color: #ffc107; color: #000; }}
        .low {{ background-color: #28a745; }}
        .alert {{
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .alert-danger {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}
        .alert-warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }}
        .alert-success {{ background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            margin: 10px 5px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
        .ai-badge {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 AI-Enhanced Security Assessment Report</h1>
        <h2>{target}</h2>
        <p><span class="ai-badge">AI-Powered Analysis</span></p>
        <p>Scan completed: {scan_time[:19].replace('T', ' ')}</p>
    </div>
    
    <div class="summary-card">
        <h2>📊 Executive Summary</h2>
        <p><strong>Target Domain:</strong> {target}</p>
        <p><strong>Total Vulnerabilities Found:</strong> {vuln_count}</p>
        <p><strong>Overall Risk Score:</strong> {severity_score}/10</p>
        <p><strong>Assessment Status:</strong> Complete</p>
    </div>
    
    <h3>🚨 Vulnerability Breakdown</h3>
    <div class="severity-grid">
        <div class="severity-card critical">
            <h3>{severity_counts['Critical']}</h3>
            <p>Critical</p>
        </div>
        <div class="severity-card high">
            <h3>{severity_counts['High']}</h3>
            <p>High</p>
        </div>
        <div class="severity-card medium">
            <h3>{severity_counts['Medium']}</h3>
            <p>Medium</p>
        </div>
        <div class="severity-card low">
            <h3>{severity_counts['Low']}</h3>
            <p>Low</p>
        </div>
    </div>
"""
        
        # Add risk assessment alert
        if severity_score >= 8:
            html_content += '''
    <div class="alert alert-danger">
        <h4>🔴 HIGH RISK ASSESSMENT</h4>
        <p>Critical security vulnerabilities have been identified that require <strong>immediate attention</strong>. Please review the attached reports and take corrective action within 24-48 hours.</p>
    </div>'''
        elif severity_score >= 5:
            html_content += '''
    <div class="alert alert-warning">
        <h4>🟡 MEDIUM RISK ASSESSMENT</h4>
        <p>Multiple security vulnerabilities have been identified that should be addressed promptly. Please review the attached reports and prioritize remediation efforts.</p>
    </div>'''
        else:
            html_content += '''
    <div class="alert alert-success">
        <h4>🟢 LOW RISK ASSESSMENT</h4>
        <p>Few security issues were identified. Continue maintaining current security practices and address the findings when convenient.</p>
    </div>'''
        
        # Add vulnerability details
        html_content += '''
    <h3>🔍 Key Findings</h3>
    <div class="summary-card">
        <ul>'''
        
        for vuln in report_data.get('vulnerabilities', [])[:5]:  # Show top 5 vulnerabilities
            vuln_type = vuln.get('type', 'Unknown')
            severity = vuln.get('severity', 'Medium')
            url = vuln.get('url', 'N/A')[:80] + '...' if len(vuln.get('url', '')) > 80 else vuln.get('url', 'N/A')
            
            html_content += f'''
            <li><strong>{vuln_type}</strong> ({severity} severity) - {url}</li>'''
        
        if len(report_data.get('vulnerabilities', [])) > 5:
            remaining = len(report_data.get('vulnerabilities', [])) - 5
            html_content += f'''
            <li><em>...and {remaining} more vulnerabilities (see attached reports)</em></li>'''
        
        html_content += '''
        </ul>
    </div>
    
    <h3>📋 What's Included</h3>
    <div class="summary-card">
        <ul>
            <li>📄 <strong>Comprehensive HTML Report</strong> - Detailed analysis with AI insights</li>
            <li>📊 <strong>Executive Summary</strong> - High-level overview for management</li>
            <li>🎯 <strong>Individual HackerOne Reports</strong> - Ready for bug bounty submission</li>
            <li>📁 <strong>Raw Scan Data (JSON)</strong> - Technical details for developers</li>
        </ul>
    </div>
    
    <h3>⚡ Next Steps</h3>
    <div class="summary-card">
        <ol>
            <li><strong>Review Attached Reports:</strong> Examine all vulnerability details</li>
            <li><strong>Prioritize Fixes:</strong> Address Critical and High severity issues first</li>
            <li><strong>Implement Security Measures:</strong> Apply recommended mitigations</li>
            <li><strong>Submit to Bug Bounty:</strong> Use HackerOne templates if applicable</li>
            <li><strong>Schedule Regular Scans:</strong> Maintain ongoing security assessment</li>
        </ol>
    </div>
    
    <div style="text-align: center; margin: 30px 0;">
        <p><strong>Need help with remediation?</strong></p>
        <p>Each vulnerability report includes detailed remediation steps and AI-generated recommendations.</p>
    </div>
    
    <div class="footer">
        <p>🤖 This report was generated using AI-Enhanced Bug Bounty Scanner v2.0</p>
        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><strong>⚠️ CONFIDENTIAL:</strong> This security assessment is confidential and should only be shared with authorized personnel.</p>
    </div>
</body>
</html>'''
        
        return html_content
    
    def create_zip_archive(self, report_dir):
        """Create zip archive of all report files"""
        zip_path = f"{report_dir}/security_assessment_report.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files in the report directory
            for file_path in Path(report_dir).rglob('*'):
                if file_path.is_file() and file_path.name != 'security_assessment_report.zip':
                    arcname = file_path.relative_to(report_dir)
                    zipf.write(file_path, arcname)
        
        return zip_path
    
    def send_report_email(self, report_data, report_dir, recipient_email=None):
        """Send comprehensive report via email"""
        if not recipient_email:
            recipient_email = self.config.get('recipient_email')
        
        if not recipient_email:
            print("[ERROR] No recipient email configured!")
            return False
        
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['sender_email']
            msg['To'] = recipient_email
            
            target = report_data.get('target', 'Unknown Target')
            vuln_count = len(report_data.get('vulnerabilities', []))
            severity_score = report_data.get('severity_score', 0)
            
            # Set subject based on risk level
            if severity_score >= 8:
                priority = "🔴 CRITICAL"
            elif severity_score >= 5:
                priority = "🟡 HIGH"
            else:
                priority = "🟢 LOW"
            
            msg['Subject'] = f"{priority} Security Assessment Report - {target} ({vuln_count} vulnerabilities found)"
            
            # Create HTML content
            html_content = self.create_professional_email(report_data, report_dir)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Create zip archive and attach
            zip_path = self.create_zip_archive(report_dir)
            
            with open(zip_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= "security_report_{target}_{datetime.now().strftime("%Y%m%d")}.zip"'
            )
            msg.attach(part)
            
            # Send email
            print(f"[EMAIL] Sending report to {recipient_email}...")
            
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['sender_email'], self.config['sender_password'])
            
            text = msg.as_string()
            server.sendmail(self.config['sender_email'], recipient_email, text)
            server.quit()
            
            print(f"[EMAIL] ✅ Report sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"[EMAIL] ❌ Failed to send email: {e}")
            return False
    
    def submit_to_hackerone(self, vulnerability_reports, program_handle):
        """Submit vulnerability reports to HackerOne (requires API token)"""
        # This is a placeholder for HackerOne API integration
        # You would need to set up API credentials and implement the API calls
        
        print("[HACKERONE] HackerOne integration not yet configured")
        print("Individual HackerOne report templates have been generated in the reports folder")
        print("You can manually copy and submit these reports to HackerOne programs")
        
        # Save submission instructions
        instructions = f"""
# HackerOne Submission Instructions

## Generated Reports
The following HackerOne-ready reports have been generated:

"""
        for i, report_file in enumerate(vulnerability_reports):
            if os.path.exists(report_file):
                instructions += f"- {os.path.basename(report_file)}\n"
        
        instructions += f"""
## How to Submit

1. Visit the target's HackerOne program page
2. Click "Submit Report" 
3. Copy the content from each report file above
4. Fill in any additional details requested by the program
5. Submit the report

## Tips for Successful Submissions

- Always follow the program's scope and rules
- Provide clear reproduction steps
- Include proof-of-concept code when appropriate
- Be respectful and professional in communication
- Wait for program response before public disclosure

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        return instructions

def main():
    """Main function for sending reports"""
    if len(sys.argv) < 2:
        print("Usage: python3 ai_report_sender.py <report_directory> [email]")
        print("Example: python3 ai_report_sender.py results/example.com_20250810_123456 user@example.com")
        sys.exit(1)
    
    report_dir = sys.argv[1]
    custom_email = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(report_dir):
        print(f"[ERROR] Report directory {report_dir} not found!")
        sys.exit(1)
    
    # Load scan results
    results_file = os.path.join(report_dir, 'scan_results.json')
    if not os.path.exists(results_file):
        print(f"[ERROR] Scan results file not found in {report_dir}")
        sys.exit(1)
    
    try:
        with open(results_file, 'r') as f:
            report_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load scan results: {e}")
        sys.exit(1)
    
    # Initialize report sender
    sender = AIReportSender()
    
    # Send email report
    success = sender.send_report_email(report_data, report_dir, custom_email)
    
    if success:
        print(f"[SUCCESS] 🎉 Report sent successfully!")
        print(f"[INFO] Report includes:")
        print(f"  📄 Comprehensive HTML report")
        print(f"  📊 Executive summary")
        print(f"  🎯 HackerOne-ready vulnerability reports")
        print(f"  📁 Raw scan data")
        
        # Generate HackerOne submission instructions
        hackerone_reports = [
            os.path.join(report_dir, f) for f in os.listdir(report_dir) 
            if f.startswith('hackerone_report_') and f.endswith('.md')
        ]
        
        if hackerone_reports:
            instructions = sender.submit_to_hackerone(hackerone_reports, "target_program")
            instructions_file = os.path.join(report_dir, 'hackerone_submission_guide.md')
            with open(instructions_file, 'w') as f:
                f.write(instructions)
            print(f"[INFO] 🎯 HackerOne submission guide created: {instructions_file}")
    else:
        print("[ERROR] ❌ Failed to send report")
        sys.exit(1)

if __name__ == "__main__":
    main()
