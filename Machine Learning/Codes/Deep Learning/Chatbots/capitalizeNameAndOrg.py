import re
import spacy
from typing import List, Tuple, Dict
import nltk
from nltk import ne_chunk, pos_tag, word_tokenize
from nltk.tree import Tree

# Download required NLTK data (run once)
#nltk.data.path.append('E:\Machine Learning\Codes\Deep Learning\Chatbots\CapitalizeNameAndOrg')
#nltk.download('punkt',download_dir= 'E:\Machine Learning\Codes\Deep Learning\Chatbots\CapitalizeNameAndOrg')
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('taggers/averaged_perceptron_tagger')
    nltk.data.find('chunkers/maxent_ne_chunker')
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')
    nltk.download('words')

class NameOrganizationCapitalizer:
    """Class to identify and capitalize names and organizations in text"""
    
    def __init__(self, method='spacy'):
        """
        Initialize with preferred NER method
        Args:
            method: 'spacy', 'nltk', or 'combined'
        """
        self.method = method
        
        # Load spaCy model if needed
        if method in ['spacy', 'combined']:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None
        
        # Common prefixes and suffixes for organizations
        self.org_indicators = {
            'prefixes': ['the', 'a', 'an'],
            'suffixes': ['inc', 'corp', 'corporation', 'company', 'co', 'ltd', 'limited', 
                        'llc', 'llp', 'plc', 'ag', 'sa', 'gmbh', 'kg', 'oy']
        }
        
        # Common title prefixes that should remain lowercase unless at sentence start
        self.title_prefixes = ['mr', 'mrs', 'ms', 'dr', 'prof', 'sir', 'lady']
    
    def extract_entities_spacy(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Extract named entities using spaCy"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG']:
                entities.append((ent.text, ent.label_, ent.start_char, ent.end_char))
        
        return entities
    
    def extract_entities_nltk(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Extract named entities using NLTK"""
        tokens = word_tokenize(text)
        pos_tags = pos_tag(tokens)
        tree = ne_chunk(pos_tags)
        
        entities = []
        current_pos = 0
        
        for subtree in tree:
            if isinstance(subtree, Tree):
                entity_name = ' '.join([token for token, pos in subtree.leaves()])
                entity_type = subtree.label()
                
                if entity_type in ['PERSON', 'ORGANIZATION']:
                    # Find position in original text
                    start_pos = text.find(entity_name, current_pos)
                    if start_pos != -1:
                        end_pos = start_pos + len(entity_name)
                        entities.append((entity_name, entity_type, start_pos, end_pos))
                        current_pos = end_pos
            else:
                # Update position for non-entity tokens
                token, pos = subtree
                current_pos = text.find(token, current_pos) + len(token)
        
        return entities
    
    def extract_entities_regex(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Extract potential names and organizations using regex patterns"""
        entities = []
        
        # Pattern for potential person names (Title Case words, possibly with titles)
        person_pattern = r'\b(?:(?:Mr|Mrs|Ms|Dr|Prof|Sir|Lady)\.?\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        
        # Pattern for potential organizations (words with Inc, Corp, etc.)
        org_pattern = r'\b[A-Z][a-zA-Z\s&]+(?:Inc|Corp|Corporation|Company|Co|Ltd|Limited|LLC|LLP|PLC)\.?\b'
        
        # Find person names
        for match in re.finditer(person_pattern, text):
            entities.append((match.group(), 'PERSON', match.start(), match.end()))
        
        # Find organizations
        for match in re.finditer(org_pattern, text):
            entities.append((match.group(), 'ORG', match.start(), match.end()))
        
        return entities
    
    def capitalize_proper_name(self, name: str, entity_type: str) -> str:
        """Properly capitalize a name or organization"""
        if not name:
            return name
        
        words = name.split()
        capitalized_words = []
        
        for i, word in enumerate(words):
            word_lower = word.lower()
            
            # Handle different cases
            if entity_type == 'PERSON':
                # For person names
                if word_lower in self.title_prefixes and i == 0:
                    # Capitalize titles at the beginning
                    capitalized_words.append(word_lower.capitalize())
                elif word_lower in ['of', 'the', 'and', 'von', 'van', 'de', 'da', 'di']:
                    # Keep certain prepositions lowercase unless at start
                    if i == 0:
                        capitalized_words.append(word_lower.capitalize())
                    else:
                        capitalized_words.append(word_lower)
                else:
                    # Capitalize other words
                    capitalized_words.append(word_lower.capitalize())
            
            elif entity_type == 'ORG':
                # For organizations
                if word_lower in self.org_indicators['prefixes'] and i > 0:
                    # Keep articles lowercase unless at start
                    capitalized_words.append(word_lower)
                elif word_lower in self.org_indicators['suffixes']:
                    # Handle common business suffixes
                    if word_lower in ['inc', 'corp', 'ltd', 'llc', 'llp', 'plc']:
                        capitalized_words.append(word_lower.upper())
                    else:
                        capitalized_words.append(word_lower.capitalize())
                elif word_lower in ['of', 'the', 'and', 'for', 'in', 'on', 'at', 'to']:
                    # Keep prepositions lowercase unless at start
                    if i == 0:
                        capitalized_words.append(word_lower.capitalize())
                    else:
                        capitalized_words.append(word_lower)
                else:
                    # Capitalize other words
                    capitalized_words.append(word_lower.capitalize())
        
        return ' '.join(capitalized_words)
    
    def capitalize_text(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Capitalize names and organizations in text
        Returns: (modified_text, list_of_changes)
        """
        # Extract entities based on chosen method
        if self.method == 'spacy':
            entities = self.extract_entities_spacy(text)
        elif self.method == 'nltk':
            entities = self.extract_entities_nltk(text)
        elif self.method == 'regex':
            entities = self.extract_entities_regex(text)
        elif self.method == 'combined':
            # Combine results from multiple methods
            spacy_entities = self.extract_entities_spacy(text)
            nltk_entities = self.extract_entities_nltk(text)
            regex_entities = self.extract_entities_regex(text)
            
            # Merge and deduplicate entities
            entities = self.merge_entities([spacy_entities, nltk_entities, regex_entities])
        else:
            entities = []
        
        # Sort entities by position (reverse order for replacement)
        entities.sort(key=lambda x: x[2], reverse=True)
        
        modified_text = text
        changes = []
        
        # Replace entities with capitalized versions
        for entity_text, entity_type, start_pos, end_pos in entities:
            original = entity_text
            capitalized = self.capitalize_proper_name(entity_text, entity_type)
            
            if original != capitalized:
                modified_text = modified_text[:start_pos] + capitalized + modified_text[end_pos:]
                changes.append({
                    'original': original,
                    'capitalized': capitalized,
                    'type': entity_type,
                    'position': (start_pos, end_pos)
                })
        
        return modified_text, changes
    
    def merge_entities(self, entity_lists: List[List[Tuple]]) -> List[Tuple]:
        """Merge and deduplicate entities from multiple sources"""
        all_entities = []
        for entity_list in entity_lists:
            all_entities.extend(entity_list)
        
        # Remove duplicates based on text and position overlap
        unique_entities = []
        for entity in all_entities:
            entity_text, entity_type, start, end = entity
            
            # Check if this entity overlaps with existing ones
            is_duplicate = False
            for existing in unique_entities:
                existing_text, existing_type, existing_start, existing_end = existing
                
                # Check for overlap
                if (start < existing_end and end > existing_start) or \
                   (entity_text.lower() == existing_text.lower()):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_entities.append(entity)
        
        return unique_entities
    
    def capitalize_first_char_only(self, text: str) -> str:
        """Simple method to capitalize only the first character of detected entities"""
        # This is a simpler alternative that just capitalizes first letters
        entities = []
        
        if self.method == 'spacy' and self.nlp:
            entities = self.extract_entities_spacy(text)
        elif self.method == 'nltk':
            entities = self.extract_entities_nltk(text)
        else:
            entities = self.extract_entities_regex(text)
        
        # Sort by position (reverse order)
        entities.sort(key=lambda x: x[2], reverse=True)
        
        modified_text = text
        
        for entity_text, entity_type, start_pos, end_pos in entities:
            if entity_text and entity_text[0].islower():
                # Only capitalize if first character is lowercase
                capitalized = entity_text[0].upper() + entity_text[1:]
                modified_text = modified_text[:start_pos] + capitalized + modified_text[end_pos:]
        
        return modified_text

# Additional utility functions
def capitalize_sentences(text: str) -> str:
    """Capitalize the first letter of each sentence"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    capitalized_sentences = []
    
    for sentence in sentences:
        if sentence:
            # Capitalize first letter of sentence
            first_char_index = 0
            while first_char_index < len(sentence) and not sentence[first_char_index].isalpha():
                first_char_index += 1
            
            if first_char_index < len(sentence):
                capitalized = (sentence[:first_char_index] + 
                             sentence[first_char_index].upper() + 
                             sentence[first_char_index + 1:])
                capitalized_sentences.append(capitalized)
            else:
                capitalized_sentences.append(sentence)
    
    return ' '.join(capitalized_sentences)

def smart_capitalize_text(text: str, method='spacy') -> str:
    """
    Comprehensive text capitalization including sentences and named entities
    """
    # Initialize capitalizer
    capitalizer = NameOrganizationCapitalizer(method=method)
    
    # First, capitalize named entities
    entity_capitalized_text, changes = capitalizer.capitalize_text(text)
    
    # Then, capitalize sentence beginnings
    final_text = capitalize_sentences(entity_capitalized_text)
    
    return final_text

# Example usage and testing
def main():
    """Example usage of the capitalization tools"""
    
    # Sample text with various capitalization issues
    sample_text = """
    hello, my name is john smith and i work at microsoft corporation. 
    yesterday, i met dr. sarah johnson from google inc. 
    we discussed a partnership between microsoft and the reuters news agency. 
    the meeting was held at apple park in cupertino.
    """
    sample_text = """i am asif from microsoft, i want to learn Generative AI, please help me"""
    print("=== Original Text ===")
    print(sample_text)
    
    # Method 1: Using spaCy (most accurate)
    print("\n=== Using spaCy NER ===")
    capitalizer_spacy = NameOrganizationCapitalizer(method='spacy')
    capitalized_text, changes = capitalizer_spacy.capitalize_text(sample_text)
    
    print("Capitalized text:")
    print(capitalized_text)
    print("\nChanges made:")
    for change in changes:
        print(f"  {change['original']} → {change['capitalized']} ({change['type']})")
  



    # Method 3: Combined approach with sentence capitalization
    print("\n=== Smart Capitalization (Combined) ===")
    final_text = smart_capitalize_text(sample_text, method='spacy')
    print("Final text:")
    print(final_text)
    
    # Method 4: Simple first character capitalization
    print("\n=== Simple First Character Capitalization ===")
    simple_cap = capitalizer_spacy.capitalize_first_char_only(sample_text)
    print("Simple capitalized text:")
    print(simple_cap)

'''
    # Method 2: Using NLTK
    print("\n=== Using NLTK NER ===")
    capitalizer_nltk = NameOrganizationCapitalizer(method='nltk')
    capitalized_text_nltk, changes_nltk = capitalizer_nltk.capitalize_text(sample_text)
    print("Capitalized text:")
    print(capitalized_text_nltk)
'''

if __name__ == "__main__":
    main()