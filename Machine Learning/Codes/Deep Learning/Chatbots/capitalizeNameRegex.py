from spacy.matcher import Matcher
import spacy

def get_spacy_model():
    return spacy.load("en_core_web_sm") #  python -m spacy download en_core_web_sm
nlp = get_spacy_model()
matcher = Matcher(nlp.vocab)

def setup_name_patterns():
    """Setup patterns for common name contexts"""
   
    
    # Patterns that often precede names
    name_context_patterns = [
        [{"LOWER": {"IN": ["my", "i'm", "i", "am"]}}, {"LOWER": {"REGEX": r"^[a-z]{2,}$"}}],
        [{"LOWER": "name"}, {"LOWER": "is"}, {"LOWER": {"REGEX": r"^[a-z]{2,}$"}}],
        [{"LOWER": "call"}, {"LOWER": "me"}, {"LOWER": {"REGEX": r"^[a-z]{2,}$"}}],
        [{"LOWER": "hello"}, {"LOWER": {"REGEX": r"^[a-z]{2,}$"}}],
        [{"LOWER": "hi"}, {"LOWER": {"REGEX": r"^[a-z]{2,}$"}}],
    ]
    
    for i, pattern in enumerate(name_context_patterns):
        matcher.add(f"NAME_CONTEXT_{i}", [pattern])

    def smart_capitalize( text):
        """Capitalize likely names based on context"""
        setup_name_patterns()  # Ensure patterns are set up
        doc = nlp(text)
        matches = matcher(doc)

        # Copy tokens to a list for modification
        tokens = [token.text for token in doc]

        # Only capitalize the likely name, not the word before it
        for match_id, start, end in matches:
            if end-1 < len(tokens):
                # Capitalize only the last token in the match (the name)
                word_to_cap = tokens[end-1]
                if word_to_cap.islower() and len(word_to_cap) >= 2:
                    tokens[end-1] = word_to_cap.capitalize()

        # Reconstruct the text using spaCy's token spacing
        new_text = ""
        for i, token in enumerate(doc):
            if i > 0:
                if token.whitespace_:
                    new_text += token.whitespace_
                else:
                    # Add a space if the previous token was a word and this is a word
                    if not doc[i-1].is_punct and not token.is_punct:
                        new_text += " "
            new_text += tokens[i]
        return new_text