#!/usr/bin/env python3
"""
Advanced AI-Powered Bug Bounty Scanner v3.0
Integrates multiple free AI APIs for vulnerability analysis
Generates professional HackerOne reports with enhanced error handling
"""

import requests
import json
import asyncio
import aiohttp
import subprocess
import os
import sys
from datetime import datetime
import re
from urllib.parse import urlparse, urljoin
import time
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import logging
from pathlib import Path

# Import our enhanced modules
from tool_manager import ToolManager
from config_manager import ConfigManager
from ai_manager import AIManager
from updater import UpdateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIVulnScanner:
    def __init__(self):
        logger.info("🚀 Initializing Advanced AI-Powered Bug Bounty Scanner v3.0")
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.tool_manager = ToolManager()
        self.ai_manager = AIManager()
        self.update_manager = UpdateManager()
        
        # Load configurations
        self.config = {
            'tools': self.config_manager.load_config('tools'),
            'scanner': self.config_manager.load_config('scanner'),
            'ai': self.config_manager.load_config('ai'),
            'email': self.config_manager.load_config('email')
        }
        
        # Initialize session with enhanced headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Bug Bounty Scanner v3.0 (Professional Security Research)'
        })
        
        # Enhanced vulnerability patterns
        self.vuln_patterns = {
            'xss': [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'on\w+\s*=',
                r'alert\(',
                r'confirm\(',
                r'prompt\(',
                r'<svg.*?onload.*?>',
                r'<img.*?onerror.*?>'
            ],
            'sqli': [
                r'error.*sql',
                r'mysql_fetch',
                r'ORA-[0-9]+',
                r'Microsoft.*ODBC.*SQL',
                r'PostgreSQL.*ERROR',
                r'Warning.*mysql_',
                r'SQL syntax.*error',
                r'MariaDB server version',
                r'sqlite3.OperationalError'
            ],
            'lfi': [
                r'/etc/passwd',
                r'\.\./',
                r'%2e%2e%2f',
                r'%252e%252e%252f',
                r'root:x:0:0:',
                r'daemon:x:1:1:'
            ],
            'rfi': [
                r'http://.*\?',
                r'ftp://.*\?',
                r'php://filter',
                r'data://',
                r'expect://'
            ],
            'ssrf': [
                r'localhost',
                r'127\.0\.0\.1',
                r'169\.254\.',
                r'10\.\d+\.\d+\.\d+',
                r'192\.168\.',
                r'172\.(1[6-9]|2[0-9]|3[0-1])\.'
            ],
            'command_injection': [
                r'uid=\d+.*gid=\d+',
                r'/bin/bash',
                r'/bin/sh',
                r'sh-\d+\.\d+\$',
                r'root@.*:/#'
            ],
            'path_traversal': [
                r'\.\./',
                r'\.\.\\',
                r'%2e%2e%2f',
                r'%2e%2e%5c',
                r'..%2f',
                r'..%5c'
            ]
        }
        
        # Initialize results structure
        self.results = {
            'target': '',
            'scan_time': '',
            'scan_id': '',
            'vulnerabilities': [],
            'ai_analysis': [],
            'recommendations': [],
            'severity_score': 0,
            'subdomains': [],
            'endpoints': [],
            'technologies': [],
            'statistics': {
                'total_requests': 0,
                'vulnerabilities_found': 0,
                'false_positives_filtered': 0,
                'scan_duration': 0
            },
            'system_info': {
                'scanner_version': '3.0',
                'tools_status': {},
                'ai_models_used': []
            }
        }

    async def setup_ai_models(self):
        """Setup and test AI models"""
        print("[AI] Setting up AI analysis engines...")
        
        # Try to start Ollama if not running
        try:
            subprocess.run(['ollama', 'serve'], timeout=5, capture_output=True)
        except:
            pass
            
        # Test Ollama connection
        try:
            response = requests.post(self.ai_endpoints['ollama'], 
                                   json={'model': 'llama2', 'prompt': 'test'}, 
                                   timeout=5)
            print("[AI] ✅ Ollama available")
        except:
            print("[AI] ❌ Ollama not available")
            
        # Setup HuggingFace models (no API key needed for inference API)
        self.hf_models = [
            'microsoft/DialoGPT-medium',
            'microsoft/CodeBERT-base',
            'facebook/bart-large',
        ]

    async def ai_analyze_vulnerability(self, vuln_data: Dict) -> Dict:
        """Use AI to analyze vulnerability details"""
        prompt = f"""
        Analyze this potential security vulnerability:
        
        Type: {vuln_data.get('type', 'Unknown')}
        URL: {vuln_data.get('url', 'N/A')}
        Details: {vuln_data.get('details', 'N/A')}
        Evidence: {vuln_data.get('evidence', 'N/A')}
        
        Provide:
        1. Severity assessment (Critical/High/Medium/Low)
        2. Exploitability analysis
        3. Business impact
        4. Remediation steps
        5. HackerOne report template
        
        Format as JSON with these fields:
        {{"severity": "", "exploitability": "", "impact": "", "remediation": "", "hackerone_template": ""}}
        """
        
        ai_response = await self.query_ai_models(prompt)
        
        try:
            # Parse AI response and structure it
            analysis = {
                'ai_model': ai_response.get('model', 'mixed'),
                'severity': self.extract_severity(ai_response.get('content', '')),
                'exploitability': self.extract_exploitability(ai_response.get('content', '')),
                'impact': self.extract_impact(ai_response.get('content', '')),
                'remediation': self.extract_remediation(ai_response.get('content', '')),
                'hackerone_template': self.generate_hackerone_template(vuln_data, ai_response)
            }
            return analysis
        except Exception as e:
            print(f"[AI] Error analyzing vulnerability: {e}")
            return {'error': str(e)}

    async def query_ai_models(self, prompt: str) -> Dict:
        """Query multiple AI models and get best response"""
        responses = []
        
        # Try Ollama first (local model)
        try:
            ollama_response = await self.query_ollama(prompt)
            if ollama_response:
                responses.append(ollama_response)
        except Exception as e:
            print(f"[AI] Ollama error: {e}")
        
        # Try HuggingFace models
        try:
            hf_response = await self.query_huggingface(prompt)
            if hf_response:
                responses.append(hf_response)
        except Exception as e:
            print(f"[AI] HuggingFace error: {e}")
        
        # Return best response or combined analysis
        if responses:
            return self.combine_ai_responses(responses)
        else:
            return {'content': 'AI analysis unavailable', 'model': 'fallback'}

    async def query_ollama(self, prompt: str) -> Dict:
        """Query local Ollama model"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'model': 'llama2',
                    'prompt': prompt,
                    'stream': False
                }
                async with session.post(self.ai_endpoints['ollama'], 
                                      json=payload, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {'content': data.get('response', ''), 'model': 'ollama-llama2'}
        except Exception as e:
            print(f"[AI] Ollama query failed: {e}")
        return None

    async def query_huggingface(self, prompt: str) -> Dict:
        """Query HuggingFace inference API (free tier)"""
        try:
            # Use a model suitable for text generation
            model = "microsoft/DialoGPT-medium"
            url = f"https://api-inference.huggingface.co/models/{model}"
            
            async with aiohttp.ClientSession() as session:
                payload = {"inputs": prompt}
                async with session.post(url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and data:
                            return {'content': data[0].get('generated_text', ''), 'model': 'huggingface'}
        except Exception as e:
            print(f"[AI] HuggingFace query failed: {e}")
        return None

    def combine_ai_responses(self, responses: List[Dict]) -> Dict:
        """Combine multiple AI responses for better analysis"""
        combined_content = ""
        models_used = []
        
        for resp in responses:
            combined_content += f"\n--- {resp['model']} ---\n{resp['content']}\n"
            models_used.append(resp['model'])
        
        return {
            'content': combined_content,
            'model': f"combined-{'-'.join(models_used)}"
        }

    def extract_severity(self, content: str) -> str:
        """Extract severity from AI response"""
        content_lower = content.lower()
        if 'critical' in content_lower:
            return 'Critical'
        elif 'high' in content_lower:
            return 'High'
        elif 'medium' in content_lower:
            return 'Medium'
        elif 'low' in content_lower:
            return 'Low'
        else:
            return 'Medium'  # Default

    def extract_exploitability(self, content: str) -> str:
        """Extract exploitability assessment"""
        # Simple keyword-based extraction (can be improved with NLP)
        if 'easily exploitable' in content.lower() or 'trivial' in content.lower():
            return 'High'
        elif 'difficult' in content.lower() or 'requires' in content.lower():
            return 'Low'
        else:
            return 'Medium'

    def extract_impact(self, content: str) -> str:
        """Extract business impact assessment"""
        impact_keywords = {
            'data breach': 'High',
            'unauthorized access': 'High',
            'information disclosure': 'Medium',
            'denial of service': 'Medium',
            'defacement': 'Low'
        }
        
        content_lower = content.lower()
        for keyword, impact in impact_keywords.items():
            if keyword in content_lower:
                return impact
        return 'Medium'

    def extract_remediation(self, content: str) -> str:
        """Extract remediation steps from AI response"""
        lines = content.split('\n')
        remediation_lines = []
        capture = False
        
        for line in lines:
            if 'remediation' in line.lower() or 'fix' in line.lower() or 'solution' in line.lower():
                capture = True
            elif capture and line.strip():
                remediation_lines.append(line.strip())
            elif capture and not line.strip():
                break
                
        return '\n'.join(remediation_lines) if remediation_lines else 'Apply security best practices'

    def generate_hackerone_template(self, vuln_data: Dict, ai_response: Dict) -> str:
        """Generate professional HackerOne report template"""
        template = f"""
