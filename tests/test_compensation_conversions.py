"""
Test compensation conversions to hourly rate
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.llm_assistant import CompensationExtractor


def test_conversions():
    """Test various compensation formats and their conversion to hourly"""
    print("\n" + "="*70)
    print("Testing Compensation Conversions to Hourly Rate")
    print("="*70)
    print("\nAssumptions:")
    print("  - 40 hours per week")
    print("  - 4 weeks per month (160 hours/month)")
    print("  - 52 weeks per year (2,080 hours/year)")
    print("="*70)
    
    # Initialize extractor
    print("\nInitializing CompensationExtractor...")
    try:
        extractor = CompensationExtractor(provider='gemini')
        print("✓ Extractor initialized\n")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        print("\nMake sure GEMINI_API_KEY is set in your .env file!")
        return False
    
    # Test cases
    test_cases = [
        {
            "text": "Salary: $35 per hour",
            "expected_hourly": 35.0,
            "description": "Already hourly"
        },
        {
            "text": "Compensation: $6,400 per month",
            "expected_hourly": 40.0,  # 6400 / (4 * 40) = 40
            "description": "Monthly salary conversion"
        },
        {
            "text": "Annual salary: $83,200",
            "expected_hourly": 40.0,  # 83200 / (52 * 40) = 40
            "description": "Yearly salary conversion"
        },
        {
            "text": "Pay: $25-35/hour",
            "expected_hourly": 35.0,
            "description": "Hourly range (takes highest)"
        },
        {
            "text": "Salary range: $70,000 - $90,000 per year",
            "expected_hourly": 43.27,  # 90000 / (52 * 40) ≈ 43.27
            "description": "Yearly range conversion"
        }
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Input: '{test_case['text']}'")
        
        try:
            result = extractor.extract_compensation(test_case['text'])
            
            if result['value'] is None:
                print(f"   ✗ Failed: No value extracted")
                continue
            
            hourly_rate = result['value']
            formatted = extractor.format_compensation(result)
            
            print(f"   Hourly Rate: ${hourly_rate:.2f}/hour")
            print(f"   Formatted: {formatted}")
            
            # Check if it's close to expected (within $0.10)
            if abs(hourly_rate - test_case['expected_hourly']) < 0.1:
                print(f"   ✓ Correct! (expected ${test_case['expected_hourly']:.2f}/hour)")
                success_count += 1
            else:
                print(f"   ⚠ Warning: Expected ${test_case['expected_hourly']:.2f}/hour")
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    # Summary
    print("\n" + "="*70)
    print(f"Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✓ All conversions working correctly!")
    elif success_count > 0:
        print("⚠ Some conversions need adjustment")
    else:
        print("✗ Conversions not working")
    
    print("="*70)
    return success_count == total_tests


if __name__ == "__main__":
    success = test_conversions()
    sys.exit(0 if success else 1)
