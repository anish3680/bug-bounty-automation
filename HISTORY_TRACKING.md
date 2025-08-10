# 📊 History Tracking System - User Guide

## Overview

The Bug Bounty Automation Framework includes a comprehensive history tracking system that automatically logs all activities, providing detailed insights into your scanning operations, updates, and system health.

## 🎯 Features

### Automatic Tracking
- **All Activities Logged**: Every scan, update, configuration change is automatically tracked
- **Detailed Metadata**: Duration, targets, results, error messages, and user information
- **SQLite Database**: Efficient, local storage with advanced querying capabilities
- **No Manual Intervention**: Everything happens automatically in the background

### Activity Types Tracked
- **🔍 Scans**: Vulnerability scans with targets, duration, and results
- **🔄 Updates**: Tool updates, template updates, framework updates
- **⚙️ Configuration**: Setup changes and configuration modifications
- **📝 Reports**: Report generation and email sending
- **📦 Installation**: Tool and AI model installations
- **🚨 Errors**: Failed operations with detailed error information
- **🖥️ System**: Framework startup and system events
- **🤖 AI Models**: AI model installations and usage
- **📧 Email**: Email notifications and reports

### Status Tracking
- **✅ Success**: Completed operations
- **❌ Failed**: Operations that encountered errors
- **⏳ In Progress**: Currently running operations
- **🚫 Cancelled**: User-cancelled operations
- **⚠️ Partial**: Partially completed operations

## 🚀 Usage

### Basic Commands

#### View Recent Activity
```bash
# Show last 10 activities (default)
python3 bug_bounty_scanner.py history

# Show last 20 activities
python3 bug_bounty_scanner.py history --recent 20
```

#### Activity Summary
```bash
# Show summary for last 30 days (default)
python3 bug_bounty_scanner.py history --summary 30

# Show summary for last 7 days
python3 bug_bounty_scanner.py history --summary 7
```

#### Scan-Specific History
```bash
# Show all scans for a specific target
python3 bug_bounty_scanner.py history --scans example.com

# Show all scan history
python3 bug_bounty_scanner.py history --scans ""
```

#### Update History
```bash
# Show all update activities
python3 bug_bounty_scanner.py history --updates
```

#### Search History
```bash
# Search for specific terms
python3 bug_bounty_scanner.py history --search "nuclei"
python3 bug_bounty_scanner.py history --search "error"
python3 bug_bounty_scanner.py history --search "example.com"
```

#### Export History
```bash
# Export to JSON (default)
python3 bug_bounty_scanner.py history --export history_backup.json

# Export to CSV
python3 bug_bounty_scanner.py history --export history_backup.csv
```

### Standalone History Manager

The history system can also be used independently:

```bash
# Direct usage
python3 history_manager.py

# Database statistics
python3 history_manager.py --stats

# Activity summary
python3 history_manager.py --summary 14

# Search entries
python3 history_manager.py --search "vulnerability"

# Export data
python3 history_manager.py --export my_history.json --format json

# Cleanup old entries (older than 90 days)
python3 history_manager.py --cleanup 90
```

## 📈 Understanding the Data

### Activity Summary Report
```
📊 Activity Summary (Last 30 days)
==================================================
📈 Total Activities: 156
✅ Success Rate: 94.2%

🎯 Activities by Type:
   scan: 45
   update: 12
   system: 8
   config: 3

📊 Activities by Status:
   success: 147
   failed: 9

🎯 Most Active Targets:
   example.com: 15 scans
   test.com: 8 scans
   target.org: 5 scans
```

### Recent Activity Display
```
📊 Recent Activity (Last 10 entries)
================================================================================
✅ 🔍 [2025-01-10 15:30:22] Scan completed successfully - 3 vulnerabilities found → example.com (45.2s)
✅ 🔄 [2025-01-10 14:15:10] Security tools updated successfully (12.5s)
❌ 🔍 [2025-01-10 13:05:33] Scan failed for test.invalid (2.1s)
   💥 DNS resolution failed for test.invalid
✅ 🖥️ [2025-01-10 12:00:00] Bug Bounty Framework Started
```

### Database Statistics
```
📊 Database Statistics
==============================
📈 Total Entries: 1,247
💾 Database Size: 2.5 MB
📅 Date Range: 2024-12-01 to 2025-01-10
📂 Database Path: /home/user/bug-bounty-automation/history.db
```

