#!/usr/bin/env python3
import requests
import json

# Test the export submissions endpoint
try:
    response = requests.get('http://127.0.0.1:5001/export_submissions')
    data = response.json()
    
    print("=== SUBMISSION EXPORT RESULTS ===")
    print(f"Success: {data['success']}")
    print(f"Number of submissions: {data['count']}")
    print("\n=== GEDCOM EXPORT (Ready for MacFamilyTree) ===")
    print(data['gedcom_data'])
    
except Exception as e:
    print(f"Error: {e}")
    print("Make sure the Flask app is running on port 5001") 