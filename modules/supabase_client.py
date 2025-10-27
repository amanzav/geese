"""
Supabase Client Module
Handles all cloud database operations for job data storage
"""

import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from supabase import create_client, Client
import json


class SupabaseClient:
    """Client for interacting with Supabase cloud database"""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Supabase client
        
        Args:
            url: Supabase project URL (defaults to SUPABASE_URL env var)
            key: Supabase API key (defaults to SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY env var)
        """
        self.url = url or os.getenv('SUPABASE_URL')
        # Try service key first (for scraper), fall back to anon key
        self.key = key or os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        
        if not self.url or not self.key:
            raise ValueError(
                "Supabase credentials not found. "
                "Please set SUPABASE_URL and SUPABASE_SERVICE_KEY (or SUPABASE_ANON_KEY) environment variables "
                "or pass them to the constructor."
            )
        
        self.client: Client = create_client(self.url, self.key)
    
    # ========================================================================
    # JOBS TABLE OPERATIONS
    # ========================================================================
    
    def insert_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Insert or update a job in the cloud database
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse compensation if it's a dict
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
            
            # Parse array fields if they're strings
            app_docs = job_data.get('application_documents_required')
            if isinstance(app_docs, str):
                try:
                    app_docs = json.loads(app_docs) if app_docs and app_docs.strip() else None
                except (json.JSONDecodeError, ValueError):
                    app_docs = None
            elif not isinstance(app_docs, list):
                app_docs = None
            
            degrees = job_data.get('targeted_degrees_disciplines')
            if isinstance(degrees, str):
                try:
                    degrees = json.loads(degrees) if degrees and degrees.strip() else None
                except (json.JSONDecodeError, ValueError):
                    degrees = None
            elif not isinstance(degrees, list):
                degrees = None
            
            # Prepare the job record
            job_record = {
                'job_id': job_data.get('id'),
                'title': job_data.get('title'),
                'company': job_data.get('company'),
                'division': job_data.get('division', 'N/A'),
                'location': job_data.get('location'),
                'level': job_data.get('level'),
                'openings': int(job_data.get('openings', 0)),
                'applications': int(job_data.get('applications', 0)),
                'chances': float(job_data.get('chances', 0.0)),
                'deadline': job_data.get('deadline'),
                'summary': job_data.get('summary', 'N/A'),
                'responsibilities': job_data.get('responsibilities', 'N/A'),
                'skills': job_data.get('skills', 'N/A'),
                'additional_info': job_data.get('additional_info', 'N/A'),
                'employment_location_arrangement': job_data.get('employment_location_arrangement', 'N/A'),
                'work_term_duration': job_data.get('work_term_duration', 'N/A'),
                'application_documents_required': app_docs,
                'targeted_degrees_disciplines': degrees,
                'compensation_value': comp_value,
                'compensation_currency': comp_currency,
                'compensation_period': comp_period,
                'compensation_raw': comp_raw,
                'is_active': True
            }
            
            # Use upsert to insert or update
            response = self.client.table('jobs').upsert(job_record).execute()
            
            return True
        except Exception as e:
            print(f"❌ Error inserting job {job_data.get('id')}: {e}")
            return False
    
    def insert_jobs_batch(self, jobs: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, int]:
        """
        Insert multiple jobs in batches for better performance
        
        Args:
            jobs: List of job dictionaries
            batch_size: Number of jobs to insert per batch
            
        Returns:
            Dictionary with success/failure counts
        """
        total = len(jobs)
        success = 0
        failed = 0
        
        print(f"📤 Uploading {total} jobs to Supabase in batches of {batch_size}...")
        
        for i in range(0, total, batch_size):
            batch = jobs[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            print(f"   Batch {batch_num}/{total_batches} ({len(batch)} jobs)...", end=' ')
            
            for job in batch:
                if self.insert_job(job):
                    success += 1
                else:
                    failed += 1
            
            print(f"✅ Done")
        
        print(f"\n✅ Upload complete: {success} succeeded, {failed} failed")
        return {'success': success, 'failed': failed, 'total': total}
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """
        Fetch a single job by ID
        
        Args:
            job_id: The job ID to fetch
            
        Returns:
            Job dictionary or None if not found
        """
        try:
            response = self.client.table('jobs').select('*').eq('job_id', job_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"❌ Error fetching job {job_id}: {e}")
            return None
    
    def get_jobs_by_ids(self, job_ids: List[str]) -> List[Dict]:
        """
        Fetch multiple jobs by their IDs
        
        Args:
            job_ids: List of job IDs to fetch
            
        Returns:
            List of job dictionaries
        """
        try:
            response = self.client.table('jobs').select('*').in_('job_id', job_ids).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Error fetching jobs: {e}")
            return []
    
    def get_all_active_jobs(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Fetch all active jobs
        
        Args:
            limit: Maximum number of jobs to return (None for all)
            
        Returns:
            List of job dictionaries
        """
        try:
            query = self.client.table('jobs').select('*').eq('is_active', True)
            
            if limit:
                query = query.limit(limit)
            
            response = query.execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"❌ Error fetching active jobs: {e}")
            return []
    
    def search_jobs(self, 
                   company: Optional[str] = None,
                   title: Optional[str] = None,
                   location: Optional[str] = None,
                   min_compensation: Optional[float] = None,
                   required_documents: Optional[List[str]] = None,
                   targeted_degrees: Optional[List[str]] = None,
                   limit: int = 100) -> List[Dict]:
        """
        Search jobs with various filters
        
        Args:
            company: Filter by company name (case-insensitive partial match)
            title: Filter by job title (case-insensitive partial match)
            location: Filter by location (case-insensitive partial match)
            min_compensation: Minimum compensation value
            required_documents: Filter by required documents (must contain all)
            targeted_degrees: Filter by targeted degrees (must contain any)
            limit: Maximum number of results
            
        Returns:
            List of matching job dictionaries
        """
        try:
            query = self.client.table('jobs').select('*').eq('is_active', True)
            
            if company:
                query = query.ilike('company', f'%{company}%')
            
            if title:
                query = query.ilike('title', f'%{title}%')
            
            if location:
                query = query.ilike('location', f'%{location}%')
            
            if min_compensation is not None:
                query = query.gte('compensation_value', min_compensation)
            
            # Note: JSONB filters require special handling in Supabase
            # These may need to be post-filtered in Python
            
            query = query.limit(limit)
            response = query.execute()
            
            jobs = response.data if response.data else []
            
            # Post-filter for JSONB array conditions
            if required_documents:
                jobs = [
                    job for job in jobs
                    if job.get('application_documents_required') and
                    all(doc in job['application_documents_required'] for doc in required_documents)
                ]
            
            if targeted_degrees:
                jobs = [
                    job for job in jobs
                    if job.get('targeted_degrees_disciplines') and
                    any(degree in job['targeted_degrees_disciplines'] for degree in targeted_degrees)
                ]
            
            return jobs
        except Exception as e:
            print(f"❌ Error searching jobs: {e}")
            return []
    
    def deactivate_job(self, job_id: str) -> bool:
        """
        Mark a job as inactive (soft delete)
        
        Args:
            job_id: The job ID to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.client.table('jobs').update({
                'is_active': False
            }).eq('job_id', job_id).execute()
            
            return True
        except Exception as e:
            print(f"❌ Error deactivating job {job_id}: {e}")
            return False
    
    def get_job_count(self, active_only: bool = True) -> int:
        """
        Get total count of jobs
        
        Args:
            active_only: Count only active jobs if True
            
        Returns:
            Number of jobs
        """
        try:
            query = self.client.table('jobs').select('job_id', count='exact')
            
            if active_only:
                query = query.eq('is_active', True)
            
            response = query.execute()
            return response.count if response.count else 0
        except Exception as e:
            print(f"❌ Error getting job count: {e}")
            return 0
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def test_connection(self) -> bool:
        """
        Test the Supabase connection
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to query jobs table (just count)
            response = self.client.table('jobs').select('job_id', count='exact').limit(1).execute()
            print("✅ Supabase connection successful!")
            return True
        except Exception as e:
            print(f"❌ Supabase connection failed: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with various statistics
        """
        try:
            total_jobs = self.get_job_count(active_only=False)
            active_jobs = self.get_job_count(active_only=True)
            
            return {
                'total_jobs': total_jobs,
                'active_jobs': active_jobs,
                'inactive_jobs': total_jobs - active_jobs
            }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}


# Singleton instance
_supabase_client = None

def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client singleton instance"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