# {vuln_data.get('type', 'Security Vulnerability').title()} in {vuln_data.get('url', 'Target Application')}

## Summary
A {vuln_data.get('type', 'security vulnerability')} was discovered in the target application that could potentially be exploited by malicious actors.

## Description
{ai_response.get('content', 'Detailed vulnerability analysis')[:500]}...

## Steps to Reproduce
1. Navigate to: {vuln_data.get('url', 'target URL')}
2. {vuln_data.get('steps', 'Perform the following steps to reproduce the vulnerability')}
3. Observe the security issue

## Proof of Concept
```
{vuln_data.get('evidence', 'Evidence details')}
```

## Impact
{self.extract_impact(ai_response.get('content', ''))}

## Remediation
{self.extract_remediation(ai_response.get('content', ''))}

## References
- OWASP Top 10
- CWE Classification
- Security Best Practices

## Timeline
- Discovery Date: {datetime.now().strftime('%Y-%m-%d')}
- Reported Date: {datetime.now().strftime('%Y-%m-%d')}

---
*Report generated by AI-Enhanced Bug Bounty Scanner v2.0*
        """
        return template.strip()

    async def deep_scan_target(self, target: str):
        """Perform comprehensive security scan"""
        self.results['target'] = target
        self.results['scan_time'] = datetime.now().isoformat()
        
        print(f"[SCAN] Starting deep scan of {target}")
        
        # 1. Subdomain enumeration with AI-powered analysis
        await self.enumerate_subdomains(target)
        
        # 2. Technology detection
        await self.detect_technologies(target)
        
        # 3. Endpoint discovery
        await self.discover_endpoints(target)
        
        # 4. Vulnerability scanning
        await self.scan_vulnerabilities(target)
        
        # 5. AI-powered analysis of findings
        await self.ai_analyze_findings()
        
        # 6. Generate professional report
        await self.generate_report()
        
        return self.results

    async def enumerate_subdomains(self, target: str):
        """Enhanced subdomain enumeration"""
        print("[SCAN] Enumerating subdomains...")
        
        # Use multiple tools
        tools = [
            f'subfinder -d {target} -silent',
            f'assetfinder -subs-only {target}',
            f'amass enum -passive -d {target}',
        ]
        
        subdomains = set()
        for tool in tools:
            try:
                result = subprocess.run(tool.split(), capture_output=True, text=True, timeout=300)
                if result.stdout:
                    subdomains.update(result.stdout.strip().split('\n'))
            except Exception as e:
                print(f"[SCAN] Tool failed: {tool} - {e}")
        
        # AI analysis of subdomain patterns
        subdomain_list = list(subdomains)
        if subdomain_list:
            ai_analysis = await self.ai_analyze_subdomains(subdomain_list)
            self.results['ai_analysis'].append({
                'type': 'subdomain_analysis',
                'analysis': ai_analysis
            })
        
        self.results['subdomains'] = subdomain_list
        print(f"[SCAN] Found {len(subdomain_list)} subdomains")

    async def ai_analyze_subdomains(self, subdomains: List[str]) -> Dict:
        """AI analysis of subdomain patterns"""
        prompt = f"""
        Analyze these subdomains for security implications:
        {json.dumps(subdomains[:50], indent=2)}
        
        Identify:
        1. Interesting subdomains for security testing
        2. Potential development/staging environments
        3. Admin panels or sensitive endpoints
        4. Subdomains that might have weaker security
        5. Priority targets for further testing
        
        Provide a JSON response with prioritized targets.
        """
        
        return await self.query_ai_models(prompt)

    async def detect_technologies(self, target: str):
        """Detect web technologies"""
        print("[SCAN] Detecting technologies...")
        
        try:
            # Use whatweb for technology detection
            result = subprocess.run(
                ['whatweb', '--color=never', f'http://{target}'],
                capture_output=True, text=True, timeout=60
            )
            if result.stdout:
                self.results['technologies'] = result.stdout
        except Exception as e:
            print(f"[SCAN] Technology detection failed: {e}")

    async def discover_endpoints(self, target: str):
        """Discover endpoints and URLs"""
        print("[SCAN] Discovering endpoints...")
        
        endpoints = []
        
        # Use various discovery methods
        discovery_methods = [
            f'waybackurls {target}',
            f'gau {target}',
            f'gospider -s http://{target} -c 10 -d 2'
        ]
        
        for method in discovery_methods:
            try:
                result = subprocess.run(method.split(), capture_output=True, text=True, timeout=300)
                if result.stdout:
                    endpoints.extend(result.stdout.strip().split('\n'))
            except Exception as e:
                print(f"[SCAN] Endpoint discovery failed: {method} - {e}")
        
        self.results['endpoints'] = list(set(endpoints))
        print(f"[SCAN] Found {len(self.results['endpoints'])} endpoints")

    async def scan_vulnerabilities(self, target: str):
        """Scan for various vulnerabilities"""
        print("[SCAN] Scanning for vulnerabilities...")
        
        vulnerabilities = []
        
        # XSS Detection
        xss_vulns = await self.detect_xss(target)
        vulnerabilities.extend(xss_vulns)
        
        # SQL Injection Detection
        sqli_vulns = await self.detect_sqli(target)
        vulnerabilities.extend(sqli_vulns)
        
        # SSRF Detection
        ssrf_vulns = await self.detect_ssrf(target)
        vulnerabilities.extend(ssrf_vulns)
        
        # File Inclusion Detection
        lfi_vulns = await self.detect_lfi(target)
        vulnerabilities.extend(lfi_vulns)
        
        self.results['vulnerabilities'] = vulnerabilities
        print(f"[SCAN] Found {len(vulnerabilities)} potential vulnerabilities")

    async def detect_xss(self, target: str) -> List[Dict]:
        """Detect XSS vulnerabilities"""
        print("[SCAN] Testing for XSS...")
        
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '"><script>alert(document.domain)</script>',
            "javascript:alert('XSS')",
            '<img src=x onerror=alert("XSS")>',
            '<svg/onload=alert("XSS")>'
        ]
        
        vulnerabilities = []
        
        for endpoint in self.results['endpoints'][:20]:  # Test top 20 endpoints
            for payload in xss_payloads:
                try:
                    # Test parameter injection
                    if '?' in endpoint:
                        test_url = f"{endpoint}&xss_test={payload}"
                    else:
                        test_url = f"{endpoint}?xss_test={payload}"
                    
                    response = requests.get(test_url, timeout=10)
                    
                    # Check if payload is reflected
                    if payload in response.text:
                        vuln = {
                            'type': 'XSS',
                            'severity': 'Medium',
                            'url': test_url,
                            'payload': payload,
                            'evidence': f'Payload reflected in response',
                            'details': f'XSS vulnerability found at {endpoint}'
                        }
                        vulnerabilities.append(vuln)
                        
                except Exception as e:
                    continue
                    
        return vulnerabilities

    async def detect_sqli(self, target: str) -> List[Dict]:
        """Detect SQL Injection vulnerabilities"""
        print("[SCAN] Testing for SQL Injection...")
        
        sqli_payloads = [
            "'",
            "1' OR '1'='1",
            "1' UNION SELECT NULL--",
            "1'; DROP TABLE users--",
            "' OR 1=1#"
        ]
        
        vulnerabilities = []
        
        for endpoint in self.results['endpoints'][:15]:  # Test top 15 endpoints
            for payload in sqli_payloads:
                try:
                    if '?' in endpoint:
                        test_url = f"{endpoint}&sqli_test={payload}"
                    else:
                        test_url = f"{endpoint}?sqli_test={payload}"
                    
                    response = requests.get(test_url, timeout=10)
                    
                    # Check for SQL error messages
                    for pattern in self.vuln_patterns['sqli']:
                        if re.search(pattern, response.text, re.IGNORECASE):
                            vuln = {
                                'type': 'SQL Injection',
                                'severity': 'High',
                                'url': test_url,
                                'payload': payload,
                                'evidence': f'SQL error pattern found: {pattern}',
                                'details': f'SQL injection vulnerability found at {endpoint}'
                            }
                            vulnerabilities.append(vuln)
                            break
                            
                except Exception as e:
                    continue
                    
        return vulnerabilities

    async def detect_ssrf(self, target: str) -> List[Dict]:
        """Detect SSRF vulnerabilities"""
        print("[SCAN] Testing for SSRF...")
        
        ssrf_payloads = [
            'http://localhost:80',
            'http://127.0.0.1:22',
            'http://169.254.169.254/',  # AWS metadata
            'http://169.254.169.254/latest/meta-data/',
            'file:///etc/passwd'
        ]
        
        vulnerabilities = []
        
        for endpoint in self.results['endpoints'][:10]:  # Test top 10 endpoints
            for payload in ssrf_payloads:
                try:
                    if '?' in endpoint:
                        test_url = f"{endpoint}&url={payload}"
                    else:
                        test_url = f"{endpoint}?url={payload}"
                    
                    response = requests.get(test_url, timeout=15)
                    
                    # Check for SSRF indicators
                    if response.status_code == 200 and len(response.text) > 100:
                        # Additional checks for SSRF evidence
                        if 'root:' in response.text or 'localhost' in response.text:
                            vuln = {
                                'type': 'SSRF',
                                'severity': 'High',
                                'url': test_url,
                                'payload': payload,
                                'evidence': 'Potential SSRF response detected',
                                'details': f'SSRF vulnerability found at {endpoint}'
                            }
                            vulnerabilities.append(vuln)
                            
                except Exception as e:
                    continue
                    
        return vulnerabilities

    async def detect_lfi(self, target: str) -> List[Dict]:
        """Detect Local File Inclusion vulnerabilities"""
        print("[SCAN] Testing for LFI...")
        
        lfi_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '/etc/passwd',
            'file:///etc/passwd',
            '....//....//....//etc/passwd'
        ]
        
        vulnerabilities = []
        
        for endpoint in self.results['endpoints'][:10]:  # Test top 10 endpoints
            for payload in lfi_payloads:
                try:
                    if '?' in endpoint:
                        test_url = f"{endpoint}&file={payload}"
                    else:
                        test_url = f"{endpoint}?file={payload}"
                    
                    response = requests.get(test_url, timeout=10)
                    
                    # Check for LFI patterns
                    for pattern in self.vuln_patterns['lfi']:
                        if re.search(pattern, response.text, re.IGNORECASE):
                            vuln = {
                                'type': 'LFI',
                                'severity': 'High',
                                'url': test_url,
                                'payload': payload,
                                'evidence': f'File inclusion pattern found: {pattern}',
                                'details': f'LFI vulnerability found at {endpoint}'
                            }
                            vulnerabilities.append(vuln)
                            break
                            
                except Exception as e:
                    continue
                    
        return vulnerabilities

    async def ai_analyze_findings(self):
        """Use AI to analyze all findings and generate insights"""
        print("[AI] Analyzing findings with AI...")
        
        # Analyze each vulnerability with AI
        for i, vuln in enumerate(self.results['vulnerabilities']):
            ai_analysis = await self.ai_analyze_vulnerability(vuln)
            self.results['vulnerabilities'][i]['ai_analysis'] = ai_analysis
            
            # Update severity based on AI analysis
            if 'severity' in ai_analysis:
                self.results['vulnerabilities'][i]['severity'] = ai_analysis['severity']
        
        # Generate overall security assessment
        overall_prompt = f"""
        Analyze this security scan report:
        
        Target: {self.results['target']}
        Subdomains: {len(self.results['subdomains'])}
        Endpoints: {len(self.results['endpoints'])}
        Vulnerabilities: {len(self.results['vulnerabilities'])}
        
        Vulnerability Summary:
        {json.dumps([v['type'] for v in self.results['vulnerabilities']], indent=2)}
        
        Provide:
        1. Overall security posture assessment
        2. Priority recommendations
        3. Risk score (1-10)
        4. Executive summary for report
        """
        
        overall_analysis = await self.query_ai_models(overall_prompt)
        self.results['ai_analysis'].append({
            'type': 'overall_assessment',
            'analysis': overall_analysis
        })
        
        # Calculate severity score
        severity_scores = {'Critical': 10, 'High': 7, 'Medium': 4, 'Low': 1}
        total_score = sum(severity_scores.get(v.get('severity', 'Low'), 1) for v in self.results['vulnerabilities'])
        self.results['severity_score'] = min(total_score, 10)

    async def generate_report(self):
        """Generate comprehensive report"""
        print("[REPORT] Generating professional report...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = f"results/{self.results['target']}_{timestamp}"
        os.makedirs(report_dir, exist_ok=True)
        
        # Generate HackerOne reports for each vulnerability
        for i, vuln in enumerate(self.results['vulnerabilities']):
            if 'ai_analysis' in vuln and 'hackerone_template' in vuln['ai_analysis']:
                filename = f"{report_dir}/hackerone_report_{i+1}_{vuln['type'].lower().replace(' ', '_')}.md"
                with open(filename, 'w') as f:
                    f.write(vuln['ai_analysis']['hackerone_template'])
        
        # Generate comprehensive HTML report
        html_report = self.generate_html_report()
        with open(f"{report_dir}/comprehensive_report.html", 'w') as f:
            f.write(html_report)
        
        # Generate JSON export
        with open(f"{report_dir}/scan_results.json", 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Generate executive summary
        exec_summary = self.generate_executive_summary()
        with open(f"{report_dir}/executive_summary.md", 'w') as f:
            f.write(exec_summary)
        
        print(f"[REPORT] Reports generated in: {report_dir}")
        return report_dir

    def generate_html_report(self) -> str:
        """Generate professional HTML report"""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Enhanced Security Assessment - {self.results['target']}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 40px; border-bottom: 3px solid #007acc; padding-bottom: 20px; }}
        .severity-critical {{ color: #d73502; font-weight: bold; }}
        .severity-high {{ color: #ff4444; font-weight: bold; }}
        .severity-medium {{ color: #ff9800; font-weight: bold; }}
        .severity-low {{ color: #4caf50; font-weight: bold; }}
        .vuln-card {{ background: #f9f9f9; border-left: 5px solid #007acc; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .recommendations {{ background: #e8f5e8; border: 1px solid #4caf50; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        pre {{ background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .ai-badge {{ background: linear-gradient(45deg, #667eea, #764ba2); color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 AI-Enhanced Security Assessment</h1>
            <h2>{self.results['target']}</h2>
            <p><strong>Scan Date:</strong> {self.results['scan_time'][:19]} | <span class="ai-badge">AI-Powered Analysis</span></p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>{len(self.results['subdomains'])}</h3>
                <p>Subdomains Found</p>
            </div>
            <div class="stat-card">
                <h3>{len(self.results['endpoints'])}</h3>
                <p>Endpoints Discovered</p>
            </div>
            <div class="stat-card">
                <h3>{len(self.results['vulnerabilities'])}</h3>
                <p>Vulnerabilities Detected</p>
            </div>
            <div class="stat-card">
                <h3>{self.results['severity_score']}/10</h3>
                <p>Risk Score</p>
            </div>
        </div>
        
        <h2>🚨 Vulnerability Summary</h2>
        """
        
        # Add vulnerabilities
        for vuln in self.results['vulnerabilities']:
            severity_class = f"severity-{vuln.get('severity', 'medium').lower()}"
            html += f"""
            <div class="vuln-card">
                <h3>{vuln.get('type', 'Unknown Vulnerability')} 
                    <span class="{severity_class}">[{vuln.get('severity', 'Medium')}]</span>
                </h3>
                <p><strong>URL:</strong> <code>{vuln.get('url', 'N/A')}</code></p>
                <p><strong>Details:</strong> {vuln.get('details', 'No details available')}</p>
                
                <h4>🤖 AI Analysis</h4>
                <div style="background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 10px 0;">
            """
            
            if 'ai_analysis' in vuln:
                ai = vuln['ai_analysis']
                html += f"""
                    <p><strong>Exploitability:</strong> {ai.get('exploitability', 'Unknown')}</p>
                    <p><strong>Business Impact:</strong> {ai.get('impact', 'Unknown')}</p>
                    <p><strong>Remediation:</strong> {ai.get('remediation', 'No specific recommendations')}</p>
                """
            else:
                html += "<p>AI analysis pending...</p>"
            
            html += "</div></div>"
        
        # Add recommendations
        html += """
        <h2>💡 AI-Generated Recommendations</h2>
        <div class="recommendations">
            <h3>Priority Actions:</h3>
            <ul>
                <li>Immediately patch all Critical and High severity vulnerabilities</li>
                <li>Implement Web Application Firewall (WAF) protection</li>
                <li>Enable Content Security Policy (CSP) headers</li>
                <li>Conduct regular security testing and code reviews</li>
                <li>Implement input validation and output encoding</li>
            </ul>
        </div>
        
        <h2>🔧 Technical Details</h2>
        <details>
            <summary>View Raw Scan Data</summary>
            <pre><code>""" + json.dumps(self.results, indent=2, default=str) + """</code></pre>
        </details>
        
        <footer style="text-align: center; margin-top: 40px; color: #666;">
            <p>Generated by AI-Enhanced Bug Bounty Scanner v2.0 | """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </footer>
    </div>
