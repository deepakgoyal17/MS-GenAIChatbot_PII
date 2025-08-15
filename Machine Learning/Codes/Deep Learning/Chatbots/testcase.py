from app import setup_name_patterns, smart_capitalize,fake_ner_replace
from base_logger import BaseLogger
import logging

logger = BaseLogger(log_name='testcases_chatbot_app', log_level=logging.INFO, log_dir='logs').get_logger()
logger.info("Chatbot application started")

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

def test_find_ent_type(text):
    # Use spaCy to detect NER objects, then replace with Faker-generated values
    print(f"Original text: {text}")
    text = fake_ner_replace(text)  # Apply smart capitalization
    print(f"Processed text: {text}")
   

def test_fake_ner_replace(text):
    # Use spaCy to detect NER objects, then replace with Faker-generated values
    print(f"Original text: {text}")
    text = fake_ner_replace(text)  # Apply smart capitalization
    print(f"Processed text: {text}")

# Run the test
#find_ent_type("Generative AI")
#test_find_ent_type("My name is asif, I am from microsoft, I want to learn generative ai, please help me")
test_fake_ner_replace("My name is Aaliyah Popova, and I am a jeweler with 13 years of experience. I remember a very unique and challenging project I had to work on last year.")

#test_smart_capitalize()
print("Test passed!")




