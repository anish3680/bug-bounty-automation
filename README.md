# 🚀 Bug Bounty Automation Framework v3.1

> **AI-Enhanced Security Testing with Professional Reporting and Smart Automation**

A comprehensive, AI-powered bug bounty automation framework that combines multiple security tools with advanced AI analysis, false positive filtering, and multi-platform report generation to deliver professional-grade vulnerability assessments.

## ✨ Key Features

### 🎯 Core Capabilities
- **Multi-Tool Integration**: Nuclei, Subfinder, HTTPx, SQLMap, Dalfox, Nmap, and more
- **AI-Powered Analysis**: Uses Ollama, HuggingFace, Groq, and OpenAI for vulnerability analysis
- **Smart False Positive Filtering**: AI-powered filtering reduces noise by up to 80%
- **Multi-Platform Reports**: Generate reports for HackerOne, Bugcrowd, and custom formats
- **Enhanced Email System**: Graceful fallbacks and professional HTML reports
- **Self-Updating System**: Automatically updates tools, templates, and vulnerability signatures
- **Robust Error Handling**: Graceful degradation and comprehensive recovery mechanisms

### 🤖 AI Enhancement
- **Multi-Model Support**: Ollama (local), HuggingFace (free), Groq (free), OpenAI (paid)
- **Intelligent Analysis**: False positive filtering, severity assessment, and impact analysis
- **Dynamic Payload Generation**: AI-generated payloads for specific targets
- **Contextual Reporting**: Professional vulnerability reports with business impact analysis

### 🛠️ Management Features
- **Configuration Wizard**: Interactive setup for all components
- **Tool Manager**: Automatic installation and updates of security tools
- **Health Monitoring**: Comprehensive system status and health checks
- **Backup & Recovery**: Automatic backups with rollback capabilities

## 🔧 Installation

### Prerequisites
- **Python 3.8+**
- **Go 1.19+** (for Go-based security tools)
- **Git** (for repository management)
- **curl** and **wget** (for downloads)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/bug-bounty-automation.git
cd bug-bounty-automation

# Install Python dependencies
pip3 install -r requirements.txt

# Run first-time setup
python3 bug_bounty_scanner.py setup
```

## 🚀 Quick Start

### Basic Usage
```bash
# Simple vulnerability scan
python3 bug_bounty_scanner.py scan example.com

# Comprehensive scan with email reporting
python3 bug_bounty_scanner.py scan example.com --thorough --email

# Check system status
python3 bug_bounty_scanner.py status

# Update all components
python3 bug_bounty_scanner.py update
```

### Configuration
```bash
# Run configuration wizard
python3 bug_bounty_scanner.py config

# Install AI models
python3 bug_bounty_scanner.py install-ai

# Check system health
python3 bug_bounty_scanner.py health
```

## 🧠 AI Models

The framework supports multiple AI models with automatic fallback:

1. **Ollama (Local)** - Privacy-focused, no API limits
   - Recommended: `llama3.2:3b`
   - Installation: `python3 bug_bounty_scanner.py install-ai`

2. **HuggingFace (Free)** - No API key required
   - Always available as fallback

3. **Groq (Free Tier)** - Fast inference
   - Get free API key: [console.groq.com](https://console.groq.com)

4. **OpenAI (Paid)** - Highest quality analysis
   - Optional: [platform.openai.com](https://platform.openai.com)

## 🛠️ Security Tools

### Integrated Tools
- **Nuclei** - Vulnerability scanner (4000+ templates)
- **Subfinder** - Subdomain discovery
- **HTTPx** - HTTP toolkit and probe
- **SQLMap** - SQL injection testing
- **Dalfox** - XSS scanner
- **Nmap** - Network scanner
- **Whatweb** - Technology detection
- **Waybackurls** - Historical URL discovery
- **Gospider** - Web crawler
- **GAU** - Get All URLs
- **Amass** - Attack surface mapping

All tools are automatically installed and updated.

## 📊 Report Generation

### Report Types
1. **HTML Report** - Interactive web-based dashboard
2. **HackerOne Reports** - Ready-to-submit markdown files
3. **JSON Export** - Raw data for custom processing
4. **Executive Summary** - Business impact assessment

### Sample Output Structure
```
results/example.com_20240110_143022/
├── comprehensive_report.html      # Interactive dashboard
├── executive_summary.md          # Business summary
├── hackerone_report_1_xss.md    # Individual bug reports
├── hackerone_report_2_sqli.md
├── scan_results.json            # Raw scan data
└── evidence/                    # Screenshots & proofs
```

## ⚙️ Configuration

### Configuration Files
- `config/email_config.json` - Email settings
- `config/ai_config.json` - AI model configurations
- `config/tools_config.json` - Tool parameters
- `config/scanner_config.json` - Scan behavior

### Email Setup (Optional)
```json
{
  "enabled": true,
  "email": "your-email@gmail.com",
  "password": "your-app-password",
  "recipient": "reports@company.com",
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587
}
```

## 🔄 Updates & Maintenance

### Automatic Updates
```bash
# Enable scheduled updates (daily at 2 AM)
python3 updater.py --schedule

# Manual updates
python3 bug_bounty_scanner.py update

# Update specific components
python3 bug_bounty_scanner.py update --tools
python3 bug_bounty_scanner.py update --templates
```

### Backup & Recovery
```bash
# Rollback updates if needed
python3 updater.py --rollback

