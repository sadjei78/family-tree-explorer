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
                    type TEXT DEFAULT 'story_submission',
                    person_name TEXT NOT NULL,
                    relationship TEXT NOT NULL,
                    story TEXT NOT NULL,
                    submitter_name TEXT,
                    submitter_email TEXT,
                    person_id TEXT,
                    archived INTEGER DEFAULT 0,
                    archived_at TEXT,
                    archived_by TEXT,
                    notes TEXT,
                    sources TEXT,
                    person_data TEXT,
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
                    submitter_name TEXT,
                    submitter_email TEXT,
                    archived INTEGER DEFAULT 0,
                    archived_at TEXT,
                    archived_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            
            # Migrate existing tables to add new columns if they don't exist
            self.migrate_table_structure(cursor)
            conn.commit()
            logging.info("Database initialized successfully")
    
    def migrate_table_structure(self, cursor):
        """Add new columns to existing tables if they don't exist."""
        try:
            # Get existing columns for submissions table
            cursor.execute("PRAGMA table_info(submissions)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            # Add missing columns to submissions table
            new_columns = {
                'type': 'TEXT DEFAULT "story_submission"',
                'archived': 'INTEGER DEFAULT 0',
                'archived_at': 'TEXT',
                'archived_by': 'TEXT',
                'notes': 'TEXT',
                'sources': 'TEXT',
                'person_data': 'TEXT'
            }
            
            for column, definition in new_columns.items():
                if column not in existing_columns:
                    cursor.execute(f'ALTER TABLE submissions ADD COLUMN {column} {definition}')
                    logging.info(f"Added column {column} to submissions table")
            
            # Get existing columns for feedback table  
            cursor.execute("PRAGMA table_info(feedback)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            # Add missing columns to feedback table
            new_columns = {
                'submitter_name': 'TEXT',
                'submitter_email': 'TEXT', 
                'archived': 'INTEGER DEFAULT 0',
                'archived_at': 'TEXT',
                'archived_by': 'TEXT'
            }
            
            for column, definition in new_columns.items():
                if column not in existing_columns:
                    cursor.execute(f'ALTER TABLE feedback ADD COLUMN {column} {definition}')
                    logging.info(f"Added column {column} to feedback table")
                    
        except Exception as e:
            logging.error(f"Error migrating table structure: {e}")
    
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
                (timestamp, type, person_name, relationship, story, submitter_name, submitter_email, 
                 person_id, archived, archived_at, archived_by, notes, sources, person_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                submission_data.get('timestamp', datetime.now().isoformat()),
                submission_data.get('type', 'story_submission'),
                submission_data.get('person_name', ''),
                submission_data.get('relationship', ''),
                submission_data.get('story', ''),
                submission_data.get('submitter_name', ''),
                submission_data.get('submitter_email', ''),
                submission_data.get('person_id', ''),
                1 if submission_data.get('archived', False) else 0,
                submission_data.get('archived_at', ''),
                submission_data.get('archived_by', ''),
                submission_data.get('notes', ''),
                submission_data.get('sources', ''),
                json.dumps(submission_data.get('person_data', {})) if submission_data.get('person_data') else ''
            ))
            conn.commit()
            return cursor.lastrowid
    
    def add_feedback(self, feedback_data):
        """Add new feedback."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedback 
                (timestamp, name, email, feedback_type, message, submitter_name, submitter_email, 
                 archived, archived_at, archived_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                feedback_data.get('timestamp', datetime.now().isoformat()),
                feedback_data.get('name', ''),
                feedback_data.get('email', ''),
                feedback_data.get('feedback_type', ''),
                feedback_data.get('message', ''),
                feedback_data.get('submitter_name', ''),
                feedback_data.get('submitter_email', ''),
                1 if feedback_data.get('archived', False) else 0,
                feedback_data.get('archived_at', ''),
                feedback_data.get('archived_by', '')
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_all_submissions(self):
        """Get all submissions as a list of dictionaries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM submissions ORDER BY created_at DESC')
            submissions = []
            for row in cursor.fetchall():
                submission = dict(row)
                # Convert boolean fields
                submission['archived'] = bool(submission.get('archived', 0))
                # Parse JSON fields
                if submission.get('person_data'):
                    try:
                        submission['person_data'] = json.loads(submission['person_data'])
                    except:
                        submission['person_data'] = {}
                submissions.append(submission)
            return submissions
    
    def get_all_feedback(self):
        """Get all feedback as a list of dictionaries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM feedback ORDER BY created_at DESC')
            feedback_list = []
            for row in cursor.fetchall():
                feedback = dict(row)
                # Convert boolean fields
                feedback['archived'] = bool(feedback.get('archived', 0))
                feedback_list.append(feedback)
            return feedback_list
    
    def export_submissions_csv(self):
        """Export submissions to CSV format."""
        import csv
        import io
        
        submissions = self.get_all_submissions()
        output = io.StringIO()
        
        if submissions:
            fieldnames = ['id', 'timestamp', 'type', 'person_name', 'relationship', 'story', 
                         'submitter_name', 'submitter_email', 'person_id', 'archived', 
                         'archived_at', 'archived_by', 'notes', 'sources', 'created_at']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            # Flatten person_data and clean up data for CSV export
            for submission in submissions:
                row = {field: submission.get(field, '') for field in fieldnames}
                # Convert person_data back to string for CSV
                if 'person_data' in submission and submission['person_data']:
                    row['notes'] = f"{row.get('notes', '')}\nPerson Data: {json.dumps(submission['person_data'])}"
                writer.writerow(row)
        
        return output.getvalue()
    
    def export_feedback_csv(self):
        """Export feedback to CSV format."""
        import csv
        import io
        
        feedback_list = self.get_all_feedback()
        output = io.StringIO()
        
        if feedback_list:
            fieldnames = ['id', 'timestamp', 'name', 'email', 'feedback_type', 'message', 
                         'submitter_name', 'submitter_email', 'archived', 'archived_at', 
                         'archived_by', 'created_at']
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            # Clean up data for CSV export
            for feedback in feedback_list:
                row = {field: feedback.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        return output.getvalue()
    
    def update_submission(self, submission_id, updates):
        """Update a submission by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            for key, value in updates.items():
                if key == 'archived':
                    value = 1 if value else 0
                elif key == 'person_data' and isinstance(value, dict):
                    value = json.dumps(value)
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            if set_clauses:
                query = f"UPDATE submissions SET {', '.join(set_clauses)} WHERE id = ?"
                values.append(submission_id)
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
            return False
    
    def update_feedback(self, feedback_id, updates):
        """Update feedback by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            for key, value in updates.items():
                if key == 'archived':
                    value = 1 if value else 0
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            if set_clauses:
                query = f"UPDATE feedback SET {', '.join(set_clauses)} WHERE id = ?"
                values.append(feedback_id)
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
            return False
    
    def delete_submission(self, submission_id):
        """Delete a submission by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM submissions WHERE id = ?", (submission_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_feedback(self, feedback_id):
        """Delete feedback by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
            conn.commit()
            return cursor.rowcount > 0

# Initialize database instance
db = FamilyDatabase() 