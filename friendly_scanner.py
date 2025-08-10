#!/usr/bin/env python3
"""
User-Friendly Bug Bounty Scanner
Simple, intuitive interface with AI assistance and error handling
"""

import os
import sys
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, Any
import traceback

# Import our components
try:
    from ai_assistant import AIAssistant
    from bug_bounty_scanner import BugBountyFramework
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required files are in the same directory.")
    sys.exit(1)

class FriendlyScanner:
    def __init__(self):
        self.assistant = AIAssistant()
        self.framework = None
        self.user_session = {
            "started_at": datetime.now().isoformat(),
            "commands_run": 0,
            "errors_encountered": 0,
            "scans_completed": 0
        }
        
    def initialize_framework(self):
        """Initialize the framework with error handling"""
        try:
            if not self.framework:
                print("🔧 Initializing scanner framework...")
                self.framework = BugBountyFramework()
                return True
        except Exception as e:
            self.handle_error("Framework initialization failed", str(e))
            return False
        return True
    
    def handle_error(self, context: str, error_message: str, command_used: str = None):
        """Handle errors with AI assistance"""
        self.user_session["errors_encountered"] += 1
        
        print(f"\n❌ {context}")
        print(f"Error: {error_message}")
        
        # Log the error
        self.assistant.log_user_activity(
            action="error",
            success=False,
            error_message=error_message,
            command_used=command_used
        )
        
        # Get AI auto-fix suggestion
        fix_suggestion = self.assistant.auto_fix_error(error_message, command_used)
        print(f"\n{fix_suggestion}")
        
        # Offer additional help
        print(f"\n💡 Need more help? Type 'chat' to talk with the AI assistant!")
    
    def welcome_screen(self):
        """Show friendly welcome screen"""
        print("\n" + "="*70)
        print("🚀 **Welcome to the Friendly Bug Bounty Scanner!**")
        print("="*70)
        print("This tool makes bug bounty hunting simple and efficient!")
        print()
        print("✨ **What makes this special:**")
        print("   🤖 AI-powered assistance and error fixing")
        print("   📊 Automatic vulnerability analysis")
        print("   💌 Professional report generation")
        print("   🔄 Auto-updates and tool management")
        print("   💬 Interactive help system")
        print()
        print("🎯 **Quick Start:**")
        print("   1. Type 'scan example.com' to scan a target")
        print("   2. Type 'setup' for first-time configuration")
        print("   3. Type 'chat' to talk with the AI assistant")
        print("   4. Type 'help' for detailed instructions")
        print("="*70)
    
    def show_simple_menu(self):
        """Show simplified main menu"""
        print("\n" + "="*50)
        print("🎛️  **What would you like to do?**")
        print("="*50)
        print("1. 🎯 Scan a target for vulnerabilities")
        print("2. ⚙️  Setup and configuration")
        print("3. 📊 View system status")
        print("4. 🤖 Chat with AI assistant")
        print("5. 📝 Send feedback")
        print("6. 📚 View help and tutorials")
        print("7. 🚪 Exit")
        print("="*50)
        
        try:
            choice = input("\nEnter your choice (1-7) or command: ").strip()
            return choice
        except KeyboardInterrupt:
            return "7"
    
    def parse_simple_command(self, command: str) -> Dict[str, Any]:
        """Parse user-friendly commands"""
        command = command.lower().strip()
        
        # Menu choices
        if command in ['1', 'scan']:
            return {"action": "scan_wizard"}
        elif command in ['2', 'setup', 'config']:
            return {"action": "setup"}
        elif command in ['3', 'status', 'health']:
            return {"action": "status"}
        elif command in ['4', 'chat', 'help me', 'ai']:
            return {"action": "chat"}
        elif command in ['5', 'feedback', 'report']:
            return {"action": "feedback"}
        elif command in ['6', 'help', 'tutorial']:
            return {"action": "help"}
        elif command in ['7', 'exit', 'quit', 'bye']:
            return {"action": "exit"}
        
        # Direct scan commands
        if command.startswith('scan '):
            target = command.split(' ', 1)[1].strip()
            return {"action": "scan", "target": target}
        
        # Natural language processing
        if any(word in command for word in ['scan', 'test', 'check']):
            # Try to extract domain from command
            words = command.split()
            for word in words:
                if '.' in word and len(word) > 3:
                    return {"action": "scan", "target": word}
            return {"action": "scan_wizard"}
        
        if any(word in command for word in ['help', 'how', 'what', '?']):
            return {"action": "chat"}
        
        # Unknown command
        return {"action": "unknown", "original": command}
    
    def scan_wizard(self):
        """Interactive scan wizard"""
        print("\n🎯 **Vulnerability Scan Wizard**")
        print("="*40)
        
        try:
            # Get target
            target = input("Enter target domain (e.g., example.com): ").strip()
            if not target:
                print("❌ Target is required!")
                return
            
            # Validate target format
            if not ('.' in target and len(target) > 3):
                print("⚠️  That doesn't look like a valid domain. Continue anyway? (y/N)")
                if input().lower() != 'y':
                    return
            
            # Get scan options
            print("\n📋 **Scan Options:**")
            print("1. 🏃 Fast scan (5-10 minutes)")
            print("2. 🚀 Normal scan (15-30 minutes)")
            print("3. 🔍 Thorough scan (30+ minutes)")
            
            scan_type = input("\nSelect scan type (1-3, default: 2): ").strip()
            
            mode_map = {'1': 'fast', '2': 'normal', '3': 'thorough'}
            scan_mode = mode_map.get(scan_type, 'normal')
            
            # Email option
            email_report = input("Send results via email? (y/N): ").lower() == 'y'
            
            # Confirmation
            print(f"\n📋 **Scan Summary:**")
            print(f"Target: {target}")
            print(f"Mode: {scan_mode}")
            print(f"Email: {'Yes' if email_report else 'No'}")
            
            if input("\nProceed with scan? (Y/n): ").lower() not in ['', 'y', 'yes']:
                print("Scan cancelled.")
                return
            
            # Run the scan
            await self.run_scan(target, scan_mode, email_report)
            
        except KeyboardInterrupt:
            print("\n❌ Scan cancelled by user.")
        except Exception as e:
            self.handle_error("Scan wizard failed", str(e))
    
    async def run_scan(self, target: str, mode: str = 'normal', email: bool = False):
        """Run vulnerability scan with comprehensive error handling"""
        try:
            if not self.initialize_framework():
                return
                
            print(f"\n🚀 Starting {mode} scan of {target}...")
            print("This may take a while. Please be patient!")
            print("(Press Ctrl+C to cancel if needed)")
            
            start_time = time.time()
            
            # Log scan start
            self.assistant.log_user_activity(
                action="scan_start",
                target=target,
                command_used=f"scan {target} --{mode}",
                details={"scan_mode": mode, "email_enabled": email}
            )
            
            # Run the actual scan
            options = {
                'email': email,
                'mode': mode,
                'output_dir': None
            }
            
            results = await self.framework.run_vulnerability_scan(target, options)
            
            duration = time.time() - start_time
            
            if results:
                self.user_session["scans_completed"] += 1
                
                # Show user-friendly results
                self.show_scan_results(results, target, duration)
                
                # Log successful scan
                self.assistant.log_user_activity(
                    action="scan_complete",
                    target=target,
                    success=True,
                    duration=duration,
                    details={
                        "vulnerabilities_found": len(results.get('vulnerabilities', [])),
                        "scan_mode": mode
                    }
                )
                
                # Offer next steps
                self.suggest_next_steps(results)
                
            else:
                self.assistant.log_user_activity(
                    action="scan_complete",
                    target=target,
                    success=False,
                    duration=duration
                )
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Scan interrupted by user.")
            print("Your progress has been saved.")
        except Exception as e:
            self.handle_error("Scan execution failed", str(e), f"scan {target}")
    
    def show_scan_results(self, results: Dict[str, Any], target: str, duration: float):
        """Show user-friendly scan results"""
        print("\n" + "="*60)
        print("🎉 **Scan Completed Successfully!**")
        print("="*60)
        
        vulnerabilities = results.get('vulnerabilities', [])
        subdomains = results.get('subdomains', [])
        severity_score = results.get('severity_score', 0)
        
        print(f"🎯 Target: {target}")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"🔍 Vulnerabilities found: {len(vulnerabilities)}")
        print(f"🌐 Subdomains discovered: {len(subdomains)}")
        print(f"📈 Risk score: {severity_score}/10")
        
        if vulnerabilities:
            print(f"\n🚨 **Vulnerability Breakdown:**")
            severity_counts = {}
            for vuln in vulnerabilities:
                severity = vuln.get('severity', 'Unknown')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            for severity, count in severity_counts.items():
                emoji = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
                print(f"  {emoji} {severity}: {count}")
        else:
            print(f"\n✅ No vulnerabilities found! The target appears secure.")
        
        print("="*60)
    
    def suggest_next_steps(self, results: Dict[str, Any]):
        """Suggest next steps based on results"""
        vulnerabilities = results.get('vulnerabilities', [])
        
        print(f"\n💡 **What's Next?**")
        
        if vulnerabilities:
            print("1. 📄 Review detailed reports in the 'reports' directory")
            print("2. 🔍 Validate findings manually before reporting")
            print("3. 📝 Create professional bug bounty reports")
            print("4. 💌 Submit to bug bounty platforms")
        else:
            print("1. ✨ Great! No major vulnerabilities found")
            print("2. 🔄 Consider running a thorough scan for deeper analysis")
            print("3. 🎯 Try scanning subdomains or related assets")
        
        print("5. 🤖 Ask the AI assistant for specific guidance")
        print("6. 📊 Check system health and updates")
    
    def run_setup_wizard(self):
        """User-friendly setup wizard"""
        try:
            print("\n🔧 **First-Time Setup Wizard**")
            print("This will prepare your system for bug bounty hunting!")
            print("="*50)
            
            if not self.initialize_framework():
                return
                
            # Run the actual setup
            self.framework.run_first_time_setup()
            
            print("\n🎉 Setup completed! You're ready to start hunting!")
            
            # Log setup completion
            self.assistant.log_user_activity("setup_complete", success=True)
            
        except Exception as e:
            self.handle_error("Setup failed", str(e), "setup")
    
    def show_system_status(self):
        """Show user-friendly system status"""
        try:
            print("\n📊 **System Health Check**")
            print("="*30)
            
            if not self.initialize_framework():
                return
                
            self.framework.show_system_status()
            
        except Exception as e:
            self.handle_error("Status check failed", str(e), "status")
    
    async def main_loop(self):
        """Main interactive loop"""
        self.welcome_screen()
        
        # Check if this is first run
        try:
            if not self.initialize_framework():
                print("\n🔧 It looks like this is your first time running the scanner.")
                if input("Would you like to run the setup wizard? (Y/n): ").lower() not in ['n', 'no']:
                    self.run_setup_wizard()
        except:
            pass
        
        while True:
            try:
                self.user_session["commands_run"] += 1
                
                command = self.show_simple_menu()
                parsed = self.parse_simple_command(command)
                
                if parsed["action"] == "exit":
                    self.show_goodbye()
                    break
                
                elif parsed["action"] == "scan_wizard":
                    await self.scan_wizard()
                
                elif parsed["action"] == "scan":
                    target = parsed.get("target")
                    if target:
                        await self.run_scan(target)
                    else:
                        await self.scan_wizard()
                
                elif parsed["action"] == "setup":
                    self.run_setup_wizard()
                
                elif parsed["action"] == "status":
                    self.show_system_status()
                
                elif parsed["action"] == "chat":
                    print("\n🤖 Starting AI Assistant...")
                    self.assistant.start_interactive_chat()
                
                elif parsed["action"] == "feedback":
                    self.assistant.feedback_wizard()
                
                elif parsed["action"] == "help":
                    self.show_detailed_help()
                
                elif parsed["action"] == "unknown":
                    print(f"\n🤔 I didn't understand '{parsed['original']}'")
                    print("Let me connect you with the AI assistant for help!")
                    
                    # Auto-route to AI for unclear commands
                    response = self.assistant.get_ai_response(parsed['original'])
                    print(f"\n🤖 AI Assistant: {response}")
                    
                    if input("\nWould you like to continue chatting? (y/N): ").lower() == 'y':
                        self.assistant.start_interactive_chat()
                
                # Small pause for better UX
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n\n👋 Thanks for using the Friendly Scanner!")
                break
            except Exception as e:
                self.handle_error("Unexpected error in main loop", str(e))
                print("Don't worry - the tool is still running!")
    
    def show_detailed_help(self):
        """Show comprehensive help"""
        if self.initialize_framework():
            self.framework.show_help()
        
        print(f"\n🤖 **AI Assistant Available:**")
        print("Type 'chat' anytime to get personalized help!")
        print("The AI can help with:")
        print("• Specific error messages")
        print("• Best practices")
        print("• Tool usage")
        print("• Bug bounty tips")
    
    def show_goodbye(self):
        """Show goodbye message with session stats"""
        print("\n" + "="*50)
        print("👋 **Thank you for using the Friendly Scanner!**")
        print("="*50)
        
        # Show session statistics
        duration = (datetime.now() - datetime.fromisoformat(self.user_session["started_at"])).total_seconds()
        print(f"📊 Session Summary:")
        print(f"   ⏱️  Time used: {duration/60:.1f} minutes")
        print(f"   🎯 Commands run: {self.user_session['commands_run']}")
        print(f"   ✅ Scans completed: {self.user_session['scans_completed']}")
        print(f"   ⚠️  Errors encountered: {self.user_session['errors_encountered']}")
        
        # Log session end
        self.assistant.log_user_activity(
            action="session_end",
            success=True,
            duration=duration,
            details=self.user_session
        )
        
        print(f"\n💡 **Tips for next time:**")
        print("• Your scan results are saved in the 'reports' directory")
        print("• Use 'chat' command for instant AI help")
        print("• Check 'status' regularly to keep tools updated")
        print("\n🚀 Happy bug hunting!")

def main():
    """Main entry point"""
    try:
        scanner = FriendlyScanner()
        asyncio.run(scanner.main_loop())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("Please report this issue!")

if __name__ == "__main__":
    main()
