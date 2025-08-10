#!/usr/bin/env python3
"""
Enhanced Multi-Platform Bug Bounty Report Generator
Generates professional reports for HackerOne, Bugcrowd, and custom formats
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import base64
import hashlib
import requests
import asyncio
import aiohttp

@dataclass
class VulnerabilityReport:
    title: str
    severity: str
    vulnerability_type: str
    description: str
    impact: str
    steps_to_reproduce: List[str]
    proof_of_concept: str
    mitigation: str
    references: List[str]
    cvss_score: Optional[float] = None
    cwe_id: Optional[str] = None
    screenshots: List[str] = None

class EnhancedReportGenerator:
    def __init__(self):
        self.framework_dir = Path(__file__).parent
        self.templates_dir = self.framework_dir / 'report_templates'
        self.output_dir = self.framework_dir / 'reports'
        
        # Create directories
        self.templates_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Vulnerability type mappings
        self.vuln_type_mapping = {
            'xss': {
                'name': 'Cross-Site Scripting (XSS)',
                'cwe': 'CWE-79',
                'description_template': 'Cross-Site Scripting vulnerability allows injection of malicious scripts',
                'impact_template': 'Attackers can execute arbitrary JavaScript in victim browsers, leading to session hijacking, credential theft, or defacement'
            },
            'sqli': {
                'name': 'SQL Injection',
                'cwe': 'CWE-89',
                'description_template': 'SQL Injection vulnerability allows manipulation of database queries',
                'impact_template': 'Attackers can read, modify, or delete database contents, potentially leading to data breach or system compromise'
            },
            'lfi': {
                'name': 'Local File Inclusion',
                'cwe': 'CWE-22',
                'description_template': 'Local File Inclusion allows reading arbitrary files from the server',
                'impact_template': 'Attackers can access sensitive configuration files, source code, or system files'
            },
            'rfi': {
                'name': 'Remote File Inclusion',
                'cwe': 'CWE-98',
                'description_template': 'Remote File Inclusion allows inclusion of external files',
                'impact_template': 'Attackers can execute arbitrary code by including malicious external files'
            },
            'csrf': {
                'name': 'Cross-Site Request Forgery',
                'cwe': 'CWE-352',
                'description_template': 'CSRF vulnerability allows unauthorized actions on behalf of authenticated users',
                'impact_template': 'Attackers can perform actions as authenticated users without their consent'
            },
            'idor': {
                'name': 'Insecure Direct Object Reference',
                'cwe': 'CWE-639',
                'description_template': 'IDOR vulnerability allows access to unauthorized resources',
                'impact_template': 'Attackers can access or modify resources belonging to other users'
            }
        }
        
        # Platform-specific templates
        self.platform_templates = {
            'hackerone': self._get_hackerone_template(),
            'bugcrowd': self._get_bugcrowd_template(),
            'generic': self._get_generic_template()
        }

    def _get_hackerone_template(self) -> str:
        return """# {title}

## Summary
{summary}

## Description
{description}

## Steps to Reproduce
{steps_to_reproduce}

## Impact
{impact}

## Proof of Concept
{proof_of_concept}

## Mitigation
{mitigation}

## Supporting Material/References
{references}

## System Information
- **Vulnerability Type**: {vulnerability_type}
- **Severity**: {severity}
- **CVSS Score**: {cvss_score}
- **CWE**: {cwe_id}
- **Discovery Date**: {discovery_date}

{attachments}
"""

    def _get_bugcrowd_template(self) -> str:
        return """**Title:** {title}

**Severity:** {severity}

**Vulnerability Type:** {vulnerability_type}

**Description:**
{description}

**Reproduction Steps:**
{steps_to_reproduce}

**Impact:**
{impact}

**Proof of Concept:**
{proof_of_concept}

**Recommended Fix:**
{mitigation}

**Additional Information:**
- CWE: {cwe_id}
- CVSS Score: {cvss_score}
- Discovery Date: {discovery_date}

{references}

{attachments}
"""

    def _get_generic_template(self) -> str:
        return """# Vulnerability Report: {title}

**Date:** {discovery_date}
**Severity:** {severity}
**Type:** {vulnerability_type}
**CWE:** {cwe_id}
**CVSS Score:** {cvss_score}

## Executive Summary
{summary}

## Technical Description
{description}

