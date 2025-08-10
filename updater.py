#!/usr/bin/env python3
"""
Self-Update System for Bug Bounty Automation
Handles updates for tools, templates, frameworks, and configurations
"""

import os
import sys
import json
import shutil
import subprocess
import requests
import tempfile
import zipfile
import tarfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from concurrent.futures import ThreadPoolExecutor
import hashlib
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    
from tool_manager import ToolManager
from config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UpdateManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_manager = ConfigManager()
        self.tool_manager = ToolManager()
        
        # Update sources and configurations
        self.update_sources = {
            'nuclei_templates': {
                'type': 'git',
                'url': 'https://github.com/projectdiscovery/nuclei-templates.git',
                'local_path': Path.home() / 'nuclei-templates',
                'description': 'Nuclei vulnerability templates',
                'priority': 'high'
            },
            'payloads_all_the_things': {
                'type': 'git',
                'url': 'https://github.com/swisskyrepo/PayloadsAllTheThings.git',
                'local_path': Path.home() / 'PayloadsAllTheThings',
                'description': 'Security payload collection',
                'priority': 'medium'
            },
            'seclists': {
                'type': 'git',
                'url': 'https://github.com/danielmiessler/SecLists.git',
                'local_path': Path.home() / 'SecLists',
                'description': 'Security wordlists',
                'priority': 'medium'
            },
            'framework': {
                'type': 'git',
                'url': 'https://github.com/your-repo/bug-bounty-automation.git',  # Update with actual repo
                'local_path': self.base_dir,
                'description': 'Bug bounty automation framework',
                'priority': 'critical'
            }
        }
        
        # Update schedule
        self.update_intervals = {
            'nuclei_templates': timedelta(hours=24),  # Daily
            'payloads_all_the_things': timedelta(days=7),  # Weekly
            'seclists': timedelta(days=30),  # Monthly
            'tools': timedelta(days=7),  # Weekly
            'framework': timedelta(days=1)  # Daily check
        }
        
        self.update_state_file = self.base_dir / 'update_state.json'
        self.backup_dir = self.base_dir / 'backups'
        self.backup_dir.mkdir(exist_ok=True)

    def run_full_update(self, force: bool = False) -> bool:
        """Run comprehensive update of all components"""
        logger.info("🔄 Starting comprehensive system update...")
        
        try:
            results = {}
            
            # 1. Update security tools
            logger.info("📦 Updating security tools...")
            results['tools'] = self.update_security_tools()
            
            # 2. Update nuclei templates (critical)
            logger.info("🎯 Updating vulnerability templates...")
            results['nuclei_templates'] = self.update_nuclei_templates(force)
            
            # 3. Update payload collections
            logger.info("💉 Updating payload collections...")
            results['payloads'] = self.update_payload_collections(force)
            
            # 4. Update wordlists
            logger.info("📚 Updating wordlists...")
            results['wordlists'] = self.update_wordlists(force)
            
            # 5. Check framework updates (careful with this one)
            logger.info("🚀 Checking framework updates...")
            results['framework'] = self.check_framework_updates()
            
            # 6. Update AI models if needed
            logger.info("🤖 Checking AI model updates...")
            results['ai_models'] = self.update_ai_models()
            
            # 7. Update configurations
            logger.info("⚙️  Updating configurations...")
            results['configs'] = self.update_configurations()
            
            # Save update state
            self.save_update_state(results)
            
            # Generate update report
            self.generate_update_report(results)
            
            success_count = sum(1 for result in results.values() if result)
            total_count = len(results)
            
            logger.info(f"✅ Update complete: {success_count}/{total_count} components updated successfully")
            
            return success_count == total_count
            
        except Exception as e:
            logger.error(f"❌ Critical error during update: {e}")
            return False

    def update_security_tools(self) -> bool:
        """Update all security tools"""
        try:
            # Update nuclei templates first (most important)
            nuclei_path = shutil.which('nuclei') or str(Path.home() / 'go' / 'bin' / 'nuclei')
            if os.path.exists(nuclei_path):
                logger.info("Updating nuclei templates...")
                result = subprocess.run([nuclei_path, '-update-templates'], 
                                      capture_output=True, timeout=120)
                if result.returncode == 0:
                    logger.info("✅ Nuclei templates updated")
                else:
                    logger.warning(f"⚠️ Nuclei template update failed: {result.stderr}")
            
            # Update Go-based tools
            return self.tool_manager.update_tools()
            
        except Exception as e:
            logger.error(f"❌ Failed to update security tools: {e}")
            return False

    def update_nuclei_templates(self, force: bool = False) -> bool:
        """Update nuclei templates repository"""
        return self._update_git_repository('nuclei_templates', force)

    def update_payload_collections(self, force: bool = False) -> bool:
        """Update payload collections"""
        return self._update_git_repository('payloads_all_the_things', force)

    def update_wordlists(self, force: bool = False) -> bool:
        """Update security wordlists"""
        return self._update_git_repository('seclists', force)

    def check_framework_updates(self) -> bool:
        """Check for framework updates (be careful with this)"""
        try:
            # Check if git module is available
            if not GIT_AVAILABLE:
                logger.info("⚠️ Git module not available - skipping framework update check")
                return True
            
            # Only check, don't automatically update the framework
            logger.info("Checking for framework updates...")
            
            # If this is a git repository
            if (self.base_dir / '.git').exists():
                repo = git.Repo(self.base_dir)
                
                # Fetch latest info
                origin = repo.remotes.origin
                origin.fetch()
                
                # Check if we're behind
                commits_behind = list(repo.iter_commits('HEAD..origin/main'))
                
                if commits_behind:
                    logger.info(f"📈 Framework updates available: {len(commits_behind)} commits behind")
                    logger.info("Run 'git pull' manually to update the framework")
                    return True
                else:
                    logger.info("✅ Framework is up to date")
                    return True
            else:
                logger.info("⚠️ Framework not in git repository - manual updates required")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to check framework updates: {e}")
            return False

    def update_ai_models(self) -> bool:
        """Update AI models if needed"""
        try:
            from ai_manager import AIManager
            
            ai_manager = AIManager()
            status = ai_manager.get_model_status()
            
            # Check if Ollama is available but no models installed
            if (status.get('ollama', {}).get('available', False) and 
                not status.get('ollama', {}).get('models', [])):
                
                logger.info("Installing recommended Ollama model...")
                # This is async, need to handle properly
                import asyncio
                return asyncio.run(ai_manager.install_recommended_model())
            
            logger.info("✅ AI models are up to date")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update AI models: {e}")
            return False

    def update_configurations(self) -> bool:
        """Update configuration templates and defaults"""
        try:
            # Check if configs exist, if not create defaults
            if not self.config_manager.all_configs_exist():
                logger.info("Creating default configurations...")
                
                # Create default configs for each component
                for config_name in self.config_manager.default_configs.keys():
                    config_path = getattr(self.config_manager, f'{config_name}_config_path')
                    if not config_path.exists():
                        default_config = self.config_manager.default_configs[config_name]
                        self.config_manager.save_config(config_name, default_config)
                        logger.info(f"✅ Created default {config_name} configuration")
                
                return True
            
            logger.info("✅ Configurations are up to date")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update configurations: {e}")
            return False

    def _update_git_repository(self, repo_name: str, force: bool = False) -> bool:
        """Update a git repository"""
        try:
            # Check if git module is available
            if not GIT_AVAILABLE:
                logger.warning(f"⚠️ Git module not available - skipping {repo_name} update")
                return True
            
            repo_config = self.update_sources[repo_name]
            local_path = repo_config['local_path']
            
            # Check if update is needed (unless forced)
            if not force and not self._is_update_needed(repo_name):
                logger.info(f"⏭️ Skipping {repo_name} - not due for update")
                return True
            
            if local_path.exists():
                # Repository exists, try to update
                try:
                    logger.info(f"Updating existing repository: {repo_name}")
                    repo = git.Repo(local_path)
                    
                    # Create backup before updating
                    backup_path = self._create_backup(local_path, repo_name)
                    
                    # Pull latest changes
                    origin = repo.remotes.origin
                    origin.pull()
                    
                    logger.info(f"✅ Successfully updated {repo_name}")
                    return True
                    
                except git.exc.GitCommandError as e:
                    logger.error(f"Git error updating {repo_name}: {e}")
                    
                    # Try to restore from backup
                    if backup_path and backup_path.exists():
                        logger.info(f"Attempting to restore {repo_name} from backup")
                        self._restore_from_backup(backup_path, local_path)
                    
                    return False
            else:
                # Repository doesn't exist, clone it
                try:
                    logger.info(f"Cloning new repository: {repo_name}")
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    git.Repo.clone_from(repo_config['url'], local_path)
                    logger.info(f"✅ Successfully cloned {repo_name}")
                    return True
                    
                except git.exc.GitCommandError as e:
                    logger.error(f"Failed to clone {repo_name}: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error updating {repo_name}: {e}")
            return False

    def _is_update_needed(self, component: str) -> bool:
        """Check if component needs updating based on schedule"""
        try:
            state = self.load_update_state()
            last_update = state.get('last_updates', {}).get(component)
            
            if not last_update:
                return True  # Never updated before
            
            last_update_time = datetime.fromisoformat(last_update)
            update_interval = self.update_intervals.get(component, timedelta(days=7))
            
            return datetime.now() - last_update_time > update_interval
            
        except Exception as e:
            logger.warning(f"Could not determine update schedule for {component}: {e}")
            return True  # Default to updating if unsure

    def _create_backup(self, source_path: Path, name: str) -> Optional[Path]:
        """Create backup of directory/file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.backup_dir / f'{name}_{timestamp}'
            
            if source_path.is_dir():
                shutil.copytree(source_path, backup_path)
            else:
                shutil.copy2(source_path, backup_path)
            
            logger.info(f"📦 Created backup: {backup_path}")
            
            # Clean old backups (keep only last 5)
            self._cleanup_old_backups(name)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create backup for {name}: {e}")
            return None

    def _restore_from_backup(self, backup_path: Path, target_path: Path) -> bool:
        """Restore from backup"""
        try:
            if target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
            
            if backup_path.is_dir():
                shutil.copytree(backup_path, target_path)
            else:
                shutil.copy2(backup_path, target_path)
            
            logger.info(f"🔄 Restored {target_path} from backup")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False

    def _cleanup_old_backups(self, component_name: str, keep_count: int = 5):
        """Clean up old backups, keeping only the most recent ones"""
        try:
            pattern = f'{component_name}_*'
            backup_files = list(self.backup_dir.glob(pattern))
            
            if len(backup_files) <= keep_count:
                return
            
            # Sort by modification time, newest first
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old backups
            for old_backup in backup_files[keep_count:]:
                if old_backup.is_dir():
                    shutil.rmtree(old_backup)
                else:
                    old_backup.unlink()
                logger.info(f"🗑️ Removed old backup: {old_backup}")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups for {component_name}: {e}")

    def load_update_state(self) -> Dict[str, Any]:
        """Load update state from file"""
        try:
            if self.update_state_file.exists():
                with open(self.update_state_file, 'r') as f:
                    return json.load(f)
            return {'last_updates': {}, 'update_history': []}
        except Exception as e:
            logger.warning(f"Could not load update state: {e}")
            return {'last_updates': {}, 'update_history': []}

    def save_update_state(self, results: Dict[str, bool]):
        """Save update state to file"""
        try:
            state = self.load_update_state()
            current_time = datetime.now().isoformat()
            
            # Update last update times for successful updates
            for component, success in results.items():
                if success:
                    state['last_updates'][component] = current_time
            
            # Add to history
            history_entry = {
                'timestamp': current_time,
                'results': results,
                'success_count': sum(1 for r in results.values() if r),
                'total_count': len(results)
            }
            
            state['update_history'].append(history_entry)
            
            # Keep only last 100 history entries
            if len(state['update_history']) > 100:
                state['update_history'] = state['update_history'][-100:]
            
            with open(self.update_state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save update state: {e}")

    def generate_update_report(self, results: Dict[str, bool]):
        """Generate update report"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            report = f"""
