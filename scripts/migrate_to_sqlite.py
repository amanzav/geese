"""
Migration Script: Convert JSON files to SQLite database
Migrates existing data from file-based storage to geese.db
"""

import json
import sqlite3
import os
from datetime import datetime
from pathlib import Path


class DatabaseMigrator:
    """Migrates existing JSON data to SQLite database"""

    def __init__(self, db_path="data/geese.db", data_dir="data"):
        self.db_path = db_path
        self.data_dir = data_dir
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to SQLite database and create tables"""
        print(f"📦 Connecting to database: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Execute schema
        schema_path = os.path.join(self.data_dir, "schema.sql")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        print(f"📋 Creating tables from schema...")
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
            self.cursor.executescript(schema_sql)
        
        self.conn.commit()
        print("✅ Database initialized\n")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("🔒 Database connection closed")

    def migrate_jobs(self, jobs_file="jobs_scraped.json"):
        """Migrate jobs from jobs_scraped.json to jobs table"""
        jobs_path = os.path.join(self.data_dir, jobs_file)
        
        if not os.path.exists(jobs_path):
            print(f"⚠️  Jobs file not found: {jobs_path}")
            return 0
        
        print(f"📄 Loading jobs from {jobs_file}...")
        with open(jobs_path, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        
        print(f"💾 Migrating {len(jobs)} jobs to database...")
        migrated = 0
        
        for job in jobs:
            try:
                # Extract compensation data
                comp = job.get('compensation', {})
                if isinstance(comp, dict):
                    comp_value = comp.get('value')
                    comp_currency = comp.get('currency')
                    comp_period = comp.get('time_period')
                    comp_raw = comp.get('original_text', 'N/A')
                else:
                    # Fallback if compensation is not structured
                    comp_value = None
                    comp_currency = None
                    comp_period = None
                    comp_raw = str(comp) if comp else 'N/A'
                
                # Get current timestamp
                now = datetime.now().isoformat()
                
                self.cursor.execute('''
                    INSERT OR REPLACE INTO jobs (
                        job_id, title, company, division, location, level,
                        openings, applications, chances, deadline,
                        summary, responsibilities, skills, additional_info,
                        employment_location_arrangement, work_term_duration,
                        compensation_value, compensation_currency, compensation_period, compensation_raw,
                        scraped_at, updated_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job.get('id', ''),
                    job.get('title', ''),
                    job.get('company', ''),
                    job.get('division', 'N/A'),
                    job.get('location', ''),
                    job.get('level', ''),
                    int(job.get('openings', 0)),
                    int(job.get('applications', 0)),
                    float(job.get('chances', 0.0)),
                    job.get('deadline', ''),
                    job.get('summary', 'N/A'),
                    job.get('responsibilities', 'N/A'),
                    job.get('skills', 'N/A'),
                    job.get('additional_info', 'N/A'),
                    job.get('employment_location_arrangement', 'N/A'),
                    job.get('work_term_duration', 'N/A'),
                    comp_value,
                    comp_currency,
                    comp_period,
                    comp_raw,
                    now,
                    now,
                    1
                ))
                migrated += 1
            except Exception as e:
                print(f"  ⚠️  Error migrating job {job.get('id', 'unknown')}: {e}")
        
        self.conn.commit()
        print(f"✅ Migrated {migrated}/{len(jobs)} jobs\n")
        return migrated

    def migrate_matches(self, matches_file="job_matches_cache.json"):
        """Migrate match results from job_matches_cache.json to job_matches table"""
        matches_path = os.path.join(self.data_dir, matches_file)
        
        if not os.path.exists(matches_path):
            print(f"⚠️  Matches file not found: {matches_path}")
            return 0
        
        print(f"📄 Loading matches from {matches_file}...")
        with open(matches_path, 'r', encoding='utf-8') as f:
            matches = json.load(f)
        
        print(f"💾 Migrating {len(matches)} match results to database...")
        migrated = 0
        
        for job_id, match_data in matches.items():
            try:
                # Get current timestamp
                now = datetime.now().isoformat()
                
                # Extract match details
                scores = match_data.get('scores', {})
                
                self.cursor.execute('''
                    INSERT OR REPLACE INTO job_matches (
                        job_id, match_score, decision,
                        semantic_score, keyword_score, compensation_score, 
                        experience_score, location_score,
                        matched_skills, missing_skills, strengths, concerns, ai_reasoning,
                        technologies, analyzed_at, analysis_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_id,
                    float(match_data.get('match_score', 0.0)),
                    match_data.get('decision', 'skip'),
                    float(scores.get('semantic_score', 0.0)),
                    float(scores.get('keyword_score', 0.0)),
                    float(scores.get('compensation_score', 0.0)),
                    float(scores.get('experience_score', 0.0)),
                    float(scores.get('location_score', 0.0)),
                    json.dumps(match_data.get('matched_skills', [])),
                    json.dumps(match_data.get('missing_skills', [])),
                    json.dumps(match_data.get('strengths', [])),
                    json.dumps(match_data.get('concerns', [])),
                    match_data.get('ai_reasoning', ''),
                    json.dumps(match_data.get('technologies', [])),
                    now,
                    '1.0.0'
                ))
                migrated += 1
            except Exception as e:
                print(f"  ⚠️  Error migrating match for job {job_id}: {e}")
        
        self.conn.commit()
        print(f"✅ Migrated {migrated}/{len(matches)} match results\n")
        return migrated

    def migrate_cover_letters(self, letters_file="uploaded_cover_letters.json"):
        """Migrate cover letters from cover_letters folder (PDF files tracked in JSON)"""
        letters_path = os.path.join(self.data_dir, letters_file)
        cover_letters_dir = "cover_letters"
        
        if not os.path.exists(letters_path):
            print(f"⚠️  Cover letters tracking file not found: {letters_path}")
            return 0
        
        if not os.path.exists(cover_letters_dir):
            print(f"⚠️  Cover letters folder not found: {cover_letters_dir}")
            return 0
        
        print(f"� Loading uploaded cover letters list from {letters_file}...")
        with open(letters_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        uploaded_files = data.get('uploaded_files', [])
        print(f"💾 Processing {len(uploaded_files)} uploaded cover letters...")
        migrated = 0
        
        for filename in uploaded_files:
            try:
                # Extract job info from filename (Company_Title.pdf)
                # Remove .pdf extension
                base_name = filename.replace('.pdf', '').replace('.docx', '')
                
                # Parse company and title from filename
                # Format: Company_Name_Job_Title.pdf
                parts = base_name.split('_')
                if len(parts) < 2:
                    print(f"  ⚠️  Skipping invalid filename: {filename}")
                    continue
                
                # For now, we can't reliably extract job_id from filename
                # So we'll skip migration of cover letters for now
                # They'll be regenerated when needed
                
                # Note: We could scan jobs table to find matching company/title
                # but that's complex and error-prone
                continue
                
            except Exception as e:
                print(f"  ⚠️  Error processing cover letter {filename}: {e}")
        
        self.conn.commit()
        print(f"✅ Processed cover letters (will be regenerated as needed)\n")
        return migrated

    def create_cache_metadata(self):
        """Create initial cache metadata entries"""
        print("📝 Creating cache metadata...")
        
        now = datetime.now().isoformat()
        
        metadata = [
            ('last_migration', now),
            ('embeddings_version', 'all-MiniLM-L6-v2'),
            ('resume_last_parsed', now),
        ]
        
        for key, value in metadata:
            self.cursor.execute('''
                INSERT OR REPLACE INTO cache_metadata (cache_key, cache_value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, now))
        
        self.conn.commit()
        print("✅ Cache metadata created\n")

    def print_summary(self):
        """Print migration summary statistics"""
        print("\n" + "="*60)
        print("📊 MIGRATION SUMMARY")
        print("="*60)
        
        # Count records in each table
        tables = ['jobs', 'job_matches', 'cover_letters', 'applications', 'saved_folders']
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"  {table:20} {count:>6} records")
        
        print("="*60 + "\n")


def main():
    """Run the migration"""
    print("\n🚀 Starting migration to SQLite...\n")
    
    migrator = DatabaseMigrator()
    
    try:
        # Connect and initialize database
        migrator.connect()
        
        # Migrate data
        migrator.migrate_jobs()
        migrator.migrate_matches()
        migrator.migrate_cover_letters()
        migrator.create_cache_metadata()
        
        # Print summary
        migrator.print_summary()
        
        print("🎉 Migration completed successfully!")
        print(f"📦 Database created at: {migrator.db_path}\n")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        migrator.close()


if __name__ == "__main__":
    main()
