#!/usr/bin/env python3
"""
Test script to debug DeepEval relevance score issues
"""

import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai
from deepeval.models import DeepEvalBaseLLM
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

# Load environment variables
load_dotenv()

class TestCustomLLM(DeepEvalBaseLLM):
    def __init__(self):
        self.model_name = "models/gemini-2.5-flash"
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the Gemini model"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print("✅ CustomLLM initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize CustomLLM: {e}")
            raise e

    def generate(self, prompt: str) -> str:
        try:
            print(f"🔄 Generating response for prompt: {prompt[:50]}...")
            response = self.model.generate_content(prompt)
            if response and response.text:
                result = response.text.strip()
                print(f"✅ Generated response: {result[:50]}...")
                return result
            else:
                print("⚠️ Empty response from Gemini model")
                return "No response generated"
        except Exception as e:
            print(f"❌ Error generating content: {e}")
            return f"Error: {str(e)}"

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return self.model_name

def test_deepeval_relevancy():
    """Test DeepEval relevancy measurement"""
    print("🧪 Testing DeepEval Relevancy Measurement")
    print("=" * 50)
    
    try:
        # Initialize CustomLLM
        print("1. Initializing CustomLLM...")
        custom_llm = TestCustomLLM()
        
        # Test basic generation
        print("\n2. Testing basic generation...")
        test_prompt = "What is the capital of France?"
        test_response = custom_llm.generate(test_prompt)
        print(f"   Prompt: {test_prompt}")
        print(f"   Response: {test_response}")
        
        # Test DeepEval metric
        print("\n3. Testing DeepEval AnswerRelevancyMetric...")
        
        # Simple test case
        question = "What is the capital of France?"
        answer = "The capital of France is Paris."
        
        print(f"   Question: {question}")
        print(f"   Answer: {answer}")
        
        # Create metric
        relevancy_metric = AnswerRelevancyMetric(model=custom_llm)
        print("   ✅ AnswerRelevancyMetric created successfully")
        
        # Create LLMTestCase and measure relevancy
        print("   🔄 Creating LLMTestCase...")
        test_case = LLMTestCase(
            input=question,
            actual_output=answer
        )
        
        print("   🔄 Measuring relevancy...")
        relevancy_metric.measure(test_case)
        
        score = relevancy_metric.score
        print(f"   📊 Relevancy Score: {score}")
        
        # Check if there's additional information
        if hasattr(relevancy_metric, 'reason'):
            print(f"   📝 Reason: {relevancy_metric.reason}")
        
        if hasattr(relevancy_metric, 'success'):
            print(f"   ✅ Success: {relevancy_metric.success}")
        
        # Test with different examples
        print("\n4. Testing with different examples...")
        
        test_cases = [
            {
                "question": "How do I bake a chocolate cake?",
                "answer": "To bake a chocolate cake, you need flour, sugar, cocoa powder, eggs, and butter. Mix the ingredients and bake at 350°F for 30 minutes."
            },
            {
                "question": "What is machine learning?",
                "answer": "Machine learning is a subset of artificial intelligence that enables computers to learn and make decisions from data without being explicitly programmed."
            },
            {
                "question": "What's the weather like?",
                "answer": "I don't have access to current weather information."
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test Case {i}:")
            print(f"   Question: {test_case['question']}")
            print(f"   Answer: {test_case['answer']}")
            
            try:
                metric = AnswerRelevancyMetric(model=custom_llm)
                test_case_obj = LLMTestCase(
                    input=test_case['question'],
                    actual_output=test_case['answer']
                )
                metric.measure(test_case_obj)
                print(f"   Score: {metric.score}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 DeepEval test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

def check_environment():
    """Check if all required components are available"""
    print("🔍 Checking Environment")
    print("=" * 30)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("✅ GOOGLE_API_KEY found")
    else:
        print("❌ GOOGLE_API_KEY not found")
        print("   Please add your Google API key to the .env file")
        return False
    
    # Check imports
    try:
        import google.generativeai as genai
        print("✅ google.generativeai imported")
    except ImportError:
        print("❌ google.generativeai not available")
        return False
    
    try:
        from deepeval.models import DeepEvalBaseLLM
        from deepeval.metrics import AnswerRelevancyMetric
        print("✅ deepeval imported")
    except ImportError:
        print("❌ deepeval not available")
        print("   Install with: pip install deepeval")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 DeepEval Debugging Script")
    print("=" * 40)
    
    if check_environment():
        print("\n")
        test_deepeval_relevancy()
    else:
        print("\n❌ Environment check failed. Please fix the issues above.")
        sys.exit(1)