## Reproduction Steps
{steps_to_reproduce}

## Business Impact
{impact}

## Proof of Concept
{proof_of_concept}

## Remediation
{mitigation}

## References
{references}

{attachments}
"""

    async def ai_enhance_report(self, vulnerability_data: Dict) -> VulnerabilityReport:
        """Use AI to enhance and generate professional report content"""
        
        vuln_type = vulnerability_data.get('type', '').lower()
        url = vulnerability_data.get('url', '')
        evidence = vulnerability_data.get('evidence', '')
        
        # Get vulnerability type info
        type_info = self.vuln_type_mapping.get(vuln_type, {
            'name': vulnerability_data.get('type', 'Security Vulnerability'),
            'cwe': 'CWE-unknown',
            'description_template': 'Security vulnerability detected',
            'impact_template': 'Potential security impact'
        })
        
        # AI prompt for enhanced report generation
        prompt = f"""
        Generate a professional security vulnerability report based on this finding:
        
        Vulnerability Type: {type_info['name']}
        URL: {url}
        Evidence: {evidence}
        Severity: {vulnerability_data.get('severity', 'Medium')}
        
        Provide a comprehensive report including:
        1. Professional title
        2. Detailed technical description
        3. Step-by-step reproduction steps
        4. Business impact analysis
        5. Proof of concept
        6. Mitigation recommendations
        
        Format as JSON with these fields:
        {{
            "title": "Professional vulnerability title",
            "description": "Detailed technical description",
            "steps": ["step1", "step2", "step3"],
            "impact": "Business impact analysis",
            "poc": "Proof of concept details",
            "mitigation": "Remediation steps",
            "references": ["ref1", "ref2"]
        }}
        """
        
        # Try to get AI enhancement
        ai_response = await self._query_ai_for_enhancement(prompt)
        
        if ai_response:
            return VulnerabilityReport(
                title=ai_response.get('title', f"{type_info['name']} in {url}"),
                severity=vulnerability_data.get('severity', 'Medium'),
                vulnerability_type=type_info['name'],
                description=ai_response.get('description', type_info['description_template']),
                impact=ai_response.get('impact', type_info['impact_template']),
                steps_to_reproduce=ai_response.get('steps', []),
                proof_of_concept=ai_response.get('poc', evidence),
                mitigation=ai_response.get('mitigation', 'Apply appropriate security controls'),
                references=ai_response.get('references', []),
                cwe_id=type_info['cwe'],
                cvss_score=self._calculate_cvss_score(vulnerability_data.get('severity', 'Medium'))
            )
        
        # Fallback to template-based generation
        return self._generate_template_report(vulnerability_data, type_info)

    async def _query_ai_for_enhancement(self, prompt: str) -> Optional[Dict]:
        """Query AI models for report enhancement"""
        
        # Try Ollama first
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': 'llama3.2:3b',
                        'prompt': prompt,
                        'stream': False
                    },
                    timeout=60
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        ai_response = data.get('response', '')
                        
                        # Try to extract JSON
                        try:
                            json_start = ai_response.find('{')
                            json_end = ai_response.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                json_str = ai_response[json_start:json_end]
                                return json.loads(json_str)
                        except:
                            pass
        
        except Exception as e:
            print(f"⚠️  AI enhancement failed: {e}")
        
        return None

    def _generate_template_report(self, vulnerability_data: Dict, type_info: Dict) -> VulnerabilityReport:
        """Generate report using templates when AI is not available"""
        
        url = vulnerability_data.get('url', 'Unknown')
        evidence = vulnerability_data.get('evidence', 'No evidence provided')
        severity = vulnerability_data.get('severity', 'Medium')
        
        return VulnerabilityReport(
            title=f"{type_info['name']} in {url}",
            severity=severity,
            vulnerability_type=type_info['name'],
            description=f"{type_info['description_template']} found in {url}. {evidence}",
            impact=type_info['impact_template'],
            steps_to_reproduce=[
                f"1. Navigate to {url}",
                "2. Observe the vulnerability condition",
                "3. Verify the security impact"
            ],
            proof_of_concept=evidence,
            mitigation="Apply appropriate security controls and input validation",
            references=[
                f"OWASP: {type_info['name']}",
                f"CWE: {type_info['cwe']}"
            ],
            cwe_id=type_info['cwe'],
            cvss_score=self._calculate_cvss_score(severity)
        )

    def _calculate_cvss_score(self, severity: str) -> float:
        """Calculate CVSS score based on severity"""
        severity_mapping = {
            'critical': 9.5,
            'high': 7.5,
            'medium': 5.5,
            'low': 3.0,
            'info': 1.0
        }
        
        return severity_mapping.get(severity.lower(), 5.0)

    def generate_platform_report(self, report: VulnerabilityReport, platform: str = 'hackerone') -> str:
        """Generate report for specific platform"""
        
        template = self.platform_templates.get(platform, self.platform_templates['generic'])
        
        # Prepare data for template
        template_data = {
            'title': report.title,
            'summary': f"{report.vulnerability_type} vulnerability with {report.severity} severity",
            'description': report.description,
            'steps_to_reproduce': self._format_steps(report.steps_to_reproduce),
            'impact': report.impact,
            'proof_of_concept': report.proof_of_concept,
            'mitigation': report.mitigation,
            'vulnerability_type': report.vulnerability_type,
            'severity': report.severity,
            'cvss_score': report.cvss_score or 'N/A',
            'cwe_id': report.cwe_id or 'N/A',
            'discovery_date': datetime.now().strftime('%Y-%m-%d'),
            'references': self._format_references(report.references),
            'attachments': self._format_attachments(report.screenshots)
        }
        
        return template.format(**template_data)

    def _format_steps(self, steps: List[str]) -> str:
        """Format reproduction steps"""
        if not steps:
            return "Steps to reproduce will be provided upon request."
        
        formatted_steps = []
        for i, step in enumerate(steps, 1):
            if not step.startswith(str(i)):
                formatted_steps.append(f"{i}. {step}")
            else:
                formatted_steps.append(step)
        
        return '\n'.join(formatted_steps)

    def _format_references(self, references: List[str]) -> str:
        """Format references section"""
        if not references:
            return "Additional references available upon request."
        
        formatted_refs = []
        for ref in references:
            if ref.startswith('http'):
                formatted_refs.append(f"- {ref}")
            else:
                formatted_refs.append(f"- {ref}")
        
        return '\n'.join(formatted_refs)

    def _format_attachments(self, screenshots: List[str]) -> str:
        """Format attachments section"""
        if not screenshots:
            return "\n**Note:** Screenshots and additional proof-of-concept materials can be provided upon request."
        
        attachments = []
        for i, screenshot in enumerate(screenshots, 1):
            attachments.append(f"**Attachment {i}:** {screenshot}")
        
        return '\n'.join(attachments)

    async def generate_comprehensive_report(self, vulnerability_data: Dict, platforms: List[str] = ['hackerone']) -> Dict[str, str]:
        """Generate comprehensive reports for multiple platforms"""
        
        print(f"🔄 Generating enhanced report for {vulnerability_data.get('type', 'vulnerability')}...")
        
        # Generate enhanced report using AI
        enhanced_report = await self.ai_enhance_report(vulnerability_data)
        
        # Generate platform-specific reports
        reports = {}
        
        for platform in platforms:
            print(f"   📝 Generating {platform} report...")
            platform_report = self.generate_platform_report(enhanced_report, platform)
            reports[platform] = platform_report
        
        print("✅ Report generation completed")
        
        return reports

    def save_reports(self, reports: Dict[str, str], base_filename: str) -> Dict[str, str]:
        """Save reports to files"""
        
        saved_files = {}
        
        for platform, report_content in reports.items():
            filename = f"{base_filename}_{platform}_report.md"
            filepath = self.output_dir / filename
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                
                saved_files[platform] = str(filepath)
                print(f"✅ {platform.title()} report saved: {filepath}")
                
            except Exception as e:
                print(f"❌ Failed to save {platform} report: {e}")
        
        return saved_files

    def create_report_index(self, vulnerability_reports: List[Dict]) -> str:
        """Create an index of all generated reports"""
        
        index_content = f"""# Vulnerability Reports Index

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total Reports: {len(vulnerability_reports)}

