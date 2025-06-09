#!/usr/bin/env python3
import json
from app import load_submissions, generate_gedcom_export

# Load and display current submissions
submissions = load_submissions()

print("=== CURRENT SUBMISSIONS ===")
print(f"Total submissions: {len(submissions)}")
print()

for i, submission in enumerate(submissions, 1):
    print(f"Submission #{i}:")
    print(f"  Type: {submission['type']}")
    print(f"  Submitter: {submission['submitter_name']} ({submission['submitter_email']})")
    print(f"  Date: {submission['timestamp']}")
    
    if submission['type'] == 'update':
        print(f"  Person ID: {submission['person_id']}")
        print(f"  Changes: {submission['changes']}")
    elif submission['type'] == 'new_person':
        person_data = submission['person_data']
        print(f"  New Person: {person_data['given_name']} {person_data['surname']}")
        print(f"  Birth: {person_data.get('birth_date', 'Not provided')}")
    
    print(f"  Notes: {submission.get('notes', 'None')}")
    print(f"  Sources: {submission.get('sources', 'None')}")
    print()

# Generate GEDCOM export
print("=== GEDCOM EXPORT (For MacFamilyTree Import) ===")
gedcom_export = generate_gedcom_export(submissions)
print(gedcom_export) 