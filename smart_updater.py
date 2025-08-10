#!/usr/bin/env python3
"""
Smart Auto-Update Manager for Bug Bounty Automation
Handles comprehensive updates with backup, recovery, and intelligent scheduling
"""

import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass, asdict

@dataclass
class UpdateRecord:
    component: str
    version_before: str
    version_after: str
    timestamp: str
    success: bool
    backup_path: str
    rollback_available: bool

class SmartUpdater:
    def __init__(self):
        self.framework_dir = Path(__file__).parent
        self.logs_dir = self.framework_dir / 'logs'
        self.update_history_file = self.logs_dir / 'update_history.json'
        
        # Create necessary directories
        self.logs_dir.mkdir(exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger(__name__)
        
        # Update components configuration
        self.components = {
            'nuclei_templates': {
                'command': ['nuclei', '-update-templates'],
                'critical': True
            },
            'go_tools': {
                'tools': [
                    'github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest',
                    'github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest',
                    'github.com/projectdiscovery/httpx/cmd/httpx@latest'
                ],
                'critical': True
            },
            'pip_packages': {
                'requirements_file': 'requirements.txt',
                'critical': False
            }
        }
        
        # Load update history
        self.update_history = self._load_update_history()

    def _load_update_history(self) -> List[UpdateRecord]:
        """Load update history from file"""
        try:
            if self.update_history_file.exists():
                with open(self.update_history_file, 'r') as f:
                    data = json.load(f)
                    return [UpdateRecord(**record) for record in data]
        except Exception as e:
            self.logger.error(f"Failed to load update history: {e}")
        
        return []

    def _save_update_history(self):
        """Save update history to file"""
        try:
            data = [asdict(record) for record in self.update_history]
            with open(self.update_history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save update history: {e}")

    def create_backup(self, component: str, backup_path: Path) -> Optional[str]:
        """Create backup of component before update"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{component}_{timestamp}.zip"
            backup_file = self.backups_dir / backup_name
            
            print(f"📦 Creating backup: {backup_name}")
            
            if backup_path.exists():
                with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if backup_path.is_dir():
                        for root, dirs, files in os.walk(backup_path):
                            for file in files:
                                file_path = Path(root) / file
                                arcname = file_path.relative_to(backup_path)
                                zipf.write(file_path, arcname)
                    else:
                        zipf.write(backup_path, backup_path.name)
                
                print(f"✅ Backup created: {backup_file}")
                return str(backup_file)
            else:
                print(f"⚠️  Backup path doesn't exist: {backup_path}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            self.logger.error(f"Backup creation failed for {component}: {e}")
            return None

    def restore_backup(self, backup_path: str) -> bool:
        """Restore from backup"""
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                print(f"❌ Backup file not found: {backup_file}")
                return False
            
            print(f"🔄 Restoring from backup: {backup_file.name}")
            
            # Extract backup
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Determine extraction path based on component
                component_name = backup_file.stem.split('_')[0]
                
                if component_name == 'nuclei_templates':
                    extract_path = Path.home() / 'nuclei-templates'
                elif component_name == 'nuclei_config':
                    extract_path = Path.home() / '.config/nuclei'
                else:
                    extract_path = self.framework_dir / 'restored' / component_name
                
                # Remove existing files
                if extract_path.exists():
                    shutil.rmtree(extract_path)
                
                # Extract backup
                zipf.extractall(extract_path)
            
            print(f"✅ Backup restored successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to restore backup: {e}")
            self.logger.error(f"Backup restoration failed: {e}")
            return False

    def get_component_version(self, component: str) -> str:
        """Get current version of component"""
        try:
            config = self.components.get(component, {})
            
            if component == 'nuclei_templates':
                # Check templates directory timestamp
                templates_dir = Path.home() / 'nuclei-templates'
                if templates_dir.exists():
                    timestamp = os.path.getmtime(templates_dir)
                    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
                return "Unknown"
            
            elif component == 'go_tools':
                # Return Go version and tools info
                result = subprocess.run(['go', 'version'], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
                return "Unknown"
            
            elif component == 'pip_packages':
                # Return pip version
                result = subprocess.run(['pip', '--version'], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
                return "Unknown"
            
            elif 'version_command' in config:
                result = subprocess.run(config['version_command'], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()[:100]  # Limit output
                return "Unknown"
            
        except Exception as e:
            self.logger.error(f"Failed to get version for {component}: {e}")
        
        return "Unknown"

    def update_nuclei_templates(self, force: bool = False) -> bool:
        """Update Nuclei templates with backup"""
        component = 'nuclei_templates'
        config = self.components[component]
        
        print(f"🔄 Updating {component}...")
        
        # Get current version
        version_before = self.get_component_version(component)
        
        # Create backup if needed
        backup_path = None
        if config['backup_needed']:
            backup_path = self.create_backup(component, config['backup_path'])
        
        try:
            # Update templates
            result = subprocess.run(
                config['command'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )
            
            if result.returncode == 0:
                version_after = self.get_component_version(component)
                
                print(f"✅ {component} updated successfully")
                
                # Record update
                record = UpdateRecord(
                    component=component,
                    version_before=version_before,
                    version_after=version_after,
                    timestamp=datetime.now().isoformat(),
                    success=True,
                    backup_path=backup_path or "",
                    rollback_available=backup_path is not None
                )
                
                self.update_history.append(record)
                self._save_update_history()
                
                return True
            else:
                print(f"❌ Failed to update {component}: {result.stderr}")
                
                # Record failure
                record = UpdateRecord(
                    component=component,
                    version_before=version_before,
                    version_after=version_before,
                    timestamp=datetime.now().isoformat(),
                    success=False,
                    backup_path=backup_path or "",
                    rollback_available=backup_path is not None
                )
                
                self.update_history.append(record)
                self._save_update_history()
                
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ {component} update timed out")
            return False
        except Exception as e:
            print(f"❌ Error updating {component}: {e}")
            self.logger.error(f"Update failed for {component}: {e}")
            return False

    def update_go_tools(self) -> bool:
        """Update Go-based security tools"""
        component = 'go_tools'
        config = self.components[component]
        
        print(f"🔄 Updating Go security tools...")
        
        version_before = self.get_component_version(component)
        success_count = 0
        total_tools = len(config['tools'])
        
        for tool in config['tools']:
            try:
                print(f"  📦 Updating {tool.split('/')[-1].split('@')[0]}...")
                
                result = subprocess.run(
                    ['go', 'install', tool],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes per tool
                )
                
                if result.returncode == 0:
                    print(f"    ✅ Updated successfully")
                    success_count += 1
                else:
                    print(f"    ❌ Update failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"    ❌ Update timed out")
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        version_after = self.get_component_version(component)
        update_success = success_count == total_tools
        
        print(f"📊 Go tools update: {success_count}/{total_tools} successful")
        
        # Record update
        record = UpdateRecord(
            component=component,
            version_before=version_before,
            version_after=version_after,
            timestamp=datetime.now().isoformat(),
            success=update_success,
            backup_path="",
            rollback_available=False
        )
        
        self.update_history.append(record)
        self._save_update_history()
        
        return update_success

    def update_pip_packages(self) -> bool:
        """Update Python packages from requirements.txt"""
        component = 'pip_packages'
        
        print(f"🔄 Updating Python packages...")
        
        version_before = self.get_component_version(component)
        
        try:
            requirements_file = self.framework_dir / 'requirements.txt'
            
            if not requirements_file.exists():
                print("❌ requirements.txt not found")
                return False
            
            # Update packages
            result = subprocess.run(
                ['pip', 'install', '-r', str(requirements_file), '--upgrade'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes
            )
            
            version_after = self.get_component_version(component)
            success = result.returncode == 0
            
            if success:
                print("✅ Python packages updated successfully")
            else:
                print(f"❌ Failed to update packages: {result.stderr}")
            
            # Record update
            record = UpdateRecord(
                component=component,
                version_before=version_before,
                version_after=version_after,
                timestamp=datetime.now().isoformat(),
                success=success,
                backup_path="",
                rollback_available=False
            )
            
            self.update_history.append(record)
            self._save_update_history()
            
            return success
            
        except Exception as e:
            print(f"❌ Error updating packages: {e}")
            return False

    def check_for_updates(self) -> Dict[str, bool]:
        """Check which components have available updates"""
        updates_available = {}
        
        print("🔍 Checking for available updates...")
        
        for component, config in self.components.items():
            try:
                if component == 'nuclei_templates':
                    # Check if templates are older than 7 days
                    templates_dir = Path.home() / 'nuclei-templates'
                    if templates_dir.exists():
                        timestamp = os.path.getmtime(templates_dir)
                        age_days = (time.time() - timestamp) / 86400
                        updates_available[component] = age_days > 7
                    else:
                        updates_available[component] = True
                
                elif component == 'pip_packages':
                    # Check for outdated packages
                    result = subprocess.run(
                        ['pip', 'list', '--outdated', '--format=json'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        outdated = json.loads(result.stdout)
                        updates_available[component] = len(outdated) > 0
                    else:
                        updates_available[component] = False
                
                else:
                    # For other components, check if last update was > 30 days ago
                    last_update = None
                    for record in reversed(self.update_history):
                        if record.component == component and record.success:
                            last_update = datetime.fromisoformat(record.timestamp)
                            break
                    
                    if last_update:
                        age_days = (datetime.now() - last_update).days
                        updates_available[component] = age_days > 30
                    else:
                        updates_available[component] = True
                        
            except Exception as e:
                print(f"⚠️  Could not check updates for {component}: {e}")
                updates_available[component] = False
        
        return updates_available

    def run_comprehensive_update(self, force: bool = False) -> Dict[str, bool]:
        """Run comprehensive system update"""
        print("🚀 Starting comprehensive system update...")
        print("=" * 60)
        
        results = {}
        
        # Check for available updates first
        if not force:
            available_updates = self.check_for_updates()
            components_to_update = [comp for comp, needs_update in available_updates.items() 
                                  if needs_update]
        else:
            components_to_update = list(self.components.keys())
        
        if not components_to_update:
            print("✅ All components are up to date!")
            return {}
        
        print(f"📦 Updating {len(components_to_update)} components:")
        for comp in components_to_update:
            print(f"   - {comp}")
        print()
        
        # Update each component
        for component in components_to_update:
            print(f"{'='*20} {component.upper()} {'='*20}")
            
            if component == 'nuclei_templates':
                results[component] = self.update_nuclei_templates(force)
            elif component == 'go_tools':
                results[component] = self.update_go_tools()
            elif component == 'pip_packages':
                results[component] = self.update_pip_packages()
            else:
                print(f"⚠️  Unknown component: {component}")
                results[component] = False
            
            print()
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print("=" * 60)
        print(f"📊 Update Summary: {successful}/{total} successful")
        
        if successful == total:
            print("✅ All updates completed successfully!")
        else:
            print("⚠️  Some updates failed - check logs for details")
            failed = [comp for comp, success in results.items() if not success]
            print(f"❌ Failed: {', '.join(failed)}")
        
        return results

    def rollback_component(self, component: str) -> bool:
        """Rollback a component to previous version"""
        print(f"🔄 Rolling back {component}...")
        
        # Find last successful update with backup
        for record in reversed(self.update_history):
            if (record.component == component and 
                record.success and 
                record.rollback_available and 
                record.backup_path):
                
                print(f"📦 Found backup from {record.timestamp}")
                
                if self.restore_backup(record.backup_path):
                    print(f"✅ {component} rolled back successfully")
                    return True
                else:
                    print(f"❌ Failed to restore {component}")
                    return False
        
        print(f"❌ No rollback available for {component}")
        return False

    def get_update_history(self, component: str = None) -> List[UpdateRecord]:
        """Get update history for component or all components"""
        if component:
            return [record for record in self.update_history 
                   if record.component == component]
        return self.update_history

    def clean_old_backups(self, days_to_keep: int = 30):
        """Clean old backup files"""
        print(f"🧹 Cleaning backups older than {days_to_keep} days...")
        
        cutoff_time = time.time() - (days_to_keep * 86400)
        removed_count = 0
        
        try:
            for backup_file in self.backups_dir.glob("*.zip"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    removed_count += 1
            
            print(f"✅ Removed {removed_count} old backup files")
            
        except Exception as e:
            print(f"❌ Error cleaning backups: {e}")

    def get_system_health(self) -> Dict:
        """Get comprehensive system health report"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'overall_score': 0,
            'status': 'Unknown'
        }
        
        try:
            # Check tools
            from tool_health_checker import ToolHealthChecker
            tool_checker = ToolHealthChecker()
            tool_status = tool_checker.get_comprehensive_status()
            
            required_tools = sum(1 for status in tool_status.values() if status['required'])
            installed_required = sum(1 for status in tool_status.values() 
                                   if status['required'] and status['installed'])
            
            tools_score = (installed_required / required_tools * 100) if required_tools > 0 else 100
            health['components']['tools'] = {
                'score': tools_score,
                'installed': installed_required,
                'required': required_tools
            }
            
            # Check AI models
            from ai_model_installer import AIModelInstaller
            ai_installer = AIModelInstaller()
            running, status = ai_installer.check_ollama_status()
            models = ai_installer.get_installed_models()
            
            ai_score = 100 if (running and models) else 50 if running else 0
            health['components']['ai'] = {
                'score': ai_score,
                'ollama_running': running,
                'models_count': len(models)
            }
            
            # Calculate overall score
            component_scores = [comp['score'] for comp in health['components'].values()]
            health['overall_score'] = sum(component_scores) / len(component_scores) if component_scores else 0
            
            # Determine status
            score = health['overall_score']
            if score >= 90:
                health['status'] = 'Excellent'
            elif score >= 75:
                health['status'] = 'Good'
            elif score >= 60:
                health['status'] = 'Fair'
            else:
                health['status'] = 'Poor'
                
        except Exception as e:
            health['error'] = str(e)
        
        return health

    def schedule_auto_updates(self, enable: bool = True):
        """Enable/disable scheduled auto-updates via cron"""
        try:
            from crontab import CronTab
            
            cron = CronTab(user=True)
            
            # Remove existing job
            cron.remove_all(comment='bug-bounty-auto-update')
            
            if enable:
                # Add new job - daily at 2 AM
                job = cron.new(command=f'cd {self.framework_dir} && python3 smart_updater.py --auto',
                              comment='bug-bounty-auto-update')
                job.setall('0 2 * * * ')  # Daily at 2 AM
                
                cron.write()
                print("✅ Auto-updates scheduled for daily 2:00 AM")
            else:
                cron.write()
                print("✅ Auto-updates disabled")
                
        except ImportError:
            print("⚠️  python-crontab not available - manual scheduling required")
        except Exception as e:
            print(f"❌ Failed to schedule updates: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Update Manager for Bug Bounty Automation')
    parser.add_argument('--update', choices=['all', 'nuclei', 'tools', 'packages'], help='Run updates')
    parser.add_argument('--force', action='store_true', help='Force update even if not needed')
    parser.add_argument('--check', action='store_true', help='Check for available updates')
    parser.add_argument('--rollback', type=str, help='Rollback specific component')
    parser.add_argument('--history', type=str, nargs='?', const='all', help='Show update history')
    parser.add_argument('--schedule', action='store_true', help='Enable auto-updates')
    parser.add_argument('--no-schedule', action='store_true', help='Disable auto-updates')
    parser.add_argument('--clean-backups', type=int, default=30, help='Clean backups older than N days')
    parser.add_argument('--auto', action='store_true', help='Auto mode (for cron)')
    
    args = parser.parse_args()
    
    updater = SmartUpdater()
    
    if args.check:
        updates = updater.check_for_updates()
        print("🔍 Available Updates:")
        for component, available in updates.items():
            status = "✅ Available" if available else "⚪ Up to date"
            print(f"   {component}: {status}")
    
    elif args.update:
        if args.update == 'all':
            updater.run_comprehensive_update(args.force)
        elif args.update == 'nuclei':
            updater.update_nuclei_templates(args.force)
        elif args.update == 'tools':
            updater.update_go_tools()
        elif args.update == 'packages':
            updater.update_pip_packages()
    
    elif args.rollback:
        updater.rollback_component(args.rollback)
    
    elif args.history:
        if args.history == 'all':
            history = updater.get_update_history()
        else:
            history = updater.get_update_history(args.history)
        
        print(f"📚 Update History ({len(history)} records):")
        for record in history[-10:]:  # Show last 10
            status = "✅" if record.success else "❌"
            rollback = "🔄" if record.rollback_available else "⚪"
            print(f"   {status} {rollback} {record.component}: {record.timestamp}")
    
    elif args.schedule:
        updater.schedule_auto_updates(True)
    
    elif args.no_schedule:
        updater.schedule_auto_updates(False)
    
    elif args.clean_backups:
        updater.clean_old_backups(args.clean_backups)
    
    elif args.auto:
        # Auto mode - only update if needed
        print("🤖 Auto-update mode")
        updater.run_comprehensive_update(force=False)
    
    else:
        print("🔄 Smart Update Manager")
        print("Run with --help to see available options")
        
        # Show current status
        updates = updater.check_for_updates()
        available_count = sum(1 for available in updates.values() if available)
        
        if available_count > 0:
            print(f"📦 {available_count} updates available")
            print("Run with --update all to install updates")
        else:
            print("✅ All components are up to date")

if __name__ == "__main__":
    main()
