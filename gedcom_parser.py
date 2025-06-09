import re
from datetime import datetime

class GedcomParser:
    def __init__(self):
        self.individuals = {}
        self.families = {}
        self.notes = {}
        self.current_record = None
        self.current_record_type = None
        
    def parse_file(self, filename):
        """Parse a GEDCOM file and return structured data"""
        self.individuals = {}
        self.families = {}
        self.notes = {}
        
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(filename, 'r', encoding='latin-1') as file:
                lines = file.readlines()
        
        for line in lines:
            self.parse_line(line.strip())
        
        # Post-process to add family references to individuals
        self._add_family_references()
        
        # Resolve note references
        self._resolve_note_references()
        
        return {
            'individuals': self.individuals,
            'families': self.families,
            'notes': self.notes
        }
    
    def parse_line(self, line):
        """Parse a single GEDCOM line"""
        if not line:
            return
        
        # Parse level, tag, and value
        parts = line.split(' ', 2)
        level = int(parts[0])
        
        if len(parts) < 2:
            return
            
        tag_or_id = parts[1]
        value = parts[2] if len(parts) > 2 else ''
        
        # Handle record headers (level 0)
        if level == 0:
            if tag_or_id.startswith('@') and tag_or_id.endswith('@'):
                record_id = tag_or_id[1:-1]  # Remove @ symbols
                record_type = value
                
                if record_type == 'INDI':
                    self.current_record = record_id
                    self.current_record_type = 'INDI'
                    self.individuals[record_id] = {
                        'names': [],
                        'events': [],
                        'child_of_families': [],
                        'spouse_in_families': [],
                        'notes': []
                    }
                elif record_type == 'FAM':
                    self.current_record = record_id
                    self.current_record_type = 'FAM'
                    self.families[record_id] = {
                        'children': [],
                        'events': []
                    }
                elif record_type == 'NOTE':
                    self.current_record = record_id
                    self.current_record_type = 'NOTE'
                    self.notes[record_id] = {
                        'content': '',
                        'continuation': []
                    }
            return
        
        # Handle individual records
        if self.current_record_type == 'INDI' and self.current_record:
            self._parse_individual_data(level, tag_or_id, value)
        elif self.current_record_type == 'FAM' and self.current_record:
            self._parse_family_data(level, tag_or_id, value)
        elif self.current_record_type == 'NOTE' and self.current_record:
            self._parse_note_data(level, tag_or_id, value)
    
    def _parse_individual_data(self, level, tag, value):
        """Parse individual-specific data"""
        individual = self.individuals[self.current_record]
        
        if level == 1:
            if tag == 'NAME':
                name_info = self._parse_name(value)
                individual['names'].append(name_info)
            elif tag == 'SEX':
                individual['sex'] = value
            elif tag == 'BIRT':
                individual['_current_event'] = 'birth'
            elif tag == 'DEAT':
                individual['_current_event'] = 'death'
            elif tag == 'FAMC':
                family_id = value[1:-1] if value.startswith('@') and value.endswith('@') else value
                individual['child_of_families'].append(family_id)
            elif tag == 'FAMS':
                family_id = value[1:-1] if value.startswith('@') and value.endswith('@') else value
                individual['spouse_in_families'].append(family_id)
            elif tag == 'NOTE':
                if value.startswith('@') and value.endswith('@'):
                    # Note reference - we'll store the ID and resolve it later
                    note_id = value[1:-1]
                    individual['notes'].append({'type': 'reference', 'id': note_id})
                else:
                    # Direct note text
                    individual['notes'].append({'type': 'text', 'content': value})
            elif tag == 'CHAN' or tag == '_CRE':
                # Clear current event to avoid capturing creation dates
                individual['_current_event'] = None
        
        elif level == 2:
            if tag == 'DATE' and individual.get('_current_event'):
                event = individual.get('_current_event')
                if event == 'birth':
                    individual['birth_date'] = value
                    individual['birth_year'] = self._extract_year(value)
                elif event == 'death':
                    individual['death_date'] = value
                    individual['death_year'] = self._extract_year(value)
            elif tag == 'PLAC' and individual.get('_current_event'):
                event = individual.get('_current_event')
                if event == 'birth':
                    individual['birth_place'] = value
                elif event == 'death':
                    individual['death_place'] = value
            elif tag == 'GIVN':
                if individual['names']:
                    individual['names'][-1]['given'] = value
            elif tag == 'SURN':
                if individual['names']:
                    individual['names'][-1]['surname'] = value
            elif tag == '_CRE' or tag == 'CHAN':
                # Clear current event when we hit creation/change records
                individual['_current_event'] = None
        
        elif level == 3:
            # Level 3 is often creation dates, clear the event context
            if tag == 'DATE' and individual.get('_current_event') is None:
                # This is likely a creation date, ignore it
                pass
    
    def _parse_family_data(self, level, tag, value):
        """Parse family-specific data"""
        family = self.families[self.current_record]
        
        if level == 1:
            if tag == 'HUSB':
                person_id = value[1:-1] if value.startswith('@') and value.endswith('@') else value
                family['husband'] = person_id
            elif tag == 'WIFE':
                person_id = value[1:-1] if value.startswith('@') and value.endswith('@') else value
                family['wife'] = person_id
            elif tag == 'CHIL':
                person_id = value[1:-1] if value.startswith('@') and value.endswith('@') else value
                family['children'].append(person_id)
            elif tag == 'MARR':
                family['_current_event'] = 'marriage'
        
        elif level == 2:
            if tag == 'DATE':
                event = family.get('_current_event')
                if event == 'marriage':
                    family['marriage_date'] = value
                    family['marriage_year'] = self._extract_year(value)
            elif tag == 'PLAC':
                event = family.get('_current_event')
                if event == 'marriage':
                    family['marriage_place'] = value
    
    def _parse_name(self, name_string):
        """Parse a GEDCOM name string"""
        # GEDCOM format: "Given Names /Surname/"
        name_info = {'given': '', 'surname': '', 'full': name_string}
        
        # Extract surname (between forward slashes)
        surname_match = re.search(r'/([^/]*?)/', name_string)
        if surname_match:
            name_info['surname'] = surname_match.group(1).strip()
            # Remove surname part to get given names
            given_part = re.sub(r'/[^/]*?/', '', name_string).strip()
            name_info['given'] = given_part
        else:
            # No surname markup, treat entire string as given name
            name_info['given'] = name_string.strip()
        
        return name_info
    
    def _extract_year(self, date_string):
        """Extract year from a date string"""
        if not date_string:
            return None
        
        # Look for 4-digit year
        year_match = re.search(r'\b(1\d{3}|20\d{2})\b', date_string)
        if year_match:
            return int(year_match.group(1))
        
        return None
    
    def _add_family_references(self):
        """Add reverse family references for easier navigation"""
        for family_id, family in self.families.items():
            # Add family reference to husband
            if family.get('husband') and family['husband'] in self.individuals:
                if 'families_as_spouse' not in self.individuals[family['husband']]:
                    self.individuals[family['husband']]['families_as_spouse'] = []
                self.individuals[family['husband']]['families_as_spouse'].append(family_id)
            
            # Add family reference to wife
            if family.get('wife') and family['wife'] in self.individuals:
                if 'families_as_spouse' not in self.individuals[family['wife']]:
                    self.individuals[family['wife']]['families_as_spouse'] = []
                self.individuals[family['wife']]['families_as_spouse'].append(family_id)
            
            # Add family reference to children
            for child_id in family.get('children', []):
                if child_id in self.individuals:
                    if 'families_as_child' not in self.individuals[child_id]:
                        self.individuals[child_id]['families_as_child'] = []
                    self.individuals[child_id]['families_as_child'].append(family_id)

    def _parse_note_data(self, level, tag, value):
        """Parse note-specific data"""
        note = self.notes[self.current_record]
        
        if level == 1:
            if tag == 'CONT':
                # Continuation of note content
                if not note['content']:
                    note['content'] = value
                else:
                    note['continuation'].append(value)
    
    def _resolve_note_references(self):
        """Resolve note references to actual note content"""
        for person_id, person in self.individuals.items():
            resolved_notes = []
            for note in person.get('notes', []):
                if note['type'] == 'reference' and note['id'] in self.notes:
                    # Get the referenced note content
                    referenced_note = self.notes[note['id']]
                    content = referenced_note['content']
                    if referenced_note['continuation']:
                        content += '\n' + '\n'.join(referenced_note['continuation'])
                    resolved_notes.append({
                        'type': 'resolved',
                        'content': content
                    })
                elif note['type'] == 'text':
                    # Direct note text
                    resolved_notes.append(note)
            person['notes'] = resolved_notes 