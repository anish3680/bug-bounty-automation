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
import getpass
import hashlib

# Import all components
from tool_manager import ToolManager
from ai_manager import AIManager
from config_manager import ConfigManager
from history_manager import HistoryManager, ActivityType, ActivityStatus
from updater import UpdateManager
from ai_vuln_scanner import AIVulnScanner
from tool_health_checker import ToolHealthChecker
from ai_model_installer import AIModelInstaller
try:
    from auto_git_sync import AutoGitSync
except ImportError:
    AutoGitSync = None

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
            self.history = HistoryManager()
            if AutoGitSync:
                self.git_sync = AutoGitSync()
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
        
        start_time = datetime.now()
        
        try:
            # Log scan start
            self.history.add_entry(
                activity_type=ActivityType.SCAN,
                status=ActivityStatus.IN_PROGRESS,
                target=target,
                description=f"Vulnerability scan started for {target}",
                details={
                    "scan_mode": options.get('mode', 'normal'),
                    "email_enabled": options.get('email', False),
                    "output_dir": options.get('output_dir', '')
                }
            )
            
            # Initialize scanner
            scanner = AIVulnScanner()
            
            # Perform scan
            results = await scanner.deep_scan_target(target)
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Print summary
            print(f"\n🎉 Scan completed successfully!")
            print(f"📊 Vulnerabilities found: {len(results['vulnerabilities'])}")
            print(f"🔍 Subdomains discovered: {len(results['subdomains'])}")
            print(f"📈 Risk score: {results['severity_score']}/10")
            print(f"⏱️  Duration: {duration:.1f} seconds")
            
            # Show vulnerability breakdown
            severity_counts = {}
            if results['vulnerabilities']:
                print("\n🚨 Vulnerability Summary:")
                for vuln in results['vulnerabilities']:
                    severity = vuln.get('severity', 'Unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                for severity, count in severity_counts.items():
                    emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
                    print(f"  {emoji} {severity}: {count}")
            
            # Log successful scan
            self.history.add_entry(
                activity_type=ActivityType.SCAN,
                status=ActivityStatus.SUCCESS,
                target=target,
                description=f"Scan completed successfully - {len(results['vulnerabilities'])} vulnerabilities found",
                duration=duration,
                results={
                    "vulnerabilities_count": len(results['vulnerabilities']),
                    "subdomains_count": len(results['subdomains']),
                    "severity_score": results['severity_score'],
                    "severity_breakdown": severity_counts
                }
            )
            
            # Email results if configured
            if options.get('email') and self.config_manager.load_config('email').get('enabled'):
                await self.send_email_report(results)
            
            return results
            
        except Exception as e:
            # Calculate duration even for failed scans
            duration = (datetime.now() - start_time).total_seconds()
            
            # Log failed scan
            self.history.add_entry(
                activity_type=ActivityType.SCAN,
                status=ActivityStatus.FAILED,
                target=target,
                description=f"Scan failed for {target}",
                duration=duration,
                errors=[str(e)]
            )
            
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
  python3 bug_bounty_scanner.py history           # View activity history

HISTORY OPTIONS:
  --recent N                 # Show N recent activities (default: 10)
  --summary N                # Show summary for last N days (default: 30)
  --scans target             # Show scan history for specific target
  --updates                  # Show update history
  --search term              # Search history entries
  --export filename          # Export history to file

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
    
    def admin_menu(self):
        """Hidden admin menu - password protected"""
        if not hasattr(self, 'git_sync') or not self.git_sync:
            print("❌ Admin features not available (git sync module not found)")
            return
            
        print("\n🔒 Admin Access Required")
        password = getpass.getpass("Enter admin password: ")
        
        # Verify password
        if not self.git_sync.verify_password(password):
            print("❌ Invalid password!")
            return
        
        while True:
            print("\n" + "=" * 50)
            print("🔧 ADMIN CONTROL PANEL")
            print("=" * 50)
            print("1. 🚀 Start Auto Git Sync")
            print("2. 🛑 Stop Auto Git Sync")
            print("3. 📊 Git Sync Status")
            print("4. 🔄 Manual Git Sync")
            print("5. 🏥 Deep System Diagnostics")
            print("6. 🔧 Reset All Configurations")
            print("7. 📋 Export Complete System State")
            print("8. 🚪 Exit Admin Panel")
            print("=" * 50)
            
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == "1":
                print("🚀 Starting Auto Git Sync...")
                if self.git_sync.start_auto_sync(password):
                    print("✅ Auto-sync is now running in background")
                    print("💡 Your code changes will be automatically synced to GitHub")
                    input("Press Enter to continue...")
            
            elif choice == "2":
                print("🛑 Stopping Auto Git Sync...")
                self.git_sync.stop_auto_sync()
                input("Press Enter to continue...")
            
            elif choice == "3":
                print("📊 Git Sync Status:")
                self.git_sync.status()
                input("Press Enter to continue...")
            
            elif choice == "4":
                print("🔄 Manual Git Sync...")
                self.git_sync.manual_sync(password)
                input("Press Enter to continue...")
            
            elif choice == "5":
                self.deep_system_diagnostics()
                input("Press Enter to continue...")
            
            elif choice == "6":
                self.reset_all_configs()
                input("Press Enter to continue...")
            
            elif choice == "7":
                self.export_system_state()
                input("Press Enter to continue...")
            
            elif choice == "8":
                print("🚪 Exiting admin panel...")
                break
            
            else:
                print("❌ Invalid option. Please select 1-8.")
                input("Press Enter to continue...")
    
    def deep_system_diagnostics(self):
        """Run deep system diagnostics"""
        print("\n🔍 Running Deep System Diagnostics...")
        print("=" * 40)
        
        # Check git status
        try:
            import subprocess
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                print("📝 Uncommitted changes detected:")
                print(result.stdout)
            else:
                print("✅ Git repository is clean")
        except:
            print("⚠️  Git status check failed")
        
        # Check system resources
        try:
            import psutil
            print(f"💾 Memory usage: {psutil.virtual_memory().percent}%")
            print(f"💽 Disk usage: {psutil.disk_usage('/').percent}%")
            print(f"🖥️  CPU usage: {psutil.cpu_percent()}%")
        except ImportError:
            print("⚠️  System resource monitoring not available (install psutil)")
        
        # Check network connectivity
        try:
            import urllib.request
            urllib.request.urlopen('https://github.com', timeout=5)
            print("🌐 GitHub connectivity: ✅ OK")
        except:
            print("🌐 GitHub connectivity: ❌ Failed")
        
        # Check tool versions
        tools = ['git', 'python3', 'pip']
        for tool in tools:
            try:
                result = subprocess.run([tool, '--version'], capture_output=True, text=True)
                version = result.stdout.strip().split('\n')[0]
                print(f"🔧 {tool}: {version}")
            except:
                print(f"🔧 {tool}: ❌ Not found")
    
    def reset_all_configs(self):
        """Reset all configuration files"""
        print("\n⚠️  WARNING: This will reset ALL configurations!")
        print("This includes:")
        print("- Email settings")
        print("- API keys")
        print("- Tool configurations")
        print("- Custom settings")
        
        confirm = input("\nType 'RESET' to confirm: ")
        if confirm == 'RESET':
            try:
                self.config_manager.reset_all_configs()
                print("✅ All configurations reset")
            except Exception as e:
                print(f"❌ Reset failed: {e}")
        else:
            print("❌ Reset cancelled")
    
    def export_system_state(self):
        """Export complete system state"""
        try:
            from datetime import datetime
            import json
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"system_state_{timestamp}.json"
            
            # Collect system state
            state = {
                "timestamp": timestamp,
                "version": self.version,
                "python_version": sys.version,
                "working_directory": str(Path.cwd()),
            }
            
            # Add git status if available
            try:
                import subprocess
                result = subprocess.run(['git', 'status', '--porcelain'], 
                                      capture_output=True, text=True)
                state["git_status"] = "clean" if not result.stdout.strip() else "modified"
                
                # Get git info
                branch = subprocess.run(['git', 'branch', '--show-current'], 
                                      capture_output=True, text=True).stdout.strip()
                state["git_branch"] = branch
            except:
                state["git_status"] = "unknown"
            
            # Add tool status
            if hasattr(self, 'tool_manager'):
                try:
                    state["tool_status"] = self.tool_manager.check_tool_status()
                except:
                    state["tool_status"] = "error"
            
            # Add config status
            if hasattr(self, 'config_manager'):
                try:
                    state["config_status"] = self.config_manager.validate_all_configs()
                except:
                    state["config_status"] = "error"
            
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"✅ System state exported to: {filename}")
        except Exception as e:
            print(f"❌ Export failed: {e}")

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
    
    # History command
    history_parser = subparsers.add_parser('history', help='View activity history')
    history_parser.add_argument('--recent', type=int, default=10, help='Show recent activity (default: 10)')
    history_parser.add_argument('--summary', type=int, help='Show activity summary for N days (default: 30)')
    history_parser.add_argument('--scans', help='Show scan history for target')
    history_parser.add_argument('--updates', action='store_true', help='Show update history')
    history_parser.add_argument('--search', help='Search history entries')
    history_parser.add_argument('--export', help='Export history to file')
    
    # Help command
    subparsers.add_parser('help', help='Show detailed help')
    
    # Hidden admin command - not shown in help
    subparsers.add_parser('admin', help=argparse.SUPPRESS)
    
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
    
    elif args.command == 'history':
        # Handle history command
        if args.summary is not None:
            days = args.summary if args.summary > 0 else 30
            summary = framework.history.get_activity_summary(days)
            
            print(f"\n📊 Activity Summary (Last {days} days)")
            print("=" * 50)
            print(f"📈 Total Activities: {summary.get('total_activities', 0)}")
            print(f"✅ Success Rate: {summary.get('success_rate', 0)}%")
            
            if summary.get('activities_by_type'):
                print("\n🎯 Activities by Type:")
                for activity_type, count in summary.get('activities_by_type', {}).items():
                    print(f"   {activity_type}: {count}")
            
            if summary.get('activities_by_status'):
                print("\n📊 Activities by Status:")
                for status, count in summary.get('activities_by_status', {}).items():
                    print(f"   {status}: {count}")
            
            if summary.get('top_targets'):
                print("\n🎯 Most Active Targets:")
                for target, count in list(summary['top_targets'].items())[:5]:
                    print(f"   {target}: {count} scans")
        
        elif args.scans:
            entries = framework.history.get_scan_history(target=args.scans)
            print(f"\n🔍 Scan History for: {args.scans}")
            print("=" * 50)
            for entry in entries:
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                status_emoji = '✅' if entry['status'] == 'success' else '❌'
                duration = f" ({entry['duration']:.1f}s)" if entry['duration'] > 0 else ""
                print(f"{status_emoji} [{timestamp}] {entry['description']}{duration}")
        
        elif args.updates:
            entries = framework.history.get_update_history()
            print("\n🔄 Update History")
            print("=" * 30)
            for entry in entries:
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                status_emoji = '✅' if entry['status'] == 'success' else '❌'
                print(f"{status_emoji} [{timestamp}] {entry['description']}")
        
        elif args.search:
            entries = framework.history.search_history(args.search)
            print(f"\n🔍 Search Results for: '{args.search}'")
            print("=" * 50)
            for entry in entries[:20]:  # Show max 20 results
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                status_emoji = '✅' if entry['status'] == 'success' else '❌'
                target_str = f" → {entry['target']}" if entry['target'] else ""
                print(f"{status_emoji} [{timestamp}] {entry['description']}{target_str}")
        
        elif args.export:
            success = framework.history.export_history(args.export)
            if success:
                print(f"✅ History exported to: {args.export}")
            else:
                print("❌ Export failed")
        
        else:
            # Default: show recent activity
            framework.history.display_recent_activity(args.recent)
    
    elif args.command == 'help':
        framework.show_help()
    
    elif args.command == 'admin':
        framework.admin_menu()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
