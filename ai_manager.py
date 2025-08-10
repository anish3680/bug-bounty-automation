#!/usr/bin/env python3
"""
AI Model Management System for Bug Bounty Automation
Handles AI model optimization, fallback chains, and enhanced analysis
"""

import requests
import json
import asyncio
import aiohttp
import subprocess
import os
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from config_manager import ConfigManager

@dataclass
class AIResponse:
    content: str
    model: str
    confidence: float
    processing_time: float
    error: Optional[str] = None

class AIManager:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.ai_config = self.config_manager.load_config('ai')
        
        # Model priority order (best to worst)
        self.model_priority = [
            'openai',
            'groq', 
            'ollama',
            'huggingface',
            'fallback'
        ]
        
        # Specialized prompts for different analysis types
        self.prompts = {
            'vulnerability_analysis': """
            As a cybersecurity expert, analyze this potential vulnerability:
            
            Target: {target}
            Vulnerability Type: {vuln_type}
            Evidence: {evidence}
            Technical Details: {details}
            
            Provide a comprehensive analysis including:
            1. SEVERITY (Critical/High/Medium/Low) with justification
            2. EXPLOITABILITY assessment (Easy/Medium/Hard)
            3. BUSINESS IMPACT analysis
            4. TECHNICAL RISK assessment
            5. REMEDIATION steps (specific and actionable)
            6. CVSS v3.1 score estimation if applicable
            
            Format your response as JSON:
            {{
                "severity": "string",
                "exploitability": "string", 
                "business_impact": "string",
                "technical_risk": "string",
                "remediation": ["step1", "step2", ...],
                "cvss_score": "number or null",
                "confidence": "number (0-1)"
            }}
            """,
            
            'report_generation': """
            Generate a professional HackerOne vulnerability report for:
            
            Vulnerability: {vuln_type}
            Target: {target}
            Severity: {severity}
            Evidence: {evidence}
            Technical Analysis: {analysis}
            
            Create a well-structured report with:
            1. Clear, concise title
            2. Executive summary
            3. Detailed description
            4. Step-by-step reproduction
            5. Impact assessment
            6. Recommendations
            7. Supporting evidence
            
            Format as professional security report suitable for bug bounty submission.
            """,
            
            'false_positive_check': """
            Evaluate if this is a false positive vulnerability:
            
            Finding: {finding}
            Evidence: {evidence}
            Context: {context}
            
            Consider:
            1. Is this a real security vulnerability?
            2. Could this be a false positive from automated tools?
            3. What additional verification is needed?
            4. Risk assessment if legitimate
            
            Respond with JSON:
            {{
                "is_false_positive": boolean,
                "confidence": number (0-1),
                "reasoning": "string",
                "additional_checks": ["check1", "check2", ...]
            }}
            """,
            
            'payload_generation': """
            Generate advanced security testing payloads for {vuln_type} on {target}.
            
            Context:
            - Target details: {target_info}
            - Known protections: {protections}
            - Previous attempts: {previous_attempts}
            
            Provide 5 sophisticated payloads that:
            1. Bypass common protections
            2. Are specific to the target technology
            3. Test edge cases
            4. Demonstrate real impact
            5. Follow responsible disclosure principles
            
            Format as JSON array with explanations.
            """
        }

    async def analyze_vulnerability(self, vuln_data: Dict[str, Any]) -> AIResponse:
        """Comprehensive vulnerability analysis using AI models"""
        prompt = self.prompts['vulnerability_analysis'].format(
            target=vuln_data.get('target', 'Unknown'),
            vuln_type=vuln_data.get('type', 'Unknown'),
            evidence=vuln_data.get('evidence', 'None provided'),
            details=vuln_data.get('details', 'None provided')
        )
        
        # Try models in priority order
        for model_name in self.model_priority:
            try:
                response = await self._query_model(model_name, prompt)
                if response and not response.error:
                    # Parse and enhance the response
                    enhanced_response = await self._enhance_analysis(response, vuln_data)
                    return enhanced_response
            except Exception as e:
                print(f"[AI] {model_name} failed: {e}")
                continue
        
        # Fallback response
        return self._create_fallback_analysis(vuln_data)

    async def generate_report(self, vuln_data: Dict[str, Any], analysis: AIResponse) -> str:
        """Generate professional vulnerability report"""
        prompt = self.prompts['report_generation'].format(
            vuln_type=vuln_data.get('type', 'Security Issue'),
            target=vuln_data.get('target', 'Target System'),
            severity=analysis.content.get('severity', 'Medium') if isinstance(analysis.content, dict) else 'Medium',
            evidence=vuln_data.get('evidence', 'See technical details'),
            analysis=analysis.content
        )
        
        response = await self._query_best_available_model(prompt)
        return response.content if response else self._generate_fallback_report(vuln_data)

    async def check_false_positive(self, finding: Dict[str, Any]) -> AIResponse:
        """Check if finding is a false positive"""
        prompt = self.prompts['false_positive_check'].format(
            finding=finding.get('description', ''),
            evidence=finding.get('evidence', ''),
            context=finding.get('context', '')
        )
        
        response = await self._query_best_available_model(prompt)
        return response if response else self._create_fallback_fp_check()

    async def generate_payloads(self, vuln_type: str, target_info: Dict[str, Any]) -> List[str]:
        """Generate advanced testing payloads"""
        prompt = self.prompts['payload_generation'].format(
            vuln_type=vuln_type,
            target=target_info.get('url', 'unknown'),
            target_info=json.dumps(target_info, indent=2),
            protections=target_info.get('protections', 'Unknown'),
            previous_attempts=target_info.get('previous_attempts', 'None')
        )
        
        response = await self._query_best_available_model(prompt)
        
        if response:
            try:
                payloads = json.loads(response.content)
                return payloads if isinstance(payloads, list) else []
            except:
                # Parse text-based response
                return self._parse_payload_response(response.content)
        
        return self._get_default_payloads(vuln_type)

    async def _query_model(self, model_name: str, prompt: str) -> Optional[AIResponse]:
        """Query a specific AI model"""
        start_time = time.time()
        
        try:
            if model_name == 'openai' and self._is_openai_enabled():
                return await self._query_openai(prompt, start_time)
            elif model_name == 'groq' and self._is_groq_enabled():
                return await self._query_groq(prompt, start_time)
            elif model_name == 'ollama' and self._is_ollama_enabled():
                return await self._query_ollama(prompt, start_time)
            elif model_name == 'huggingface':
                return await self._query_huggingface(prompt, start_time)
            else:
                return None
                
        except Exception as e:
            return AIResponse(
                content="", 
                model=model_name, 
                confidence=0.0,
                processing_time=time.time() - start_time,
                error=str(e)
            )

    async def _query_best_available_model(self, prompt: str) -> Optional[AIResponse]:
        """Query the best available AI model"""
        for model_name in self.model_priority:
            response = await self._query_model(model_name, prompt)
            if response and not response.error:
                return response
        return None

    async def _query_openai(self, prompt: str, start_time: float) -> AIResponse:
        """Query OpenAI API"""
        headers = {
            'Authorization': f"Bearer {self.ai_config['openai']['api_key']}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.ai_config['openai'].get('model', 'gpt-3.5-turbo'),
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 2000,
            'temperature': 0.1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    return AIResponse(
                        content=content,
                        model='openai',
                        confidence=0.9,
                        processing_time=time.time() - start_time
                    )
                else:
                    raise Exception(f"OpenAI API error: {response.status}")

    async def _query_groq(self, prompt: str, start_time: float) -> AIResponse:
        """Query Groq API"""
        api_key = self.ai_config['groq'].get('api_key')
        if not api_key:
            raise Exception("Groq API key not configured")
        
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': 'llama3-8b-8192',  # Groq's fast model
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 2000,
            'temperature': 0.1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.ai_config['groq']['endpoint'],
                headers=headers,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    return AIResponse(
                        content=content,
                        model='groq',
                        confidence=0.8,
                        processing_time=time.time() - start_time
                    )
                else:
                    raise Exception(f"Groq API error: {response.status}")

    async def _query_ollama(self, prompt: str, start_time: float) -> AIResponse:
        """Query local Ollama model"""
        payload = {
            'model': self.ai_config['ollama'].get('model', 'llama3.2:3b'),
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': 0.1,
                'num_predict': 2000
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.ai_config['ollama']['endpoint'],
                json=payload,
                timeout=60
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('response', '')
                    return AIResponse(
                        content=content,
                        model='ollama',
                        confidence=0.7,
                        processing_time=time.time() - start_time
                    )
                else:
                    raise Exception(f"Ollama error: {response.status}")

    async def _query_huggingface(self, prompt: str, start_time: float) -> AIResponse:
        """Query HuggingFace Inference API (free tier)"""
        # Use a text generation model
        api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        
        payload = {
            'inputs': prompt,
            'options': {'wait_for_model': True},
            'parameters': {
                'max_length': 500,
                'temperature': 0.1
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url,
                json=payload,
                timeout=30
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Handle HuggingFace response format
                    if isinstance(data, list) and len(data) > 0:
                        content = data[0].get('generated_text', '')
                    else:
                        content = str(data)
                    
                    return AIResponse(
                        content=content,
                        model='huggingface',
                        confidence=0.6,
                        processing_time=time.time() - start_time
                    )
                else:
                    raise Exception(f"HuggingFace error: {response.status}")

    def _is_openai_enabled(self) -> bool:
        """Check if OpenAI is enabled and configured"""
        return (self.ai_config.get('openai', {}).get('enabled', False) and
                bool(self.ai_config.get('openai', {}).get('api_key')))

    def _is_groq_enabled(self) -> bool:
        """Check if Groq is enabled and configured"""
        return (self.ai_config.get('groq', {}).get('enabled', True) and
                bool(self.ai_config.get('groq', {}).get('api_key')))

    def _is_ollama_enabled(self) -> bool:
        """Check if Ollama is enabled and running"""
        if not self.ai_config.get('ollama', {}).get('enabled', True):
            return False
        
        try:
            response = requests.get('http://localhost:11434/api/version', timeout=5)
            return response.status_code == 200
        except:
            return False

    async def _enhance_analysis(self, response: AIResponse, vuln_data: Dict[str, Any]) -> AIResponse:
        """Enhance AI response with additional analysis"""
        try:
            # Try to parse JSON response
            if response.content.strip().startswith('{'):
                parsed_content = json.loads(response.content)
                
                # Add additional fields
                parsed_content['target'] = vuln_data.get('target', 'Unknown')
                parsed_content['scan_timestamp'] = time.time()
                parsed_content['ai_model'] = response.model
                parsed_content['ai_confidence'] = response.confidence
                
                # Validate and normalize severity
                severity = parsed_content.get('severity', 'Medium').title()
                if severity not in ['Critical', 'High', 'Medium', 'Low', 'Info']:
                    parsed_content['severity'] = 'Medium'
                else:
                    parsed_content['severity'] = severity
                
                response.content = parsed_content
                
        except json.JSONDecodeError:
            # Keep original content if not JSON
            pass
        
        return response

    def _create_fallback_analysis(self, vuln_data: Dict[str, Any]) -> AIResponse:
        """Create fallback analysis when AI is unavailable"""
        vuln_type = vuln_data.get('type', 'Unknown').lower()
        
        # Basic severity mapping
        severity_map = {
            'sql injection': 'High',
            'xss': 'Medium', 
            'cross-site scripting': 'Medium',
            'lfi': 'Medium',
            'rfi': 'High',
            'ssrf': 'Medium',
            'command injection': 'Critical',
            'path traversal': 'Medium'
        }
        
        severity = severity_map.get(vuln_type, 'Medium')
        
        fallback_content = {
            'severity': severity,
            'exploitability': 'Medium',
            'business_impact': 'Potential security compromise',
            'technical_risk': 'Requires manual verification',
            'remediation': [
                'Validate and sanitize all user inputs',
                'Implement proper access controls',
                'Apply security patches',
                'Conduct security testing'
            ],
            'cvss_score': None,
            'confidence': 0.3,
            'note': 'Fallback analysis - manual review recommended'
        }
        
        return AIResponse(
            content=fallback_content,
            model='fallback',
            confidence=0.3,
            processing_time=0.1
        )

    def _create_fallback_fp_check(self) -> AIResponse:
        """Create fallback false positive check"""
        return AIResponse(
            content={
                'is_false_positive': False,
                'confidence': 0.5,
                'reasoning': 'Manual verification required - AI unavailable',
                'additional_checks': [
                    'Manual testing required',
                    'Verify with security expert',
                    'Cross-reference with known issues'
                ]
            },
            model='fallback',
            confidence=0.5,
            processing_time=0.1
        )

    def _generate_fallback_report(self, vuln_data: Dict[str, Any]) -> str:
        """Generate fallback report when AI is unavailable"""
        return f"""
# Vulnerability Report - {vuln_data.get('type', 'Security Issue')}

**Target:** {vuln_data.get('target', 'Unknown')}
**Severity:** {vuln_data.get('severity', 'Medium')}

## Description
A potential {vuln_data.get('type', 'security vulnerability')} has been identified.

## Evidence
{vuln_data.get('evidence', 'See technical analysis for details.')}

## Recommendation
Manual verification and analysis required. Please review the findings and implement appropriate security measures.

---
*Note: This is an automated fallback report. Enhanced analysis requires AI model availability.*
        """

    def _parse_payload_response(self, content: str) -> List[str]:
        """Parse payload response from text format"""
        payloads = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                payloads.append(line)
        
        return payloads[:10]  # Limit to 10 payloads

    def _get_default_payloads(self, vuln_type: str) -> List[str]:
        """Get default payloads for vulnerability type"""
        default_payloads = {
            'xss': [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "'\"><script>alert('XSS')</script>",
                "<svg onload=alert('XSS')>"
            ],
            'sql injection': [
                "' OR '1'='1",
                "admin'--",
                "' UNION SELECT NULL--",
                "1; DROP TABLE users--",
                "' OR 1=1#"
            ],
            'lfi': [
                "../../../etc/passwd",
                "....//....//....//etc/passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "....\\\\....\\\\....\\\\windows\\\\system32\\\\drivers\\\\etc\\\\hosts"
            ]
        }
        
        return default_payloads.get(vuln_type.lower(), ['test_payload'])

    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all AI models"""
        status = {}
        
        for model_name in ['openai', 'groq', 'ollama', 'huggingface']:
            try:
                if model_name == 'openai':
                    status[model_name] = {
                        'available': self._is_openai_enabled(),
                        'configured': bool(self.ai_config.get('openai', {}).get('api_key')),
                        'priority': 1
                    }
                elif model_name == 'groq':
                    status[model_name] = {
                        'available': self._is_groq_enabled(),
                        'configured': bool(self.ai_config.get('groq', {}).get('api_key')),
                        'priority': 2
                    }
                elif model_name == 'ollama':
                    status[model_name] = {
                        'available': self._is_ollama_enabled(),
                        'configured': True,
                        'priority': 3,
                        'models': self._get_ollama_models()
                    }
                else:  # huggingface
                    status[model_name] = {
                        'available': True,  # Always available (free tier)
                        'configured': True,
                        'priority': 4
                    }
            except Exception as e:
                status[model_name] = {
                    'available': False,
                    'error': str(e),
                    'priority': 99
                }
        
        return status

    def _get_ollama_models(self) -> List[str]:
        """Get list of installed Ollama models"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                return [line.split()[0] for line in lines if line.strip()]
            return []
        except:
            return []

    async def install_recommended_model(self) -> bool:
        """Install recommended Ollama model"""
        try:
            print("Installing recommended Ollama model (llama3.2:3b)...")
            result = subprocess.run(
                ['ollama', 'pull', 'llama3.2:3b'], 
                capture_output=True, 
                text=True, 
                timeout=600
            )
            
            success = result.returncode == 0
            if success:
                print("✅ Model installed successfully")
                # Update config
                self.ai_config['ollama']['model'] = 'llama3.2:3b'
                self.config_manager.save_config('ai', self.ai_config)
            else:
                print(f"❌ Model installation failed: {result.stderr}")
            
            return success
        except subprocess.TimeoutExpired:
            print("❌ Model installation timed out")
            return False
        except Exception as e:
            print(f"❌ Model installation error: {e}")
            return False

if __name__ == "__main__":
    import argparse
    import asyncio
    
    async def main():
        parser = argparse.ArgumentParser(description="AI Model Manager")
        parser.add_argument('--status', action='store_true', help='Show AI model status')
        parser.add_argument('--install-model', action='store_true', help='Install recommended model')
        parser.add_argument('--test', action='store_true', help='Test AI models')
        
        args = parser.parse_args()
        
        manager = AIManager()
        
        if args.status:
            status = manager.get_model_status()
            print("\n🤖 AI Model Status:")
            print("=" * 50)
            
            for model, info in status.items():
                status_emoji = "✅" if info['available'] else "❌"
                print(f"{status_emoji} {model.upper()}: {'Available' if info['available'] else 'Unavailable'}")
                if 'models' in info:
                    print(f"   Models: {', '.join(info['models']) or 'None installed'}")
                if info.get('error'):
                    print(f"   Error: {info['error']}")
                print()
        
        elif args.install_model:
            await manager.install_recommended_model()
        
        elif args.test:
            # Test vulnerability analysis
            test_vuln = {
                'type': 'SQL Injection',
                'target': 'https://example.com/search?q=test',
                'evidence': "Error: You have an error in your SQL syntax",
                'details': 'Parameter "q" appears vulnerable to SQL injection'
            }
            
            print("🧪 Testing AI vulnerability analysis...")
            response = await manager.analyze_vulnerability(test_vuln)
            print(f"Model used: {response.model}")
            print(f"Confidence: {response.confidence}")
            print(f"Processing time: {response.processing_time:.2f}s")
            print(f"Content: {response.content}")
        else:
            print("Use --status, --install-model, or --test")
    
    asyncio.run(main())
