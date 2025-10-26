#!/usr/bin/env python3
"""
Sync Uploaded Cover Letters
Marks all existing cover letters as "already uploaded" to prevent re-uploading
IMPORTANT: Only marks old files. Newly created files (from today) are excluded.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

def sync_uploaded_covers(max_age_minutes=30):
    """
    Mark existing cover letters as uploaded, excluding recently created ones
    
    Args:
        max_age_minutes: Files modified within this many minutes are considered "new"
                        and won't be marked as uploaded (default: 30 minutes)
    """
    
    print("\n" + "=" * 70)
    print("📋 SYNCING UPLOADED COVER LETTERS")
    print("=" * 70 + "\n")
    
    # Get all PDF files
    cover_letters_dir = Path("cover_letters")
    if not cover_letters_dir.exists():
        print("❌ Error: cover_letters/ directory not found")
        return
    
    pdf_files = list(cover_letters_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("⚠️  No cover letters found in cover_letters/ directory")
        return
    
    print(f"📄 Found {len(pdf_files)} cover letter PDFs")
    print(f"⏰ Excluding files created/modified in last {max_age_minutes} minutes")
    print()
    
    # Calculate cutoff time
    cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
    
    # Separate old vs new files
    old_files = []
    new_files = []
    
    for pdf_path in pdf_files:
        modified_time = datetime.fromtimestamp(pdf_path.stat().st_mtime)
        if modified_time < cutoff_time:
            old_files.append(pdf_path.name)
        else:
            new_files.append((pdf_path.name, modified_time))
    
    print(f"📦 Old files (will mark as uploaded): {len(old_files)}")
    print(f"✨ New files (will skip, need upload): {len(new_files)}")
    print()
    
    if new_files:
        print(f"🆕 Recently created files (NOT marking as uploaded):")
        for filename, mod_time in sorted(new_files, key=lambda x: x[1], reverse=True)[:10]:
            time_str = mod_time.strftime("%H:%M:%S")
            print(f"   • {filename} (created at {time_str})")
        if len(new_files) > 10:
            print(f"   ... and {len(new_files) - 10} more")
        print()
    
    # Load existing tracking file
    log_file = Path("data") / "uploaded_cover_letters.json"
    uploaded_files = set()
    
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            uploaded_files = set(data.get("uploaded_files", []))
        print(f"📂 Loaded {len(uploaded_files)} already tracked uploads")
    else:
        print("📂 No existing upload tracking file found")
    
    # Add only OLD files to the tracking set
    newly_tracked = []
    for filename in old_files:
        if filename not in uploaded_files:
            newly_tracked.append(filename)
            uploaded_files.add(filename)
    
    # Save updated tracking file
    log_file.parent.mkdir(exist_ok=True)
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({"uploaded_files": sorted(list(uploaded_files))}, f, indent=2)
    
    print()
    print("=" * 70)
    print("✅ SYNC COMPLETE")
    print("=" * 70)
    print(f"Total cover letters tracked: {len(uploaded_files)}")
    print(f"Newly added to tracking: {len(newly_tracked)}")
    print(f"Already tracked: {len(uploaded_files) - len(newly_tracked)}")
    print(f"🆕 Recently created (NOT tracked): {len(new_files)}")
    print()
    
    if newly_tracked:
        print(f"📝 Newly tracked files ({len(newly_tracked)}):")
        for filename in sorted(newly_tracked)[:10]:  # Show first 10
            print(f"   • {filename}")
        if len(newly_tracked) > 10:
            print(f"   ... and {len(newly_tracked) - 10} more")
        print()
    
    print("✅ Old cover letters marked as uploaded!")
    print(f"🆕 {len(new_files)} recent files left unmarked for upload")
    print()
    print("   Next time you run `python main.py --mode upload-covers`,")
    print("   it will upload the recent files and skip the old ones.")
    print()

if __name__ == "__main__":
    sync_uploaded_covers()
