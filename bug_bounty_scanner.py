#!/usr/bin/env python3
"""
Bug Bounty Automation Framework v3.0
Main launcher with comprehensive options and enhanced user interface
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any

# Import all components
from tool_manager import ToolManager
from config_manager import ConfigManager
from ai_manager import AIManager
from updater import UpdateManager
from ai_vuln_scanner import AIVulnScanner
from tool_health_checker import ToolHealthChecker
from ai_model_installer import AIModelInstaller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BugBountyFramework:
    def __init__(self):
        self.version = "3.0"
        self.banner = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🚀 Bug Bounty Automation Framework v{self.version}                    ║
║                          AI-Enhanced Security Testing                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🎯 Automated vulnerability scanning with AI analysis                       ║
║  🤖 Multiple AI models for enhanced detection                               ║
║  📊 Professional HackerOne-ready reports                                    ║
║  🔄 Self-updating tools and templates                                       ║
║  ⚙️  Comprehensive configuration management                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        
        # Initialize managers
        try:
            self.tool_manager = ToolManager()
            self.config_manager = ConfigManager()
            self.ai_manager = AIManager()
            self.updater = UpdateManager()
        except Exception as e:
            logger.error(f"Failed to initialize managers: {e}")
            print("⚠️  Some components failed to initialize. Running setup...")
            self.run_first_time_setup()

    def print_banner(self):
        """Display the framework banner"""
        print(self.banner)
        print(f"📅 Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 Working Directory: {Path.cwd()}")
        print()

    def check_system_ready(self) -> bool:
        """Check if the system is ready for scanning with enhanced tool checking"""
        try:
            # Use enhanced tool health checker
            tool_checker = ToolHealthChecker()
            tool_status = tool_checker.get_comprehensive_status()
            
            # Check for missing required tools
            missing_required = [name for name, status in tool_status.items() 
                              if status['required'] and not status['installed']]
            
            if missing_required:
                print(f"⚠️  Missing required tools: {', '.join(missing_required)}")
                install = input("Install missing tools? (y/N): ").lower() == 'y'
                if install:
                    if tool_checker.install_missing_tools():
                        print("✅ All required tools installed")
                    else:
                        print("❌ Some tool installations failed")
                        return False
                else:
                    print("❌ Cannot proceed without required tools")
                    return False
            
            # Check configurations
            if not self.config_manager.all_configs_exist():
                print("⚠️  Configuration files missing.")
                setup = input("Run configuration setup? (y/N): ").lower() == 'y'
                if setup:
                    self.config_manager.run_setup_wizard()
                else:
                    return False
            
            # Check AI models availability
            ai_installer = AIModelInstaller()
            running, status = ai_installer.check_ollama_status()
            
            if not running and not ai_installer.get_installed_models():
                print("⚠️  No AI models available for enhanced analysis")
                install_ai = input("Install AI models for better vulnerability analysis? (y/N): ").lower() == 'y'
                if install_ai:
                    ai_installer.setup_ai_models(interactive=False)
            
            return True
            
        except Exception as e:
            logger.error(f"System readiness check failed: {e}")
            return False

    def run_first_time_setup(self):
        """Run first-time setup wizard"""
        print("\n🔧 First-Time Setup Wizard")
        print("=" * 50)
        
        # Check and install tools
        print("\n1️⃣  Checking security tools...")
        try:
            self.tool_manager = ToolManager()
            status = self.tool_manager.check_tool_status()
            
            missing = [name for name, info in status.items() 
                      if not info.get('installed', False)]
            
            if missing:
                print(f"Missing tools: {', '.join(missing)}")
                install = input("Install missing tools? (Y/n): ").lower() != 'n'
                if install:
                    self.tool_manager.install_missing_tools()
        except Exception as e:
            print(f"Tool setup failed: {e}")
        
        # Initialize configurations
        print("\n2️⃣  Setting up configurations...")
        try:
            self.config_manager = ConfigManager()
            self.config_manager.run_setup_wizard()
        except Exception as e:
            print(f"Configuration setup failed: {e}")
        
        # Initialize other managers
        try:
            self.ai_manager = AIManager()
            self.updater = UpdateManager()
        except Exception as e:
            print(f"Manager initialization failed: {e}")
        
        print("\n✅ Setup completed! You can now use the framework.")

    async def run_vulnerability_scan(self, target: str, options: Dict[str, Any]):
        """Run comprehensive vulnerability scan"""
        print(f"\n🎯 Starting vulnerability scan for: {target}")
        print("=" * 60)
        
        try:
            # Initialize scanner
            scanner = AIVulnScanner()
            
            # Perform scan
            results = await scanner.deep_scan_target(target)
            
            # Print summary
            print(f"\n🎉 Scan completed successfully!")
            print(f"📊 Vulnerabilities found: {len(results['vulnerabilities'])}")
            print(f"🔍 Subdomains discovered: {len(results['subdomains'])}")
            print(f"📈 Risk score: {results['severity_score']}/10")
            
            # Show vulnerability breakdown
            if results['vulnerabilities']:
                print("\n🚨 Vulnerability Summary:")
                severity_counts = {}
                for vuln in results['vulnerabilities']:
                    severity = vuln.get('severity', 'Unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                for severity, count in severity_counts.items():
                    emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
                    print(f"  {emoji} {severity}: {count}")
            
            # Email results if configured
            if options.get('email') and self.config_manager.load_config('email').get('enabled'):
                await self.send_email_report(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            print(f"❌ Scan failed: {e}")
            return None

    async def send_email_report(self, results: Dict[str, Any]):
        """Send email report if configured"""
        try:
            from send_email import EmailSender
            
            email_sender = EmailSender()
            if email_sender.send_vulnerability_report(results):
                print("📧 Email report sent successfully")
            else:
                print("⚠️  Failed to send email report")
        except ImportError:
            print("⚠️  Email module not available")
        except Exception as e:
            print(f"⚠️  Email sending failed: {e}")

    def show_system_status(self):
        """Display comprehensive system status"""
        print("\n🔍 System Status Report")
        print("=" * 60)
        
        try:
            # Tool status
            print("\n🛠️  Security Tools:")
            tool_status = self.tool_manager.check_tool_status()
            
            installed = sum(1 for status in tool_status.values() 
                          if status.get('installed', False))
            total = len(tool_status)
            
            print(f"  Installed: {installed}/{total}")
            
            for tool_name, status in tool_status.items():
                status_emoji = "✅" if status.get('installed') else "❌"
                version = status.get('version', 'Unknown')
                print(f"  {status_emoji} {tool_name}: {version}")
            
            # AI model status
            print("\n🤖 AI Models:")
            ai_status = self.ai_manager.get_model_status()
            
            for model_name, status in ai_status.items():
                status_emoji = "✅" if status.get('available') else "❌"
                print(f"  {status_emoji} {model_name.upper()}: {'Available' if status.get('available') else 'Unavailable'}")
                
                if model_name == 'ollama' and status.get('models'):
                    models = ', '.join(status['models'])
                    print(f"    Models: {models}")
            
            # Configuration status
            print("\n⚙️  Configurations:")
            config_status = self.config_manager.validate_all_configs()
            
            for config_name, valid in config_status.items():
                status_emoji = "✅" if valid else "❌"
                print(f"  {status_emoji} {config_name.title()}: {'Valid' if valid else 'Invalid'}")
            
            # System health
            health = self.updater.get_system_status().get('system_health', {})
            if 'error' not in health:
                print(f"\n🏥 Overall Health: {health.get('score', 0)}/100 ({health.get('status', 'Unknown')})")
            
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            print(f"❌ Status check failed: {e}")

    def run_update(self, component: str = None, force: bool = False):
        """Run system updates"""
        print("\n🔄 Running system updates...")
        
        try:
            if component == 'tools':
                success = self.updater.update_security_tools()
            elif component == 'templates':
                success = self.updater.update_nuclei_templates(force)
            else:
                success = self.updater.run_full_update(force)
            
            if success:
                print("✅ Updates completed successfully")
            else:
                print("⚠️  Some updates failed - check logs for details")
                
        except Exception as e:
            logger.error(f"Update failed: {e}")
            print(f"❌ Update failed: {e}")

    def run_configuration_wizard(self):
        """Run the configuration setup wizard"""
        try:
            self.config_manager.run_setup_wizard()
            print("✅ Configuration completed")
        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            print(f"❌ Configuration failed: {e}")

    async def install_ai_model(self):
        """Install recommended AI model"""
        try:
            print("🤖 Installing recommended AI model...")
            success = await self.ai_manager.install_recommended_model()
            
            if success:
                print("✅ AI model installed successfully")
            else:
                print("❌ AI model installation failed")
        except Exception as e:
            logger.error(f"AI model installation failed: {e}")
            print(f"❌ AI model installation failed: {e}")

    def show_help(self):
        """Display comprehensive help information"""
        help_text = f"""
