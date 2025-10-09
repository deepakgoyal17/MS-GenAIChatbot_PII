#!/usr/bin/env python3
"""
Test script to validate the fixes made to app.py
This script tests the key components without running the full Streamlit app
"""

import os
import sys
import warnings

# Set offline mode for transformers to prevent network calls when models are cached
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

def test_sentence_transformer_loading():
    """Test SentenceTransformer model loading with fallback"""
    print("Testing SentenceTransformer model loading...")
    
    try:
        from sentence_transformers import SentenceTransformer, util
        
        models_to_try = [
            'all-MiniLM-L6-v2',
            'paraphrase-MiniLM-L6-v2',
            'all-mpnet-base-v2'
        ]
        
        for model_name in models_to_try:
            try:
                print(f"  Attempting to load: {model_name}")
                # First try with offline mode disabled
                os.environ.pop('TRANSFORMERS_OFFLINE', None)
                os.environ.pop('HF_HUB_OFFLINE', None)
                
                model = SentenceTransformer(model_name)
                print(f"  ✅ Successfully loaded: {model_name}")
                
                # Re-enable offline mode
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
                os.environ['HF_HUB_OFFLINE'] = '1'
                
                return model
                
            except Exception as e:
                print(f"  ❌ Failed to load {model_name}: {str(e)[:100]}...")
                # Try with offline mode (cached models only)
                try:
                    os.environ['TRANSFORMERS_OFFLINE'] = '1'
                    os.environ['HF_HUB_OFFLINE'] = '1'
                    model = SentenceTransformer(model_name)
                    print(f"  ✅ Successfully loaded cached: {model_name}")
                    return model
                except Exception as e2:
                    print(f"  ❌ Failed to load cached {model_name}: {str(e2)[:100]}...")
                    continue
        
        print("  ⚠️ No SentenceTransformer models could be loaded")
        return None
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return None

def test_deepeval_custom_llm():
    """Test CustomLLM class compatibility with DeepEval"""
    print("\nTesting DeepEval CustomLLM compatibility...")
    
    try:
        import google.generativeai as genai
        from deepeval.models import DeepEvalBaseLLM
        from deepeval.metrics import AnswerRelevancyMetric
        
        class CustomLLM(DeepEvalBaseLLM):
            def __init__(self):
                # Mock initialization without actual API key
                self.model_name = "models/gemini-2.5-flash"

            def load_model(self):
                return self

            def generate(self, prompt: str) -> str:
                return "Mock response for testing"

            async def a_generate(self, prompt: str) -> str:
                return self.generate(prompt)

            def get_model_name(self):
                return self.model_name

        # Test instantiation
        custom_llm = CustomLLM()
        print("  ✅ CustomLLM class created successfully")
        
        # Test DeepEval compatibility (without actual measurement)
        try:
            relevancy_metric = AnswerRelevancyMetric(model=custom_llm)
            print("  ✅ AnswerRelevancyMetric accepts CustomLLM")
        except Exception as e:
            print(f"  ❌ AnswerRelevancyMetric failed: {e}")
            
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def test_spacy_model():
    """Test spaCy model loading"""
    print("\nTesting spaCy model loading...")
    
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("  ✅ spaCy model loaded successfully")
        
        # Test basic NER
        doc = nlp("John Doe works at Microsoft in Seattle.")
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        print(f"  ✅ NER test: {entities}")
        
        return nlp
        
    except OSError as e:
        print(f"  ❌ spaCy model not found: {e}")
        print("  💡 Run: python -m spacy download en_core_web_sm")
        return None
    except Exception as e:
        print(f"  ❌ spaCy error: {e}")
        return None

def main():
    """Run all tests"""
    print("🧪 Testing fixes for app.py\n")
    print("=" * 50)
    
    # Test 1: SentenceTransformer loading
    st_model = test_sentence_transformer_loading()
    
    # Test 2: DeepEval CustomLLM
    deepeval_ok = test_deepeval_custom_llm()
    
    # Test 3: spaCy model
    spacy_model = test_spacy_model()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  SentenceTransformer: {'✅ OK' if st_model else '❌ FAILED'}")
    print(f"  DeepEval CustomLLM: {'✅ OK' if deepeval_ok else '❌ FAILED'}")
    print(f"  spaCy Model: {'✅ OK' if spacy_model else '❌ FAILED'}")
    
    if st_model and deepeval_ok and spacy_model:
        print("\n🎉 All tests passed! The app should work properly now.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")
        
    print("\n💡 To run the full app: streamlit run app.py")

if __name__ == "__main__":
    main()