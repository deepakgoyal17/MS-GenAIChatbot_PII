from app import setup_name_patterns, smart_capitalize

# Test case for smart_capitalize function

def test_smart_capitalize():
    setup_name_patterns()  # Ensure patterns are registered
    input_text = "i am asif from microsoft, i want to learn generative ai, please help me"
    expected =   "i Am Asif from microsoft, i want To learn generative ai, please help me"
    output = smart_capitalize(input_text)
    print(f"Input: {input_text}")
    print(f"Output: {output}")  
    assert output == expected, f"Expected: {expected}, Got: {output}"

# Load the spaCy English model

import spacy
nlp = spacy.load("en_core_web_sm")

def find_ent_type(text):
    # Use spaCy to detect NER objects, then replace with Faker-generated values
    print(f"Original text: {text}")
    text = smart_capitalize(text)  # Apply smart capitalization
    doc = nlp(text)
    print(f"Processed text: {text}")
    print("Detected entities:") 
    print(doc) 
    print(doc.ents)
    for ent in doc.ents:
        print(ent.text, ent.label_)

# Run the test
#find_ent_type("Generative AI")
find_ent_type("My name is asif, I am from microsoft, I want to learn generative ai, please help me")

#test_smart_capitalize()
print("Test passed!")




