"""Waterloo Works Automator - Main Pipeline.

This module coordinates scraping, analysis, and persistence of WaterlooWorks
job postings. Real-time processing is supported through dedicated helper
objects that encapsulate filtering logic, credential handling, and result
collection.
"""

import json
import os
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from modules.auth import WaterlooWorksAuth
from modules.filters import FilterEngine, FilterDecision
from modules.scraper import WaterlooWorksScraper
from modules.matcher import ResumeMatcher
from modules.results_collector import RealTimeResultsCollector
from modules.config import load_app_config, resolve_waterlooworks_credentials
from modules.database import get_db
from modules.utils import get_pagination_pages, go_to_next_page, close_job_details_panel

try:  # Optional import to avoid circular dependencies in non-CLI usage
    from modules.auth import obtain_authenticated_session
except ImportError:  # pragma: no cover - fallback for environments without CLI helpers
    obtain_authenticated_session = None


class JobAnalyzer:
    """Main pipeline for scraping and analyzing WaterlooWorks jobs"""
    
    def __init__(self, config_path: str = "config.json", use_database: bool = True):
        """Initialize analyzer with configuration
        
        Args:
            config_path: Path to config.json
            use_database: Whether to use database for storage (default: True)
        """
        self.config = load_app_config(config_path)
        self.use_database = use_database
        self.matcher = ResumeMatcher(config=self.config, use_database=use_database)
        self.auth: Optional[WaterlooWorksAuth] = None  # Will be set during scraping
        self.scraper = None  # Will be set during scraping
        self.filter_engine = FilterEngine(self.config)
        print("✅ Job Analyzer initialized\n")

    def run_realtime_pipeline(
        self,
        auto_save_to_folder: bool = True,
        auth: Optional[WaterlooWorksAuth] = None,
        driver=None,
    ) -> List[Dict]:
        """
        Run REAL-TIME pipeline: scrape → analyze → save IMMEDIATELY per job

        Shows score for each job as it's processed and saves high-scoring jobs instantly.

        Args:
            auto_save_to_folder: If True, save high-scoring jobs to WW folder immediately
            auth: Optional pre-authenticated WaterlooWorks session
            driver: Optional Selenium driver if already authenticated

        Returns:
            List of analyzed jobs sorted by fit score
        """
        print("=" * 70)
        print("🚀 WATERLOO WORKS REAL-TIME JOB ANALYZER")
        print("=" * 70)
        print()
        
        # Get configuration
        filter_engine = self.filter_engine
        collector = RealTimeResultsCollector()

        auto_save_threshold = self.config.get("matcher", {}).get("auto_save_threshold", 30)
        folder_name = self.config.get("waterlooworks_folder", "geese")

        print(f"⚙️  Auto-save threshold: {auto_save_threshold}")
        print(f"📁 Target folder: '{folder_name}'")
        print()

        # Step 1: Login and navigate
        if auth or driver:
            print("🔐 Using existing WaterlooWorks session")
        else:
            print("🔐 Logging into WaterlooWorks...")

        resolved_auth, resolved_driver = self._ensure_session(auth, driver)
        self.auth = resolved_auth

        llm_provider = self.config.get("matcher", {}).get("llm_provider", "gemini")
        scraper = WaterlooWorksScraper(resolved_driver, llm_provider=llm_provider)
        self.scraper = scraper
        scraper.go_to_jobs_page()
        
        # Step 2: Process jobs in real-time
        try:
            # Get pagination info
            try:
                num_pages = get_pagination_pages(resolved_driver)
                print(f"📄 Total pages to process: {num_pages}\n")
            except Exception:
                num_pages = 1
                print("📄 Single page detected\n")
            
            print("=" * 70)
            print("🔄 PROCESSING JOBS IN REAL-TIME")
            print("=" * 70)
            print()
            
            # Process each page
            for page in range(1, num_pages + 1):
                print(f"📄 Page {page}/{num_pages}")
                print("-" * 70)
                
                rows = scraper.get_job_table()

                for _, row in enumerate(rows, 1):
                    # Parse basic job info
                    job_data = scraper.parse_job_row(row)
                    if not job_data or not job_data.get('id'):
                        continue

                    collector.start_job()

                    # Show job being processed
                    print(
                        f"\n[Job {collector.total_jobs}] {job_data.get('title', 'Unknown')} @ "
                        f"{job_data.get('company', 'N/A')}"
                    )
                    print(f"           📍 {job_data.get('location', 'N/A')}")

                    # Get detailed job info
                    print(f"           🔍 Scraping details...", end=" ")
                    job_data = scraper.get_job_details(job_data)
                    print("✓")

                    # Analyze match IMMEDIATELY
                    print(f"           🧠 Analyzing match...", end=" ")
                    result = self.matcher.analyze_single_job(job_data)
                    print("✓")

                    # Extract score
                    match = result["match"]
                    fit_score = match["fit_score"]

                    # Show score with color coding
                    if fit_score >= 70:
                        emoji = "🟢"
                    elif fit_score >= 50:
                        emoji = "🟡"
                    elif fit_score >= 30:
                        emoji = "🟠"
                    else:
                        emoji = "🔴"
                    
                    print(f"           {emoji} FIT SCORE: {fit_score}/100")
                    
                    decision: FilterDecision = filter_engine.decide_realtime(
                        job_data, match, auto_save_to_folder
                    )

                    if decision.skip:
                        if decision.message:
                            print(f"           ⏭️  {decision.message}")
                        collector.record_skipped()
                        close_job_details_panel(resolved_driver)
                    elif decision.auto_save:
                        print(f"           💾 Saving to '{folder_name}' folder...", end=" ")

                        job_data["row_element"] = row
                        success = scraper.save_job_to_folder(job_data, folder_name=folder_name)

                        if success:
                            print("✅ SAVED!")
                            collector.record_saved()
                        else:
                            print("❌ Failed")
                            collector.record_skipped()
                            close_job_details_panel(resolved_driver)

                        job_data.pop("row_element", None)
                    else:
                        if decision.message:
                            print(f"           ⏭️  {decision.message}")
                        collector.record_skipped()
                        close_job_details_panel(resolved_driver)

                    # Store result
                    collector.add_result(result)
                
                # Go to next page
                if page < num_pages:
                    print(f"\n➡️  Moving to page {page + 1}...")
                    go_to_next_page(resolved_driver)
                    print()
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Process interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Error during processing: {e}")
            traceback.print_exc()
        
        # Step 3: Save results to files
        print("\n" + "=" * 70)
        print("💾 SAVING RESULTS TO FILES")
        print("=" * 70)

        all_results = collector.persist(self.save_results)

        # Step 4: Show final summary
        print("\n" + "=" * 70)
        print("📊 FINAL SUMMARY")
        print("=" * 70)
        print(f"Total jobs processed: {collector.total_jobs}")
        print(f"✅ Saved to WW folder: {collector.saved_count}")
        print(f"⏭️  Skipped/Low score: {collector.skipped_count}")
        print()

        self.show_summary(all_results[:10])  # Show top 10
        
        # Cleanup - ensure browser is closed even if errors occurred
        if self.auth:
            try:
                self.auth.close()
            except Exception as e:
                print(f"⚠️  Warning: Failed to close browser session: {e}")
        
        return all_results
    
    def run_full_pipeline(self, detailed: bool = True, force_rematch: bool = False, auto_save_to_folder: bool = False) -> List[Dict]:
        """
        Run complete pipeline: scrape → match → filter → save (+ optional auto-save to WW folder)
        
        Args:
            detailed: Whether to scrape detailed job info (slower but better)
            force_rematch: If True, ignore cached matches and recalculate all
            auto_save_to_folder: If True, automatically save high-scoring jobs to "geese" folder
        
        Returns:
            List of analyzed jobs sorted by fit score
        """
        print("=" * 70)
        print("🚀 WATERLOO WORKS JOB ANALYZER")
        print("=" * 70)
        print()
        
        # Step 1: Scrape jobs
        print("📥 Step 1: Scraping jobs from WaterlooWorks...")
        jobs = self._scrape_jobs(detailed=detailed)
        
        if not jobs:
            print("❌ No jobs found. Exiting.")
            return []
        
        print(f"✅ Found {len(jobs)} jobs\n")
        
        # Step 2: Analyze matches
        print("🔍 Step 2: Analyzing job matches...")
        if force_rematch:
            print("⚠️  Force rematch enabled - ignoring cache")
        results = self.matcher.batch_analyze(jobs, force_rematch=force_rematch)
        print(f"✅ Analyzed {len(results)} jobs\n")
        
        # Step 3: Filter results
        print("🎯 Step 3: Applying filters...")
        filtered_results = self.apply_filters(results)
        print(f"✅ {len(filtered_results)} jobs after filtering\n")
        
        # Step 4: Auto-save high-scoring jobs to WaterlooWorks folder (optional)
        if auto_save_to_folder and self.scraper:
            print("📁 Step 4: Auto-saving high-scoring jobs to WaterlooWorks folder...")
            self.auto_save_to_folder(filtered_results)
            print()
        
        # Step 5: Save results locally
        print("💾 Step 5: Saving results to local files...")
        self.save_results(filtered_results)
        print()
        
        # Step 6: Show summary
        self.show_summary(filtered_results)
        
        # Cleanup: Close browser if still open
        if self.auth:
            try:
                self.auth.close()
            except Exception as e:
                print(f"⚠️  Warning: Failed to close browser session: {e}")
        
        return filtered_results
    
    def _scrape_jobs(
        self,
        detailed: bool = True,
        auth: Optional[WaterlooWorksAuth] = None,
    ) -> List[Dict]:
        """Scrape jobs from WaterlooWorks with incremental saving"""
        try:
            # Load existing jobs from database
            os.makedirs("data", exist_ok=True)
            existing_jobs = {}

            if self.use_database:
                # Load from database
                print("📂 Loading existing jobs from database...")
                db = get_db()
                existing_jobs = db.get_jobs_dict()
                print(f"   Found {len(existing_jobs)} cached jobs\n")

            if auth:
                print("🔐 Using existing WaterlooWorks session")
            else:
                print("🔐 Logging into WaterlooWorks...")

            # Login
            auth = self._resolve_auth(auth)

            # Store auth and scraper for later use (auto-save feature)
            self.auth = auth

            # Scrape with incremental saving
            llm_provider = self.config.get("matcher", {}).get("llm_provider", "gemini")
            scraper = WaterlooWorksScraper(auth.driver, llm_provider=llm_provider)
            self.scraper = scraper  # Store for later use
            scraper.go_to_jobs_page()
            
            # Scraper handles database saves automatically
            jobs = scraper.scrape_all_jobs(
                include_details=detailed,
                existing_jobs=existing_jobs,
                save_callback=None,  # Not needed, scraper uses database
                save_every=5,
                use_database=self.use_database
            )
            
            # DON'T close browser yet if we need to auto-save to folder
            # Browser will be closed at the end of the pipeline
            
            print(f"\n✅ Total jobs in cache: {len(jobs)}")
            print(f"   Newly scraped: {len([j for j in jobs if j.get('id') not in existing_jobs])}")
            print(f"   From cache: {len(existing_jobs)}\n")
            
            return jobs
        
        except Exception as e:
            print(f"❌ Error scraping jobs: {e}")
            traceback.print_exc()
            
            # Clean up browser on scraping failure
            if self.auth:
                try:
                    self.auth.close()
                except Exception as cleanup_error:
                    print(f"⚠️  Warning: Failed to cleanup browser: {cleanup_error}")
            
            # Try to use cached data from database
            if self.use_database:
                print("📂 Using cached jobs from database...")
                db = get_db()
                return db.get_all_jobs()
            
            return []

    def _resolve_auth(
        self, existing_auth: Optional[WaterlooWorksAuth] = None
    ) -> WaterlooWorksAuth:
        """Ensure an authenticated WaterlooWorks session is available."""

        if existing_auth:
            if existing_auth.driver is None:
                existing_auth.login()
            return existing_auth

        username, password = resolve_waterlooworks_credentials()
        if username and password:
            auth = WaterlooWorksAuth(username, password)
            auth.login()
            return auth

        if obtain_authenticated_session is None:
            raise RuntimeError(
                "No credential helper available and credentials are missing. "
                "Set WATERLOOWORKS_USERNAME and WATERLOOWORKS_PASSWORD or install CLI helpers."
            )

        return obtain_authenticated_session()

    def _ensure_session(
        self,
        auth: Optional[WaterlooWorksAuth],
        driver: Optional[Any],
    ) -> Tuple[Optional[WaterlooWorksAuth], Any]:
        """Resolve authentication/session inputs for real-time processing."""

        if auth:
            resolved_auth = self._resolve_auth(auth)
            return resolved_auth, resolved_auth.driver

        if driver:
            return None, driver

        resolved_auth = self._resolve_auth(None)
        return resolved_auth, resolved_auth.driver
    
    def apply_filters(self, results: List[Dict]) -> List[Dict]:
        """Apply configured filters to the analyzed results."""
        self.filter_engine.update_config(self.config)
        return self.filter_engine.apply_batch(results)
    
    def auto_save_to_folder(self, results: List[Dict]):
        """
        Automatically save high-scoring jobs to WaterlooWorks folder
        
        Args:
            results: List of analyzed job results
        """
        if not self.scraper:
            print("  ⚠️  Scraper not available. Skipping auto-save.")
            return
        
        # Get thresholds from config
        auto_save_threshold = self.config.get("matcher", {}).get("auto_save_threshold", 50)
        folder_name = self.config.get("waterlooworks_folder", "geese")
        
        # Find jobs that meet the threshold
        jobs_to_save = [
            r for r in results 
            if r["match"]["fit_score"] >= auto_save_threshold
        ]
        
        if not jobs_to_save:
            print(f"  ℹ️  No jobs with fit score >= {auto_save_threshold}. Nothing to save.")
            return
        
        print(f"  🎯 Found {len(jobs_to_save)} jobs with fit score >= {auto_save_threshold}")
        print(f"  📁 Saving to WaterlooWorks folder: '{folder_name}'")
        print()
        
        saved_count = 0
        failed_count = 0
        
        for i, result in enumerate(jobs_to_save, 1):
            job = result["job"]
            score = result["match"]["fit_score"]
            
            print(f"  [{i}/{len(jobs_to_save)}] {job.get('title', 'Unknown')} - Score: {score}/100")
            
            success = self.scraper.save_job_to_folder(job, folder_name=folder_name)
            
            if success:
                saved_count += 1
            else:
                failed_count += 1
            
            print()
        
        print(f"  ✅ Successfully saved: {saved_count}/{len(jobs_to_save)}")
        if failed_count > 0:
            print(f"  ❌ Failed to save: {failed_count}/{len(jobs_to_save)}")
    
    def save_results(self, results: List[Dict]):
        """Save analyzed results to database
        
        Args:
            results: List of job match results
        """
        # Save to database
        if self.use_database:
            print(f"   💾 Saving results to database...")
            db = get_db()
            saved_count = 0
            for result in results:
                # Save job if not already saved
                job = result.get("job", {})
                if job.get("id"):
                    db.insert_job(job)
                
                # Save match result
                match = result.get("match", {})
                if job.get("id") and match:
                    db.insert_match(job.get("id"), match)
                    saved_count += 1
            print(f"   ✅ Saved {saved_count} matches to database")
    
    def show_summary(self, results: List[Dict]):
        """Show summary in terminal"""
        print("=" * 70)
        print("📊 TOP MATCHES")
        print("=" * 70)
        print()
        
        if not results:
            print("No matches found after filtering.")
            return
        
        # Show top 10
        for i, result in enumerate(results[:10], 1):
            job = result["job"]
            match = result["match"]
            
            # Emoji based on score
            if match["fit_score"] >= 70:
                emoji = "🟢"
            elif match["fit_score"] >= 50:
                emoji = "🟡"
            elif match["fit_score"] >= 30:
                emoji = "🟠"
            else:
                emoji = "🔴"
            
            print(f"{emoji} #{i} - Fit Score: {match['fit_score']}/100")
            print(f"   📋 {job.get('title', 'Unknown')} at {job.get('company', 'N/A')}")
            print(f"   📍 {job.get('location', 'N/A')}")
            print(f"   📈 Keyword: {match.get('keyword_match', 0)}% | Semantic: {match['coverage']}% | Seniority: {match['seniority_alignment']}%")
            
            # Show matched tech (if any)
            if match.get("matched_technologies"):
                tech_list = match["matched_technologies"][:5]  # Top 5
                print(f"   ✅ Tech Match: {', '.join(tech_list)}")
            
            print()
        
        if len(results) > 10:
            print(f"... and {len(results) - 10} more jobs")
            print()
        
        print("=" * 70)
        print(f"✅ Analysis complete! Check data/ folder for full reports.")
        print("=" * 70)
