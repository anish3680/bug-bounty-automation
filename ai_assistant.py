#!/usr/bin/env python3
"""
AI Assistant for Bug Bounty Automation Framework
Provides intelligent help, chat support, and user guidance
"""

import os
import sys
import json
import time
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
import requests
import subprocess

class AIAssistant:
    def __init__(self):
        self.db_path = "user_analytics.db"
        self.feedback_file = "user_feedback.json"
        self.conversation_history = []
        self.setup_database()
        
        # Pre-defined responses for common questions
        self.knowledge_base = {
            "scan": {
                "keywords": ["scan", "scanning", "vulnerability", "target", "how to scan"],
                "response": """🎯 **How to Run a Scan:**

1. **Basic scan**: `python3 bug_bounty_scanner.py scan example.com`
2. **Fast scan**: `python3 bug_bounty_scanner.py scan example.com --fast`
3. **Thorough scan**: `python3 bug_bounty_scanner.py scan example.com --thorough`
4. **With email**: `python3 bug_bounty_scanner.py scan example.com --email`

**Tips:**
- Replace 'example.com' with your target domain
- Use --thorough for comprehensive results
- Make sure you have permission to scan the target!
""",
                "follow_up": "Would you like me to help you run your first scan? What's your target domain?"
            },
            
            "setup": {
                "keywords": ["setup", "install", "configuration", "first time", "getting started"],
                "response": """🔧 **Getting Started:**

1. **First-time setup**: `python3 bug_bounty_scanner.py setup`
2. **Check status**: `python3 bug_bounty_scanner.py status`
3. **Configure tools**: `python3 bug_bounty_scanner.py config`

**What setup does:**
- Installs required security tools
- Sets up configurations
- Prepares AI models
- Creates necessary directories
""",
                "follow_up": "Want me to guide you through the setup process step by step?"
            },
            
            "tools": {
                "keywords": ["tools", "missing", "install tools", "requirements"],
                "response": """🛠️ **Tool Management:**

**Check tool status**: `python3 bug_bounty_scanner.py status`
**Update tools**: `python3 bug_bounty_scanner.py update --tools`

**Common tools we install:**
- Subfinder (subdomain discovery)
- Nuclei (vulnerability scanner)  
- httpx (HTTP toolkit)
- nmap (network scanner)
- And many more...
""",
                "follow_up": "Having trouble with a specific tool? Let me know which one!"
            },
            
            "error": {
                "keywords": ["error", "failed", "not working", "problem", "issue"],
                "response": """❌ **Troubleshooting Guide:**

1. **Check system status**: `python3 bug_bounty_scanner.py status`
2. **Run health check**: `python3 bug_bounty_scanner.py health`
3. **Update everything**: `python3 bug_bounty_scanner.py update`
4. **Re-run setup**: `python3 bug_bounty_scanner.py setup`

**Common fixes:**
- Make sure you have internet connection
- Run with `sudo` if permission errors
- Check if target domain is accessible
""",
                "follow_up": "What specific error message are you seeing? I can help diagnose it!"
            },
            
            "email": {
                "keywords": ["email", "report", "notification", "send results"],
                "response": """📧 **Email Configuration:**

1. **Run config wizard**: `python3 bug_bounty_scanner.py config`
2. **Set up your email settings** (SMTP server, credentials)
3. **Test with**: `python3 bug_bounty_scanner.py scan example.com --email`

**Email features:**
- Automatic report sending
- Professional formatting
- Attachment support
- Multiple recipients
""",
                "follow_up": "Need help setting up your email provider? I can guide you!"
            }
        }
    
    def setup_database(self):
        """Setup SQLite database for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                action TEXT NOT NULL,
                target TEXT,
                success BOOLEAN,
                duration REAL,
                error_message TEXT,
                user_agent TEXT,
                ip_address TEXT,
                command_used TEXT,
                details TEXT
            )
        ''')
        
        # Chat conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                user_message TEXT,
                assistant_response TEXT,
                satisfaction INTEGER,
                resolved BOOLEAN
            )
        ''')
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                rating INTEGER,
                category TEXT,
                message TEXT,
                email TEXT,
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_user_activity(self, action: str, target: str = None, success: bool = True, 
                         duration: float = 0, error_message: str = None, 
                         command_used: str = None, details: Dict = None):
        """Log user activity for analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO user_analytics 
                (timestamp, action, target, success, duration, error_message, 
                 command_used, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                action,
                target,
                success,
                duration,
                error_message,
                command_used,
                json.dumps(details) if details else None
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"📊 Analytics logging failed: {e}")
    
    def find_best_response(self, user_input: str) -> Dict[str, Any]:
        """Find the best response based on user input"""
        user_input_lower = user_input.lower()
        
        best_match = None
        max_score = 0
        
        for topic, data in self.knowledge_base.items():
            score = 0
            for keyword in data["keywords"]:
                if keyword in user_input_lower:
                    score += 1
            
            if score > max_score:
                max_score = score
                best_match = data
        
        return best_match if max_score > 0 else None
    
    def get_ai_response(self, user_input: str) -> str:
        """Get AI response using local models or fallback"""
        try:
            # Try Ollama first
            response = self.query_ollama(user_input)
            if response:
                return response
        except:
            pass
        
        # Fallback to knowledge base
        match = self.find_best_response(user_input)
        if match:
            return match["response"] + "\n\n" + match.get("follow_up", "")
        
        # Generic helpful response
        return """🤖 I'm here to help! Here are some things I can assist with:

• **Scanning targets**: How to run vulnerability scans
• **Setup & Installation**: Getting the tool ready
• **Troubleshooting**: Fixing errors and issues
• **Configuration**: Setting up email, tools, etc.
• **Best practices**: Tips for effective bug bounty hunting

What would you like to know more about?"""
    
    def query_ollama(self, prompt: str) -> str:
        """Query local Ollama model"""
        try:
            # Enhanced prompt for bug bounty context
            enhanced_prompt = f"""You are a helpful AI assistant for a bug bounty automation tool. 
The user is asking: {prompt}

Please provide a helpful, practical response about bug bounty hunting, security scanning, 
or using security tools. Keep it friendly and actionable."""

            result = subprocess.run([
                'curl', '-s', 'http://localhost:11434/api/generate',
                '-d', json.dumps({
                    "model": "llama2",
                    "prompt": enhanced_prompt,
                    "stream": False
                })
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                response_data = json.loads(result.stdout)
                return response_data.get('response', '').strip()
                
        except Exception as e:
            print(f"🤖 AI query failed: {e}")
        
        return None
    
    def save_chat(self, user_message: str, assistant_response: str, user_id: str = "anonymous"):
        """Save chat conversation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO chat_history 
                (timestamp, user_id, user_message, assistant_response)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                user_id,
                user_message,
                assistant_response
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"💬 Chat logging failed: {e}")
    
    def collect_feedback(self, rating: int = None, category: str = None, 
                        message: str = None, email: str = None):
        """Collect user feedback"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO feedback 
                (timestamp, rating, category, message, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                rating,
                category,
                message,
                email
            ))
            
            conn.commit()
            conn.close()
            
            print("✅ Thank you for your feedback! It helps us improve.")
            
        except Exception as e:
            print(f"📝 Feedback collection failed: {e}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total scans
            cursor.execute("SELECT COUNT(*) FROM user_analytics WHERE action = 'scan'")
            total_scans = cursor.fetchone()[0]
            
            # Success rate
            cursor.execute("SELECT COUNT(*) FROM user_analytics WHERE action = 'scan' AND success = 1")
            successful_scans = cursor.fetchone()[0]
            
            # Popular targets
            cursor.execute("""
                SELECT target, COUNT(*) as count 
                FROM user_analytics 
                WHERE target IS NOT NULL 
                GROUP BY target 
                ORDER BY count DESC 
                LIMIT 5
            """)
            popular_targets = cursor.fetchall()
            
            # Recent errors
            cursor.execute("""
                SELECT error_message, COUNT(*) as count 
                FROM user_analytics 
                WHERE error_message IS NOT NULL 
                GROUP BY error_message 
                ORDER BY count DESC 
                LIMIT 5
            """)
            common_errors = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_scans": total_scans,
                "successful_scans": successful_scans,
                "success_rate": (successful_scans / total_scans * 100) if total_scans > 0 else 0,
                "popular_targets": popular_targets,
                "common_errors": common_errors
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def auto_fix_error(self, error_message: str, command_used: str = None) -> str:
        """Auto-suggest fixes for common errors"""
        error_lower = error_message.lower()
        
        # Common error patterns and fixes
        fixes = {
            "permission denied": {
                "fix": "Try running with sudo: `sudo python3 bug_bounty_scanner.py ...`",
                "reason": "The command needs administrator privileges"
            },
            "command not found": {
                "fix": "Install missing tools: `python3 bug_bounty_scanner.py update --tools`",
                "reason": "Required security tools are not installed"
            },
            "connection refused": {
                "fix": "Check internet connection and target accessibility",
                "reason": "Cannot connect to the target or external services"
            },
            "no such file": {
                "fix": "Run setup first: `python3 bug_bounty_scanner.py setup`",
                "reason": "Configuration files or directories are missing"
            },
            "timeout": {
                "fix": "Target may be slow. Try: `python3 bug_bounty_scanner.py scan target --fast`",
                "reason": "Scan is taking too long, use faster scan mode"
            },
            "dns": {
                "fix": "Check domain spelling and try again",
                "reason": "Domain name cannot be resolved"
            }
        }
        
        for pattern, solution in fixes.items():
            if pattern in error_lower:
                return f"""🔧 **Auto-Fix Suggestion:**

**Error**: {error_message}
**Solution**: {solution['fix']}
**Why**: {solution['reason']}

Need more help? Type 'help error' for detailed troubleshooting!"""
        
        return f"""🤖 **Error Detected**: {error_message}

I couldn't auto-fix this specific error, but here are general troubleshooting steps:

1. `python3 bug_bounty_scanner.py status` - Check system health
2. `python3 bug_bounty_scanner.py update` - Update all components  
3. `python3 bug_bounty_scanner.py setup` - Re-run setup if needed

Want to chat about this error? I'm here to help! 💬"""
    
    def start_interactive_chat(self):
        """Start interactive chat session"""
        print("\n" + "="*60)
        print("🤖 **AI Assistant** - I'm here to help!")
        print("="*60)
        print("Ask me anything about:")
        print("• Running scans")
        print("• Setting up tools") 
        print("• Fixing errors")
        print("• Best practices")
        print("• General questions")
        print("\nType 'quit' to exit, 'feedback' to give feedback")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n🧑‍💻 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n🤖 Goodbye! Feel free to ask for help anytime!")
                    break
                
                if user_input.lower() == 'feedback':
                    self.feedback_wizard()
                    continue
                
                # Get AI response
                response = self.get_ai_response(user_input)
                print(f"\n🤖 Assistant: {response}")
                
                # Save conversation
                self.save_chat(user_input, response)
                
                # Ask for satisfaction
                try:
                    satisfaction = input("\nWas this helpful? (y/n): ").lower()
                    if satisfaction == 'n':
                        follow_up = input("What else can I help with? ")
                        if follow_up.strip():
                            response = self.get_ai_response(follow_up)
                            print(f"\n🤖 Assistant: {response}")
                except:
                    pass
                
            except KeyboardInterrupt:
                print("\n\n🤖 Chat ended. Thanks for using the AI Assistant!")
                break
            except Exception as e:
                print(f"\n🤖 Sorry, I encountered an error: {e}")
    
    def feedback_wizard(self):
        """Interactive feedback collection"""
        print("\n" + "="*50)
        print("📝 **Feedback & Support**")
        print("="*50)
        
        try:
            # Rating
            print("How would you rate your experience? (1-5)")
            rating = int(input("Rating: "))
            
            # Category
            print("\nWhat category is your feedback about?")
            print("1. Tool functionality")
            print("2. User interface")
            print("3. Documentation")
            print("4. Performance")
            print("5. Bug report")
            print("6. Feature request")
            
            category_map = {
                1: "functionality", 2: "interface", 3: "documentation",
                4: "performance", 5: "bug", 6: "feature_request"
            }
            
            cat_choice = int(input("Category (1-6): "))
            category = category_map.get(cat_choice, "general")
            
            # Message
            message = input("\nPlease describe your feedback: ")
            
            # Optional email
            email = input("Email (optional, for follow-up): ").strip()
            if not email:
                email = None
            
            # Save feedback
            self.collect_feedback(rating, category, message, email)
            
        except KeyboardInterrupt:
            print("\nFeedback cancelled.")
        except Exception as e:
            print(f"Feedback collection failed: {e}")

def main():
    """Main function for standalone usage"""
    assistant = AIAssistant()
    
    if len(sys.argv) < 2:
        assistant.start_interactive_chat()
        return
    
    command = sys.argv[1].lower()
    
    if command == "chat":
        assistant.start_interactive_chat()
    elif command == "stats":
        stats = assistant.get_usage_stats()
        print(json.dumps(stats, indent=2))
    elif command == "feedback":
        assistant.feedback_wizard()
    else:
        print("Usage: python3 ai_assistant.py [chat|stats|feedback]")

if __name__ == "__main__":
    main()