# Bug Bounty Automation - Update Report
Generated: {timestamp}

## Update Summary
"""
            
            success_count = sum(1 for r in results.values() if r)
            total_count = len(results)
            
            report += f"- **Success Rate**: {success_count}/{total_count} ({(success_count/total_count)*100:.1f}%)\n\n"
            
            report += "## Component Status\n\n"
            
            for component, success in results.items():
                status_emoji = "✅" if success else "❌"
                description = self.update_sources.get(component, {}).get('description', component.replace('_', ' ').title())
                report += f"- {status_emoji} **{description}**: {'Updated' if success else 'Failed'}\n"
            
            # Add next update schedule
            report += "\n## Next Scheduled Updates\n\n"
            state = self.load_update_state()
            
            for component, interval in self.update_intervals.items():
                last_update = state.get('last_updates', {}).get(component)
                if last_update:
                    next_update = datetime.fromisoformat(last_update) + interval
                    report += f"- **{component.replace('_', ' ').title()}**: {next_update.strftime('%Y-%m-%d %H:%M')}\n"
                else:
                    report += f"- **{component.replace('_', ' ').title()}**: Next run\n"
            
            # Save report
            report_path = self.base_dir / f'update_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            with open(report_path, 'w') as f:
                f.write(report)
            
            logger.info(f"📊 Update report saved: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate update report: {e}")

    def rollback_updates(self, component: Optional[str] = None) -> bool:
        """Rollback updates for a component or all components"""
        try:
            if component:
                # Rollback specific component
                return self._rollback_component(component)
            else:
                # Rollback all components
                success_count = 0
                components = list(self.update_sources.keys())
                
                for comp in components:
                    if self._rollback_component(comp):
                        success_count += 1
                
                logger.info(f"Rollback complete: {success_count}/{len(components)} components rolled back")
                return success_count == len(components)
                
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False

    def _rollback_component(self, component: str) -> bool:
        """Rollback a specific component"""
        try:
            # Find most recent backup
            pattern = f'{component}_*'
            backup_files = list(self.backup_dir.glob(pattern))
            
            if not backup_files:
                logger.warning(f"No backups found for {component}")
                return False
            
            # Get most recent backup
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            
            # Get target path
            target_path = self.update_sources.get(component, {}).get('local_path')
            if not target_path:
                logger.error(f"No target path configured for {component}")
                return False
            
            # Restore from backup
            return self._restore_from_backup(latest_backup, target_path)
            
        except Exception as e:
            logger.error(f"Failed to rollback {component}: {e}")
            return False

    def schedule_automatic_updates(self, enable: bool = True) -> bool:
        """Schedule automatic updates using cron"""
        try:
            from crontab import CronTab
            
            cron = CronTab(user=True)
            
            # Remove existing job
            cron.remove_all(comment='bug-bounty-auto-update')
            
            if enable:
                # Add new job - run daily at 2 AM
                job = cron.new(command=f'{sys.executable} {__file__} --auto-update', 
                             comment='bug-bounty-auto-update')
                job.setall('0 2 * * *')  # Daily at 2 AM
                cron.write()
                
                logger.info("✅ Automatic updates scheduled for 2 AM daily")
                return True
            else:
                cron.write()
                logger.info("✅ Automatic updates disabled")
                return True
                
        except ImportError:
            logger.warning("python-crontab not installed - cannot schedule automatic updates")
            logger.info("Install with: pip install python-crontab")
            return False
        except Exception as e:
            logger.error(f"Failed to schedule automatic updates: {e}")
            return False

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Tool status
            tool_status = self.tool_manager.check_tool_status()
            
            # Update state
            update_state = self.load_update_state()
            
            # AI model status
            from ai_manager import AIManager
            ai_manager = AIManager()
            ai_status = ai_manager.get_model_status()
            
            # Configuration status
            config_status = self.config_manager.validate_all_configs()
            
            return {
                'tools': tool_status,
                'updates': update_state,
                'ai_models': ai_status,
                'configurations': config_status,
                'system_health': self._assess_system_health(tool_status, ai_status, config_status)
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {'error': str(e)}

    def _assess_system_health(self, tool_status: Dict, ai_status: Dict, config_status: Dict) -> Dict[str, Any]:
        """Assess overall system health"""
        try:
            # Count installed tools
            tools_installed = sum(1 for status in tool_status.values() 
                                if status.get('installed', False))
            total_tools = len(tool_status)
            
            # Count available AI models
            ai_available = sum(1 for status in ai_status.values()
                             if status.get('available', False))
            total_ai = len(ai_status)
            
            # Count valid configs
            configs_valid = sum(1 for valid in config_status.values() if valid)
            total_configs = len(config_status)
            
            # Calculate health score
            tool_score = (tools_installed / total_tools) * 40  # 40% weight
            ai_score = (ai_available / total_ai) * 30  # 30% weight
            config_score = (configs_valid / total_configs) * 30  # 30% weight
            
            health_score = int(tool_score + ai_score + config_score)
            
            # Determine health status
            if health_score >= 90:
                health_status = "Excellent"
            elif health_score >= 75:
                health_status = "Good"
            elif health_score >= 60:
                health_status = "Fair"
            else:
                health_status = "Poor"
            
            return {
                'score': health_score,
                'status': health_status,
                'tools_ratio': f"{tools_installed}/{total_tools}",
                'ai_ratio': f"{ai_available}/{total_ai}",
                'config_ratio': f"{configs_valid}/{total_configs}"
            }
            
        except Exception as e:
            logger.error(f"Failed to assess system health: {e}")
            return {'error': str(e)}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bug Bounty Automation Update Manager")
    parser.add_argument('--full-update', action='store_true', help='Run full system update')
    parser.add_argument('--force', action='store_true', help='Force update regardless of schedule')
    parser.add_argument('--tools-only', action='store_true', help='Update only security tools')
    parser.add_argument('--templates-only', action='store_true', help='Update only vulnerability templates')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--rollback', type=str, nargs='?', const='all', help='Rollback updates')
    parser.add_argument('--schedule', action='store_true', help='Enable automatic updates')
    parser.add_argument('--no-schedule', action='store_true', help='Disable automatic updates')
    parser.add_argument('--auto-update', action='store_true', help='Run automatic update (for cron)')
    
    args = parser.parse_args()
    
    updater = UpdateManager()
    
    if args.full_update or args.auto_update:
        success = updater.run_full_update(force=args.force)
        sys.exit(0 if success else 1)
    
    elif args.tools_only:
        success = updater.update_security_tools()
        sys.exit(0 if success else 1)
    
    elif args.templates_only:
        success = updater.update_nuclei_templates(force=args.force)
        sys.exit(0 if success else 1)
    
    elif args.status:
        status = updater.get_system_status()
        print("\n🔍 System Status Report")
        print("=" * 50)
        
        # System health
        health = status.get('system_health', {})
        if 'error' not in health:
            print(f"🏥 Overall Health: {health.get('score', 0)}/100 ({health.get('status', 'Unknown')})")
            print(f"   Tools: {health.get('tools_ratio', 'Unknown')}")
            print(f"   AI Models: {health.get('ai_ratio', 'Unknown')}")
            print(f"   Configs: {health.get('config_ratio', 'Unknown')}")
        
        print(f"\n📊 Detailed status saved to logs")
    
    elif args.rollback:
        if args.rollback == 'all':
            success = updater.rollback_updates()
        else:
            success = updater.rollback_updates(args.rollback)
        sys.exit(0 if success else 1)
    
    elif args.schedule:
        success = updater.schedule_automatic_updates(True)
        sys.exit(0 if success else 1)
    
    elif args.no_schedule:
        success = updater.schedule_automatic_updates(False)
        sys.exit(0 if success else 1)
    
    else:
        print("Use --full-update, --status, --tools-only, --templates-only, --rollback, --schedule, or --no-schedule")
        print("Run with --help for more options")
