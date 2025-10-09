#!/usr/bin/env python3
"""
Test script for batch processing functionality
"""

import os
import sys
import pandas as pd
from config import PIIProtectionConfig
from excel_exporter import PIIAnalysisExporter
from base_logger import BaseLogger
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_batch_processing():
    """Test batch processing with sample data"""

    # Initialize logger
    logger = BaseLogger(log_name='test_batch', log_level=logging.INFO, log_dir='logs').get_logger()

    # Create test configuration
    config = PIIProtectionConfig()
    config.enable_batch_processing = True
    config.batch_input_file = 'test_batch_input.csv'
    config.batch_text_column = 'text'
    config.batch_max_rows = 2
    config.batch_output_file = 'test_batch_results.xlsx'
    config.batch_background_mode = True

    # Enable some PII methods (but not API-dependent ones for testing)
    config.enable_fake_names = True
    config.enable_xxxx_masking = True
    config.enable_excel_export = True

    # Initialize excel exporter
    excel_exporter = PIIAnalysisExporter(output_dir="analysis_results", logger=logger)

    try:
        # Import and run batch processing
        from app_modular import process_batch_texts
        output_path = process_batch_texts(config, excel_exporter)
        print(f"Batch processing test completed successfully!")
        print(f"Results saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Batch processing test failed: {e}")
        logger.error(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing batch processing functionality...")
    success = test_batch_processing()
    sys.exit(0 if success else 1)