</body>
</html>"""
        
        return html

    def generate_executive_summary(self) -> str:
        """Generate executive summary"""
        critical_count = len([v for v in self.results['vulnerabilities'] if v.get('severity') == 'Critical'])
        high_count = len([v for v in self.results['vulnerabilities'] if v.get('severity') == 'High'])
        medium_count = len([v for v in self.results['vulnerabilities'] if v.get('severity') == 'Medium'])
        low_count = len([v for v in self.results['vulnerabilities'] if v.get('severity') == 'Low'])
        
        summary = f"""# Executive Security Assessment Summary

## Target: {self.results['target']}
## Assessment Date: {self.results['scan_time'][:19]}
## Overall Risk Score: {self.results['severity_score']}/10

### Key Findings

- **Total Subdomains Discovered:** {len(self.results['subdomains'])}
- **Total Endpoints Analyzed:** {len(self.results['endpoints'])}
- **Security Vulnerabilities Found:** {len(self.results['vulnerabilities'])}

### Vulnerability Breakdown

| Severity | Count | Priority |
|----------|-------|----------|
| Critical | {critical_count} | Immediate Action Required |
| High     | {high_count} | Fix Within 48 Hours |
| Medium   | {medium_count} | Fix Within 1 Week |
| Low      | {low_count} | Fix Within 1 Month |

