#!/usr/bin/env python3
"""
AI-Powered False Positive Detection and Filtering System
Uses machine learning and AI models to identify and filter false positives
"""

import json
import re
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import requests
import asyncio
import aiohttp
from datetime import datetime
import logging

@dataclass
class VulnerabilityFindings:
    id: str
    type: str
    severity: str
    url: str
    title: str
    description: str
    evidence: str
    source_tool: str
    confidence: float = 0.0
    is_false_positive: bool = False
    ai_analysis: Dict = None

class AIFalsePositiveFilter:
    def __init__(self):
        self.framework_dir = Path(__file__).parent
        self.false_positive_patterns = self._load_fp_patterns()
        self.verified_fps = self._load_verified_fps()
        self.ai_models = {
            'ollama': 'http://localhost:11434/api/generate',
            'huggingface': 'https://api-inference.huggingface.co/models/',
        }
        
        # Common false positive indicators
        self.fp_indicators = {
            'nuclei': [
                # Common false positive patterns for Nuclei
                r'test\.php\?id=\d+',  # Test files
                r'example\.com',        # Example domains
                r'localhost:\d+',       # Local development
                r'127\.0\.0\.1',        # Localhost
                r'staging\.',           # Staging environments
                r'dev\.',               # Dev environments
            ],
            'xss': [
                # XSS false positive patterns
                r'alert\([\'"]test[\'"]\)',     # Test alerts
                r'console\.log',                # Console logs
                r'<script>.*</script>',         # Generic script tags
                r'javascript:void\(0\)',        # Void javascript
                r'onclick=[\'"].*[\'"]',        # Generic onclick
            ],
            'sqli': [
                # SQL injection false positive patterns
                r'mysql_error',                 # Generic MySQL errors
                r'Database connection failed',   # Connection errors
                r'syntax error.*mysql',         # Syntax errors
                r'You have an error in your SQL', # MySQL error messages
            ]
        }

    def _load_fp_patterns(self) -> Dict[str, List[str]]:
        """Load known false positive patterns from file"""
        patterns_file = self.framework_dir / 'config' / 'false_positive_patterns.json'
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {}

    def _load_verified_fps(self) -> set:
        """Load verified false positives (hashed)"""
        fp_file = self.framework_dir / 'config' / 'verified_false_positives.json'
        
        if fp_file.exists():
            try:
                with open(fp_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('hashes', []))
            except Exception:
                pass
        
        return set()

    def _generate_finding_hash(self, finding: VulnerabilityFindings) -> str:
        """Generate a unique hash for a finding"""
        content = f"{finding.type}:{finding.url}:{finding.title}:{finding.evidence}"
        return hashlib.md5(content.encode()).hexdigest()

    def check_pattern_based_fp(self, finding: VulnerabilityFindings) -> Tuple[bool, str]:
        """Check for false positives using pattern matching"""
        
        # Check against known verified false positives
        finding_hash = self._generate_finding_hash(finding)
        if finding_hash in self.verified_fps:
            return True, "Previously verified false positive"
        
        # Check source-specific patterns
        source_patterns = self.fp_indicators.get(finding.source_tool, [])
        
        # Check URL patterns
        for pattern in source_patterns:
            if re.search(pattern, finding.url, re.IGNORECASE):
                return True, f"URL matches FP pattern: {pattern}"
        
        # Check evidence patterns
        for pattern in source_patterns:
            if re.search(pattern, finding.evidence, re.IGNORECASE):
                return True, f"Evidence matches FP pattern: {pattern}"
        
        # Check title patterns
        for pattern in source_patterns:
            if re.search(pattern, finding.title, re.IGNORECASE):
                return True, f"Title matches FP pattern: {pattern}"
        
        # Generic false positive indicators
        generic_fp_patterns = [
            r'test\d*\.(php|jsp|asp|html)',  # Test pages
            r'example\.(com|org|net)',        # Example domains
            r'dummy|sample|fake|mock',        # Dummy content
            r'staging|dev|test|demo',         # Non-production environments
        ]
        
        combined_text = f"{finding.url} {finding.title} {finding.evidence}".lower()
        
        for pattern in generic_fp_patterns:
            if re.search(pattern, combined_text):
                return True, f"Generic FP pattern matched: {pattern}"
        
        return False, ""

    async def ai_analyze_finding(self, finding: VulnerabilityFindings) -> Dict[str, Any]:
        """Use AI to analyze if finding is a false positive"""
        
        prompt = f"""
        Analyze this security finding and determine if it's a false positive:

        Type: {finding.type}
        Severity: {finding.severity}
        URL: {finding.url}
        Title: {finding.title}
        Description: {finding.description}
        Evidence: {finding.evidence}
        Source Tool: {finding.source_tool}

        Consider these factors:
        1. Is this a real exploitable vulnerability?
        2. Could this be caused by test/demo content?
        3. Does the evidence show actual exploitation potential?
        4. Are there context clues suggesting this is benign?
        5. Is the URL/endpoint likely to be production-facing?

        Respond in JSON format:
        {{
            "is_false_positive": true/false,
            "confidence": 0.0-1.0,
            "reasoning": "detailed explanation",
            "risk_factors": ["factor1", "factor2"],
            "recommended_action": "verify_manually|dismiss|escalate"
        }}
        """

        # Try Ollama first
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ai_models['ollama'],
                    json={
                        'model': 'llama3.2:3b',
                        'prompt': prompt,
                        'stream': False
                    },
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        ai_response = data.get('response', '')
                        
                        # Try to parse JSON from response
                        try:
                            # Extract JSON from response
                            json_start = ai_response.find('{')
                            json_end = ai_response.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                json_str = ai_response[json_start:json_end]
                                return json.loads(json_str)
                        except:
                            pass
                        
                        # Fallback: analyze response text
                        return self._parse_ai_response_text(ai_response)
        
        except Exception as e:
            logging.error(f"Ollama analysis failed: {e}")

        # Fallback to HuggingFace
        try:
            model_url = f"{self.ai_models['huggingface']}microsoft/DialoGPT-medium"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    model_url,
                    json={'inputs': prompt[:1000]},  # Truncate for HF limits
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data and isinstance(data, list) and len(data) > 0:
                            ai_response = data[0].get('generated_text', '')
                            return self._parse_ai_response_text(ai_response)
        
        except Exception as e:
            logging.error(f"HuggingFace analysis failed: {e}")

        # Ultimate fallback
        return {
            'is_false_positive': False,
            'confidence': 0.0,
            'reasoning': 'AI analysis unavailable',
            'risk_factors': [],
            'recommended_action': 'verify_manually'
        }

    def _parse_ai_response_text(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response text when JSON parsing fails"""
        
        # Look for key indicators in the response
        response_lower = response_text.lower()
        
        # Determine false positive likelihood
        fp_indicators = ['false positive', 'not exploitable', 'benign', 'safe', 'test content']
        real_indicators = ['exploitable', 'vulnerability', 'security risk', 'malicious']
        
        fp_score = sum(1 for indicator in fp_indicators if indicator in response_lower)
        real_score = sum(1 for indicator in real_indicators if indicator in response_lower)
        
        is_fp = fp_score > real_score
        confidence = min(0.8, max(0.3, abs(fp_score - real_score) / 10))
        
        return {
            'is_false_positive': is_fp,
            'confidence': confidence,
            'reasoning': f"Text analysis based on response: {response_text[:200]}...",
            'risk_factors': [],
            'recommended_action': 'verify_manually'
        }

    async def comprehensive_fp_analysis(self, finding: VulnerabilityFindings) -> VulnerabilityFindings:
        """Run comprehensive false positive analysis"""
        
        # Step 1: Pattern-based check
        is_pattern_fp, pattern_reason = self.check_pattern_based_fp(finding)
        
        if is_pattern_fp:
            finding.is_false_positive = True
            finding.confidence = 0.9
            finding.ai_analysis = {
                'method': 'pattern_matching',
                'reasoning': pattern_reason,
                'confidence': 0.9
            }
            return finding
        
        # Step 2: Context analysis
        context_fp, context_reason = self._analyze_context(finding)
        if context_fp:
            finding.is_false_positive = True
            finding.confidence = 0.8
            finding.ai_analysis = {
                'method': 'context_analysis',
                'reasoning': context_reason,
                'confidence': 0.8
            }
            return finding
        
        # Step 3: AI analysis
        try:
            ai_analysis = await self.ai_analyze_finding(finding)
            finding.ai_analysis = ai_analysis
            finding.is_false_positive = ai_analysis.get('is_false_positive', False)
            finding.confidence = ai_analysis.get('confidence', 0.5)
        except Exception as e:
            logging.error(f"AI analysis failed: {e}")
            finding.confidence = 0.5
        
        return finding

    def _analyze_context(self, finding: VulnerabilityFindings) -> Tuple[bool, str]:
        """Analyze contextual clues for false positives"""
        
        # Check for development/staging environments
        dev_indicators = ['localhost', '127.0.0.1', 'dev.', 'staging.', 'test.', 'demo.']
        for indicator in dev_indicators:
            if indicator in finding.url.lower():
                return True, f"Development environment detected: {indicator}"
        
        # Check for test content
        test_indicators = ['test', 'sample', 'demo', 'example', 'dummy']
        combined_content = f"{finding.title} {finding.description} {finding.evidence}".lower()
        
        for indicator in test_indicators:
            if indicator in combined_content:
                return True, f"Test content detected: {indicator}"
        
        # Check URL structure for common false positive patterns
        if re.search(r'/test/', finding.url):
            return True, "Test directory in URL path"
        
        if re.search(r'\.(txt|log|bak|old)$', finding.url):
            return True, "Non-executable file extension"
        
        # Check for HTTP status codes that indicate false positives
        if '404' in finding.evidence or '403' in finding.evidence:
            return True, "HTTP error status in evidence"
        
        return False, ""

    async def filter_findings_batch(self, findings: List[Dict]) -> List[Dict]:
        """Filter a batch of findings for false positives"""
        
        print(f"🔍 Analyzing {len(findings)} findings for false positives...")
        
        # Convert to VulnerabilityFindings objects
        vuln_findings = []
        for i, finding in enumerate(findings):
            vuln_finding = VulnerabilityFindings(
                id=finding.get('id', str(i)),
                type=finding.get('type', 'unknown'),
                severity=finding.get('severity', 'medium'),
                url=finding.get('url', ''),
                title=finding.get('title', ''),
                description=finding.get('description', ''),
                evidence=finding.get('evidence', ''),
                source_tool=finding.get('source_tool', 'unknown')
            )
            vuln_findings.append(vuln_finding)
        
        # Analyze each finding
        analyzed_findings = []
        false_positive_count = 0
        
        for finding in vuln_findings:
            analyzed = await self.comprehensive_fp_analysis(finding)
            analyzed_findings.append(analyzed)
            
            if analyzed.is_false_positive:
                false_positive_count += 1
                print(f"   🚫 FP: {analyzed.title} (confidence: {analyzed.confidence:.2f})")
            else:
                print(f"   ✅ Valid: {analyzed.title} (confidence: {analyzed.confidence:.2f})")
        
        print(f"📊 False positive analysis complete:")
        print(f"   Total findings: {len(findings)}")
        print(f"   False positives: {false_positive_count}")
        print(f"   Valid findings: {len(findings) - false_positive_count}")
        
        # Convert back to dictionaries and filter
        filtered_findings = []
        for analyzed in analyzed_findings:
            if not analyzed.is_false_positive:
                finding_dict = {
                    'id': analyzed.id,
                    'type': analyzed.type,
                    'severity': analyzed.severity,
                    'url': analyzed.url,
                    'title': analyzed.title,
                    'description': analyzed.description,
                    'evidence': analyzed.evidence,
                    'source_tool': analyzed.source_tool,
                    'confidence': analyzed.confidence,
                    'ai_analysis': analyzed.ai_analysis
                }
                filtered_findings.append(finding_dict)
        
        return filtered_findings

    def save_verified_fp(self, finding_hash: str):
        """Save a verified false positive for future reference"""
        self.verified_fps.add(finding_hash)
        
        # Save to file
        fp_file = self.framework_dir / 'config' / 'verified_false_positives.json'
        fp_file.parent.mkdir(exist_ok=True)
        
        try:
            data = {'hashes': list(self.verified_fps)}
            with open(fp_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save verified FP: {e}")

    def create_fp_report(self, analyzed_findings: List[VulnerabilityFindings]) -> str:
        """Create a detailed false positive analysis report"""
        
        fp_findings = [f for f in analyzed_findings if f.is_false_positive]
        valid_findings = [f for f in analyzed_findings if not f.is_false_positive]
        
        report = f"""
# False Positive Analysis Report

## Summary
- **Total Findings**: {len(analyzed_findings)}
- **False Positives**: {len(fp_findings)}
- **Valid Findings**: {len(valid_findings)}
- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## False Positive Details

"""
        
        for fp in fp_findings:
            report += f"""
### {fp.title}
- **Type**: {fp.type}
- **URL**: {fp.url}
- **Confidence**: {fp.confidence:.2f}
- **Reasoning**: {fp.ai_analysis.get('reasoning', 'N/A') if fp.ai_analysis else 'N/A'}
- **Source**: {fp.source_tool}

"""
        
        report += f"""
## Valid Findings Summary

"""
        
        for valid in valid_findings[:10]:  # Show first 10 valid findings
            report += f"""
- **{valid.title}** ({valid.severity}) - {valid.url}
"""
        
        if len(valid_findings) > 10:
            report += f"\n... and {len(valid_findings) - 10} more valid findings\n"
        
        return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-Powered False Positive Filter')
    parser.add_argument('--input', required=True, help='JSON file with findings')
    parser.add_argument('--output', help='Output file for filtered results')
    parser.add_argument('--report', help='Generate FP analysis report')
    
    args = parser.parse_args()
    
    async def process_findings():
        filter_system = AIFalsePositiveFilter()
        
        # Load findings
        with open(args.input, 'r') as f:
            findings = json.load(f)
        
        # Filter findings
        filtered_findings = await filter_system.filter_findings_batch(findings)
        
        # Save results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(filtered_findings, f, indent=2)
            print(f"✅ Filtered results saved to {args.output}")
        
        # Generate report
        if args.report:
            # Convert filtered findings back for report
            analyzed_findings = []
            for finding in filtered_findings:
                vf = VulnerabilityFindings(**finding)
                analyzed_findings.append(vf)
            
            report = filter_system.create_fp_report(analyzed_findings)
            with open(args.report, 'w') as f:
                f.write(report)
            print(f"✅ Analysis report saved to {args.report}")
    
    # Run async processing
    asyncio.run(process_findings())

if __name__ == "__main__":
    main()
