#!/usr/bin/env python3
"""
AI Model Auto-Installer for Bug Bounty Automation
Handles automatic installation and management of AI models
"""

import os
import subprocess
import requests
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil
import tempfile

class AIModelInstaller:
    def __init__(self):
        self.ollama_endpoint = "http://localhost:11434"
        self.recommended_models = [
            {
                'name': 'llama3.2:3b',
                'size': '2.0GB',
                'description': 'Fast and efficient for vulnerability analysis',
                'recommended': True
            },
            {
                'name': 'codellama:7b',
                'size': '3.8GB', 
                'description': 'Specialized for code analysis and security',
                'recommended': True
            },
            {
                'name': 'mistral:7b',
                'size': '4.1GB',
                'description': 'General purpose model with good reasoning',
                'recommended': False
            },
            {
                'name': 'llama3.2:1b',
                'size': '1.3GB',
                'description': 'Lightweight model for resource-constrained systems',
                'recommended': False
            }
        ]
        
        # Free API endpoints that don't require API keys
        self.free_api_endpoints = {
            'huggingface': {
                'models': [
                    'microsoft/DialoGPT-medium',
                    'facebook/blenderbot-400M-distill',
                    'microsoft/CodeBERT-base'
                ],
                'endpoint': 'https://api-inference.huggingface.co/models/',
                'description': 'Free inference API (no API key required)'
            }
        }

    def check_ollama_status(self) -> Tuple[bool, str]:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=5)
            if response.status_code == 200:
                return True, "Running"
            else:
                return False, f"HTTP {response.status_code}"
        except requests.ConnectionError:
            return False, "Not running"
        except Exception as e:
            return False, f"Error: {e}"

    def install_ollama(self) -> bool:
        """Install Ollama if not present"""
        print("🦙 Installing Ollama...")
        
        try:
            # Check if already installed
            if shutil.which('ollama'):
                print("✅ Ollama already installed")
                return True
            
            # Download and install Ollama
            print("📥 Downloading Ollama installer...")
            
            install_cmd = [
                'curl', '-fsSL', 'https://ollama.ai/install.sh', '|', 'sh'
            ]
            
            # Use shell=True for pipe operation
            result = subprocess.run(
                'curl -fsSL https://ollama.ai/install.sh | sh',
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ Ollama installed successfully")
                
                # Start Ollama service
                print("🔄 Starting Ollama service...")
                subprocess.run(['ollama', 'serve'], check=False)
                time.sleep(3)  # Give it time to start
                
                return True
            else:
                print(f"❌ Failed to install Ollama: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Ollama installation timed out")
            return False
        except Exception as e:
            print(f"❌ Error installing Ollama: {e}")
            return False

    def start_ollama_service(self) -> bool:
        """Start Ollama service"""
        print("🔄 Starting Ollama service...")
        
        try:
            # Try to start as background process
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            
            # Wait and check if it started
            time.sleep(5)
            running, status = self.check_ollama_status()
            
            if running:
                print("✅ Ollama service started successfully")
                return True
            else:
                print(f"❌ Failed to start Ollama service: {status}")
                return False
                
        except Exception as e:
            print(f"❌ Error starting Ollama service: {e}")
            return False

    def get_installed_models(self) -> List[str]:
        """Get list of installed Ollama models"""
        try:
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception:
            return []

    def install_ollama_model(self, model_name: str) -> bool:
        """Install a specific Ollama model"""
        print(f"📦 Installing model: {model_name}")
        print("⏳ This may take several minutes depending on model size...")
        
        try:
            # Use ollama pull command
            result = subprocess.run(
                ['ollama', 'pull', model_name],
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout for large models
            )
            
            if result.returncode == 0:
                print(f"✅ Model {model_name} installed successfully")
                return True
            else:
                print(f"❌ Failed to install {model_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Installation of {model_name} timed out")
            return False
        except Exception as e:
            print(f"❌ Error installing {model_name}: {e}")
            return False

    def test_model(self, model_name: str) -> bool:
        """Test if a model is working"""
        print(f"🧪 Testing model: {model_name}")
        
        try:
            test_prompt = "What is cybersecurity?"
            
            response = requests.post(
                f"{self.ollama_endpoint}/api/generate",
                json={
                    'model': model_name,
                    'prompt': test_prompt,
                    'stream': False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and len(data['response'].strip()) > 10:
                    print(f"✅ Model {model_name} is working correctly")
                    return True
            
            print(f"❌ Model {model_name} test failed")
            return False
            
        except Exception as e:
            print(f"❌ Error testing {model_name}: {e}")
            return False

    def get_system_resources(self) -> Dict[str, float]:
        """Get system resources to recommend appropriate models"""
        try:
            import psutil
            
            # Get available memory
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            total_gb = memory.total / (1024**3)
            
            # Get available disk space
            disk = psutil.disk_usage('/')
            disk_free_gb = disk.free / (1024**3)
            
            return {
                'memory_available_gb': available_gb,
                'memory_total_gb': total_gb,
                'disk_free_gb': disk_free_gb
            }
        except ImportError:
            print("⚠️  psutil not available, using default resource estimates")
            return {
                'memory_available_gb': 8.0,
                'memory_total_gb': 16.0,
                'disk_free_gb': 50.0
            }
        except Exception:
            return {
                'memory_available_gb': 4.0,
                'memory_total_gb': 8.0,
                'disk_free_gb': 20.0
            }

    def recommend_models_for_system(self) -> List[Dict]:
        """Recommend models based on system resources"""
        resources = self.get_system_resources()
        
        print(f"📊 System Resources:")
        print(f"   Available Memory: {resources['memory_available_gb']:.1f} GB")
        print(f"   Total Memory: {resources['memory_total_gb']:.1f} GB")
        print(f"   Free Disk Space: {resources['disk_free_gb']:.1f} GB")
        
        recommended = []
        
        # Filter models based on available resources
        for model in self.recommended_models:
            model_size_gb = float(model['size'].replace('GB', ''))
            
            # Check if we have enough disk space (with 2GB buffer)
            if resources['disk_free_gb'] >= model_size_gb + 2:
                # Check if we have enough memory (rough estimate: model size * 1.5 for runtime)
                estimated_memory_need = model_size_gb * 1.5
                
                if resources['memory_available_gb'] >= estimated_memory_need:
                    model['suitable'] = True
                    model['reason'] = "Suitable for your system"
                else:
                    model['suitable'] = False
                    model['reason'] = f"May need {estimated_memory_need:.1f}GB RAM"
                    
                recommended.append(model)
            else:
                model['suitable'] = False
                model['reason'] = f"Needs {model_size_gb}GB disk space"
                recommended.append(model)
        
        return recommended

    def setup_ai_models(self, interactive: bool = True) -> bool:
        """Complete AI model setup process"""
        print("🤖 AI Model Setup Wizard")
        print("=" * 50)
        
        # Step 1: Check/Install Ollama
        running, status = self.check_ollama_status()
        
        if not running:
            print(f"❌ Ollama status: {status}")
            
            if not shutil.which('ollama'):
                if not interactive or input("Install Ollama? (y/N): ").lower() == 'y':
                    if not self.install_ollama():
                        print("❌ Failed to install Ollama")
                        return False
                else:
                    print("❌ Ollama installation cancelled")
                    return False
            else:
                # Ollama installed but not running
                if not self.start_ollama_service():
                    print("❌ Failed to start Ollama service")
                    return False
        else:
            print(f"✅ Ollama status: {status}")
        
        # Step 2: Check existing models
        installed_models = self.get_installed_models()
        print(f"\n📦 Currently installed models: {len(installed_models)}")
        
        if installed_models:
            for model in installed_models:
                print(f"   ✅ {model}")
        
        # Step 3: Recommend models based on system
        print(f"\n🎯 Model Recommendations:")
        recommendations = self.recommend_models_for_system()
        
        models_to_install = []
        
        for model in recommendations:
            status_icon = "✅" if model['suitable'] else "⚠️"
            rec_text = " (RECOMMENDED)" if model['recommended'] and model['suitable'] else ""
            
            print(f"{status_icon} {model['name']} - {model['size']}{rec_text}")
            print(f"   {model['description']}")
            print(f"   Status: {model['reason']}")
            
            # Auto-select suitable recommended models or ask user
            if model['suitable'] and model['recommended']:
                if model['name'] not in installed_models:
                    if not interactive:
                        models_to_install.append(model['name'])
                        print(f"   → Will install automatically")
                    elif input(f"   Install {model['name']}? (Y/n): ").lower() != 'n':
                        models_to_install.append(model['name'])
            
            print()
        
        # Step 4: Install selected models
        if models_to_install:
            print(f"🚀 Installing {len(models_to_install)} models...")
            
            success_count = 0
            for model_name in models_to_install:
                if self.install_ollama_model(model_name):
                    if self.test_model(model_name):
                        success_count += 1
                    else:
                        print(f"⚠️  {model_name} installed but failed test")
                else:
                    print(f"❌ Failed to install {model_name}")
            
            print(f"\n📊 Installation Summary: {success_count}/{len(models_to_install)} models working")
            
            if success_count > 0:
                print("✅ AI models are ready for vulnerability analysis!")
                return True
            else:
                print("❌ No models were successfully installed")
                return False
        
        elif installed_models:
            print("✅ Using existing models")
            # Test at least one existing model
            for model in installed_models[:1]:  # Test first model
                if self.test_model(model):
                    print("✅ AI models are ready!")
                    return True
            
            print("⚠️  Existing models may not be working properly")
            return False
        
        else:
            print("❌ No AI models available")
            return False

    def create_ai_config(self) -> Dict:
        """Create AI configuration based on available models"""
        config = {
            'ollama': {
                'enabled': False,
                'endpoint': self.ollama_endpoint,
                'model': '',
                'available_models': []
            },
            'huggingface': {
                'enabled': True,
                'api_key': '',  # Not required for free inference
                'models': self.free_api_endpoints['huggingface']['models']
            },
            'groq': {
                'enabled': False,  # Requires API key
                'api_key': '',
                'endpoint': 'https://api.groq.com/openai/v1/chat/completions'
            },
            'openai': {
                'enabled': False,  # Requires API key
                'api_key': '',
                'model': 'gpt-3.5-turbo'
            }
        }
        
        # Check Ollama models
        running, _ = self.check_ollama_status()
        if running:
            installed_models = self.get_installed_models()
            if installed_models:
                config['ollama']['enabled'] = True
                config['ollama']['model'] = installed_models[0]  # Use first model as default
                config['ollama']['available_models'] = installed_models
        
        return config

    def save_config(self, config: Dict, config_path: str):
        """Save AI configuration to file"""
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✅ AI configuration saved to {config_path}")
        except Exception as e:
            print(f"❌ Failed to save config: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Model Installer for Bug Bounty Automation')
    parser.add_argument('--install', action='store_true', help='Run full AI setup')
    parser.add_argument('--auto', action='store_true', help='Auto-install without prompts')
    parser.add_argument('--status', action='store_true', help='Check AI model status')
    parser.add_argument('--test', type=str, help='Test specific model')
    parser.add_argument('--config', type=str, help='Save config to specific path')
    
    args = parser.parse_args()
    
    installer = AIModelInstaller()
    
    if args.status:
        running, status = installer.check_ollama_status()
        print(f"Ollama Status: {status}")
        
        if running:
            models = installer.get_installed_models()
            print(f"Installed Models: {len(models)}")
            for model in models:
                print(f"   - {model}")
        
        # Check system resources
        resources = installer.get_system_resources()
        print(f"\nSystem Resources:")
        print(f"   Available Memory: {resources['memory_available_gb']:.1f} GB")
        print(f"   Free Disk Space: {resources['disk_free_gb']:.1f} GB")
    
    elif args.test:
        if installer.test_model(args.test):
            print(f"✅ Model {args.test} is working")
        else:
            print(f"❌ Model {args.test} failed test")
    
    elif args.install:
        success = installer.setup_ai_models(interactive=not args.auto)
        
        if success and args.config:
            config = installer.create_ai_config()
            installer.save_config(config, args.config)
        
        sys.exit(0 if success else 1)
    
    else:
        # Default: show recommendations
        print("🤖 AI Model Recommendations")
        installer.recommend_models_for_system()

if __name__ == "__main__":
    main()