🚀 Bug Bounty Automation Framework v{self.version} - Help Guide

BASIC USAGE:
  python3 bug_bounty_scanner.py scan <target>     # Run vulnerability scan
  python3 bug_bounty_scanner.py status            # Show system status
  python3 bug_bounty_scanner.py setup             # Run configuration wizard

SCAN OPTIONS:
  --email                    # Send results via email (if configured)
  --fast                     # Quick scan mode
  --thorough                 # Comprehensive scan mode
  --output-dir <path>        # Specify output directory

MANAGEMENT:
  python3 bug_bounty_scanner.py update            # Update all components
  python3 bug_bounty_scanner.py update --tools    # Update only tools
  python3 bug_bounty_scanner.py update --force    # Force update

CONFIGURATION:
  python3 bug_bounty_scanner.py config            # Run setup wizard
  python3 bug_bounty_scanner.py install-ai        # Install AI models

ADVANCED:
  python3 bug_bounty_scanner.py rollback          # Rollback updates
  python3 bug_bounty_scanner.py schedule          # Enable auto-updates
  python3 bug_bounty_scanner.py health            # System health check

EXAMPLES:
  # Basic scan
  python3 bug_bounty_scanner.py scan example.com

  # Thorough scan with email
  python3 bug_bounty_scanner.py scan example.com --thorough --email

  # Setup and status check
  python3 bug_bounty_scanner.py setup
  python3 bug_bounty_scanner.py status

