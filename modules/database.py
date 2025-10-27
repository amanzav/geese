"""
Database Module for WaterlooWorks Automator
Handles all SQLite database operations
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from contextlib import contextmanager


# Schema version - increment this when making schema changes
CURRENT_SCHEMA_VERSION = 1


class Database:
    """SQLite database manager for WaterlooWorks Automator"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            from .config import load_app_config
            config = load_app_config()
            db_path = config.get("paths", {}).get("database_path", "data/geese.db")
        self.db_path = db_path
        self._ensure_db_exists()
        self._check_and_migrate_schema()

    def _ensure_db_exists(self):
        """Initialize database if it doesn't exist"""
        db_file = Path(self.db_path)
        if not db_file.exists():
            print(f"📦 Database not found. Initializing new database at {self.db_path}...")
            self._initialize_schema()
            print(f"✅ Database initialized successfully!")
    
    def _initialize_schema(self):
        """Create database schema from schema.sql"""
        # Create data directory if it doesn't exist
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Read schema file
        schema_path = Path(__file__).parent.parent / "data" / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found at {schema_path}. "
                "Cannot initialize database without schema."
            )
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()
        
        # Execute schema
        with self.get_connection() as conn:
            conn.executescript(schema)
        
        # Set initial schema version
        self.set_schema_version(CURRENT_SCHEMA_VERSION)
    
    def _check_and_migrate_schema(self):
        """Check schema version and apply migrations if needed"""
        current_version = self.get_schema_version()
        
        if current_version < CURRENT_SCHEMA_VERSION:
            print(f"📦 Database schema outdated (v{current_version}). Upgrading to v{CURRENT_SCHEMA_VERSION}...")
            self._apply_migrations(current_version)
            print(f"✅ Database upgraded successfully!")
        elif current_version > CURRENT_SCHEMA_VERSION:
            raise RuntimeError(
                f"Database schema version (v{current_version}) is newer than application version (v{CURRENT_SCHEMA_VERSION}). "
                "Please update the application."
            )
    
    def get_schema_version(self) -> int:
        """Get current database schema version"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT cache_value FROM cache_metadata WHERE cache_key = 'schema_version'")
                result = cursor.fetchone()
                return int(result[0]) if result else 0
        except sqlite3.OperationalError:
            # Table doesn't exist yet (very first run)
            return 0
    
    def set_schema_version(self, version: int):
        """Set database schema version"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO cache_metadata (cache_key, cache_value, updated_at)
                VALUES ('schema_version', ?, ?)
            ''', (str(version), datetime.now().isoformat()))
    
    def _apply_migrations(self, from_version: int):
        """Apply incremental schema migrations"""
        # Apply migrations sequentially
        for version in range(from_version + 1, CURRENT_SCHEMA_VERSION + 1):
            print(f"   Applying migration: v{version-1} → v{version}")
            
            if version == 1:
                # Migration to v1 (initial schema)
                # This shouldn't be needed since _initialize_schema handles it
                pass
            
            # Future migrations go here:
            # elif version == 2:
            #     with self.get_connection() as conn:
            #         conn.execute("ALTER TABLE jobs ADD COLUMN new_field TEXT")
            #     self.set_schema_version(2)
            
            # Update version after each migration
            self.set_schema_version(version)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ========================================================================
    # JOBS TABLE OPERATIONS
    # ========================================================================

    def insert_job(self, job_data: Dict[str, Any]) -> bool:
        """Insert or update a job in the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Extract compensation
                comp = job_data.get('compensation', {})
                if isinstance(comp, dict):
                    comp_value = comp.get('value')
                    comp_currency = comp.get('currency')
                    comp_period = comp.get('time_period')
                    comp_raw = comp.get('original_text', 'N/A')
                else:
                    comp_value = None
                    comp_currency = None
                    comp_period = None
                    comp_raw = str(comp) if comp else 'N/A'
                
                now = datetime.now().isoformat()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO jobs (
                        job_id, title, company, division, location, level,
                        openings, applications, chances, deadline,
                        summary, responsibilities, skills, additional_info,
                        employment_location_arrangement, work_term_duration,
                        compensation_value, compensation_currency, compensation_period, compensation_raw,
                        scraped_at, updated_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job_data.get('id'),
                    job_data.get('title'),
                    job_data.get('company'),
                    job_data.get('division', 'N/A'),
                    job_data.get('location'),
                    job_data.get('level'),
                    int(job_data.get('openings', 0)),
                    int(job_data.get('applications', 0)),
                    float(job_data.get('chances', 0.0)),
                    job_data.get('deadline'),
                    job_data.get('summary', 'N/A'),
                    job_data.get('responsibilities', 'N/A'),
                    job_data.get('skills', 'N/A'),
                    job_data.get('additional_info', 'N/A'),
                    job_data.get('employment_location_arrangement', 'N/A'),
                    job_data.get('work_term_duration', 'N/A'),
                    comp_value,
                    comp_currency,
                    comp_period,
                    comp_raw,
                    now,
                    now,
                    1
                ))
                return True
        except Exception as e:
            print(f"❌ Error inserting job {job_data.get('id')}: {e}")
            return False

    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get a single job by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_jobs(self, active_only: bool = True) -> List[Dict]:
        """Get all jobs from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if active_only:
                cursor.execute('SELECT * FROM jobs WHERE is_active = 1')
            else:
                cursor.execute('SELECT * FROM jobs')
            return [dict(row) for row in cursor.fetchall()]

    def get_jobs_dict(self) -> Dict[str, Dict]:
        """Get all jobs as dictionary (for backwards compatibility)"""
        jobs = self.get_all_jobs()
        return {job['job_id']: job for job in jobs}

    # ========================================================================
    # JOB MATCHES TABLE OPERATIONS
    # ========================================================================

    def insert_match(self, job_id: str, match_data: Dict[str, Any]) -> bool:
        """Insert or update a match result"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                scores = match_data.get('scores', {})
                now = datetime.now().isoformat()
                
                cursor.execute('''
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
                return True
        except Exception as e:
            print(f"❌ Error inserting match for job {job_id}: {e}")
            return False

    def get_match(self, job_id: str) -> Optional[Dict]:
        """Get match result for a job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM job_matches WHERE job_id = ?', (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            # Convert back to dict and parse JSON fields
            match = dict(row)
            match['matched_skills'] = json.loads(match['matched_skills'])
            match['missing_skills'] = json.loads(match['missing_skills'])
            match['strengths'] = json.loads(match['strengths'])
            match['concerns'] = json.loads(match['concerns'])
            match['technologies'] = json.loads(match['technologies'])
            
            # Reconstruct scores dict for backwards compatibility
            match['scores'] = {
                'semantic_score': match['semantic_score'],
                'keyword_score': match['keyword_score'],
                'compensation_score': match['compensation_score'],
                'experience_score': match['experience_score'],
                'location_score': match['location_score']
            }
            
            return match

    def get_all_matches(self) -> Dict[str, Dict]:
        """Get all match results as dictionary (for backwards compatibility)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM job_matches')
            
            matches = {}
            for row in cursor.fetchall():
                match = dict(row)
                job_id = match['job_id']
                
                # Parse JSON fields
                match['matched_skills'] = json.loads(match['matched_skills'])
                match['missing_skills'] = json.loads(match['missing_skills'])
                match['strengths'] = json.loads(match['strengths'])
                match['concerns'] = json.loads(match['concerns'])
                match['technologies'] = json.loads(match['technologies'])
                
                # Reconstruct scores dict
                match['scores'] = {
                    'semantic_score': match['semantic_score'],
                    'keyword_score': match['keyword_score'],
                    'compensation_score': match['compensation_score'],
                    'experience_score': match['experience_score'],
                    'location_score': match['location_score']
                }
                
                matches[job_id] = match
            
            return matches

    def get_top_matches(self, limit: int = 20) -> List[Dict]:
        """Get top matches (decision='apply') ordered by score"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM top_matches
                ORDER BY match_score DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # COVER LETTERS TABLE OPERATIONS
    # ========================================================================

    def insert_cover_letter(self, job_id: str, content: str, file_path: Optional[str] = None,
                           provider: str = "gemini") -> int:
        """Insert a cover letter and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO cover_letters (
                    job_id, content, file_path, generated_at,
                    generation_provider, word_count
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                content,
                file_path,
                now,
                provider,
                len(content.split())
            ))
            return cursor.lastrowid

    def mark_cover_letter_uploaded(self, letter_id: int) -> bool:
        """Mark a cover letter as uploaded"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('''
                    UPDATE cover_letters
                    SET is_uploaded = 1, uploaded_at = ?
                    WHERE letter_id = ?
                ''', (now, letter_id))
                return True
        except Exception as e:
            print(f"❌ Error marking cover letter uploaded: {e}")
            return False

    def get_cover_letter(self, job_id: str) -> Optional[Dict]:
        """Get cover letter for a job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM cover_letters 
                WHERE job_id = ? 
                ORDER BY generated_at DESC 
                LIMIT 1
            ''', (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ========================================================================
    # SAVED FOLDERS TABLE OPERATIONS
    # ========================================================================

    def mark_job_saved(self, job_id: str, folder_name: Optional[str] = None) -> bool:
        """Mark a job as saved to a WaterlooWorks folder"""
        if folder_name is None:
            from .config import load_app_config
            config = load_app_config()
            folder_name = config.get("waterlooworks_folder", "geese")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT OR IGNORE INTO saved_folders (job_id, folder_name, saved_at)
                    VALUES (?, ?, ?)
                ''', (job_id, folder_name, now))
                return True
        except Exception as e:
            print(f"❌ Error marking job saved: {e}")
            return False

    def is_job_saved(self, job_id: str, folder_name: Optional[str] = None) -> bool:
        """Check if job is already saved to folder"""
        if folder_name is None:
            from .config import load_app_config
            config = load_app_config()
            folder_name = config.get("waterlooworks_folder", "geese")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM saved_folders
                WHERE job_id = ? AND folder_name = ?
            ''', (job_id, folder_name))
            count = cursor.fetchone()[0]
            return count > 0

    # ========================================================================
    # CACHE METADATA OPERATIONS
    # ========================================================================

    def set_cache_value(self, key: str, value: str):
        """Set a cache metadata value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT OR REPLACE INTO cache_metadata (cache_key, cache_value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value, now))

    def get_cache_value(self, key: str) -> Optional[str]:
        """Get a cache metadata value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT cache_value FROM cache_metadata WHERE cache_key = ?', (key,))
            row = cursor.fetchone()
            return row[0] if row else None

    # ========================================================================
    # UTILITY OPERATIONS
    # ========================================================================

    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            tables = ['jobs', 'job_matches', 'cover_letters', 'applications', 'saved_folders']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            
            return stats


# Singleton instance
_db_instance = None

def get_db() -> Database:
    """Get or create database singleton instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
