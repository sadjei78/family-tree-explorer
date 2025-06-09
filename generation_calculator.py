class GenerationCalculator:
    def __init__(self, individuals, families):
        self.individuals = individuals
        self.families = families
        # Use Samuel (1863) as G1 baseline
        self.g1_baseline = "I71243996"  # Samuel - Born: 13 April 1863
        self.generation_cache = {}
        
    def calculate_generation(self, person_id):
        """Calculate generation number for a person relative to G1 baseline"""
        if person_id in self.generation_cache:
            return self.generation_cache[person_id]
        
        if person_id == self.g1_baseline:
            self.generation_cache[person_id] = 1
            return 1
        
        # Use BFS to find shortest path to G1 baseline
        generation = self._calculate_generation_bfs(person_id)
        self.generation_cache[person_id] = generation
        return generation
    
    def _calculate_generation_bfs(self, target_person_id):
        """Use BFS to find generation relative to G1 baseline"""
        if target_person_id == self.g1_baseline:
            return 1
        
        visited = set()
        queue = [(self.g1_baseline, 1)]  # (person_id, generation)
        visited.add(self.g1_baseline)
        
        # Build a graph of all connections
        connections = {}
        for person_id in self.individuals:
            connections[person_id] = self._get_connected_people(person_id)
        
        while queue:
            current_person_id, current_generation = queue.pop(0)
            
            for connected_person_id in connections.get(current_person_id, set()):
                if connected_person_id in visited:
                    continue
                
                visited.add(connected_person_id)
                
                # Determine generation of connected person
                relationship = self._get_relationship_type(current_person_id, connected_person_id)
                
                if relationship == 'child':
                    next_generation = current_generation + 1
                elif relationship == 'parent':
                    next_generation = current_generation - 1
                else:  # sibling or spouse
                    next_generation = current_generation
                
                if connected_person_id == target_person_id:
                    return next_generation
                
                queue.append((connected_person_id, next_generation))
        
        # If no path found, try to estimate based on birth year
        return self._estimate_generation_by_birth_year(target_person_id)
    
    def _get_connected_people(self, person_id):
        """Get all people directly connected to this person"""
        connected = set()
        person = self.individuals.get(person_id, {})
        
        # Get parents and siblings through child_of_families
        for family_id in person.get('child_of_families', []):
            family = self.families.get(family_id, {})
            
            # Add parents
            if family.get('husband'):
                connected.add(family['husband'])
            if family.get('wife'):
                connected.add(family['wife'])
            
            # Add siblings
            for child_id in family.get('children', []):
                if child_id != person_id:
                    connected.add(child_id)
        
        # Get spouses and children through spouse_in_families
        for family_id in person.get('spouse_in_families', []):
            family = self.families.get(family_id, {})
            
            # Add spouse
            if family.get('husband') == person_id and family.get('wife'):
                connected.add(family['wife'])
            elif family.get('wife') == person_id and family.get('husband'):
                connected.add(family['husband'])
            
            # Add children
            for child_id in family.get('children', []):
                connected.add(child_id)
        
        return connected
    
    def _get_relationship_type(self, person1_id, person2_id):
        """Determine the type of relationship between two people"""
        person1 = self.individuals.get(person1_id, {})
        person2 = self.individuals.get(person2_id, {})
        
        # Check if person2 is a child of person1
        for family_id in person1.get('spouse_in_families', []):
            family = self.families.get(family_id, {})
            if person2_id in family.get('children', []):
                return 'child'
        
        # Check if person1 is a child of person2
        for family_id in person2.get('spouse_in_families', []):
            family = self.families.get(family_id, {})
            if person1_id in family.get('children', []):
                return 'parent'
        
        # Check if they are spouses
        for family_id in person1.get('spouse_in_families', []):
            family = self.families.get(family_id, {})
            if (family.get('husband') == person1_id and family.get('wife') == person2_id) or \
               (family.get('wife') == person1_id and family.get('husband') == person2_id):
                return 'spouse'
        
        # Check if they are siblings
        for family_id in person1.get('child_of_families', []):
            family = self.families.get(family_id, {})
            if person2_id in family.get('children', []):
                return 'sibling'
        
        return 'unknown'
    
    def _estimate_generation_by_birth_year(self, person_id):
        """Estimate generation based on birth year if no family connection found"""
        person = self.individuals.get(person_id, {})
        person_birth_year = person.get('birth_year')
        
        if not person_birth_year:
            return None  # Can't estimate without birth year
        
        # G1 baseline is 1863, estimate ~25-30 years per generation
        baseline_year = 1863
        years_per_generation = 27
        
        generation_diff = (person_birth_year - baseline_year) / years_per_generation
        estimated_generation = 1 + round(generation_diff)
        
        # Ensure it's at least G1
        return max(1, estimated_generation)
    
    def get_generation_label(self, person_id):
        """Get the generation label (G1, G2, etc.) for a person"""
        generation = self.calculate_generation(person_id)
        if generation is None:
            return "G?"
        return f"G{generation}"
    
    def get_baseline_info(self):
        """Get information about the G1 baseline person"""
        person = self.individuals.get(self.g1_baseline, {})
        if person.get('names'):
            name = person['names'][0]
            full_name = f"{name.get('given', '')} {name.get('surname', '')}".strip()
            return {
                'id': self.g1_baseline,
                'name': full_name,
                'birth_year': person.get('birth_year'),
                'birth_date': person.get('birth_date')
            }
        return None 