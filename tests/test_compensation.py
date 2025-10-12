"""
Test Compensation Extraction
Tests the LLM-based compensation extraction with various input formats
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.llm_assistant import CompensationExtractor


def test_compensation_extraction():
    """Test compensation extraction with various formats"""
    
    print("🧪 Testing Compensation Extraction\n")
    print("=" * 70)
    
    # Test cases covering different scenarios
    test_cases = [
        # Range with explicit highest
        ("Pay Rate: $ 25.00 - $35.00 per hour depending on experience", 35.0, "CAD", "hourly"),
        
        # Single value with currency
        ("Compensation: $30/hour CAD", 30.0, "CAD", "hourly"),
        
        # USD currency
        ("Salary: $25-30/hour USD", 30.0, "USD", "hourly"),
        
        # Yearly salary
        ("Annual salary: $60,000 - $75,000", 75000.0, "CAD", "yearly"),
        
        # Monthly
        ("Monthly stipend: $3000-$4000 CAD", 4000.0, "CAD", "monthly"),
        
        # TBD/Unknown cases
        ("Compensation will be discussed during interview", None, None, None),
        ("TBD", None, None, None),
        ("Competitive compensation package", None, None, None),
        ("To be determined based on experience", None, None, None),
        
        # Edge cases
        ("$40/hr", 40.0, "CAD", "hourly"),
        ("20-25 per hour", 25.0, "CAD", "hourly"),
    ]
    
    try:
        # Initialize extractor (will use GEMINI_API_KEY from .env)
        extractor = CompensationExtractor(provider="gemini")
        
        passed = 0
        failed = 0
        
        for i, (text, expected_value, expected_currency, expected_period) in enumerate(test_cases, 1):
            print(f"\nTest {i}:")
            print(f"Input: '{text}'")
            
            result = extractor.extract_compensation(text)
            
            print(f"Result: {extractor.format_compensation(result)}")
            print(f"  Value: {result['value']}")
            print(f"  Currency: {result['currency']}")
            print(f"  Period: {result['time_period']}")
            
            # Check if result matches expectations
            value_match = result['value'] == expected_value
            currency_match = result['currency'] == expected_currency
            period_match = result['time_period'] == expected_period
            
            if value_match and currency_match and period_match:
                print("  ✅ PASS")
                passed += 1
            else:
                print(f"  ❌ FAIL")
                print(f"     Expected: value={expected_value}, currency={expected_currency}, period={expected_period}")
                failed += 1
        
        print("\n" + "=" * 70)
        print(f"\n📊 Test Results:")
        print(f"   ✅ Passed: {passed}/{len(test_cases)}")
        print(f"   ❌ Failed: {failed}/{len(test_cases)}")
        print(f"   📈 Success Rate: {(passed/len(test_cases))*100:.1f}%")
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        print("\nMake sure:")
        print("  1. You have a .env file with GEMINI_API_KEY")
        print("  2. google-generativeai is installed: pip install google-generativeai")
        print("  3. Your API key is valid")
        return False
    
    return failed == 0


if __name__ == "__main__":
    success = test_compensation_extraction()
    sys.exit(0 if success else 1)
