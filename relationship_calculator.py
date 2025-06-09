from collections import deque

class RelationshipCalculator:
    def __init__(self, family_data):
        self.individuals = family_data['individuals']
        self.families = family_data['families']
        
    def calculate_relationship(self, person1_id, person2_id):
        """Calculate the relationship between two people"""
        if person1_id == person2_id:
            return "Self"
        
        if person1_id not in self.individuals or person2_id not in self.individuals:
            return "Unknown relationship"
        
        # Find shortest path between the two people
        path = self._find_path(person1_id, person2_id)
        
        if not path:
            return "No known relationship"
        
        return self._interpret_relationship_path(path, person1_id, person2_id)
    
    def _find_path(self, start_id, target_id):
        """Find the shortest path between two people using BFS"""
        if start_id == target_id:
            return [start_id]
        
        visited = set()
        queue = deque([(start_id, [start_id])])
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Get all connected people (parents, children, spouses)
            connected_people = self._get_connected_people(current_id)
            
            for connected_id in connected_people:
                if connected_id == target_id:
                    return path + [connected_id]
                
                if connected_id not in visited:
                    queue.append((connected_id, path + [connected_id]))
        
        return None
    
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
    
    def _interpret_relationship_path(self, path, person1_id, person2_id):
        """Interpret a relationship path to generate a relationship description"""
        if len(path) < 2:
            return "Unknown relationship"
        
        # Simple direct relationships
        if len(path) == 2:
            return self._get_direct_relationship(person1_id, person2_id)
        
        # For longer paths, try to determine the relationship type
        if len(path) == 3:
            middle_person = path[1]
            rel1 = self._get_direct_relationship(person1_id, middle_person)
            rel2 = self._get_direct_relationship(middle_person, person2_id)
            
            # Sibling relationships
            if rel1 in ["Child", "Son", "Daughter"] and rel2 in ["Child", "Son", "Daughter"]:
                return self._get_sibling_relationship(person2_id)
            
            # Grandparent/grandchild relationships
            if rel1 in ["Child", "Son", "Daughter"] and rel2 in ["Parent", "Father", "Mother"]:
                return self._get_grandparent_relationship(person2_id, person1_id)
            if rel1 in ["Parent", "Father", "Mother"] and rel2 in ["Child", "Son", "Daughter"]:
                return self._get_grandchild_relationship(person2_id)
            
            # Uncle/aunt and niece/nephew relationships
            if rel1 in ["Parent", "Father", "Mother"] and rel2 == "Sibling":
                return self._get_aunt_uncle_relationship(person2_id)
            if rel1 == "Sibling" and rel2 in ["Child", "Son", "Daughter"]:
                return self._get_niece_nephew_relationship(person2_id)
            
            # In-law relationships - spouse's parents
            if rel1 == "Spouse" and rel2 in ["Parent", "Father", "Mother"]:
                return self._get_parent_in_law_relationship(person2_id)
            
            # In-law relationships - child's spouse
            if rel1 in ["Parent", "Father", "Mother"] and rel2 == "Spouse":
                return self._get_child_in_law_relationship(person2_id)
            
            # In-law relationships - spouse's siblings
            if rel1 == "Spouse" and rel2 == "Sibling":
                return self._get_sibling_in_law_relationship(person2_id)
            
            # In-law relationships - sibling's spouse
            if rel1 == "Sibling" and rel2 == "Spouse":
                return self._get_sibling_in_law_relationship(person2_id)
        
        # Handle 4-step relationships for extended in-law relationships
        if len(path) == 4:
            middle1 = path[1]
            middle2 = path[2]
            rel1 = self._get_direct_relationship(person1_id, middle1)
            rel2 = self._get_direct_relationship(middle1, middle2)
            rel3 = self._get_direct_relationship(middle2, person2_id)
            
            # Spouse's grandparents (spouse -> parent -> parent)
            if (rel1 == "Spouse" and 
                rel2 in ["Parent", "Father", "Mother"] and 
                rel3 in ["Parent", "Father", "Mother"]):
                return self._get_grandparent_in_law_relationship(person2_id)
            
            # Grandchild's spouse (child -> child -> spouse)
            if (rel1 in ["Child", "Son", "Daughter"] and 
                rel2 in ["Child", "Son", "Daughter"] and 
                rel3 == "Spouse"):
                return self._get_grandchild_in_law_relationship(person2_id)
            
            # Spouse's aunt/uncle (spouse -> parent -> sibling)
            if (rel1 == "Spouse" and 
                rel2 in ["Parent", "Father", "Mother"] and 
                rel3 == "Sibling"):
                return self._get_aunt_uncle_in_law_relationship(person2_id)
            
            # Spouse's sibling's spouse (spouse -> sibling -> spouse)
            if (rel1 == "Spouse" and 
                rel2 == "Sibling" and 
                rel3 == "Spouse"):
                return self._get_sibling_in_law_relationship(person2_id)
            
            # Spouse's sibling's children (spouse -> sibling -> child)
            if (rel1 == "Spouse" and 
                rel2 == "Sibling" and 
                rel3 in ["Child", "Son", "Daughter"]):
                return self._get_niece_nephew_relationship(person2_id)
            
            # Sibling's spouse's sibling (sibling -> spouse -> sibling)
            if (rel1 == "Sibling" and 
                rel2 == "Spouse" and 
                rel3 == "Sibling"):
                return self._get_sibling_in_law_relationship(person2_id)
        
        # Handle 5-step relationships for very extended in-law relationships
        if len(path) == 5:
            middle1 = path[1]
            middle2 = path[2]
            middle3 = path[3]
            rel1 = self._get_direct_relationship(person1_id, middle1)
            rel2 = self._get_direct_relationship(middle1, middle2)
            rel3 = self._get_direct_relationship(middle2, middle3)
            rel4 = self._get_direct_relationship(middle3, person2_id)
            
            # Spouse's sibling's spouse's sibling (spouse -> sibling -> spouse -> sibling)
            if (rel1 == "Spouse" and 
                rel2 == "Sibling" and 
                rel3 == "Spouse" and 
                rel4 == "Sibling"):
                return self._get_sibling_in_law_relationship(person2_id)
            
            # Spouse's sibling's child's spouse (spouse -> sibling -> child -> spouse)
            if (rel1 == "Spouse" and 
                rel2 == "Sibling" and 
                rel3 in ["Child", "Son", "Daughter"] and 
                rel4 == "Spouse"):
                return self._get_child_in_law_relationship(person2_id)
        
        # For complex relationships, provide a general description
        generations_up = 0
        generations_down = 0
        
        for i in range(len(path) - 1):
            rel = self._get_direct_relationship(path[i], path[i + 1])
            if rel in ["Parent", "Father", "Mother"]:
                generations_up += 1
            elif rel in ["Child", "Son", "Daughter"]:
                generations_down += 1
        
        net_generations = generations_up - generations_down
        
        if net_generations > 0:
            if net_generations == 1:
                return "Parent"
            elif net_generations == 2:
                return "Grandparent"
            else:
                return f"{net_generations}x Great-Grandparent"
        elif net_generations < 0:
            abs_generations = abs(net_generations)
            if abs_generations == 1:
                return "Child"
            elif abs_generations == 2:
                return "Grandchild"
            else:
                return f"{abs_generations}x Great-Grandchild"
        else:
            # Same generation - likely cousin
            if len(path) > 3:
                return "Cousin"
            else:
                return "Related"
    
    def _get_direct_relationship(self, person1_id, person2_id):
        """Get the direct relationship between two people (parent/child/spouse/sibling)"""
        person1 = self.individuals.get(person1_id, {})
        person2 = self.individuals.get(person2_id, {})
        
        # Check if person2 is a child of person1
        for family_id in person1.get('spouse_in_families', []):
            family = self.families.get(family_id, {})
            if person2_id in family.get('children', []):
                person2_sex = person2.get('sex', 'U')
                if person2_sex == 'M':
                    return "Son"
                elif person2_sex == 'F':
                    return "Daughter"
                else:
                    return "Child"
        
        # Check if person1 is a child of person2
        for family_id in person2.get('spouse_in_families', []):
            family = self.families.get(family_id, {})
            if person1_id in family.get('children', []):
                person2_sex = person2.get('sex', 'U')
                if person2_sex == 'M':
                    return "Father"
                elif person2_sex == 'F':
                    return "Mother"
                else:
                    return "Parent"
        
        # Check if they are spouses
        for family_id in person1.get('spouse_in_families', []):
            family = self.families.get(family_id, {})
            if (family.get('husband') == person1_id and family.get('wife') == person2_id) or \
               (family.get('wife') == person1_id and family.get('husband') == person2_id):
                return "Spouse"
        
        # Check if they are siblings
        for family_id in person1.get('child_of_families', []):
            family = self.families.get(family_id, {})
            if person2_id in family.get('children', []):
                return "Sibling"
        
        return "Related"
    
    def get_ancestors(self, person_id, generations=3):
        """Get ancestors of a person up to specified generations"""
        ancestors = []
        current_generation = [person_id]
        
        for gen in range(generations):
            next_generation = []
            for person in current_generation:
                parents = self._get_parents(person)
                next_generation.extend(parents)
                if parents:
                    ancestors.extend([(parent, gen + 1) for parent in parents])
            
            if not next_generation:
                break
            current_generation = next_generation
        
        return ancestors
    
    def get_descendants(self, person_id, generations=3):
        """Get descendants of a person up to specified generations"""
        descendants = []
        current_generation = [person_id]
        
        for gen in range(generations):
            next_generation = []
            for person in current_generation:
                children = self._get_children(person)
                next_generation.extend(children)
                if children:
                    descendants.extend([(child, gen + 1) for child in children])
            
            if not next_generation:
                break
            current_generation = next_generation
        
        return descendants
    
    def _get_parents(self, person_id):
        """Get the parents of a person"""
        parents = []
        person = self.individuals.get(person_id, {})
        
        for family_id in person.get('child_of_families', []):
            family = self.families.get(family_id, {})
            if family.get('husband'):
                parents.append(family['husband'])
            if family.get('wife'):
                parents.append(family['wife'])
        
        return parents
    
    def _get_children(self, person_id):
        """Get the children of a person"""
        children = []
        person = self.individuals.get(person_id, {})
        
        for family_id in person.get('spouse_in_families', []):
            family = self.families.get(family_id, {})
            children.extend(family.get('children', []))
        
        return children
    
    def _get_sibling_relationship(self, person_id):
        """Get specific sibling relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Brother"
        elif sex == 'F':
            return "Sister"
        else:
            return "Sibling"
    
    def _get_grandparent_relationship(self, person_id, reference_id):
        """Get specific grandparent relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Grandfather"
        elif sex == 'F':
            return "Grandmother"
        else:
            return "Grandparent"
    
    def _get_grandchild_relationship(self, person_id):
        """Get specific grandchild relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Grandson"
        elif sex == 'F':
            return "Granddaughter"
        else:
            return "Grandchild"
    
    def _get_aunt_uncle_relationship(self, person_id):
        """Get specific aunt/uncle relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Uncle"
        elif sex == 'F':
            return "Aunt"
        else:
            return "Uncle/Aunt"
    
    def _get_niece_nephew_relationship(self, person_id):
        """Get specific niece/nephew relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Nephew"
        elif sex == 'F':
            return "Niece"
        else:
            return "Niece/Nephew"
    
    def _get_parent_in_law_relationship(self, person_id):
        """Get specific parent-in-law relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Father-in-law"
        elif sex == 'F':
            return "Mother-in-law"
        else:
            return "Parent-in-law"
    
    def _get_child_in_law_relationship(self, person_id):
        """Get specific child-in-law relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Son-in-law"
        elif sex == 'F':
            return "Daughter-in-law"
        else:
            return "Child-in-law"
    
    def _get_sibling_in_law_relationship(self, person_id):
        """Get specific sibling-in-law relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Brother-in-law"
        elif sex == 'F':
            return "Sister-in-law"
        else:
            return "Sibling-in-law"
    
    def _get_grandparent_in_law_relationship(self, person_id):
        """Get specific grandparent-in-law relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Grandfather-in-law"
        elif sex == 'F':
            return "Grandmother-in-law"
        else:
            return "Grandparent-in-law"
    
    def _get_grandchild_in_law_relationship(self, person_id):
        """Get specific grandchild-in-law relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Grandson-in-law"
        elif sex == 'F':
            return "Granddaughter-in-law"
        else:
            return "Grandchild-in-law"
    
    def _get_aunt_uncle_in_law_relationship(self, person_id):
        """Get specific aunt/uncle-in-law relationship with gender"""
        person = self.individuals.get(person_id, {})
        sex = person.get('sex', 'U')
        if sex == 'M':
            return "Uncle-in-law"
        elif sex == 'F':
            return "Aunt-in-law"
        else:
            return "Aunt/Uncle-in-law" 