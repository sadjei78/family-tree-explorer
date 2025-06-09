from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from gedcom_parser import GedcomParser
from relationship_calculator import RelationshipCalculator
from generation_calculator import GenerationCalculator
from database_setup import db

# Configuration
DEBUG = os.getenv('FLASK_ENV') != 'production'
PORT = int(os.getenv('PORT', 5001))
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
EXPLORE_PASSWORD = os.getenv('EXPLORE_PASSWORD', 'family2025')

# Email Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USERNAME)

# Load environment variables from .env file
load_dotenv()

# Configuration
APP_VERSION = "2025.06.1"  # Format: YEAR.MONTH.DATABASE_VERSION
DATABASE_VERSION = "1.0"   # Increment when GEDCOM data is updated
LAST_UPDATED = "June 2025"

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')  # Change this!

# Initialize the GEDCOM parser
parser = GedcomParser()
gedcom_file = os.getenv('GEDCOM_FILE_PATH', 'sample-family.ged')  # Fallback to sample data
family_data = parser.parse_file(gedcom_file)
relationship_calc = RelationshipCalculator(family_data)
generation_calc = GenerationCalculator(family_data['individuals'], family_data['families'])

# Reference person is now stored per-user in Flask sessions

# Authentication decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def explore_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('explore_authenticated'):
            return jsonify({'error': 'Authentication required', 'auth_required': True}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def homepage():
    """Homepage with welcome message and app overview"""
    return render_template('homepage.html', 
                         app_version=APP_VERSION,
                         database_version=DATABASE_VERSION,
                         last_updated=LAST_UPDATED,
                         total_individuals=len(family_data['individuals']),
                         total_families=len(family_data['families']))

@app.route('/explore')
def index():
    """Main family tree explorer interface"""
    # Check if user has entered the explore password
    if not session.get('explore_authenticated'):
        return redirect(url_for('homepage'))
    
    # Get user's reference person from session, or default
    user_reference_person = session.get('reference_person_id')
    if user_reference_person is None:
        user_reference_person = find_main_person()
        session['reference_person_id'] = user_reference_person
    
    # Get current reference person data to display on load
    reference_person = family_data['individuals'].get(user_reference_person, {})
    reference_name = "Unknown"
    if reference_person.get('names'):
        primary_name = reference_person['names'][0]
        reference_name = f"{primary_name.get('given', '')} {primary_name.get('surname', '')}".strip()
    
    return render_template('index.html', 
                         initial_person_id=user_reference_person,
                         reference_person_name=reference_name,
                         app_version=APP_VERSION)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_authenticated'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid password!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_authenticated', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('homepage'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard for managing submissions and feedback"""
    # Get admin's current reference person
    admin_reference_person = session.get('admin_reference_person_id')
    if admin_reference_person is None:
        admin_reference_person = find_main_person()
        session['admin_reference_person_id'] = admin_reference_person
    
    # Get reference person name
    reference_person = family_data['individuals'].get(admin_reference_person, {})
    reference_name = "Unknown"
    if reference_person.get('names'):
        primary_name = reference_person['names'][0]
        reference_name = f"{primary_name.get('given', '')} {primary_name.get('surname', '')}".strip()
    
    # Get admin profile info
    admin_name = session.get('admin_name', reference_name)
    admin_email = session.get('admin_email', '')
    
    return render_template('admin.html',
                         app_version=APP_VERSION,
                         database_version=DATABASE_VERSION,
                         gedcom_filename=gedcom_file,
                         total_individuals=len(family_data['individuals']),
                         total_families=len(family_data['families']),
                         admin_name=admin_name,
                         admin_email=admin_email,
                         reference_person_id=admin_reference_person,
                         reference_person_name=reference_name)

@app.route('/search')
@explore_required
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    
    results = []
    for person_id, person in family_data['individuals'].items():
        names = person.get('names', [])
        for name_info in names:
            full_name = f"{name_info.get('given', '')} {name_info.get('surname', '')}".strip()
            if query.lower() in full_name.lower():
                results.append({
                    'id': person_id,
                    'name': full_name,
                    'birth_year': person.get('birth_year'),
                    'death_year': person.get('death_year'),
                    'summary': generate_person_summary(person_id)
                })
    
    return jsonify(results[:20])  # Limit to 20 results

@app.route('/person/<person_id>')
@explore_required
def get_person(person_id):
    if person_id not in family_data['individuals']:
        return jsonify({'error': 'Person not found'}), 404
    
    # Get user's reference person from session, or default
    user_reference_person = session.get('reference_person_id')
    if user_reference_person is None:
        user_reference_person = find_main_person()
        session['reference_person_id'] = user_reference_person
    
    person = family_data['individuals'][person_id]
    
    # Calculate relationship to the user's reference person
    relationship = relationship_calc.calculate_relationship(user_reference_person, person_id)
    
    # Calculate generation
    generation_label = generation_calc.get_generation_label(person_id)
    
    return jsonify({
        'person': person,
        'relationship': relationship,
        'summary': generate_person_summary(person_id),
        'family_connections': get_family_connections(person_id),
        'notes': person.get('notes', []),
        'generation': generation_label
    })

def find_main_person():
    """Find Rev Emmanuel Adjei as the main reference person (or John Doe in sample data)"""
    for person_id, person in family_data['individuals'].items():
        names = person.get('names', [])
        for name_info in names:
            full_name = f"{name_info.get('given', '')} {name_info.get('surname', '')}".strip()
            # Look for Rev Emmanuel Adjei in real data
            if 'Emmanuel' in full_name and 'Adjei' in full_name:
                return person_id
            # Fallback to John Doe for sample data demonstration
            if 'John' in full_name and 'Doe' in full_name:
                return person_id
    
    # Final fallback to first person if neither found
    return list(family_data['individuals'].keys())[0] if family_data['individuals'] else None

def generate_person_summary(person_id):
    """Generate a brief summary of a person"""
    person = family_data['individuals'].get(person_id, {})
    names = person.get('names', [])
    
    if not names:
        return "No information available"
    
    primary_name = names[0]
    full_name = f"{primary_name.get('given', '')} {primary_name.get('surname', '')}".strip()
    
    summary_parts = [full_name]
    
    # Add birth and death info
    birth_info = []
    if person.get('birth_date'):
        birth_info.append(f"born {person['birth_date']}")
    if person.get('birth_place'):
        birth_info.append(f"in {person['birth_place']}")
    
    if birth_info:
        summary_parts.append(f"({', '.join(birth_info)})")
    
    if person.get('death_date'):
        summary_parts.append(f"died {person['death_date']}")
    
    # Add occupation or title if available
    if person.get('occupation'):
        summary_parts.append(f"Occupation: {person['occupation']}")
    
    return '. '.join(summary_parts)

def get_family_connections(person_id):
    """Get immediate family connections for a person"""
    person = family_data['individuals'].get(person_id, {})
    connections = {
        'parents': [],
        'spouses': [],
        'children': []
    }
    
    # Find parents through family relationships
    for family_id in person.get('child_of_families', []):
        family = family_data['families'].get(family_id, {})
        if family.get('husband'):
            connections['parents'].append({
                'id': family['husband'],
                'name': get_person_name(family['husband'])
            })
        if family.get('wife'):
            connections['parents'].append({
                'id': family['wife'],
                'name': get_person_name(family['wife'])
            })
    
    # Find spouses and children through families where this person is a parent
    for family_id in person.get('spouse_in_families', []):
        family = family_data['families'].get(family_id, {})
        
        # Add spouse
        if family.get('husband') == person_id and family.get('wife'):
            connections['spouses'].append({
                'id': family['wife'],
                'name': get_person_name(family['wife'])
            })
        elif family.get('wife') == person_id and family.get('husband'):
            connections['spouses'].append({
                'id': family['husband'],
                'name': get_person_name(family['husband'])
            })
        
        # Add children
        for child_id in family.get('children', []):
            connections['children'].append({
                'id': child_id,
                'name': get_person_name(child_id)
            })
    
    return connections

def get_person_name(person_id):
    """Get the primary name of a person"""
    person = family_data['individuals'].get(person_id, {})
    names = person.get('names', [])
    if names:
        primary_name = names[0]
        return f"{primary_name.get('given', '')} {primary_name.get('surname', '')}".strip()
    return "Unknown"

@app.route('/stats')
def get_stats():
    """Get database statistics"""
    return jsonify({
        'total_individuals': len(family_data['individuals']),
        'total_families': len(family_data['families']),
        'date_range': get_date_range(),
        'most_common_surnames': get_common_surnames(),
        'app_version': APP_VERSION,
        'database_version': DATABASE_VERSION,
        'last_updated': LAST_UPDATED
    })

@app.route('/version')
def get_version():
    """Get version information"""
    return jsonify({
        'app_version': APP_VERSION,
        'database_version': DATABASE_VERSION,
        'last_updated': LAST_UPDATED,
        'total_individuals': len(family_data['individuals']),
        'total_families': len(family_data['families'])
    })

def get_date_range():
    """Get the date range of the family tree"""
    birth_years = []
    for person in family_data['individuals'].values():
        if person.get('birth_year'):
            birth_years.append(person['birth_year'])
    
    if birth_years:
        return {
            'earliest': min(birth_years),
            'latest': max(birth_years)
        }
    return None

def get_common_surnames():
    """Get the most common surnames in the database"""
    surname_count = {}
    for person in family_data['individuals'].values():
        for name_info in person.get('names', []):
            surname = name_info.get('surname', '').strip()
            if surname:
                surname_count[surname] = surname_count.get(surname, 0) + 1
    
    # Return top 10 surnames
    return sorted(surname_count.items(), key=lambda x: x[1], reverse=True)[:10]

@app.route('/set_reference_person/<person_id>')
def set_reference_person(person_id):
    """Set a new reference person for relationship calculations (per user session)"""
    if person_id not in family_data['individuals']:
        return jsonify({'success': False, 'error': 'Person not found'}), 404
    
    # Store in user's session
    session['reference_person_id'] = person_id
    person = family_data['individuals'][person_id]
    
    # Get person name
    reference_name = "Unknown"
    if person.get('names'):
        primary_name = person['names'][0]
        reference_name = f"{primary_name.get('given', '')} {primary_name.get('surname', '')}".strip()
    
    return jsonify({
        'success': True,
        'reference_person_id': person_id,
        'reference_person_name': reference_name
    })

@app.route('/get_reference_person')
def get_reference_person():
    """Get current reference person information (per user session)"""
    # Get user's reference person from session, or default
    user_reference_person = session.get('reference_person_id')
    if user_reference_person is None:
        user_reference_person = find_main_person()
        session['reference_person_id'] = user_reference_person
    
    person = family_data['individuals'].get(user_reference_person, {})
    reference_name = "Unknown"
    if person.get('names'):
        primary_name = person['names'][0]
        reference_name = f"{primary_name.get('given', '')} {primary_name.get('surname', '')}".strip()
    
    return jsonify({
        'reference_person_id': user_reference_person,
        'reference_person_name': reference_name
    })

@app.route('/verify_explore_password', methods=['POST'])
def verify_explore_password():
    """Verify the explore password"""
    data = request.get_json()
    password = data.get('password', '')
    
    if password == EXPLORE_PASSWORD:
        # Store in session that user has entered correct password
        session['explore_authenticated'] = True
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Invalid password'})

@app.route('/submit_update', methods=['POST'])
def submit_update():
    """Submit an update or correction for an existing person"""
    try:
        data = request.get_json()
        
        # Get person name for display in admin
        person_name = get_person_name(data.get('person_id', ''))
        
        submission = {
            'type': 'update',
            'person_id': data.get('person_id'),
            'person_name': person_name,  # Add person name for admin display
            'submitter_name': data.get('submitter_name'),
            'submitter_email': data.get('submitter_email'),
            'timestamp': datetime.now().isoformat(),
            'changes': data.get('changes', ''),  # Store as string, not object
            'notes': data.get('notes', ''),
            'sources': data.get('sources', '')
        }
        
        # Save to submissions file
        save_submission(submission)
        
        return jsonify({'success': True, 'message': 'Update submitted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/submit_new_person', methods=['POST'])
def submit_new_person():
    """Submit a new person entry"""
    try:
        data = request.get_json()
        
        # Create person name for display
        given_name = data.get('given_name', '').strip()
        surname = data.get('surname', '').strip()
        person_name = f"{given_name} {surname}".strip() or "New Person"
        
        submission = {
            'type': 'new_person',
            'person_name': person_name,  # Add person name for admin display
            'submitter_name': data.get('submitter_name'),
            'submitter_email': data.get('submitter_email'),
            'timestamp': datetime.now().isoformat(),
            'person_data': {
                'given_name': given_name,
                'surname': surname,
                'birth_date': data.get('birth_date'),
                'birth_place': data.get('birth_place'),
                'death_date': data.get('death_date'),
                'death_place': data.get('death_place'),
                'sex': data.get('sex'),
                'father_name': data.get('father_name'),
                'mother_name': data.get('mother_name'),
                'spouse_name': data.get('spouse_name')
            },
            'notes': data.get('notes', ''),
            'sources': data.get('sources', '')
        }
        
        # Save to submissions file
        save_submission(submission)
        
        return jsonify({'success': True, 'message': 'New person submitted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback, questions, or feature requests"""
    try:
        data = request.get_json()
        feedback = {
            'type': 'feedback',
            'feedback_type': data.get('feedback_type'),  # 'question', 'bug', 'feature', 'general'
            'submitter_name': data.get('submitter_name'),
            'submitter_email': data.get('submitter_email'),
            'timestamp': datetime.now().isoformat(),
            'subject': data.get('subject', ''),
            'message': data.get('message', ''),
            'page_url': data.get('page_url', ''),
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        # Save to feedback file
        save_feedback(feedback)
        
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_submissions')
def export_submissions():
    """Export submissions in CSV format and GEDCOM-compatible format"""
    try:
        submissions = load_submissions()
        # Only export non-archived submissions  
        active_submissions = [s for s in submissions if not s.get('archived', False)]
        gedcom_export = generate_gedcom_export(active_submissions)
        csv_data = db.export_submissions_csv()
        
        return jsonify({
            'success': True,
            'submissions': active_submissions,
            'gedcom_data': gedcom_export,
            'csv_data': csv_data,
            'count': len(active_submissions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_feedback')
def export_feedback():
    """Export all feedback for review"""
    try:
        feedback_list = load_feedback()
        # Only return non-archived feedback
        active_feedback = [f for f in feedback_list if not f.get('archived', False)]
        csv_data = db.export_feedback_csv()
        
        return jsonify({
            'success': True,
            'feedback': active_feedback,
            'csv_data': csv_data,
            'count': len(active_feedback)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/archive_submission/<int:submission_index>', methods=['POST'])
@admin_required
def archive_submission(submission_index):
    """Archive a specific submission"""
    try:
        submissions = load_submissions()
        if submission_index < 0 or submission_index >= len(submissions):
            return jsonify({'success': False, 'error': 'Invalid submission index'}), 400
        
        # Mark as archived
        submissions[submission_index]['archived'] = True
        submissions[submission_index]['archived_at'] = datetime.now().isoformat()
        submissions[submission_index]['archived_by'] = session.get('admin_authenticated', 'admin')
        
        # Save back to file
        save_submissions_list(submissions)
        
        # Log the archiving action
        log_admin_action('archive_submission', {
            'submission_index': submission_index,
            'submission_type': submissions[submission_index].get('type'),
            'submitter': submissions[submission_index].get('submitter_name')
        })
        
        return jsonify({'success': True, 'message': 'Submission archived successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/archive_feedback/<int:feedback_index>', methods=['POST'])
@admin_required
def archive_feedback(feedback_index):
    """Archive a specific feedback item"""
    try:
        feedback_list = load_feedback()
        if feedback_index < 0 or feedback_index >= len(feedback_list):
            return jsonify({'success': False, 'error': 'Invalid feedback index'}), 400
        
        # Mark as archived
        feedback_list[feedback_index]['archived'] = True
        feedback_list[feedback_index]['archived_at'] = datetime.now().isoformat()
        feedback_list[feedback_index]['archived_by'] = session.get('admin_authenticated', 'admin')
        
        # Save back to file
        save_feedback_list(feedback_list)
        
        # Log the archiving action
        log_admin_action('archive_feedback', {
            'feedback_index': feedback_index,
            'feedback_type': feedback_list[feedback_index].get('feedback_type'),
            'submitter': feedback_list[feedback_index].get('submitter_name')
        })
        
        return jsonify({'success': True, 'message': 'Feedback archived successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/view_archived')
@admin_required
def view_archived():
    """View all archived submissions and feedback"""
    try:
        submissions = load_submissions()
        feedback_list = load_feedback()
        
        archived_submissions = [s for s in submissions if s.get('archived', False)]
        archived_feedback = [f for f in feedback_list if f.get('archived', False)]
        
        return jsonify({
            'success': True,
            'archived_submissions': archived_submissions,
            'archived_feedback': archived_feedback,
            'submission_count': len(archived_submissions),
            'feedback_count': len(archived_feedback)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/delete_archived_submission/<int:submission_index>', methods=['DELETE'])
@admin_required
def delete_archived_submission(submission_index):
    """Permanently delete an archived submission"""
    try:
        submissions = load_submissions()
        if submission_index < 0 or submission_index >= len(submissions):
            return jsonify({'success': False, 'error': 'Invalid submission index'}), 400
        
        submission = submissions[submission_index]
        if not submission.get('archived', False):
            return jsonify({'success': False, 'error': 'Submission must be archived before deletion'}), 400
        
        # Log the deletion action before removing
        log_admin_action('delete_archived_submission', {
            'submission_index': submission_index,
            'submission_data': submission,
            'deleted_at': datetime.now().isoformat()
        })
        
        # Remove from list
        del submissions[submission_index]
        
        # Save back to file
        save_submissions_list(submissions)
        
        return jsonify({'success': True, 'message': 'Archived submission deleted permanently'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/delete_archived_feedback/<int:feedback_index>', methods=['DELETE'])
@admin_required
def delete_archived_feedback(feedback_index):
    """Permanently delete an archived feedback item"""
    try:
        feedback_list = load_feedback()
        if feedback_index < 0 or feedback_index >= len(feedback_list):
            return jsonify({'success': False, 'error': 'Invalid feedback index'}), 400
        
        feedback = feedback_list[feedback_index]
        if not feedback.get('archived', False):
            return jsonify({'success': False, 'error': 'Feedback must be archived before deletion'}), 400
        
        # Log the deletion action before removing
        log_admin_action('delete_archived_feedback', {
            'feedback_index': feedback_index,
            'feedback_data': feedback,
            'deleted_at': datetime.now().isoformat()
        })
        
        # Remove from list
        del feedback_list[feedback_index]
        
        # Save back to file
        save_feedback_list(feedback_list)
        
        return jsonify({'success': True, 'message': 'Archived feedback deleted permanently'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/admin_audit_log')
@admin_required
def admin_audit_log():
    """View admin audit log"""
    try:
        audit_log = load_audit_log()
        
        return jsonify({
            'success': True,
            'audit_log': audit_log,
            'count': len(audit_log)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/admin/profile', methods=['GET', 'POST'])
@admin_required
def admin_profile():
    """Manage admin profile information"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            session['admin_name'] = data.get('admin_name', '').strip()
            session['admin_email'] = data.get('admin_email', '').strip()
            
            # Log profile update
            log_admin_action('update_profile', {
                'admin_name': session['admin_name'],
                'admin_email': session['admin_email']
            })
            
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    # GET request - return current profile
    return jsonify({
        'success': True,
        'admin_name': session.get('admin_name', ''),
        'admin_email': session.get('admin_email', ''),
        'reference_person_id': session.get('admin_reference_person_id'),
        'reference_person_name': get_person_name(session.get('admin_reference_person_id', ''))
    })

@app.route('/admin/set_reference_person/<person_id>', methods=['POST'])
@admin_required
def admin_set_reference_person(person_id):
    """Set admin's reference person"""
    try:
        if person_id not in family_data['individuals']:
            return jsonify({'success': False, 'error': 'Invalid person ID'}), 400
        
        session['admin_reference_person_id'] = person_id
        reference_name = get_person_name(person_id)
        
        # If admin name not set, use reference person name
        if not session.get('admin_name'):
            session['admin_name'] = reference_name
        
        # Log reference person change
        log_admin_action('change_reference_person', {
            'person_id': person_id,
            'person_name': reference_name
        })
        
        return jsonify({
            'success': True,
            'message': 'Reference person updated successfully',
            'reference_person_name': reference_name
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/send_response', methods=['POST'])
@admin_required
def send_response():
    """Send email response to submission or feedback"""
    try:
        data = request.get_json()
        recipient_email = data.get('recipient_email')
        recipient_name = data.get('recipient_name', 'User')
        subject = data.get('subject', 'Response to your submission')
        message_body = data.get('message', '')
        original_subject = data.get('original_subject', '')
        response_type = data.get('response_type', 'general')  # submission, feedback, general
        
        if not recipient_email or not message_body:
            return jsonify({'success': False, 'error': 'Email and message are required'}), 400
        
        # Get admin info
        admin_name = session.get('admin_name', 'Family Tree Administrator')
        admin_email = session.get('admin_email', FROM_EMAIL)
        
        # Compose email subject
        if original_subject:
            email_subject = f"Re: {original_subject}"
        else:
            email_subject = subject
        
        # Compose email body
        email_body = f"""Dear {recipient_name},

Thank you for your {response_type} to our Family Tree Explorer.

{message_body}

If you have any further questions or need additional assistance, please don't hesitate to reach out.

Best regards,
{admin_name}
Family Tree Administrator

---
This email was sent in response to your submission to the Family Tree Explorer.
"""
        
        # Send email
        success = send_email(recipient_email, email_subject, email_body, admin_email, admin_name)
        
        if success:
            # Log the response
            log_admin_action('send_email_response', {
                'recipient_email': recipient_email,
                'recipient_name': recipient_name,
                'subject': email_subject,
                'response_type': response_type,
                'admin_name': admin_name,
                'admin_email': admin_email
            })
            
            return jsonify({'success': True, 'message': 'Email sent successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to send email. Please check email configuration.'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

def save_submission(submission):
    """Save a submission to the database"""
    return db.add_submission(submission)

def load_submissions():
    """Load all submissions from the database"""
    return db.get_all_submissions()

def save_feedback(feedback):
    """Save feedback to the database"""
    return db.add_feedback(feedback)

def load_feedback():
    """Load all feedback from the database"""
    return db.get_all_feedback()

def save_submissions_list(submissions):
    """Save submissions list to database - deprecated (use individual add methods)"""
    # This function is deprecated but kept for backward compatibility
    for submission in submissions:
        db.add_submission(submission)

def save_feedback_list(feedback_list):
    """Save feedback list to database - deprecated (use individual add methods)"""
    # This function is deprecated but kept for backward compatibility  
    for feedback in feedback_list:
        db.add_feedback(feedback)

def log_admin_action(action_type, action_data):
    """Log admin actions for audit purposes"""
    audit_file = 'admin_audit.json'
    
    # Load existing audit log
    if os.path.exists(audit_file):
        with open(audit_file, 'r', encoding='utf-8') as f:
            audit_log = json.load(f)
    else:
        audit_log = []
    
    # Create audit entry
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'action_type': action_type,
        'admin_session': session.get('admin_authenticated', 'unknown'),
        'admin_name': session.get('admin_name', 'Unknown Admin'),
        'admin_email': session.get('admin_email', ''),
        'user_agent': request.headers.get('User-Agent', ''),
        'ip_address': request.remote_addr,
        'action_data': action_data
    }
    
    # Add to log
    audit_log.append(audit_entry)
    
    # Keep only last 1000 entries to prevent file from growing too large
    if len(audit_log) > 1000:
        audit_log = audit_log[-1000:]
    
    # Save back to file
    with open(audit_file, 'w', encoding='utf-8') as f:
        json.dump(audit_log, f, indent=2, ensure_ascii=False)

def send_email(to_email, subject, body, from_email=None, from_name=None):
    """Send email using SMTP"""
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            print("Email configuration not set up - email not sent")
            return False
        
        if from_email is None:
            from_email = FROM_EMAIL
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{from_name} <{from_email}>" if from_name else from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach body
        msg.attach(MIMEText(body, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable security
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        print(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def load_audit_log():
    """Load admin audit log"""
    audit_file = 'admin_audit.json'
    
    if os.path.exists(audit_file):
        with open(audit_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def generate_gedcom_export(submissions):
    """Generate GEDCOM-compatible export of submissions"""
    gedcom_lines = []
    gedcom_lines.append("0 HEAD")
    gedcom_lines.append("1 SOUR Family Tree Submissions")
    gedcom_lines.append("1 GEDC")
    gedcom_lines.append("2 VERS 5.5.1")
    gedcom_lines.append("2 FORM LINEAGE-LINKED")
    gedcom_lines.append("1 CHAR UTF-8")
    gedcom_lines.append("1 DATE " + datetime.now().strftime("%d %b %Y").upper())
    gedcom_lines.append("")
    
    person_counter = 1
    note_counter = 1
    
    for submission in submissions:
        if submission['type'] == 'new_person':
            person_data = submission['person_data']
            person_id = f"SUB{person_counter:06d}"
            
            # Person record
            gedcom_lines.append(f"0 @I{person_id}@ INDI")
            
            # Name
            given = person_data.get('given_name', '').strip()
            surname = person_data.get('surname', '').strip()
            if given or surname:
                gedcom_lines.append(f"1 NAME {given} /{surname}/")
                if given:
                    gedcom_lines.append(f"2 GIVN {given}")
                if surname:
                    gedcom_lines.append(f"2 SURN {surname}")
            
            # Sex
            if person_data.get('sex'):
                gedcom_lines.append(f"1 SEX {person_data['sex']}")
            
            # Birth
            if person_data.get('birth_date') or person_data.get('birth_place'):
                gedcom_lines.append("1 BIRT")
                if person_data.get('birth_date'):
                    gedcom_lines.append(f"2 DATE {person_data['birth_date']}")
                if person_data.get('birth_place'):
                    gedcom_lines.append(f"2 PLAC {person_data['birth_place']}")
            
            # Death
            if person_data.get('death_date') or person_data.get('death_place'):
                gedcom_lines.append("1 DEAT")
                if person_data.get('death_date'):
                    gedcom_lines.append(f"2 DATE {person_data['death_date']}")
                if person_data.get('death_place'):
                    gedcom_lines.append(f"2 PLAC {person_data['death_place']}")
            
            # Notes
            if submission.get('notes'):
                note_id = f"SUB_NOTE{note_counter:06d}"
                gedcom_lines.append(f"1 NOTE @{note_id}@")
                note_counter += 1
            
            # Submission metadata note
            meta_note_id = f"SUB_META{note_counter:06d}"
            gedcom_lines.append(f"1 NOTE @{meta_note_id}@")
            note_counter += 1
            
            person_counter += 1
            gedcom_lines.append("")
    
    # Add note records
    note_counter = 1
    for submission in submissions:
        if submission.get('notes'):
            note_id = f"SUB_NOTE{note_counter:06d}"
            gedcom_lines.append(f"0 @{note_id}@ NOTE")
            gedcom_lines.append(f"1 CONT {submission['notes']}")
            if submission.get('sources'):
                gedcom_lines.append(f"1 CONT Sources: {submission['sources']}")
            gedcom_lines.append("")
            note_counter += 1
        
        # Metadata note
        meta_note_id = f"SUB_META{note_counter:06d}"
        gedcom_lines.append(f"0 @{meta_note_id}@ NOTE")
        gedcom_lines.append(f"1 CONT Submitted by: {submission.get('submitter_name', 'Unknown')}")
        gedcom_lines.append(f"1 CONT Email: {submission.get('submitter_email', 'Unknown')}")
        gedcom_lines.append(f"1 CONT Date: {submission.get('timestamp', 'Unknown')}")
        gedcom_lines.append(f"1 CONT Type: {submission.get('type', 'Unknown')}")
        gedcom_lines.append("")
        note_counter += 1
    
    gedcom_lines.append("0 TRLR")
    
    return '\n'.join(gedcom_lines)

if __name__ == '__main__':
    # Use environment variables for production deployment
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG) 