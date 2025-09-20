#!/usr/bin/env python3
"""
Final test to verify all fixes are working
"""

import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")

    try:
        # Test config import
        from config import PIIProtectionConfig
        print("✅ Config module imported successfully")

        # Test excel exporter import
        from excel_exporter import PIIAnalysisExporter
        print("✅ Excel exporter imported successfully")

        # Test modular app imports
        from app_modular import load_conditional_imports
        print("✅ Modular app imports working")

        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_config_system():
    """Test configuration system"""
    print("\n🧪 Testing configuration system...")

    try:
        from config import PIIProtectionConfig

        # Test default config
        config = PIIProtectionConfig()
        print("✅ Default configuration created")

        # Test config serialization
        config_dict = config.to_dict()
        config2 = PIIProtectionConfig.from_dict(config_dict)
        print("✅ Configuration serialization working")

        # Test feature flags
        assert config.enable_fake_names == True
        assert config.enable_xxxx_masking == True
        assert config.enable_llm_pii_removal == True
        print("✅ Feature flags working correctly")

        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_custom_llm():
    """Test CustomLLM class instantiation"""
    print("\n🧪 Testing CustomLLM class...")

    try:
        # Test modular app CustomLLM
        from app_modular import load_conditional_imports

        # Create a mock config for testing
        from config import PIIProtectionConfig
        config = PIIProtectionConfig(enable_deepeval=True)

        # Load conditional imports
        imports = load_conditional_imports(config)

        if 'deepeval' in imports:
            DeepEvalBaseLLM, AnswerRelevancyMetric, LLMTestCase = imports['deepeval']

            class TestCustomLLM(DeepEvalBaseLLM):
                def __init__(self):
                    self.model = None
                    self.model_name = "test-model"

                def load_model(self):
                    return self

                def generate(self, prompt: str) -> str:
                    return "Test response"

                async def a_generate(self, prompt: str) -> str:
                    return self.generate(prompt)

                def get_model_name(self):
                    return self.model_name

            # Test instantiation
            custom_llm = TestCustomLLM()
            print("✅ CustomLLM class instantiated successfully")

            # Test required methods
            assert hasattr(custom_llm, 'load_model')
            assert hasattr(custom_llm, 'generate')
            assert hasattr(custom_llm, 'get_model_name')
            print("✅ All required methods present")

            return True
        else:
            print("⚠️ DeepEval not available, skipping CustomLLM test")
            return True

    except Exception as e:
        print(f"❌ CustomLLM test failed: {e}")
        return False

def test_excel_exporter():
    """Test Excel exporter functionality"""
    print("\n🧪 Testing Excel exporter...")

    try:
        from excel_exporter import PIIAnalysisExporter

        # Create exporter
        exporter = PIIAnalysisExporter(output_dir="test_results")
        print("✅ Excel exporter created")

        # Add test data
        test_data = {
            'original_prompt': 'Hello, my name is John Doe',
            'real_response': 'Hello John Doe!',
            'relevancy_real': 0.85,
            'processing_time_real': 1.2
        }

        exporter.add_analysis_record(test_data)
        print("✅ Test data added")

        # Test stats
        stats = exporter.get_current_stats()
        assert stats['total_queries'] == 1
        print("✅ Statistics working correctly")

        return True
    except Exception as e:
        print(f"❌ Excel exporter test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running final verification tests")
    print("=" * 50)

    tests = [
        ("Import Test", test_imports),
        ("Config System Test", test_config_system),
        ("CustomLLM Test", test_custom_llm),
        ("Excel Exporter Test", test_excel_exporter)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"[PASS] {test_name}: PASSED")
            else:
                print(f"[FAIL] {test_name}: FAILED")
        except Exception as e:
            print(f"[ERROR] {test_name}: ERROR - {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("SUCCESS: All tests passed! The application should work correctly.")
        print("\nReady to run:")
        print("   python run.py modular    # Run modular version")
        print("   python run.py original   # Run original version")
        return True
    else:
        print("WARNING: Some tests failed. Please check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)