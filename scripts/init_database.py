"""
Database Initialization Script for Geese

This script initializes a new SQLite database and optionally migrates
existing JSON data from previous versions.

Usage:
    python scripts/init_database.py              # Create fresh database
    python scripts/init_database.py --migrate    # Create + migrate old JSON data
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.database import get_db, CURRENT_SCHEMA_VERSION


def create_fresh_database():
    """Create a fresh database with current schema"""
    print("=" * 70)
    print("🗄️  GEESE DATABASE INITIALIZATION")
    print("=" * 70)
    print()
    
    db_path = Path("data/geese.db")
    
    if db_path.exists():
        response = input(f"⚠️  Database already exists at {db_path}. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("❌ Initialization cancelled.")
            return False
        
        # Backup existing database
        backup_path = db_path.with_suffix('.db.backup')
        import shutil
        shutil.copy(db_path, backup_path)
        print(f"📦 Existing database backed up to: {backup_path}")
        
        # Delete existing database
        db_path.unlink()
        print(f"🗑️  Removed existing database")
    
    print(f"📦 Creating new database at: {db_path}")
    
    # Initialize database (this will auto-create schema)
    db = get_db()
    
    print(f"✅ Database created successfully!")
    print(f"   Schema version: {CURRENT_SCHEMA_VERSION}")
    print()
    
    # Show table stats
    stats = db.get_stats()
    print("📊 Database Structure:")
    for table, count in stats.items():
        print(f"   ✓ {table}: {count} records")
    
    print()
    print("=" * 70)
    print("✅ INITIALIZATION COMPLETE!")
    print("=" * 70)
    
    return True


def migrate_json_data():
    """Migrate old JSON data to SQLite database"""
    print()
    print("=" * 70)
    print("📦 MIGRATING OLD JSON DATA")
    print("=" * 70)
    print()
    
    db = get_db()
    
    # Migrate jobs from jobs_scraped.json
    jobs_json_path = Path("data/jobs_scraped.json")
    if jobs_json_path.exists():
        print(f"📂 Found jobs cache: {jobs_json_path}")
        try:
            with open(jobs_json_path, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
            
            print(f"   Migrating {len(jobs)} jobs...")
            migrated_count = 0
            for job in jobs:
                if db.insert_job(job):
                    migrated_count += 1
            
            print(f"   ✅ Migrated {migrated_count}/{len(jobs)} jobs")
        except Exception as e:
            print(f"   ❌ Error migrating jobs: {e}")
    else:
        print(f"ℹ️  No jobs cache found at {jobs_json_path}")
    
    # Migrate matches from job_matches_cache.json
    matches_json_path = Path("data/job_matches_cache.json")
    if matches_json_path.exists():
        print(f"📂 Found matches cache: {matches_json_path}")
        try:
            with open(matches_json_path, 'r', encoding='utf-8') as f:
                matches = json.load(f)
            
            print(f"   Migrating {len(matches)} match results...")
            migrated_count = 0
            for job_id, match_data in matches.items():
                if db.insert_match(job_id, match_data):
                    migrated_count += 1
            
            print(f"   ✅ Migrated {migrated_count}/{len(matches)} matches")
        except Exception as e:
            print(f"   ❌ Error migrating matches: {e}")
    else:
        print(f"ℹ️  No matches cache found at {matches_json_path}")
    
    print()
    print("=" * 70)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 70)
    print()
    
    # Show final stats
    stats = db.get_stats()
    print("📊 Final Database Statistics:")
    for table, count in stats.items():
        if count > 0:
            print(f"   {table:25} {count:>6} records")
    print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Initialize Geese database and optionally migrate old JSON data"
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Migrate existing JSON data after creating database"
    )
    
    args = parser.parse_args()
    
    # Create fresh database
    success = create_fresh_database()
    
    if not success:
        return
    
    # Migrate old data if requested
    if args.migrate:
        migrate_json_data()
    
    print()
    print("🎉 You're all set! Run 'python main.py' to start using Geese.")
    print()


if __name__ == "__main__":
    main()
