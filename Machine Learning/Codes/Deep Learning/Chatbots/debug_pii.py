#!/usr/bin/env python3
"""
Debug script for PII replacement functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import PIIProtectionConfig
from app_modular import load_conditional_imports, fake_ner_replace, mask_ner_with_xxxx

def test_pii_replacement():
    """Test PII replacement functions"""

    # Create config with PII features enabled
    config = PIIProtectionConfig()
    config.enable_fake_names = True
    config.enable_xxxx_masking = True

    print("Config created:")
    print(f"  enable_fake_names: {config.enable_fake_names}")
    print(f"  enable_xxxx_masking: {config.enable_xxxx_masking}")

    # Load imports
    imports = load_conditional_imports(config)
    print(f"\nImports loaded: {list(imports.keys())}")

    # Load spaCy model
    if 'spacy' in imports:
        try:
            nlp = imports['spacy'].load("en_core_web_sm")
            print("spaCy model loaded successfully")
        except OSError:
            print("spaCy model not available")
            return
    else:
        print("spaCy not in imports")
        return

    # Test text
    test_text = "My name is John Doe and I work at Microsoft. Contact me at john.doe@email.com or (555) 123-4567."
    print(f"\nTest text: {test_text}")

    # Test fake NER replacement
    print("\nTesting fake NER replacement...")
    fake_text, ner_map = fake_ner_replace(test_text, nlp, config, imports)
    print(f"Fake text: {fake_text}")
    print(f"NER map: {ner_map}")

    # Test XXXX masking
    print("\nTesting XXXX masking...")
    masked_text, mask_map = mask_ner_with_xxxx(test_text, nlp, config, imports)
    print(f"Masked text: {masked_text}")
    print(f"Mask map: {mask_map}")

if __name__ == "__main__":
    test_pii_replacement()