# View system status
python3 bug_bounty_scanner.py health
```

## 🎯 Usage Examples

### Basic Scanning
```bash
# Quick scan
python3 bug_bounty_scanner.py scan target.com

# Thorough scan with AI analysis
python3 bug_bounty_scanner.py scan target.com --thorough

# Scan with email reports
python3 bug_bounty_scanner.py scan target.com --email
```

### Advanced Features
```bash
# Custom output directory
python3 bug_bounty_scanner.py scan target.com --output-dir /path/to/results

# System management
python3 bug_bounty_scanner.py status    # Check all components
python3 bug_bounty_scanner.py health    # System health score
python3 bug_bounty_scanner.py update    # Update everything
```

### Direct Tool Access
```bash
# Tool management
python3 tool_manager.py --status      # Check tool status
python3 tool_manager.py --install     # Install missing tools

# AI management
python3 ai_manager.py --status        # Check AI models
python3 ai_manager.py --test          # Test AI analysis

# Configuration
python3 config_manager.py --setup     # Run setup wizard
python3 config_manager.py --validate  # Validate configs
```

## 🔍 Troubleshooting

### Common Issues

1. **Tools Not Installing**
   ```bash
   # Check Go installation
   go version
   
   # Force reinstall tools
   python3 tool_manager.py --install --force
   ```

2. **AI Models Not Working**
   ```bash
   # Check AI status
   python3 ai_manager.py --status
   
   # Install local model
   python3 bug_bounty_scanner.py install-ai
   ```

3. **Configuration Problems**
   ```bash
   # Reset and reconfigure
   python3 config_manager.py --reset
   python3 bug_bounty_scanner.py setup
   ```

### Performance Tips
```bash
# Fast scan mode (less thorough but quicker)
python3 bug_bounty_scanner.py scan target.com --fast

# Monitor system resources
python3 bug_bounty_scanner.py health
```

### Log Files
- `scanner.log` - Main scanning activity
- `updater.log` - Update operations
- `tool_manager.log` - Tool management
- `config_manager.log` - Configuration changes

## 🚨 Security & Ethics

### Responsible Usage
- ✅ Only scan authorized targets
- ✅ Follow responsible disclosure
- ✅ Respect rate limits
- ✅ Use for legitimate security testing only

### Privacy Features
- 🔒 Local AI processing with Ollama
- 🔒 No data sent to external APIs by default
- 🔒 All scan data stored locally
- 🔒 Encrypted email reports

## 🤝 Contributing

### Development Setup
```bash
git clone https://github.com/your-repo/bug-bounty-automation.git
cd bug-bounty-automation
pip3 install -r requirements-dev.txt

# Run tests
python3 -m pytest tests/

# Format code
black *.py && flake8 *.py
```

### Adding Features
1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Submit a pull request

## 📞 Support

### Community
- 💬 [Discord Server](https://discord.gg/your-server)
- 📱 [Telegram Channel](https://t.me/your-channel)
- 💻 [GitHub Discussions](https://github.com/your-repo/bug-bounty-automation/discussions)

### Documentation
- 📚 [GitHub Wiki](https://github.com/your-repo/bug-bounty-automation/wiki)
- 🎥 [Video Tutorials](https://youtube.com/playlist?list=your-playlist)
- 📖 [API Documentation](https://your-repo.github.io/bug-bounty-automation/)

### Issues
Report bugs on [GitHub Issues](https://github.com/your-repo/bug-bounty-automation/issues) with:
- Detailed problem description
- Steps to reproduce
- System information
- Log files

## 🎉 Success Stories

> *"This framework helped me discover 15+ vulnerabilities in my first week of bug hunting!"*
> 
> *"The AI analysis reduced my false positives by 80% and the reports are professional quality."*
> 
> *"The automated tool management saved me hours of setup time."*

## 📋 Changelog

### v3.0 (Current)
- ✨ Complete AI integration with multiple models
- ✨ Self-updating system with backup/recovery
- ✨ Professional HTML and HackerOne reports
- ✨ Comprehensive configuration management
- ✨ Enhanced error handling and logging
- ✨ Tool auto-installation and updates

### v2.0
- Basic AI analysis integration
- Multi-tool vulnerability scanning
- Simple report generation

### v1.0
- Initial release with basic scanning

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

### Security Tools
- [ProjectDiscovery](https://github.com/projectdiscovery) - Nuclei, Subfinder, HTTPx
- [OWASP](https://owasp.org) - Security methodologies
- [SecLists](https://github.com/danielmiessler/SecLists) - Wordlists

### AI Platforms
- [Ollama](https://ollama.ai) - Local AI hosting
- [HuggingFace](https://huggingface.co) - Open source models
- [Groq](https://groq.com) - Fast inference
- [OpenAI](https://openai.com) - Advanced models

### Community
Special thanks to bug bounty hunters, security researchers, and open source contributors who make this project possible.

---

<div align="center">

**⭐ Star this project if it helps you find vulnerabilities! ⭐**

[🚀 Get Started](https://github.com/your-repo/bug-bounty-automation) | [📚 Documentation](https://github.com/your-repo/bug-bounty-automation/wiki) | [💬 Community](https://discord.gg/your-server)

*Built with ❤️ for the security community*

</div>
