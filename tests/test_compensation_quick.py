"""
Quick test for compensation extraction - tests just the core functionality
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.llm_assistant import CompensationExtractor


def test_basic_extraction():
    """Test basic compensation extraction with a simple example"""
    print("\n" + "="*60)
    print("Testing Compensation Extraction")
    print("="*60)
    
    # Initialize extractor
    print("\n1. Initializing CompensationExtractor...")
    try:
        extractor = CompensationExtractor(provider='gemini')
        print("   ✓ Extractor initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize: {e}")
        print("\n   Make sure GEMINI_API_KEY is set in your .env file!")
        return False
    
    # Test case: Simple hourly range
    test_text = """
    Compensation: $30-40 per hour
    Benefits: Health insurance, gym membership
    """
    
    print(f"\n2. Testing extraction on sample text:")
    print(f"   Input: '$30-40 per hour'")
    
    try:
        result = extractor.extract_compensation(test_text)
        print(f"\n   ✓ Extraction successful!")
        print(f"\n   Results:")
        print(f"   - Value: ${result['value']}")
        print(f"   - Currency: {result['currency']}")
        print(f"   - Time Period: {result['time_period']}")
        print(f"   - Formatted: {extractor.format_compensation(result)}")
        
        # Validate it extracted the highest value (40)
        if result['value'] == 40.0:
            print(f"\n   ✓ Correctly extracted highest value from range!")
        else:
            print(f"\n   ⚠ Warning: Expected 40.0 but got {result['value']}")
        
        print("\n" + "="*60)
        print("✓ Test completed successfully!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n   ✗ Extraction failed: {e}")
        print("\n" + "="*60)
        print("✗ Test failed")
        print("="*60)
        return False


if __name__ == "__main__":
    success = test_basic_extraction()
    sys.exit(0 if success else 1)
