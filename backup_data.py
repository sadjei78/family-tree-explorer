#!/usr/bin/env python3
"""
Family Tree Data Backup and Restore Script
Provides secure backup and restore functionality for family submissions and feedback
"""

import os
import shutil
import json
import sqlite3
from datetime import datetime
from database_setup import db

def create_backup():
    """Create a timestamped backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = "db_backups"
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Database file backup
    if os.path.exists('family_data.db'):
        backup_path = os.path.join(backup_dir, f"family_data_{timestamp}.db")
        shutil.copy2('family_data.db', backup_path)
        print(f"✅ Database backed up to: {backup_path}")
    
    # Export to JSON for human readability
    json_backup_path = os.path.join(backup_dir, f"family_data_{timestamp}.json")
    
    backup_data = {
        'backup_timestamp': datetime.now().isoformat(),
        'submissions': db.get_all_submissions(),
        'feedback': db.get_all_feedback()
    }
    
    with open(json_backup_path, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON backup created: {json_backup_path}")
    
    # Export CSV files for spreadsheet analysis
    csv_dir = os.path.join(backup_dir, f"csv_{timestamp}")
    os.makedirs(csv_dir, exist_ok=True)
    
    submissions_csv = db.export_submissions_csv()
    feedback_csv = db.export_feedback_csv()
    
    with open(os.path.join(csv_dir, 'submissions.csv'), 'w', encoding='utf-8') as f:
        f.write(submissions_csv)
    
    with open(os.path.join(csv_dir, 'feedback.csv'), 'w', encoding='utf-8') as f:
        f.write(feedback_csv)
    
    print(f"✅ CSV exports created in: {csv_dir}")
    
    return {
        'timestamp': timestamp,
        'database_backup': backup_path if os.path.exists('family_data.db') else None,
        'json_backup': json_backup_path,
        'csv_directory': csv_dir
    }

def restore_from_backup(backup_file):
    """Restore data from a backup file"""
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    try:
        if backup_file.endswith('.db'):
            # Restore from SQLite database backup
            current_backup = f"family_data_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if os.path.exists('family_data.db'):
                shutil.copy2('family_data.db', current_backup)
                print(f"💾 Current database backed up to: {current_backup}")
            
            shutil.copy2(backup_file, 'family_data.db')
            print(f"✅ Database restored from: {backup_file}")
            
        elif backup_file.endswith('.json'):
            # Restore from JSON backup
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Clear existing data (create fresh database)
            if os.path.exists('family_data.db'):
                current_backup = f"family_data_restore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2('family_data.db', current_backup)
                print(f"💾 Current database backed up to: {current_backup}")
            
            # Initialize fresh database
            from database_setup import FamilyDatabase
            fresh_db = FamilyDatabase()
            
            # Restore submissions
            for submission in backup_data.get('submissions', []):
                fresh_db.add_submission(submission)
            
            # Restore feedback
            for feedback in backup_data.get('feedback', []):
                fresh_db.add_feedback(feedback)
            
            print(f"✅ Data restored from JSON backup: {backup_file}")
            print(f"   Restored {len(backup_data.get('submissions', []))} submissions")
            print(f"   Restored {len(backup_data.get('feedback', []))} feedback items")
            
        return True
        
    except Exception as e:
        print(f"❌ Error restoring backup: {e}")
        return False

def list_backups():
    """List all available backups"""
    backup_dir = "db_backups"
    
    if not os.path.exists(backup_dir):
        print("📁 No backup directory found")
        return []
    
    backups = []
    for file in os.listdir(backup_dir):
        if file.startswith('family_data_') and (file.endswith('.db') or file.endswith('.json')):
            file_path = os.path.join(backup_dir, file)
            stat = os.stat(file_path)
            backups.append({
                'filename': file,
                'path': file_path,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime)
            })
    
    backups.sort(key=lambda x: x['modified'], reverse=True)
    
    print("📋 Available Backups:")
    print("-" * 60)
    for backup in backups:
        size_mb = backup['size'] / 1024 / 1024
        print(f"{backup['filename']:35} {size_mb:6.2f}MB {backup['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    return backups

def get_data_stats():
    """Get current database statistics"""
    try:
        submissions = db.get_all_submissions()
        feedback = db.get_all_feedback()
        
        print("📊 Current Database Statistics:")
        print("-" * 40)
        print(f"Total Submissions: {len(submissions)}")
        print(f"Total Feedback:    {len(feedback)}")
        
        if submissions:
            latest_submission = max(submissions, key=lambda x: x.get('created_at', ''))
            print(f"Latest Submission: {latest_submission.get('created_at', 'Unknown')}")
        
        if feedback:
            latest_feedback = max(feedback, key=lambda x: x.get('created_at', ''))
            print(f"Latest Feedback:   {latest_feedback.get('created_at', 'Unknown')}")
        
        # Database file size
        if os.path.exists('family_data.db'):
            db_size = os.path.getsize('family_data.db') / 1024 / 1024
            print(f"Database Size:     {db_size:.2f}MB")
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")

def main():
    """Main backup script interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔄 Family Tree Data Management")
        print("=" * 40)
        print("Usage:")
        print("  python backup_data.py backup         - Create new backup")
        print("  python backup_data.py restore <file> - Restore from backup")
        print("  python backup_data.py list           - List available backups")
        print("  python backup_data.py stats          - Show current data statistics")
        print()
        get_data_stats()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'backup':
        print("🔄 Creating backup...")
        result = create_backup()
        print("✅ Backup completed successfully!")
        
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("❌ Please specify backup file to restore from")
            print("Usage: python backup_data.py restore <backup_file>")
            return
        
        backup_file = sys.argv[2]
        print(f"🔄 Restoring from: {backup_file}")
        
        # Confirm restoration
        response = input("⚠️  This will replace current data. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Restoration cancelled")
            return
        
        restore_from_backup(backup_file)
        
    elif command == 'list':
        list_backups()
        
    elif command == 'stats':
        get_data_stats()
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: backup, restore, list, stats")

if __name__ == '__main__':
    main() 