### Risk Assessment

"""
        
        if self.results['severity_score'] >= 8:
            summary += "🔴 **HIGH RISK**: Critical vulnerabilities identified that require immediate attention.\n\n"
        elif self.results['severity_score'] >= 5:
            summary += "🟡 **MEDIUM RISK**: Multiple vulnerabilities found that should be addressed promptly.\n\n"
        else:
            summary += "🟢 **LOW RISK**: Few low-severity issues identified. Maintain current security practices.\n\n"
        
        summary += """### Immediate Actions Required

1. **Patch Critical Vulnerabilities**: Address all critical and high-severity issues immediately
2. **Implement Security Headers**: Deploy proper security headers across all applications
3. **Input Validation**: Implement comprehensive input validation and sanitization
4. **Regular Security Testing**: Establish ongoing security assessment processes
5. **Security Training**: Conduct security awareness training for development teams

### HackerOne Report Files

Individual HackerOne-ready vulnerability reports have been generated for each finding. These can be directly submitted to bug bounty programs.

---
*This assessment was conducted using AI-enhanced security testing methodologies and should be reviewed by qualified security professionals.*
"""
        
        return summary

async def main():
    """Main execution function"""
    if len(sys.argv) != 2:
        print("Usage: python3 ai_vuln_scanner.py <target-domain>")
        sys.exit(1)
    
    target = sys.argv[1]
    scanner = AIVulnScanner()
    
    print(f"🤖 Starting AI-Enhanced Bug Bounty Scan for: {target}")
    print("=" * 60)
    
    try:
        # Setup AI models
        await scanner.setup_ai_models()
        
        # Perform deep scan
        results = await scanner.deep_scan_target(target)
        
        print("\n" + "=" * 60)
        print("🎉 Scan completed successfully!")
        print(f"📊 Found {len(results['vulnerabilities'])} vulnerabilities")
        print(f"🔍 Analyzed {len(results['subdomains'])} subdomains")
        print(f"📈 Risk Score: {results['severity_score']}/10")
        
        # Results will be saved automatically by generate_report()
        
    except KeyboardInterrupt:
        print("\n❌ Scan interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during scan: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