## Summary by Severity

"""
        
        # Count by severity
        severity_counts = {}
        for report in vulnerability_reports:
            severity = report.get('severity', 'Unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        for severity, count in sorted(severity_counts.items()):
            emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
            index_content += f"- {emoji} **{severity}**: {count} reports\n"
        
        index_content += f"""

## Detailed Reports

"""
        
        for i, report in enumerate(vulnerability_reports, 1):
            title = report.get('title', 'Unknown Vulnerability')
            severity = report.get('severity', 'Unknown')
            url = report.get('url', 'N/A')
            
            index_content += f"""### {i}. {title}
- **Severity**: {severity}
- **URL**: {url}
- **Type**: {report.get('type', 'Unknown')}
- **Report Files**:
"""
            
            # List generated report files
            for platform in ['hackerone', 'bugcrowd', 'generic']:
                filename = f"{report.get('id', str(i))}_{platform}_report.md"
                index_content += f"  - [{platform.title()}](./{filename})\n"
            
            index_content += "\n"
        
        return index_content

    async def batch_generate_reports(self, vulnerabilities: List[Dict], platforms: List[str] = ['hackerone', 'generic']) -> Dict[str, Any]:
        """Generate reports for multiple vulnerabilities"""
        
        print(f"🚀 Starting batch report generation for {len(vulnerabilities)} vulnerabilities...")
        
        generated_reports = []
        summary = {
            'total_vulnerabilities': len(vulnerabilities),
            'successful_reports': 0,
            'failed_reports': 0,
            'platforms': platforms,
            'generated_files': {}
        }
        
        for i, vuln in enumerate(vulnerabilities):
            try:
                print(f"\n📝 Processing vulnerability {i+1}/{len(vulnerabilities)}: {vuln.get('type', 'Unknown')}")
                
                # Generate reports for all platforms
                reports = await self.generate_comprehensive_report(vuln, platforms)
                
                # Save reports
                base_filename = f"vuln_{i+1}_{vuln.get('type', 'unknown')}"
                saved_files = self.save_reports(reports, base_filename)
                
                # Track generated report
                report_info = {
                    'id': str(i+1),
                    'title': vuln.get('title', f"{vuln.get('type', 'Unknown')} vulnerability"),
                    'type': vuln.get('type', 'Unknown'),
                    'severity': vuln.get('severity', 'Medium'),
                    'url': vuln.get('url', 'N/A'),
                    'files': saved_files
                }
                
                generated_reports.append(report_info)
                summary['successful_reports'] += 1
                summary['generated_files'].update(saved_files)
                
            except Exception as e:
                print(f"❌ Failed to generate report for vulnerability {i+1}: {e}")
                summary['failed_reports'] += 1
        
        # Generate index file
        index_content = self.create_report_index(generated_reports)
        index_file = self.output_dir / 'vulnerability_reports_index.md'
        
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(index_content)
            print(f"✅ Report index saved: {index_file}")
            summary['index_file'] = str(index_file)
        except Exception as e:
            print(f"⚠️  Failed to create index file: {e}")
        
        # Final summary
        print(f"\n📊 Batch Report Generation Summary:")
        print(f"   Total Vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"   Successful Reports: {summary['successful_reports']}")
        print(f"   Failed Reports: {summary['failed_reports']}")
        print(f"   Files Generated: {len(summary['generated_files'])}")
        print(f"   Output Directory: {self.output_dir}")
        
        return summary

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Bug Bounty Report Generator')
    parser.add_argument('--input', required=True, help='JSON file with vulnerability data')
    parser.add_argument('--platforms', nargs='+', choices=['hackerone', 'bugcrowd', 'generic'], 
                       default=['hackerone'], help='Platforms to generate reports for')
    parser.add_argument('--output-dir', help='Output directory for reports')
    
    args = parser.parse_args()
    
    async def generate_reports():
        generator = EnhancedReportGenerator()
        
        if args.output_dir:
            generator.output_dir = Path(args.output_dir)
            generator.output_dir.mkdir(exist_ok=True)
        
        # Load vulnerability data
        with open(args.input, 'r') as f:
            vulnerabilities = json.load(f)
        
        # Ensure vulnerabilities is a list
        if isinstance(vulnerabilities, dict):
            vulnerabilities = [vulnerabilities]
        
        # Generate reports
        summary = await generator.batch_generate_reports(vulnerabilities, args.platforms)
        
        print(f"\n🎉 Report generation completed!")
        print(f"Check the output directory: {generator.output_dir}")
    
    # Run async report generation
    asyncio.run(generate_reports())

if __name__ == "__main__":
    main()
