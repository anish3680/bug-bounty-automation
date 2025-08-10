#!/usr/bin/env python3
"""
Auto Git Sync System
Automatically syncs code changes to GitHub repository
Password protected admin feature
"""

import os
import sys
import time
import subprocess
import hashlib
import getpass
from datetime import datetime
import threading
import signal

class AutoGitSync:
    def __init__(self):
        self.sync_enabled = False
        self.watch_interval = 60  # Check every 60 seconds
        self.repo_path = "/home/phantomx/bug-bounty-automation"
        # Password hash (default: "admin123" - change this!)
        self.password_hash = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # SHA256 of "admin123"
        self.sync_thread = None
        self.running = False
        
    def hash_password(self, password):
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password):
        """Verify admin password"""
        return self.hash_password(password) == self.password_hash
    
    def check_git_changes(self):
        """Check if there are any uncommitted changes"""
        try:
            os.chdir(self.repo_path)
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            return len(result.stdout.strip()) > 0
        except Exception as e:
            print(f"Error checking git status: {e}")
            return False
    
    def sync_to_github(self):
        """Sync changes to GitHub"""
        try:
            os.chdir(self.repo_path)
            
            # Add all changes
            subprocess.run(['git', 'add', '-A'], check=True)
            
            # Commit with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_msg = f"Auto-sync: Updates from {timestamp}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            # Push to GitHub
            subprocess.run(['git', 'push'], check=True)
            
            print(f"✅ Auto-synced to GitHub at {timestamp}")
            return True
            
        except subprocess.CalledProcessError:
            # No changes to commit or push failed
            return False
        except Exception as e:
            print(f"❌ Sync error: {e}")
            return False
    
    def sync_worker(self):
        """Background sync worker thread"""
        while self.running:
            if self.sync_enabled and self.check_git_changes():
                self.sync_to_github()
            time.sleep(self.watch_interval)
    
    def start_auto_sync(self, password):
        """Start auto sync with password verification"""
        if not self.verify_password(password):
            print("❌ Invalid password!")
            return False
        
        if self.running:
            print("⚠️  Auto-sync is already running!")
            return True
        
        self.sync_enabled = True
        self.running = True
        self.sync_thread = threading.Thread(target=self.sync_worker, daemon=True)
        self.sync_thread.start()
        
        print("🚀 Auto-sync started! Changes will be automatically pushed to GitHub.")
        print(f"📁 Monitoring: {self.repo_path}")
        print(f"⏱️  Check interval: {self.watch_interval} seconds")
        return True
    
    def stop_auto_sync(self):
        """Stop auto sync"""
        self.running = False
        self.sync_enabled = False
        if self.sync_thread:
            self.sync_thread.join(timeout=2)
        print("🛑 Auto-sync stopped!")
    
    def status(self):
        """Show sync status"""
        if self.running and self.sync_enabled:
            print("🟢 Auto-sync: ACTIVE")
            print(f"📁 Repository: {self.repo_path}")
            print(f"⏱️  Interval: {self.watch_interval}s")
        else:
            print("🔴 Auto-sync: INACTIVE")
    
    def manual_sync(self, password):
        """Manually trigger sync"""
        if not self.verify_password(password):
            print("❌ Invalid password!")
            return False
        
        print("🔄 Manual sync triggered...")
        if self.check_git_changes():
            success = self.sync_to_github()
            if success:
                print("✅ Manual sync completed!")
            else:
                print("❌ Manual sync failed!")
        else:
            print("ℹ️  No changes to sync.")
        return True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down auto-sync...")
    sys.exit(0)

def main():
    """Main function - hidden admin interface"""
    signal.signal(signal.SIGINT, signal_handler)
    
    sync_manager = AutoGitSync()
    
    if len(sys.argv) < 2:
        print("🔒 Git Auto-Sync Admin Panel")
        print("Usage:")
        print("  python3 auto_git_sync.py start    - Start auto-sync")
        print("  python3 auto_git_sync.py stop     - Stop auto-sync")
        print("  python3 auto_git_sync.py status   - Show status")
        print("  python3 auto_git_sync.py sync     - Manual sync")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        password = getpass.getpass("Enter admin password: ")
        if sync_manager.start_auto_sync(password):
            try:
                # Keep running until interrupted
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                sync_manager.stop_auto_sync()
    
    elif command == "stop":
        sync_manager.stop_auto_sync()
    
    elif command == "status":
        sync_manager.status()
    
    elif command == "sync":
        password = getpass.getpass("Enter admin password: ")
        sync_manager.manual_sync(password)
    
    else:
        print("❌ Unknown command!")

if __name__ == "__main__":
    main()