## 🛠️ Advanced Usage

### Programmatic Access

You can also access the history system programmatically:

```python
from history_manager import HistoryManager, ActivityType, ActivityStatus

# Initialize history manager
history = HistoryManager()

# Add custom entry
history.add_entry(
    activity_type=ActivityType.SCAN,
    status=ActivityStatus.SUCCESS,
    target="example.com",
    description="Custom scan completed",
    duration=30.5,
    results={"vulnerabilities": 2, "severity": "medium"}
)

# Query entries
recent_scans = history.get_scan_history(target="example.com", limit=10)
summary = history.get_activity_summary(days_back=30)

# Export data
history.export_history("backup.json", format="json")
```

### Database Schema

The history is stored in a SQLite database with the following structure:

```sql
CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    status TEXT NOT NULL,
    target TEXT,
    description TEXT,
    details TEXT,        -- JSON: additional metadata
    duration REAL,       -- seconds
    user TEXT,
    version TEXT,
    errors TEXT,         -- JSON: error messages
    results TEXT,        -- JSON: operation results
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Configuration & Maintenance

### Database Location
- Default: `/home/user/bug-bounty-automation/history.db`
- Configurable via HistoryManager constructor
- Automatically created on first use

### Automatic Cleanup
```bash
# Remove entries older than 90 days (default)
python3 history_manager.py --cleanup 90

# Remove entries older than 30 days
python3 history_manager.py --cleanup 30
```

### Backup & Recovery
```bash
# Create backup
python3 history_manager.py --export full_backup_$(date +%Y%m%d).json

# Database file backup
cp history.db history_backup_$(date +%Y%m%d).db
```

## 📊 Integration with Other Components

### Scan Integration
- Automatically logs scan start/completion
- Records target, duration, vulnerabilities found
- Tracks scan modes (fast, thorough, normal)
- Logs errors with detailed messages

### Update Integration  
- Tracks tool updates (nuclei, subfinder, etc.)
- Records template updates
- Logs framework updates
- Monitors success/failure rates

### Configuration Integration
- Logs configuration changes
- Tracks setup wizard runs
- Records email setup changes

### AI Model Integration
- Tracks model installations
- Logs AI service availability
- Records model usage statistics

## 🎯 Use Cases

### Performance Monitoring
- Track scan durations over time
- Identify frequently scanned targets
- Monitor update frequency and success rates

### Debugging & Troubleshooting
- Search for error patterns
- Identify failing components
- Track configuration changes that caused issues

### Reporting & Analytics
- Generate activity reports for management
- Track productivity metrics
- Monitor system health trends

### Audit & Compliance
- Maintain records of all security activities
- Export data for compliance reporting
- Track user activities and system changes

## 🔐 Privacy & Security

### Data Storage
- All data stored locally in SQLite database
- No data sent to external services
- User has full control over data retention

### Sensitive Information
- Passwords and API keys are never logged
- Error messages are sanitized
- Personal data handling follows best practices

### Access Control
- Database file permissions set to user-only
- No network access required
- Logs can be encrypted if needed

## 🚀 Future Enhancements

### Planned Features
- **Web Dashboard**: Visual analytics and charts
- **Real-time Monitoring**: Live activity feed
- **Advanced Filtering**: Complex query capabilities  
- **Alerts**: Notification on specific events
- **Integration**: Export to monitoring systems

### Customization Options
- **Custom Activity Types**: Add your own categories
- **Flexible Storage**: Alternative database backends
- **Advanced Analytics**: Machine learning insights
- **API Integration**: RESTful API for external tools

## 📞 Support & Troubleshooting

### Common Issues

**Database Lock Error**
```bash
# Check if another process is using the database
lsof history.db

# Solution: Wait for other processes to complete or restart framework
```

**Large Database Size**
```bash
# Check database size
python3 history_manager.py --stats

# Cleanup old entries
python3 history_manager.py --cleanup 60
```

**Missing Entries**
- Ensure framework has write permissions to directory
- Check if logging is disabled in configuration
- Verify database file is not corrupted

### Getting Help
- Check logs in `updater.log` for debugging information
- Run `python3 history_manager.py --stats` to verify database health
- Use `--search` to find specific activities or errors

---

*The History Tracking System is designed to provide comprehensive visibility into your bug bounty automation activities while maintaining privacy and performance.*
