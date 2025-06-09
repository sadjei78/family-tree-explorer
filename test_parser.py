from gedcom_parser import GedcomParser

parser = GedcomParser()
try:
    data = parser.parse_file('Weku-2025.ged')
    print(f'Successfully parsed GEDCOM file!')
    print(f'Found {len(data["individuals"])} individuals')
    print(f'Found {len(data["families"])} families')
    
    # Show a few example names
    count = 0
    for person_id, person in data['individuals'].items():
        if person.get('names'):
            name = person['names'][0]
            full_name = f"{name.get('given', '')} {name.get('surname', '')}".strip()
            print(f'Example person: {full_name}')
            count += 1
            if count >= 3:
                break
                
    print('Parser test completed successfully!')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc() 