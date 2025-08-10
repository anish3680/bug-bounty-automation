#!/usr/bin/env python3
"""
Configuration Management System for Bug Bounty Automation
Handles setup, validation, and management of all configurations
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import getpass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import subprocess

class ConfigManager:
    def __init__(self):
        self.config_dir = Path(__file__).parent / 'config'
        self.config_dir.mkdir(exist_ok=True)
        
        # Configuration file paths
        self.email_config_path = self.config_dir / 'email_config.json'
        self.ai_config_path = self.config_dir / 'ai_config.json'
        self.tools_config_path = self.config_dir / 'tools_config.json'
        self.scanner_config_path = self.config_dir / 'scanner_config.json'
        
        # Default configurations
        self.default_configs = {
            'email': {
                'enabled': False,
                'smtp_server': '',
                'smtp_port': 587,
                'email': '',
                'password': '',
                'recipient': '',
                'use_tls': True,
                'timeout': 30
            },
            'ai': {
                'ollama': {
                    'enabled': True,
                    'endpoint': 'http://localhost:11434/api/generate',
                    'model': 'llama3.2:3b',
                    'timeout': 30
                },
                'huggingface': {
                    'enabled': True,
                    'api_key': '',
                    'models': [
                        'microsoft/DialoGPT-medium',
                        'microsoft/CodeBERT-base',
                        'facebook/bart-large'
                    ]
                },
                'groq': {
                    'enabled': True,
                    'api_key': '',
                    'endpoint': 'https://api.groq.com/openai/v1/chat/completions'
                },
                'openai': {
                    'enabled': False,
                    'api_key': '',
                    'model': 'gpt-3.5-turbo'
                }
            },
            'tools': {
                'nuclei': {
                    'threads': 25,
                    'rate_limit': 150,
                    'timeout': 5,
                    'severity': ['critical', 'high', 'medium'],
                    'templates_dir': str(Path.home() / 'nuclei-templates')
                },
                'subfinder': {
                    'threads': 10,
                    'timeout': 30,
                    'sources': ['all']
                },
                'httpx': {
                    'threads': 50,
                    'timeout': 10,
                    'retries': 2,
                    'follow_redirects': True
                },
                'sqlmap': {
                    'threads': 5,
                    'level': 1,
                    'risk': 1,
                    'timeout': 30
                },
                'dalfox': {
                    'threads': 10,
                    'delay': 2,
                    'timeout': 10
                }
            },
            'scanner': {
                'max_concurrent_scans': 3,
                'default_timeout': 300,
                'output_format': 'json',
                'save_raw_output': True,
                'auto_update_tools': True,
                'vulnerability_threshold': 'medium',
                'generate_reports': True,
                'report_formats': ['html', 'json', 'markdown']
            }
        }

    def run_setup_wizard(self):
        """Interactive setup wizard for first-time configuration"""
        print("🔧 Bug Bounty Automation - Configuration Setup Wizard")
        print("=" * 60)
        
        if self.all_configs_exist():
            print("📋 Existing configuration detected.")
            choice = input("Do you want to reconfigure? (y/N): ").lower()
            if choice != 'y':
                return
        
        print("\n1️⃣  Setting up Email Configuration...")
        self._setup_email_config()
        
        print("\n2️⃣  Setting up AI Configuration...")
        self._setup_ai_config()
        
        print("\n3️⃣  Setting up Tool Configuration...")
        self._setup_tools_config()
        
        print("\n4️⃣  Setting up Scanner Configuration...")
        self._setup_scanner_config()
        
        print("\n✅ Configuration setup complete!")
        print("🚀 You can now run the bug bounty scanner.")
        
        # Test configurations
        print("\n🧪 Testing configurations...")
        self.validate_all_configs()

    def _setup_email_config(self):
        """Setup email configuration"""
        config = self.default_configs['email'].copy()
        
        print("\n📧 Email Configuration (Optional - for report delivery)")
        enable = input("Enable email reports? (y/N): ").lower() == 'y'
        config['enabled'] = enable
        
        if enable:
            config['email'] = input("Your email address: ")
            config['password'] = getpass.getpass("Email password (or app password): ")
            config['recipient'] = input("Recipient email (default: same as sender): ") or config['email']
            
            # Auto-detect SMTP settings
            domain = config['email'].split('@')[-1].lower()
            smtp_settings = {
                'gmail.com': ('smtp.gmail.com', 587),
                'outlook.com': ('smtp-mail.outlook.com', 587),
                'hotmail.com': ('smtp-mail.outlook.com', 587),
                'yahoo.com': ('smtp.mail.yahoo.com', 587),
                'icloud.com': ('smtp.mail.me.com', 587)
            }
            
            if domain in smtp_settings:
                config['smtp_server'], config['smtp_port'] = smtp_settings[domain]
                print(f"✅ Auto-detected SMTP: {config['smtp_server']}:{config['smtp_port']}")
            else:
                config['smtp_server'] = input("SMTP server: ")
                config['smtp_port'] = int(input("SMTP port (587): ") or "587")
        
        self.save_config('email', config)

    def _setup_ai_config(self):
        """Setup AI configuration"""
        config = self.default_configs['ai'].copy()
        
        print("\n🤖 AI Configuration")
        print("AI models are used for vulnerability analysis and report generation.")
        
        # Ollama setup
        print("\n🦙 Ollama (Local AI Model)")
        if self._check_ollama_running():
            print("✅ Ollama is running")
            models = self._get_ollama_models()
            if models:
                print(f"Available models: {', '.join(models)}")
                model_choice = input("Choose model (default: llama3.2:3b): ") or "llama3.2:3b"
                config['ollama']['model'] = model_choice
            else:
                print("⚠️  No models installed")
                install = input("Install recommended model (llama3.2:3b)? (y/N): ").lower() == 'y'
                if install:
                    self._install_ollama_model("llama3.2:3b")
        else:
            print("❌ Ollama not running or not installed")
            config['ollama']['enabled'] = False
        
        # API keys (optional)
        print("\n🔑 API Keys (Optional - improves AI analysis quality)")
        groq_key = input("Groq API key (free tier available): ").strip()
        if groq_key:
            config['groq']['api_key'] = groq_key
        
        openai_key = input("OpenAI API key (optional): ").strip()
        if openai_key:
            config['openai']['enabled'] = True
            config['openai']['api_key'] = openai_key
        
        self.save_config('ai', config)

    def _setup_tools_config(self):
        """Setup tools configuration"""
        config = self.default_configs['tools'].copy()
        
        print("\n🛠️  Tool Configuration")
        print("Using recommended defaults for optimal performance.")
        
        # Ask for performance preferences
        performance = input("Performance mode (fast/balanced/thorough) [balanced]: ").lower() or "balanced"
        
        if performance == "fast":
            config['nuclei']['threads'] = 50
            config['nuclei']['rate_limit'] = 300
            config['httpx']['threads'] = 100
        elif performance == "thorough":
            config['nuclei']['threads'] = 10
            config['nuclei']['rate_limit'] = 50
            config['httpx']['threads'] = 20
            config['sqlmap']['level'] = 3
            config['sqlmap']['risk'] = 2
        
        self.save_config('tools', config)

    def _setup_scanner_config(self):
        """Setup scanner configuration"""
        config = self.default_configs['scanner'].copy()
        
        print("\n📊 Scanner Configuration")
        
        # Vulnerability threshold
        threshold = input("Minimum vulnerability severity to report (low/medium/high) [medium]: ") or "medium"
        config['vulnerability_threshold'] = threshold
        
        # Report formats
        print("Available report formats: html, json, markdown, pdf")
        formats = input("Report formats (comma-separated) [html,json,markdown]: ") or "html,json,markdown"
        config['report_formats'] = [f.strip() for f in formats.split(',')]
        
        self.save_config('scanner', config)

    def validate_all_configs(self) -> Dict[str, bool]:
        """Validate all configurations"""
        results = {
            'email': self.validate_email_config(),
            'ai': self.validate_ai_config(),
            'tools': self.validate_tools_config(),
            'scanner': self.validate_scanner_config()
        }
        
        for config_name, valid in results.items():
            status = "✅" if valid else "❌"
            print(f"{status} {config_name.capitalize()} configuration")
        
        return results

    def validate_email_config(self) -> bool:
        """Validate email configuration"""
        try:
            config = self.load_config('email')
            if not config.get('enabled', False):
                return True  # Email is optional
            
            required_fields = ['email', 'password', 'smtp_server', 'smtp_port']
            if not all(config.get(field) for field in required_fields):
                print("❌ Missing required email fields")
                return False
            
            # Test SMTP connection
            try:
                server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
                if config.get('use_tls', True):
                    server.starttls()
                server.login(config['email'], config['password'])
                server.quit()
                print("✅ Email SMTP connection successful")
                return True
            except Exception as e:
                print(f"❌ Email SMTP test failed: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Email config validation error: {e}")
            return False

    def validate_ai_config(self) -> bool:
        """Validate AI configuration"""
        try:
            config = self.load_config('ai')
            valid_endpoints = 0
            
            # Test Ollama
            if config['ollama']['enabled']:
                if self._test_ollama():
                    valid_endpoints += 1
                    print("✅ Ollama endpoint working")
                else:
                    print("❌ Ollama endpoint failed")
            
            # Test Groq
            if config['groq']['api_key']:
                if self._test_groq_api(config['groq']['api_key']):
                    valid_endpoints += 1
                    print("✅ Groq API working")
                else:
                    print("❌ Groq API failed")
            
            # Test OpenAI
            if config['openai']['enabled'] and config['openai']['api_key']:
                if self._test_openai_api(config['openai']['api_key']):
                    valid_endpoints += 1
                    print("✅ OpenAI API working")
                else:
                    print("❌ OpenAI API failed")
            
            # At least one AI endpoint should work
            return valid_endpoints > 0
            
        except Exception as e:
            print(f"❌ AI config validation error: {e}")
            return False

    def validate_tools_config(self) -> bool:
        """Validate tools configuration"""
        try:
            config = self.load_config('tools')
            # Basic validation - check if required tools are available
            from tool_manager import ToolManager
            
            tool_manager = ToolManager()
            status = tool_manager.check_tool_status()
            
            required_tools = ['nuclei', 'subfinder', 'httpx', 'sqlmap', 'nmap']
            missing_required = [tool for tool in required_tools 
                              if not status.get(tool, {}).get('installed', False)]
            
            if missing_required:
                print(f"❌ Missing required tools: {', '.join(missing_required)}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Tools config validation error: {e}")
            return False

    def validate_scanner_config(self) -> bool:
        """Validate scanner configuration"""
        try:
            config = self.load_config('scanner')
            
            # Check threshold
            valid_thresholds = ['low', 'medium', 'high', 'critical']
            if config.get('vulnerability_threshold', 'medium') not in valid_thresholds:
                print("❌ Invalid vulnerability threshold")
                return False
            
            # Check report formats
            valid_formats = ['html', 'json', 'markdown', 'pdf']
            report_formats = config.get('report_formats', [])
            if not all(fmt in valid_formats for fmt in report_formats):
                print("❌ Invalid report format specified")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Scanner config validation error: {e}")
            return False

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load configuration by name"""
        config_files = {
            'email': self.email_config_path,
            'ai': self.ai_config_path,
            'tools': self.tools_config_path,
            'scanner': self.scanner_config_path
        }
        
        config_path = config_files.get(config_name)
        if not config_path or not config_path.exists():
            return self.default_configs.get(config_name, {})
        
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {config_name} config: {e}")
            return self.default_configs.get(config_name, {})

    def save_config(self, config_name: str, config_data: Dict[str, Any]):
        """Save configuration by name"""
        config_files = {
            'email': self.email_config_path,
            'ai': self.ai_config_path,
            'tools': self.tools_config_path,
            'scanner': self.scanner_config_path
        }
        
        config_path = config_files.get(config_name)
        if not config_path:
            raise ValueError(f"Unknown config name: {config_name}")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"✅ Saved {config_name} configuration")
        except Exception as e:
            print(f"❌ Failed to save {config_name} config: {e}")

    def all_configs_exist(self) -> bool:
        """Check if all configuration files exist"""
        config_files = [
            self.email_config_path,
            self.ai_config_path,
            self.tools_config_path,
            self.scanner_config_path
        ]
        return all(path.exists() for path in config_files)

    def _check_ollama_running(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get('http://localhost:11434/api/version', timeout=5)
            return response.status_code == 200
        except:
            return False

    def _get_ollama_models(self) -> List[str]:
        """Get list of installed Ollama models"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = [line.split()[0] for line in lines if line.strip()]
                return models
            return []
        except:
            return []

    def _install_ollama_model(self, model_name: str) -> bool:
        """Install Ollama model"""
        try:
            print(f"Installing {model_name} (this may take a while)...")
            result = subprocess.run(['ollama', 'pull', model_name], 
                                  capture_output=True, text=True, timeout=600)
            return result.returncode == 0
        except:
            return False

    def _test_ollama(self) -> bool:
        """Test Ollama endpoint"""
        try:
            response = requests.post('http://localhost:11434/api/generate',
                                   json={'model': 'llama3.2:3b', 'prompt': 'test', 'stream': False},
                                   timeout=10)
            return response.status_code == 200
        except:
            return False

    def _test_groq_api(self, api_key: str) -> bool:
        """Test Groq API"""
        try:
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get('https://api.groq.com/openai/v1/models', 
                                  headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False

    def _test_openai_api(self, api_key: str) -> bool:
        """Test OpenAI API"""
        try:
            headers = {'Authorization': f'Bearer {api_key}'}
            response = requests.get('https://api.openai.com/v1/models', 
                                  headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False

    def reset_config(self, config_name: Optional[str] = None):
        """Reset configuration to defaults"""
        if config_name:
            if config_name in self.default_configs:
                self.save_config(config_name, self.default_configs[config_name])
                print(f"✅ Reset {config_name} configuration to defaults")
            else:
                print(f"❌ Unknown configuration: {config_name}")
        else:
            # Reset all configs
            for name, default_config in self.default_configs.items():
                self.save_config(name, default_config)
            print("✅ Reset all configurations to defaults")

    def export_config(self, output_path: str):
        """Export all configurations to a file"""
        try:
            all_configs = {}
            for config_name in self.default_configs.keys():
                all_configs[config_name] = self.load_config(config_name)
            
            with open(output_path, 'w') as f:
                json.dump(all_configs, f, indent=2)
            print(f"✅ Exported configuration to {output_path}")
        except Exception as e:
            print(f"❌ Failed to export configuration: {e}")

    def import_config(self, config_path: str):
        """Import configurations from a file"""
        try:
            with open(config_path, 'r') as f:
                all_configs = json.load(f)
            
            for config_name, config_data in all_configs.items():
                if config_name in self.default_configs:
                    self.save_config(config_name, config_data)
            
            print(f"✅ Imported configuration from {config_path}")
        except Exception as e:
            print(f"❌ Failed to import configuration: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bug Bounty Automation Config Manager")
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    parser.add_argument('--validate', action='store_true', help='Validate configurations')
    parser.add_argument('--reset', type=str, nargs='?', const='all', help='Reset config (specify name or "all")')
    parser.add_argument('--export', type=str, help='Export config to file')
    parser.add_argument('--import', type=str, dest='import_file', help='Import config from file')
    
    args = parser.parse_args()
    
    manager = ConfigManager()
    
    if args.setup:
        manager.run_setup_wizard()
    elif args.validate:
        manager.validate_all_configs()
    elif args.reset:
        if args.reset == 'all':
            manager.reset_config()
        else:
            manager.reset_config(args.reset)
    elif args.export:
        manager.export_config(args.export)
    elif args.import_file:
        manager.import_config(args.import_file)
    else:
        print("Use --setup to run the configuration wizard")
