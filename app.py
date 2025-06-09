from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import json
import os
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from gedcom_parser import GedcomParser
from relationship_calculator import RelationshipCalculator
from generation_calculator import GenerationCalculator

# Configuration
DEBUG = os.getenv('FLASK_ENV') != 'production'
PORT = int(os.getenv('PORT', 5001))
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

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

# Set default reference person (will be initialized after function definition)
current_reference_person = None

# Authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin_login'))
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
    global current_reference_person
    
    # Initialize reference person if not set
    if current_reference_person is None:
        current_reference_person = find_main_person()
    
    # Get current reference person data to display on load
    reference_person = family_data['individuals'].get(current_reference_person, {})
    reference_name = "Unknown"
    if reference_person.get('names'):
        primary_name = reference_person['names'][0]
        reference_name = f"{primary_name.get('given', '')} {primary_name.get('surname', '')}".strip()
    
    return render_template('index.html', 
                         initial_person_id=current_reference_person,
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
    return render_template('admin.html',
                         app_version=APP_VERSION,
                         database_version=DATABASE_VERSION,
                         gedcom_filename=gedcom_file,
                         total_individuals=len(family_data['individuals']),
                         total_families=len(family_data['families']))

@app.route('/search')
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
def get_person(person_id):
    global current_reference_person
    
    if person_id not in family_data['individuals']:
        return jsonify({'error': 'Person not found'}), 404
    
    # Initialize reference person if not set
    if current_reference_person is None:
        current_reference_person = find_main_person()
    
    person = family_data['individuals'][person_id]
    
    # Calculate relationship to the current reference person
    relationship = relationship_calc.calculate_relationship(current_reference_person, person_id)
    
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
    """Find Sam Adjei (the submitter) as the main reference person"""
    for person_id, person in family_data['individuals'].items():
        names = person.get('names', [])
        for name_info in names:
            full_name = f"{name_info.get('given', '')} {name_info.get('surname', '')}".strip()
            if 'Sam' in full_name and 'Adjei' in full_name:
                return person_id
    
    # Fallback to first person if Sam not found
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
    """Set a new reference person for relationship calculations"""
    global current_reference_person
    
    if person_id not in family_data['individuals']:
        return jsonify({'success': False, 'error': 'Person not found'}), 404
    
    current_reference_person = person_id
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
    """Get current reference person information"""
    person = family_data['individuals'].get(current_reference_person, {})
    reference_name = "Unknown"
    if person.get('names'):
        primary_name = person['names'][0]
        reference_name = f"{primary_name.get('given', '')} {primary_name.get('surname', '')}".strip()
    
    return jsonify({
        'reference_person_id': current_reference_person,
        'reference_person_name': reference_name
    })

@app.route('/submit_update', methods=['POST'])
def submit_update():
    """Submit an update or correction for an existing person"""
    try:
        data = request.get_json()
        submission = {
            'type': 'update',
            'person_id': data.get('person_id'),
            'submitter_name': data.get('submitter_name'),
            'submitter_email': data.get('submitter_email'),
            'timestamp': datetime.now().isoformat(),
            'changes': data.get('changes', {}),
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
        submission = {
            'type': 'new_person',
            'submitter_name': data.get('submitter_name'),
            'submitter_email': data.get('submitter_email'),
            'timestamp': datetime.now().isoformat(),
            'person_data': {
                'given_name': data.get('given_name'),
                'surname': data.get('surname'),
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
    """Export submissions in GEDCOM-compatible format"""
    try:
        submissions = load_submissions()
        gedcom_export = generate_gedcom_export(submissions)
        
        return jsonify({
            'success': True,
            'submissions': submissions,
            'gedcom_data': gedcom_export,
            'count': len(submissions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/export_feedback')
def export_feedback():
    """Export all feedback for review"""
    try:
        feedback_list = load_feedback()
        
        return jsonify({
            'success': True,
            'feedback': feedback_list,
            'count': len(feedback_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

def save_submission(submission):
    """Save a submission to the submissions file"""
    submissions_file = 'family_submissions.json'
    
    # Load existing submissions
    if os.path.exists(submissions_file):
        with open(submissions_file, 'r', encoding='utf-8') as f:
            submissions = json.load(f)
    else:
        submissions = []
    
    # Add new submission
    submissions.append(submission)
    
    # Save back to file
    with open(submissions_file, 'w', encoding='utf-8') as f:
        json.dump(submissions, f, indent=2, ensure_ascii=False)

def load_submissions():
    """Load all submissions from the submissions file"""
    submissions_file = 'family_submissions.json'
    
    if os.path.exists(submissions_file):
        with open(submissions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_feedback(feedback):
    """Save feedback to the feedback file"""
    feedback_file = 'family_feedback.json'
    
    # Load existing feedback
    if os.path.exists(feedback_file):
        with open(feedback_file, 'r', encoding='utf-8') as f:
            feedback_list = json.load(f)
    else:
        feedback_list = []
    
    # Add new feedback
    feedback_list.append(feedback)
    
    # Save back to file
    with open(feedback_file, 'w', encoding='utf-8') as f:
        json.dump(feedback_list, f, indent=2, ensure_ascii=False)

def load_feedback():
    """Load all feedback from the feedback file"""
    feedback_file = 'family_feedback.json'
    
    if os.path.exists(feedback_file):
        with open(feedback_file, 'r', encoding='utf-8') as f:
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