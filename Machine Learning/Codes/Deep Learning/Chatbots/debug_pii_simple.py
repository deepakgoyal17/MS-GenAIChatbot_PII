#!/usr/bin/env python3
"""
Simple debug script for PII replacement functionality
"""

import spacy
from faker import Faker

def test_spacy_ner():
    """Test spaCy NER detection"""

    # Load spaCy model
    try:
        nlp = spacy.load("en_core_web_sm")
        print("spaCy model loaded successfully")
    except OSError:
        print("spaCy model not available")
        return

    # Test text
    test_text = "My name is John Doe and I work at Microsoft. Contact me at john.doe@email.com or (555) 123-4567."
    print(f"\nTest text: {test_text}")

    # Process with spaCy
    doc = nlp(test_text)

    print("\nspaCy entities found:")
    for ent in doc.ents:
        print(f"  {ent.text} -> {ent.label_}")

    # Test Faker
    faker = Faker()
    print("\nFaker samples:")
    print(f"  Name: {faker.name()}")
    print(f"  Company: {faker.company()}")
    print(f"  Email: {faker.email()}")
    print(f"  Phone: {faker.phone_number()}")

if __name__ == "__main__":
    test_spacy_ner()