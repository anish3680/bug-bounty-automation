#!/usr/bin/env python3
"""
Enhanced Tool Health Checker for Bug Bounty Automation
Provides comprehensive tool detection, installation, and health monitoring
"""

import os
import subprocess
import sys
import json
import time
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests
from dataclasses import dataclass

@dataclass
class ToolInfo:
    name: str
    binary_name: str
    install_method: str
    check_command: List[str]
    install_command: List[str]
    version_command: List[str]
    required: bool = True
    description: str = ""

class ToolHealthChecker:
    def __init__(self):
        self.tools = {
            'nuclei': ToolInfo(
                name='Nuclei',
                binary_name='nuclei',
                install_method='go',
                check_command=['nuclei', '-version'],
                install_command=['go', 'install', 'github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest'],
                version_command=['nuclei', '-version'],
                description='Vulnerability scanner with 4000+ templates'
            ),
            'subfinder': ToolInfo(
                name='Subfinder',
                binary_name='subfinder',
                install_method='go',
                check_command=['subfinder', '-version'],
                install_command=['go', 'install', 'github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest'],
                version_command=['subfinder', '-version'],
                description='Subdomain discovery tool'
            ),
            'httpx': ToolInfo(
                name='HTTPx',
                binary_name='httpx',
                install_method='mixed',  # Can be installed via apt or go
                check_command=['httpx', '-version'],
                install_command=['go', 'install', 'github.com/projectdiscovery/httpx/cmd/httpx@latest'],
                version_command=['httpx', '-version'],
                description='HTTP toolkit and probe'
            ),
            'dalfox': ToolInfo(
                name='DalFox',
                binary_name='dalfox',
                install_method='go',
                check_command=['dalfox', 'version'],
                install_command=['go', 'install', 'github.com/hahwul/dalfox/v2@latest'],
                version_command=['dalfox', 'version'],
                description='XSS scanner and exploitation toolkit'
            ),
            'sqlmap': ToolInfo(
                name='SQLMap',
                binary_name='sqlmap',
                install_method='apt',
                check_command=['sqlmap', '--version'],
                install_command=['sudo', 'apt', 'update', '&&', 'sudo', 'apt', 'install', '-y', 'sqlmap'],
                version_command=['sqlmap', '--version'],
                description='SQL injection detection and exploitation'
            ),
            'nmap': ToolInfo(
                name='Nmap',
                binary_name='nmap',
                install_method='apt',
                check_command=['nmap', '--version'],
                install_command=['sudo', 'apt', 'update', '&&', 'sudo', 'apt', 'install', '-y', 'nmap'],
                version_command=['nmap', '--version'],
                description='Network discovery and security auditing'
            ),
            'whatweb': ToolInfo(
                name='WhatWeb',
                binary_name='whatweb',
                install_method='apt',
                check_command=['whatweb', '--version'],
                install_command=['sudo', 'apt', 'update', '&&', 'sudo', 'apt', 'install', '-y', 'whatweb'],
                version_command=['whatweb', '--version'],
                description='Web technology fingerprinting'
            ),
            'waybackurls': ToolInfo(
                name='Waybackurls',
                binary_name='waybackurls',
                install_method='go',
                check_command=['waybackurls', '-h'],
                install_command=['go', 'install', 'github.com/tomnomnom/waybackurls@latest'],
                version_command=['waybackurls', '-h'],
                description='Historical URL discovery via Wayback Machine'
            ),
            'gospider': ToolInfo(
                name='GoSpider',
                binary_name='gospider',
                install_method='go',
                check_command=['gospider', '-h'],
                install_command=['go', 'install', 'github.com/jaeles-project/gospider@latest'],
                version_command=['gospider', '-h'],
                description='Web crawler and spider'
            ),
            'gau': ToolInfo(
                name='GetAllUrls',
                binary_name='gau',
                install_method='go',
                check_command=['gau', '--version'],
                install_command=['go', 'install', 'github.com/lc/gau/v2/cmd/gau@latest'],
                version_command=['gau', '--version'],
                description='Fetch URLs from various sources'
            ),
            'amass': ToolInfo(
                name='Amass',
                binary_name='amass',
                install_method='go',
                check_command=['amass', '--version'],
                install_command=['go', 'install', 'github.com/owasp-amass/amass/v4/...@latest'],
                version_command=['amass', '--version'],
                description='Attack surface mapping and asset discovery',
                required=False  # Optional tool
            )
        }
        
        self.go_bin_path = os.path.expanduser('~/go/bin')
        self.local_bin_path = os.path.expanduser('~/.local/bin')
        
        # Ensure go bin is in PATH
        if self.go_bin_path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = f"{self.go_bin_path}:{os.environ.get('PATH', '')}"

    def check_go_installed(self) -> bool:
        """Check if Go is installed and properly configured"""
        try:
            result = subprocess.run(['go', 'version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Go installed: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print("❌ Go not found or not properly configured")
        return False

    def install_go_tool(self, tool_info: ToolInfo) -> bool:
        """Install a Go-based tool"""
        print(f"🔄 Installing {tool_info.name} via Go...")
        
        try:
            # Run the go install command
            result = subprocess.run(
                tool_info.install_command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                print(f"✅ {tool_info.name} installed successfully")
                return True
            else:
                print(f"❌ Failed to install {tool_info.name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Installation of {tool_info.name} timed out")
            return False
        except Exception as e:
            print(f"❌ Error installing {tool_info.name}: {e}")
            return False

    def install_apt_tool(self, tool_info: ToolInfo) -> bool:
        """Install an apt-based tool"""
        print(f"🔄 Installing {tool_info.name} via apt...")
        
        try:
            # Update package list first
            subprocess.run(['sudo', 'apt', 'update'], check=True, capture_output=True)
            
            # Install the tool
            cmd = ['sudo', 'apt', 'install', '-y', tool_info.binary_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ {tool_info.name} installed successfully")
                return True
            else:
                print(f"❌ Failed to install {tool_info.name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Installation of {tool_info.name} timed out")
            return False
        except Exception as e:
            print(f"❌ Error installing {tool_info.name}: {e}")
            return False

    def check_tool_installed(self, tool_info: ToolInfo) -> Tuple[bool, str]:
        """Check if a specific tool is installed and get version"""
        try:
            # First check if binary exists in common paths
            binary_path = shutil.which(tool_info.binary_name)
            if binary_path:
                # Try to get version
                result = subprocess.run(
                    tool_info.check_command,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 or 'version' in result.stdout.lower() or 'v' in result.stdout:
                    version = result.stdout.strip() or result.stderr.strip()
                    return True, version
            
            return False, "Not found"
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            return False, f"Error: {e}"

    def get_comprehensive_status(self) -> Dict[str, Dict]:
        """Get comprehensive status of all tools"""
        print("🔍 Checking tool installation status...")
        print("=" * 60)
        
        status = {}
        missing_required = []
        
        for tool_name, tool_info in self.tools.items():
            installed, version = self.check_tool_installed(tool_info)
            
            status[tool_name] = {
                'name': tool_info.name,
                'installed': installed,
                'version': version,
                'required': tool_info.required,
                'description': tool_info.description,
                'install_method': tool_info.install_method
            }
            
            # Print status
            status_emoji = "✅" if installed else ("🔴" if tool_info.required else "🟡")
            required_text = " (Required)" if tool_info.required else " (Optional)"
            
            print(f"{status_emoji} {tool_info.name}{required_text}")
            if installed:
                print(f"   Version: {version}")
            else:
                print(f"   Status: Not installed")
                if tool_info.required:
                    missing_required.append(tool_name)
            
            print(f"   Description: {tool_info.description}")
            print()
        
        # Summary
        total_tools = len(self.tools)
        installed_count = sum(1 for s in status.values() if s['installed'])
        required_count = sum(1 for s in status.values() if s['required'])
        required_installed = sum(1 for s in status.values() if s['required'] and s['installed'])
        
        print("📊 Summary:")
        print(f"   Total tools: {total_tools}")
        print(f"   Installed: {installed_count}/{total_tools}")
        print(f"   Required installed: {required_installed}/{required_count}")
        
        if missing_required:
            print(f"   ❌ Missing required tools: {', '.join(missing_required)}")
        else:
            print("   ✅ All required tools are installed")
        
        return status

    def install_missing_tools(self, auto_install: bool = False) -> bool:
        """Install missing tools with user confirmation"""
        status = self.get_comprehensive_status()
        
        missing_tools = [
            (name, info) for name, tool_status in status.items() 
            for info in [self.tools[name]] 
            if not tool_status['installed'] and tool_status['required']
        ]
        
        if not missing_tools:
            print("✅ All required tools are already installed!")
            return True
        
        print(f"\n🔧 Found {len(missing_tools)} missing required tools:")
        for name, tool_info in missing_tools:
            print(f"   - {tool_info.name} ({tool_info.description})")
        
        if not auto_install:
            response = input(f"\nInstall {len(missing_tools)} missing tools? (y/N): ").lower()
            if response not in ['y', 'yes']:
                print("❌ Installation cancelled")
                return False
        
        # Check prerequisites
        if any(tool_info.install_method == 'go' for _, tool_info in missing_tools):
            if not self.check_go_installed():
                print("❌ Go is required but not installed. Please install Go first.")
                return False
        
        # Install each missing tool
        success_count = 0
        for name, tool_info in missing_tools:
            print(f"\n{'='*50}")
            print(f"Installing {tool_info.name}...")
            
            if tool_info.install_method == 'go':
                if self.install_go_tool(tool_info):
                    success_count += 1
            elif tool_info.install_method in ['apt', 'mixed']:
                if self.install_apt_tool(tool_info):
                    success_count += 1
            else:
                print(f"⚠️  Unknown install method for {tool_info.name}")
        
        print(f"\n{'='*50}")
        print(f"📊 Installation complete: {success_count}/{len(missing_tools)} tools installed")
        
        # Verify installations
        if success_count > 0:
            print("\n🔍 Verifying installations...")
            time.sleep(2)  # Give time for binaries to be available
            self.get_comprehensive_status()
        
        return success_count == len(missing_tools)

    def update_nuclei_templates(self) -> bool:
        """Update Nuclei templates"""
        print("🔄 Updating Nuclei templates...")
        
        try:
            result = subprocess.run(
                ['nuclei', '-update-templates'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ Nuclei templates updated successfully")
                return True
            else:
                print(f"❌ Failed to update Nuclei templates: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Nuclei template update timed out")
            return False
        except Exception as e:
            print(f"❌ Error updating Nuclei templates: {e}")
            return False

    def create_health_report(self) -> Dict:
        """Create a comprehensive health report"""
        status = self.get_comprehensive_status()
        
        # Calculate health score
        total_required = sum(1 for s in status.values() if s['required'])
        installed_required = sum(1 for s in status.values() if s['required'] and s['installed'])
        
        health_score = (installed_required / total_required * 100) if total_required > 0 else 100
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'health_score': health_score,
            'tool_status': status,
            'summary': {
                'total_tools': len(status),
                'installed_tools': sum(1 for s in status.values() if s['installed']),
                'required_tools': total_required,
                'required_installed': installed_required,
                'missing_required': [
                    name for name, s in status.items() 
                    if s['required'] and not s['installed']
                ]
            },
            'recommendations': self.get_recommendations(status)
        }
        
        return report

    def get_recommendations(self, status: Dict) -> List[str]:
        """Get recommendations based on current tool status"""
        recommendations = []
        
        missing_required = [name for name, s in status.items() if s['required'] and not s['installed']]
        if missing_required:
            recommendations.append(
                f"Install missing required tools: {', '.join(missing_required)}"
            )
        
        # Check if Go tools need updating
        go_tools = [name for name, s in status.items() if s['install_method'] == 'go' and s['installed']]
        if go_tools:
            recommendations.append("Consider updating Go-based tools regularly")
        
        # Check if Nuclei templates need updating
        if status.get('nuclei', {}).get('installed'):
            recommendations.append("Update Nuclei templates weekly for latest vulnerability checks")
        
        if not missing_required:
            recommendations.append("All required tools are installed - system is ready for scanning")
        
        return recommendations

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Bug Bounty Tool Health Checker')
    parser.add_argument('--status', action='store_true', help='Check tool status')
    parser.add_argument('--install', action='store_true', help='Install missing tools')
    parser.add_argument('--auto', action='store_true', help='Auto-install without confirmation')
    parser.add_argument('--update-templates', action='store_true', help='Update Nuclei templates')
    parser.add_argument('--report', action='store_true', help='Generate health report')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    checker = ToolHealthChecker()
    
    if args.install:
        checker.install_missing_tools(auto_install=args.auto)
    elif args.update_templates:
        checker.update_nuclei_templates()
    elif args.report:
        report = checker.create_health_report()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"\n🏥 Tool Health Report")
            print(f"Health Score: {report['health_score']:.1f}%")
            print("\n📋 Recommendations:")
            for rec in report['recommendations']:
                print(f"   - {rec}")
    else:
        # Default: show status
        checker.get_comprehensive_status()

if __name__ == "__main__":
    main()
