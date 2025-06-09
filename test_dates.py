from gedcom_parser import GedcomParser

parser = GedcomParser()
try:
    data = parser.parse_file('Weku-2025.ged')
    print(f'Successfully parsed GEDCOM file!')
    print(f'Found {len(data["individuals"])} individuals')
    
    # Test specific people we know have birth dates
    test_people = []
    for person_id, person in data['individuals'].items():
        if person.get('names'):
            name = person['names'][0]
            full_name = f"{name.get('given', '')} {name.get('surname', '')}".strip()
            
            # Look for people with birth dates to test
            if person.get('birth_date') and any(test_name in full_name for test_name in ['Tawiah Akogyeram', 'Anton Wiedemann', 'Mason Stewart', 'Laurence']):
                test_people.append({
                    'name': full_name,
                    'birth_date': person.get('birth_date'),
                    'birth_year': person.get('birth_year'),
                    'id': person_id
                })
    
    print('\n=== Sample Birth Dates (should be actual birth dates, not creation dates) ===')
    for person in test_people[:5]:
        print(f"• {person['name']}: {person['birth_date']} (Year: {person['birth_year']})")
    
    # Count how many people have birth dates
    people_with_birth_dates = sum(1 for p in data['individuals'].values() if p.get('birth_date'))
    print(f'\nTotal people with birth dates: {people_with_birth_dates}')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc() 