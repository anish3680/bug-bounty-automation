#!/usr/bin/env python3
"""
History Management System for Bug Bounty Automation Framework
Tracks all activities, updates, scans, and changes
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ActivityType(Enum):
    """Types of activities to track"""
    SCAN = "scan"
    UPDATE = "update"
    CONFIG = "config"
    REPORT = "report"
    INSTALL = "install"
    ERROR = "error"
    SYSTEM = "system"
    AI_MODEL = "ai_model"
    EMAIL = "email"
    BACKUP = "backup"
    RESTORE = "restore"

class ActivityStatus(Enum):
    """Status of activities"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"
    PARTIAL = "partial"

@dataclass
class HistoryEntry:
    """Individual history entry"""
    id: Optional[int] = None
    timestamp: str = ""
    activity_type: str = ""
    status: str = ""
    target: str = ""
    description: str = ""
    details: Dict[str, Any] = None
    duration: float = 0.0
    user: str = ""
    version: str = ""
    errors: List[str] = None
    results: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.details is None:
            self.details = {}
        if self.errors is None:
            self.errors = []
        if self.results is None:
            self.results = {}
        if not self.user:
            self.user = os.getenv('USER', 'unknown')

class HistoryManager:
    def __init__(self, db_path: Optional[str] = None):
        self.base_dir = Path(__file__).parent
        self.db_path = Path(db_path) if db_path else self.base_dir / 'history.db'
        self.version = "3.1"
        
        # Create database and tables
        self._init_database()
        
        # Add framework startup entry
        self._log_system_startup()

    def _init_database(self):
        """Initialize SQLite database for history tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        activity_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        target TEXT,
                        description TEXT,
                        details TEXT,
                        duration REAL,
                        user TEXT,
                        version TEXT,
                        errors TEXT,
                        results TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp ON history(timestamp)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_activity_type ON history(activity_type)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_status ON history(status)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_target ON history(target)
                ''')
                
                conn.commit()
                logger.info(f"📊 History database initialized: {self.db_path}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize history database: {e}")
            raise

    def _log_system_startup(self):
        """Log system startup"""
        try:
            self.add_entry(
                activity_type=ActivityType.SYSTEM,
                status=ActivityStatus.SUCCESS,
                description="Bug Bounty Framework Started",
                details={
                    "framework_version": self.version,
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "working_directory": str(self.base_dir)
                }
            )
        except Exception as e:
            logger.warning(f"Could not log system startup: {e}")

    def add_entry(
        self,
        activity_type: ActivityType,
        status: ActivityStatus,
        target: str = "",
        description: str = "",
        details: Optional[Dict[str, Any]] = None,
        duration: float = 0.0,
        errors: Optional[List[str]] = None,
        results: Optional[Dict[str, Any]] = None
    ) -> int:
        """Add a new history entry"""
        try:
            entry = HistoryEntry(
                timestamp=datetime.now().isoformat(),
                activity_type=activity_type.value,
                status=status.value,
                target=target,
                description=description,
                details=details or {},
                duration=duration,
                version=self.version,
                errors=errors or [],
                results=results or {}
            )
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    INSERT INTO history (
                        timestamp, activity_type, status, target, description,
                        details, duration, user, version, errors, results
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.timestamp,
                    entry.activity_type,
                    entry.status,
                    entry.target,
                    entry.description,
                    json.dumps(entry.details),
                    entry.duration,
                    entry.user,
                    entry.version,
                    json.dumps(entry.errors),
                    json.dumps(entry.results)
                ))
                
                entry_id = cursor.lastrowid
                conn.commit()
                
                logger.debug(f"📝 History entry added: ID {entry_id}")
                return entry_id
                
        except Exception as e:
            logger.error(f"❌ Failed to add history entry: {e}")
            return -1

    def get_entries(
        self,
        limit: int = 100,
        activity_type: Optional[ActivityType] = None,
        status: Optional[ActivityStatus] = None,
        target: Optional[str] = None,
        days_back: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve history entries with optional filtering"""
        try:
            query = "SELECT * FROM history WHERE 1=1"
            params = []
            
            if activity_type:
                query += " AND activity_type = ?"
                params.append(activity_type.value)
                
            if status:
                query += " AND status = ?"
                params.append(status.value)
                
            if target:
                query += " AND target LIKE ?"
                params.append(f"%{target}%")
                
            if days_back:
                cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
                query += " AND timestamp >= ?"
                params.append(cutoff_date)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                entries = []
                for row in rows:
                    entry = dict(row)
                    # Parse JSON fields
                    for field in ['details', 'errors', 'results']:
                        try:
                            entry[field] = json.loads(entry[field] or '{}')
                        except:
                            entry[field] = {}
                    entries.append(entry)
                
                return entries
                
        except Exception as e:
            logger.error(f"❌ Failed to retrieve history entries: {e}")
            return []

    def get_activity_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """Get activity summary for the specified period"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Total activities
                total_cursor = conn.execute(
                    "SELECT COUNT(*) FROM history WHERE timestamp >= ?",
                    (cutoff_date,)
                )
                total_activities = total_cursor.fetchone()[0]
                
                # Activities by type
                type_cursor = conn.execute('''
                    SELECT activity_type, COUNT(*) as count
                    FROM history
                    WHERE timestamp >= ?
                    GROUP BY activity_type
                    ORDER BY count DESC
                ''', (cutoff_date,))
                activities_by_type = dict(type_cursor.fetchall())
                
                # Activities by status
                status_cursor = conn.execute('''
                    SELECT status, COUNT(*) as count
                    FROM history
                    WHERE timestamp >= ?
                    GROUP BY status
                    ORDER BY count DESC
                ''', (cutoff_date,))
                activities_by_status = dict(status_cursor.fetchall())
                
                # Success rate
                success_count = activities_by_status.get('success', 0)
                success_rate = (success_count / total_activities * 100) if total_activities > 0 else 0
                
                # Most active targets
                target_cursor = conn.execute('''
                    SELECT target, COUNT(*) as count
                    FROM history
                    WHERE timestamp >= ? AND target != ""
                    GROUP BY target
                    ORDER BY count DESC
                    LIMIT 10
                ''', (cutoff_date,))
                top_targets = dict(target_cursor.fetchall())
                
                # Recent errors
                error_cursor = conn.execute('''
                    SELECT timestamp, description, errors
                    FROM history
                    WHERE timestamp >= ? AND status = "failed" AND errors != "[]"
                    ORDER BY timestamp DESC
                    LIMIT 5
                ''', (cutoff_date,))
                recent_errors = []
                for row in error_cursor.fetchall():
                    try:
                        errors = json.loads(row[2])
                        recent_errors.append({
                            'timestamp': row[0],
                            'description': row[1],
                            'errors': errors
                        })
                    except:
                        pass
                
                return {
                    'period_days': days_back,
                    'total_activities': total_activities,
                    'success_rate': round(success_rate, 1),
                    'activities_by_type': activities_by_type,
                    'activities_by_status': activities_by_status,
                    'top_targets': top_targets,
                    'recent_errors': recent_errors
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to generate activity summary: {e}")
            return {}

    def get_scan_history(self, target: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get scan-specific history"""
        entries = self.get_entries(
            limit=limit,
            activity_type=ActivityType.SCAN,
            target=target
        )
        return entries

    def get_update_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get update-specific history"""
        entries = self.get_entries(
            limit=limit,
            activity_type=ActivityType.UPDATE
        )
        return entries

    def export_history(self, output_file: Optional[str] = None, format: str = 'json') -> bool:
        """Export history to file"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"history_export_{timestamp}.{format}"
            
            entries = self.get_entries(limit=10000)  # Export all entries
            
            output_path = Path(output_file)
            
            if format.lower() == 'json':
                with open(output_path, 'w') as f:
                    json.dump({
                        'export_timestamp': datetime.now().isoformat(),
                        'framework_version': self.version,
                        'total_entries': len(entries),
                        'entries': entries
                    }, f, indent=2)
                    
            elif format.lower() == 'csv':
                import csv
                with open(output_path, 'w', newline='') as f:
                    if entries:
                        writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                        writer.writeheader()
                        for entry in entries:
                            # Convert complex fields to strings
                            row = entry.copy()
                            for field in ['details', 'errors', 'results']:
                                row[field] = json.dumps(row[field])
                            writer.writerow(row)
            
            logger.info(f"📄 History exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to export history: {e}")
            return False

    def cleanup_old_entries(self, keep_days: int = 90) -> int:
        """Remove old history entries"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=keep_days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM history WHERE timestamp < ?",
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                
            logger.info(f"🗑️  Cleaned up {deleted_count} old history entries")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old entries: {e}")
            return 0

    def search_history(self, search_term: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search history entries by description, target, or details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT * FROM history
                    WHERE description LIKE ? OR target LIKE ? OR details LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", limit))
                
                rows = cursor.fetchall()
                entries = []
                for row in rows:
                    entry = dict(row)
                    # Parse JSON fields
                    for field in ['details', 'errors', 'results']:
                        try:
                            entry[field] = json.loads(entry[field] or '{}')
                        except:
                            entry[field] = {}
                    entries.append(entry)
                
                return entries
                
        except Exception as e:
            logger.error(f"❌ Failed to search history: {e}")
            return []

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total entries
                total_cursor = conn.execute("SELECT COUNT(*) FROM history")
                total_entries = total_cursor.fetchone()[0]
                
                # Database size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                # Date range
                range_cursor = conn.execute(
                    "SELECT MIN(timestamp), MAX(timestamp) FROM history"
                )
                date_range = range_cursor.fetchone()
                
                return {
                    'total_entries': total_entries,
                    'database_size_bytes': db_size,
                    'database_size_mb': round(db_size / (1024 * 1024), 2),
                    'earliest_entry': date_range[0],
                    'latest_entry': date_range[1],
                    'database_path': str(self.db_path)
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get database stats: {e}")
            return {}

    def display_recent_activity(self, limit: int = 10):
        """Display recent activity in a formatted way"""
        try:
            entries = self.get_entries(limit=limit)
            
            print(f"\n📊 Recent Activity (Last {limit} entries)")
            print("=" * 80)
            
            if not entries:
                print("   No activity found")
                return
            
            for entry in entries:
                timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                
                # Status emoji
                status_emoji = {
                    'success': '✅',
                    'failed': '❌',
                    'in_progress': '⏳',
                    'cancelled': '🚫',
                    'partial': '⚠️'
                }.get(entry['status'], '❓')
                
                # Activity type emoji
                type_emoji = {
                    'scan': '🔍',
                    'update': '🔄',
                    'config': '⚙️',
                    'report': '📝',
                    'install': '📦',
                    'error': '🚨',
                    'system': '🖥️',
                    'ai_model': '🤖',
                    'email': '📧',
                    'backup': '💾',
                    'restore': '🔄'
                }.get(entry['activity_type'], '📌')
                
                target_str = f" → {entry['target']}" if entry['target'] else ""
                duration_str = f" ({entry['duration']:.1f}s)" if entry['duration'] > 0 else ""
                
                print(f"{status_emoji} {type_emoji} [{timestamp}] {entry['description']}{target_str}{duration_str}")
                
                # Show errors if any
                if entry['errors']:
                    for error in entry['errors'][:2]:  # Show max 2 errors
                        print(f"   💥 {error}")
            
            print()
            
        except Exception as e:
            logger.error(f"❌ Failed to display recent activity: {e}")

def main():
    """Command line interface for history management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bug Bounty Framework History Manager")
    parser.add_argument('--recent', type=int, default=10, help='Show recent activity (default: 10)')
    parser.add_argument('--summary', type=int, help='Show activity summary for N days (default: 30)')
    parser.add_argument('--scans', help='Show scan history for target')
    parser.add_argument('--updates', action='store_true', help='Show update history')
    parser.add_argument('--search', help='Search history entries')
    parser.add_argument('--export', help='Export history to file')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    parser.add_argument('--cleanup', type=int, help='Cleanup entries older than N days')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    
    args = parser.parse_args()
    
    history = HistoryManager()
    
    if args.stats:
        stats = history.get_database_stats()
        print("\n📊 Database Statistics")
        print("=" * 30)
        print(f"📈 Total Entries: {stats.get('total_entries', 0)}")
        print(f"💾 Database Size: {stats.get('database_size_mb', 0)} MB")
        print(f"📅 Date Range: {stats.get('earliest_entry', 'N/A')} to {stats.get('latest_entry', 'N/A')}")
        print(f"📂 Database Path: {stats.get('database_path', 'N/A')}")
    
    elif hasattr(args, 'recent') and args.recent and not args.summary and not args.scans and not args.updates and not args.search and not args.export and not args.cleanup:
        history.display_recent_activity(args.recent)
    
    elif args.summary is not None:
        days = args.summary if args.summary > 0 else 30
        summary = history.get_activity_summary(days)
        
        print(f"\n📊 Activity Summary (Last {days} days)")
        print("=" * 50)
        print(f"📈 Total Activities: {summary.get('total_activities', 0)}")
        print(f"✅ Success Rate: {summary.get('success_rate', 0)}%")
        
        print("\n🎯 Activities by Type:")
        for activity_type, count in summary.get('activities_by_type', {}).items():
            print(f"   {activity_type}: {count}")
        
        print("\n📊 Activities by Status:")
        for status, count in summary.get('activities_by_status', {}).items():
            print(f"   {status}: {count}")
        
        if summary.get('top_targets'):
            print("\n🎯 Most Active Targets:")
            for target, count in list(summary['top_targets'].items())[:5]:
                print(f"   {target}: {count} scans")
        
        if summary.get('recent_errors'):
            print("\n🚨 Recent Errors:")
            for error in summary['recent_errors']:
                timestamp = datetime.fromisoformat(error['timestamp']).strftime('%Y-%m-%d %H:%M')
                print(f"   [{timestamp}] {error['description']}")
    
    elif args.scans:
        entries = history.get_scan_history(target=args.scans)
        print(f"\n🔍 Scan History for: {args.scans}")
        print("=" * 50)
        for entry in entries:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            status_emoji = '✅' if entry['status'] == 'success' else '❌'
            print(f"{status_emoji} [{timestamp}] {entry['description']}")
    
    elif args.updates:
        entries = history.get_update_history()
        print("\n🔄 Update History")
        print("=" * 30)
        for entry in entries:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            status_emoji = '✅' if entry['status'] == 'success' else '❌'
            print(f"{status_emoji} [{timestamp}] {entry['description']}")
    
    elif args.search:
        entries = history.search_history(args.search)
        print(f"\n🔍 Search Results for: '{args.search}'")
        print("=" * 50)
        for entry in entries[:20]:  # Show max 20 results
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            status_emoji = '✅' if entry['status'] == 'success' else '❌'
            target_str = f" → {entry['target']}" if entry['target'] else ""
            print(f"{status_emoji} [{timestamp}] {entry['description']}{target_str}")
    
    elif args.export:
        success = history.export_history(args.export, args.format)
        if success:
            print(f"✅ History exported to: {args.export}")
        else:
            print("❌ Export failed")
    
    elif args.cleanup:
        deleted_count = history.cleanup_old_entries(args.cleanup)
        print(f"🗑️  Cleaned up {deleted_count} entries older than {args.cleanup} days")
    
    elif args.stats:
        stats = history.get_database_stats()
        print("\n📊 Database Statistics")
        print("=" * 30)
        print(f"📈 Total Entries: {stats.get('total_entries', 0)}")
        print(f"💾 Database Size: {stats.get('database_size_mb', 0)} MB")
        print(f"📅 Date Range: {stats.get('earliest_entry', 'N/A')} to {stats.get('latest_entry', 'N/A')}")
        print(f"📂 Database Path: {stats.get('database_path', 'N/A')}")
    
    else:
        # Default: show recent activity
        history.display_recent_activity(10)

if __name__ == "__main__":
    main()