For more information, visit: https://github.com/your-repo/bug-bounty-automation
        """
        print(help_text)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Bug Bounty Automation Framework v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Run vulnerability scan')
    scan_parser.add_argument('target', help='Target domain to scan')
    scan_parser.add_argument('--email', action='store_true', help='Send results via email')
    scan_parser.add_argument('--fast', action='store_true', help='Quick scan mode')
    scan_parser.add_argument('--thorough', action='store_true', help='Comprehensive scan mode')
    scan_parser.add_argument('--output-dir', help='Output directory for results')
    
    # Status command
    subparsers.add_parser('status', help='Show system status')
    
    # Setup command
    subparsers.add_parser('setup', help='Run first-time setup wizard')
    
    # Config command
    subparsers.add_parser('config', help='Run configuration wizard')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update system components')
    update_parser.add_argument('--tools', action='store_true', help='Update only tools')
    update_parser.add_argument('--templates', action='store_true', help='Update only templates')
    update_parser.add_argument('--force', action='store_true', help='Force update')
    
    # AI model command
    subparsers.add_parser('install-ai', help='Install recommended AI model')
    
    # Health command
    subparsers.add_parser('health', help='System health check')
    
    # Help command
    subparsers.add_parser('help', help='Show detailed help')
    
    args = parser.parse_args()
    
    # Initialize framework
    framework = BugBountyFramework()
    framework.print_banner()
    
    if not args.command:
        framework.show_help()
        return
    
    # Handle commands
    if args.command == 'scan':
        if not framework.check_system_ready():
            print("❌ System not ready for scanning. Please run setup first.")
            return
        
        options = {
            'email': args.email,
            'mode': 'thorough' if args.thorough else 'fast' if args.fast else 'normal',
            'output_dir': args.output_dir
        }
        
        await framework.run_vulnerability_scan(args.target, options)
    
    elif args.command == 'status':
        framework.show_system_status()
    
    elif args.command == 'setup':
        framework.run_first_time_setup()
    
    elif args.command == 'config':
        framework.run_configuration_wizard()
    
    elif args.command == 'update':
        component = None
        if args.tools:
            component = 'tools'
        elif args.templates:
            component = 'templates'
        
        framework.run_update(component, args.force)
    
    elif args.command == 'install-ai':
        await framework.install_ai_model()
    
    elif args.command == 'health':
        try:
            status = framework.updater.get_system_status()
            health = status.get('system_health', {})
            
            print(f"\n🏥 System Health Report")
            print("=" * 40)
            
            if 'error' not in health:
                score = health.get('score', 0)
                status_text = health.get('status', 'Unknown')
                
                print(f"Overall Health: {score}/100 ({status_text})")
                print(f"Tools: {health.get('tools_ratio', 'Unknown')}")
                print(f"AI Models: {health.get('ai_ratio', 'Unknown')}")
                print(f"Configurations: {health.get('config_ratio', 'Unknown')}")
                
                if score >= 90:
                    print("✅ System is in excellent condition")
                elif score >= 75:
                    print("✅ System is in good condition")
                elif score >= 60:
                    print("⚠️  System needs some attention")
                else:
                    print("❌ System requires immediate attention")
            else:
                print(f"❌ Health check failed: {health['error']}")
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    elif args.command == 'help':
        framework.show_help()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
