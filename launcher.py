#!/usr/bin/env python3
"""
Bug Bounty Automation Framework - Main Launcher
User-friendly entry point with all features integrated
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

def main():
    """Main launcher with simple interface selection"""
    
    print("🚀 Bug Bounty Automation Framework")
    print("=" * 40)
    
    parser = argparse.ArgumentParser(
        description="Bug Bounty Automation Framework - Choose your interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Interface Options:
  --friendly    Launch user-friendly interface (recommended for beginners)
  --advanced    Launch advanced CLI interface (for experienced users)
  --chat        Start AI assistant chat
  --admin       Admin panel (password protected)

Quick Commands:
  python3 launcher.py                    # Interactive menu
  python3 launcher.py --friendly         # Friendly interface
  python3 launcher.py scan example.com   # Quick scan
  python3 launcher.py --chat            # AI chat
  python3 launcher.py --admin           # Admin panel

Examples:
  python3 launcher.py --friendly        # Best for new users
  python3 launcher.py scan example.com  # Quick vulnerability scan
  python3 launcher.py --chat           # Get help from AI
        """
    )
    
    parser.add_argument('--friendly', action='store_true', 
                       help='Launch user-friendly interface')
    parser.add_argument('--advanced', action='store_true',
                       help='Launch advanced CLI interface')
    parser.add_argument('--chat', action='store_true',
                       help='Start AI assistant')
    parser.add_argument('--admin', action='store_true',
                       help='Access admin panel')
    
    # Quick scan command
    parser.add_argument('command', nargs='?', help='Quick command (scan, chat, etc.)')
    parser.add_argument('target', nargs='?', help='Target domain for quick scan')
    
    args = parser.parse_args()
    
    # Handle quick commands
    if args.command == 'scan' and args.target:
        print(f"🎯 Quick scan mode: {args.target}")
        launch_quick_scan(args.target)
        return
    
    if args.command == 'chat' or args.chat:
        launch_ai_chat()
        return
    
    if args.admin:
        launch_admin_panel()
        return
    
    if args.advanced:
        launch_advanced_interface()
        return
    
    if args.friendly:
        launch_friendly_interface()
        return
    
    # No arguments - show interactive menu
    show_interface_menu()

def show_interface_menu():
    """Show interface selection menu"""
    print("\n🎛️  Choose Your Interface:")
    print("=" * 30)
    print("1. 🌟 Friendly Interface (Recommended for beginners)")
    print("2. 🔧 Advanced Interface (For experienced users)")
    print("3. 🤖 AI Assistant Chat")
    print("4. 📊 System Status")
    print("5. 🚪 Exit")
    print("=" * 30)
    
    try:
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            launch_friendly_interface()
        elif choice == '2':
            launch_advanced_interface()
        elif choice == '3':
            launch_ai_chat()
        elif choice == '4':
            show_quick_status()
        elif choice == '5':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice. Please select 1-5.")
            show_interface_menu()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

def launch_friendly_interface():
    """Launch the user-friendly interface"""
    print("\n🌟 Starting Friendly Interface...")
    try:
        os.system("python3 friendly_scanner.py")
    except Exception as e:
        print(f"❌ Failed to start friendly interface: {e}")
        print("Trying fallback method...")
        import friendly_scanner
        friendly_scanner.main()

def launch_advanced_interface():
    """Launch the advanced CLI interface"""
    print("\n🔧 Starting Advanced Interface...")
    print("Available commands: scan, status, setup, config, update, health, history, help")
    print("Example: python3 bug_bounty_scanner.py scan example.com")
    print("Type 'python3 bug_bounty_scanner.py help' for full documentation")

def launch_ai_chat():
    """Launch AI assistant"""
    print("\n🤖 Starting AI Assistant...")
    try:
        from ai_assistant import AIAssistant
        assistant = AIAssistant()
        assistant.start_interactive_chat()
    except ImportError:
        print("❌ AI Assistant not available. Please check installation.")
    except Exception as e:
        print(f"❌ Failed to start AI assistant: {e}")

def launch_admin_panel():
    """Launch admin panel"""
    print("\n🔐 Starting Admin Panel...")
    try:
        os.system("python3 bug_bounty_scanner.py admin")
    except Exception as e:
        print(f"❌ Failed to start admin panel: {e}")

def launch_quick_scan(target: str):
    """Launch quick scan"""
    print(f"🚀 Starting quick scan of {target}...")
    try:
        os.system(f"python3 bug_bounty_scanner.py scan {target}")
    except Exception as e:
        print(f"❌ Quick scan failed: {e}")

def show_quick_status():
    """Show quick system status"""
    print("\n📊 System Status:")
    try:
        os.system("python3 bug_bounty_scanner.py status")
    except Exception as e:
        print(f"❌ Status check failed: {e}")
    
    input("\nPress Enter to continue...")
    show_interface_menu()

if __name__ == "__main__":
    main()
