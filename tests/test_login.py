"""
Test script for WaterlooWorks authentication
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from modules.auth import WaterlooWorksAuth


def main():
    print("🪿 Geese - Login Test\n")
    
    # Load credentials
    load_dotenv()
    username = os.getenv("WATERLOOWORKS_USERNAME")
    password = os.getenv("WATERLOOWORKS_PASSWORD")
    
    if not username or not password:
        print("❌ ERROR: Add credentials to .env file")
        return
    
    auth = WaterlooWorksAuth(username, password)
    
    try:
        auth.login()
        
        # Keep browser open for 10 seconds
        print("Browser will stay open for 10 seconds...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        auth.close()
        print("✅ Test complete!")


if __name__ == "__main__":
    main()
