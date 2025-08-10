#!/usr/bin/env python3
"""
Tool Management System for Bug Bounty Automation
Handles installation, updates, and validation of security tools
"""

import os
import sys
import subprocess
import requests
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor
import platform
import zipfile
import tarfile
import tempfile
from urllib.parse import urlparse
import stat

class ToolManager:
    def __init__(self):
        self.home_dir = Path.home()
        self.go_bin = self.home_dir / "go" / "bin"
        self.local_bin = Path("/usr/local/bin")
        self.user_bin = self.home_dir / ".local" / "bin"
        
        # Ensure directories exist
        self.go_bin.mkdir(parents=True, exist_ok=True)
        self.user_bin.mkdir(parents=True, exist_ok=True)
        
        # Tool definitions with installation methods
        self.tools = {
            'nuclei': {
                'binary_name': 'nuclei',
                'install_method': 'go',
                'go_package': 'github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest',
                'check_command': ['nuclei', '-version'],
                'description': 'Fast vulnerability scanner',
                'required': True
            },
            'subfinder': {
                'binary_name': 'subfinder', 
                'install_method': 'go',
                'go_package': 'github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest',
                'check_command': ['subfinder', '-version'],
                'description': 'Subdomain discovery tool',
                'required': True
            },
            'httpx': {
                'binary_name': 'httpx',
                'install_method': 'go', 
                'go_package': 'github.com/projectdiscovery/httpx/cmd/httpx@latest',
                'check_command': ['httpx', '-version'],
                'description': 'HTTP toolkit',
                'required': True
            },
            'dalfox': {
                'binary_name': 'dalfox',
                'install_method': 'go',
                'go_package': 'github.com/hahwul/dalfox/v2@latest',
                'check_command': ['dalfox', 'version'],
                'description': 'XSS scanner',
                'required': True
            },
            'waybackurls': {
                'binary_name': 'waybackurls',
                'install_method': 'go',
                'go_package': 'github.com/tomnomnom/waybackurls@latest',
                'check_command': ['waybackurls', '-h'],
                'description': 'Wayback machine URL fetcher',
                'required': False
            },
            'gospider': {
                'binary_name': 'gospider',
                'install_method': 'go',
                'go_package': 'github.com/jaeles-project/gospider@latest',
                'check_command': ['gospider', '-h'],
                'description': 'Web crawler',
                'required': False
            },
            'gau': {
                'binary_name': 'gau',
                'install_method': 'go',
                'go_package': 'github.com/lc/gau/v2/cmd/gau@latest',
                'check_command': ['gau', '-h'],
                'description': 'Get All URLs',
                'required': False
            },
            'whatweb': {
                'binary_name': 'whatweb',
                'install_method': 'package',
                'package_name': 'whatweb',
                'check_command': ['whatweb', '--version'],
                'description': 'Web technology identifier',
                'required': False
            },
            'sqlmap': {
                'binary_name': 'sqlmap',
                'install_method': 'package',
                'package_name': 'sqlmap',
                'check_command': ['sqlmap', '--version'],
                'description': 'SQL injection tool',
                'required': True
            },
            'nmap': {
                'binary_name': 'nmap',
                'install_method': 'package',
                'package_name': 'nmap',
                'check_command': ['nmap', '--version'],
                'description': 'Network scanner',
                'required': True
            },
            'amass': {
                'binary_name': 'amass',
                'install_method': 'snap',
                'package_name': 'amass',
                'check_command': ['amass', 'version'],
                'description': 'Attack surface mapping',
                'required': False
            }
        }
        
        # Additional wordlists and data
        self.wordlists = {
            'SecLists': {
                'url': 'https://github.com/danielmiessler/SecLists/archive/refs/heads/master.zip',
                'extract_to': self.home_dir / 'wordlists' / 'SecLists',
                'description': 'Security wordlists collection'
            },
            'PayloadsAllTheThings': {
                'url': 'https://github.com/swisskyrepo/PayloadsAllTheThings/archive/refs/heads/master.zip', 
                'extract_to': self.home_dir / 'wordlists' / 'PayloadsAllTheThings',
                'description': 'Payload collection for security testing'
            }
        }

    def check_tool_status(self) -> Dict[str, Dict]:
        """Check status of all tools"""
        print("🔍 Checking tool installation status...")
        status = {}
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for tool_name, tool_config in self.tools.items():
                future = executor.submit(self._check_single_tool, tool_name, tool_config)
                futures[future] = tool_name
            
            for future in futures:
                tool_name = futures[future]
                try:
                    status[tool_name] = future.result()
                except Exception as e:
                    status[tool_name] = {
                        'installed': False,
                        'version': 'Error',
                        'error': str(e),
                        'path': None
                    }
        
        return status

    def _check_single_tool(self, tool_name: str, tool_config: Dict) -> Dict:
        """Check if a single tool is installed"""
        try:
            # Try to find the binary
            binary_path = shutil.which(tool_config['binary_name'])
            if not binary_path:
                # Check in go/bin directory
                go_binary = self.go_bin / tool_config['binary_name']
                if go_binary.exists():
                    binary_path = str(go_binary)
                else:
                    return {
                        'installed': False,
                        'version': None,
                        'path': None,
                        'description': tool_config['description']
                    }
            
            # Try to get version
            try:
                result = subprocess.run(
                    tool_config['check_command'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                version_output = result.stdout + result.stderr
                version = self._extract_version(version_output)
            except:
                version = "Unknown"
            
            return {
                'installed': True,
                'version': version,
                'path': binary_path,
                'description': tool_config['description']
            }
            
        except Exception as e:
            return {
                'installed': False,
                'version': None,
                'path': None,
                'error': str(e),
                'description': tool_config['description']
            }

    def _extract_version(self, version_output: str) -> str:
        """Extract version from command output"""
        import re
        
        # Common version patterns
        patterns = [
            r'v?(\d+\.\d+\.\d+)',
            r'version[:\s]+v?(\d+\.\d+\.\d+)',
            r'(\d+\.\d+\.\d+)',
            r'v(\d+\.\d+)',
            r'(\d+\.\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, version_output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"

    def install_missing_tools(self, force: bool = False) -> bool:
        """Install all missing tools"""
        print("📦 Installing missing security tools...")
        
        status = self.check_tool_status()
        to_install = []
        
        for tool_name, tool_status in status.items():
            if not tool_status['installed'] or force:
                to_install.append(tool_name)
        
        if not to_install:
            print("✅ All tools are already installed!")
            return True
        
        print(f"Installing {len(to_install)} tools: {', '.join(to_install)}")
        
        success_count = 0
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for tool_name in to_install:
                future = executor.submit(self._install_single_tool, tool_name)
                futures[future] = tool_name
            
            for future in futures:
                tool_name = futures[future]
                try:
                    success = future.result()
                    if success:
                        print(f"✅ {tool_name} installed successfully")
                        success_count += 1
                    else:
                        print(f"❌ Failed to install {tool_name}")
                except Exception as e:
                    print(f"❌ Error installing {tool_name}: {e}")
        
        print(f"Installation complete: {success_count}/{len(to_install)} tools installed")
        return success_count == len(to_install)

    def _install_single_tool(self, tool_name: str) -> bool:
        """Install a single tool"""
        tool_config = self.tools[tool_name]
        
        try:
            if tool_config['install_method'] == 'go':
                return self._install_go_tool(tool_name, tool_config)
            elif tool_config['install_method'] == 'package':
                return self._install_package_tool(tool_name, tool_config)
            elif tool_config['install_method'] == 'snap':
                return self._install_snap_tool(tool_name, tool_config)
            elif tool_config['install_method'] == 'github':
                return self._install_github_tool(tool_name, tool_config)
            else:
                print(f"Unknown install method for {tool_name}")
                return False
                
        except Exception as e:
            print(f"Error installing {tool_name}: {e}")
            return False

    def _install_go_tool(self, tool_name: str, tool_config: Dict) -> bool:
        """Install Go-based tool"""
        try:
            # Check if Go is installed
            go_path = shutil.which('go')
            if not go_path:
                print(f"Go not found, cannot install {tool_name}")
                return False
            
            # Install using go install
            cmd = ['go', 'install', '-v', tool_config['go_package']]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Verify installation
                binary_path = self.go_bin / tool_config['binary_name']
                if binary_path.exists():
                    # Make sure it's executable
                    os.chmod(binary_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                    return True
            
            print(f"Go install failed for {tool_name}: {result.stderr}")
            return False
            
        except subprocess.TimeoutExpired:
            print(f"Go install timeout for {tool_name}")
            return False
        except Exception as e:
            print(f"Go install error for {tool_name}: {e}")
            return False

    def _install_package_tool(self, tool_name: str, tool_config: Dict) -> bool:
        """Install package manager tool"""
        try:
            # Try different package managers
            package_managers = [
                ['apt', 'install', '-y'],
                ['yum', 'install', '-y'],
                ['dnf', 'install', '-y'],
                ['pacman', '-S', '--noconfirm'],
                ['zypper', 'install', '-y']
            ]
            
            for pm in package_managers:
                pm_binary = shutil.which(pm[0])
                if pm_binary:
                    cmd = pm + [tool_config['package_name']]
                    try:
                        # Check if we need sudo
                        if os.geteuid() != 0:
                            cmd = ['sudo'] + cmd
                        
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                        if result.returncode == 0:
                            return True
                        else:
                            print(f"Package install failed: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        print(f"Package install timeout for {tool_name}")
                        continue
            
            print(f"No suitable package manager found for {tool_name}")
            return False
            
        except Exception as e:
            print(f"Package install error for {tool_name}: {e}")
            return False

    def _install_snap_tool(self, tool_name: str, tool_config: Dict) -> bool:
        """Install snap package"""
        try:
            snap_path = shutil.which('snap')
            if not snap_path:
                print(f"Snap not available for {tool_name}")
                return False
            
            cmd = ['sudo', 'snap', 'install', tool_config['package_name']]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Snap install error for {tool_name}: {e}")
            return False

    def update_tools(self) -> bool:
        """Update all installed tools"""
        print("🔄 Updating security tools...")
        
        # Update nuclei templates
        self._update_nuclei_templates()
        
        # Update go tools
        self._update_go_tools()
        
        # Update package manager tools
        self._update_packages()
        
        return True

    def _update_nuclei_templates(self):
        """Update nuclei templates"""
        try:
            nuclei_path = shutil.which('nuclei') or str(self.go_bin / 'nuclei')
            if os.path.exists(nuclei_path):
                print("Updating nuclei templates...")
                subprocess.run([nuclei_path, '-update-templates'], 
                             capture_output=True, timeout=60)
        except Exception as e:
            print(f"Failed to update nuclei templates: {e}")

    def _update_go_tools(self):
        """Update Go-based tools"""
        print("Updating Go tools...")
        go_tools = [name for name, config in self.tools.items() 
                   if config['install_method'] == 'go']
        
        for tool_name in go_tools:
            try:
                tool_config = self.tools[tool_name]
                cmd = ['go', 'install', '-v', tool_config['go_package']]
                subprocess.run(cmd, capture_output=True, timeout=120)
                print(f"Updated {tool_name}")
            except Exception as e:
                print(f"Failed to update {tool_name}: {e}")

    def _update_packages(self):
        """Update system packages"""
        try:
            # Try apt first (most common)
            if shutil.which('apt'):
                subprocess.run(['sudo', 'apt', 'update'], capture_output=True)
                subprocess.run(['sudo', 'apt', 'upgrade', '-y'], capture_output=True)
        except Exception as e:
            print(f"Failed to update packages: {e}")

    def install_wordlists(self) -> bool:
        """Install common wordlists"""
        print("📚 Installing security wordlists...")
        
        success_count = 0
        for name, config in self.wordlists.items():
            try:
                if self._download_and_extract(name, config):
                    print(f"✅ {name} installed")
                    success_count += 1
                else:
                    print(f"❌ Failed to install {name}")
            except Exception as e:
                print(f"❌ Error installing {name}: {e}")
        
        return success_count == len(self.wordlists)

    def _download_and_extract(self, name: str, config: Dict) -> bool:
        """Download and extract wordlist archives"""
        try:
            extract_path = config['extract_to']
            
            # Skip if already exists
            if extract_path.exists():
                print(f"{name} already exists at {extract_path}")
                return True
            
            # Create parent directory
            extract_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download
            response = requests.get(config['url'], stream=True, timeout=300)
            response.raise_for_status()
            
            # Save to temp file and extract
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            try:
                if config['url'].endswith('.zip'):
                    with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path.parent)
                        # Rename extracted folder to match expected name
                        extracted_name = zip_ref.namelist()[0].split('/')[0]
                        if extracted_name != extract_path.name:
                            os.rename(extract_path.parent / extracted_name, extract_path)
                elif config['url'].endswith(('.tar.gz', '.tgz')):
                    with tarfile.open(tmp_path, 'r:gz') as tar_ref:
                        tar_ref.extractall(extract_path.parent)
                
                return extract_path.exists()
                
            finally:
                os.unlink(tmp_path)
                
        except Exception as e:
            print(f"Failed to download {name}: {e}")
            return False

    def print_status_report(self):
        """Print comprehensive tool status report"""
        print("\n" + "="*80)
        print("🛠️  SECURITY TOOLS STATUS REPORT")
        print("="*80)
        
        status = self.check_tool_status()
        
        installed = []
        missing = []
        
        for tool_name, tool_status in status.items():
            tool_config = self.tools[tool_name]
            required = "🔴 REQUIRED" if tool_config.get('required', False) else "🟡 Optional"
            
            if tool_status['installed']:
                installed.append({
                    'name': tool_name,
                    'version': tool_status['version'],
                    'path': tool_status['path'],
                    'description': tool_status['description'],
                    'required': tool_config.get('required', False)
                })
            else:
                missing.append({
                    'name': tool_name,
                    'description': tool_status['description'],
                    'required': tool_config.get('required', False)
                })
        
        # Print installed tools
        if installed:
            print(f"\n✅ INSTALLED TOOLS ({len(installed)}):")
            print("-" * 50)
            for tool in sorted(installed, key=lambda x: (not x['required'], x['name'])):
                req_marker = "🔴" if tool['required'] else "🟡"
                print(f"{req_marker} {tool['name']:15} | v{tool['version']:10} | {tool['description']}")
                print(f"   └─ Path: {tool['path']}")
        
        # Print missing tools  
        if missing:
            print(f"\n❌ MISSING TOOLS ({len(missing)}):")
            print("-" * 50)
            for tool in sorted(missing, key=lambda x: (not x['required'], x['name'])):
                req_marker = "🔴" if tool['required'] else "🟡"
                print(f"{req_marker} {tool['name']:15} | {tool['description']}")
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tools: {len(self.tools)}")
        print(f"   Installed:   {len(installed)}")
        print(f"   Missing:     {len(missing)}")
        
        required_missing = sum(1 for tool in missing if tool['required'])
        if required_missing > 0:
            print(f"   🔴 CRITICAL: {required_missing} required tools missing!")
        else:
            print(f"   ✅ All required tools installed")
        
        print("\n" + "="*80)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Tools Manager")
    parser.add_argument('--install', action='store_true', help='Install missing tools')
    parser.add_argument('--update', action='store_true', help='Update existing tools')
    parser.add_argument('--wordlists', action='store_true', help='Install wordlists')
    parser.add_argument('--status', action='store_true', help='Show tool status')
    parser.add_argument('--force', action='store_true', help='Force reinstallation')
    
    args = parser.parse_args()
    
    manager = ToolManager()
    
    if args.status or (not any(vars(args).values())):
        manager.print_status_report()
    
    if args.install:
        manager.install_missing_tools(force=args.force)
    
    if args.update:
        manager.update_tools()
    
    if args.wordlists:
        manager.install_wordlists()
