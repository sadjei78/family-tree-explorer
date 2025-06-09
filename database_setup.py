import sqlite3
import json
import os
from datetime import datetime
import logging

class FamilyDatabase:
    def __init__(self, db_path='family_data.db'):
        self.db_path = db_path
        self.init_database()
        self.migrate_existing_data()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create submissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    person_name TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    story TEXT NOT NULL,
                    submitter_name TEXT,
                    submitter_email TEXT,
                    person_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    name TEXT,
                    email TEXT,
                    feedback_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logging.info("Database initialized successfully")
    
    def migrate_existing_data(self):
        """Migrate data from existing JSON files if they exist."""
        # Migrate submissions
        if os.path.exists('family_submissions.json'):
            try:
                with open('family_submissions.json', 'r') as f:
                    submissions = json.load(f)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    for submission in submissions:
                        cursor.execute('''
                            INSERT OR IGNORE INTO submissions 
                            (timestamp, person_name, relationship, story, submitter_name, submitter_email, person_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            submission.get('timestamp', ''),
                            submission.get('person_name', ''),
                            submission.get('relationship', ''),
                            submission.get('story', ''),
                            submission.get('submitter_name', ''),
                            submission.get('submitter_email', ''),
                            submission.get('person_id', '')
                        ))
                    conn.commit()
                
                # Backup and remove old file
                os.rename('family_submissions.json', 'family_submissions.json.backup')
                logging.info("Migrated submissions from JSON to database")
            except Exception as e:
                logging.error(f"Error migrating submissions: {e}")
        
        # Migrate feedback
        if os.path.exists('family_feedback.json'):
            try:
                with open('family_feedback.json', 'r') as f:
                    feedback_list = json.load(f)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    for feedback in feedback_list:
                        cursor.execute('''
                            INSERT OR IGNORE INTO feedback 
                            (timestamp, name, email, feedback_type, message)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            feedback.get('timestamp', ''),
                            feedback.get('name', ''),
                            feedback.get('email', ''),
                            feedback.get('feedback_type', ''),
                            feedback.get('message', '')
                        ))
                    conn.commit()
                
                # Backup and remove old file
                os.rename('family_feedback.json', 'family_feedback.json.backup')
                logging.info("Migrated feedback from JSON to database")
            except Exception as e:
                logging.error(f"Error migrating feedback: {e}")
    
    def add_submission(self, submission_data):
        """Add a new family story submission."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO submissions 
                (timestamp, person_name, relationship, story, submitter_name, submitter_email, person_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                submission_data.get('timestamp', datetime.now().isoformat()),
                submission_data.get('person_name', ''),
                submission_data.get('relationship', ''),
                submission_data.get('story', ''),
                submission_data.get('submitter_name', ''),
                submission_data.get('submitter_email', ''),
                submission_data.get('person_id', '')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def add_feedback(self, feedback_data):
        """Add new feedback."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedback 
                (timestamp, name, email, feedback_type, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                feedback_data.get('timestamp', datetime.now().isoformat()),
                feedback_data.get('name', ''),
                feedback_data.get('email', ''),
                feedback_data.get('feedback_type', ''),
                feedback_data.get('message', '')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_submissions(self):
        """Get all submissions as a list of dictionaries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM submissions ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_feedback(self):
        """Get all feedback as a list of dictionaries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM feedback ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def export_submissions_csv(self):
        """Export submissions to CSV format."""
        import csv
        import io
        
        submissions = self.get_all_submissions()
        output = io.StringIO()
        
        if submissions:
            fieldnames = ['timestamp', 'person_name', 'relationship', 'story', 'submitter_name', 'submitter_email', 'person_id', 'created_at']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(submissions)
        
        return output.getvalue()
    
    def export_feedback_csv(self):
        """Export feedback to CSV format."""
        import csv
        import io
        
        feedback_list = self.get_all_feedback()
        output = io.StringIO()
        
        if feedback_list:
            fieldnames = ['timestamp', 'name', 'email', 'feedback_type', 'message', 'created_at']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(feedback_list)
        
        return output.getvalue()

# Initialize database instance
db = FamilyDatabase() 