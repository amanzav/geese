#!/usr/bin/env python3
"""
Clear All Caches - Fresh Start Script
Clears all cached data to start completely fresh
"""

import os
import shutil
from pathlib import Path

def clear_caches():
    """Clear all cache files and directories"""
    
    print("\n" + "=" * 50)
    print("  CLEARING ALL CACHES - FRESH START")
    print("=" * 50 + "\n")
    
    # Define cache files/directories to clear
    caches = [
        ("data/job_matches_cache.json", "Match results cache"),
        ("embeddings/resume/index.faiss", "Resume embeddings index"),
        ("embeddings/resume/metadata.json", "Resume embeddings metadata"),
        ("data/jobs_scraped.json", "Scraped jobs data"),
    ]
    
    cleared_count = 0
    skipped_count = 0
    
    for file_path, description in caches:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Deleted: {file_path} ({description})")
                cleared_count += 1
            except Exception as e:
                print(f"❌ Error deleting {file_path}: {e}")
        else:
            print(f"⏭️  Skipped: {file_path} (not found)")
            skipped_count += 1
    
    print("\n" + "=" * 50)
    print(f"  ✨ DONE! Cleared {cleared_count} files, skipped {skipped_count}")
    print("=" * 50 + "\n")
    
    print("What happens on next run of main.py:")
    print("  1. Resume embeddings will be rebuilt (with skills!)")
    print("  2. Jobs will be scraped fresh from WaterlooWorks")
    print("  3. All match scores will be recalculated")
    print("  4. New cache will be generated\n")
    
    print("✅ Ready! Run: python main.py\n")

if __name__ == "__main__":
    clear_caches()
